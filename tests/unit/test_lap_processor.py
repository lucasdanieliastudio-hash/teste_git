"""Testes das funcoes puras de processamento (nao precisam de mock)."""

import csv
import io

import pytest

from f1.domain.models import DEFAULT_TEAM_COLOUR, FastestLapEntry, Lap
from f1.processing.lap_processor import (
    average_lap_time,
    best_lap_per_driver,
    build_driver_index,
    compute_top_n_laps,
    filter_valid_laps,
    format_gap,
    format_lap_time,
    rows_to_csv,
    to_table_rows,
)


def test_filter_valid_laps_removes_pit_out_and_untimed_laps(laps):
    valid = filter_valid_laps(laps)

    assert len(valid) == 7
    assert all(lap.lap_duration is not None for lap in valid)
    assert not any(lap.is_pit_out_lap for lap in valid)


def test_filter_valid_laps_removes_zero_duration():
    lap = Lap(driver_number=1, lap_number=1, lap_duration=0.0)
    assert filter_valid_laps([lap]) == []


def test_build_driver_index_maps_number_to_driver(drivers):
    index = build_driver_index(drivers)

    assert set(index) == {1, 4, 16}
    assert index[16].name_acronym == "LEC"


def test_best_lap_per_driver_keeps_one_lap_each(laps):
    best = {lap.driver_number: lap.lap_duration for lap in best_lap_per_driver(laps)}

    assert best == {1: 94.456, 16: 94.900, 4: 94.700, 44: 97.000}


def test_compute_top_n_orders_by_lap_time(laps, drivers):
    top = compute_top_n_laps(laps, build_driver_index(drivers), n=3)

    assert [entry.lap_duration for entry in top] == [94.456, 94.700, 94.900]
    assert [entry.position for entry in top] == [1, 2, 3]
    assert top[0].name_acronym == "VER"
    assert top[0].team_colour == "#3671C6"


def test_compute_top_n_calculates_gap_to_first(laps, drivers):
    top = compute_top_n_laps(laps, build_driver_index(drivers), n=3)

    assert top[0].gap_to_first == 0.0
    assert top[1].gap_to_first == pytest.approx(0.244)
    assert top[2].gap_to_first == pytest.approx(0.444)


def test_compute_top_n_can_repeat_driver_by_default(laps, drivers):
    top = compute_top_n_laps(laps, build_driver_index(drivers), n=6)

    numbers = [entry.driver_number for entry in top]
    assert numbers.count(16) == 2


def test_compute_top_n_one_per_driver(laps, drivers):
    top = compute_top_n_laps(
        laps, build_driver_index(drivers), n=10, one_per_driver=True
    )

    numbers = [entry.driver_number for entry in top]
    assert len(numbers) == len(set(numbers)) == 4


def test_compute_top_n_handles_unknown_driver(laps, drivers):
    top = compute_top_n_laps(
        laps, build_driver_index(drivers), n=10, one_per_driver=True
    )

    unknown = next(entry for entry in top if entry.driver_number == 44)
    assert unknown.driver_name == "Piloto #44"
    assert unknown.team_colour == DEFAULT_TEAM_COLOUR
    assert unknown.team_name is None


def test_compute_top_n_returns_less_when_not_enough_laps(laps, drivers):
    assert len(compute_top_n_laps(laps, build_driver_index(drivers), n=50)) == 7


def test_compute_top_n_empty_input():
    assert compute_top_n_laps([], {}, n=5) == []


def test_compute_top_n_tie_breaks_by_earlier_lap():
    laps = [
        Lap(driver_number=2, lap_number=5, lap_duration=90.0),
        Lap(driver_number=1, lap_number=7, lap_duration=90.0),
        Lap(driver_number=3, lap_number=5, lap_duration=90.0),
    ]
    top = compute_top_n_laps(laps, {}, n=3)
    assert [(e.lap_number, e.driver_number) for e in top] == [(5, 2), (5, 3), (7, 1)]


@pytest.mark.parametrize("n", [0, -1])
def test_compute_top_n_rejects_invalid_n(laps, n):
    with pytest.raises(ValueError):
        compute_top_n_laps(laps, {}, n=n)


def test_average_lap_time(laps, drivers):
    top = compute_top_n_laps(laps, build_driver_index(drivers), n=3)
    assert average_lap_time(top) == pytest.approx(94.685)


def test_average_lap_time_empty():
    assert average_lap_time([]) is None


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (92.345, "1:32.345"),
        (60.0, "1:00.000"),
        (59.9996, "1:00.000"),
        (45.1, "45.100"),
        (125.0, "2:05.000"),
        (None, "-"),
        (-1.0, "-"),
    ],
)
def test_format_lap_time(seconds, expected):
    assert format_lap_time(seconds) == expected


@pytest.mark.parametrize(
    ("gap", "expected"), [(0.0, "-"), (0.2441, "+0.244"), (1.5, "+1.500")]
)
def test_format_gap(gap, expected):
    assert format_gap(gap) == expected


def test_to_table_rows(laps, drivers):
    top = compute_top_n_laps(laps, build_driver_index(drivers), n=2)
    rows = to_table_rows(top)

    assert rows[0]["Pos"] == 1
    assert rows[0]["Piloto"] == "Max VERSTAPPEN"
    assert rows[0]["Tempo"] == "1:34.456"
    assert rows[0]["Gap"] == "-"
    assert rows[1]["Gap"] == "+0.244"
    assert rows[0]["Speed trap (km/h)"] == 312


def test_to_table_rows_missing_optional_fields():
    entry = FastestLapEntry(
        position=1,
        driver_number=9,
        driver_name="Piloto #9",
        lap_number=3,
        lap_duration=80.0,
    )
    row = to_table_rows([entry])[0]
    assert row["Equipe"] == ""
    assert row["S1"] == "-"
    assert row["Speed trap (km/h)"] == ""


def test_rows_to_csv_escapes_commas():
    rows = [{"Piloto": "Silva, Joao", "Tempo": "1:30.000"}]
    text = rows_to_csv(rows)

    parsed = list(csv.DictReader(io.StringIO(text)))
    assert parsed == [{"Piloto": "Silva, Joao", "Tempo": "1:30.000"}]


def test_rows_to_csv_empty():
    assert rows_to_csv([]) == ""
