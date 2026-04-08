"""SEC EDGAR — US financial filings, insider trading, beneficial ownership."""
import json
from datetime import datetime, timezone
from typing import Optional

from core import database
from core.config import SEC_EDGAR_SEARCH, SEC_EDGAR_CIK
from core.http_client import get


def search_filings(query: str, form_type: Optional[str] = None,
                   days_back: int = 365, limit: int = 40) -> list[dict]:
    """Full-text search SEC EDGAR filings."""
    from datetime import timedelta
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days_back)
    params: dict = {
        "q": query,
        "dateRange": "custom",
        "startdt": str(start),
        "enddt": str(end),
        "hits.hits.total.value": "true",
        "_source": "period_of_report,entity_name,file_date,form_type,accession_no",
    }
    if form_type:
        params["forms"] = form_type
    results = []
    try:
        resp = get(SEC_EDGAR_SEARCH, params=params, timeout=20)
        data = resp.json() if resp.status_code == 200 else {}
        hits = data.get("hits", {}).get("hits", [])
        for h in hits[:limit]:
            src = h.get("_source", {})
            results.append({
                "accession_no": h.get("_id", ""),
                "cik": src.get("entity_id", ""),
                "company_name": src.get("entity_name", ""),
                "form_type": src.get("form_type", ""),
                "filed_date": src.get("file_date", ""),
                "period_of_report": src.get("period_of_report", ""),
                "description": src.get("biz_description", ""),
                "document_url": f"https://www.sec.gov/Archives/edgar/data/{src.get('entity_id','')}/{h.get('_id','').replace('-','')}/",
                "full_text_snippet": "",
            })
    except Exception:
        pass
    return results


def search_and_store(query: str, form_type: Optional[str] = None, days_back: int = 365) -> list[dict]:
    """Search EDGAR, store results, return list."""
    results = search_filings(query, form_type=form_type, days_back=days_back)
    if not results:
        return results
    now = datetime.now(timezone.utc).isoformat()
    for r in results:
        database.execute_write(
            """INSERT OR IGNORE INTO sec_filings
               (accession_no, cik, company_name, form_type, filed_date, period_of_report,
                description, document_url, full_text_snippet, collected_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (r["accession_no"], r["cik"], r["company_name"], r["form_type"],
             r["filed_date"], r["period_of_report"], r["description"],
             r["document_url"], r["full_text_snippet"], now),
        )
    return results


def insider_trading(name: str) -> list[dict]:
    """Search Form 4 (insider trading) filings by person name."""
    return search_filings(name, form_type="4", days_back=730)


def search_db(query: str) -> list[dict]:
    rows = database.execute(
        "SELECT * FROM sec_filings WHERE company_name LIKE ? OR description LIKE ? ORDER BY filed_date DESC LIMIT 100",
        (f"%{query}%", f"%{query}%"),
    )
    return [dict(r) for r in rows]
