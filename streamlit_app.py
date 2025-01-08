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
df = df.sort_values("DATA DE ATRIBUIÇÃO:")

# Convert the "DATA DE ATRIBUIÇÃO:" column to datetime
df["DATA DE ATRIBUIÇÃO:"] = pd.to_datetime(df["DATA DE ATRIBUIÇÃO:"], format='%d/%m/%Y', errors='coerce')
df = df.dropna(subset=["DATA DE ATRIBUIÇÃO:"])  # drop rows with unparseable dates

# Extract year, month, etc.
df["Year"] = df["DATA DE ATRIBUIÇÃO:"].dt.year
df["Month"] = df["DATA DE ATRIBUIÇÃO:"].dt.month
df["Quarter"] = df["DATA DE ATRIBUIÇÃO:"].dt.quarter
df["Semester"] = np.where(df["Month"].isin([1,2,3,4,5,6]), 1, 2)
df["Year-Quarter"] = df["Year"].astype(str) + "-T" + df["Quarter"].astype(str)
df["Year-Month"] = df["DATA DE ATRIBUIÇÃO:"].dt.strftime("%Y-%m")
df["Year-Semester"] = df["Year"].astype(str) + "-S" + df["Semester"].astype(str)

# ------------------ Data de Conclusão ------------------
df = df.sort_values("DATA DE CONCLUSÃO:")
df["DATA DE CONCLUSÃO:"] = pd.to_datetime(df["DATA DE CONCLUSÃO:"], format='%d/%m/%Y', errors='coerce')
df = df.dropna(subset=["DATA DE CONCLUSÃO:"])

df["Year conclusion"] = df["DATA DE CONCLUSÃO:"].dt.year
df["Month conclusion"] = df["DATA DE CONCLUSÃO:"].dt.month
df["Quarter conclusion"] = df["DATA DE CONCLUSÃO:"].dt.quarter
df["Semester conclusion"] = np.where(df["Month conclusion"].isin([1,2,3,4,5,6]), 1, 2)
df["Year-Quarter conclusion"] = df["Year conclusion"].astype(str) + "-T" + df["Quarter conclusion"].astype(str)
df["Year-Month conclusion"] = df["DATA DE CONCLUSÃO:"].dt.strftime("%Y-%m")
df["Year-Semester conclusion"] = df["Year conclusion"].astype(str) + "-S" + df["Semester conclusion"].astype(str)
# --------------------------------------------------------

unique_year_month = sorted(df["Year-Month"].unique())
unique_year_quarter = sorted(df["Year-Quarter"].unique())
unique_year_semester = sorted(df["Year-Semester"].unique())
unique_year = sorted(df["Year"].unique())

unique_year_month.insert(0, "Todos")
unique_year_quarter.insert(0, "Todos")
unique_year_semester.insert(0, "Todos")
unique_year.insert(0, "Todos")

# Define the list of "CLASSIFICAÇÃO DO PROCESSO:" values and add "Todos"
desired_classificacao = df["CLASSIFICAÇÃO DO PROCESSO:"].unique().tolist()
desired_classificacao.insert(0, "Todos")
classificacao = st.sidebar.selectbox("Classificação do Processo:", desired_classificacao)

# Define the list of "NÚMERO DO PROCESSO:" values and add "Todos"
desired_numero_processo = df["NÚMERO DO PROCESSO:"].unique().tolist()
desired_numero_processo.insert(0, "Todos")
numero_processo = st.sidebar.selectbox("Número do Processo:", desired_numero_processo)

month = st.sidebar.selectbox("Mês", unique_year_month)
quarter = st.sidebar.selectbox("Trimestre", unique_year_quarter)
semester = st.sidebar.selectbox("Semestre", unique_year_semester)
year = st.sidebar.selectbox("Ano", unique_year)

desired_unidades = ["CRER", "HECAD", "HUGOL", "HDS", "AGIR", "TEIA", "CED"]
desired_unidades.insert(0, "Todos")
unidade = st.sidebar.selectbox("Unidade:", desired_unidades)

# --------------- Apply Filters ---------------
if month == "Todos":
    df_filtered = df
else:
    df_filtered = df[df["Year-Month"] == month]

if quarter != "Todos":
    df_filtered = df_filtered[df_filtered["Year-Quarter"] == quarter]

if semester != "Todos":
    df_filtered = df_filtered[df_filtered["Year-Semester"] == semester]

if year != "Todos":
    df_filtered = df_filtered[df_filtered["Year"] == year]

if unidade != "Todos":
    df_filtered = df_filtered[df_filtered["UNIDADE:"] == unidade]

if classificacao != "Todos":
    df_filtered = df_filtered[df_filtered["CLASSIFICAÇÃO DO PROCESSO:"] == classificacao]

if numero_processo != "Todos":
    df_filtered = df_filtered[df_filtered["NÚMERO DO PROCESSO:"] == numero_processo]

# ------------------------------------------------

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)
col5, col7 = st.columns(2)
col6 = st.columns(1)
col8, col9 = st.columns(2)

# Calculate the Quantity of "ATRIBUÍDO" (simply the number of rows in df_filtered)
quantity_atribuido = len(df_filtered)

# A simpler example of quantity_finalizado and quantity_residual
# (But keep your logic if you have a specific calculation)
quantity_residual = (df1["FORMULA 1"] == 2).sum()

if quarter == "Todos" and month == "Todos":
    quantity_finalizado = quantity_atribuido - quantity_residual
else:
    if quarter == "Todos":
        first_year_month = df_filtered["Year-Month"].iloc[0] if not df_filtered.empty else None
        quantity_finalizado = (df["Year-Month conclusion"] == first_year_month).sum() if first_year_month else 0
    else:
        if month == "Todos":
            first_year_quarter = df_filtered["Year-Quarter"].iloc[0] if not df_filtered.empty else None
            quantity_finalizado = (df["Year-Quarter conclusion"] == first_year_quarter).sum() if first_year_quarter else 0
        else:
            quantity_finalizado = 0

quantity_residual = quantity_atribuido - quantity_finalizado

st.sidebar.markdown(f"**RESIDUAL:** {quantity_residual}")
st.sidebar.markdown(f"**ATRIBUÍDO:** {quantity_atribuido}")
st.sidebar.markdown(f"**FINALIZADO:** {quantity_finalizado}")

# -- Bar Chart: Processos atribuídos a cada analista
df_filtered["ANALISTA:"] = (
    df_filtered["ANALISTA:"]
    .str.strip()
    .str.lower()
    .str.capitalize()
)
df_filtered["ANALISTA:"].replace(
    {"Renato": "Renato", "Ingrid": "Ingrid", "Naiani": "Naiani", "Yasmine ": "Yasmine"},
    inplace=True
)
counts = df_filtered["ANALISTA:"].value_counts().reset_index()
counts.columns = ["ANALISTA", "Quantidade"]

fig_date = px.bar(counts, x="ANALISTA", y="Quantidade", title="Quantidade de processos atribuídos a cada analista")
col1.plotly_chart(fig_date)

# -- Bar Chart: Lead time médio por analista
avg_lead_time = df_filtered.groupby("ANALISTA:")["LEAD TIME DO PROCESSO:"].mean().reset_index()
avg_lead_time = avg_lead_time.sort_values(by="LEAD TIME DO PROCESSO:", ascending=False)
fig_avg_lead_time = px.bar(avg_lead_time, x="ANALISTA:", y="LEAD TIME DO PROCESSO:", title="Lead Time Médio por Analista")
col2.plotly_chart(fig_avg_lead_time)

# -- Line Chart: Taxa de assertividade por mês
assertividade_data = (
    df_filtered.groupby(["Year-Month"])["ANDAMENTO:"]
    .apply(lambda x: (x == "FINALIZADO").sum() / x.count() * 100 if x.count() else 0)
    .reset_index()
)
assertividade_data.columns = ["Year-Month", "Taxa de assertividade"]
fig_assertividade = px.line(
    assertividade_data,
    x="Year-Month",
    y="Taxa de assertividade",
    title="Taxa de assertividade dos processos recebidos (%)"
)
fig_assertividade.add_hline(y=90, line_dash="dash", line_color="green", annotation_text="90%", annotation_position="bottom right")
fig_assertividade.add_annotation(text="META", xref="paper", yref="y", x=0.999, y=91, showarrow=False)
col4.plotly_chart(fig_assertividade)

# -- Bar Chart: Inconformidades por Unidade
desired_unidades_inconf = ["CRER", "HECAD", "HUGOL", "HDS", "AGIR", "TEIA", "CED"]
df_inconf = df_filtered[
    (df_filtered["UNIDADE:"].isin(desired_unidades_inconf)) 
    & (df_filtered["INCONFORMIDADE 1:"] != "-")
]
grouped_data = df_inconf.groupby(["UNIDADE:", "INCONFORMIDADE 1:"]).size().reset_index(name="Quantidade")
grouped_data = grouped_data.sort_values(by="Quantidade", ascending=False)
fig_inconformidade = px.bar(
    grouped_data,
    x="UNIDADE:",
    y="Quantidade",
    color="INCONFORMIDADE 1:",
    title="Quantidade de Inconformidades por Unidade"
)
col5.plotly_chart(fig_inconformidade)

# -- Line Chart: Comportamento das Inconformidades por Mês
inconformidade_data = df_inconf[df_inconf["INCONFORMIDADE 1:"] != "-"]
inconformidade_grouped = (
    inconformidade_data.groupby(["Year-Month", "INCONFORMIDADE 1:"])
    .size()
    .reset_index(name="Quantidade")
)
fig_inconformidade_lines = px.line(
    inconformidade_grouped,
    x="Year-Month",
    y="Quantidade",
    color="INCONFORMIDADE 1:",
    title="Comportamento das Inconformidades por Mês"
)
col7.plotly_chart(fig_inconformidade_lines)

# -- Donut Chart: Porcentagem de Produtividade da Equipe
completed_jobs = df_filtered[df_filtered["ANDAMENTO:"].isin(["FINALIZADO", "DEVOLVIDO A UNIDADE"])]
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

# --------------------------------------------------------
#  ULTIMO GRÁFICO - DINÂMICO: VALOR RESIDUAL AO LONGO DO TEMPO
# --------------------------------------------------------
# A) Contar quantos processos foram atribuídos em cada "Year-Month"
assigned_per_month = (
    df.groupby("Year-Month")["NÚMERO DO PROCESSO:"]
    .count()
    .sort_index()
    .rename("Assigned")
)

# B) Contar quantos processos foram finalizados em cada "Year-Month conclusion"
concluded_per_month = (
    df[df["ANDAMENTO:"] == "FINALIZADO"]  # ou você pode tirar esse filtro se quiser "concluído" de outra forma
    .groupby("Year-Month conclusion")["NÚMERO DO PROCESSO:"]
    .count()
    .sort_index()
    .rename("Concluded")
)

# Precisamos de uma lista única de meses (Year-Month) presentes em ambos
all_months = sorted(set(assigned_per_month.index).union(set(concluded_per_month.index)))

# Criar DataFrame com todos os meses
df_residual_calc = pd.DataFrame({"Year-Month": all_months}).set_index("Year-Month")

# Juntar as colunas Assigned e Concluded, preenchendo 0 onde não há valor
df_residual_calc["Assigned"] = assigned_per_month
df_residual_calc["Concluded"] = concluded_per_month
df_residual_calc = df_residual_calc.fillna(0)

# Agora vamos calcular cumulativo: total atribuído até o mês, menos total concluído até o mês
df_residual_calc["Assigned_cum"] = df_residual_calc["Assigned"].cumsum()
df_residual_calc["Concluded_cum"] = df_residual_calc["Concluded"].cumsum()

# "Valor Residual" é a diferença cumulativa
df_residual_calc["Valor Residual"] = df_residual_calc["Assigned_cum"] - df_residual_calc["Concluded_cum"]

# Vamos plotar
fig_residual = px.line(
    df_residual_calc.reset_index(),
    x="Year-Month",
    y="Valor Residual",
    title="Valor Residual ao longo do tempo (Dinâmico)"
)
fig_residual.update_traces(mode="lines+markers")
fig_residual.add_hline(y=0, line_dash="dash", line_color="green")

# Se quiser ajustar largura:
fig_residual.update_layout(width=1125)

st.plotly_chart(fig_residual)




#----------------------------------------------------------------------


# Create a line chart for the residual values over time
fig_residual = px.line(df_residual_values, x="Year-Month", y="Valor Residual", title="Valor Residual ao longo do tempo")

# Customize the line chart if needed
fig_residual.update_traces(mode="lines+markers")

fig_residual.add_hline(y=0, line_dash="dash", line_color="green")

# Update the layout to set the width
fig_residual.update_layout(width=1125)  # You can adjust the width as needed

# Show the line chart in Streamlit
st.plotly_chart(fig_residual)



avg_lead_time_value = filtered_df["LEAD TIME DO PROCESSO:"].mean()

# Format the average lead time value to display only three decimals
avg_lead_time_value = "{:.3f}".format(avg_lead_time_value)


# Display the average lead time in a metric display
col9.subheader('Lead Time médio ⏳')
col9.metric(label='Lead Time (dias)', value=avg_lead_time_value, delta=None)

# Optionally, you can add a description or any additional information
col9.write("Esse valor representa o lead time do período selecionado.")



# Group the data by "Year-Month" and calculate the average lead time
avg_lead_time_over_time = filtered_df.groupby("Year-Month")["LEAD TIME DO PROCESSO:"].mean().reset_index()

# Create a line chart for the average lead time over time
fig_avg_lead_time_over_time = px.line(avg_lead_time_over_time, x="Year-Month", y="LEAD TIME DO PROCESSO:", title="Lead Time Médio ao longo do tempo")

# Customize the line chart if needed
fig_avg_lead_time_over_time.update_traces(mode="lines+markers")

# Update the layout to set the width
fig_avg_lead_time_over_time.update_layout(width=600)


# Show the line chart in Streamlit
col8.plotly_chart(fig_avg_lead_time_over_time)



# Display the filtered DataFrame
st.write("Dados Selecionados:")
st.dataframe(filtered_df)




#atribuídos x realizados x residual
#meta de conformidade que é 90% e qual a % atual
#processos devolvidos e quais as suas inconformidades
#lead time por analista
#meta prevista de 100% e meta realizada
#quantidade de recebidos, de realziados e de inconformidades
#% de produtividade da equipe
#inconformidades por unidade
