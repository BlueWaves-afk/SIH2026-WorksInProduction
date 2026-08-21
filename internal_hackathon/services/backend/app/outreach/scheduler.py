from apscheduler.schedulers.background import BackgroundScheduler
import structlog

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.delivery import process_outbox as process_outbox_once
from app.services.digest import send_district_digests
from app.services.ingestion import run_ingestion_cycle
from app.services.outreach import run_outreach_cycle
from app.services.retention import run_retention_cycle
from app.services.sla import scan_sla_breaches

logger = structlog.get_logger()


def process_outbox():
    db = SessionLocal()
    try:
        result = process_outbox_once(db)
        logger.info("outbox_cycle_complete", **result)
    finally:
        db.close()


def process_outreach():
    db = SessionLocal()
    try:
        result = run_outreach_cycle(db)
        logger.info("outreach_decision_cycle_complete", created=result["created"], skipped=result["skipped"])
    finally:
        db.close()


def process_sla():
    db = SessionLocal()
    try:
        result = scan_sla_breaches(db)
        logger.info("sla_cycle_complete", **result)
    finally:
        db.close()


def process_retention():
    db = SessionLocal()
    try:
        result = run_retention_cycle(db)
        logger.info("retention_cycle_complete", **result)
    finally:
        db.close()


def process_ingestion():
    db = SessionLocal()
    try:
        result = run_ingestion_cycle(db)
        logger.info("ingestion_cycle_complete", rescored=result["rescored"], live_fetched=result["live_fetched"], failed=result["failed"])
    finally:
        db.close()


def process_district_digest():
    db = SessionLocal()
    try:
        result = send_district_digests(db)
        logger.info("district_digest_cycle_complete", **result)
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(process_outbox, "interval", minutes=1, id="outbox", replace_existing=True)
    scheduler.add_job(process_outreach, "interval", minutes=5, id="outreach", replace_existing=True)
    scheduler.add_job(process_sla, "interval", minutes=5, id="sla", replace_existing=True)
    scheduler.add_job(process_retention, "interval", hours=24, id="retention", replace_existing=True)
    if settings.ingestion_enabled:
        scheduler.add_job(
            process_ingestion,
            "interval",
            minutes=settings.ingestion_interval_minutes,
            id="ingestion",
            replace_existing=True,
        )
    if settings.district_digest_enabled:
        scheduler.add_job(
            process_district_digest,
            "cron",
            hour=settings.district_digest_hour,
            minute=0,
            id="district_digest",
            replace_existing=True,
        )
    scheduler.start()
    logger.info(
        "scheduler_started",
        ingestion=settings.ingestion_enabled,
        ingestion_interval_min=settings.ingestion_interval_minutes,
        district_digest=settings.district_digest_enabled,
    )
    return scheduler
