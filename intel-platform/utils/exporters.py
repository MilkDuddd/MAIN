"""Export intelligence results to JSON, CSV, and Markdown formats."""

import csv
import json
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core import settings


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def to_json(data: Any, filename: Optional[str] = None) -> Path:
    """Export data to a JSON file in the output directory."""
    from typing import Optional
    out_dir = settings.output_dir()
    fname = filename or f"intel_{_timestamp()}.json"
    path = out_dir / fname
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def to_csv(rows: list[dict], filename: Optional[str] = None) -> Path:
    """Export a list of dicts to CSV."""
    from typing import Optional
    out_dir = settings.output_dir()
    fname = filename or f"intel_{_timestamp()}.csv"
    path = out_dir / fname
    if not rows:
        path.write_text("")
        return path
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def to_markdown(title: str, sections: dict[str, str], filename: Optional[str] = None) -> Path:
    """Export a structured report to Markdown."""
    from typing import Optional
    out_dir = settings.output_dir()
    fname = filename or f"intel_report_{_timestamp()}.md"
    path = out_dir / fname
    lines = [
        f"# {title}",
        f"*Generated: {datetime.now(timezone.utc).isoformat()}*",
        "",
    ]
    for heading, content in sections.items():
        lines.append(f"## {heading}")
        lines.append(content)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def entity_report(entity_name: str, profile) -> Path:
    """Generate a full Markdown entity intelligence report."""
    sections: dict[str, str] = {}

    # Identity
    e = profile.entity
    sections["Entity Overview"] = (
        f"**Name:** {e.canonical_name}  \n"
        f"**Type:** {e.entity_type}  \n"
        f"**Aliases:** {', '.join(e.aliases) or 'None'}  \n"
        f"**Data Sources:** {', '.join(e.source_modules) or 'None'}  \n"
    )

    # Sanctions
    if profile.sanctions:
        lines = ["| List | Type | Nationality | DOB | Programs |", "|------|------|-------------|-----|----------|"]
        for s in profile.sanctions:
            lines.append(f"| {s.list_source} | {s.entity_type or '—'} | {s.nationality or '—'} | {s.date_of_birth or '—'} | {', '.join(s.programs[:3])} |")
        sections["Sanctions"] = "\n".join(lines)

    # Donations
    if profile.donations:
        lines = ["| Donor | Recipient | Party | Amount | Date |", "|-------|-----------|-------|--------|------|"]
        for d in profile.donations[:20]:
            amt = f"${d.amount_usd:,.0f}" if d.amount_usd else "—"
            lines.append(f"| {d.donor_name} | {d.recipient_name} | {d.recipient_party or '—'} | {amt} | {d.transaction_date or '—'} |")
        sections["Political Donations"] = "\n".join(lines)

    # Board roles
    if profile.board_roles:
        lines = ["| Person | Company | Role | Start | End |", "|--------|---------|------|-------|-----|"]
        for b in profile.board_roles:
            lines.append(f"| {b.person_name} | {b.company_name} | {b.role or '—'} | {b.start_date or '—'} | {b.end_date or 'Present'} |")
        sections["Board Memberships"] = "\n".join(lines)

    # AI summary
    if profile.ai_summary:
        sections["AI Analysis"] = profile.ai_summary

    return to_markdown(f"Intel Report: {entity_name}", sections)
