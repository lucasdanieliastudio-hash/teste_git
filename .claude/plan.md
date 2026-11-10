# plan.md — Dashboard F1 com OpenF1

> Gerado a partir de `@.claude/doc_api.md` e `@.claude/SKILL.md`.
> Para implementar: "Implemente o projeto do @.claude/plan.md, conforme a skill @.claude/SKILL.md".

## 1. Objetivo

Dashboard web em Streamlit que mostra **as voltas mais rápidas de cada circuito** (por sessão) usando os dados históricos gratuitos da OpenF1 (2023+). O usuário escolhe temporada → GP → sessão e vê o ranking com cores das equipes, gap para o primeiro e tempos de setor.

Critério de pronto:
- Dashboard abre em `http://localhost:8501` e mostra o top N de uma sessão real.
- `ruff check .` e `ruff format . --check` sem erros.
- `pytest` verde com cobertura ≥ 50%.
- `mkdocs build --strict` sem erros e docs publicadas pelo CI.

## 2. Stack

| Item | Escolha | Motivo |
|---|---|---|
| Ambiente | Poetry | Obrigatório (SKILL §2) |
| Python | ≥ 3.12 | Sintaxe moderna de tipos |
| HTTP | httpx | Timeout nativo e `MockTransport` para testes |
| Modelos | Pydantic v2 | Validação dos payloads |
| UI | Streamlit + Plotly | Dashboard rápido com gráfico interativo |
| Config | python-dotenv | `.env` local |
| Qualidade | Ruff, pre-commit | SKILL §4 e §7 |
| Testes | pytest, pytest-cov, pytest-mock | SKILL §5 |
| Docs | MkDocs Material | SKILL §6 |
| CI | GitHub Actions | Lint, testes e deploy das docs |

## 3. Arquitetura

```
src/f1/
├── dashboard.py            # composition root Streamlit
├── domain/
│   ├── models.py           # Meeting, Session, Driver, Lap, FastestLapEntry, SessionSummary
│   ├── repositories.py     # ABCs: Meeting/Session/Driver/LapRepository
│   └── services.py         # F1DashboardService
├── ingestion/
│   ├── http_client.py      # HttpClient (timeout, retry, backoff, 404 = vazio)
│   └── openf1_client.py    # repositórios concretos + parse_items resiliente
├── processing/
│   └── lap_processor.py    # funções puras: filtro, ranking, formatação
└── utils/
    ├── config.py           # Settings a partir do .env
    └── logger.py           # get_logger
```

### Regras de negócio (processing)
1. Volta válida = `lap_duration` não nulo e > 0, e `is_pit_out_lap` falso.
2. Ranking ordenado por tempo; desempate pela volta mais cedo e depois pelo número do carro.
3. Tamanho do ranking configurável (`n ≥ 1`, slider de 3 a 20 na tela).
4. Opção "uma volta por piloto" (melhor volta de cada um) ou ranking absoluto.
5. Gap = tempo da volta − tempo da mais rápida.
6. Tempo formatado como `m:ss.mmm`.

### Resiliência (ingestion)
- Retry com backoff exponencial (0,5s, 1s, 2s...) em timeout, erro de rede, 429 e 5xx.
- 404 da OpenF1 vira lista vazia.
- Itens que não passam na validação do Pydantic são logados e ignorados.
- Pilotos duplicados no `/drivers` são removidos.

### Tela (dashboard)
- Sidebar: Temporada, Grande Prêmio, Sessão (Corrida pré-selecionada), Tamanho do ranking, Uma volta por piloto.
- Cards: volta mais rápida, piloto, média do top N, voltas válidas/total.
- Gráfico de barras horizontais com a cor de cada equipe.
- Tabela com posição, piloto, equipe, volta, tempo, gap, setores e speed trap.
- Botão para baixar o ranking em CSV.
- Mensagem amigável se a API falhar.
- Cache: `st.cache_resource` (serviço) e `st.cache_data` com TTL de 1h (consultas).

## 4. Configuração (`.env.example`)

```
OPENF1_BASE_URL=https://api.openf1.org/v1
OPENF1_TIMEOUT=10
OPENF1_MAX_RETRIES=3
DEFAULT_YEAR=2024
TOP_N_LAPS=5
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 5. Testes

| Arquivo | O que cobre |
|---|---|
| `test_lap_processor.py` | filtro, ranking, desempate, uma volta por piloto, formatação, CSV |
| `test_models.py` | parsing dos payloads, campos extras, cor da equipe |
| `test_http_client.py` | sucesso, 404, retry em 5xx/429/timeout, erro 4xx, JSON inválido |
| `test_openf1_client.py` | parâmetros enviados, itens inválidos, duplicados |
| `test_services.py` | orquestração com repositórios mockados |
| `test_config.py` | leitura do `.env` e valores inválidos |
| `test_dashboard.py` | tela inteira com `streamlit.testing.AppTest` e API simulada |
| `integration/test_openf1_live.py` | ponta a ponta na API real (GP do Bahrein 2024) |

## 6. CI (GitHub Actions)

Em todo push e PR:
1. **lint**: `ruff check .` e `ruff format . --check`
2. **test**: `pytest tests/unit/` com cobertura ≥ 50%
3. **docs** (só na `main`, depois de lint e test): `mkdocs gh-deploy --force`

## 7. Ordem de execução

1. Bootstrap: `pyproject.toml`, `.gitignore`, `.env.example`, `.pre-commit-config.yaml`
2. `utils` (logger, config)
3. `domain` (models → repositories → services)
4. `processing` + testes
5. `ingestion` + testes com `MockTransport`
6. Testes do serviço
7. `dashboard.py` + teste com AppTest
8. Documentação MkDocs
9. Workflow de CI
10. README (ASCII)
