"""Deterministic replay recipes used by the demo and acceptance tests."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    description: str


SCENARIOS: tuple[Scenario, ...] = (
    Scenario("normal", "Fresh, low-shock observations"),
    Scenario("rainfall_shock", "Drought + price crash + opted-in due window"),
    Scenario("price_crash", "Mandi price crash without a rainfall shock"),
    Scenario("due_window", "Opted-in repayment window without acute weather shock"),
    Scenario("stale_data", "The last-good feed is past its TTL"),
)

SCENARIO_IDS = frozenset(item.scenario_id for item in SCENARIOS)
