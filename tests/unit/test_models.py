"""Testes de parsing dos payloads da OpenF1 com os modelos Pydantic."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from f1.domain.models import (
    DEFAULT_TEAM_COLOUR,
    Driver,
    FastestLapEntry,
    Lap,
    Meeting,
    Session,
    SessionSummary,
)


def test_driver_ignores_extra_fields(driver_payloads):
    driver = Driver.model_validate(driver_payloads[0])

    assert driver.driver_number == 1
    assert driver.name_acronym == "VER"
    assert not hasattr(driver, "country_code")


@pytest.mark.parametrize(
    ("colour", "expected"),
    [
        ("3671C6", "#3671C6"),
        ("#e8002d", "#E8002D"),
        ("ff8000 ", "#FF8000"),
        (None, DEFAULT_TEAM_COLOUR),
        ("", DEFAULT_TEAM_COLOUR),
        ("ZZZZZZ", DEFAULT_TEAM_COLOUR),
        ("123", DEFAULT_TEAM_COLOUR),
    ],
)
def test_driver_team_hex(colour, expected):
    assert Driver(driver_number=1, team_colour=colour).team_hex == expected


def test_driver_display_name_fallbacks():
    assert (
        Driver(driver_number=1, full_name="Max VERSTAPPEN").display_name
        == "Max VERSTAPPEN"
    )
    assert (
        Driver(driver_number=1, broadcast_name="M VERSTAPPEN").display_name
        == "M VERSTAPPEN"
    )
    assert Driver(driver_number=99).display_name == "Piloto #99"


def test_lap_parses_payload(lap_payloads):
    lap = Lap.model_validate(lap_payloads[2])

    assert lap.lap_number == 3
    assert lap.lap_duration == pytest.approx(94.456)
    assert lap.st_speed == 312
    assert lap.is_pit_out_lap is False


def test_lap_null_pit_out_becomes_false(lap_payloads):
    lap = Lap.model_validate(lap_payloads[0])
    assert lap.is_pit_out_lap is False
    assert lap.lap_duration is None


def test_lap_requires_driver_number():
    with pytest.raises(ValidationError):
        Lap.model_validate({"lap_number": 1, "lap_duration": 90.0})


def test_meeting_parses_date_and_label():
    meeting = Meeting.model_validate(
        {
            "meeting_key": 1229,
            "meeting_name": "Bahrain Grand Prix",
            "year": 2024,
            "country_name": "Bahrain",
            "circuit_short_name": "Sakhir",
            "location": "Sakhir",
            "date_start": "2024-02-29T11:30:00+00:00",
            "gmt_offset": "03:00:00",
        }
    )

    assert isinstance(meeting.date_start, datetime)
    assert meeting.label == "Bahrain Grand Prix - Sakhir"


def test_meeting_label_without_circuit():
    meeting = Meeting(meeting_key=1, meeting_name="Pre-Season Testing", year=2024)
    assert meeting.label == "Pre-Season Testing"


def test_session_parses_payload():
    session = Session.model_validate(
        {
            "session_key": 9472,
            "session_name": "Race",
            "session_type": "Race",
            "meeting_key": 1229,
            "year": 2024,
            "date_start": "2024-03-02T15:00:00+00:00",
            "date_end": "2024-03-02T17:00:00+00:00",
        }
    )
    assert session.session_type == "Race"
    assert session.date_end > session.date_start


def test_models_are_immutable():
    driver = Driver(driver_number=1)
    with pytest.raises(ValidationError):
        driver.driver_number = 2


def test_session_summary_fastest():
    entry = FastestLapEntry(
        position=1, driver_number=1, driver_name="X", lap_number=2, lap_duration=90.0
    )
    summary = SessionSummary(
        session_key=1, total_laps=10, valid_laps=8, drivers_count=1, top_laps=[entry]
    )
    empty = SessionSummary(
        session_key=1, total_laps=0, valid_laps=0, drivers_count=0, top_laps=[]
    )

    assert summary.fastest == entry
    assert empty.fastest is None
