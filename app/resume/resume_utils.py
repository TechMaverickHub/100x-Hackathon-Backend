import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


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

    client = Groq(api_key=api_key)
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