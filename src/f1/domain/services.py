"""Servico de aplicacao que orquestra repositorios e processamento."""

from f1.domain.models import FastestLapEntry, Meeting, Session, SessionSummary
from f1.domain.repositories import (
    DriverRepository,
    LapRepository,
    MeetingRepository,
    SessionRepository,
)
from f1.processing.lap_processor import (
    average_lap_time,
    build_driver_index,
    compute_top_n_laps,
    filter_valid_laps,
)
from f1.utils.logger import get_logger

logger = get_logger(__name__)


def _sort_by_date(items: list) -> list:
    # Itens sem data vao para o final, mantendo a ordem original entre eles.
    return sorted(items, key=lambda item: (item.date_start is None, item.date_start))


class F1DashboardService:
    """Ponto unico que o dashboard usa para obter dados ja processados.

    Recebe os repositorios por injecao de dependencia: nao sabe se os dados vem
    da API, de um arquivo ou de um mock.
    """

    def __init__(
        self,
        meetings: MeetingRepository,
        sessions: SessionRepository,
        drivers: DriverRepository,
        laps: LapRepository,
    ) -> None:
        self._meetings = meetings
        self._sessions = sessions
        self._drivers = drivers
        self._laps = laps

    def list_meetings(self, year: int) -> list[Meeting]:
        """Meetings da temporada em ordem cronologica."""
        return _sort_by_date(self._meetings.list_meetings(year))

    def list_sessions(self, meeting_key: int) -> list[Session]:
        """Sessoes do meeting em ordem cronologica."""
        return _sort_by_date(self._sessions.list_sessions(meeting_key))

    def get_fastest_laps(
        self, session_key: int, n: int = 5, one_per_driver: bool = False
    ) -> list[FastestLapEntry]:
        """Ranking das ``n`` voltas mais rapidas da sessao."""
        laps = self._laps.list_laps(session_key)
        drivers = self._drivers.list_drivers(session_key)
        return compute_top_n_laps(
            laps, build_driver_index(drivers), n=n, one_per_driver=one_per_driver
        )

    def get_session_summary(
        self, session_key: int, n: int = 5, one_per_driver: bool = False
    ) -> SessionSummary:
        """Ranking + numeros gerais da sessao, numa unica ida a API."""
        laps = self._laps.list_laps(session_key)
        drivers = self._drivers.list_drivers(session_key)
        top = compute_top_n_laps(
            laps, build_driver_index(drivers), n=n, one_per_driver=one_per_driver
        )
        valid = filter_valid_laps(laps)
        logger.info(
            "Sessao %s: %s voltas (%s validas), %s pilotos",
            session_key,
            len(laps),
            len(valid),
            len(drivers),
        )
        return SessionSummary(
            session_key=session_key,
            total_laps=len(laps),
            valid_laps=len(valid),
            drivers_count=len(drivers),
            top_laps=top,
            average_top_lap=average_lap_time(top),
        )
