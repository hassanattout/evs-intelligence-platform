import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd

from src.data_generator import generate_synthetic_data
from src.risk_scoring import calculate_risk_score

st.title("Rapport & Recommandations")

df = generate_synthetic_data(300)
df = calculate_risk_score(df)

selected_equipment = st.selectbox(
    "Choisir un équipement",
    df["equipment_id"]
)

equipment = df[df["equipment_id"] == selected_equipment].iloc[0]

st.subheader("Synthèse équipement")

col1, col2, col3 = st.columns(3)

col1.metric("Équipement", equipment["equipment_id"])
col2.metric("Score de risque", f"{equipment['risk_score']}/100")
col3.metric("Classe de risque", equipment["risk_class"])

st.markdown("---")

st.subheader("Données techniques")

technical_data = {
    "Âge": f"{equipment['age_years']} ans",
    "Heures d'utilisation/an": equipment["usage_hours_per_year"],
    "Dernière maintenance": f"{equipment['last_maintenance_days']} jours",
    "Pannes sur 3 ans": equipment["number_of_failures_3y"],
    "Environnement": equipment["environment"],
    "Criticité": equipment["criticality_level"],
    "Non-conformités réglementaires": equipment["regulatory_non_conformities"],
}

st.table(pd.DataFrame(technical_data.items(), columns=["Paramètre", "Valeur"]))

st.markdown("---")

st.subheader("Recommandation automatique")

risk_class = equipment["risk_class"]

if risk_class == "Critique":
    recommendation = "Arrêt recommandé et intervention immédiate."
    priority = "Priorité 1"
    inspection_delay = "Sous 7 jours"
    st.error(recommendation)

elif risk_class == "Élevé":
    recommendation = "Maintenance corrective à planifier rapidement."
    priority = "Priorité 2"
    inspection_delay = "Sous 30 jours"
    st.warning(recommendation)

elif risk_class == "Modéré":
    recommendation = "Surveillance renforcée et maintenance préventive."
    priority = "Priorité 3"
    inspection_delay = "Sous 90 jours"
    st.info(recommendation)

else:
    recommendation = "Suivi standard selon le planning de maintenance."
    priority = "Priorité 4"
    inspection_delay = "Inspection périodique"
    st.success(recommendation)

st.write(f"**Niveau de priorité:** {priority}")
st.write(f"**Délai recommandé:** {inspection_delay}")

st.markdown("---")

st.subheader("Rapport synthétique")

report_text = f"""
Rapport EVS automatisé

Équipement: {equipment['equipment_id']}
Âge: {equipment['age_years']} ans
Environnement: {equipment['environment']}

Score de risque: {equipment['risk_score']}/100
Classe de risque: {equipment['risk_class']}

Historique de pannes sur 3 ans: {equipment['number_of_failures_3y']}
Dernière maintenance: {equipment['last_maintenance_days']} jours
Non-conformités réglementaires: {equipment['regulatory_non_conformities']}

Recommandation:
{recommendation}

Priorité:
{priority}

Délai recommandé:
{inspection_delay}
"""

st.text_area("Rapport généré", report_text, height=350)

st.download_button(
    label="Télécharger le rapport",
    data=report_text,
    file_name=f"rapport_evs_{selected_equipment}.txt",
    mime="text/plain"
)