"""Testes do carregamento de configuracoes."""

from f1.utils.config import DEFAULT_BASE_URL, Settings, load_settings
from f1.utils.logger import get_logger

ENV_VARS = [
    "OPENF1_BASE_URL",
    "OPENF1_TIMEOUT",
    "OPENF1_MAX_RETRIES",
    "DEFAULT_YEAR",
    "TOP_N_LAPS",
    "ENVIRONMENT",
]


def _clear(monkeypatch) -> None:
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_defaults(monkeypatch):
    _clear(monkeypatch)
    assert load_settings(load_env_file=False) == Settings()
    assert Settings().base_url == DEFAULT_BASE_URL


def test_env_overrides(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OPENF1_BASE_URL", "http://localhost:9000/v1/")
    monkeypatch.setenv("OPENF1_TIMEOUT", "2.5")
    monkeypatch.setenv("OPENF1_MAX_RETRIES", "5")
    monkeypatch.setenv("DEFAULT_YEAR", "2023")
    monkeypatch.setenv("TOP_N_LAPS", "10")
    monkeypatch.setenv("ENVIRONMENT", "production")

    settings = load_settings(load_env_file=False)

    assert settings.base_url == "http://localhost:9000/v1"
    assert settings.timeout_seconds == 2.5
    assert settings.max_retries == 5
    assert settings.default_year == 2023
    assert settings.top_n_laps == 10
    assert settings.environment == "production"


def test_invalid_values_fall_back_to_defaults(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OPENF1_TIMEOUT", "rapido")
    monkeypatch.setenv("DEFAULT_YEAR", "dois mil")
    monkeypatch.setenv("TOP_N_LAPS", "")
    monkeypatch.setenv("OPENF1_MAX_RETRIES", "0")

    settings = load_settings(load_env_file=False)

    assert settings.timeout_seconds == 10.0
    assert settings.default_year == 2024
    assert settings.top_n_laps == 5
    assert settings.max_retries == 1  # nunca menos que 1 tentativa


def test_get_logger_returns_named_logger():
    assert get_logger("f1.teste").name == "f1.teste"
