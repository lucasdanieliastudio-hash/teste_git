# SKILL.md — Padrões de Engenharia para Projetos Python

> Guia que a IA (e qualquer pessoa do time) deve seguir ao criar ou alterar código neste repositório.
> Se algo aqui conflitar com um pedido, pergunte antes de desviar.

---

## 1. Estrutura de diretórios (obrigatória)

```
projeto/
├── pyproject.toml            # dependências e configs (Poetry, Ruff, Pytest)
├── poetry.lock               # gerado pelo Poetry, nunca editar à mão
├── .env.example              # variáveis de ambiente de exemplo (sem segredos)
├── .gitignore
├── .pre-commit-config.yaml
├── README.md                 # somente ASCII
├── mkdocs.yml
├── src/<pacote>/
│   ├── domain/               # modelos, interfaces (repositórios) e serviços
│   ├── ingestion/            # acesso a APIs/arquivos/bancos
│   ├── processing/           # funções puras de transformação
│   └── utils/                # logger, config
├── tests/
│   ├── conftest.py           # fixtures compartilhadas
│   ├── unit/                 # rápidos, sem rede
│   └── integration/          # tocam serviços reais (@pytest.mark.integration)
└── docs/                     # páginas do MkDocs
```

## 2. Ambiente com Poetry

- Poetry é obrigatório. **Não usar `pip install` dentro do projeto.**
- Dependências de produção: `poetry add <pacote>`
- Dependências de dev: `poetry add --group dev <pacote>`
- Dependências de documentação: `poetry add --group docs <pacote>`
- Tudo roda com `poetry run ...` (ou pelos atalhos `poetry run task <nome>`).
- Versão do projeto segue SemVer (`MAJOR.MINOR.PATCH`).

## 3. Arquitetura em camadas

Regra de dependência: **UI → domain ← ingestion / processing**.

| Camada | Pode importar | Não pode |
|---|---|---|
| `domain` | `processing`, `utils`, bibliotecas puras (pydantic) | `ingestion`, `httpx`, `streamlit` |
| `processing` | `domain.models` | qualquer I/O (rede, disco, print) |
| `ingestion` | `domain`, `utils`, `httpx` | `streamlit` |
| UI (`dashboard.py`) | tudo | regra de negócio própria |

Outras regras:
- Serviços recebem dependências pelo construtor (injeção de dependência).
- Repositórios são `ABC`s no domínio; implementações concretas ficam em `ingestion`.
- Funções curtas, com um propósito só. Se passou de ~30 linhas, considere quebrar.
- Proibido: variáveis globais mutáveis, `print` para log, segredos no código, `except:` vazio.

## 4. Qualidade de código

- PEP 8, verificado pelo **Ruff** (lint + formatação + ordem de imports).
- Config: `line-length = 88`, regras `E, W, F, I, B, C4, UP, N`.
- Critério de aceite: `ruff check .` e `ruff format . --check` sem erros.

## 5. Testes

- Framework: **pytest** + `pytest-cov` + `pytest-mock`.
- **Cobertura mínima: 50%** (o CI falha abaixo disso).
- Unitários não fazem chamada de rede: use `httpx.MockTransport`, `MagicMock` ou `monkeypatch`.
- Funções de `processing` são testadas sem nenhum mock.
- Integração fica em `tests/integration/`, marcada com `@pytest.mark.integration`, e não roda por padrão.
- Nome dos testes descreve o comportamento: `test_<o_que>_<quando>_<resultado>`.

## 6. Documentação

- **MkDocs Material**, configurado em `mkdocs.yml`.
- Páginas mínimas: `index`, `architecture`, `project-structure`, `running-locally`, `running-tests`, `contributing`.
- Docstrings em funções públicas.
- O CI publica a documentação no GitHub Pages a cada push na `main`.

## 7. Boas práticas adicionais

- Type hints em todas as funções públicas.
- Logging com `get_logger(__name__)`; nada de `print`.
- Configuração via variáveis de ambiente (`.env` local, `.env.example` versionado).
- **Nunca** commitar `.env`, tokens ou senhas.
- Pre-commit instalado (`poetry run pre-commit install`) com Ruff e checagens de YAML/TOML.

## 8. Fluxo Git e Pull Requests

- Branches: `main` (estável, publicada) e `dev` (integração). Features em `feature/<nome>`.
- Commits pequenos e descritivos, no imperativo: "Adiciona filtro de ranking".
- Todo merge na `main` passa por PR com CI verde.
- Descrição do PR:

```markdown
## O que foi feito
## Por que foi feito
## Como testar
## Checklist
- [ ] ruff check e ruff format sem erros
- [ ] testes passando com cobertura >= 50%
- [ ] documentação atualizada
```

## 9. Nomenclatura

| Elemento | Padrão | Exemplo |
|---|---|---|
| módulos e funções | `snake_case` | `lap_processor.py`, `compute_top_n_laps` |
| classes | `PascalCase` | `F1DashboardService` |
| constantes | `UPPER_SNAKE_CASE` | `DEFAULT_BASE_URL` |
| privados | prefixo `_` | `_lap_sort_key` |

Imports sempre absolutos (`from f1.domain.models import Lap`), agrupados em: padrão → terceiros → projeto.
