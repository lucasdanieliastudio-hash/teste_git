# OpenF1 API — Resumo para o projeto

> Fonte oficial: https://openf1.org/docs
> URL base: `https://api.openf1.org/v1/`

## Visão geral

- API aberta e não-oficial com dados de cronometragem e telemetria da Fórmula 1.
- **Dados históricos (2023 em diante): gratuitos e sem autenticação.** É o que este projeto usa.
- Dados em tempo real exigem assinatura paga (fora do escopo).
- Respostas em **JSON** (ou CSV com `csv=true`).
- Quando um filtro não encontra nada, a API responde **HTTP 404** com `{"detail": "No results found."}`. O cliente deve tratar isso como lista vazia.
- Existe limite de requisições por minuto. Em caso de **HTTP 429**, esperar e tentar de novo (backoff).

## Filtros

Todo endpoint aceita filtros na query string:

| Operador | Exemplo |
|---|---|
| igual | `driver_number=44` |
| maior / menor ou igual | `lap_duration<=90`, `speed>=300` |
| maior / menor | `rpm>12000`, `throttle<50` |

Atalhos úteis: `session_key=latest` e `meeting_key=latest` trazem a sessão/etapa mais recente.

## Hierarquia dos dados

```
year (temporada)
 └── meeting  (fim de semana de GP)          meeting_key
      └── session (TL1, TL2, TL3, Quali, Sprint, Race)   session_key
           ├── drivers (pilotos da sessão)
           └── laps    (voltas de cada piloto)
```

## Endpoints usados no dashboard

### `GET /meetings`
Fins de semana de corrida de uma temporada.

| Campo | Tipo | Descrição |
|---|---|---|
| `meeting_key` | int | ID único da etapa |
| `meeting_name` | str | Nome do GP (ex.: "Bahrain Grand Prix") |
| `year` | int | Temporada |
| `country_name` | str | País |
| `circuit_short_name` | str | Nome curto do circuito (ex.: "Sakhir") |
| `location` | str | Cidade |
| `date_start` | datetime ISO 8601 | Início do fim de semana |

Exemplo: `GET /v1/meetings?year=2024`

### `GET /sessions`
Sessões de um meeting.

| Campo | Tipo | Descrição |
|---|---|---|
| `session_key` | int | ID único da sessão |
| `session_name` | str | "Practice 1", "Qualifying", "Sprint", "Race"... |
| `session_type` | str | "Practice", "Qualifying", "Race" |
| `meeting_key` | int | Etapa a que pertence |
| `date_start` / `date_end` | datetime | Período da sessão |

Exemplo: `GET /v1/sessions?meeting_key=1229`

### `GET /drivers`
Pilotos de uma sessão. Pode vir o mesmo piloto mais de uma vez (deduplicar por `driver_number`).

| Campo | Tipo | Descrição |
|---|---|---|
| `driver_number` | int | Número do carro |
| `full_name` | str | Nome completo |
| `name_acronym` | str | Sigla de 3 letras (VER, HAM...) |
| `team_name` | str | Equipe |
| `team_colour` | str | Cor da equipe em hex **sem `#`** (ex.: `3671C6`) |
| `headshot_url` | str | Foto do piloto |

Exemplo: `GET /v1/drivers?session_key=9472`

### `GET /laps`
Volta a volta de cada piloto.

| Campo | Tipo | Descrição |
|---|---|---|
| `driver_number` | int | Número do carro |
| `lap_number` | int | Número da volta |
| `lap_duration` | float \| null | Tempo da volta em segundos (null na 1ª volta e em voltas incompletas) |
| `duration_sector_1/2/3` | float \| null | Tempo de cada setor |
| `i1_speed` / `i2_speed` | int \| null | Velocidade nos pontos intermediários (km/h) |
| `st_speed` | int \| null | Velocidade no speed trap (km/h) |
| `is_pit_out_lap` | bool \| null | Volta de saída dos boxes (não conta para ranking) |

Exemplo: `GET /v1/laps?session_key=9472&driver_number=1`

## Outros endpoints (evolução futura)

`car_data`, `position`, `intervals`, `pit`, `stints`, `weather`, `race_control`, `team_radio`, `session_result`, `starting_grid`, `championship_drivers`, `championship_teams`.
