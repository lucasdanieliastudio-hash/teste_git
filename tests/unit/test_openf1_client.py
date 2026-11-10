"""Testes dos repositorios OpenF1 com respostas simuladas."""

import httpx
import pytest

from f1.domain.models import Driver
from f1.ingestion.http_client import HttpClient
from f1.ingestion.openf1_client import (
    OpenF1DriverRepository,
    OpenF1LapRepository,
    OpenF1MeetingRepository,
    OpenF1SessionRepository,
    parse_items,
)


@pytest.fixture
def fake_api(driver_payloads, lap_payloads):
    """Simula a OpenF1 respondendo por endpoint e guarda as requisicoes feitas."""
    requests: list[httpx.Request] = []
    routes = {
        "/v1/meetings": [
            {"meeting_key": 1229, "meeting_name": "Bahrain Grand Prix", "year": 2024},
            {"meeting_name": "sem chave"},  # invalido: sera ignorado
        ],
        "/v1/sessions": [
            {"session_key": 9472, "session_name": "Race", "meeting_key": 1229},
        ],
        "/v1/drivers": [*driver_payloads, driver_payloads[0]],  # piloto duplicado
        "/v1/laps": lap_payloads,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=routes.get(request.url.path, []))

    http = HttpClient(
        base_url="https://api.openf1.org/v1",
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    return http, requests


def test_meeting_repository_skips_invalid_items(fake_api):
    http, requests = fake_api
    meetings = OpenF1MeetingRepository(http).list_meetings(2024)

    assert [m.meeting_key for m in meetings] == [1229]
    assert requests[0].url.params["year"] == "2024"


def test_session_repository(fake_api):
    http, requests = fake_api
    sessions = OpenF1SessionRepository(http).list_sessions(1229)

    assert sessions[0].session_name == "Race"
    assert requests[0].url.params["meeting_key"] == "1229"


def test_driver_repository_removes_duplicates(fake_api):
    http, _ = fake_api
    drivers = OpenF1DriverRepository(http).list_drivers(9472)

    assert [d.driver_number for d in drivers] == [1, 16, 4]


def test_lap_repository_with_and_without_driver_filter(fake_api):
    http, requests = fake_api
    repo = OpenF1LapRepository(http)

    assert len(repo.list_laps(9472)) == 9
    repo.list_laps(9472, driver_number=16)

    assert "driver_number" not in requests[0].url.params
    assert requests[1].url.params["driver_number"] == "16"


def test_parse_items_logs_and_skips(caplog):
    rows = [{"driver_number": 1}, {"driver_number": "abc"}, {}]
    with caplog.at_level("WARNING"):
        drivers = parse_items(rows, Driver)

    assert [d.driver_number for d in drivers] == [1]
    assert "2 item(ns) invalido(s)" in caplog.text
