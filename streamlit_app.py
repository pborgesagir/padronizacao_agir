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
# 2) SIDEBAR FILTERS
# --------------------------------------------------------------------------

# --- Year/Month/Quarter/Semester filters ---
unique_year_month = sorted(df["Year-Month"].unique())
unique_year_quarter = sorted(df["Year-Quarter"].unique())
unique_year_semester = sorted(df["Year-Semester"].unique())
unique_year = sorted(df["Year"].unique())

unique_year_month.insert(0, "Todos")
unique_year_quarter.insert(0, "Todos")
unique_year_semester.insert(0, "Todos")
unique_year.insert(0, "Todos")

month = st.sidebar.selectbox("Mês", unique_year_month)
quarter = st.sidebar.selectbox("Trimestre", unique_year_quarter)
semester = st.sidebar.selectbox("Semestre", unique_year_semester)
year = st.sidebar.selectbox("Ano", unique_year)

# --- Classificação filter ---
desired_classificacao = df["CLASSIFICAÇÃO DO PROCESSO:"].unique().tolist()
desired_classificacao.insert(0, "Todos")
classificacao = st.sidebar.selectbox("Classificação do Processo:", desired_classificacao)

# --- Número do Processo filter ---
desired_numero_processo = df["NÚMERO DO PROCESSO:"].unique().tolist()
desired_numero_processo.insert(0, "Todos")
numero_processo = st.sidebar.selectbox("Número do Processo:", desired_numero_processo)

# --- Unidade filter ---
desired_unidades = ["CRER", "HECAD", "HUGOL", "HDS", "AGIR", "TEIA", "CED"]
desired_unidades.insert(0, "Todos")
unidade = st.sidebar.selectbox("Unidade:", desired_unidades)

# --------------------------------------------------------------------------
# 3) APPLY FILTERS IN SEQUENCE
# --------------------------------------------------------------------------
filtered_df = df.copy()

# 3.1) Year-Month
if month != "Todos":
    filtered_df = filtered_df[filtered_df["Year-Month"] == month]

# 3.2) Year-Quarter
if quarter != "Todos":
    filtered_df = filtered_df[filtered_df["Year-Quarter"] == quarter]

# 3.3) Year-Semester
if semester != "Todos":
    filtered_df = filtered_df[filtered_df["Year-Semester"] == semester]

# 3.4) Year
if year != "Todos":
    filtered_df = filtered_df[filtered_df["Year"] == year]

# 3.5) Unidade
if unidade != "Todos":
    filtered_df = filtered_df[filtered_df["UNIDADE:"] == unidade]

# 3.6) Classificação
if classificacao != "Todos":
    filtered_df = filtered_df[filtered_df["CLASSIFICAÇÃO DO PROCESSO:"] == classificacao]

# 3.7) Número do Processo
if numero_processo != "Todos":
    filtered_df = filtered_df[filtered_df["NÚMERO DO PROCESSO:"] == numero_processo]

# --------------------------------------------------------------------------
# 4) NEW FILTER FOR "ANALISTA:"
# --------------------------------------------------------------------------
# Before we do the filter, let's standardize the analyst names across the entire filtered_df.
# (Or do it in df beforehand, if you prefer.)

filtered_df["ANALISTA:"] = (
    filtered_df["ANALISTA:"]
    .astype(str)            # just in case of non-string
    .str.strip()
    .str.lower()
    .str.capitalize()
)

# Optionally, replace certain names as you did before:
filtered_df["ANALISTA:"].replace(
    {
        "Renato": "Renato", 
        "Ingrid": "Ingrid",
        "Naiani": "Naiani", 
        "Yasmine ": "Yasmine"
    }, 
    inplace=True
)

# Build the unique analyst list for the sidebar
unique_analista = sorted(filtered_df["ANALISTA:"].unique())
unique_analista.insert(0, "Todos")

analista = st.sidebar.selectbox("Analista:", unique_analista)

if analista != "Todos":
    filtered_df = filtered_df[filtered_df["ANALISTA:"] == analista]



col9, col8 = st.columns(2)
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)
col10 = st.columns(1)[0] 
col5, col7 = st.columns(2)
col6 = st.columns(1)









# Calculate the Quantity of "ATRIBUÍDO" (total number of rows in filtered_df)
quantity_atribuido = len(filtered_df["Year-Month"])
quantity_residual = (df1["FORMULA 1"] == 2).sum()
# Calculate the Quantity of "FINALIZADO"
if quarter == "Todos" and month == "Todos":
    # When both "Trimestre" and "Mês" are "Todos", quantity_finalizado is the count of values in "FORMULA 1" in df
    quantity_finalizado = quantity_atribuido - quantity_residual
else:
    # When at least one of "Trimestre" or "Mês" is not "Todos"
    if quarter == "Todos":
        # When only "Trimestre" is "Todos", use the first value in "Year-Month" of filtered_df
        first_year_month = filtered_df["Year-Month"].iloc[0]
        quantity_finalizado = (df["Year-Month conclusion"] == first_year_month).sum()
    else:
        if month == "Todos":
            # When only "Mês" is "Todos", use the first value in "Year-Quarter" of filtered_df
            first_year_quarter = filtered_df["Year-Quarter"].iloc[0]
            quantity_finalizado = (df["Year-Quarter conclusion"] == first_year_quarter).sum()
        else:
            # When both "Trimestre" and "Mês" are not "Todos", quantity_finalizado is 0
            quantity_finalizado = 0

# Calculate the Quantity of "RESIDUAL"
quantity_residual = quantity_atribuido - quantity_finalizado







# Create a dictionary to hold the values
data = {
    'Category': ['RESIDUAL', 'ATRIBUÍDO', 'FINALIZADO'],
    'Quantity': [quantity_residual, quantity_atribuido, quantity_finalizado]
}


# You can also display the values as text in the sidebar
st.sidebar.markdown(f"**RESIDUAL:** {quantity_residual}")
st.sidebar.markdown(f"**ATRIBUÍDO:** {quantity_atribuido}")
st.sidebar.markdown(f"**FINALIZADO:** {quantity_finalizado}")

# Standardize the names and capitalize the first letter
filtered_df["ANALISTA:"] = filtered_df["ANALISTA:"].str.strip().str.lower().str.capitalize()
filtered_df["ANALISTA:"].replace({"Renato": "Renato", "Ingrid": "Ingrid", "Naiani": "Naiani", "Yasmine ": "Yasmine"}, inplace=True)

counts = filtered_df["ANALISTA:"].value_counts().reset_index()
counts.columns = ["ANALISTA", "Quantidade"]

fig_date = px.bar(counts, x="ANALISTA", y="Quantidade", title="Quantidade de processos atribuídos a cada analista")
col1.plotly_chart(fig_date)

# Assuming filtered_df is your DataFrame
avg_lead_time = filtered_df.groupby("ANALISTA:")["LEAD TIME DO PROCESSO:"].mean().reset_index()
avg_lead_time = avg_lead_time.sort_values(by="LEAD TIME DO PROCESSO:", ascending=False)

fig_avg_lead_time = px.bar(avg_lead_time, x="ANALISTA:", y="LEAD TIME DO PROCESSO:", title="Lead Time Médio por Analista")
col2.plotly_chart(fig_avg_lead_time)

#   TERCEIRO GRÁFICO
# Calculate the "Taxa de assertividade" for each month
assertividade_data = filtered_df.groupby(["Year-Month"])["ANDAMENTO:"].apply(lambda x: (x == "FINALIZADO").sum() / x.count() * 100).reset_index()
assertividade_data.columns = ["Year-Month", "Taxa de assertividade"]

# Create a line chart
fig_assertividade = px.line(assertividade_data, x="Year-Month", y="Taxa de assertividade", title="Taxa de assertividade dos processos recebidos (%)")

# Add a horizontal line at 90%
fig_assertividade.add_hline(y=90, line_dash="dash", line_color="green", annotation_text="90%", annotation_position="bottom right")

# Add the "target" annotation
fig_assertividade.add_annotation(text="META", xref="paper", yref="y", x=0.999, y=91, showarrow=False)

# Show the line chart
col4.plotly_chart(fig_assertividade)

# QUARTO GRÁFICOOO -------------------

# Define the list of "UNIDADE:" values you want to include
desired_unidades = ["CRER", "HECAD", "HUGOL", "HDS", "AGIR", "TEIA", "CED"]

# Filter the DataFrame to include only the desired "UNIDADE:" values and where "INCONFORMIDADE 1:" is not equal to "-"
filtered_df = filtered_df[(filtered_df["UNIDADE:"].isin(desired_unidades)) & (filtered_df["INCONFORMIDADE 1:"] != "-")]

# Group the data by "UNIDADE:" and "INCONFORMIDADE 1:" and count the occurrences
grouped_data = filtered_df.groupby(["UNIDADE:", "INCONFORMIDADE 1:"]).size().reset_index(name="Quantidade")

# Sort the grouped_data DataFrame in descending order based on the "Quantidade" column
grouped_data = grouped_data.sort_values(by="Quantidade", ascending=False)

# Create a bar chart
fig_inconformidade = px.bar(grouped_data, x="UNIDADE:", y="Quantidade", color="INCONFORMIDADE 1:", title="Quantidade de Inconformidades por Unidade")

# Show the bar chart
col5.plotly_chart(fig_inconformidade)

#QUINTO GRÁFICO --------------------------------------

# Filter out rows with "-" values in "INCONFORMIDADE 1:"
inconformidade_data = filtered_df[filtered_df["INCONFORMIDADE 1:"] != "-"]

# Group the data by "Year-Month" and "INCONFORMIDADE 1:" and count the occurrences
inconformidade_grouped = inconformidade_data.groupby(["Year-Month", "INCONFORMIDADE 1:"]).size().reset_index(name="Quantidade")

# Create a line chart with multiple lines, one for each value in "INCONFORMIDADE 1:"
fig_inconformidade_lines = px.line(inconformidade_grouped, x="Year-Month", y="Quantidade", color="INCONFORMIDADE 1:", title="Comportamento das Inconformidades por Mês")

# Show the line chart
col7.plotly_chart(fig_inconformidade_lines)

#SEXTO GRÁFICO ---------------------------------

# Filter the DataFrame to include only rows with "FINALIZADO" or "DEVOLVIDO A UNIDADE" in "ANDAMENTO:"
completed_jobs = filtered_df[filtered_df["ANDAMENTO:"].isin(["FINALIZADO", "DEVOLVIDO A UNIDADE"])]

# Group the data by "ANALISTA:" and count the occurrences
analista_counts = completed_jobs["ANALISTA:"].value_counts().reset_index()
analista_counts.columns = ["ANALISTA:", "Quantidade"]

# Create a donut chart
fig_donut = px.pie(
    analista_counts,
    names="ANALISTA:",
    values="Quantidade",
    title="Porcentagem de Produtividade da Equipe",
    hole=0.4  # Adjust the hole size (0.4 represents 40% of the inner hole)
)

# Show the donut chart
col3.plotly_chart(fig_donut)





# #ULTIMO GRAFICO

# data = {
#     "Year-Month": ["2022-01", "2022-02", "2022-03", "2022-04", "2022-05", "2022-06", "2022-07", "2022-08", "2022-09", "2022-10", "2022-11", "2022-12", "2023-01", "2023-02", "2023-03", "2023-04", "2023-05", "2023-06", "2023-07", "2023-08", "2023-09", "2023-10", "2023-11", "2023-12", "2024-01", "2024-02"],
#     "Valor Residual": [20, 5, -1, -5, 11, 4, -6, -3, 7, -11, 0, -2, -13, -5, 2, -1, 4, -4, 6, 2, 0, -8, -1, -3, 0, 1]
# }

# df_residual_values = pd.DataFrame(data)



# #----------------------------------------------------------------------


# # Create a line chart for the residual values over time
# fig_residual = px.line(df_residual_values, x="Year-Month", y="Valor Residual", title="Valor Residual ao longo do tempo")

# # Customize the line chart if needed
# fig_residual.update_traces(mode="lines+markers")

# fig_residual.add_hline(y=0, line_dash="dash", line_color="green")

# # Update the layout to set the width
# fig_residual.update_layout(width=1125)  # You can adjust the width as needed

# # Show the line chart in Streamlit
# st.plotly_chart(fig_residual)


# --------------------------------------------------------------------------
# TREEMAP: CLASSIFICAÇÃO DO PROCESSO POR ANALISTA (INVERTED)
# --------------------------------------------------------------------------

# Group data by "CLASSIFICAÇÃO DO PROCESSO:" and "ANALISTA:" and count
classification_by_analyst = (
    filtered_df.groupby(["CLASSIFICAÇÃO DO PROCESSO:", "ANALISTA:"])
    .size()
    .reset_index(name="Quantidade")
)

# Create a treemap
fig_treemap_inverted = px.treemap(
    classification_by_analyst,
    path=["CLASSIFICAÇÃO DO PROCESSO:", "ANALISTA:"],  # Inverted order
    values="Quantidade",
    title="Classificação do Processo por Analista (Treemap Inverted)",
    color="Quantidade",
    color_continuous_scale="Blues",  # You can change color scale if desired
)

# Display the treemap in a Streamlit column or directly with st.plotly_chart
col10.plotly_chart(fig_treemap_inverted)







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
