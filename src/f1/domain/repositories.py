"""Interfaces (contratos) de acesso a dados.

O dominio depende apenas destas abstracoes; quem implementa e a camada de
ingestao. Assim da para trocar a fonte de dados (ou usar mocks nos testes)
sem mexer na regra de negocio.
"""

from abc import ABC, abstractmethod

from f1.domain.models import Driver, Lap, Meeting, Session


class MeetingRepository(ABC):
    @abstractmethod
    def list_meetings(self, year: int) -> list[Meeting]:
        """Lista os meetings (fins de semana de corrida) de uma temporada."""


class SessionRepository(ABC):
    @abstractmethod
    def list_sessions(self, meeting_key: int) -> list[Session]:
        """Lista as sessoes de um meeting."""


class DriverRepository(ABC):
    @abstractmethod
    def list_drivers(self, session_key: int) -> list[Driver]:
        """Lista os pilotos de uma sessao."""


class LapRepository(ABC):
    @abstractmethod
    def list_laps(
        self, session_key: int, driver_number: int | None = None
    ) -> list[Lap]:
        """Lista as voltas de uma sessao (opcionalmente de um piloto)."""
