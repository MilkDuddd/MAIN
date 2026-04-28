"""Shared utility functions."""

from __future__ import annotations
import re


def parse_salary(text: str) -> tuple[int | None, int | None]:
    if not text:
        return None, None
    nums = re.findall(r"\$?([\d,]+)(?:k|K)?", text)
    values = []
    for n in nums:
        val = int(n.replace(",", ""))
        if "k" in text.lower() and val < 1000:
            val *= 1000
        values.append(val)
    if len(values) >= 2:
        return min(values), max(values)
    if len(values) == 1:
        return values[0], None
    return None, None


def truncate(text: str, max_len: int = 100) -> str:
    if not text:
        return ""
    return text[:max_len] + "…" if len(text) > max_len else text


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
