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

# Convert the "DATA DE ATRIBUIÇÃO:" column to datetime with errors='coerce'
df["DATA DE ATRIBUIÇÃO:"] = pd.to_datetime(df["DATA DE ATRIBUIÇÃO:"], format='%d/%m/%Y', errors='coerce')

# Filter out rows where the date could not be parsed (NaT)
df = df.dropna(subset=["DATA DE ATRIBUIÇÃO:"])

# Extract year, month, and quarter
df["Year"] = df["DATA DE ATRIBUIÇÃO:"].dt.year
df["Month"] = df["DATA DE ATRIBUIÇÃO:"].dt.month
df["Quarter"] = df["DATA DE ATRIBUIÇÃO:"].dt.quarter
df["Semester"] = np.where(df["DATA DE ATRIBUIÇÃO:"].dt.month.isin([1, 2, 3, 4, 5, 6]), 1, 2)

# Create a "Year-Quarter" column
df["Year-Quarter"] = df["Year"].astype(str) + "-T" + df["Quarter"].astype(str)

# If you want to create a "Year-Month" column, you can use the following line
df["Year-Month"] = df["DATA DE ATRIBUIÇÃO:"].dt.strftime("%Y-%m")

# Create a "Year-Quarter" column
df["Year-Semester"] = df["Year"].astype(str) + "-S" + df["Semester"].astype(str)


#----------------------- CREATING THE COLUMN TO DATA DE CONCLUSÃO ------


df = df.sort_values("DATA DE CONCLUSÃO:")
# Convert the "DATA DE ATRIBUIÇÃO:" column to datetime with errors='coerce'
df["DATA DE CONCLUSÃO:"] 
