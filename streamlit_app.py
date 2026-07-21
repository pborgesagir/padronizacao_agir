import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title='Dashboard - Padronização AGIR',
    layout='wide',
    page_icon="https://media.licdn.com/dms/image/C4D0BAQHXylmAyGyD3A/company-logo_200_200/0/1630570245289?e=2147483647&v=beta&t=Dxas2us5gteu0P_9mdkQBwJEyg2aoc215Vrk2phu7Bs",
    initial_sidebar_state='auto'
)

url = "https://docs.google.com/spreadsheets/d/1CGypJWn35SFD6oYeLmFU1HjMhxJRBpuuVuVeP7y86wo/edit#gid=0"

# --------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------

def safe_sorted_unique(series: pd.Series, placeholder: str = "Não informado") -> list:
    """Return a sorted list of unique values from a column that may contain
    mixed types (str / float / NaN), which is common with Google Sheets data
    and is exactly what caused the original TypeError.
    """
    if series is None:
        return []
    cleaned = series.fillna(placeholder).astype(str).str.strip()
    cleaned = cleaned[cleaned != ""]
    return sorted(cleaned.unique(), key=str)


def normalize_text_column(series: pd.Series, placeholder: str = "Não informado", title_case: bool = True) -> pd.Series:
    """Force a column to a clean, consistent string dtype so it never mixes
    float/str again after filtering."""
    s = series.fillna(placeholder).astype(str).str.strip()
    if title_case:
        s = s.str.title()
    return s


def safe_chart(container, render_fn, empty_message="Sem dados para este gráfico com os filtros atuais."):
    """Runs a chart-rendering function but never lets it crash the whole app."""
    try:
        render_fn(container)
    except Exception as e:
        container.warning(f"{empty_message}\n\nDetalhe técnico: {e}")


REQUIRED_COLUMNS = [
    "DATA DE ATRIBUIÇÃO:", "DATA DE CONCLUSÃO:", "ANDAMENTO:", "ANALISTA:",
    "LEAD TIME DO PROCESSO:", "UNIDADE:", "CLASSIFICAÇÃO DO PROCESSO:",
    "NÚMERO DO PROCESSO:", "INCONFORMIDADE 1:",
]

# --------------------------------------------------------------------------
# 1) LOAD DATA (cached, with manual refresh)
# --------------------------------------------------------------------------

st.title("DASHBOARD - PADRONIZAÇÃO AGIR")

conn = st.connection("gsheets", type=GSheetsConnection)

col_refresh, _ = st.columns([1, 5])
if col_refresh.button("🔄 Atualizar dados da planilha"):
    st.cache_data.clear()


@st.cache_data(ttl=300, show_spinner="Carregando dados da planilha...")
def load_data(sheet_url: str) -> pd.DataFrame:
    data = conn.read(spreadsheet=sheet_url, usecols=list(range(22)))
    return data


try:
    df = load_data(url)
except Exception as e:
    st.error(f"Não foi possível carregar a planilha. Verifique a conexão/URL. Detalhe: {e}")
    st.stop()

missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing_cols:
    st.error(
        "As seguintes colunas esperadas não foram encontradas na planilha: "
        f"{missing_cols}. Verifique se os cabeçalhos da planilha não mudaram."
    )
    st.stop()

# --------------------------------------------------------------------------
# 2) CLEAN / PREPARE THE DATA
# --------------------------------------------------------------------------

# Normalize every text column ONCE, right after load, so nothing downstream
# (filters, groupby, sorted()) ever sees a mixed str/float column again.
df["ANALISTA:"] = normalize_text_column(df["ANALISTA:"])
df["UNIDADE:"] = normalize_text_column(df["UNIDADE:"], title_case=False)
df["CLASSIFICAÇÃO DO PROCESSO:"] = normalize_text_column(df["CLASSIFICAÇÃO DO PROCESSO:"], title_case=False)
df["NÚMERO DO PROCESSO:"] = normalize_text_column(df["NÚMERO DO PROCESSO:"], title_case=False)
# "-" is used as a sentinel meaning "no inconformidade" further down, so keep it as-is
df["INCONFORMIDADE 1:"] = df["INCONFORMIDADE 1:"].fillna("-").astype(str).str.strip()
df["ANDAMENTO:"] = normalize_text_column(df["ANDAMENTO:"], title_case=False)

# Lead time must be numeric, not text
df["LEAD TIME DO PROCESSO:"] = pd.to_numeric(df["LEAD TIME DO PROCESSO:"], errors="coerce")

# Dates
df = df.sort_values("DATA DE ATRIBUIÇÃO:")
df["DATA DE ATRIBUIÇÃO:"] = pd.to_datetime(df["DATA DE ATRIBUIÇÃO:"], format='%d/%m/%Y', errors='coerce')
df = df.dropna(subset=["DATA DE ATRIBUIÇÃO:"])

df["Year"] = df["DATA DE ATRIBUIÇÃO:"].dt.year
df["Month"] = df["DATA DE ATRIBUIÇÃO:"].dt.month
df["Quarter"] = df["DATA DE ATRIBUIÇÃO:"].dt.quarter
df["Semester"] = np.where(df["DATA DE ATRIBUIÇÃO:"].dt.month.isin([1, 2, 3, 4, 5, 6]), 1, 2)

df["Year-Quarter"] = df["Year"].astype(str) + "-T" + df["Quarter"].astype(str)
df["Year-Month"] = df["DATA DE ATRIBUIÇÃO:"].dt.strftime("%Y-%m")
df["Year-Semester"] = df["Year"].astype(str) + "-S" + df["Semester"].astype(str)

df = df.sort_values("DATA DE CONCLUSÃO:")
df["DATA DE CONCLUSÃO:"] = pd.to_datetime(df["DATA DE CONCLUSÃO:"], format='%d/%m/%Y', errors='coerce')
# NOTE: rows without a conclusion date are still "in progress" -- we no longer
# drop them from the whole dataframe (the original code dropped EVERY row
# lacking a conclusion date, which silently hid open/pending processes from
# every chart, including ones that only need the assignment date).
df["Year conclusion"] = df["DATA DE CONCLUSÃO:"].dt.year
df["Month conclusion"] = df["DATA DE CONCLUSÃO:"].dt.month
df["Quarter conclusion"] = df["DATA DE CONCLUSÃO:"].dt.quarter
df["Semester conclusion"] = np.where(df["DATA DE CONCLUSÃO:"].dt.month.isin([1, 2, 3, 4, 5, 6]), 1, 2)
df["Year-Quarter conclusion"] = df["Year conclusion"].astype("Int64").astype(str) + "-T" + df["Quarter conclusion"].astype("Int64").astype(str)
df["Year-Month conclusion"] = df["DATA DE CONCLUSÃO:"].dt.strftime("%Y-%m")
df["Year-Semester conclusion"] = df["Year"].astype(str) + "-S" + df["Semester conclusion"].astype("Int64").astype(str)

if df.empty:
    st.warning("Nenhum registro com datas válidas foi encontrado na planilha.")
    st.stop()

# --------------------------------------------------------------------------
# 3) SIDEBAR FILTERS (MULTI-SELECTION) -- all built with safe_sorted_unique
# --------------------------------------------------------------------------

st.sidebar.header("Filtros")

unique_year_month = safe_sorted_unique(df["Year-Month"])
unique_year_quarter = safe_sorted_unique(df["Year-Quarter"])
unique_year_semester = safe_sorted_unique(df["Year-Semester"])
unique_year = safe_sorted_unique(df["Year"])

month_selection = st.sidebar.multiselect("Mês (Year-Month)", unique_year_month, default=[])
quarter_selection = st.sidebar.multiselect("Trimestre (Year-Quarter)", unique_year_quarter, default=[])
semester_selection = st.sidebar.multiselect("Semestre (Year-Semester)", unique_year_semester, default=[])
year_selection = st.sidebar.multiselect("Ano (Year)", unique_year, default=[])

unique_classificacao = safe_sorted_unique(df["CLASSIFICAÇÃO DO PROCESSO:"])
classificacao_selection = st.sidebar.multiselect("Classificação do Processo:", unique_classificacao, default=[])

unique_numero_processo = safe_sorted_unique(df["NÚMERO DO PROCESSO:"])
numero_processo_selection = st.sidebar.multiselect("Número do Processo:", unique_numero_processo, default=[])

desired_unidades = ["CRER", "HECAD", "HUGOL", "HDS", "AGIR", "TEIA", "CED"]
available_unidades = [u for u in desired_unidades if u in df["UNIDADE:"].unique()]
unidade_selection = st.sidebar.multiselect("Unidade:", available_unidades, default=[])

unique_analista = safe_sorted_unique(df["ANALISTA:"])
analista_selection = st.sidebar.multiselect("Analista:", unique_analista, default=[])

# --------------------------------------------------------------------------
# 4) APPLY FILTERS
# --------------------------------------------------------------------------

filtered_df = df.copy()

if month_selection:
    filtered_df = filtered_df[filtered_df["Year-Month"].isin(month_selection)]
if quarter_selection:
    filtered_df = filtered_df[filtered_df["Year-Quarter"].isin(quarter_selection)]
if semester_selection:
    filtered_df = filtered_df[filtered_df["Year-Semester"].isin(semester_selection)]
if year_selection:
    filtered_df = filtered_df[filtered_df["Year"].astype(str).isin([str(y) for y in year_selection])]
if unidade_selection:
    filtered_df = filtered_df[filtered_df["UNIDADE:"].isin(unidade_selection)]
if classificacao_selection:
    filtered_df = filtered_df[filtered_df["CLASSIFICAÇÃO DO PROCESSO:"].isin(classificacao_selection)]
if numero_processo_selection:
    filtered_df = filtered_df[filtered_df["NÚMERO DO PROCESSO:"].isin(numero_processo_selection)]
if analista_selection:
    filtered_df = filtered_df[filtered_df["ANALISTA:"].isin(analista_selection)]

if filtered_df.empty:
    st.warning("Nenhum processo corresponde aos filtros selecionados. Ajuste os filtros na barra lateral.")
    st.stop()

# --------------------------------------------------------------------------
# 5) METRICS
# --------------------------------------------------------------------------

quantity_atribuido = len(filtered_df)
quantity_finalizado = int(filtered_df["ANDAMENTO:"].eq("Finalizado").sum())
quantity_residual = quantity_atribuido - quantity_finalizado
pct_finalizado = (quantity_finalizado / quantity_atribuido * 100) if quantity_atribuido else 0

st.sidebar.markdown("---")
st.sidebar.metric("ATRIBUÍDO", quantity_atribuido)
st.sidebar.metric("FINALIZADO", quantity_finalizado, delta=f"{pct_finalizado:.1f}%")
st.sidebar.metric("RESIDUAL", quantity_residual)

# --------------------------------------------------------------------------
# 6) LAYOUT (tabs keep things organized and load only what's visible)
# --------------------------------------------------------------------------

tab_overview, tab_analistas, tab_qualidade, tab_dados = st.tabs(
    ["📊 Visão Geral", "👤 Analistas", "⚠️ Qualidade", "🗂️ Dados"]
)

# ---------------------- TAB: VISÃO GERAL -----------------------------------
with tab_overview:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Processos Atribuídos", quantity_atribuido)
    k2.metric("Processos Finalizados", quantity_finalizado)
    k3.metric("Residual", quantity_residual)
    avg_lead_time_value = filtered_df["LEAD TIME DO PROCESSO:"].mean()
    k4.metric("Lead Time Médio (dias)", f"{avg_lead_time_value:.2f}" if pd.notna(avg_lead_time_value) else "—")

    c1, c2 = st.columns(2)

    def render_lead_time_evolution(container):
        avg_lead_time_over_time = (
            filtered_df.dropna(subset=["LEAD TIME DO PROCESSO:"])
            .groupby("Year-Month")["LEAD TIME DO PROCESSO:"].mean()
            .reset_index()
            .sort_values("Year-Month")
        )
        fig = px.line(
            avg_lead_time_over_time, x="Year-Month", y="LEAD TIME DO PROCESSO:",
            title="Lead Time Médio ao Longo do Tempo", markers=True
        )
        container.plotly_chart(fig, use_container_width=True)

    safe_chart(c1, render_lead_time_evolution)

    def render_assertividade(container):
        assertividade_data = (
            filtered_df.groupby("Year-Month")["ANDAMENTO:"]
            .apply(lambda x: (x == "Finalizado").sum() / x.count() * 100 if x.count() > 0 else 0)
            .reset_index()
        )
        assertividade_data.columns = ["Year-Month", "Taxa de assertividade"]
        assertividade_data = assertividade_data.sort_values("Year-Month")
        fig = px.line(assertividade_data, x="Year-Month", y="Taxa de assertividade",
                      title="Taxa de Assertividade dos Processos Recebidos (%)", markers=True)
        fig.add_hline(y=90, line_dash="dash", line_color="green",
                      annotation_text="META 90%", annotation_position="bottom right")
        container.plotly_chart(fig, use_container_width=True)

    safe_chart(c2, render_assertividade)

    def render_treemap(container):
        classification_by_analyst = (
            filtered_df.groupby(["CLASSIFICAÇÃO DO PROCESSO:", "ANALISTA:"])
            .size().reset_index(name="Quantidade")
        )
        fig = px.treemap(
            classification_by_analyst,
            path=["CLASSIFICAÇÃO DO PROCESSO:", "ANALISTA:"],
            values="Quantidade",
            title="Classificação do Processo por Analista",
            color="Quantidade", color_continuous_scale="Blues"
        )
        container.plotly_chart(fig, use_container_width=True)

    safe_chart(st, render_treemap)

# ---------------------- TAB: ANALISTAS --------------------------------------
with tab_analistas:
    c1, c2 = st.columns(2)

    def render_counts(container):
        counts = filtered_df["ANALISTA:"].value_counts().reset_index()
        counts.columns = ["ANALISTA", "Quantidade"]
        fig = px.bar(counts, x="ANALISTA", y="Quantidade",
                     title="Quantidade de Processos Atribuídos a Cada Analista")
        container.plotly_chart(fig, use_container_width=True)

    safe_chart(c1, render_counts)

    def render_avg_lead_time(container):
        avg_lead_time = (
            filtered_df.dropna(subset=["LEAD TIME DO PROCESSO:"])
            .groupby("ANALISTA:")["LEAD TIME DO PROCESSO:"].mean()
            .reset_index()
            .sort_values(by="LEAD TIME DO PROCESSO:", ascending=False)
        )
        fig = px.bar(avg_lead_time, x="ANALISTA:", y="LEAD TIME DO PROCESSO:",
                     title="Lead Time Médio por Analista")
        container.plotly_chart(fig, use_container_width=True)

    safe_chart(c2, render_avg_lead_time)

    def render_donut(container):
        completed_jobs = filtered_df[filtered_df["ANDAMENTO:"].isin(["Finalizado", "Devolvido A Unidade"])]
        analista_counts = completed_jobs["ANALISTA:"].value_counts().reset_index()
        analista_counts.columns = ["ANALISTA:", "Quantidade"]
        fig = px.pie(analista_counts, names="ANALISTA:", values="Quantidade",
                     title="Distribuição da Produtividade da Equipe", hole=0.4)
        container.plotly_chart(fig, use_container_width=True)

    safe_chart(st, render_donut)

# ---------------------- TAB: QUALIDADE --------------------------------------
with tab_qualidade:
    c1, c2 = st.columns(2)

    def render_inconformidade_bar(container):
        inconf_filtered = filtered_df[
            (filtered_df["UNIDADE:"].isin(desired_unidades)) &
            (filtered_df["INCONFORMIDADE 1:"] != "-")
        ]
        if inconf_filtered.empty:
            container.info("Nenhuma inconformidade registrada para os filtros atuais.")
            return
        grouped_data = (
            inconf_filtered.groupby(["UNIDADE:", "INCONFORMIDADE 1:"])
            .size().reset_index(name="Quantidade")
            .sort_values(by="Quantidade", ascending=False)
        )
        fig = px.bar(grouped_data, x="UNIDADE:", y="Quantidade", color="INCONFORMIDADE 1:",
                     title="Quantidade de Inconformidades por Unidade")
        container.plotly_chart(fig, use_container_width=True)

    safe_chart(c1, render_inconformidade_bar)

    def render_inconformidade_lines(container):
        inconformidade_data = filtered_df[filtered_df["INCONFORMIDADE 1:"] != "-"]
        if inconformidade_data.empty:
            container.info("Nenhuma inconformidade registrada para os filtros atuais.")
            return
        inconformidade_grouped = (
            inconformidade_data.groupby(["Year-Month", "INCONFORMIDADE 1:"])
            .size().reset_index(name="Quantidade")
            .sort_values("Year-Month")
        )
        fig = px.line(inconformidade_grouped, x="Year-Month", y="Quantidade", color="INCONFORMIDADE 1:",
                      title="Comportamento das Inconformidades por Mês")
        container.plotly_chart(fig, use_container_width=True)

    safe_chart(c2, render_inconformidade_lines)

# ---------------------- TAB: DADOS ------------------------------------------
with tab_dados:
    st.write(f"### Dados Selecionados ({len(filtered_df)} registros)")
    st.dataframe(filtered_df, use_container_width=True)
    st.download_button(
        "⬇️ Baixar dados filtrados (CSV)",
        data=filtered_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="processos_filtrados.csv",
        mime="text/csv",
    )
