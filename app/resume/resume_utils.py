import json
import os
from typing import Dict, Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# JSON robustness instructions
JSON_INSTRUCTIONS = """
Important instructions for JSON robustness:
- Use double quotes for all keys and string values.
- Return only the JSON; do not include any extra text or explanations.
- Follow the example structure provided for each function.
"""

def generate_latex_prompt(data: dict) -> str:
    """
    Generates an ATS-friendly LaTeX resume from user input JSON via GROQ LLM.

    Args:
        data (dict): Resume input including name, role, tagline, bio, skills, projects, experience, education, contact.

    Returns:
        str: Raw LaTeX code of the resume.
    """
    # --- Build prompt for LLM ---
    technical_skills = ', '.join([f"{s['skill']}({s['weight']})" for s in data.get('skills', {}).get('technical', [])])
    soft_skills = ', '.join([f"{s['skill']}({s['weight']})" for s in data.get('skills', {}).get('soft', [])])

    projects_text = ''.join([f"- {p['title']}: {p['desc']}\n" for p in data.get('projects', [])])
    experience_text = ''.join(
        [f"- {e['role']} at {e['company']} ({e['duration']}): {e['desc']}\n" for e in data.get('experience', [])])
    education_text = ''.join(
        [f"- {ed['degree']} from {ed['institution']} ({ed['year']})\n" for ed in data.get('education', [])])

    prompt = f"""
Generate only the LaTeX code for a classic, one-column, fully monochrome, ATS-friendly resume. 
Use the following information to populate the resume. 
Do NOT include any explanation, instructions, or text outside LaTeX code. Only LaTeX.

Name: {data.get('name')}
Role: {data.get('role')}
Tagline: {data.get('tagline')}
Bio: {data.get('bio')}

Skills:
Technical: {technical_skills}
Soft: {soft_skills}

Projects:
{projects_text}

Experience:
{experience_text}

Education:
{education_text}

Contact:
Email: {data.get('email')}
LinkedIn: {data.get('linkedin')}
GitHub: {data.get('github')}
Twitter: {data.get('twitter')}
"""

    # --- GROQ LLM integration ---
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=6000
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
