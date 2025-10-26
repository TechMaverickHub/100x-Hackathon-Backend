import json
import os
from html.parser import HTMLParser

import PyPDF2
from docx import Document
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


# -------------------------------
# 1️⃣ File Parsing Functions
# -------------------------------

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file, concatenating all pages."""
    reader = PyPDF2.PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a Word document."""
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def extract_resume_text(file_path: str, file_type: str) -> str:
    """Extract text based on file type ('pdf' or 'docx')."""
    if file_type.lower() == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type.lower() == "docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file type. Only PDF and DOCX allowed.")


# -------------------------------
# 2️⃣ Heading / Structure Extraction
# -------------------------------

def detect_headings(text: str) -> list:
    """Detect section headings like Experience, Education, Skills."""
    headings = []
    for line in text.splitlines():
        line_clean = line.strip().lower()
        if line_clean in ["experience", "education", "skills"]:
            headings.append(line.strip())
    return headings


# -------------------------------
# 3️⃣ HTML Validation
# -------------------------------

class HTMLValidator(HTMLParser):
    def error(self, message):
        raise ValueError(f"HTML Validation Error: {message}")


def validate_html(html_content: str):
    """Validate HTML using Python's built-in parser."""
    parser = HTMLValidator()
    parser.feed(html_content)


# -------------------------------
# 4️⃣ LLM HTML Generation
# -------------------------------

def generate_html_via_llm(text: str, headings: list) -> str:
    """
    Generate responsive HTML via GROQ LLM.

    Requirements:
        - Fully responsive layout
        - Inline CSS
        - Suggest color schemes & fonts
        - SEO meta tags
        - Browser-compatible HTML
    """
    prompt = f"""
You are an expert front-end designer and HTML/CSS generator. 
Your task is to generate a SINGLE-PAGE responsive personal portfolio website in pure HTML with inline CSS.

INPUT CONTENT:
{text}

STRUCTURE REQUIRED:
Sections to include (in this order):
1. Home (hero intro with name, role, short tagline)
2. About (brief professional bio)
3. Resume (download button for résumé)
4. Projects (interactive cards or grid)
5. Contact (simple section with email & links)

REQUIREMENTS:
1. Return ONLY the raw HTML code — no markdown, explanations, comments, triple backticks, or "html\\n" prefixes.
2. The output must start with "<!DOCTYPE html>" and end with "</html>".
3. All styles must be included in a <style> block inside the <head> (no external CSS or JS files).
4. Layout must be fully responsive and mobile-friendly.
5. Apply a clean, minimal design (lots of whitespace, simple color palette, soft shadows, modern typography).
6. Let the model automatically choose an appropriate font and harmonious color palette.
7. Include subtle, accessible interactive behavior — e.g. smooth scroll navigation, hover effects, mobile menu toggle.
8. Include a favicon placeholder link in the <head>.
9. Add <meta> tags for SEO and social preview (title, description, keywords, og:title, og:description, og:type, og:image placeholder).
10. Ensure HTML passes semantic and accessibility standards.
11. Optimize for browser compatibility and responsiveness.
12. Include a "Download Resume" button in the Resume section with a placeholder href (e.g., resume.pdf).
13. Use sample project cards (title, short description, and “View Project” button).
14. Use only the input content for text; no filler biography beyond what is provided.
15. Output clean, export-ready HTML starting with <!DOCTYPE html> and ending with </html>.
"""

    # --- GROQ LLM integration example ---
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
    )
    html_content = response.choices[0].message.content.strip()
    return html_content


# -------------------------------
# 5️⃣ Full Pipeline Function
# -------------------------------

def process_resume(file_path: str, file_type: str) -> str:
    """
    Full end-to-end pipeline:
    1. Extract text
    2. Detect headings
    3. Generate HTML via LLM
    4. Validate HTML
    5. Return export-ready HTML
    """
    text = extract_resume_text(file_path, file_type)
    headings = detect_headings(text)
    html_content = generate_html_via_llm(text, headings)
    validate_html(html_content)
    return html_content


# def generate_portfolio_from_qna(qna_data: dict) -> str:
#     """
#     Generate a SINGLE-PAGE responsive portfolio HTML via GROQ LLM
#     using structured QnA input.
#
#     Requirements:
#         - Fully responsive layout
#         - Inline CSS
#         - Suggested color schemes & fonts
#         - SEO meta tags
#         - Browser-compatible HTML
#         - Use ONLY the provided content (no filler text)
#     """
#
#     # Convert QnA dict to JSON for clarity in prompt
#     structured_content = json.dumps(qna_data, indent=2)
#
#     prompt = f"""
# You are an expert front-end designer and HTML/CSS generator.
# Your task is to generate a SINGLE-PAGE responsive personal portfolio website in pure HTML with inline CSS.
#
# INPUT CONTENT:
# {structured_content}
#
# STRUCTURE REQUIRED:
# Sections to include (in this order):
# 1. Home (hero intro with name, role, short tagline)
# 2. About (brief professional bio + skills)
# 3. Resume (download button using provided resume_link)
# 4. Projects (interactive cards or grid)
# 5. Contact (simple section with email & links)
#
# REQUIREMENTS:
# 1. Return ONLY raw HTML code — no markdown, explanations, comments, triple backticks, or "html\\n" prefixes.
# 2. The output must start with "<!DOCTYPE html>" and end with "</html>".
# 3. All styles must be included in a <style> block inside the <head> (no external CSS or JS files).
# 4. Layout must be fully responsive and mobile-friendly.
# 5. Apply a clean, minimal design (whitespace, simple color palette, soft shadows, modern typography).
# 6. Let the model automatically choose an appropriate font and harmonious color palette.
# 7. Include subtle interactive behavior — e.g., smooth scroll, hover effects, mobile menu toggle.
# 8. Include a favicon placeholder link in the <head>.
# 9. Add <meta> tags for SEO and social preview (title, description, keywords, og:title, og:description, og:type, og:image placeholder).
# 10. Ensure semantic HTML and accessibility standards.
# 11. Optimize for browser compatibility and responsiveness.
# 12. Use "Download Resume" button with the provided resume_link.
# 13. Include sample project cards with title, description, and "View Project" button using provided projects.
# 14. Use only the input content for all text — no extra filler biography.
# 15. Output clean, export-ready HTML starting with <!DOCTYPE html> and ending with </html>.
# """
#
#     # --- GROQ LLM integration ---
#     client = Groq(api_key=os.getenv("GROQ_API_KEY"))
#     response = client.chat.completions.create(
#         model="openai/gpt-oss-20b",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.6,
#         max_tokens=6000
#     )
#
#     html_content = response.choices[0].message.content.strip()
#
#     # Safety: ensure output starts/ends with proper HTML tags
#     if not html_content.startswith("<!DOCTYPE html>"):
#         html_content = "<!DOCTYPE html>" + html_content.split("<!DOCTYPE html>")[-1]
#     if "</html>" not in html_content:
#         html_content += "</html>"
#
#     return html_content

def generate_portfolio_from_qna(qna_data: dict) -> str:
    """
    Generate a SINGLE-PAGE responsive portfolio HTML using structured QnA input.

    Requirements:
        - Fully responsive layout
        - Inline CSS
        - Modern fonts & harmonious color palette
        - SEO meta tags
        - Browser-compatible HTML
        - Only use provided content; no filler text
    """
    structured_content = json.dumps(qna_data, indent=2)

    prompt = f"""
You are an expert front-end designer and HTML/CSS developer. 
Your task: Generate a SINGLE-PAGE personal portfolio website in pure HTML with inline CSS.

INPUT CONTENT:
{structured_content}

SECTIONS TO INCLUDE (in this order):
1. Home: Hero section with full name, role, tagline; centered, prominent, visually striking.
2. About: Professional bio and skills; show technical skills as bars or badges, soft skills as tags or icons.
3. Projects: Responsive grid of project cards with title, description, 'View Project' button; hover effects encouraged.
4. Experience: Timeline or card list showing role, company, duration, description.
5. Education: Simple, readable list of degrees and institutions.
6. Contact: Email, LinkedIn, GitHub, Twitter links; clickable icons.

DESIGN & FUNCTIONAL REQUIREMENTS:
- Use inline CSS only; no external files.
- Fully responsive: desktop, tablet, mobile.
- Modern minimal aesthetic with whitespace, subtle shadows, and soft color palette.
- Choose appropriate Google-font-like fonts.
- Subtle interactive effects: hover highlights, smooth scroll, mobile menu toggle.
- Include favicon placeholder and meta tags for SEO and social preview:
  - title, description, keywords
  - og:title, og:description, og:type, og:image placeholder
- Semantic HTML5, accessible elements (alt tags, ARIA where needed).
- Use only content provided; no extra filler.
- Clean export-ready HTML, starting with "<!DOCTYPE html>" and ending with "</html>".
"""

    # --- GROQ LLM integration ---
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=6000
    )

    html_content = response.choices[0].message.content.strip()

    # Safety: ensure output starts/ends with proper HTML tags
    if not html_content.startswith("<!DOCTYPE html>"):
        html_content = "<!DOCTYPE html>" + html_content.split("<!DOCTYPE html>")[-1]
    if "</html>" not in html_content:
        html_content += "</html>"

    return html_content

def get_file_type(user):
    """
    Determines the file type of the user's uploaded resume.

    Args:
        user: Django user instance with a 'resume_file' attribute.

    Returns:
        file_type (str): 'pdf' or 'docx'

    Raises:
        ValueError: If the file type is unsupported.
    """
    file_path = user.resume_file.path if hasattr(user.resume_file, 'path') else user.resume_file
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == '.pdf':
        return file_path, 'pdf'
    elif ext in ['.doc', '.docx']:
        return file_path, 'docx'
    else:
        raise ValueError("Unsupported file type")