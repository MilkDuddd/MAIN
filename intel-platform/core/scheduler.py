"""APScheduler job registry for live intel updates."""

from __future__ import annotations

import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import (
    INTERVAL_FLIGHTS, INTERVAL_VESSELS, INTERVAL_UAP_NEWS,
    INTERVAL_NEWS, INTERVAL_GDELT, INTERVAL_CONFLICTS,
    INTERVAL_LEADERS, INTERVAL_BILLIONAIRES, INTERVAL_SANCTIONS,
    INTERVAL_CORPS, INTERVAL_DONATIONS, INTERVAL_TENDERS,
)

log = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
    return _scheduler


def start() -> None:
    s = get_scheduler()
    if not s.running:
        s.start()
        log.info("Scheduler started")


def stop() -> None:
    s = get_scheduler()
    if s.running:
        s.shutdown(wait=False)
        log.info("Scheduler stopped")


def add_job(func: Callable, interval_sec: int, job_id: str, **kwargs) -> None:
    s = get_scheduler()
    if s.get_job(job_id):
        s.remove_job(job_id)
    s.add_job(
        func,
        trigger=IntervalTrigger(seconds=interval_sec),
        id=job_id,
        kwargs=kwargs,
        misfire_grace_time=60,
        coalesce=True,
        max_instances=1,
    )
    log.info("Registered job '%s' every %ds", job_id, interval_sec)


def register_all_jobs() -> None:
    """Register the default set of live-update jobs."""
    # Import lazily to avoid circular deps at startup
    from modules.geopolitical.world_leaders import update_leaders
    from modules.geopolitical.event_tracker import update_gdelt_events
    from modules.geopolitical.sanctions import update_sanctions
    from modules.geopolitical.conflict_monitor import update_conflicts
    from modules.sigint.adsb_tracker import update_flights
    from modules.sigint.ais_tracker import update_vessels
    from modules.uap.news_tracker import update_uap_news
    from modules.power.billionaires import update_billionaires
    from modules.feed.rss_aggregator import update_all_feeds

    add_job(update_flights,       INTERVAL_FLIGHTS,      "flights")
    add_job(update_vessels,       INTERVAL_VESSELS,      "vessels")
    add_job(update_uap_news,      INTERVAL_UAP_NEWS,     "uap_news")
    add_job(update_all_feeds,     INTERVAL_NEWS,         "rss_feeds")
    add_job(update_gdelt_events,  INTERVAL_GDELT,        "gdelt")
    add_job(update_conflicts,     INTERVAL_CONFLICTS,    "conflicts")
    add_job(update_leaders,       INTERVAL_LEADERS,      "leaders")
    add_job(update_billionaires,  INTERVAL_BILLIONAIRES, "billionaires")
    add_job(update_sanctions,     INTERVAL_SANCTIONS,    "sanctions")
