import os
from typing import Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def generate_cover_letter(resume_text: str, job_description: str, tone="Professional") -> str:
    """
    Generate a personalized cover letter based on the user's resume and the job description.

    Args:
        resume_text (str): The text content of the user's resume.
        job_description (str): The text content of the job description.
        tone (Optional[str]): Optional tone preset, e.g., 'professional', 'friendly', 'creative'.

    Returns:
        str: Generated cover letter (only the letter text).
    """

    # Base prompt
    prompt = f"""
    You are an expert career advisor specialized in writing highly effective, ATS-friendly cover letters. 
    Using the resume and job description below, generate a **concise, professional cover letter** that would fit a single page. 

    Requirements:
    - Highlight the candidate's most relevant achievements with measurable results.
    - Mirror the key skills and qualifications from the job description.
    - Keep a strictly professional tone, emphasizing the value the candidate brings to the company.
    - Avoid filler; every sentence should demonstrate impact or relevance.

    Resume:
    {resume_text}

    Job Description:
    {job_description}

    Output only the cover letter text.
    """

    # Add tone if provided
    if tone:
        prompt += f"\n\nTone: Write the cover letter in a {tone} tone."

        # --- GROQ LLM integration example ---
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
    )
    html_content = response.choices[0].message.content.strip()
    return html_content
