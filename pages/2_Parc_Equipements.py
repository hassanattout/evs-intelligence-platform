import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

from src.data_generator import generate_synthetic_data
from src.risk_scoring import calculate_risk_score

st.title("Parc Équipements")

df = generate_synthetic_data(300)
df = calculate_risk_score(df)

st.sidebar.header("Filtres")

risk_filter = st.sidebar.multiselect(
    "Classe de risque",
    options=df["risk_class"].dropna().unique(),
    default=df["risk_class"].dropna().unique()
)

environment_filter = st.sidebar.multiselect(
    "Environnement",
    options=df["environment"].unique(),
    default=df["environment"].unique()
)

criticality_filter = st.sidebar.multiselect(
    "Niveau de criticité",
    options=sorted(df["criticality_level"].unique()),
    default=sorted(df["criticality_level"].unique())
)

filtered_df = df[
    (df["risk_class"].isin(risk_filter)) &
    (df["environment"].isin(environment_filter)) &
    (df["criticality_level"].isin(criticality_filter))
]

st.subheader("Vue globale du parc")
st.write(f"Nombre d'équipements affichés: {len(filtered_df)}")

st.dataframe(filtered_df, use_container_width=True)

st.subheader("Sélection d'un équipement")

selected_equipment = st.selectbox(
    "Choisir un équipement",
    filtered_df["equipment_id"]
)

equipment = filtered_df[filtered_df["equipment_id"] == selected_equipment].iloc[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Âge", f"{equipment['age_years']} ans")
col2.metric("Risque", f"{equipment['risk_score']}/100")
col3.metric("Classe", equipment["risk_class"])
col4.metric("Pannes 3 ans", equipment["number_of_failures_3y"])

st.write("### Détails équipement")
st.json(equipment.to_dict())