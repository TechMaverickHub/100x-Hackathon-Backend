import json
import os
from typing import Dict, Optional

from dotenv import load_dotenv
from groq import Groq

import re

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# JSON robustness instructions
JSON_INSTRUCTIONS = """
Important instructions for JSON robustness:
- Use double quotes for all keys and string values.
- Return only the JSON; do not include any extra text or explanations.
- Follow the example structure provided for each function.
"""

# def generate_latex_prompt(data: dict) -> str:
#     """
#     Generates an ATS-friendly LaTeX resume from user input JSON via GROQ LLM.
#
#     Args:
#         data (dict): Resume input including name, role, tagline, bio, skills, projects, experience, education, contact.
#
#     Returns:
#         str: Raw LaTeX code of the resume.
#     """
#     # --- Build prompt for LLM ---
#     technical_skills = ', '.join([f"{s['skill']}({s['weight']})" for s in data.get('skills', {}).get('technical', [])])
#     soft_skills = ', '.join([f"{s['skill']}" for s in data.get('skills', {}).get('soft', [])])
#
#     projects_text = ''.join([f"- {p['title']}: {p['desc']}\n" for p in data.get('projects', [])])
#     experience_text = ''.join(
#         [f"- {e['role']} at {e['company']} ({e['duration']}): {e['desc']}\n" for e in data.get('experience', [])])
#     education_text = ''.join(
#         [f"- {ed['degree']} from {ed['institution']} ({ed['year']})\n" for ed in data.get('education', [])])
#
#     prompt = f"""
# Generate only the LaTeX code for a classic, one-column, fully monochrome, ATS-friendly resume.
# Use the following information to populate the resume.
# Do NOT include any explanation, instructions, or text outside LaTeX code. Only LaTeX.
#
# Name: {data.get('name')}
# Role: {data.get('role')}
# Tagline: {data.get('tagline')}
# Bio: {data.get('bio')}
#
# Skills:
# Technical: {technical_skills}
# Soft: {soft_skills}
#
# Projects:
# {projects_text}
#
# Experience:
# {experience_text}
#
# Education:
# {education_text}
#
# Contact:
# Email: {data.get('email')}
# LinkedIn: {data.get('linkedin')}
# GitHub: {data.get('github')}
# Twitter: {data.get('twitter')}
# """
#
#     # --- GROQ LLM integration ---
#     api_key = os.getenv("GROQ_API_KEY")
#     if not api_key:
#         raise ValueError("GROQ_API_KEY not found in environment variables")
#
#     response = client.chat.completions.create(
#         model="openai/gpt-oss-20b",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.6,
#         max_tokens=6000
#     )
#
#     choices = getattr(response, "choices", None)
#     if not choices or not hasattr(choices[0], "message"):
#         raise RuntimeError("Unexpected response from GROQ API")
#
#     latex_content = choices[0].message.content.strip()
#     return latex_content



def _limit_items(items, max_items, min_items=None):
    if not items:
        return []
    limited = items[:max_items]
    if min_items and len(limited) < min_items:
        limited = items[:min_items]
    return limited


def _limit_bullets(lines, max_lines, max_chars):
    if not lines:
        return []
    trimmed = []
    for line in lines:
        clean = line.strip()
        if not clean:
            continue
        trimmed.append(clean[:max_chars].rstrip())
        if len(trimmed) >= max_lines:
            break
    return trimmed


def _split_sentences(text: str):
    if not text:
        return []
    candidates = re.split(r'(?<=[.!?])\s+|\n+', text)
    lines = [candidate.strip() for candidate in candidates if candidate.strip()]
    return lines


def _format_itemize_block(lines):
    if not lines:
        return ""
    bullet_lines = "".join([f"    \\item {line}\n" for line in lines])
    return "\\begin{itemize}\n" + bullet_lines + "\\end{itemize}\n"


def generate_latex_prompt(data: dict) -> str:
    """
    Generates an ATS-optimized LaTeX resume that fits exactly one page.
    Applies deterministic trimming to keep each section within tight bounds
    before delegating fine-grained control to the LLM.
    """

    # --- Configurable caps to maintain one-page layout ---
    summary_max_chars = 1500
    tech_skill_cap = 15
    soft_skill_cap = 12
    project_cap = 4
    project_bullet_cap = 4
    experience_cap = 4
    experience_bullet_cap = 5
    education_cap = 3
    bullet_char_cap = 220

    # --- Summary / Bio ---
    summary_text_raw = (data.get('bio') or "").strip()
    summary_sentences = _split_sentences(summary_text_raw)
    if not summary_sentences:
        summary_sentences = [summary_text_raw]
    min_summary_sentences = 4
    max_summary_sentences = 6
    if len(summary_sentences) < min_summary_sentences:
        summary_sentences = summary_sentences + summary_sentences[:1] * (min_summary_sentences - len(summary_sentences))
    summary_sentences = summary_sentences[:max_summary_sentences]
    summary_text = " ".join(summary_sentences)
    summary_text = summary_text[:summary_max_chars]
    summary_hint = ""
    if len(summary_text_raw) < 400:
        summary_hint = "%% Expand summary to 4-6 sentences referencing skills, impact, and industries.\n"

    # --- Build contact links ---
    contact_links_list = []
    if data.get('email'):
        contact_links_list.append(f"\\href{{mailto:{data['email']}}}{{Email}}")
    for label in ("LinkedIn", "GitHub", "Portfolio", "Website", "Twitter"):
        link = data.get('links', {}).get(label)
        if link:
            contact_links_list.append(f"\\href{{{link}}}{{{label}}}")
    contact_links = " | ".join(contact_links_list)

    # --- Structured Text Assembly ---
    technical_skills = _limit_items(data.get('skills', {}).get('technical', []), tech_skill_cap)
    soft_skills = _limit_items(data.get('skills', {}).get('soft', []), soft_skill_cap)

    tech_skill_text = ', '.join([f"{s['skill']} ({s['weight']})" for s in technical_skills])
    soft_skill_text = ', '.join([s['skill'] for s in soft_skills])
    soft_skills_line = f"\\\\{soft_skill_text}" if soft_skill_text else ""

    projects = []  # each entry: (latex_block, min_required_bullets)
    for project in _limit_items(data.get('projects', []), project_cap):
        bullet_lines = project.get('desc_lines') or []
        if not bullet_lines:
            bullet_lines = _split_sentences(project.get('desc', ''))
        if not bullet_lines:
            bullet_lines = [project.get('desc', '')]
        lines = _limit_bullets(bullet_lines, project_bullet_cap, bullet_char_cap)
        context_note = ""
        if len(lines) <= 1:
            context_note = "%% Expand to at least two bullet points using provided details.\n"
        projects.append(
    f"\\noindent\\textbf{{{project.get('title', 'Project')}}} \\\\ \n"
            + context_note
            + _format_itemize_block(lines)
        )
    projects_text = "".join(projects)

    experiences = []
    for exp in _limit_items(data.get('experience', []), experience_cap):
        bullet_lines = exp.get('desc_lines') or []
        if not bullet_lines:
            bullet_lines = _split_sentences(exp.get('desc', ''))
        if not bullet_lines:
            bullet_lines = [exp.get('desc', '')]
        bullets = _limit_bullets(bullet_lines, experience_bullet_cap, bullet_char_cap)
        context_note = ""
        if len(bullets) <= 2:
            context_note = "%% Elaborate responsibilities/results to reach 3-5 bullets.\n"
        header = f"\\noindent\\textbf{{{exp.get('role', 'Role')} at {exp.get('company', 'Company')}}} \\hfill {exp.get('duration', '')} \\\\\n"
        location_line = f"\\textit{{{exp.get('location', '')}}} \\\\\n" if exp.get('location') else ""
        experiences.append(header + location_line + context_note + _format_itemize_block(bullets))
    experience_text = "".join(experiences)

    education = []
    for edu in _limit_items(data.get('education', []), education_cap):
        education.append(
            f"\\noindent \\textbf{{{edu.get('degree', 'Degree')} from {edu.get('institution', 'Institution')}}} \\hfill {edu.get('year', '')} \n"
        )
    education_text = "".join(education)

    # --- Adaptive One-Page Prompt ---
    prompt = f"""
Generate ONLY LaTeX code for a one-page, ATS-friendly resume.
Do NOT include any commentary.

\\documentclass[10pt,a4paper]{{article}}
\\usepackage{{geometry}}
\\geometry{{a4paper, top=0.55in, bottom=0.55in, left=0.55in, right=0.55in}}
\\usepackage{{enumitem}}
\\usepackage{{hyperref}}
\\usepackage{{titlesec}}
\\linespread{{0.95}}
\\setlength{{\\parskip}}{{0pt}}
\\setlist[itemize]{{noitemsep, topsep=0pt, left=0.15in}}
\\titleformat*{{\\section}}{{\\large\\bfseries}}
\\pagenumbering{{gobble}}
\\renewcommand{{\\labelitemi}}{{--}}

\\begin{{document}}

\\begin{{center}}
    {{\\LARGE \\textbf{{{data.get('name', '')}}}}} \\\\[0.15cm]
    {data.get('role', '')} | {data.get('tagline', '')} \\\\[0.15cm]
    {data.get('location', '')} | {data.get('phone', '')} \\\\
    {contact_links}
\\end{{center}}

\\vspace{{0.15cm}}

\\section*{{Summary}}
{summary_hint}{summary_text}

\\section*{{Skills}}
{tech_skill_text}
{soft_skills_line}

\\section*{{Projects}}
{projects_text}

\\section*{{Experience}}
{experience_text}

\\section*{{Education}}
{education_text}

\\end{{document}}

STRICT FORMAT RULES (must comply to keep resume exactly one page):
1. DO NOT change margins, font sizes, or spacing defined above.
2. Ensure the compiled output uses the entire single page—neither spilling to a second page nor leaving noticeable blank regions.
3. Ensure the summary spans 4–6 sentences highlighting skills, domains, and measurable impact derived from the provided bio.
4. For every project, produce 2–4 concise bullet lines by decomposing the provided descriptions into actions, tools, and measurable outcomes; stay faithful to supplied details.
5. For every experience entry, produce 3–5 concise bullet lines emphasizing scope, contribution, and results using the given text; do not fabricate organizations or responsibilities.
6. When content is short, meaningfully expand existing statements with truthful details (metrics, tech stack, context) derived from supplied text.
7. Bullet items must remain single lines after typesetting; tighten wording if necessary while preserving action → impact flow.
8. If space still remains, enrich existing bullets with quantifiable results or context from the input data so the page feels complete.
9. Never add new sections or reorder existing ones.
"""

    # --- GROQ API Call ---
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=7000
    )

    choices = getattr(response, "choices", None)
    if not choices or not hasattr(choices[0], "message"):
        raise RuntimeError("Unexpected response from GROQ API")

    latex_content = choices[0].message.content.strip()
    return latex_content

def generate_resume_score(resume_text: str, job_description: str) -> Dict:
    """
    Generate a structured JSON score for a resume against a job description using GROQ LLM.

    Returns JSON with keys: score, strengths, weaknesses.
    Ensures valid JSON with double quotes and no extra text.
    """

    # Prompt with JSON robustness instructions
    prompt = f"""
You are a career coach AI. Given the resume and job description below, provide:
1. A match score (0-100)
2. Key strengths matched
3. Key weaknesses or missing experience

Resume:
{resume_text}

Job Description:
{job_description}

Return the result as a JSON object with keys:
"score", "strengths", "weaknesses".

**Important instructions for JSON robustness**:
- Use double quotes for all keys and strings.
- Return only the JSON; do not add extra text or explanations.
- Example structure:
{{
    "score": 85,
    "strengths": ["Python expertise", "Django experience"],
    "weaknesses": ["Missing Azure Cognitive Services experience"]
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content.strip()

    try:
        result_json = json.loads(content)
    except json.JSONDecodeError:
        # fallback if JSON parsing fails
        result_json = {"raw_text": content}

    return result_json


def keyword_gap_analysis(resume_text: str, job_description: str) -> Dict:
    """
    Compare resume against job description and return matched and missing keywords.
    Returns structured JSON with keys: matched_keywords, missing_keywords.
    """
    prompt = f"""
Extract keywords from the job description that are relevant to the role.
Compare them to the resume and return two lists: "matched_keywords" and "missing_keywords".

Resume:
{resume_text}

Job Description:
{job_description}

**Important instructions for JSON robustness**:
- Use double quotes for all keys and strings.
- Return only the JSON; do not add extra text or explanations.
- Example structure:
{{
    "matched_keywords": ["Python", "Django", "REST API"],
    "missing_keywords": ["Azure Cognitive Services", "Autogen", "Power Automate"]
}}
"""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_text": content}


# 2. Auto-Rewrite / Enhancement Suggestions
def auto_rewrite_resume(resume_text: str, job_description: str, tone: Optional[str] = "Professional") -> Dict:
    """
    Rewrite the resume to improve alignment with the job description.
    Returns JSON with keys: original_text, enhanced_text, suggested_keywords_added.
    """
    prompt = f"""
Rewrite the resume content to improve alignment with the job description.
Add missing keywords naturally without changing the meaning.
Maintain a {tone} tone.

Resume:
{resume_text}

Job Description:
{job_description}

**Important instructions for JSON robustness**:
- Use double quotes for all keys and strings.
- Return only the JSON; do not add extra text or explanations.
- Example structure:
{{
    "original_text": "Experienced software developer with 3 years in Python and Django.",
    "enhanced_text": "Experienced software developer with 3 years in Python and Django, skilled in Azure Cognitive Services and Autogen for AI applications.",
    "suggested_keywords_added": ["Azure Cognitive Services", "Autogen"]
}}
"""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_text": content}

def generate_skill_gap(resume_text: str, job_description: str) -> Dict:
    """
    Compare resume against job description and return matched, missing, and extended skill insights.
    Returns structured JSON with keys:
    - matched_skills
    - missing_skills
    - gap_score
    - match_percent
    - summary
    - comparative_insight
    - trend_insight
    - visual_summary
    """
    prompt = f"""
Extract and compare the skills from the job description and the resume.
Return a structured JSON with the following keys:

1. "matched_skills": skills present in both resume and job description.
2. "missing_skills": skills required by the job but missing in the resume.
3. "gap_score": fraction of required skills missing (0-1).
4. "match_percent": percentage of required skills matched (integer 0–100).
5. "summary": a one- or two-sentence summary explaining the skill match and improvement suggestion.
6. "comparative_insight": {{
       "average_match_percent_for_role": integer,
       "market_position": one of ["Above average", "Average", "Slightly below average", "Below average"],
       "insight": short text describing how this resume compares to other candidates.
   }}
7. "trend_insight": {{
       "emerging_skills": list of new or trending skills relevant to this role,
       "high_demand_skills": list of in-demand skills mentioned in the job description,
       "insight": one-sentence summary highlighting which missing skills matter most.
   }}
8. "visual_summary": {{
       "show_progress_bar": true,
       "color_code": one of ["success", "warning", "danger"] depending on skill match level,
       "label": formatted text like "Skill Match: 67%"
   }}

Resume:
{resume_text}

Job Description:
{job_description}

**Important JSON formatting rules**:
- Use double quotes for all keys and strings.
- Do not include explanations, markdown, or text outside the JSON.
- Example structure:
{{
    "matched_skills": ["Python", "Django"],
    "missing_skills": ["SQL", "Machine Learning"],
    "gap_score": 0.33,
    "match_percent": 67,
    "summary": "You match 67% of the skills required. Adding SQL and Machine Learning would improve your alignment.",
    "comparative_insight": {{
        "average_match_percent_for_role": 72,
        "market_position": "Slightly below average",
        "insight": "Most applicants for similar roles include ML or SQL experience."
    }},
    "trend_insight": {{
        "emerging_skills": ["Generative AI", "Prompt Engineering"],
        "high_demand_skills": ["Machine Learning", "SQL"],
        "insight": "Machine Learning and SQL are trending upward in demand for this role."
    }},
    "visual_summary": {{
        "show_progress_bar": true,
        "color_code": "warning",
        "label": "Skill Match: 67%"
    }}
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_text": content}

def generate_career_recommendation(resume_text: str, job_description: str) -> Dict:
    """
    Analyze the candidate's resume and job description to generate personalized
    career growth recommendations, suggested learning resources, and actionable advice.

    Returns structured JSON with keys:
    - "career_paths": list of recommended job-aligned roles
    - "career_level": analysis of current vs target level (e.g., entry → mid-level)
    - "recommended_courses": list of relevant upskilling or certification courses
    - "recommended_blogs": list of key blogs or articles to follow
    - "recommended_repos": list of GitHub repositories to study or contribute to
    - "recommended_projects": list of practical project ideas for portfolio building
    - "advice": concise personalized guidance summary (1–2 sentences)
    - "next_steps": list of 3–5 actionable short-term steps
    """
    prompt = f"""
Analyze the candidate's resume and the following job description to recommend
career paths, skill-building resources, and next actions. Tailor everything
toward the target job role described.

Resume:
{resume_text}

Job Description:
{job_description}

You must:
1. Suggest 1–3 suitable career paths aligned with the candidate's current skills and target job.
2. Assess the candidate's current career level vs. target level (e.g., "mid-level aiming for senior role").
3. Recommend 3–5 upskilling or certification courses (Coursera, Udemy, LinkedIn Learning, etc.).
4. Recommend 2–3 blogs or knowledge hubs to follow (with title, short description, link).
5. Recommend 2–3 GitHub repositories relevant to the target job (with short description, link).
6. Suggest 2–3 project ideas that would strengthen their portfolio for this role.
7. Provide one concise "advice" paragraph (1–2 sentences).
8. Provide a "next_steps" list of 3–5 actionable tasks (e.g., "Add SQL project", "Refactor GitHub portfolio").

**Important instructions for JSON robustness**:
- Use double quotes for all keys and strings.
- Return only the JSON; no commentary or explanations.
- Keep all text concise and role-specific.
- Example structure:
{{
    "career_paths": ["Data Analyst", "Machine Learning Engineer"],
    "career_level": {{
        "current_level": "Entry-level",
        "target_level": "Mid-level",
        "insight": "The candidate has strong programming skills but lacks applied ML experience."
    }},
    "recommended_courses": [
        {{
            "title": "SQL for Data Science",
            "platform": "Coursera",
            "link": "https://www.coursera.org/learn/sql-for-data-science"
        }},
        {{
            "title": "Machine Learning A-Z",
            "platform": "Udemy",
            "link": "https://www.udemy.com/course/machinelearning"
        }}
    ],
    "recommended_blogs": [
        {{
            "title": "Towards Data Science",
            "description": "Practical guides and industry insights for data professionals.",
            "link": "https://towardsdatascience.com/"
        }},
        {{
            "title": "Analytics Vidhya",
            "description": "Data science tutorials and career growth insights.",
            "link": "https://www.analyticsvidhya.com/blog/"
        }}
    ],
    "recommended_repos": [
        {{
            "title": "Awesome Machine Learning",
            "description": "Curated list of top ML frameworks and projects.",
            "link": "https://github.com/josephmisiti/awesome-machine-learning"
        }},
        {{
            "title": "Data Science Portfolio Template",
            "description": "Portfolio starter repo for showcasing data projects.",
            "link": "https://github.com/username/datascience-portfolio"
        }}
    ],
    "recommended_projects": [
        {{
            "title": "Customer Churn Prediction",
            "description": "Build an ML model to predict customer churn using Python."
        }},
        {{
            "title": "Job Skill Extraction NLP App",
            "description": "Develop a resume parser that extracts and matches skills to job descriptions."
        }}
    ],
    "advice": "Focus on demonstrating end-to-end data project delivery to reach mid-level expectations.",
    "next_steps": [
        "Add an SQL project to portfolio.",
        "Refactor GitHub repositories for readability.",
        "Start contributing to open ML repos.",
        "Follow 2–3 key industry blogs.",
        "Complete a structured ML course."
    ]
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_text": content}