from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.integrations.canonical import ReplayDriver
from app.models.farmer import FarmerProfile
from app.models.observation import Observation
from app.services.scoring import compute_for_profile
from app.services.workflow import persist_event_with_workflow


SCENARIO_ALIASES = {
    "drought": "rainfall_shock",
    "drought_crash": "rainfall_shock",
}


def run_replay(db: Session, profile: FarmerProfile, scenario: str, day_offset: int = 0) -> dict:
    canonical_scenario = SCENARIO_ALIASES.get(scenario, scenario)
    bundle = ReplayDriver().generate(canonical_scenario, day_offset)
    rows: list[Observation] = []
    for payload in bundle.observations:
        row = Observation(
            farmer_token=profile.farmer_token,
            source=payload.source,
            observed_at=payload.observed_at.replace(tzinfo=None),
            village_id=profile.village_id,
            plot_grid=payload.plot_grid,
            metric=payload.metric,
            value=payload.value,
            unit=payload.unit,
            quality=payload.quality,
            ttl=int(payload.ttl.total_seconds()),
        )
        db.add(row)
        rows.append(row)
    db.flush()
    as_of = datetime(2026, 6, 1, tzinfo=UTC) + timedelta(days=day_offset)
    event = compute_for_profile(db, profile, as_of=as_of, rows=rows)
    event_row, case_row = persist_event_with_workflow(db, profile, event)
    db.commit()
    return {"event": event, "event_row": event_row, "case_row": case_row, "scenario": canonical_scenario}
