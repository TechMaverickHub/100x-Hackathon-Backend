# PortfolioAI PRD

## Abstract
PortfolioAI is a web-based suite that empowers engineers and career-switchers to build a standout portfolio, résumé, and cover letter within minutes, receive real-time optimization and AI-driven job prep, and discover curated job openings. The product is optimized for hackathon delivery with speed and API-driven architecture.

## Business Objectives
- Reduce time and friction for users to become job-ready
- Increase number of engineers moving from discovery to job application
- Demonstrate advanced AI integration for rapid, personalized career support

## KPI

| GOAL            | METRIC            | QUESTION                                  |
|-----------------|-------------------|--------------------------------------------|
| New User Growth | # Signups         | How many engineers register during v1?     |
| Engagement      | Applications sent | How many job applications are initiated?   |
| Retention       | D7 Retention      | What % return within their first week?     |

## Success Criteria
- At least 50% of signups generate a hosted portfolio and send one application
- AI feature demos are completed without critical errors
- Positive feedback from hackathon judges/users

## User Journeys
- An engineer uploads a résumé or answers questions, reviews their AI-built site, receives optimization feedback, and applies for jobs directly.
- A career-switcher starts without a résumé, gets an AI-generated one, then builds a portfolio and cover letter, and receives interview coaching.

## Scenarios
- First-time job seeker generates and exports résumé and portfolio in a single session.
- User receives a job alert, clicks “apply,” and portfolio and résumé are attached.
- User requests real-time CV/portfolio optimization targeting a specific job post.
- User completes a mock interview with AI feedback.

## User Flow
- User signs up/logs in
- Chooses input: Upload résumé or guided Q&A
- AI generates portfolio, résumé, and cover letter
- User reviews/edits output, receives optimization suggestions
- User subscribes to job alerts, chooses sources and keywords
- User receives alert, applies with profile in one click
- Optional: User books AI mock interview/receives coaching

## Functional Requirements

| SECTION         | SUB-SECTION            | USER STORY & EXPECTED BEHAVIORS                                                                                            | SCREENS        |
|-----------------|------------------------|----------------------------------------------------------------------------------------------------------------------------|----------------|
| Signup          | Email                  | User creates account via email with confirmation, then proceeds to upload or Q&A.                                           | TBD            |
| Login           | Email                  | User logs in, resumes previous session, can access saved portfolios and results.                                            | TBD            |
| Portfolio       | QnA, Résumé upload     | User can generate a site from résumé or by answering questions, receives hosted site + downloadable HTML.                    | TBD            |
| Résumé          | CV generation, rewrite | User can generate or optimize résumé, see score/gap vs job description, and download ATS-ready doc.                         | TBD            |
| Cover Letter    | Auto                   | User generates job-specific letter auto-filled with portfolio data, can edit tone, and downloads or copies output.           | TBD            |
| Job Alerts      | Custom sources         | User submits keywords and sources to receive matching jobs via email and app, with “apply with profile” shortcut.            | TBD            |
| Mock Interview  | AI Interviewer         | User takes a simulated interview with real-time feedback, transcript, and scoring.                                          | TBD            |

## Model Requirements

| SPECIFICATION        | REQUIREMENT           | RATIONALE                                             |
|----------------------|----------------------|-------------------------------------------------------|
| Open vs Proprietary  | Open or Hackathon API| Rapid integration, demo focus                         |
| Context Window       | 8-16k tokens         | For résumé parsing and Q&A long answers               |
| Modalities           | Text only            | Simplicity, demo focus                                |
| Fine Tuning          | None (assumption)    | Limited time/resources                                |
| Latency              | <5s P50, <10s P95    | To keep user flow smooth                              |
| Parameters           | Hackathon default    | Minimize setup                                        |

## Data Requirements
- All user data is from uploads, Q&A, or input
- No PII retention outside user session (assumption)
- No external scraping except user-supplied job source links
- No ongoing collection/fine tuning for v1

## Prompt Requirements
- AI prompts produce concise, ATS-friendly documents
- Tone can be formal or user-edited
- JSON or plain text output, no hallucinated sections
- Policy reminders for content boundaries (assumption)

## Testing & Measurement
- Manual demo flows for each feature (QA by team)
- Golden path checks for signups, doc generation, job alert, interview sim
- Live bug list tracked by team
- At least 3 user flow tests per feature

## Risks & Mitigations

| RISK                | MITIGATION                           |
|---------------------|--------------------------------------|
| Code issues         | Limit scope, use working endpoints    |
| AI output off-target| Provide manual edit/review step       |
| Integration failure | Stagger features, fallback flows      |

## Costs
- Development: Team hours only, as for hackathon
- Ops: None anticipated for MVP (demo infra only, assumption)

## Assumptions & Dependencies
- APIs listed are operational and accessible
- All AI features run via supplied endpoints
- Webapp only; no mobile
- No live user data outside demos
- Hackathon duration is <7 days

## Compliance/Privacy/Legal
- User data is ephemeral, deleted post-demo (assumption)
- No external compliance requirements for hackathon

## GTM/Rollout Plan
- Internal demo for hackathon judges
- Blog post or demo video after event
- No phased rollout; immediate full demo at hackathon
