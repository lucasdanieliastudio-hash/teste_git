# Estrutura do projeto

```
f1-dashboard/
├── .claude/
│   ├── doc_api.md            # resumo da API OpenF1 usado como contexto para a IA
│   ├── SKILL.md              # padrões de engenharia que a IA deve seguir
│   └── plan.md               # plano de implementação do projeto
├── .github/workflows/
│   └── ci.yml                # lint, testes e deploy das docs
├── .vscode/                  # extensões, Ruff ao salvar, testes e debug no VS Code
├── docs/                     # esta documentação (MkDocs)
├── src/f1/
│   ├── dashboard.py          # tela Streamlit (entry point)
│   ├── domain/
│   │   ├── models.py         # entidades Pydantic
│   │   ├── repositories.py   # interfaces de acesso a dados
│   │   └── services.py       # F1DashboardService
│   ├── ingestion/
│   │   ├── http_client.py    # cliente HTTP com retry/backoff
│   │   └── openf1_client.py  # repositórios da OpenF1
│   ├── processing/
│   │   └── lap_processor.py  # regras de ranking (funções puras)
│   └── utils/
│       ├── config.py         # leitura do .env
│       └── logger.py         # get_logger
├── tests/
│   ├── conftest.py           # payloads de exemplo da OpenF1
│   ├── unit/                 # rodam sem internet
│   └── integration/          # batem na API real
├── .env.example              # variáveis de ambiente de exemplo
├── .pre-commit-config.yaml   # hooks rodados a cada commit
├── CLAUDE.md                 # guia para o Claude Code
├── mkdocs.yml                # configuração da documentação
├── poetry.lock               # versões travadas das dependências
├── pyproject.toml            # dependências e configs de Ruff/Pytest/Taskipy
└── README.md                 # visão geral (somente ASCII)
```

## Variáveis de ambiente

| Variável | Padrão | Para quê |
|---|---|---|
| `OPENF1_BASE_URL` | `https://api.openf1.org/v1` | URL da API |
| `OPENF1_TIMEOUT` | `10` | timeout de cada requisição (s) |
| `OPENF1_MAX_RETRIES` | `3` | tentativas em falhas temporárias |
| `DEFAULT_YEAR` | `2024` | temporada que abre selecionada |
| `TOP_N_LAPS` | `5` | tamanho inicial do ranking |
| `ENVIRONMENT` | `development` | ambiente atual |
| `LOG_LEVEL` | `INFO` | nível de log |
