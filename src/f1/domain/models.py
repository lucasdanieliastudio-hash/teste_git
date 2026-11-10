"""Entidades de dominio (Pydantic v2) que espelham os payloads da API OpenF1."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

DEFAULT_TEAM_COLOUR = "#888888"


class OpenF1Model(BaseModel):
    """Base comum: ignora campos extras que a API possa adicionar no futuro."""

    model_config = ConfigDict(extra="ignore", frozen=True)


class Meeting(OpenF1Model):
    """Um fim de semana de corrida (Grande Premio ou teste)."""

    meeting_key: int
    meeting_name: str
    year: int
    country_name: str | None = None
    circuit_short_name: str | None = None
    location: str | None = None
    date_start: datetime | None = None

    @property
    def label(self) -> str:
        circuit = self.circuit_short_name or self.location
        return f"{self.meeting_name} - {circuit}" if circuit else self.meeting_name


class Session(OpenF1Model):
    """Uma sessao dentro de um meeting (treino, classificacao, sprint, corrida)."""

    session_key: int
    session_name: str
    meeting_key: int | None = None
    session_type: str | None = None
    year: int | None = None
    country_name: str | None = None
    circuit_short_name: str | None = None
    date_start: datetime | None = None
    date_end: datetime | None = None


class Driver(OpenF1Model):
    """Piloto inscrito em uma sessao."""

    driver_number: int
    full_name: str | None = None
    name_acronym: str | None = None
    broadcast_name: str | None = None
    team_name: str | None = None
    team_colour: str | None = None
    headshot_url: str | None = None

    @property
    def display_name(self) -> str:
        return self.full_name or self.broadcast_name or f"Piloto #{self.driver_number}"

    @property
    def team_hex(self) -> str:
        """Cor da equipe no formato ``#RRGGBB`` (a API envia sem o ``#``)."""
        colour = (self.team_colour or "").strip().lstrip("#")
        if len(colour) == 6:
            try:
                int(colour, 16)
            except ValueError:
                return DEFAULT_TEAM_COLOUR
            return f"#{colour.upper()}"
        return DEFAULT_TEAM_COLOUR


class Lap(OpenF1Model):
    """Uma volta de um piloto em uma sessao."""

    driver_number: int
    lap_number: int
    lap_duration: float | None = None
    duration_sector_1: float | None = None
    duration_sector_2: float | None = None
    duration_sector_3: float | None = None
    i1_speed: int | None = None
    i2_speed: int | None = None
    st_speed: int | None = None
    is_pit_out_lap: bool = False

    @field_validator("is_pit_out_lap", mode="before")
    @classmethod
    def _none_is_false(cls, value: object) -> object:
        return False if value is None else value


class FastestLapEntry(OpenF1Model):
    """Linha do ranking de voltas mais rapidas (resultado do processamento)."""

    position: int
    driver_number: int
    driver_name: str
    name_acronym: str | None = None
    team_name: str | None = None
    team_colour: str = DEFAULT_TEAM_COLOUR
    lap_number: int
    lap_duration: float
    gap_to_first: float = 0.0
    duration_sector_1: float | None = None
    duration_sector_2: float | None = None
    duration_sector_3: float | None = None
    st_speed: int | None = None


class SessionSummary(OpenF1Model):
    """Visao geral de uma sessao para os cards do dashboard."""

    session_key: int
    total_laps: int
    valid_laps: int
    drivers_count: int
    top_laps: list[FastestLapEntry]
    average_top_lap: float | None = None

    @property
    def fastest(self) -> FastestLapEntry | None:
        return self.top_laps[0] if self.top_laps else None
