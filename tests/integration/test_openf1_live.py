"""Testes de integracao contra a API real (precisam de internet).

Nao rodam por padrao. Para rodar:
    poetry run pytest tests/integration/ -m integration --no-cov
"""

import pytest

from f1.domain.services import F1DashboardService
from f1.ingestion.http_client import HttpClient
from f1.ingestion.openf1_client import (
    OpenF1DriverRepository,
    OpenF1LapRepository,
    OpenF1MeetingRepository,
    OpenF1SessionRepository,
)
from f1.utils.config import load_settings

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def service():
    settings = load_settings()
    http = HttpClient(base_url=settings.base_url, timeout=30, max_retries=3)
    yield F1DashboardService(
        OpenF1MeetingRepository(http),
        OpenF1SessionRepository(http),
        OpenF1DriverRepository(http),
        OpenF1LapRepository(http),
    )
    http.close()


def test_live_2024_season_end_to_end(service):
    meetings = service.list_meetings(2024)
    assert len(meetings) >= 20

    bahrain = next(
        m
        for m in meetings
        if m.country_name == "Bahrain" and "Grand Prix" in m.meeting_name
    )
    sessions = service.list_sessions(bahrain.meeting_key)
    race = next(s for s in sessions if s.session_name == "Race")

    summary = service.get_session_summary(race.session_key, n=5)

    assert summary.drivers_count >= 20
    assert len(summary.top_laps) == 5
    times = [entry.lap_duration for entry in summary.top_laps]
    assert times == sorted(times)
    assert 85 < times[0] < 110  # volta de corrida no Bahrein fica nessa faixa
