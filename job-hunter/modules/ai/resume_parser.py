"""AI-powered resume parser — extracts structured profile data from resume text."""

from __future__ import annotations
import json
import re


def parse_resume(api_key: str, resume_text: str) -> dict:
    """
    Send resume text to Claude and get back structured profile data.

    Returns a dict with keys:
        name, email, phone, location, linkedin_url, github_url,
        portfolio_url, headline, summary, skills (list), desired_roles (list),
        experience (list of dicts), education (list of dicts)
    """
    import anthropic

    prompt = f"""You are a resume parser. Extract structured data from the resume below and return ONLY valid JSON with no commentary, no markdown fences, no extra text.

Return exactly this JSON structure (use empty string "" for missing text fields, empty list [] for missing list fields, false for missing booleans):

{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+1 555-000-0000",
  "location": "City, State",
  "linkedin_url": "https://linkedin.com/in/...",
  "github_url": "https://github.com/...",
  "portfolio_url": "",
  "headline": "Short professional title/headline",
  "summary": "2-3 sentence professional summary",
  "skills": ["Skill1", "Skill2", "Skill3"],
  "desired_roles": [],
  "experience": [
    {{
      "company": "Company Name",
      "title": "Job Title",
      "location": "City, State or Remote",
      "start_date": "Mon YYYY",
      "end_date": "Mon YYYY",
      "current": false,
      "description": "Key responsibilities and achievements in 2-4 sentences."
    }}
  ],
  "education": [
    {{
      "institution": "University Name",
      "degree": "B.S.",
      "field_of_study": "Computer Science",
      "start_date": "YYYY",
      "end_date": "YYYY",
      "gpa": ""
    }}
  ]
}}

Rules:
- Extract ALL work experience entries, most recent first
- For current positions, set end_date to "" and current to true
- Extract ALL education entries
- Skills should be a flat list of individual skills (not categories)
- If a field isn't present in the resume, use "" or []
- Return ONLY the JSON object, nothing else

Resume:
{resume_text[:6000]}"""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()

    # Strip any accidental markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    parsed = json.loads(raw)

    # Ensure required keys exist with safe defaults
    defaults = {
        "name": "", "email": "", "phone": "", "location": "",
        "linkedin_url": "", "github_url": "", "portfolio_url": "",
        "headline": "", "summary": "", "skills": [], "desired_roles": [],
        "experience": [], "education": [],
    }
    for k, v in defaults.items():
        parsed.setdefault(k, v)

    return parsed
