import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title='Dashboard - Padronização AGIR',
    layout='wide',
    page_icon="https://media.licdn.com/dms/image/C4D0BAQHXylmAyGyD3A/company-logo_200_200/0/1630570245289?e=2147483647&v=beta&t=Dxas2us5gteu0P_9mdkQBwJEyg2aoc215Vrk2phu7Bs",
    initial_sidebar_state='auto'
)

url = "https://docs.google.com/spreadsheets/d/1CGypJWn35SFD6oYeLmFU1HjMhxJRBpuuVuVeP7y86wo/edit#gid=0"
st.title("DASHBOARD - PADRONIZAÇÃO AGIR")
conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read(spreadsheet=url, usecols=list(range(22)))
df1 = conn.read(spreadsheet=url, usecols=list(range(22)))

# --------------------------------------------------------------------------
# 1) PREPARE THE DATA
# --------------------------------------------------------------------------
df = df.sort_values("DATA DE ATRIBUIÇÃO:")

# Convert the "DATA DE ATRIBUIÇÃO:" column to datetime with errors='coerce'
df["DATA DE ATRIBUIÇÃO:"] = pd.to_datetime(df["DATA DE ATRIBUIÇÃO:"], format='%d/%m/%Y', errors='coerce')
# Filter out rows where the date could not be parsed (NaT)
df = df.dropna(subset=["DATA DE ATRIBUIÇÃO:"])

# Extract year, month, quarter, semester
df["Year"] = df["DATA DE ATRIBUIÇÃO:"].dt.year
df["Month"] = df["DATA DE ATRIBUIÇÃO:"].dt.month
df["Quarter"] = df["DATA DE ATRIBUIÇÃO:"].dt.quarter
df["Semester"] = np.where(df["DATA DE ATRIBUIÇÃO:"].dt.month.isin([1,2,3,4,5,6]), 1, 2)

df["Year-Quarter"] = df["Year"].astype(str) + "-T" + df["Quarter"].astype(str)
df["Year-Month"] = df["DATA DE ATRIBUIÇÃO:"].dt.strftime("%Y-%m")
df["Year-Semester"] = df["Year"].astype(str) + "-S" + df["Semester"].astype(str)

# ----------------------- COLUMN FOR DATA DE CONCLUSÃO ---------------------
df = df.sort_values("DATA DE CONCLUSÃO:")
df["DATA DE CONCLUSÃO:"] = pd.to_datetime(df["DATA DE CONCLUSÃO:"], format='%d/%m/%Y', errors='coerce')
df = df.dropna(subset=["DATA DE CONCLUSÃO:"])

df["Year conclusion"] = df["DATA DE CONCLUSÃO:"].dt.year
df["Month conclusion"] = df["DATA DE CONCLUSÃO:"].dt.month
df["Quarter conclusion"] = df["DATA DE CONCLUSÃO:"].dt.quarter
df["Semester conclusion"] = np.where(df["DATA DE CONCLUSÃO:"].dt.month.isin([1,2,3,4,5,6]), 1, 2)

df["Year-Quarter conclusion"] = df["Year conclusion"].astype(str) + "-T" + df["Quarter conclusion"].astype(str)
df["Year-Month conclusion"] = df["DATA DE CONCLUSÃO:"].dt.strftime("%Y-%m")
df["Year-Semester conclusion"] = df["Year"].astype(str) + "-S" + df["Semester conclusion"].astype(str)

# --------------------------------------------------------------------------
# 2) SIDEBAR FILTERS (MULTI-SELECTION)
# --------------------------------------------------------------------------

unique_year_month = sorted(df["Year-Month"].dropna().unique())
unique_year_quarter = sorted(df["Year-Quarter"].dropna().unique())
unique_year_semester = sorted(df["Year-Semester"].dropna().unique())
unique_year = sorted(df["Year"].dropna().unique())

# Let’s give the user a multi-select widget for each dimension.
# If the user selects nothing, we'll treat that as "no filter" for that dimension.
month_selection = st.sidebar.multiselect("Mês (Year-Month)", unique_year_month, default=[])
quarter_selection = st.sidebar.multiselect("Trimestre (Year-Quarter)", unique_year_quarter, default=[])
semester_selection = st.sidebar.multiselect("Semestre (Year-Semester)", unique_year_semester, default=[])
year_selection = st.sidebar.multiselect("Ano (Year)", unique_year, default=[])

# --- Classificação filter (multi) ---
unique_classificacao = sorted(df["CLASSIFICAÇÃO DO PROCESSO:"].dropna().unique())
classificacao_selection = st.sidebar.multiselect("Classificação do Processo:", unique_classificacao, default=[])

# --- Número do Processo filter (multi) ---
unique_numero_processo = sorted(df["NÚMERO DO PROCESSO:"].dropna().unique())
numero_processo_selection = st.sidebar.multiselect("Número do Processo:", unique_numero_processo, default=[])

# --- Unidade filter (multi) ---
desired_unidades = ["CRER", "HECAD", "HUGOL", "HDS", "AGIR", "TEIA", "CED"]
unidade_selection = st.sidebar.multiselect("Unidade:", desired_unidades, default=[])

# --------------------------------------------------------------------------
# 3) APPLY FILTERS
# --------------------------------------------------------------------------
filtered_df = df.copy()

# Filter by Year-Month
if month_selection:
    filtered_df = filtered_df[filtered_df["Year-Month"].isin(month_selection)]

# Filter by Year-Quarter
if quarter_selection:
    filtered_df = filtered_df[filtered_df["Year-Quarter"].isin(quarter_selection)]

# Filter by Year-Semester
if semester_selection:
    filtered_df = filtered_df[filtered_df["Year-Semester"].isin(semester_selection)]

# Filter by Year
if year_selection:
    filtered_df = filtered_df[filtered_df["Year"].isin(year_selection)]

# Filter by Unidade
if unidade_selection:
    filtered_df = filtered_df[filtered_df["UNIDADE:"].isin(unidade_selection)]

# Filter by Classificação
if classificacao_selection:
    filtered_df = filtered_df[filtered_df["CLASSIFICAÇÃO DO PROCESSO:"].isin(classificacao_selection)]

# Filter by Número do Processo
if numero_processo_selection:
    filtered_df = filtered_df[filtered_df["NÚMERO DO PROCESSO:"].isin(numero_processo_selection)]

# --------------------------------------------------------------------------
# 4) NEW FILTER FOR "ANALISTA:" (MULTI-SELECTION)
# --------------------------------------------------------------------------
filtered_df["ANALISTA:"] = (
    filtered_df["ANALISTA:"]
    .astype(str)
    .str.strip()
    .str.lower()
    .str.capitalize()
)

unique_analista = sorted(filtered_df["ANALISTA:"].unique())
analista_selection = st.sidebar.multiselect("Analista:", unique_analista, default=[])

if analista_selection:
    filtered_df = filtered_df[filtered_df["ANALISTA:"].isin(analista_selection)]

# --------------------------------------------------------------------------
# LAYOUT COLUMNS
# --------------------------------------------------------------------------
col9, col8 = st.columns(2)
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)
col10 = st.columns(1)[0] 
col5, col7 = st.columns(2)

# --------------------------------------------------------------------------
# CALCULATE METRICS
# --------------------------------------------------------------------------
# 1) ATRIBUÍDO = # of rows in the filtered data
quantity_atribuido = len(filtered_df)

# 2) FINALIZADO = how many of those have ANDAMENTO: == "FINALIZADO"
quantity_finalizado = filtered_df["ANDAMENTO:"].eq("FINALIZADO").sum()

# 3) RESIDUAL = ATRIBUÍDO - FINALIZADO
quantity_residual = quantity_atribuido - quantity_finalizado

# Display them in sidebar
st.sidebar.markdown(f"**RESIDUAL:** {quantity_residual}")
st.sidebar.markdown(f"**ATRIBUÍDO:** {quantity_atribuido}")
st.sidebar.markdown(f"**FINALIZADO:** {quantity_finalizado}")

# --------------------------------------------------------------------------
# BAR CHART: Processes per ANALISTA
# --------------------------------------------------------------------------
counts = filtered_df["ANALISTA:"].value_counts().reset_index()
counts.columns = ["ANALISTA", "Quantidade"]

fig_date = px.bar(counts, x="ANALISTA", y="Quantidade", 
                  title="Quantidade de processos atribuídos a cada analista")
col1.plotly_chart(fig_date)

# --------------------------------------------------------------------------
# BAR CHART: Average LEAD TIME por ANALISTA
# --------------------------------------------------------------------------
avg_lead_time = filtered_df.groupby("ANALISTA:")["LEAD TIME DO PROCESSO:"].mean().reset_index()
avg_lead_time = avg_lead_time.sort_values(by="LEAD TIME DO PROCESSO:", ascending=False)

fig_avg_lead_time = px.bar(avg_lead_time, x="ANALISTA:", y="LEAD TIME DO PROCESSO:",
                           title="Lead Time Médio por Analista")
col2.plotly_chart(fig_avg_lead_time)

# --------------------------------------------------------------------------
# LINE CHART: Taxa de assertividade dos processos recebidos (%)
# --------------------------------------------------------------------------
# For each Year-Month, let's define assertividade as:
# (# FINALIZADO / total do mês) * 100
# If you have no data for that month, you won't see a point.

assertividade_data = (
    filtered_df
    .groupby("Year-Month")["ANDAMENTO:"]
    .apply(lambda x: (x == "FINALIZADO").sum() / x.count() * 100 if x.count() > 0 else 0)
    .reset_index()
)
assertividade_data.columns = ["Year-Month", "Taxa de assertividade"]

fig_assertividade = px.line(assertividade_data, 
                            x="Year-Month", 
                            y="Taxa de assertividade", 
                            title="Taxa de assertividade dos processos recebidos (%)")

fig_assertividade.add_hline(y=90, line_dash="dash", line_color="green", 
                            annotation_text="90%", 
                            annotation_position="bottom right")
fig_assertividade.add_annotation(text="META", xref="paper", yref="y", x=0.99, y=91, showarrow=False)

col4.plotly_chart(fig_assertividade)

# --------------------------------------------------------------------------
# BAR CHART: Quantidade de Inconformidades por Unidade
# --------------------------------------------------------------------------
# Filter out rows where "INCONFORMIDADE 1:" is "-"
desired_unidades_list = ["CRER", "HECAD", "HUGOL", "HDS", "AGIR", "TEIA", "CED"]
inconf_filtered = filtered_df[
    (filtered_df["UNIDADE:"].isin(desired_unidades_list)) &
    (filtered_df["INCONFORMIDADE 1:"] != "-")
]

grouped_data = inconf_filtered.groupby(["UNIDADE:", "INCONFORMIDADE 1:"]).size().reset_index(name="Quantidade")
grouped_data = grouped_data.sort_values(by="Quantidade", ascending=False)

fig_inconformidade = px.bar(grouped_data, x="UNIDADE:", y="Quantidade", color="INCONFORMIDADE 1:",
                            title="Quantidade de Inconformidades por Unidade")
col5.plotly_chart(fig_inconformidade)

# --------------------------------------------------------------------------
# LINE CHART: Comportamento das Inconformidades por Mês
# --------------------------------------------------------------------------
inconformidade_data = filtered_df[filtered_df["INCONFORMIDADE 1:"] != "-"]
inconformidade_grouped = (
    inconformidade_data
    .groupby(["Year-Month", "INCONFORMIDADE 1:"])
    .size()
    .reset_index(name="Quantidade")
)

fig_inconformidade_lines = px.line(inconformidade_grouped, 
                                   x="Year-Month", 
                                   y="Quantidade", 
                                   color="INCONFORMIDADE 1:", 
                                   title="Comportamento das Inconformidades por Mês")
col7.plotly_chart(fig_inconformidade_lines)

# --------------------------------------------------------------------------
# DONUT CHART: Porcentagem de Produtividade da Equipe
# (processos que estão FINALIZADO ou DEVOLVIDO A UNIDADE)
# --------------------------------------------------------------------------
completed_jobs = filtered_df[filtered_df["ANDAMENTO:"].isin(["FINALIZADO", "DEVOLVIDO A UNIDADE"])]
analista_counts = completed_jobs["ANALISTA:"].value_counts().reset_index()
analista_counts.columns = ["ANALISTA:", "Quantidade"]

fig_donut = px.pie(
    analista_counts,
    names="ANALISTA:",
    values="Quantidade",
    title="Porcentagem de Produtividade da Equipe",
    hole=0.4
)
col3.plotly_chart(fig_donut)

# --------------------------------------------------------------------------
# TREEMAP: CLASSIFICAÇÃO DO PROCESSO -> ANALISTA
# --------------------------------------------------------------------------
classification_by_analyst = (
    filtered_df
    .groupby(["CLASSIFICAÇÃO DO PROCESSO:", "ANALISTA:"])
    .size()
    .reset_index(name="Quantidade")
)

fig_treemap_inverted = px.treemap(
    classification_by_analyst,
    path=["CLASSIFICAÇÃO DO PROCESSO:", "ANALISTA:"],
    values="Quantidade",
    title="Classificação do Processo por Analista",
    color="Quantidade",
    color_continuous_scale="Blues"
)
col10.plotly_chart(fig_treemap_inverted)

# --------------------------------------------------------------------------
# LEAD TIME MÉDIO (MÉTRICA) e LEAD TIME AO LONGO DO TEMPO
# --------------------------------------------------------------------------
avg_lead_time_value = filtered_df["LEAD TIME DO PROCESSO:"].mean()
avg_lead_time_str = f"{avg_lead_time_value:.3f}"  # 3 decimal places

col9.subheader('Lead Time médio ⏳')
col9.metric(label='Lead Time (dias)', value=avg_lead_time_str)
col9.write("Esse valor representa o lead time do período selecionado.")

# Evolução do lead time ao longo do tempo
avg_lead_time_over_time = filtered_df.groupby("Year-Month")["LEAD TIME DO PROCESSO:"].mean().reset_index()
fig_avg_lead_time_over_time = px.line(
    avg_lead_time_over_time,
    x="Year-Month",
    y="LEAD TIME DO PROCESSO:",
    title="Lead Time Médio ao longo do tempo"
)
fig_avg_lead_time_over_time.update_traces(mode="lines+markers")

fig_avg_lead_time_over_time.update_layout(width=600)
col8.plotly_chart(fig_avg_lead_time_over_time)

# --------------------------------------------------------------------------
# DISPLAY THE FILTERED DATAFRAME
# --------------------------------------------------------------------------
st.write("### Dados Selecionados:")
st.dataframe(filtered_df)
