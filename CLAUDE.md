# CLAUDE.md

Guia para o Claude Code trabalhar neste repositório.

## Contexto

Dashboard Streamlit com as voltas mais rápidas por circuito usando a API OpenF1.
Padrões obrigatórios em `.claude/SKILL.md`; plano do projeto em `.claude/plan.md`;
resumo da API em `.claude/doc_api.md`.

## Comandos

```bash
poetry install --with dev,docs        # instalar tudo
poetry run task app                   # abrir o dashboard (http://localhost:8501)
poetry run task test                  # testes unitários + cobertura
poetry run task test-integration      # testes contra a API real
poetry run task lint                  # ruff check
poetry run task format                # ruff format
poetry run task docs                  # docs em http://127.0.0.1:8000
poetry run pytest tests/unit/test_lap_processor.py::test_format_lap_time   # um teste
```

## Arquitetura

UI → domain ← ingestion / processing

- `dashboard.py`: só liga as peças e desenha a tela.
- `domain/services.py`: `F1DashboardService` depende só das ABCs de `domain/repositories.py`.
- `processing/lap_processor.py`: funções puras, testadas sem mock.
- `ingestion/`: `HttpClient` (retry/backoff, 404 = vazio) e repositórios OpenF1.

## Regras

- README.md somente com caracteres ASCII.
- Sem `print`: use `get_logger(__name__)`.
- Testes unitários nunca chamam a rede.
- Cobertura mínima de 50% (CI falha abaixo).
- Docs são publicadas no GitHub Pages a cada push na `main`.
