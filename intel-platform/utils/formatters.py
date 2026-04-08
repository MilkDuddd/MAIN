"""Rich table and panel renderers for CLI output."""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


def leaders_table(leaders) -> Table:
    t = Table(title="World Leaders", box=box.ROUNDED, show_lines=True)
    t.add_column("Country", style="cyan", min_width=20)
    t.add_column("Name", style="bold white")
    t.add_column("Role", style="green")
    t.add_column("Party", style="yellow")
    t.add_column("Since", style="dim")
    for l in leaders:
        t.add_row(
            f"{l.country_code or ''} {l.country}",
            l.name,
            l.role,
            l.party or "—",
            l.in_office_since or "—",
        )
    return t


def sanctions_table(sanctions) -> Table:
    t = Table(title="Sanctions Results", box=box.ROUNDED, show_lines=True)
    t.add_column("List", style="red", width=8)
    t.add_column("Name", style="bold white")
    t.add_column("Type", style="cyan", width=12)
    t.add_column("Nationality", style="yellow")
    t.add_column("DOB", style="dim")
    t.add_column("Programs", style="red dim")
    for s in sanctions:
        t.add_row(
            s.list_source,
            s.name,
            s.entity_type or "—",
            s.nationality or "—",
            s.date_of_birth or "—",
            ", ".join(s.programs[:3]) if s.programs else "—",
        )
    return t


def billionaires_table(billionaires) -> Table:
    t = Table(title="Billionaires", box=box.ROUNDED, show_lines=False)
    t.add_column("Rank", style="dim", width=6)
    t.add_column("Name", style="bold white")
    t.add_column("Net Worth", style="bold green")
    t.add_column("Country", style="cyan")
    t.add_column("Industry", style="yellow")
    t.add_column("Company", style="dim")
    for b in billionaires:
        t.add_row(
            str(b.source_rank or "—"),
            b.name,
            b.net_worth_display,
            b.country or "—",
            b.industry or "—",
            b.primary_company or "—",
        )
    return t


def flights_table(flights) -> Table:
    t = Table(title="Live Flights", box=box.SIMPLE, show_lines=False)
    t.add_column("ICAO24", style="cyan", width=8)
    t.add_column("Callsign", style="bold white", width=10)
    t.add_column("Country", style="yellow")
    t.add_column("Lat", style="dim", width=9)
    t.add_column("Lon", style="dim", width=10)
    t.add_column("Alt (ft)", style="green", width=9)
    t.add_column("Speed (kts)", style="blue", width=11)
    t.add_column("Track°", style="dim", width=7)
    t.add_column("Squawk", style="red", width=7)
    for f in flights:
        t.add_row(
            f.icao24,
            f.callsign or "—",
            f.origin_country or "—",
            f"{f.latitude:.3f}" if f.latitude is not None else "—",
            f"{f.longitude:.3f}" if f.longitude is not None else "—",
            f"{f.altitude_ft:,.0f}" if f.altitude_ft is not None else "—",
            f"{f.speed_knots:.1f}" if f.speed_knots is not None else "—",
            f"{f.true_track:.0f}" if f.true_track is not None else "—",
            f.squawk or "—",
        )
    return t


def vessels_table(vessels) -> Table:
    t = Table(title="Vessel Tracks", box=box.SIMPLE, show_lines=False)
    t.add_column("MMSI", style="cyan", width=12)
    t.add_column("Name", style="bold white")
    t.add_column("Flag", style="yellow", width=6)
    t.add_column("Type", style="green")
    t.add_column("Lat", style="dim", width=9)
    t.add_column("Lon", style="dim", width=10)
    t.add_column("SOG (kts)", style="blue", width=10)
    t.add_column("Dest.", style="dim")
    for v in vessels:
        t.add_row(
            v.mmsi,
            v.name or "—",
            v.flag or "—",
            v.vessel_type_name,
            f"{v.latitude:.3f}" if v.latitude is not None else "—",
            f"{v.longitude:.3f}" if v.longitude is not None else "—",
            f"{v.sog:.1f}" if v.sog is not None else "—",
            v.destination or "—",
        )
    return t


def uap_sightings_table(sightings) -> Table:
    t = Table(title="UAP Sightings", box=box.ROUNDED, show_lines=True)
    t.add_column("Date", style="cyan", width=12)
    t.add_column("Location", style="bold white")
    t.add_column("Shape", style="yellow", width=12)
    t.add_column("Duration", style="dim", width=10)
    t.add_column("Source", style="dim", width=8)
    t.add_column("Description", style="white")
    for s in sightings:
        location = f"{s.city or ''}, {s.state or ''}, {s.country or ''}".strip(", ")
        dur = f"{s.duration_sec}s" if s.duration_sec else "—"
        desc = (s.description or "")[:80]
        t.add_row(s.occurred_date or "—", location, s.shape or "—", dur, s.source, desc)
    return t


def hearings_panel(hearings) -> None:
    """Print UAP hearing transcripts as panels."""
    for h in hearings:
        witnesses_str = "\n".join(f"  • {w}" for w in h.witnesses) if h.witnesses else "  N/A"
        quotes_str = "\n".join(f'  "{q}"' for q in (h.key_quotes or [])[:3])
        content = (
            f"[cyan]Date:[/cyan] {h.date or '—'}\n"
            f"[cyan]Committee:[/cyan] {h.committee or '—'} ({h.chamber or '—'})\n\n"
            f"[bold]Witnesses:[/bold]\n{witnesses_str}\n\n"
            f"[bold]Summary:[/bold]\n{h.summary or '—'}\n\n"
            f"[bold]Key Quotes:[/bold]\n{quotes_str or '  N/A'}\n\n"
            f"[dim]URL: {h.document_url or '—'}[/dim]"
        )
        console.print(Panel(content, title=f"[bold yellow]{h.title}[/bold yellow]", border_style="yellow"))


def events_table(events) -> Table:
    t = Table(title="Political Events (GDELT)", box=box.SIMPLE, show_lines=False)
    t.add_column("Date", style="cyan", width=12)
    t.add_column("Actor/Source", style="bold white")
    t.add_column("Country", style="yellow", width=15)
    t.add_column("Description", style="white")
    for e in events:
        t.add_row(
            e.event_date or "—",
            e.actor1 or "—",
            e.actor1_country or "—",
            (e.event_description or "")[:80],
        )
    return t


def conflicts_table(events) -> Table:
    t = Table(title="Conflict Events", box=box.ROUNDED, show_lines=True)
    t.add_column("Date", style="cyan", width=12)
    t.add_column("Country", style="yellow")
    t.add_column("Location", style="white")
    t.add_column("Type", style="red")
    t.add_column("Actors", style="bold white")
    t.add_column("Fatalities", style="red bold", width=11)
    t.add_column("Source", style="dim", width=8)
    for e in events:
        actors = " vs ".join(filter(None, [e.actor1, e.actor2]))
        t.add_row(
            e.event_date or "—",
            e.country or "—",
            e.location or "—",
            e.event_type or "—",
            actors or "—",
            str(e.fatalities) if e.fatalities is not None else "—",
            e.source,
        )
    return t


def donations_table(donations) -> Table:
    t = Table(title="Political Donations", box=box.ROUNDED, show_lines=False)
    t.add_column("Donor", style="bold white")
    t.add_column("Recipient", style="cyan")
    t.add_column("Party", style="yellow", width=12)
    t.add_column("Amount", style="bold green")
    t.add_column("Date", style="dim", width=12)
    t.add_column("Cycle", style="dim", width=6)
    for d in donations:
        amt = f"${d.amount_usd:,.0f}" if d.amount_usd else "—"
        t.add_row(d.donor_name, d.recipient_name, d.recipient_party or "—", amt, d.transaction_date or "—", d.election_cycle or "—")
    return t


def feed_table(items) -> Table:
    t = Table(title="Latest Intelligence Feed", box=box.SIMPLE, show_lines=False)
    t.add_column("Time", style="dim", width=12)
    t.add_column("Source", style="cyan", width=20)
    t.add_column("Category", style="yellow", width=14)
    t.add_column("Title", style="bold white")
    for item in items:
        pub = (item.published_at or "")[:10]
        t.add_row(pub, item.source[:20], item.category or "—", item.title[:80])
    return t


def error_panel(message: str, title: str = "Error") -> None:
    console.print(Panel(f"[red]{message}[/red]", title=f"[bold red]{title}[/bold red]", border_style="red"))


def success_panel(message: str, title: str = "Success") -> None:
    console.print(Panel(f"[green]{message}[/green]", title=f"[bold green]{title}[/bold green]", border_style="green"))
