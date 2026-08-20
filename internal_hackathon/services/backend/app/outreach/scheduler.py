from apscheduler.schedulers.background import BackgroundScheduler
import structlog
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.outbox import OutboxMessage
from app.adapters.notification import MockNotificationAdapter

logger = structlog.get_logger()
notification_adapter = MockNotificationAdapter()

def is_quiet_hours() -> bool:
    # Quiet hours: 8 PM (20) to 8 AM (8)
    current_hour = datetime.now().hour
    return current_hour >= 20 or current_hour < 8

def process_outbox():
    if is_quiet_hours():
        logger.info("Quiet hours active, pausing outbox processing.")
        return

    db = SessionLocal()
    try:
        # Fetch pending messages or those due for a retry
        now = datetime.utcnow()
        messages = db.query(OutboxMessage).filter(
            (OutboxMessage.status == 'pending') | 
            ((OutboxMessage.status == 'failed') & (OutboxMessage.next_retry_at <= now))
        ).limit(50).all()

        for msg in messages:
            try:
                # Attempt delivery
                result = notification_adapter.send_action_card(msg.farmer_phone, msg.channel, msg.content)
                msg.status = 'sent'
                msg.sent_at = now
            except Exception as e:
                msg.retry_count += 1
                if msg.retry_count >= 3:
                    msg.status = 'dead_letter'
                else:
                    msg.status = 'failed'
                    msg.next_retry_at = now + timedelta(minutes=15 * msg.retry_count) # Exponential backoff
                msg.error_log = str(e)
            
            db.commit()

    except Exception as e:
        logger.error(f"Outbox processing failed: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run every minute for MVP purposes
    scheduler.add_job(process_outbox, 'interval', minutes=1)
    scheduler.start()
    logger.info("Outreach scheduler started.")

