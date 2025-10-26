import os
from typing import List, Dict
import json

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_interview_questions(
        resume_text: str,
        job_description: str,
        question_type: str
) -> List[Dict]:
    """
    Generate 5 role-aware interview questions using an LLM based on a resume and job description.

    Args:
        resume_text: Full text of the candidate's resume.
        job_description: Job description text.
        question_type: "technical", "behavioral", or "mixed".

    Returns:
        List of 5 questions in JSON format:
        [
            {"text": "Question text", "type": "technical|behavioral", "context": "Optional hints"},
            ...
        ]

    **Important instructions for JSON robustness**:
    - Use double quotes for all keys and strings.
    - Return only JSON array of objects; do not add extra text.
    """

    prompt = f"""
You are an expert career coach AI. Based on the candidate's resume and the job description below,
generate exactly 5 interview questions relevant to the role.

Resume:
{resume_text}

Job Description:
{job_description}

Question type requested: {question_type}

For each question, include:
1. "text": the question itself
2. "type": "technical" or "behavioral"
3. "context": optional hints or reasoning why this question is relevant to the candidate's profile

Return only a JSON array of 5 objects, for example:

[
    {{"text": "Explain polymorphism in OOP.", "type": "technical", "context": "The candidate has Python and Django experience"}},
    ...
]

**JSON robustness rules**:
- Use double quotes for all keys and strings.
- Return only JSON, no extra text or explanations.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content.strip()

    try:
        questions = json.loads(content)
    except json.JSONDecodeError:
        # fallback in case parsing fails
        questions = [{"text": content, "type": question_type, "context": ""}]

    return questions


def generate_interview_score(
    resume_text: str,
    job_description: str,
    question_list: List[Dict]
) -> Dict:
    """
    Generate a structured JSON analysis of a candidate's fit for a role
    based on their resume, job description, and a set of interview questions with answers.

    Returns JSON with keys:
    - overall_score: float (0-1)
    - strengths: List[str]
    - areas_to_improve: List[str]
    - recommendations: List[str]
    - questions_feedback: List[Dict] with keys: question, answer, feedback

    Ensures valid JSON with double quotes and no extra text.
    """

    # Convert question_list to formatted string for prompt
    questions_str = "\n".join(
        [
            f"{i+1}. Question: {q['text']}\n   Type: {q['type']}\n   Context: {q.get('context','')}\n   Answer: {q.get('answer','')}"
            for i, q in enumerate(question_list)
        ]
    )

    prompt = f"""
You are an expert career coach AI. Given a candidate's resume, job description,
and a list of interview questions with answers, analyze the candidate's fit and performance potential.

Resume:
{resume_text}

Job Description:
{job_description}

Interview Questions with Answers:
{questions_str}

Provide an overall assessment including:
1. overall_score (0-1 scale)
2. Key strengths
3. Areas to improve
4. Actionable recommendations for improvement

Also provide feedback for each question in the list including:
- question
- answer
- feedback on how to improve the answer

Return only a JSON object in this exact format:
{{
  "overall_score": 0.0,
  "strengths": [],
  "areas_to_improve": [],
  "recommendations": [],
  "questions_feedback": [
      {{"question": "", "answer": "", "feedback": ""}}
  ]
}}

**Important instructions for JSON robustness**:
- Use double quotes for all keys and strings.
- Return only JSON; do not add extra text or explanations.
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
