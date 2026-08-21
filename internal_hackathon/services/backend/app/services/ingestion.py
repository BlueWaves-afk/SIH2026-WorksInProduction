"""Automatic ingest -> rescore cycle for the whole consented cohort.

This is the clock that turns the platform from a manually-triggered scorer into
a continuously refreshed farmer-risk service. It mirrors the per-farmer
``POST /risk-events/recalculate`` flow, run for every storage-consented profile:

    (optional) live fetch  ->  FDI rescore  ->  persist event + case workflow

Outreach is intentionally NOT triggered here. The dedicated outreach cycle
already runs on its own cadence and picks up the band changes this job writes,
keeping the "decide" pass observable and auditable on its own.

Failure isolation: one farmer's live-source outage or bad row never aborts the
cohort. Each profile is committed independently; failures are counted and
logged, and the cycle continues.
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.live_data import LiveIngestionError, sync_profile_observations
from app.models.farmer import FarmerProfile
from app.security import AuthContext
from app.security.audit import record_audit
from app.services.scoring import compute_for_profile
from app.services.workflow import persist_event_with_workflow

logger = structlog.get_logger()

_SYSTEM_ACTOR = AuthContext(principal="ingestion-scheduler", role="admin", scopes=frozenset({"*"}))


def _has_storage_consent(profile: FarmerProfile) -> bool:
    flags = profile.consent_flags or {}
    return bool(flags.get("store_data", flags.get("storage", False)))


def run_ingestion_cycle(
    db: Session,
    *,
    now: datetime | None = None,
    actor: AuthContext | None = None,
    live: bool | None = None,
) -> dict:
    """Refresh signals and rescore every eligible farmer.

    ``live`` overrides the ``live_data_enabled`` flag (used by tests). When live
    is off, stored/replay observations are rescored so bands still expire and
    hysteresis still advances.
    """

    as_of = now or datetime.now(UTC)
    system_actor = actor or _SYSTEM_ACTOR
    use_live = settings.live_data_enabled if live is None else live

    scanned = rescored = live_fetched = skipped = failed = 0
    bands: dict[str, int] = {"green": 0, "amber": 0, "red": 0}

    profiles = db.query(FarmerProfile).limit(settings.ingestion_cohort_limit).all()
    for profile in profiles:
        scanned += 1
        if not _has_storage_consent(profile):
            skipped += 1
            continue
        try:
            if use_live:
                try:
                    sync_profile_observations(db, profile, as_of=as_of)
                    live_fetched += 1
                except LiveIngestionError as exc:
                    # Stale/unavailable source is not fatal: rescore stored rows
                    # so freshness (and confidence) degrade honestly instead of
                    # the whole cohort failing.
                    db.rollback()
                    logger.warning("ingestion_live_source_unavailable", farmer=profile.farmer_token, error=str(exc))
            event = compute_for_profile(db, profile, as_of=as_of)
            row, _ = persist_event_with_workflow(db, profile, event, actor=system_actor)
            record_audit(
                db,
                actor=system_actor,
                action="risk_event.ingestion_cycle",
                target_id=event.event_id,
                details={"band": event.band, "score": event.score, "live": use_live},
            )
            db.commit()
            db.refresh(row)
            rescored += 1
            bands[str(event.band).lower()] = bands.get(str(event.band).lower(), 0) + 1
        except Exception as exc:  # noqa: BLE001 - isolate one farmer's failure from the cohort
            db.rollback()
            failed += 1
            logger.error("ingestion_profile_failed", farmer=profile.farmer_token, error=str(exc))

    summary = {
        "scanned": scanned,
        "rescored": rescored,
        "live_fetched": live_fetched,
        "skipped_no_consent": skipped,
        "failed": failed,
        "bands": bands,
        "live": use_live,
    }
    logger.info("ingestion_cycle_complete", **summary)
    return summary
