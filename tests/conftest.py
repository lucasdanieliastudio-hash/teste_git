"""Fixtures compartilhadas: payloads no formato real da API OpenF1."""

import pytest

from f1.domain.models import Driver, Lap


@pytest.fixture
def driver_payloads() -> list[dict]:
    return [
        {
            "driver_number": 1,
            "full_name": "Max VERSTAPPEN",
            "name_acronym": "VER",
            "broadcast_name": "M VERSTAPPEN",
            "team_name": "Red Bull Racing",
            "team_colour": "3671C6",
            "headshot_url": "https://example.com/ver.png",
            "session_key": 9472,
            "meeting_key": 1229,
            "country_code": "NED",
        },
        {
            "driver_number": 16,
            "full_name": "Charles LECLERC",
            "name_acronym": "LEC",
            "team_name": "Ferrari",
            "team_colour": "E8002D",
            "session_key": 9472,
        },
        {
            "driver_number": 4,
            "full_name": "Lando NORRIS",
            "name_acronym": "NOR",
            "team_name": "McLaren",
            "team_colour": "FF8000",
            "session_key": 9472,
        },
    ]


@pytest.fixture
def lap_payloads() -> list[dict]:
    def lap(
        driver: int, number: int, duration: float | None, pit_out: bool | None = False
    ) -> dict:
        return {
            "driver_number": driver,
            "lap_number": number,
            "lap_duration": duration,
            "duration_sector_1": None if duration is None else round(duration * 0.3, 3),
            "duration_sector_2": None if duration is None else round(duration * 0.4, 3),
            "duration_sector_3": None if duration is None else round(duration * 0.3, 3),
            "i1_speed": 290,
            "i2_speed": 275,
            "st_speed": 312,
            "is_pit_out_lap": pit_out,
            "segments_sector_1": [2049, 2049],
            "session_key": 9472,
            "meeting_key": 1229,
            "date_start": "2024-03-02T15:05:00+00:00",
        }

    return [
        lap(1, 1, None, None),  # primeira volta sem tempo
        lap(1, 2, 95.123),
        lap(1, 3, 94.456),  # melhor volta do VER
        lap(1, 4, 101.0, True),  # saida de box: descartada
        lap(16, 2, 95.010),
        lap(16, 3, 94.900),  # melhor volta do LEC
        lap(4, 2, 94.700),  # melhor volta da sessao (NOR)
        lap(4, 3, 96.300),
        lap(44, 2, 97.000),  # piloto que nao veio no endpoint de drivers
    ]


@pytest.fixture
def drivers(driver_payloads: list[dict]) -> list[Driver]:
    return [Driver.model_validate(item) for item in driver_payloads]


@pytest.fixture
def laps(lap_payloads: list[dict]) -> list[Lap]:
    return [Lap.model_validate(item) for item in lap_payloads]
