#!/usr/bin/env python3
"""
Intel Platform — OSINT/SIGINT/Geopolitical Intelligence CLI
Usage: python main.py [command] [subcommand] [options]
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click
from rich.console import Console
from rich.markdown import Markdown

from core import database, settings as cfg
from utils import formatters

console = Console()


# ── Root group ────────────────────────────────────────────────────────────────

@click.group()
@click.version_option("2.1.0", prog_name="Intel Platform")
def cli():
    """Intel Platform — OSINT/SIGINT/Geopolitical Intelligence System."""
    database.init_db()
    # Seed static datasets on first run
    _seed_static_data()


def _seed_static_data():
    """Load static curated datasets into DB on first run."""
    try:
        from modules.uap.congress_uap import populate_db as seed_hearings
        from modules.uap.declassified import populate_db as seed_docs
        from modules.uap.faa_reports import populate_db as seed_faa
        seed_hearings()
        seed_docs()
        seed_faa()
    except Exception:
        pass


# ── OSINT commands ─────────────────────────────────────────────────────────────

@cli.group()
def osint():
    """Open Source Intelligence — domain, person, and org profiling."""


@osint.command("whois")
@click.argument("domain")
def osint_whois(domain: str):
    """WHOIS registration lookup for a domain."""
    from modules.osint.whois_dns import fetch_whois
    with console.status(f"[cyan]WHOIS lookup: {domain}...[/cyan]"):
        result = fetch_whois(domain)
    if result.error:
        formatters.error_panel(result.error, "WHOIS Error")
        return
    content = (
        f"[bold]Domain:[/bold] {result.domain}\n"
        f"[bold]Registrar:[/bold] {result.registrar or '—'}\n"
        f"[bold]Registrant:[/bold] {result.registrant_name or '—'} / {result.registrant_org or '—'}\n"
        f"[bold]Email:[/bold] {result.registrant_email or '—'}\n"
        f"[bold]Country:[/bold] {result.registrant_country or '—'}\n"
        f"[bold]Created:[/bold] {result.created_date or '—'}\n"
        f"[bold]Expires:[/bold] {result.expiry_date or '—'}\n"
        f"[bold]Name Servers:[/bold] {', '.join(result.name_servers[:4]) or '—'}"
    )
    from rich.panel import Panel
    console.print(Panel(content, title=f"[bold cyan]WHOIS: {domain}[/bold cyan]", border_style="cyan"))


@osint.command("dns")
@click.argument("domain")
@click.option("--types", default="A,AAAA,MX,TXT,NS", help="Comma-separated record types")
def osint_dns(domain: str, types: str):
    """DNS record enumeration for a domain."""
    from modules.osint.whois_dns import fetch_dns
    from rich.table import Table
    record_types = [t.strip().upper() for t in types.split(",")]
    with console.status(f"[cyan]DNS enumeration: {domain}...[/cyan]"):
        result = fetch_dns(domain, record_types)
    if result.error:
        formatters.error_panel(result.error)
        return
    t = Table(title=f"DNS Records: {domain}", show_lines=True)
    t.add_column("Type", style="cyan", width=8)
    t.add_column("Value", style="white")
    t.add_column("TTL", style="dim", width=8)
    for r in result.records:
        t.add_row(r.record_type, r.value, str(r.ttl) if r.ttl else "—")
    console.print(t)
    console.print(f"[dim]{len(result.records)} records found[/dim]")


@osint.command("certs")
@click.argument("domain")
@click.option("--no-wildcard", is_flag=True, help="Exact match only")
def osint_certs(domain: str, no_wildcard: bool):
    """Certificate transparency log search (crt.sh)."""
    from modules.osint.cert_transparency import fetch_certs
    from rich.table import Table
    with console.status(f"[cyan]Searching crt.sh for {domain}...[/cyan]"):
        result = fetch_certs(domain, wildcard=not no_wildcard)
    if result.error:
        formatters.error_panel(result.error)
        return
    t = Table(title=f"Certificates: {domain} ({len(result.entries)} found)", show_lines=True)
    t.add_column("ID", style="dim", width=12)
    t.add_column("Common Name", style="cyan")
    t.add_column("Issuer", style="yellow")
    t.add_column("Not Before", style="dim", width=12)
    t.add_column("Not After", style="dim", width=12)
    t.add_column("SANs", style="white")
    for e in result.entries[:50]:
        t.add_row(
            (e.cert_id or "")[:10],
            e.common_name or "—",
            (e.issuer or "")[:40],
            (e.not_before or "")[:10],
            (e.not_after or "")[:10],
            ", ".join(e.san_names[:3]),
        )
    console.print(t)


@osint.command("social")
@click.argument("username")
def osint_social(username: str):
    """Check username presence across social platforms."""
    from modules.osint.social_media import check_username
    from rich.table import Table
    with console.status(f"[cyan]Checking username: {username} across platforms...[/cyan]"):
        result = check_username(username)
    t = Table(title=f"Social Presence: {username}", show_lines=False)
    t.add_column("Platform", style="cyan", width=18)
    t.add_column("Status", width=10)
    t.add_column("URL", style="dim")
    for p in result.platforms:
        status = "[bold green]FOUND[/bold green]" if p.exists else "[dim red]Not found[/dim red]"
        t.add_row(p.platform, status, p.profile_url or "—")
    console.print(t)
    found = sum(1 for p in result.platforms if p.exists)
    console.print(f"[dim]Found on {found}/{len(result.platforms)} platforms[/dim]")


@osint.command("github")
@click.argument("username")
def osint_github(username: str):
    """GitHub profile and repository reconnaissance."""
    from modules.osint.github_recon import fetch_github_profile
    from rich.panel import Panel
    from rich.table import Table
    with console.status(f"[cyan]GitHub recon: {username}...[/cyan]"):
        profile = fetch_github_profile(username)
    if profile.error:
        formatters.error_panel(profile.error)
        return
    content = (
        f"[bold]Name:[/bold] {profile.name or '—'}\n"
        f"[bold]Bio:[/bold] {profile.bio or '—'}\n"
        f"[bold]Company:[/bold] {profile.company or '—'}\n"
        f"[bold]Location:[/bold] {profile.location or '—'}\n"
        f"[bold]Email:[/bold] {profile.email or '—'}\n"
        f"[bold]Followers:[/bold] {profile.followers:,}  "
        f"[bold]Following:[/bold] {profile.following:,}  "
        f"[bold]Repos:[/bold] {profile.public_repos}\n"
        f"[bold]Joined:[/bold] {(profile.created_at or '')[:10]}\n"
        f"[bold]Organizations:[/bold] {', '.join(profile.organizations) or '—'}"
    )
    console.print(Panel(content, title=f"[bold cyan]GitHub: {username}[/bold cyan]", border_style="cyan"))
    if profile.repos:
        t = Table(title="Top Repositories", show_lines=False)
        t.add_column("Repo", style="cyan")
        t.add_column("Language", style="yellow", width=12)
        t.add_column("Stars", style="green", width=7)
        t.add_column("Description", style="dim")
        for r in profile.repos[:15]:
            t.add_row(r["name"], r["language"] or "—", str(r["stars"] or 0), (r["description"] or "")[:60])
        console.print(t)


@osint.command("wayback")
@click.argument("url")
@click.option("--limit", default=40, show_default=True, help="Max snapshots to return")
@click.option("--from-year", "from_year", default=None, help="Start year e.g. 2018")
@click.option("--to-year", "to_year", default=None, help="End year e.g. 2023")
def osint_wayback(url: str, limit: int, from_year, to_year):
    """Wayback Machine snapshot history for a domain or URL."""
    from modules.osint.wayback import fetch_and_store
    from rich.table import Table
    with console.status(f"[cyan]Fetching archive history for {url}...[/cyan]"):
        snapshots = fetch_and_store(url, limit=limit)
    if not snapshots:
        console.print("[yellow]No snapshots found.[/yellow]")
        return
    t = Table(title=f"Wayback Snapshots: {url} ({len(snapshots)} found)", show_lines=False)
    t.add_column("Timestamp", style="dim", width=18)
    t.add_column("Status", width=8)
    t.add_column("MIME Type", style="yellow", width=20)
    t.add_column("Snapshot URL", style="cyan")
    for s in snapshots[:40]:
        ts = s.get("timestamp", "")
        formatted = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[8:10]}:{ts[10:12]}" if len(ts) >= 12 else ts
        t.add_row(formatted, s.get("status_code", "—"), s.get("mime_type", "—")[:20], s.get("snapshot_url", "")[:60])
    console.print(t)


@osint.command("wiki")
@click.argument("entity")
def osint_wiki(entity: str):
    """Wikipedia entity enrichment — summary, key facts, categories."""
    from modules.osint.wikipedia_enricher import enrich_entity, get_summary
    from rich.panel import Panel
    with console.status(f"[cyan]Wikipedia lookup: {entity}...[/cyan]"):
        info = get_summary(entity)
    if not info:
        console.print(f"[yellow]No Wikipedia article found for '{entity}'[/yellow]")
        return
    content = (
        f"[bold]Title:[/bold] {info.get('title','')}\n"
        f"[bold]URL:[/bold] {info.get('url','')}\n"
        f"[bold]Last Revised:[/bold] {(info.get('last_revised',''))[:10]}\n\n"
        f"{info.get('summary','')[:800]}"
    )
    console.print(Panel(content, title=f"[bold cyan]Wikipedia: {entity}[/bold cyan]", border_style="cyan"))
    cats = info.get("categories", [])
    if cats:
        console.print(f"[dim]Categories: {', '.join(cats[:8])}[/dim]")


@osint.command("ip")
@click.argument("address")
def osint_ip(address: str):
    """IP address geolocation, ISP, proxy/hosting detection (ip-api.com — no key required)."""
    from modules.osint.ip_intel import lookup_ip
    from rich.panel import Panel
    with console.status(f"[cyan]IP lookup: {address}...[/cyan]"):
        info = lookup_ip(address)
    if "error" in info:
        formatters.error_panel(info["error"])
        return
    content = (
        f"[bold]IP:[/bold] {info.get('ip_address', address)}\n"
        f"[bold]Hostname:[/bold] {info.get('hostname','—')}\n"
        f"[bold]Location:[/bold] {info.get('city','—')}, {info.get('region','—')}, {info.get('country','—')}\n"
        f"[bold]Organization:[/bold] {info.get('org','—')}\n"
        f"[bold]ISP:[/bold] {info.get('isp','—')}\n"
        f"[bold]ASN:[/bold] {info.get('asn','—')}\n"
        f"[bold]Proxy:[/bold] {'Yes' if info.get('is_proxy') else 'No'}  "
        f"[bold]Hosting:[/bold] {'Yes' if info.get('is_hosting') else 'No'}  "
        f"[bold]Mobile:[/bold] {'Yes' if info.get('is_mobile') else 'No'}\n"
        f"[bold]Source:[/bold] ip-api.com (free, no key required)"
    )
    console.print(Panel(content, title=f"[bold cyan]IP Intelligence: {address}[/bold cyan]", border_style="cyan"))


@osint.command("ioc")
@click.argument("indicator")
@click.option("--type", "ioc_type", default=None, help="Force type: domain, IPv4, URL, FileHash-SHA256, CVE")
def osint_ioc(indicator: str, ioc_type):
    """Threat intelligence lookup — domain/IP/hash via abuse.ch (URLhaus + MalwareBazaar) + OTX."""
    from modules.osint.threat_lookup import lookup_indicator
    from modules.osint.threat_feeds import lookup_ioc
    from rich.panel import Panel
    import json

    with console.status(f"[cyan]Threat intel lookup: {indicator}...[/cyan]"):
        otx = lookup_ioc(indicator, ioc_type)
        abuse = lookup_indicator(indicator)

    lines = [
        f"[bold]Indicator:[/bold] {indicator}",
    ]
    if abuse and "error" not in abuse:
        try:
            cats = json.loads(abuse.get("categories", "[]"))
        except Exception:
            cats = []
        lines += [
            f"[bold]abuse.ch Malicious URLs:[/bold] {abuse.get('malicious_votes', 0)}",
            f"[bold]abuse.ch Tags:[/bold] {', '.join(cats[:5]) if cats else '—'}",
            f"[bold]Source:[/bold] {abuse.get('source', 'URLhaus/MalwareBazaar')} (no key required)",
        ]
    if otx and "error" not in otx:
        lines += [
            f"[bold]OTX Pulses:[/bold] {otx.get('malicious_votes','—')}",
            f"[bold]OTX Tags:[/bold] {', '.join(eval(otx.get('categories','[]'))[:5]) if otx.get('categories') else '—'}",
        ]
    console.print(Panel("\n".join(lines), title=f"[bold red]Threat Intel: {indicator}[/bold red]", border_style="red"))


@osint.command("breaches")
@click.argument("target", metavar="DOMAIN_OR_EMAIL")
def osint_breaches(target: str):
    """Data breach lookup — check domain or email against HIBP."""
    from modules.osint.breach_intel import check_and_store
    from rich.table import Table
    with console.status(f"[cyan]Checking breach databases for: {target}...[/cyan]"):
        results = check_and_store(target)
    if not results:
        console.print(f"[green]No breaches found for '{target}'[/green]")
        return
    if results and "error" in results[0]:
        formatters.error_panel(results[0]["error"])
        return
    t = Table(title=f"Data Breaches: {target} ({len(results)} found)", show_lines=True)
    t.add_column("Breach", style="bold white")
    t.add_column("Date", style="dim", width=12)
    t.add_column("Records", style="red", width=12)
    t.add_column("Data Types", style="yellow")
    t.add_column("Verified", width=8)
    for r in results:
        import json
        try:
            classes = ", ".join(json.loads(r.get("data_classes", "[]"))[:4])
        except Exception:
            classes = str(r.get("data_classes", ""))
        t.add_row(
            r.get("breach_name","—"),
            r.get("breach_date","—"),
            f"{r.get('pwn_count',0):,}",
            classes,
            "Yes" if r.get("is_verified") else "No",
        )
    console.print(t)


@osint.command("email-hunt")
@click.argument("domain")
@click.option("--limit", default=25, show_default=True)
@click.option("--first", default=None, help="First name for targeted guess")
@click.option("--last", default=None, help="Last name for targeted guess")
def osint_email_hunt(domain: str, limit: int, first, last):
    """Guess email patterns for a domain (local pattern analysis + MX check, no API key)."""
    from modules.osint.email_intel import domain_search, guess_email_patterns
    from rich.table import Table
    with console.status(f"[cyan]Email pattern analysis: {domain}...[/cyan]"):
        if first or last:
            emails_raw = guess_email_patterns(domain, first or "", last or "")
            result = {"domain": domain, "organization": "", "pattern": "targeted-guess",
                      "emails_found": len(emails_raw),
                      "emails": [{"email": e["email"], "first_name": first or "",
                                  "last_name": last or "", "position": "Targeted",
                                  "confidence": e["confidence"]} for e in emails_raw]}
        else:
            result = domain_search(domain, limit=limit)
    console.print(f"[bold]Domain:[/bold] {domain} | "
                  f"[bold]MX Valid:[/bold] {'Yes' if result.get('mx_valid') else 'No'} | "
                  f"[bold]Patterns:[/bold] {result.get('emails_found',0)} | "
                  f"[dim]{result.get('note', 'No external API used')}[/dim]")
    emails = result.get("emails", [])
    if emails:
        t = Table(title=f"Email Patterns: {domain}", show_lines=False)
        t.add_column("Email", style="cyan")
        t.add_column("Position", style="yellow")
        t.add_column("Confidence", style="green", width=12)
        for e in emails:
            t.add_row(e.get("email",""), e.get("position","—")[:40], f"{e.get('confidence',0)}%")
        console.print(t)


@osint.command("academic")
@click.argument("query")
@click.option("--author", default=None, help="Filter by author name")
@click.option("--institution", default=None, help="Filter by institution")
@click.option("--limit", default=20, show_default=True)
def osint_academic(query: str, author, institution, limit: int):
    """Scientific paper intelligence via OpenAlex (250M+ papers)."""
    from modules.osint.academic_intel import search_and_store
    from rich.table import Table
    import json
    with console.status(f"[cyan]Academic search: {query}...[/cyan]"):
        papers = search_and_store(query, author=author, institution=institution)
    if not papers:
        console.print("[yellow]No papers found.[/yellow]")
        return
    t = Table(title=f"Academic Papers: {query} ({len(papers)} found)", show_lines=True)
    t.add_column("Year", style="dim", width=6)
    t.add_column("Title", style="bold white")
    t.add_column("Authors/Orgs", style="cyan")
    t.add_column("Journal", style="yellow")
    t.add_column("Citations", style="green", width=10)
    for p in papers[:limit]:
        try:
            authors_data = json.loads(p.get("authors","[]"))
            author_str = ", ".join(a["name"] for a in authors_data[:2])
            if len(authors_data) > 2:
                author_str += f" +{len(authors_data)-2}"
        except Exception:
            author_str = "—"
        t.add_row(
            str(p.get("publication_year","—")),
            (p.get("title",""))[:70],
            author_str[:50],
            (p.get("journal","—"))[:30],
            str(p.get("cited_by_count",0)),
        )
    console.print(t)


@osint.command("dork")
@click.argument("target")
@click.option("--type", "dork_type", default="news", help=f"Dork type: {', '.join(['news','pastebin','linkedin','github_mentions','court_records','site_docs','crypto_wallets'])}")
def osint_dork(target: str, dork_type: str):
    """Search engine intelligence dork against a target."""
    from modules.osint.search_dorks import dork_target
    from rich.table import Table
    with console.status(f"[cyan]Running {dork_type} dork on: {target}...[/cyan]"):
        result = dork_target(target, dork_type)
    if result.error:
        formatters.error_panel(result.error)
        return
    t = Table(title=f"Dork Results: {target} ({dork_type})", show_lines=True)
    t.add_column("Title", style="bold white")
    t.add_column("URL", style="cyan dim")
    t.add_column("Snippet", style="dim")
    for r in result.results:
        t.add_row(r["title"][:60], r["url"][:60], r["snippet"][:80])
    console.print(t)
    console.print(f"[dim]Query: {result.query}[/dim]")


# ── SIGINT commands ────────────────────────────────────────────────────────────

@cli.group()
def sigint():
    """SIGINT-adjacent — flight tracking, vessel tracking, RF spectrum."""


@sigint.command("flights")
@click.option("--callsign", default=None, help="Filter by callsign")
@click.option("--country", default=None, help="Filter by origin country")
@click.option("--bbox", default=None, help="Bounding box: lat_min,lon_min,lat_max,lon_max")
@click.option("--live", is_flag=True, help="Fetch live from OpenSky (default: use DB cache)")
def sigint_flights(callsign, country, bbox, live):
    """ADS-B flight tracking via OpenSky Network."""
    from modules.sigint.adsb_tracker import fetch_flights, search_db
    parsed_bbox = None
    if bbox:
        try:
            parts = [float(x) for x in bbox.split(",")]
            parsed_bbox = tuple(parts)
        except ValueError:
            formatters.error_panel("Invalid bbox format. Use: lat_min,lon_min,lat_max,lon_max")
            return

    if live:
        with console.status("[cyan]Fetching live flights from OpenSky...[/cyan]"):
            result = fetch_flights(bbox=parsed_bbox, callsign=callsign, country=country)
    else:
        result = search_db(callsign=callsign, country=country)

    if result.error:
        formatters.error_panel(result.error)
        return
    if not result.flights:
        console.print("[yellow]No flights found.[/yellow]")
        return
    console.print(formatters.flights_table(result.flights))
    console.print(f"[dim]{result.total} flights[/dim]")


@sigint.command("vessels")
@click.option("--mmsi", default=None, help="Filter by MMSI number")
@click.option("--country", default=None, help="Filter by flag country")
@click.option("--live", is_flag=True, help="Fetch live from aisstream.io")
def sigint_vessels(mmsi, country, live):
    """AIS vessel tracking."""
    from modules.sigint.ais_tracker import fetch_vessels_sync, search_db
    if live:
        with console.status("[cyan]Connecting to aisstream.io...[/cyan]"):
            result = fetch_vessels_sync(mmsi=mmsi)
    else:
        result = search_db(mmsi=mmsi, country=country)

    if result.error:
        formatters.error_panel(result.error)
        return
    if not result.vessels:
        console.print("[yellow]No vessels found.[/yellow]")
        return
    console.print(formatters.vessels_table(result.vessels))


@sigint.command("gfw-vessels")
@click.argument("mmsi", required=False, default=None)
@click.option("--flag", default=None, help="Filter by flag state (ISO 2-letter code)")
@click.option("--name", "vessel_name", default=None, help="Search by vessel name")
def sigint_gfw_vessels(mmsi, flag, vessel_name):
    """Global Fishing Watch vessel intelligence — dark vessels, IUU flags."""
    from modules.sigint.gfw_tracker import search_vessels, update_vessel_tracks_gfw
    from rich.table import Table
    with console.status("[cyan]Searching Global Fishing Watch...[/cyan]"):
        if mmsi:
            result_info = update_vessel_tracks_gfw(mmsi)
        vessels = search_vessels(mmsi=mmsi, flag=flag, vessel_name=vessel_name)
    if vessels and "error" in vessels[0]:
        formatters.error_panel(vessels[0]["error"])
        return
    if not vessels:
        console.print("[yellow]No vessels found.[/yellow]")
        return
    t = Table(title=f"Global Fishing Watch Vessels ({len(vessels)} found)", show_lines=True)
    t.add_column("MMSI", style="cyan", width=12)
    t.add_column("Vessel Name", style="bold white")
    t.add_column("Flag", width=8)
    t.add_column("IMO", style="dim", width=12)
    t.add_column("Class", style="yellow")
    for v in vessels[:30]:
        t.add_row(v.get("mmsi","—"), v.get("vessel_name","—"), v.get("flag","—"),
                  v.get("imo","—"), v.get("vessel_class","—"))
    console.print(t)


@sigint.command("fcc")
@click.argument("callsign")
def sigint_fcc(callsign: str):
    """FCC ULS radio license lookup by callsign."""
    from modules.sigint.rf_databases import fetch_fcc, save_to_db
    from rich.table import Table
    with console.status(f"[cyan]FCC ULS lookup: {callsign}...[/cyan]"):
        result = fetch_fcc(callsign=callsign)
    if result.error:
        formatters.error_panel(result.error)
        return
    save_to_db(result)
    t = Table(title=f"FCC License: {callsign}", show_lines=True)
    t.add_column("Callsign", style="cyan")
    t.add_column("License Name", style="white")
    t.add_column("Entity", style="yellow")
    t.add_column("Freq (MHz)", style="green")
    t.add_column("Service", style="dim")
    t.add_column("State", style="dim")
    t.add_column("Status", style="dim")
    for a in result.allocations:
        t.add_row(a.callsign or "—", a.license_name or "—", a.entity_name or "—",
                  str(a.frequency_mhz or "—"), a.service_type or "—", a.state or "—", a.status or "—")
    console.print(t)


# ── Geopolitical commands ─────────────────────────────────────────────────────

@cli.group()
def geo():
    """Geopolitical intelligence — leaders, events, sanctions, conflicts."""


@geo.command("leaders")
@click.option("--country", default=None, help="Filter by country name or code (e.g. US, Russia)")
@click.option("--refresh", is_flag=True, help="Fetch fresh data from Wikidata")
def geo_leaders(country, refresh):
    """World leaders database (heads of state and government)."""
    from modules.geopolitical.world_leaders import fetch_leaders, search_db, update_leaders
    if refresh:
        with console.status("[cyan]Fetching world leaders from Wikidata...[/cyan]"):
            update_leaders()
        console.print("[green]Leaders database updated.[/green]")

    result = search_db(country)
    if result.error:
        formatters.error_panel(result.error)
        return
    if not result.leaders:
        # Try live fetch if DB empty
        with console.status("[cyan]No cache found, fetching from Wikidata...[/cyan]"):
            result = fetch_leaders(country)
    console.print(formatters.leaders_table(result.leaders[:100]))
    console.print(f"[dim]{result.total} leaders found[/dim]")


@geo.command("sanctions")
@click.argument("name")
@click.option("--list", "list_source", default=None, help="Filter: OFAC, UN, EU")
@click.option("--refresh", is_flag=True, help="Download fresh sanctions lists")
def geo_sanctions(name, list_source, refresh):
    """Search sanctions lists (OFAC, UN, EU)."""
    from modules.geopolitical.sanctions import update_sanctions, search
    if refresh:
        with console.status("[cyan]Downloading sanctions lists...[/cyan]"):
            update_sanctions()
        console.print("[green]Sanctions lists updated.[/green]")
    with console.status(f"[cyan]Searching sanctions for: {name}...[/cyan]"):
        result = search(name, list_source)
    if result.error:
        formatters.error_panel(result.error)
        return
    if not result.matches:
        console.print(f"[green]No sanctions matches found for '{name}'[/green]")
        return
    console.print(formatters.sanctions_table(result.matches))
    console.print(f"[dim]{result.total} matches[/dim]")


@geo.command("events")
@click.option("--country", default=None, help="Filter by country name")
@click.option("--days", default=7, show_default=True, help="Days lookback")
@click.option("--live", is_flag=True, help="Fetch fresh from GDELT")
def geo_events(country, days, live):
    """Political events from GDELT Project."""
    from modules.geopolitical.event_tracker import fetch_events, search_db
    if live:
        with console.status(f"[cyan]Fetching GDELT events...[/cyan]"):
            result = fetch_events(country, days)
    else:
        result = search_db(country, days)
    if result.error:
        formatters.error_panel(result.error)
        return
    console.print(formatters.events_table(result.events[:50]))
    console.print(f"[dim]{result.total} events[/dim]")


@geo.command("conflicts")
@click.option("--country", default=None, help="Filter by country")
@click.option("--days", default=30, show_default=True, help="Days lookback")
@click.option("--live", is_flag=True, help="Fetch fresh from ACLED/ReliefWeb")
def geo_conflicts(country, days, live):
    """Conflict events from ACLED and ReliefWeb."""
    from modules.geopolitical.conflict_monitor import update_conflicts, search_db
    if live:
        with console.status("[cyan]Fetching conflict data...[/cyan]"):
            update_conflicts()
    result = search_db(country, days)
    if result.error:
        formatters.error_panel(result.error)
        return
    console.print(formatters.conflicts_table(result.events[:50]))
    console.print(f"[dim]{result.total} events[/dim]")


# ── Power structure commands ───────────────────────────────────────────────────

@cli.group()
def power():
    """Power structure intelligence — billionaires, corporations, donations."""


@power.command("billionaires")
@click.option("--country", default=None, help="Filter by country")
@click.option("--top", "top_n", default=50, show_default=True, help="Top N results")
@click.option("--refresh", is_flag=True, help="Refresh from Wikidata/Forbes")
def power_billionaires(country, top_n, refresh):
    """Global billionaire wealth list."""
    from modules.power.billionaires import update_billionaires, search_db
    if refresh:
        with console.status("[cyan]Refreshing billionaire data...[/cyan]"):
            update_billionaires()
        console.print("[green]Billionaire data updated.[/green]")
    result = search_db(country, top_n)
    if not result.billionaires:
        with console.status("[cyan]No cache, fetching from Wikidata...[/cyan]"):
            update_billionaires()
        result = search_db(country, top_n)
    console.print(formatters.billionaires_table(result.billionaires))
    console.print(f"[dim]{result.total} billionaires[/dim]")


@power.command("corp")
@click.argument("name")
@click.option("--live", is_flag=True, help="Fetch live from OpenCorporates")
def power_corp(name: str, live: bool):
    """Corporate structure lookup via OpenCorporates."""
    from modules.power.corporations import fetch_company, search_db, save_to_db
    from rich.table import Table
    if live:
        with console.status(f"[cyan]Searching OpenCorporates: {name}...[/cyan]"):
            result = fetch_company(name)
        if result.corporations:
            save_to_db(result.corporations)
    else:
        result = search_db(name)
    if result.error:
        formatters.error_panel(result.error)
        return
    t = Table(title=f"Corporations: {name}", show_lines=True)
    t.add_column("Name", style="bold white")
    t.add_column("Jurisdiction", style="cyan")
    t.add_column("Type", style="yellow")
    t.add_column("Status", style="green")
    t.add_column("Incorporated", style="dim")
    for c in result.corporations[:30]:
        t.add_row(c.name, c.jurisdiction or "—", c.company_type or "—", c.status or "—", c.incorporation_date or "—")
    console.print(t)


@power.command("donations")
@click.argument("entity")
@click.option("--live", is_flag=True, help="Fetch live from FEC API")
def power_donations(entity: str, live: bool):
    """Political donation records from FEC."""
    from modules.power.donations import fetch_donations, save_to_db, search_db
    if live:
        with console.status(f"[cyan]Querying FEC for: {entity}...[/cyan]"):
            result = fetch_donations(entity)
        if result.donations:
            save_to_db(result.donations)
    else:
        result = search_db(entity)
    if result.error:
        formatters.error_panel(result.error)
        return
    console.print(formatters.donations_table(result.donations[:50]))
    console.print(f"[dim]{result.total} donations | Total: ${result.total_amount_usd:,.0f}[/dim]")


@power.command("offshore")
@click.argument("name")
@click.option("--limit", default=40, show_default=True)
def power_offshore(name: str, limit: int):
    """ICIJ Offshore Leaks — Panama/Pandora Papers shell company search."""
    from modules.power.offshore_leaks import search_and_store
    from rich.table import Table
    with console.status(f"[cyan]Searching ICIJ Offshore Leaks for: {name}...[/cyan]"):
        results = search_and_store(name, limit=limit)
    if not results:
        console.print(f"[yellow]No offshore leak entries found for '{name}'[/yellow]")
        return
    t = Table(title=f"ICIJ Offshore Leaks: {name} ({len(results)} found)", show_lines=True)
    t.add_column("Name", style="bold white")
    t.add_column("Type", style="cyan", width=15)
    t.add_column("Jurisdiction", style="yellow")
    t.add_column("Data Source", style="dim")
    t.add_column("Valid Until", style="dim", width=12)
    for r in results:
        t.add_row(r.get("name","—"), r.get("entity_type","—"), r.get("jurisdiction","—"),
                  r.get("data_source","—"), r.get("valid_until","—"))
    console.print(t)


@power.command("sec-filings")
@click.argument("company")
@click.option("--form", "form_type", default=None, help="Form type: 10-K, 10-Q, 8-K, 4, SC 13G")
@click.option("--days", "days_back", default=365, show_default=True, help="Days lookback")
def power_sec_filings(company: str, form_type, days_back: int):
    """SEC EDGAR financial filings search."""
    from modules.power.sec_edgar import search_and_store
    from rich.table import Table
    with console.status(f"[cyan]SEC EDGAR search: {company}...[/cyan]"):
        results = search_and_store(company, form_type=form_type, days_back=days_back)
    if not results:
        console.print(f"[yellow]No SEC filings found for '{company}'[/yellow]")
        return
    t = Table(title=f"SEC Filings: {company} ({len(results)} found)", show_lines=True)
    t.add_column("Filed", style="dim", width=12)
    t.add_column("Form", style="cyan", width=10)
    t.add_column("Company", style="bold white")
    t.add_column("Period", style="dim", width=12)
    t.add_column("URL", style="dim")
    for r in results:
        t.add_row(r.get("filed_date","—"), r.get("form_type","—"), r.get("company_name","—"),
                  r.get("period_of_report","—"), r.get("document_url","—")[:50])
    console.print(t)


@power.command("sec-insider")
@click.argument("name")
def power_sec_insider(name: str):
    """SEC Form 4 insider trading search."""
    from modules.power.sec_edgar import insider_trading
    from rich.table import Table
    with console.status(f"[cyan]Searching SEC insider trading: {name}...[/cyan]"):
        results = insider_trading(name)
    if not results:
        console.print(f"[yellow]No Form 4 filings found for '{name}'[/yellow]")
        return
    t = Table(title=f"Insider Trading (Form 4): {name}", show_lines=True)
    t.add_column("Filed", style="dim", width=12)
    t.add_column("Company", style="bold white")
    t.add_column("Period", style="dim")
    for r in results[:30]:
        t.add_row(r.get("filed_date","—"), r.get("company_name","—"), r.get("period_of_report","—"))
    console.print(t)


@power.command("congress-member")
@click.argument("name")
def power_congress_member(name: str):
    """ProPublica Congress — member search with ideology score and contact info."""
    from modules.power.congress_votes import search_and_store
    from rich.table import Table
    with console.status(f"[cyan]Searching Congress members: {name}...[/cyan]"):
        members = search_and_store(name)
    if not members:
        console.print(f"[yellow]No Congress members found for '{name}'[/yellow]")
        return
    t = Table(title=f"Congress Members: {name}", show_lines=True)
    t.add_column("Name", style="bold white")
    t.add_column("Party", style="cyan", width=8)
    t.add_column("Chamber", style="yellow", width=10)
    t.add_column("State", width=8)
    t.add_column("In Office", width=10)
    t.add_column("DW-Nominate", width=12)
    t.add_column("Twitter", style="dim")
    for m in members:
        dw = f"{m.get('dw_nominate',0):.3f}" if m.get('dw_nominate') is not None else "—"
        t.add_row(m.get("full_name",""), m.get("party","—"), m.get("chamber","—"),
                  m.get("state","—"), "Yes" if m.get("in_office") else "No", dw,
                  m.get("twitter_account","—"))
    console.print(t)


@power.command("congress-votes")
@click.argument("member_id")
@click.option("--limit", default=30, show_default=True)
def power_congress_votes(member_id: str, limit: int):
    """ProPublica Congress — voting record for a member by ID."""
    from modules.power.congress_votes import get_votes, store_votes
    from rich.table import Table
    with console.status(f"[cyan]Fetching voting record for {member_id}...[/cyan]"):
        votes = get_votes(member_id)
        if votes:
            store_votes(votes)
    if not votes:
        console.print(f"[yellow]No votes found for member ID '{member_id}'[/yellow]")
        return
    t = Table(title=f"Voting Record: {member_id} ({len(votes)} votes)", show_lines=False)
    t.add_column("Date", style="dim", width=12)
    t.add_column("Position", width=12)
    t.add_column("Result", width=12)
    t.add_column("Bill", style="cyan")
    t.add_column("Title", style="dim")
    for v in votes[:limit]:
        pos = v.get("vote_position","—")
        pos_color = "green" if pos == "Yes" else ("red" if pos == "No" else "yellow")
        t.add_row(v.get("vote_date","")[:10], f"[{pos_color}]{pos}[/{pos_color}]",
                  v.get("result","—"), v.get("bill_id","—")[:20], v.get("bill_title","—")[:60])
    console.print(t)


@power.command("board")
@click.argument("name")
@click.option("--company", "is_company", is_flag=True, help="Search by company name instead of person")
def power_board(name: str, is_company: bool):
    """Board membership cross-reference."""
    from modules.power.board_tracker import search_by_person, search_by_company
    from rich.table import Table
    members = search_by_company(name) if is_company else search_by_person(name)
    t = Table(title=f"Board Memberships: {name}", show_lines=True)
    t.add_column("Person", style="bold white")
    t.add_column("Company", style="cyan")
    t.add_column("Role", style="yellow")
    t.add_column("Start", style="dim")
    t.add_column("End", style="dim")
    for m in members:
        t.add_row(m.person_name, m.company_name, m.role or "—", m.start_date or "—", m.end_date or "Present")
    console.print(t)
    console.print(f"[dim]{len(members)} board memberships found[/dim]")


@geo.command("wanted")
@click.argument("name")
@click.option("--live", is_flag=True, help="Search live FBI + Interpol APIs")
@click.option("--update", is_flag=True, help="Download full wanted lists to DB")
def geo_wanted(name: str, live: bool, update: bool):
    """Search FBI + Interpol wanted persons lists."""
    from modules.geopolitical.wanted import search, search_live, update_wanted
    from rich.table import Table
    if update:
        with console.status("[cyan]Downloading FBI + Interpol wanted lists...[/cyan]"):
            stats = update_wanted()
        console.print(f"[green]Updated: {stats['fbi']} FBI, {stats['interpol']} Interpol, {stats['stored']} stored[/green]")
    if live:
        with console.status(f"[cyan]Searching live: {name}...[/cyan]"):
            results = search_live(name)
    else:
        results = search(name)
        if not results:
            with console.status(f"[cyan]Not in DB, searching live: {name}...[/cyan]"):
                results = search_live(name)
    if not results:
        console.print(f"[green]No wanted persons found for '{name}'[/green]")
        return
    t = Table(title=f"Wanted Persons: {name} ({len(results)} found)", show_lines=True)
    t.add_column("Source", style="cyan", width=10)
    t.add_column("Name", style="bold white")
    t.add_column("Nationality", width=14)
    t.add_column("DOB", width=12)
    t.add_column("Charges", style="dim")
    t.add_column("Reward", style="yellow")
    for r in results:
        t.add_row(r.get("list_source","—"), r.get("full_name","—"), r.get("nationality","—"),
                  r.get("date_of_birth","—"), (r.get("charges","—") or "—")[:60],
                  "Yes" if r.get("reward_text") else "No")
    console.print(t)


# ── UAP commands ───────────────────────────────────────────────────────────────

@cli.group()
def uap():
    """UAP/Anomalous phenomena intelligence — sightings, hearings, documents."""


@uap.command("sightings")
@click.option("--state", default=None, help="US state code (e.g. CA, TX)")
@click.option("--days", default=30, show_default=True)
@click.option("--keyword", default=None, help="Filter by description keyword")
@click.option("--source", default="NUFORC", help="Source: NUFORC, FAA")
def uap_sightings(state, days, keyword, source):
    """UAP sighting database (NUFORC, FAA documented encounters)."""
    from modules.uap.nuforc import search_db as nuforc_search
    from modules.uap.faa_reports import search_db as faa_search
    if source.upper() == "FAA":
        result = faa_search(keyword)
    else:
        result = nuforc_search(state, days, keyword)
    if result.error:
        formatters.error_panel(result.error)
        return
    console.print(formatters.uap_sightings_table(result.sightings[:50]))
    console.print(f"[dim]{result.total} sightings[/dim]")


@uap.command("hearings")
@click.option("--keyword", default=None, help="Filter by keyword")
def uap_hearings(keyword):
    """Congressional UAP hearing transcripts and summaries."""
    from modules.uap.congress_uap import search_db
    result = search_db(keyword)
    if result.error:
        formatters.error_panel(result.error)
        return
    formatters.hearings_panel(result.hearings)
    console.print(f"[dim]{result.total} hearings[/dim]")


@uap.command("documents")
@click.option("--keyword", default=None, help="Search keyword")
def uap_documents(keyword):
    """Declassified UAP documents and reports."""
    from modules.uap.declassified import get_all, search
    from rich.table import Table
    docs = search(keyword) if keyword else get_all()
    t = Table(title="Declassified UAP Documents", show_lines=True)
    t.add_column("Date", style="dim", width=12)
    t.add_column("Source", style="cyan", width=12)
    t.add_column("Title", style="bold white")
    t.add_column("Classification", style="yellow", width=18)
    t.add_column("Summary", style="dim")
    for d in docs:
        t.add_row(
            d.report_date or "—", d.source, d.title,
            d.classification or "—", (d.summary or "")[:80]
        )
    console.print(t)


@uap.command("news")
@click.option("--days", default=7, show_default=True)
@click.option("--refresh", is_flag=True, help="Fetch fresh news")
def uap_news(days, refresh):
    """Recent UAP news from RSS and news APIs."""
    from modules.uap.news_tracker import update_uap_news, search_db
    if refresh:
        with console.status("[cyan]Fetching UAP news...[/cyan]"):
            update_uap_news()
    result = search_db(days)
    from rich.table import Table
    t = Table(title="UAP News", show_lines=False)
    t.add_column("Date", style="dim", width=12)
    t.add_column("Source", style="cyan", width=20)
    t.add_column("Title", style="bold white")
    t.add_column("Keywords", style="yellow dim")
    for item in result.items[:50]:
        t.add_row(
            (item.published_at or "")[:10],
            item.source[:20],
            item.title[:70],
            ", ".join(item.matched_keywords[:3]),
        )
    console.print(t)
    console.print(f"[dim]{result.total} articles[/dim]")


# ── Correlation commands ───────────────────────────────────────────────────────

@cli.command("correlate")
@click.argument("name")
@click.option("--report", is_flag=True, help="Export full Markdown report")
def correlate(name: str, report: bool):
    """Cross-source entity correlation and intelligence profile."""
    from modules.correlation.entity_resolver import build_profile
    from modules.correlation.timeline import build_entity_timeline
    from modules.correlation.ai_analyst import analyze_entity
    from rich.panel import Panel

    with console.status(f"[cyan]Building intelligence profile for: {name}...[/cyan]"):
        profile = build_profile(name)

    console.print(Panel(
        f"[bold]Entity:[/bold] {profile.entity.canonical_name}\n"
        f"[bold]Type:[/bold] {profile.entity.entity_type}\n"
        f"[bold]Aliases:[/bold] {', '.join(profile.entity.aliases) or 'None'}\n"
        f"[bold]Data Sources:[/bold] {', '.join(profile.entity.source_modules) or 'Unknown'}\n"
        f"[bold]Sanctions:[/bold] {len(profile.sanctions)} matches\n"
        f"[bold]Donations:[/bold] {len(profile.donations)} records\n"
        f"[bold]Board Roles:[/bold] {len(profile.board_roles)}\n"
        f"[bold]Corporations:[/bold] {len(profile.corporations)}\n"
        f"[bold]Relationships:[/bold] {len(profile.relationships)}",
        title=f"[bold yellow]Intel Profile: {name}[/bold yellow]",
        border_style="yellow",
    ))

    if profile.sanctions:
        console.print(formatters.sanctions_table(profile.sanctions[:10]))
    if profile.donations:
        console.print(formatters.donations_table(profile.donations[:15]))

    # Timeline
    timeline = build_entity_timeline(name)
    if timeline:
        from rich.table import Table
        t = Table(title="Entity Timeline", show_lines=False)
        t.add_column("Date", style="dim", width=12)
        t.add_column("Event Type", style="cyan", width=25)
        t.add_column("Description", style="white")
        t.add_column("Source", style="dim", width=12)
        for e in timeline[:20]:
            t.add_row(e.date[:10] if e.date else "—", e.event_type, e.description[:80], e.source)
        console.print(t)

    # AI analysis
    console.print("\n[bold cyan]AI Analysis[/bold cyan]")
    for chunk in analyze_entity(profile):
        console.print(chunk, end="")
    console.print()

    if report:
        from utils.exporters import entity_report
        profile.ai_summary = "".join(analyze_entity(profile, stream=False))
        path = entity_report(name, profile)
        formatters.success_panel(f"Report saved: {path}")


# ── Feed commands ──────────────────────────────────────────────────────────────

@cli.group()
def feed():
    """Live intelligence feed — alerts and real-time updates."""


@feed.command("start")
def feed_start():
    """Start the live intelligence collection daemon."""
    from modules.feed.live_updater import start_daemon
    start_daemon()


@feed.command("status")
def feed_status():
    """Show status of scheduled intelligence jobs."""
    from modules.feed.live_updater import list_jobs
    from rich.table import Table
    jobs = list_jobs()
    if not jobs:
        console.print("[yellow]No jobs running. Start the daemon with: intel feed start[/yellow]")
        return
    t = Table(title="Scheduler Jobs")
    t.add_column("Job ID", style="cyan")
    t.add_column("Next Run", style="green")
    for j in jobs:
        t.add_row(j["id"], j["next_run"] or "—")
    console.print(t)


@feed.command("latest")
@click.option("--category", default=None, help="Filter: geopolitical, uap, power, general")
@click.option("--days", default=3, show_default=True)
def feed_latest(category, days):
    """Show latest feed items."""
    from modules.feed.rss_aggregator import get_recent
    items = get_recent(category=category, days=days)
    console.print(formatters.feed_table(items))


@feed.command("alerts")
@click.option("--add-keyword", "add_kw", default=None, help="Add a keyword to watch")
@click.option("--add-entity", "add_ent", default=None, help="Add an entity to watch")
@click.option("--remove", "remove_kw", default=None, help="Remove a keyword")
@click.option("--list", "list_all", is_flag=True, help="List current watchlist")
def feed_alerts(add_kw, add_ent, remove_kw, list_all):
    """Manage alert watchlist."""
    from modules.feed.alert_engine import (
        add_keyword, add_entity, remove_keyword, list_keywords, list_entities, get_active_alerts
    )
    from rich.table import Table
    if add_kw:
        add_keyword(add_kw)
        formatters.success_panel(f"Added keyword: '{add_kw}'")
    if add_ent:
        add_entity(add_ent)
        formatters.success_panel(f"Added tracked entity: '{add_ent}'")
    if remove_kw:
        remove_keyword(remove_kw)
        formatters.success_panel(f"Removed keyword: '{remove_kw}'")
    if list_all or not any([add_kw, add_ent, remove_kw]):
        kws = list_keywords()
        ents = list_entities()
        console.print(f"[bold]Keywords:[/bold] {', '.join(kws) or 'None'}")
        console.print(f"[bold]Entities:[/bold] {', '.join(ents) or 'None'}")
        alerts = get_active_alerts()
        if alerts:
            t = Table(title=f"Active Alerts ({len(alerts)})", show_lines=False)
            t.add_column("Severity", width=10)
            t.add_column("Message", style="white")
            t.add_column("Time", style="dim", width=20)
            for a in alerts:
                sev_color = {"critical": "red", "warning": "yellow", "info": "blue"}.get(a.severity, "white")
                t.add_row(f"[{sev_color}]{a.severity}[/{sev_color}]", a.message[:80], (a.created_at or "")[:19])
            console.print(t)


# ── AI Ask command ─────────────────────────────────────────────────────────────

@cli.command("ask")
@click.argument("question")
@click.option("--context", default=None, help="Provide additional context")
def ask(question: str, context: str):
    """Ask the AI intelligence analyst a question."""
    from core.ai_engine import analyze
    console.print(f"[bold cyan]Question:[/bold cyan] {question}\n")
    console.print("[bold]Analysis:[/bold]")
    for chunk in analyze(question, context=context):
        console.print(chunk, end="")
    console.print()


# ── Settings commands ──────────────────────────────────────────────────────────

@cli.group()
def settings():
    """Configuration management."""


@settings.command("show")
def settings_show():
    """Show current configuration."""
    from rich.table import Table
    all_s = cfg.all_settings()
    t = Table(title="Intel Platform Settings", show_lines=False)
    t.add_column("Key", style="cyan")
    t.add_column("Value", style="white")
    for k, v in all_s.items():
        # Mask API keys
        if "key" in k or "api" in k:
            display = "***" + str(v)[-4:] if v else "[dim]not set[/dim]"
        else:
            display = str(v) if v else "[dim]not set[/dim]"
        t.add_row(k, display)
    console.print(t)


@settings.command("set")
@click.argument("key")
@click.argument("value")
def settings_set(key: str, value: str):
    """Set a configuration value."""
    cfg.set(key, value)
    formatters.success_panel(f"Set {key} = {'***' if 'key' in key else value}")


@settings.command("get")
@click.argument("key")
def settings_get(key: str):
    """Get a configuration value."""
    val = cfg.get(key)
    console.print(f"{key} = {val}")


if __name__ == "__main__":
    cli()
