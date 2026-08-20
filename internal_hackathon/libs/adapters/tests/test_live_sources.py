from datetime import date

import httpx
import pytest

from adapters.core.interfaces import SignalRequest
from adapters.sources.agmarknet.real import AgmarknetRealAdapter
from adapters.sources.imd.real import IMDRealAdapter


def request(**overrides):
    values = {
        "village_id": "V123",
        "district_id": "D1",
        "commodity": "cotton",
        "date_range": (date(2026, 8, 1), date(2026, 8, 7)),
    }
    values.update(overrides)
    return SignalRequest(**values)


def test_imd_real_adapter_parses_official_rainfall_fields_and_headers():
    seen = {}

    def handler(req: httpx.Request):
        seen["url"] = str(req.url)
        seen["authorization"] = req.headers.get("authorization")
        return httpx.Response(
            200,
            json=[
                {
                    "District": "Nashik",
                    "Date": "2026-08-07",
                    "Daily Actual": "7.5",
                    "Daily Normal": "10.0",
                    "Daily Departure Per": "-25%",
                }
            ],
        )

    adapter = IMDRealAdapter(
        "https://api.example.test/districtrainfall",
        api_key="secret-not-in-url",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    rows = adapter.fetch(request())
    assert rows[0].metric == "rainfall_deviation_pct"
    assert rows[0].value == -25
    assert rows[0].village_id == "V123"
    assert "start_date=2026-08-01" in seen["url"]
    assert seen["authorization"] == "Bearer secret-not-in-url"
    assert adapter.health().ok


def test_imd_derives_departure_when_only_actual_and_normal_are_available():
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, json={"data": [{"date": "2026-08-07", "Daily Actual": 5, "Daily Normal": 10}]})
    )
    adapter = IMDRealAdapter("https://api.example.test/weather", client=httpx.Client(transport=transport))
    assert adapter.fetch(request())[0].value == -50


def test_agmarknet_emits_modal_and_explainable_price_shock():
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json={
                "records": [
                    {
                        "commodity": "Cotton",
                        "market": "Nashik",
                        "date": "2026-08-07",
                        "modal_price": "5,000",
                        "seasonal_median": 6250,
                        "msp": 5700,
                    }
                ]
            },
        )
    )
    adapter = AgmarknetRealAdapter("https://api.example.test/mandi", client=httpx.Client(transport=transport))
    rows = adapter.fetch(request())
    assert {row.metric for row in rows} == {"mandi_modal_price", "mandi_price_deviation_pct"}
    price = next(row for row in rows if row.metric == "mandi_price_deviation_pct")
    assert price.value == {"deviation_pct": -20.0, "below_msp": True}


def test_real_adapter_fails_closed_without_endpoint_and_records_health():
    adapter = IMDRealAdapter()
    with pytest.raises(RuntimeError, match="configured endpoint"):
        adapter.fetch(request())
    state = adapter.health()
    assert not state.ok
    assert "configured endpoint" in (state.last_error or "")
