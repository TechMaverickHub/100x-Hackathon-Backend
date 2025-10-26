import os

import feedparser
from dotenv import load_dotenv
from groq import Groq

import json
from typing import List, Dict


client = Groq(api_key=os.getenv("GROQ_API_KEY"))

load_dotenv()


def fetch_jobs_from_rss(url: str, limit: int = 5):
    """
    Fetch a limited number of jobs from RSS feed to improve response speed.
    """
    feed = feedparser.parse(url)
    jobs = []
    for entry in feed.entries[:limit]:  # limit to top N items
        jobs.append({
            "title": entry.title,
            "description": entry.get("summary", ""),
            "link": entry.link,
            "published": entry.get("published", ""),
        })
    return jobs

def match_jobs_to_resume(user_resume_text: str, jobs: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    Match user's resume with job descriptions using Groq LLM semantic scoring.

    Returns a list of top-k matched jobs with JSON structure:
    [
        {
            "title": "Software Engineer",
            "link": "https://example.com/job1?resume_prefilled=true",
            "score": 87,
            "keywords_matched": ["Python", "REST APIs", "Django"]
        },
        ...
    ]
    """

    matched_jobs = []

    for job in jobs:
        # --- Build structured prompt ---
        prompt = f"""
You are an AI job-matching assistant.

Given a candidate's resume and a job description, analyze their match quality.

Return a JSON object with:
- "score": integer (0–100) similarity score
- "keywords_matched": list of top matching skills or terms

Resume:
{user_resume_text}

Job Description:
{job['description']}

Return only JSON.
Example format:
{{
    "score": 85,
    "keywords_matched": ["Python", "Machine Learning", "REST API"]
}}
        """

        # --- Query the LLM ---
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content.strip()

        # --- Safe JSON parsing ---
        try:
            result_json = json.loads(content)
        except json.JSONDecodeError:
            result_json = {"score": 0, "keywords_matched": []}

        score = result_json.get("score", 0)
        if score > 50:  # threshold
            matched_jobs.append({
                "title": job.get("title"),
                "link": job.get("link", "#") + "?resume_prefilled=true",
                "score": score,
                "keywords_matched": result_json.get("keywords_matched", [])
            })

    # --- Sort and return top K ---
    matched_jobs.sort(key=lambda x: x["score"], reverse=True)
    return matched_jobs[:top_k]



def get_job_alerts_for_user(resume_text, user, max_jobs_per_source: int = 5):
    """
    Fetch limited jobs from each RSS source, match using LLM, and return top matches.
    Limits are applied for fast response.
    """
    user_sources = user.job_sources.values("source__name", "source__rss_url")

    all_jobs = []
    for source in user_sources:
        rss_url = source.get("source__rss_url")
        source_name = source.get("source__name")

        if not rss_url:
            continue

        try:
            print(f"Fetching top {max_jobs_per_source} jobs from {source_name}: {rss_url}")
            jobs = fetch_jobs_from_rss(rss_url, limit=max_jobs_per_source)
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"Error fetching from {source_name}: {e}")

    if not all_jobs:
        print("No jobs fetched from any active sources.")
        return []

    # Limit total jobs sent to LLM to avoid long delays
    all_jobs = all_jobs[:10]
    print(f"Matching {len(all_jobs)} jobs using LLM...")

    return match_jobs_to_resume(resume_text, all_jobs, top_k=5)