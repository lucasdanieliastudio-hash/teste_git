"""Cliente HTTP com timeout, retry e backoff exponencial."""

import time
from collections.abc import Callable
from typing import Any

import httpx

from f1.utils.logger import get_logger

logger = get_logger(__name__)

RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class HttpClientError(Exception):
    """Falha ao buscar dados na API depois de esgotar as tentativas."""


class HttpClient:
    """Wrapper fino sobre ``httpx.Client`` focado em APIs JSON de leitura.

    - Repete a chamada em erros de rede, timeout, 429 e 5xx.
    - Trata 404 como "sem resultados" (a OpenF1 responde 404 quando o filtro
      nao encontra nada).
    - ``transport`` e ``sleep`` podem ser injetados para testes.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_retries < 1:
            raise ValueError("max_retries precisa ser >= 1")
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._sleep = sleep
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            transport=transport,
            headers={"Accept": "application/json", "User-Agent": "f1-dashboard/0.1"},
        )

    def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Faz um GET e devolve sempre uma lista de objetos JSON."""
        last_error: str = "erro desconhecido"
        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.get(path, params=params)
            except httpx.TimeoutException as exc:
                last_error = f"timeout ({exc.__class__.__name__})"
            except httpx.TransportError as exc:
                last_error = f"erro de rede ({exc})"
            else:
                if response.status_code == 404:
                    logger.info("Sem resultados para %s %s", path, params)
                    return []
                if response.status_code in RETRYABLE_STATUS:
                    last_error = f"HTTP {response.status_code}"
                elif response.is_error:
                    raise HttpClientError(
                        f"HTTP {response.status_code} em {path}: {response.text[:200]}"
                    )
                else:
                    return self._parse(response, path)

            if attempt < self._max_retries:
                delay = self._backoff_factor * (2 ** (attempt - 1))
                logger.warning(
                    "Tentativa %s/%s falhou em %s (%s). Nova tentativa em %.1fs",
                    attempt,
                    self._max_retries,
                    path,
                    last_error,
                    delay,
                )
                self._sleep(delay)

        raise HttpClientError(
            f"Falha em {path} apos {self._max_retries} tentativas: {last_error}"
        )

    @staticmethod
    def _parse(response: httpx.Response, path: str) -> list[dict[str, Any]]:
        try:
            data = response.json()
        except ValueError as exc:
            raise HttpClientError(f"Resposta invalida (nao e JSON) em {path}") from exc
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        raise HttpClientError(f"Formato inesperado em {path}: {type(data).__name__}")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
