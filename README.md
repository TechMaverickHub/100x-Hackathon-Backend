# PortfolioAI — Instant Personal Brand & Job-Readiness Suite

## Problem
Early-career engineers and career-switchers often face challenges such as:

- Lack of a polished online presence, spending days struggling with portfolios, résumés, and cover letters.
- Generic job alerts that bury the few perfect openings in a flood of noise.
- Ad-hoc interview preparation, leaving candidates unsure of real-world expectations.

## Solution
PortfolioAI is an AI-driven web application that transforms raw inputs (existing CV, LinkedIn URL, or a short Q&A) into:

- A fully hosted portfolio site
- ATS-ready résumé
- Tailored cover letters
- Personalized job alerts

It also provides an AI interviewer that offers real-time coaching and feedback.

## Scope / Features

### 1. AI Portfolio Builder
- Accepts PDF/Word résumé or guided Q&A to generate a responsive, host-ready portfolio site.
- Supports custom subdomains and exportable HTML for full control.

### 2. AI CV Generator
- Collects work history, skills, and metrics through dynamic interview prompts when no résumé exists.
- Outputs ATS-friendly PDF or DOCX résumés.

### 3. AI Cover-Letter Writer
- Generates job-specific letters using role descriptions + user portfolio data.
- Includes editable tone presets for personalization.

### 4. Résumé / Portfolio Optimizer
- Real-time scoring and keyword gap analysis against target job descriptions.
- Provides auto-rewrite suggestions to improve impact.

### 5. AI Mock Interviewer
- Role-aware question sets (technical, behavioral) with live transcripts.
- Tracks confidence metrics and gives actionable improvement tips.

### 6. Career Coaching & Skill Gap Analysis
- Personalized AI-driven career guidance based on portfolio and job targets.

### 7. Job-Opening Alert Engine
- Users select sources (LinkedIn, AngelList, Wellfound, company RSS, etc.), keywords, and alert frequency.
- Delivers notifications via email & in-app, with an 'Apply-with-Profile' shortcut.


## 🚀 Getting Started

### 🔁 1. Clone the Repository

```bash
git clone https://github.com/TechMaverickHub/100x-Hackathon-Backend.git
cd 100x-Hackathon-Backend

---

### 🐍 2. Create a Virtual Environment

```bash
# Linux/macOS
python3 -m venv env
source env/bin/activate

# Windows
python -m venv env
env\Scripts\activate
```

---

### 📦 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Setup

Create a `.env` file in the project root:

```env
DATABASE_NAME=
DATABASE_USER=
DATABASE_PASS=
DATABASE_HOST=
DATABASE_PORT=
DEBUG=TRUE

GROQ_API_KEY=
RESEND_API_KEY=
```

---

## 🗃️ Database Setup

### 🔧 Make Migrations

```bash
python manage.py makemigrations user
python manage.py makemigrations role

```

### ⚙️ Apply Migrations

```bash
python manage.py migrate
```

### 📥 Load Initial Data

```bash
python manage.py loaddata app/role/fixtures/roles.json

```

---

## 🧪 Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

Access the API at:  
👉 `http://localhost:8000/`

---

## 📚 API Documentation

Interactive Swagger docs available at:  
`http://localhost:8000/swagger/`

---

---

**PortfolioAI** streamlines job readiness for engineers, turning hours of work into minutes.
