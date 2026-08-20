"""Live weather/market ingestion for the canonical observation boundary.

The backend owns persistence and consent checks; the adapters package owns
provider HTTP and parsing.  Keeping those concerns separate makes the same
source contract usable by replay tests, a local proxy, or the official IMD /
AGMARKNET endpoints once deployment credentials are provided.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal

from adapters.core.interfaces import ObservationPayload, SignalRequest
from adapters.sources.registry import build_registry
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.farmer import FarmerProfile
from app.models.observation import Observation


LIVE_SOURCES = ("imd", "agmarknet")
SourceName = Literal["imd", "agmarknet"]


class LiveIngestionError(RuntimeError):
    """Raised when a requested live source cannot safely be used."""


@dataclass(frozen=True)
class LiveFetchResult:
    observations: list[ObservationPayload]
    sources: list[dict[str, Any]]
    errors: list[dict[str, str]]


def _registry():
    # Pydantic Settings reads .env.local, whereas os.environ may not contain
    # those values.  Pass the resolved settings explicitly to the registry.
    environ = {
        "ADAPTER_MODE_IMD": settings.adapter_mode_imd,
        "ADAPTER_MODE_AGMARKNET": settings.adapter_mode_agmarknet,
        "IMD_ENDPOINT": settings.imd_endpoint or "",
        "IMD_API_KEY": settings.imd_api_key or "",
        "AGMARKNET_ENDPOINT": settings.agmarknet_endpoint or "",
        "AGMARKNET_API_KEY": settings.agmarknet_api_key or "",
        "LIVE_ADAPTER_TIMEOUT_SECONDS": str(settings.live_adapter_timeout_seconds),
    }
    return build_registry(environ)


def _request(
    *,
    village_id: str | None,
    district_id: str | None,
    mandi_id: str | None,
    commodity: str | None,
    start_date: date | None,
    end_date: date | None,
) -> SignalRequest:
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=7))
    if start > end:
        raise ValueError("start_date must be on or before end_date")
    return SignalRequest(
        village_id=village_id,
        district_id=district_id,
        mandi_id=mandi_id,
        commodity=commodity,
        date_range=(start, end),
    )


def adapter_health(*, sources: list[SourceName] | None = None) -> list[dict[str, Any]]:
    registry = _registry()
    selected = sources or list(LIVE_SOURCES)
    result: list[dict[str, Any]] = []
    for source in selected:
        adapter = registry.get(source)
        health = adapter.health().model_dump(mode="json")
        result.append(
            {
                "source": source,
                "mode": adapter.mode.value,
                "configured": bool(getattr(adapter, "configured", False)),
                "health": health,
            }
        )
    return result


def fetch_live(
    *,
    village_id: str | None = None,
    district_id: str | None = None,
    mandi_id: str | None = None,
    commodity: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    sources: list[SourceName] | None = None,
) -> LiveFetchResult:
    if not settings.live_data_enabled:
        raise LiveIngestionError("live data is disabled; set LIVE_DATA_ENABLED=true for a deployment")
    request = _request(
        village_id=village_id,
        district_id=district_id,
        mandi_id=mandi_id,
        commodity=commodity,
        start_date=start_date,
        end_date=end_date,
    )
    registry = _registry()
    selected = sources or list(LIVE_SOURCES)
    observations: list[ObservationPayload] = []
    source_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for source in selected:
        adapter = registry.get(source)
        try:
            if adapter.mode.value != "real":
                raise LiveIngestionError(
                    f"{source} adapter is in mock mode; set ADAPTER_MODE_{source.upper()}=real"
                )
            rows = adapter.fetch(request)
            observations.extend(rows)
            source_rows.append(
                {
                    "source": source,
                    "mode": adapter.mode.value,
                    "configured": bool(getattr(adapter, "configured", False)),
                    "observation_count": len(rows),
                    "health": adapter.health().model_dump(mode="json"),
                }
            )
        except Exception as exc:
            # Provider URLs, headers and response bodies are intentionally not
            # returned to clients.  The adapter health state has the same safe
            # error summary for operator diagnostics.
            errors.append({"source": source, "message": str(exc).split("?", 1)[0][:240]})
            source_rows.append(
                {
                    "source": source,
                    "mode": adapter.mode.value,
                    "configured": bool(getattr(adapter, "configured", False)),
                    "observation_count": 0,
                    "health": adapter.health().model_dump(mode="json"),
                }
            )
    return LiveFetchResult(observations=observations, sources=source_rows, errors=errors)


def sync_profile_observations(
    db: Session,
    profile: FarmerProfile,
    *,
    as_of: datetime | None = None,
) -> tuple[list[Observation], LiveFetchResult]:
    """Fetch live rows, persist only new observations, and return DB rows.

    This function intentionally does not compute a score.  The caller can pass
    the returned rows into the pure FDI engine, preserving the existing
    side-effect-free scoring contract.
    """
    effective_as_of = as_of or datetime.now(UTC)
    result = fetch_live(
        village_id=profile.village_id,
        district_id=None,
        commodity=profile.crop,
        end_date=effective_as_of.date(),
        sources=list(LIVE_SOURCES),
    )
    if result.errors:
        failed = ", ".join(item["source"] for item in result.errors)
        raise LiveIngestionError(f"live source unavailable: {failed}")

    persisted: list[Observation] = []
    for payload in result.observations:
        observed_at = payload.observed_at.replace(tzinfo=None)
        duplicate = (
            db.query(Observation)
            .filter(
                Observation.farmer_token == profile.farmer_token,
                Observation.source == payload.source,
                Observation.metric == payload.metric,
                Observation.observed_at == observed_at,
            )
            .first()
        )
        if duplicate is not None:
            persisted.append(duplicate)
            continue
        row = Observation(
            farmer_token=profile.farmer_token,
            source=payload.source,
            observed_at=observed_at,
            village_id=payload.village_id or profile.village_id,
            plot_grid=payload.plot_grid,
            metric=payload.metric,
            value=payload.value,
            unit=payload.unit,
            quality=payload.quality,
            ttl=int(payload.ttl.total_seconds()),
        )
        db.add(row)
        persisted.append(row)
    db.flush()
    return persisted, result


__all__ = [
    "LIVE_SOURCES",
    "LiveFetchResult",
    "LiveIngestionError",
    "adapter_health",
    "fetch_live",
    "sync_profile_observations",
]
