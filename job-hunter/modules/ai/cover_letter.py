"""AI cover letter generator using Claude (Anthropic)."""

from __future__ import annotations
import json


def generate_cover_letter(
    api_key: str,
    profile: dict,
    role: str,
    company: str,
    tone: str = "Professional",
    length: str = "Medium (3 paragraphs)",
    job_description: str = "",
) -> str:
    import anthropic

    length_map = {
        "Short (1 paragraph)": "one concise paragraph (100-150 words)",
        "Medium (3 paragraphs)": "three paragraphs (250-350 words)",
        "Long (5 paragraphs)": "five paragraphs (450-550 words)",
    }
    length_desc = length_map.get(length, "three paragraphs")

    skills = ", ".join(profile.get("skills_list") or []) or profile.get("skills", "") or "various technical skills"

    experience_lines = []
    for exp in (profile.get("experience") or [])[:3]:
        end = "Present" if exp.get("current") else (exp.get("end_date") or "")
        experience_lines.append(f"- {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('start_date', '')}–{end})")

    education_lines = []
    for edu in (profile.get("education") or [])[:2]:
        education_lines.append(f"- {edu.get('degree', '')} in {edu.get('field_of_study', '')} from {edu.get('institution', '')}")

    jd_section = f"\n\nJob Description / Requirements:\n{job_description[:1500]}" if job_description.strip() else ""

    prompt = f"""Write a cover letter for the following job application.

Applicant Profile:
- Name: {profile.get('name', '')}
- Headline: {profile.get('headline', '')}
- Summary: {profile.get('summary', '')}
- Key Skills: {skills}
- Recent Experience:
{chr(10).join(experience_lines) if experience_lines else '  (none listed)'}
- Education:
{chr(10).join(education_lines) if education_lines else '  (none listed)'}

Target Role: {role}
Target Company: {company}
Tone: {tone}
Length: {length_desc}
{jd_section}

Instructions:
- Write the cover letter body only (no "Dear Hiring Manager" header, no sign-off line)
- Be specific and concrete; avoid generic buzzwords
- Match tone to '{tone}'
- Highlight the most relevant experience and skills for this role
- Keep it to {length_desc}
- Do NOT include placeholder brackets like [Your Name] — write the actual content
"""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def tailor_resume_snippet(
    api_key: str,
    profile: dict,
    job_description: str,
    section: str = "summary",
) -> str:
    import anthropic

    section_map = {
        "summary": "professional summary / headline",
        "skills": "skills section highlighting the most relevant skills",
        "experience": "bullet points for the most recent job experience",
    }

    prompt = f"""Given this job description:

{job_description[:2000]}

And this candidate profile:
Name: {profile.get('name', '')}
Current Summary: {profile.get('summary', '')}
Skills: {', '.join(profile.get('skills_list') or [])}

Write a tailored {section_map.get(section, section)} that would resonate with this job posting.
Be concise and impactful. Return only the text, no labels or headers."""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def score_job_fit(
    api_key: str,
    profile: dict,
    job: dict,
) -> dict:
    """Returns a fit score and brief explanation."""
    import anthropic

    prompt = f"""Rate how well this candidate fits this job on a scale of 0-100.

Candidate:
- Title/Headline: {profile.get('headline', '')}
- Skills: {', '.join(profile.get('skills_list') or [])}
- Experience: {len(profile.get('experience') or [])} positions

Job:
- Title: {job.get('title', '')}
- Company: {job.get('company', '')}
- Description: {(job.get('description') or '')[:500]}

Respond with JSON only: {{"score": <0-100>, "reason": "<one sentence>"}}"""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        return json.loads(message.content[0].text)
    except Exception:
        return {"score": 50, "reason": "Unable to parse response."}
