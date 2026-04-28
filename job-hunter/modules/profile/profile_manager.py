"""Profile manager — retrieves profile data formatted for use in applications."""

from __future__ import annotations
import json
from typing import Optional

from core.database import execute


def get_profile(profile_id: int) -> Optional[dict]:
    rows = execute("SELECT * FROM profiles WHERE id=?", (profile_id,))
    if not rows:
        return None
    p = dict(rows[0])
    try:
        p["skills_list"] = json.loads(p.get("skills") or "[]")
        p["desired_roles_list"] = json.loads(p.get("desired_roles") or "[]")
    except Exception:
        p["skills_list"] = []
        p["desired_roles_list"] = []
    p["experience"] = get_experience(profile_id)
    p["education"] = get_education(profile_id)
    p["certifications"] = get_certifications(profile_id)
    return p


def get_experience(profile_id: int) -> list[dict]:
    rows = execute("SELECT * FROM work_experience WHERE profile_id=? ORDER BY sort_order, id DESC", (profile_id,))
    result = []
    for row in rows:
        e = dict(row)
        try:
            e["achievements_list"] = json.loads(e.get("achievements") or "[]")
            e["technologies_list"] = json.loads(e.get("technologies") or "[]")
        except Exception:
            e["achievements_list"] = []
            e["technologies_list"] = []
        result.append(e)
    return result


def get_education(profile_id: int) -> list[dict]:
    return [dict(r) for r in execute("SELECT * FROM education WHERE profile_id=? ORDER BY sort_order, id DESC", (profile_id,))]


def get_certifications(profile_id: int) -> list[dict]:
    return [dict(r) for r in execute("SELECT * FROM certifications WHERE profile_id=? ORDER BY id DESC", (profile_id,))]


def format_resume_text(profile: dict) -> str:
    lines = []
    lines.append(f"{profile.get('name', '')}")
    lines.append(f"{profile.get('email', '')}  |  {profile.get('phone', '')}  |  {profile.get('location', '')}")
    if profile.get("linkedin_url"):
        lines.append(profile["linkedin_url"])
    lines.append("")

    if profile.get("headline"):
        lines.append(profile["headline"])
        lines.append("")

    if profile.get("summary"):
        lines.append("SUMMARY")
        lines.append(profile["summary"])
        lines.append("")

    if profile.get("skills_list"):
        lines.append("SKILLS")
        lines.append(", ".join(profile["skills_list"]))
        lines.append("")

    if profile.get("experience"):
        lines.append("EXPERIENCE")
        for exp in profile["experience"]:
            end = "Present" if exp.get("current") else (exp.get("end_date") or "")
            lines.append(f"{exp['title']} — {exp['company']}  ({exp.get('start_date', '')} – {end})")
            if exp.get("description"):
                lines.append(exp["description"])
            lines.append("")

    if profile.get("education"):
        lines.append("EDUCATION")
        for edu in profile["education"]:
            lines.append(f"{edu.get('degree', '')} in {edu.get('field_of_study', '')} — {edu['institution']}  ({edu.get('start_date', '')} – {edu.get('end_date', '')})")
        lines.append("")

    return "\n".join(lines)
