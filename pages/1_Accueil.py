import streamlit as st
import pandas as pd

from src.data_generator import generate_synthetic_data
from src.risk_scoring import calculate_risk_score

st.title("EVS Intelligence Platform")

# Generate data
df = generate_synthetic_data(300)

# Calculate risk
df = calculate_risk_score(df)

# Metrics
total_equipment = len(df)
avg_risk = round(df["risk_score"].mean(), 1)
high_risk = len(df[df["risk_class"].isin(["Élevé", "Critique"])])

col1, col2, col3 = st.columns(3)

col1.metric("Nombre d'équipements", total_equipment)
col2.metric("Risque moyen", avg_risk)
col3.metric("Équipements à risque élevé", high_risk)

st.subheader("Répartition des niveaux de risque")

st.bar_chart(df["risk_class"].value_counts())

st.subheader("Top 10 équipements les plus critiques")

top10 = df.sort_values(by="risk_score", ascending=False).head(10)

st.dataframe(top10)