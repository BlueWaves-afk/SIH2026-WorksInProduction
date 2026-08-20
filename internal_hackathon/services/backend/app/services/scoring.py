"""Database-to-pure-engine integration for the canonical FDI scorer."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.integrations.canonical import (
    ScoringConsentContext,
    ScoringFarmerContext,
    ScoringObservation,
    compute_risk_event,
)
from app.models.farmer import FarmerProfile
from app.models.observation import Observation as ObservationRow
from app.models.risk import RiskEvent as RiskEventRow


def _aware(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def farmer_context(profile: FarmerProfile) -> ScoringFarmerContext:
    irrigation = profile.irrigation_type if profile.irrigation_type in {"rainfed", "partial", "assured"} else "rainfed"
    area = profile.area_band if profile.area_band in {"<1", "1-2", ">2"} else None
    institutional = profile.institutional_access if profile.institutional_access in {"good", "limited", "unknown"} else "unknown"
    soil = profile.soil_retention if profile.soil_retention in {"poor", "medium", "good", "unknown"} else "unknown"
    return ScoringFarmerContext(
        farmer_token=profile.farmer_token,
        village_id=profile.village_id,
        crop=profile.crop,
        sowing_date=profile.sowing_date or date.today(),
        irrigation_type=irrigation,
        area_band=area,
        secondary_crop=profile.secondary_crop,
        schemes_enrolled=profile.schemes_enrolled or [],
        institutional_access=institutional,
        soil_retention=soil,
    )


def consent_context(profile: FarmerProfile) -> ScoringConsentContext:
    flags = profile.consent_flags or {}
    return ScoringConsentContext(
        farmer_token=profile.farmer_token,
        storage=bool(flags.get("store_data", flags.get("storage", False))),
        contact=bool(flags.get("contact_me", flags.get("contact", False))),
        analytics=bool(flags.get("use_analytics", flags.get("analytics", False))),
        due_window=bool(flags.get("due_window", False)),
        consent_scopes=[name for name, value in flags.items() if bool(value)],
    )


def scoring_observations(rows: list[ObservationRow]) -> list[ScoringObservation]:
    return [
        ScoringObservation(
            source=row.source,
            observed_at=_aware(row.observed_at),
            village_id=row.village_id,
            plot_grid=row.plot_grid,
            metric=row.metric,
            value=row.value,
            unit=row.unit or "",
            quality=row.quality or "good",
            ttl=timedelta(seconds=int(row.ttl or 172800)),
        )
        for row in rows
    ]


def compute_for_profile(
    db: Session,
    profile: FarmerProfile,
    *,
    as_of: datetime | None = None,
    rows: list[ObservationRow] | None = None,
):
    observations = rows if rows is not None else list(
        db.query(ObservationRow)
        .filter(ObservationRow.farmer_token == profile.farmer_token)
        .order_by(ObservationRow.observed_at.desc())
        .limit(100)
        .all()
    )
    prior = []
    for row in (
        db.query(RiskEventRow)
        .filter(RiskEventRow.farmer_token == profile.farmer_token)
        .order_by(RiskEventRow.evaluated_at.desc())
        .limit(3)
        .all()
    ):
        # The pure engine only needs the prior band/timestamps for hysteresis.
        from scoring_engine.types import RiskEvent as ScoringRiskEvent

        prior.append(
            ScoringRiskEvent(
                event_id=row.event_id,
                farmer_token=row.farmer_token,
                village_id=row.village_id,
                score=float(row.score or 0),
                band=str(row.band or "green").lower(),
                confidence=float(row.confidence or 0),
                contributors=row.contributors or [],
                action_ids=row.action_ids or [],
                model_version=row.model_version or "unknown",
                evaluated_at=_aware(row.evaluated_at),
                expires_at=_aware(row.expires_at),
                disclaimer=row.disclaimer or "This is not a credit, loan-default, or insurance score.",
                context_flags=row.context_flags or [],
            )
        )
    return compute_risk_event(
        farmer_context(profile),
        scoring_observations(observations),
        consent_context(profile),
        prior_events=prior,
        as_of=_aware(as_of),
    )


def persist_risk_event(db: Session, event) -> RiskEventRow:
    row = RiskEventRow(
        event_id=event.event_id,
        farmer_token=event.farmer_token,
        village_id=event.village_id,
        score=event.score,
        band=event.band,
        confidence=event.confidence,
        contributors=[item.model_dump(mode="json") for item in event.contributors],
        action_ids=event.action_ids,
        model_version=event.model_version,
        evaluated_at=_aware(event.evaluated_at),
        expires_at=_aware(event.expires_at),
        disclaimer=event.disclaimer,
        context_flags=event.context_flags,
    )
    db.add(row)
    return row
