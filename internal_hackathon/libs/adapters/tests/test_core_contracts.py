from datetime import UTC, datetime, timedelta

import pytest

from adapters.core import AdapterMode, AdapterRegistry, HealthTracker, QualityGate
from adapters.core.interfaces import ObservationPayload, RawPayload
from adapters.core.normalizer import normalize
from adapters.replay import ReplayDriver

NOW = datetime(2026, 6, 1, tzinfo=UTC)


def test_registry_switches_mode_without_caller_changes():
    class Adapter:
        def __init__(self, mode):
            self.mode = mode

    registry = AdapterRegistry.from_factories(
        "imd",
        {
            AdapterMode.MOCK: lambda: Adapter(AdapterMode.MOCK),
            AdapterMode.REAL: lambda: Adapter(AdapterMode.REAL),
        },
        {"ADAPTER_MODE_IMD": "real"},
    )
    assert registry.get("imd").mode is AdapterMode.REAL


def test_normalizer_and_quality_gate_map_and_dedupe():
    payload = RawPayload(
        source="agmarknet",
        fetched_at=NOW,
        body={"data": [{"field": "price_deviation_pct", "value": -20, "unit": "percent"}]},
    )
    observations = normalize(payload)
    assert observations[0].metric == "mandi_price_deviation_pct"
    gate = QualityGate()
    assert len(gate.accept(observations + observations, NOW)) == 1


def test_ttl_marks_old_observation_stale():
    old = ObservationPayload(
        source="imd",
        observed_at=NOW - timedelta(days=3),
        metric="rainfall_deviation_pct",
        value=-20,
        ttl=timedelta(days=2),
    )
    assert QualityGate().accept([old], NOW)[0].quality == "stale"


def test_health_tracker_opens_and_recovers_circuit():
    tracker = HealthTracker("imd", AdapterMode.REAL, failure_threshold=2)
    tracker.failure("timeout")
    state = tracker.failure("timeout")
    assert state.circuit_open and not state.ok
    state = tracker.success(NOW)
    assert state.ok and not state.circuit_open and state.consecutive_failures == 0


@pytest.mark.parametrize("scenario", ["normal", "rainfall_shock", "price_crash", "due_window", "stale_data"])
def test_replay_scenarios_are_deterministic(scenario):
    driver = ReplayDriver()
    first = driver.generate(scenario, 0)
    second = driver.generate(scenario, 0)
    assert first.model_dump() == second.model_dump()
    assert first.observations
    if scenario == "rainfall_shock":
        assert {item.metric for item in first.observations} >= {
            "rainfall_deviation_pct",
            "mandi_price_deviation_pct",
            "due_window",
        }


def test_flagship_replay_carries_every_restricted_source_as_a_labeled_fixture():
    sources = {item.source for item in ReplayDriver().generate("rainfall_shock", 0).observations}
    assert sources >= {"imd", "agmarknet", "msp", "bhuvan", "soil", "sentinel2", "advisory", "farmer"}
