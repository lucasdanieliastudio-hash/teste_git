"""Testes da tela Streamlit com o AppTest oficial e a API simulada."""

from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from f1.ingestion.http_client import HttpClient, HttpClientError

APP_PATH = str(Path(__file__).resolve().parents[2] / "src" / "f1" / "dashboard.py")


def _clear_caches() -> None:
    st.cache_data.clear()
    st.cache_resource.clear()


@pytest.fixture
def fake_api(monkeypatch, driver_payloads, lap_payloads):
    routes = {
        "/meetings": [
            {
                "meeting_key": 1229,
                "meeting_name": "Bahrain Grand Prix",
                "year": 2024,
                "country_name": "Bahrain",
                "circuit_short_name": "Sakhir",
                "date_start": "2024-02-29T11:30:00+00:00",
            }
        ],
        "/sessions": [
            {
                "session_key": 9472,
                "session_name": "Race",
                "date_start": "2024-03-02T15:00:00+00:00",
            },
            {
                "session_key": 9471,
                "session_name": "Qualifying",
                "date_start": "2024-03-01T16:00:00+00:00",
            },
        ],
        "/drivers": driver_payloads,
        "/laps": lap_payloads,
    }

    def fake_get(self, path, params=None):
        return routes.get(path, [])

    monkeypatch.setattr(HttpClient, "get", fake_get)
    monkeypatch.setenv("DEFAULT_YEAR", "2024")
    monkeypatch.setenv("TOP_N_LAPS", "5")
    _clear_caches()
    yield routes
    _clear_caches()


def run_app() -> AppTest:
    return AppTest.from_file(APP_PATH, default_timeout=30).run()


def test_dashboard_renders_ranking(fake_api):
    app = run_app()

    assert not app.exception
    assert "F1 Dashboard" in app.title[0].value
    assert app.selectbox[0].value == 2024
    assert app.selectbox[2].value.session_name == "Race"  # corrida vem selecionada

    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Volta mais rapida"] == "1:34.456"
    assert metrics["Piloto"] == "VER"
    assert metrics["Voltas validas"] == "7/9"
    assert len(app.dataframe[0].value) == 5


def test_dashboard_ranking_size_and_one_per_driver(fake_api):
    app = run_app()
    app.slider[0].set_value(10).run()
    assert len(app.dataframe[0].value) == 7

    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 4


def test_dashboard_session_without_laps(fake_api):
    fake_api["/laps"] = []
    app = run_app()

    assert not app.exception
    assert "Ainda nao ha voltas" in app.info[0].value


def test_dashboard_without_meetings(fake_api):
    fake_api["/meetings"] = []
    app = run_app()

    assert not app.exception
    assert "Nenhum GP encontrado" in app.warning[0].value


def test_dashboard_shows_friendly_error_when_api_fails(monkeypatch):
    def failing_get(self, path, params=None):
        raise HttpClientError("Falha em /meetings apos 3 tentativas")

    monkeypatch.setattr(HttpClient, "get", failing_get)
    _clear_caches()
    app = run_app()
    _clear_caches()

    assert not app.exception
    assert "Nao consegui falar com a API" in app.error[0].value
