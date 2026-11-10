# F1 Dashboard

Dashboard interativo de Formula 1 feito com Streamlit que mostra as voltas mais
rapidas por circuito usando os dados historicos gratuitos da API OpenF1
(temporadas de 2023 em diante).

Projeto pratico da trilha "Python, Git e IA" do Instituto NTA, com foco em boas
praticas: arquitetura em camadas, testes automatizados, lint, documentacao e CI.

## Funcionalidades

- Selecao de temporada, Grande Premio e sessao (a corrida vem selecionada)
- Ranking das N voltas mais rapidas (de 3 a 20) com as cores das equipes
- Modo "uma volta por piloto" ou ranking absoluto
- Gap para o primeiro, tempos de setor e speed trap
- Download do ranking em CSV
- Retry automatico quando a API falha e mensagem amigavel para o usuario

## Tecnologias

- Python 3.12+
- Poetry (dependencias e ambiente)
- Streamlit + Plotly (interface)
- httpx (HTTP com retry e backoff)
- Pydantic v2 (modelos)
- Pytest + pytest-cov (testes, cobertura minima de 50%)
- Ruff + pre-commit (lint e formatacao)
- MkDocs Material (documentacao)
- GitHub Actions (CI e deploy das docs no GitHub Pages)

## Estrutura

```
src/f1/
  dashboard.py        # tela Streamlit (entry point)
  domain/             # modelos, interfaces e servico
  ingestion/          # cliente HTTP e repositorios da OpenF1
  processing/         # regras de ranking (funcoes puras)
  utils/              # logger e configuracao
tests/
  unit/               # rodam sem internet
  integration/        # batem na API real
docs/                 # documentacao MkDocs
.claude/              # doc_api.md, SKILL.md e plan.md usados com a IA
```

## Como rodar

```bash
poetry install --with dev,docs
poetry run task app
```

Abra http://localhost:8501

## Testes e qualidade

```bash
poetry run task test               # testes unitarios + cobertura
poetry run task test-integration   # testes contra a API real
poetry run task lint               # ruff check
poetry run task format             # ruff format
poetry run pre-commit install      # hooks a cada commit
```

## Documentacao

```bash
poetry run task docs        # http://127.0.0.1:8000
poetry run task docs-build  # gera o site em site/
```

A cada push na branch main o CI publica a documentacao no GitHub Pages.

## Fonte dos dados

[OpenF1](https://openf1.org) - API aberta e nao oficial de dados de Formula 1.
