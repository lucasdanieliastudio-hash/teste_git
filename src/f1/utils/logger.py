"""Fabrica de loggers padronizada para todo o projeto."""

import logging
import os

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured = False


def _configure_root() -> None:
    global _configured
    if _configured:
        return
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format=_LOG_FORMAT)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger configurado. Use sempre ``get_logger(__name__)``."""
    _configure_root()
    return logging.getLogger(name)
