from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.models import EnergyReadings, GeoCoordinates, MeterExport, MeterPage


def test_health_does_not_require_a_live_portal(monkeypatch) -> None:
    monkeypatch.setenv("URJA_EMAIL", "test@example.test")
    monkeypatch.setenv("URJA_PASSWORD", "not-a-real-password")
    get_settings.cache_clear()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_meter_list_normalizes_the_observed_portal_fields() -> None:
    page = MeterPage.model_validate(
        {
            "data": [
                {
                    "meterId": "M-100",
                    "serialNo": "SN-100",
                    "make": "Acme",
                    "phaseType": "three",
                    "installStatus": "active",
                    "dtCode": "DT-1",
                }
            ],
            "total": 1,
            "page": 1,
        }
    )

    assert page.data[0].meter_id == "M-100"
    assert page.data[0].serial_no == "SN-100"
    assert page.page_size == 20


def test_detail_models_normalize_numeric_strings() -> None:
    geo = GeoCoordinates.model_validate({"latitude": "26.93", "longitude": "75.83"})
    energy = EnergyReadings.model_validate(
        {"data": [{"timestamp": "30/06/2026 23:30", "kwh": "1.5", "kvah": "2.0", "voltR": "230"}]}
    )

    assert geo.latitude == 26.93
    assert energy.data[0].kwh == 1.5
    assert energy.data[0].volt_r == 230


def test_export_model_includes_hierarchy() -> None:
    export = MeterExport.model_validate(
        {
            "total": 1,
            "data": [
                {
                    "meterId": "M-100",
                    "installType": "CT Operated",
                    "build": "v2",
                    "hierarchy": {
                        level: {"name": level.title(), "code": level.upper()}
                        for level in ("zone", "circle", "division", "subdivision", "substation", "feeder", "dt")
                    },
                    "geo": {"lat": 26.9, "lng": 75.8},
                }
            ],
        }
    )

    assert export.data[0].hierarchy.dt.code == "DT"

