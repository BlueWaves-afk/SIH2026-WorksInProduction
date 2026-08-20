"""Backward-compatible facade for the canonical FDI v2 scoring engine.

New code must use ``app.services.scoring`` and
``scoring_engine.compute_risk_event``. This facade exists only for older local
imports and delegates to that same pure engine; it contains no second rule set.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.integrations.canonical import (
    ScoringConsentContext,
    ScoringFarmerContext,
    ScoringObservation,
    compute_risk_event,
)


class ScoringEngine:
    def calculate_score(
        self,
        farmer_profile: dict,
        weather_data: dict | None,
        market_data: dict | None,
        repayment_opt_in: dict | None = None,
        farmer_report: dict | None = None,
    ) -> dict:
        """Adapt the retired v1 call shape to the FDI v2 engine."""

        now = datetime.now(UTC)
        observations: list[ScoringObservation] = []
        if weather_data:
            legacy_ttl = int(weather_data.get("ttl", 48))
            observations.append(
                ScoringObservation(
                    source="IMD",
                    observed_at=now - timedelta(days=3) if legacy_ttl < 0 else now,
                    metric="rainfall_deviation_pct",
                    value=weather_data.get("value", 0),
                    unit="percent",
                    ttl=timedelta(hours=max(1, abs(legacy_ttl))),
                )
            )
        if market_data:
            observations.append(
                ScoringObservation(
                    source="Agmarknet",
                    observed_at=now,
                    metric="mandi_price_deviation_pct",
                    value={
                        "deviation_pct": market_data.get("deviation_pct", 0),
                        "below_msp": bool(market_data.get("below_msp", False)),
                    },
                    unit="percent",
                    ttl=timedelta(days=2),
                )
            )
        due = bool(repayment_opt_in and repayment_opt_in.get("is_due_soon"))
        if due:
            observations.append(
                ScoringObservation(
                    source="farmer_opt_in",
                    observed_at=now,
                    metric="due_window",
                    value={"days_to_due": 5, "amount_band": "medium"},
                    ttl=timedelta(days=2),
                )
            )
        if farmer_report and farmer_report.get("has_shock"):
            observations.append(
                ScoringObservation(
                    source="farmer",
                    observed_at=now,
                    metric="acute_farmer_report",
                    value=farmer_report.get("shock_type", "reported shock"),
                    ttl=timedelta(days=2),
                )
            )

        raw_area = farmer_profile.get("area_band")
        area = "<1" if raw_area in {"<1", "<1 ha"} else "1-2" if raw_area in {"1-2", "1-2 ha"} else ">2"
        event = compute_risk_event(
            ScoringFarmerContext(
                farmer_token="legacy-farmer",
                village_id="legacy-village",
                crop=farmer_profile.get("crop", "unknown"),
                sowing_date=farmer_profile.get("sowing_date", date.today()),
                irrigation_type=farmer_profile.get("irrigation_type", "rainfed"),
                area_band=area,
                institutional_access="limited",
                soil_retention="poor",
            ),
            observations,
            ScoringConsentContext(farmer_token="legacy-farmer", due_window=due),
            as_of=now,
        )
        return {
            "score": event.score,
            "band": event.band.title(),
            "confidence": event.confidence,
            "drivers": [driver.explanation for driver in event.contributors],
        }
