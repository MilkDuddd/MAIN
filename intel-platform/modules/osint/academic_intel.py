"""OpenAlex — academic/scientific paper intelligence, author affiliations, funding."""
import json
from datetime import datetime, timezone
from typing import Optional

from core import database
from core.config import OPENALEX_API
from core.http_client import get

# Use polite pool with email header (optional but recommended)
_HEADERS = {"User-Agent": "IntelPlatform/2.0 (research; contact@example.com)"}


def search_papers(query: str, author: Optional[str] = None,
                  institution: Optional[str] = None, limit: int = 25) -> list[dict]:
    """Search academic papers via OpenAlex."""
    params: dict = {
        "search": query,
        "per-page": min(limit, 50),
        "select": "id,title,authorships,publication_year,primary_location,doi,abstract_inverted_index,cited_by_count,grants",
    }
    if author:
        params["filter"] = f"author.display_name.search:{author}"
    if institution:
        params["filter"] = f"authorships.institutions.display_name.search:{institution}"

    papers = []
    try:
        resp = get(f"{OPENALEX_API}/works", params=params, headers=_HEADERS, timeout=20)
        if resp.status_code != 200:
            return papers
        data = resp.json()
        for work in data.get("results", []):
            authors_list = []
            institutions_set = set()
            for auth in work.get("authorships", []):
                name = auth.get("author", {}).get("display_name", "")
                insts = [i.get("display_name", "") for i in auth.get("institutions", [])]
                authors_list.append({"name": name, "institutions": insts})
                institutions_set.update(insts)

            # Reconstruct abstract from inverted index if present
            abstract = ""
            inv = work.get("abstract_inverted_index")
            if inv:
                try:
                    max_pos = max(p for positions in inv.values() for p in positions)
                    words = [""] * (max_pos + 1)
                    for word, positions in inv.items():
                        for pos in positions:
                            words[pos] = word
                    abstract = " ".join(words)[:1000]
                except Exception:
                    pass

            funding_sources = [g.get("funder_display_name", "") for g in work.get("grants", [])]
            journal = (work.get("primary_location") or {}).get("source", {})
            journal_name = journal.get("display_name", "") if journal else ""

            papers.append({
                "paper_id": work.get("id", "").replace("https://openalex.org/", ""),
                "title": work.get("title", ""),
                "authors": json.dumps(authors_list),
                "institutions": json.dumps(list(institutions_set)),
                "publication_year": work.get("publication_year"),
                "journal": journal_name,
                "doi": work.get("doi", ""),
                "abstract": abstract,
                "cited_by_count": work.get("cited_by_count", 0),
                "funding_sources": json.dumps(funding_sources),
                "open_access_url": (work.get("primary_location") or {}).get("landing_page_url", ""),
            })
    except Exception:
        pass
    return papers


def search_and_store(query: str, author: Optional[str] = None,
                     institution: Optional[str] = None) -> list[dict]:
    papers = search_papers(query, author=author, institution=institution)
    if not papers:
        return papers
    now = datetime.now(timezone.utc).isoformat()
    for p in papers:
        database.execute_write(
            """INSERT OR IGNORE INTO academic_papers
               (paper_id, title, authors, institutions, publication_year, journal, doi,
                abstract, cited_by_count, funding_sources, open_access_url, collected_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (p["paper_id"], p["title"], p["authors"], p["institutions"],
             p["publication_year"], p["journal"], p["doi"], p["abstract"],
             p["cited_by_count"], p["funding_sources"], p["open_access_url"], now),
        )
    return papers


def search_db(query: str) -> list[dict]:
    rows = database.execute(
        "SELECT * FROM academic_papers WHERE title LIKE ? OR authors LIKE ? OR institutions LIKE ? ORDER BY cited_by_count DESC LIMIT 50",
        (f"%{query}%", f"%{query}%", f"%{query}%"),
    )
    return [dict(r) for r in rows]
