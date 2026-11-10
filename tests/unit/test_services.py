"""Testes do F1DashboardService com repositorios mockados."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from f1.domain.models import Meeting, Session
from f1.domain.repositories import (
    DriverRepository,
    LapRepository,
    MeetingRepository,
    SessionRepository,
)
from f1.domain.services import F1DashboardService


@pytest.fixture
def repos(laps, drivers):
    meetings = MagicMock(spec=MeetingRepository)
    sessions = MagicMock(spec=SessionRepository)
    driver_repo = MagicMock(spec=DriverRepository)
    lap_repo = MagicMock(spec=LapRepository)
    driver_repo.list_drivers.return_value = drivers
    lap_repo.list_laps.return_value = laps
    return meetings, sessions, driver_repo, lap_repo


@pytest.fixture
def service(repos) -> F1DashboardService:
    return F1DashboardService(*repos)


def _dt(month: int, day: int) -> datetime:
    return datetime(2024, month, day, tzinfo=UTC)


def test_list_meetings_sorted_by_date(service, repos):
    repos[0].list_meetings.return_value = [
        Meeting(meeting_key=3, meeting_name="C", year=2024, date_start=_dt(4, 5)),
        Meeting(meeting_key=9, meeting_name="Sem data", year=2024),
        Meeting(meeting_key=1, meeting_name="A", year=2024, date_start=_dt(3, 1)),
    ]

    result = service.list_meetings(2024)

    assert [m.meeting_key for m in result] == [1, 3, 9]
    repos[0].list_meetings.assert_called_once_with(2024)


def test_list_sessions_sorted_by_date(service, repos):
    repos[1].list_sessions.return_value = [
        Session(session_key=2, session_name="Race", date_start=_dt(3, 2)),
        Session(session_key=1, session_name="Qualifying", date_start=_dt(3, 1)),
    ]

    result = service.list_sessions(1229)

    assert [s.session_name for s in result] == ["Qualifying", "Race"]
    repos[1].list_sessions.assert_called_once_with(1229)


def test_get_fastest_laps(service, repos):
    top = service.get_fastest_laps(9472, n=2)

    assert [entry.name_acronym for entry in top] == ["VER", "NOR"]
    repos[3].list_laps.assert_called_once_with(9472)
    repos[2].list_drivers.assert_called_once_with(9472)


def test_get_fastest_laps_one_per_driver(service):
    top = service.get_fastest_laps(9472, n=10, one_per_driver=True)
    assert len(top) == 4


def test_get_session_summary(service):
    summary = service.get_session_summary(9472, n=3)

    assert summary.session_key == 9472
    assert summary.total_laps == 9
    assert summary.valid_laps == 7
    assert summary.drivers_count == 3
    assert len(summary.top_laps) == 3
    assert summary.fastest.name_acronym == "VER"
    assert summary.average_top_lap == pytest.approx(94.685)


def test_get_session_summary_without_laps(service, repos):
    repos[3].list_laps.return_value = []

    summary = service.get_session_summary(9472)

    assert summary.top_laps == []
    assert summary.fastest is None
    assert summary.average_top_lap is None
