import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd

from src.data_generator import generate_synthetic_data
from src.risk_scoring import calculate_risk_score, normalize

st.title("Évaluation du Risque")

# Data
df = generate_synthetic_data(300)
df = calculate_risk_score(df)

# Selection
selected_equipment = st.selectbox(
    "Choisir un équipement",
    df["equipment_id"]
)

equipment = df[df["equipment_id"] == selected_equipment].iloc[0]

# Display main metrics
col1, col2, col3 = st.columns(3)

col1.metric("Score de risque", f"{equipment['risk_score']}/100")
col2.metric("Classe", equipment["risk_class"])
col3.metric("Âge", f"{equipment['age_years']} ans")

st.markdown("---")

st.subheader("Analyse des facteurs de risque")

# Compute factors manually for explainability
df_temp = df.copy()

age_factor = normalize(df_temp["age_years"])
usage_factor = normalize(df_temp["usage_hours_per_year"])
maintenance_factor = normalize(df_temp["last_maintenance_days"])
failure_factor = normalize(df_temp["number_of_failures_3y"])
regulatory_factor = normalize(df_temp["regulatory_non_conformities"])
criticality_factor = normalize(df_temp["criticality_level"])

environment_map = {
    "Normal": 0.2,
    "Poussiéreux": 0.5,
    "Humide": 0.6,
    "Sévère": 1.0
}

env_factor = df_temp["environment"].map(environment_map)

# Extract selected row index
idx = df_temp[df_temp["equipment_id"] == selected_equipment].index[0]

factors = {
    "Âge": age_factor.iloc[idx],
    "Utilisation": usage_factor.iloc[idx],
    "Retard maintenance": maintenance_factor.iloc[idx],
    "Historique pannes": failure_factor.iloc[idx],
    "Environnement": env_factor.iloc[idx],
    "Non-conformités": regulatory_factor.iloc[idx],
    "Criticité": criticality_factor.iloc[idx],
}

factor_df = pd.DataFrame.from_dict(factors, orient="index", columns=["Impact"])

st.bar_chart(factor_df)

st.subheader("Interprétation")

# Simple explanation logic
explanations = []

if factors["Âge"] > 0.7:
    explanations.append("Équipement ancien")

if factors["Retard maintenance"] > 0.7:
    explanations.append("Maintenance en retard")

if factors["Historique pannes"] > 0.6:
    explanations.append("Historique de pannes élevé")

if factors["Environnement"] > 0.7:
    explanations.append("Environnement sévère")

if factors["Non-conformités"] > 0.5:
    explanations.append("Présence de non-conformités")

if factors["Criticité"] > 0.7:
    explanations.append("Équipement critique pour l’activité")

if explanations:
    for exp in explanations:
        st.write(f"• {exp}")
else:
    st.write("Aucun facteur critique majeur détecté")

st.markdown("---")

st.subheader("Conclusion")

if equipment["risk_class"] in ["Élevé", "Critique"]:
    st.error("Risque élevé → intervention recommandée rapidement")
elif equipment["risk_class"] == "Modéré":
    st.warning("Risque modéré → surveillance renforcée")
else:
    st.success("Risque faible → suivi standard")