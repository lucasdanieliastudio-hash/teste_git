"""Testes do HttpClient usando httpx.MockTransport (nenhuma chamada real)."""

import httpx
import pytest

from f1.ingestion.http_client import HttpClient, HttpClientError

BASE_URL = "https://api.openf1.org/v1"


def make_client(
    handler, max_retries: int = 3, sleeps: list | None = None
) -> HttpClient:
    recorded = sleeps if sleeps is not None else []
    return HttpClient(
        base_url=BASE_URL,
        max_retries=max_retries,
        transport=httpx.MockTransport(handler),
        sleep=recorded.append,
    )


def test_get_returns_list_and_sends_params():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json=[{"a": 1}, {"a": 2}])

    with make_client(handler) as client:
        data = client.get("/laps", {"session_key": 9472})

    assert data == [{"a": 1}, {"a": 2}]
    assert seen["url"] == f"{BASE_URL}/laps?session_key=9472"


def test_get_wraps_single_object_in_list():
    client = make_client(lambda request: httpx.Response(200, json={"a": 1}))
    assert client.get("/x") == [{"a": 1}]


def test_get_drops_non_object_items():
    client = make_client(lambda request: httpx.Response(200, json=[{"a": 1}, 3, "x"]))
    assert client.get("/x") == [{"a": 1}]


def test_404_means_no_results():
    client = make_client(
        lambda request: httpx.Response(404, json={"detail": "No results found."})
    )
    assert client.get("/laps", {"session_key": 1}) == []


def test_retries_on_server_error_then_succeeds():
    calls = {"n": 0}
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=[{"ok": True}])

    client = make_client(handler, sleeps=sleeps)

    assert client.get("/sessions") == [{"ok": True}]
    assert calls["n"] == 3
    assert sleeps == [0.5, 1.0]  # backoff exponencial


def test_retries_on_rate_limit():
    responses = iter([httpx.Response(429), httpx.Response(200, json=[])])
    client = make_client(lambda request: next(responses))
    assert client.get("/x") == []


def test_raises_after_exhausting_retries_on_timeout():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ReadTimeout("lento demais", request=request)

    client = make_client(handler, max_retries=2)

    with pytest.raises(HttpClientError, match="2 tentativas"):
        client.get("/laps")
    assert calls["n"] == 2


def test_raises_after_network_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sem internet", request=request)

    with pytest.raises(HttpClientError, match="erro de rede"):
        make_client(handler, max_retries=1).get("/laps")


def test_client_error_is_not_retried():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(400, text="bad request")

    with pytest.raises(HttpClientError, match="HTTP 400"):
        make_client(handler).get("/laps")
    assert calls["n"] == 1


def test_invalid_json_raises():
    client = make_client(lambda request: httpx.Response(200, text="<html>oops</html>"))
    with pytest.raises(HttpClientError, match="nao e JSON"):
        client.get("/x")


def test_unexpected_json_type_raises():
    client = make_client(lambda request: httpx.Response(200, json="texto"))
    with pytest.raises(HttpClientError, match="Formato inesperado"):
        client.get("/x")


def test_max_retries_must_be_positive():
    with pytest.raises(ValueError):
        HttpClient(base_url=BASE_URL, max_retries=0)
