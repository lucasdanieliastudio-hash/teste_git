"""Funcoes puras de processamento de voltas (sem I/O, sem efeitos colaterais)."""

import csv
import io
from collections.abc import Iterable

from f1.domain.models import DEFAULT_TEAM_COLOUR, Driver, FastestLapEntry, Lap


def filter_valid_laps(laps: Iterable[Lap]) -> list[Lap]:
    """Mantem so voltas cronometradas: com tempo positivo e que nao sao saida de box."""
    return [
        lap
        for lap in laps
        if lap.lap_duration is not None
        and lap.lap_duration > 0
        and not lap.is_pit_out_lap
    ]


def build_driver_index(drivers: Iterable[Driver]) -> dict[int, Driver]:
    """Indexa os pilotos pelo numero do carro para lookup O(1)."""
    return {driver.driver_number: driver for driver in drivers}


def best_lap_per_driver(laps: Iterable[Lap]) -> list[Lap]:
    """Retorna apenas a melhor volta de cada piloto."""
    best: dict[int, Lap] = {}
    for lap in filter_valid_laps(laps):
        current = best.get(lap.driver_number)
        if current is None or _lap_sort_key(lap) < _lap_sort_key(current):
            best[lap.driver_number] = lap
    return list(best.values())


def compute_top_n_laps(
    laps: Iterable[Lap],
    driver_index: dict[int, Driver],
    n: int = 5,
    one_per_driver: bool = False,
) -> list[FastestLapEntry]:
    """Monta o ranking das ``n`` voltas mais rapidas.

    Args:
        laps: voltas da sessao (validas ou nao; o filtro e aplicado aqui).
        driver_index: pilotos indexados por numero (ver :func:`build_driver_index`).
        n: tamanho do ranking. Precisa ser >= 1.
        one_per_driver: se ``True``, cada piloto aparece no maximo uma vez.

    Raises:
        ValueError: se ``n`` for menor que 1.
    """
    if n < 1:
        raise ValueError("n precisa ser maior ou igual a 1")

    candidates = (
        best_lap_per_driver(laps) if one_per_driver else filter_valid_laps(laps)
    )
    ranked = sorted(candidates, key=_lap_sort_key)[:n]
    if not ranked:
        return []

    fastest_time = ranked[0].lap_duration or 0.0
    return [
        _to_entry(position, lap, driver_index.get(lap.driver_number), fastest_time)
        for position, lap in enumerate(ranked, start=1)
    ]


def average_lap_time(entries: Iterable[FastestLapEntry]) -> float | None:
    """Media dos tempos de volta do ranking (``None`` se vazio)."""
    times = [entry.lap_duration for entry in entries]
    if not times:
        return None
    return round(sum(times) / len(times), 3)


def format_lap_time(seconds: float | None) -> str:
    """Formata segundos como ``m:ss.mmm`` (ex.: ``92.345`` -> ``1:32.345``)."""
    if seconds is None or seconds < 0:
        return "-"
    total_ms = round(seconds * 1000)
    minutes, rest_ms = divmod(total_ms, 60_000)
    secs, ms = divmod(rest_ms, 1000)
    if minutes:
        return f"{minutes}:{secs:02d}.{ms:03d}"
    return f"{secs}.{ms:03d}"


def format_gap(gap: float) -> str:
    """Formata a diferenca para o primeiro colocado (``+0.123`` ou ``-``)."""
    return "-" if gap <= 0 else f"+{gap:.3f}"


def to_table_rows(entries: Iterable[FastestLapEntry]) -> list[dict[str, object]]:
    """Converte o ranking em linhas prontas para exibir em tabela."""
    return [
        {
            "Pos": entry.position,
            "Piloto": entry.driver_name,
            "Sigla": entry.name_acronym or "",
            "Equipe": entry.team_name or "",
            "Volta": entry.lap_number,
            "Tempo": format_lap_time(entry.lap_duration),
            "Gap": format_gap(entry.gap_to_first),
            "S1": format_lap_time(entry.duration_sector_1),
            "S2": format_lap_time(entry.duration_sector_2),
            "S3": format_lap_time(entry.duration_sector_3),
            "Speed trap (km/h)": entry.st_speed if entry.st_speed is not None else "",
        }
        for entry in entries
    ]


def rows_to_csv(rows: list[dict[str, object]]) -> str:
    """Serializa as linhas da tabela em CSV (com escape correto de virgulas)."""
    if not rows:
        return ""
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=list(rows[0].keys()), lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _lap_sort_key(lap: Lap) -> tuple[float, int, int]:
    # Desempate estavel: menor tempo, depois volta mais cedo, depois numero do carro.
    return (lap.lap_duration or float("inf"), lap.lap_number, lap.driver_number)


def _to_entry(
    position: int, lap: Lap, driver: Driver | None, fastest_time: float
) -> FastestLapEntry:
    duration = lap.lap_duration or 0.0
    return FastestLapEntry(
        position=position,
        driver_number=lap.driver_number,
        driver_name=driver.display_name if driver else f"Piloto #{lap.driver_number}",
        name_acronym=driver.name_acronym if driver else None,
        team_name=driver.team_name if driver else None,
        team_colour=driver.team_hex if driver else DEFAULT_TEAM_COLOUR,
        lap_number=lap.lap_number,
        lap_duration=duration,
        gap_to_first=round(duration - fastest_time, 3),
        duration_sector_1=lap.duration_sector_1,
        duration_sector_2=lap.duration_sector_2,
        duration_sector_3=lap.duration_sector_3,
        st_speed=lap.st_speed,
    )
