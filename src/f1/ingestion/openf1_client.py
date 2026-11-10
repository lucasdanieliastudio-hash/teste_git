"""Implementacoes concretas dos repositorios usando a API OpenF1."""

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ValidationError

from f1.domain.models import Driver, Lap, Meeting, Session
from f1.domain.repositories import (
    DriverRepository,
    LapRepository,
    MeetingRepository,
    SessionRepository,
)
from f1.ingestion.http_client import HttpClient
from f1.utils.logger import get_logger

logger = get_logger(__name__)


def parse_items[T: BaseModel](
    rows: Iterable[dict[str, Any]], model: type[T]
) -> list[T]:
    """Valida cada linha com Pydantic, registrando e pulando as invalidas.

    Um item mal formado nao derruba a consulta inteira.
    """
    items: list[T] = []
    skipped = 0
    for row in rows:
        try:
            items.append(model.model_validate(row))
        except ValidationError as exc:
            skipped += 1
            logger.debug("Item invalido para %s ignorado: %s", model.__name__, exc)
    if skipped:
        logger.warning(
            "%s item(ns) invalido(s) de %s ignorado(s)", skipped, model.__name__
        )
    return items


class OpenF1MeetingRepository(MeetingRepository):
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_meetings(self, year: int) -> list[Meeting]:
        return parse_items(self._http.get("/meetings", {"year": year}), Meeting)


class OpenF1SessionRepository(SessionRepository):
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_sessions(self, meeting_key: int) -> list[Session]:
        rows = self._http.get("/sessions", {"meeting_key": meeting_key})
        return parse_items(rows, Session)


class OpenF1DriverRepository(DriverRepository):
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_drivers(self, session_key: int) -> list[Driver]:
        rows = self._http.get("/drivers", {"session_key": session_key})
        # A API pode repetir o mesmo piloto; fica o primeiro registro de cada numero.
        unique: dict[int, Driver] = {}
        for driver in parse_items(rows, Driver):
            unique.setdefault(driver.driver_number, driver)
        return list(unique.values())


class OpenF1LapRepository(LapRepository):
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_laps(
        self, session_key: int, driver_number: int | None = None
    ) -> list[Lap]:
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return parse_items(self._http.get("/laps", params), Lap)
