"""Live update orchestrator — starts/stops scheduled intel collection."""

import logging
import signal
import sys
import time

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from core import database, scheduler
from modules.feed.alert_engine import get_active_alerts

log = logging.getLogger(__name__)
console = Console()


def start_daemon(verbose: bool = False) -> None:
    """
    Start the live intelligence update daemon.
    Runs continuously until interrupted.
    """
    database.init_db()
    scheduler.start()
    scheduler.register_all_jobs()

    console.print(Panel.fit(
        "[bold green]Intel Platform Live Daemon Started[/bold green]\n"
        "Collecting intelligence from all configured sources.\n"
        "Press [bold]Ctrl+C[/bold] to stop.",
        title="Intel Platform",
        border_style="green",
    ))

    def handle_sigint(sig, frame):
        console.print("\n[yellow]Shutting down daemon...[/yellow]")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    # Status display loop
    while True:
        try:
            _print_status()
            time.sleep(60)
        except KeyboardInterrupt:
            break

    scheduler.stop()


def _print_status() -> None:
    """Print current scheduler job status."""
    s = scheduler.get_scheduler()
    if not s.running:
        return

    table = Table(title="Active Jobs", show_header=True)
    table.add_column("Job ID", style="cyan")
    table.add_column("Next Run", style="green")
    table.add_column("Status", style="yellow")

    for job in s.get_jobs():
        next_run = str(job.next_run_time)[:19] if job.next_run_time else "N/A"
        table.add_row(job.id, next_run, "Active")

    console.print(table)

    # Show recent alerts
    alerts = get_active_alerts(limit=5)
    if alerts:
        console.print(f"[bold red]{len(alerts)} active alerts[/bold red]")
        for a in alerts[:3]:
            console.print(f"  [yellow]⚠[/yellow] {a.message}")


def trigger_now(job_id: str) -> None:
    """Manually trigger a scheduled job immediately."""
    s = scheduler.get_scheduler()
    job = s.get_job(job_id)
    if job:
        job.modify(next_run_time=None)
        s.wakeup()
        console.print(f"[green]Triggered job: {job_id}[/green]")
    else:
        console.print(f"[red]Job not found: {job_id}[/red]")


def list_jobs() -> list[dict]:
    """Return status of all scheduled jobs."""
    s = scheduler.get_scheduler()
    if not s.running:
        return []
    return [
        {
            "id": job.id,
            "next_run": str(job.next_run_time)[:19] if job.next_run_time else None,
        }
        for job in s.get_jobs()
    ]
