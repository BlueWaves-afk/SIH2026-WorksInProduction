from apscheduler.schedulers.background import BackgroundScheduler
import structlog

from app.core.database import SessionLocal
from app.services.delivery import process_outbox as process_outbox_once
from app.services.outreach import run_outreach_cycle
from app.services.retention import run_retention_cycle

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


def process_retention():
    db = SessionLocal()
    try:
        result = run_retention_cycle(db)
        logger.info("retention_cycle_complete", **result)
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(process_outbox, "interval", minutes=1, id="outbox", replace_existing=True)
    scheduler.add_job(process_outreach, "interval", minutes=5, id="outreach", replace_existing=True)
    scheduler.add_job(process_retention, "interval", hours=24, id="retention", replace_existing=True)
    scheduler.start()
    logger.info("outreach_scheduler_started")
    return scheduler
