"""Dashboard Streamlit (composition root).

Aqui so ligamos as pecas e desenhamos a tela; regra de negocio fica no
``domain`` e no ``processing``.

Rodar com:  poetry run streamlit run src/f1/dashboard.py
"""

from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from f1.domain.models import FastestLapEntry, Meeting, Session, SessionSummary
from f1.domain.services import F1DashboardService
from f1.ingestion.http_client import HttpClient, HttpClientError
from f1.ingestion.openf1_client import (
    OpenF1DriverRepository,
    OpenF1LapRepository,
    OpenF1MeetingRepository,
    OpenF1SessionRepository,
)
from f1.processing.lap_processor import (
    format_gap,
    format_lap_time,
    rows_to_csv,
    to_table_rows,
)
from f1.utils.config import load_settings

FIRST_SEASON = 2023  # dados historicos gratuitos da OpenF1 comecam em 2023
SESSION_NAMES_PT = {
    "Practice 1": "Treino Livre 1",
    "Practice 2": "Treino Livre 2",
    "Practice 3": "Treino Livre 3",
    "Qualifying": "Classificacao",
    "Sprint Qualifying": "Classificacao Sprint",
    "Sprint Shootout": "Classificacao Sprint",
    "Sprint": "Sprint",
    "Race": "Corrida",
}

settings = load_settings()


# ------------------------------------------------------------------ dependencias
@st.cache_resource
def get_service() -> F1DashboardService:
    http = HttpClient(
        base_url=settings.base_url,
        timeout=settings.timeout_seconds,
        max_retries=settings.max_retries,
    )
    return F1DashboardService(
        meetings=OpenF1MeetingRepository(http),
        sessions=OpenF1SessionRepository(http),
        drivers=OpenF1DriverRepository(http),
        laps=OpenF1LapRepository(http),
    )


@st.cache_data(ttl=3600, show_spinner="Buscando os GPs da temporada...")
def load_meetings(year: int) -> list[Meeting]:
    return get_service().list_meetings(year)


@st.cache_data(ttl=3600, show_spinner="Buscando as sessoes...")
def load_sessions(meeting_key: int) -> list[Session]:
    return get_service().list_sessions(meeting_key)


@st.cache_data(ttl=3600, show_spinner="Buscando as voltas da sessao...")
def load_summary(session_key: int, n: int, one_per_driver: bool) -> SessionSummary:
    return get_service().get_session_summary(session_key, n, one_per_driver)


# ------------------------------------------------------------------ helpers de tela
def session_label(session: Session) -> str:
    return SESSION_NAMES_PT.get(session.session_name, session.session_name)


def default_session_index(sessions: list[Session]) -> int:
    for index, session in enumerate(sessions):
        if session.session_name == "Race":
            return index
    return len(sessions) - 1


def build_chart(entries: list[FastestLapEntry]) -> go.Figure:
    labels = [
        f"{e.position}. {e.name_acronym or e.driver_name} (volta {e.lap_number})"
        for e in entries
    ]
    times = [e.lap_duration for e in entries]
    figure = go.Figure(
        go.Bar(
            x=times,
            y=labels,
            orientation="h",
            marker_color=[e.team_colour for e in entries],
            text=[format_lap_time(t) for t in times],
            textposition="outside",
            customdata=[
                [e.team_name or "-", format_gap(e.gap_to_first)] for e in entries
            ],
            hovertemplate="%{y}<br>Tempo: %{text}<br>Equipe: %{customdata[0]}"
            "<br>Gap: %{customdata[1]}<extra></extra>",
        )
    )
    padding = max(0.3, (max(times) - min(times)) * 0.25)
    figure.update_layout(
        height=max(280, 42 * len(entries) + 80),
        margin={"l": 10, "r": 30, "t": 10, "b": 10},
        xaxis={
            "title": "Tempo de volta (s)",
            "range": [min(times) - padding, max(times) + padding],
        },
        yaxis={"autorange": "reversed"},
        showlegend=False,
    )
    return figure


def stop_with_api_error(error: HttpClientError) -> None:
    st.error(
        "Nao consegui falar com a API do OpenF1 agora. "
        "Confira sua internet e tente de novo em alguns minutos."
    )
    st.caption(f"Detalhe tecnico: {error}")
    st.stop()


# ------------------------------------------------------------------ pagina
def main() -> None:
    st.set_page_config(
        page_title="F1 Dashboard", page_icon=":racing_car:", layout="wide"
    )
    st.title(":racing_car: F1 Dashboard")
    st.caption("Voltas mais rapidas por circuito com dados da API OpenF1")

    current_year = datetime.now().year
    years = list(range(current_year, FIRST_SEASON - 1, -1))

    with st.sidebar:
        st.header("Filtros")
        default_year = (
            settings.default_year if settings.default_year in years else years[-1]
        )
        year = st.selectbox("Temporada", years, index=years.index(default_year))

        try:
            meetings = load_meetings(year)
        except HttpClientError as error:
            stop_with_api_error(error)
            return
        if not meetings:
            st.warning(f"Nenhum GP encontrado para {year}.")
            st.stop()

        meeting = st.selectbox(
            "Grande Premio",
            meetings,
            index=len(meetings) - 1,
            format_func=lambda m: m.label,
        )

        try:
            sessions = load_sessions(meeting.meeting_key)
        except HttpClientError as error:
            stop_with_api_error(error)
            return
        if not sessions:
            st.warning("Esse GP ainda nao tem sessoes disponiveis.")
            st.stop()

        session = st.selectbox(
            "Sessao",
            sessions,
            index=default_session_index(sessions),
            format_func=session_label,
        )
        top_n = st.slider(
            "Tamanho do ranking", 3, 20, min(max(settings.top_n_laps, 3), 20)
        )
        one_per_driver = st.toggle(
            "Uma volta por piloto",
            value=False,
            help="Ligado: mostra a melhor volta de cada piloto. "
            "Desligado: as voltas mais rapidas da sessao, mesmo que repitam piloto.",
        )

    try:
        summary = load_summary(session.session_key, top_n, one_per_driver)
    except HttpClientError as error:
        stop_with_api_error(error)
        return

    when = meeting.date_start.strftime("%d/%m/%Y") if meeting.date_start else ""
    st.subheader(f"{meeting.meeting_name} - {session_label(session)}")
    st.caption(
        " | ".join(
            p for p in [meeting.circuit_short_name, meeting.country_name, when] if p
        )
    )

    fastest = summary.fastest
    if fastest is None:
        st.info("Ainda nao ha voltas cronometradas para essa sessao.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Volta mais rapida", format_lap_time(fastest.lap_duration))
    col2.metric(
        "Piloto", fastest.name_acronym or fastest.driver_name, fastest.team_name
    )
    col3.metric(
        f"Media do top {len(summary.top_laps)}",
        format_lap_time(summary.average_top_lap),
    )
    col4.metric("Voltas validas", f"{summary.valid_laps}/{summary.total_laps}")

    st.plotly_chart(build_chart(summary.top_laps), width="stretch")

    rows = to_table_rows(summary.top_laps)
    st.dataframe(rows, hide_index=True, width="stretch")

    st.download_button(
        "Baixar ranking (CSV)",
        data=rows_to_csv(rows),
        file_name=f"top_voltas_{session.session_key}.csv",
        mime="text/csv",
    )
    st.caption(
        "Voltas de saida de box e voltas sem tempo sao descartadas. "
        "Fonte: [OpenF1](https://openf1.org)."
    )


main()
