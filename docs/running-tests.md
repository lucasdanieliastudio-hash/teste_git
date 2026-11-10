# Testes

## Rodando

```bash
poetry run task test                 # unitários + relatório de cobertura
poetry run pytest -v                 # tudo, com nome de cada teste
poetry run pytest tests/unit/test_services.py            # um arquivo
poetry run pytest -k "one_per_driver"                    # por nome
poetry run task test-integration     # API real (precisa de internet)
```

A cobertura mínima é **50%**: abaixo disso o `pytest` (e o CI) falham. Hoje ela fica perto de **98%**.

## O que cada arquivo testa

| Arquivo | Foco | Técnica |
|---|---|---|
| `test_lap_processor.py` | filtro, ranking, desempate, formatação, CSV | funções puras, sem mock |
| `test_models.py` | parsing dos payloads, cor da equipe, imutabilidade | Pydantic |
| `test_http_client.py` | 404, retry em 5xx/429/timeout, backoff, erros | `httpx.MockTransport` |
| `test_openf1_client.py` | parâmetros enviados, itens inválidos, duplicados | `httpx.MockTransport` |
| `test_services.py` | orquestração do serviço | `MagicMock` dos repositórios |
| `test_config.py` | leitura do `.env` e valores inválidos | `monkeypatch` |
| `test_dashboard.py` | a tela inteira (cards, tabela, slider, toggle, erros) | `streamlit.testing.AppTest` |
| `integration/test_openf1_live.py` | ponta a ponta no GP do Bahrein 2024 | API real |

## Fixtures

Os payloads de exemplo ficam em `tests/conftest.py` e seguem o formato real da OpenF1 (inclusive com campos extras e valores `null`), para garantir que o parsing aguenta dados reais.

## Testes de integração

Marcados com `@pytest.mark.integration` e **excluídos por padrão** (`-m 'not integration'` no `pyproject.toml`), porque dependem de internet e da disponibilidade da API.
