"""Certificate transparency log search via crt.sh."""

import json
from datetime import datetime, timezone

from core import database, http_client
from core.config import CRT_SH_URL
from models.osint import CertEntry, CertResult


def fetch_certs(domain: str, wildcard: bool = True) -> CertResult:
    """Search crt.sh for certificate transparency records for a domain."""
    query = f"%.{domain}" if wildcard else domain
    try:
        resp = http_client.get(
            CRT_SH_URL,
            params={"q": query, "output": "json"},
            source="crt.sh",
            timeout=30,
        )
        data = resp.json()
        entries: list[CertEntry] = []
        seen_ids: set[str] = set()
        for item in data:
            cert_id = str(item.get("id", ""))
            if cert_id in seen_ids:
                continue
            seen_ids.add(cert_id)
            # SAN names (name_value may contain newline-separated names)
            san_names_raw = item.get("name_value", "")
            san_names = [s.strip() for s in san_names_raw.split("\n") if s.strip()]
            entries.append(CertEntry(
                domain=domain,
                cert_id=cert_id,
                issuer=item.get("issuer_name"),
                common_name=item.get("common_name"),
                san_names=san_names,
                not_before=item.get("not_before"),
                not_after=item.get("not_after"),
            ))
        _save(entries)
        return CertResult(domain=domain, entries=entries)
    except Exception as e:
        return CertResult(domain=domain, error=str(e))


def _save(entries: list[CertEntry]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            e.domain, e.cert_id, e.issuer, e.common_name,
            json.dumps(e.san_names), e.not_before, e.not_after, now,
        )
        for e in entries
    ]
    database.execute_many(
        """INSERT OR IGNORE INTO cert_transparency
        (domain, cert_id, issuer, common_name, san_names, not_before, not_after, collected_at)
        VALUES (?,?,?,?,?,?,?,?)""",
        rows,
    )
