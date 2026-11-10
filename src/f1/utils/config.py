"""Carrega as configuracoes do projeto a partir de variaveis de ambiente / .env."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from f1.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_BASE_URL = "https://api.openf1.org/v1"


@dataclass(frozen=True)
class Settings:
    """Configuracoes imutaveis da aplicacao."""

    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: float = 10.0
    max_retries: int = 3
    default_year: int = 2024
    top_n_laps: int = 5
    environment: str = "development"


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Valor invalido para %s=%r; usando %s", name, raw, default)
        return default


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Valor invalido para %s=%r; usando %s", name, raw, default)
        return default


def load_settings(load_env_file: bool = True) -> Settings:
    """Le o ``.env`` (se existir) e monta um objeto :class:`Settings`."""
    if load_env_file:
        load_dotenv()
    return Settings(
        base_url=os.getenv("OPENF1_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        timeout_seconds=_get_float("OPENF1_TIMEOUT", Settings.timeout_seconds),
        max_retries=max(1, _get_int("OPENF1_MAX_RETRIES", Settings.max_retries)),
        default_year=_get_int("DEFAULT_YEAR", Settings.default_year),
        top_n_laps=max(1, _get_int("TOP_N_LAPS", Settings.top_n_laps)),
        environment=os.getenv("ENVIRONMENT", Settings.environment),
    )
