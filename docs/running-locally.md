# Rodando localmente

## Pré-requisitos

- **Python 3.12 ou mais novo** ([python.org](https://www.python.org/downloads/))
- **Poetry 2.x**
- **Git**

Instalando o Poetry:

=== "Windows (PowerShell)"

    ```powershell
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
    ```

=== "Linux / macOS"

    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

Confira com `poetry --version`.

## Passo a passo

```bash
# 1. instalar as dependências (cria o .venv dentro do projeto)
poetry config virtualenvs.in-project true
poetry install --with dev,docs

# 2. (opcional) criar seu .env a partir do exemplo
cp .env.example .env          # no Windows: copy .env.example .env

# 3. abrir o dashboard
poetry run task app
```

O navegador abre em <http://localhost:8501>. Se não abrir, acesse o endereço manualmente.

!!! tip "VS Code"
    Para o VS Code usar o mesmo ambiente: `Ctrl+Shift+P` → **Python: Select Interpreter** → escolha o `.venv` da pasta do projeto.

    A pasta `.vscode/` já traz extensões recomendadas, Ruff formatando ao salvar, testes na aba Testing e a configuração **Dashboard F1 (Streamlit)** para depurar com F5.

## Atalhos disponíveis

| Comando | O que faz |
|---|---|
| `poetry run task app` | abre o dashboard |
| `poetry run task test` | testes unitários com cobertura |
| `poetry run task test-integration` | testes contra a API real |
| `poetry run task lint` | `ruff check .` |
| `poetry run task format` | `ruff format .` |
| `poetry run task docs` | documentação em <http://127.0.0.1:8000> |
| `poetry run task docs-build` | gera o site estático em `site/` |

## Problemas comuns

**"Nao consegui falar com a API do OpenF1"**
: Verifique a internet. A OpenF1 tem limite de requisições por minuto; espere um pouco e recarregue.

**`ModuleNotFoundError: No module named 'f1'`**
: Rode `poetry install` de novo na pasta do projeto e use sempre `poetry run ...`.

**A temporada atual aparece vazia**
: Os dados entram na OpenF1 conforme as corridas acontecem. Escolha uma temporada anterior.
