from datetime import date

import httpx
import pytest

from adapters.core.interfaces import SignalRequest
from adapters.sources.agmarknet.real import AgmarknetRealAdapter
from adapters.sources.agristack.real import AgriStackRealAdapter
from adapters.sources.bhuvan.real import BhuvanRealAdapter
from adapters.sources.imd.real import IMDRealAdapter
from adapters.sources.msp.real import MSPRealAdapter
from adapters.sources.sentinel2.real import Sentinel2RealAdapter
from adapters.sources.soil.real import SoilRealAdapter


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
    assert all(row.ttl.days == 3 for row in rows)
    price = next(row for row in rows if row.metric == "mandi_price_deviation_pct")
    assert price.value == {"deviation_pct": -20.0, "below_msp": True}


def test_agmarknet_ogd_endpoint_uses_data_gov_query_contract():
    seen = {}

    def handler(request: httpx.Request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"records": []})

    adapter = AgmarknetRealAdapter(
        "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24",
        api_key="ogd-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    adapter.fetch(request())
    assert seen["params"]["api-key"] == "ogd-key"
    assert seen["params"]["format"] == "json"
    assert seen["params"]["limit"] == "1000"
    assert seen["params"]["filters[commodity]"] == "cotton"


def test_real_adapter_fails_closed_without_endpoint_and_records_health():
    adapter = IMDRealAdapter()
    with pytest.raises(RuntimeError, match="configured endpoint"):
        adapter.fetch(request())
    state = adapter.health()
    assert not state.ok
    assert "configured endpoint" in (state.last_error or "")


def test_bhuvan_real_adapter_parses_geojson_coordinates_and_layers():
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json={
                "type": "FeatureCollection",
                "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [73.8, 20.2]}, "properties": {"elevation": 620, "land_use_class": "cropland"}}],
            },
        )
    )
    rows = BhuvanRealAdapter("https://bhuvan.example.test/search", client=httpx.Client(transport=transport)).fetch(request())
    assert {row.metric for row in rows} >= {"village_coordinates", "elevation_m", "land_use_class"}
    assert next(row for row in rows if row.metric == "village_coordinates").value == {"lat": 20.2, "lon": 73.8}


def test_agristack_real_adapter_requires_storage_consent_and_prefills_profile():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "data": {
                    "village_id": "V123",
                    "crop_name": "cotton",
                    "land_area_band": "small",
                    "irrigation_type": "rainfed",
                    "updated_at": "2026-08-07T00:00:00Z",
                }
            },
        )
    )
    adapter = AgriStackRealAdapter(
        "https://apisetu.example.test/farmer",
        api_key="api-setu-key",
        client=httpx.Client(transport=transport),
    )
    with pytest.raises(PermissionError):
        adapter.fetch_profile(type("Consent", (), {"storage": False})(), "farmer-token")
    profile = adapter.fetch_profile(type("Consent", (), {"storage": True})(), "farmer-token")
    assert profile.farmer_ref == "farmer-token"
    assert profile.village_id == "V123"
    assert profile.crop == "cotton"
    assert profile.irrigation_type == "rainfed"


def test_msp_real_adapter_parses_versioned_reference_price():
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"data": [{"Crops": "Cotton", "MSP 2026-27": "8260", "season": "KMS 2026-27"}]}))
    rows = MSPRealAdapter("https://msp.example.test/table", client=httpx.Client(transport=transport)).fetch(request())
    assert rows[0].metric == "msp_price"
    assert rows[0].value["price"] == 8260
    assert rows[0].ttl.days == 365


def test_sentinel2_real_adapter_uses_oauth_and_derives_ndvi_anomaly():
    seen: list[str] = []

    def handler(req: httpx.Request):
        seen.append(req.method)
        if req.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": "access-token", "expires_in": 300})
        assert req.headers.get("authorization") == "Bearer access-token"
        return httpx.Response(200, json={"data": [{"date": "2026-08-07", "ndvi": 0.35, "ndvi_baseline": 0.5}]})

    adapter = Sentinel2RealAdapter(
        "https://sentinel.example.test/indices",
        client_id="client-id",
        client_secret="client-secret",
        token_url="https://sentinel.example.test/token",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    rows = adapter.fetch(request())
    assert rows[0].metric == "ndvi_anomaly_pct"
    assert rows[0].value == pytest.approx(30)
    assert seen == ["POST", "GET"]


def test_soil_real_adapter_parses_soil_health_card_fields():
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, json={"records": [{"sample_date": "2026-07-01", "soil_retention": "poor", "pH": 6.8, "organic_carbon": 0.42}]})
    )
    rows = SoilRealAdapter("https://soil.example.test/health", client=httpx.Client(transport=transport)).fetch(request())
    assert {row.metric for row in rows} >= {"soil_retention", "soil_ph", "soil_organic_carbon_pct"}
    assert next(row for row in rows if row.metric == "soil_retention").value == "poor"
