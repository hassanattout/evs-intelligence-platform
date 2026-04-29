import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd

from src.data_generator import generate_synthetic_data
from src.risk_scoring import calculate_risk_score

st.title("Checklist EVS")

# Load data
df = generate_synthetic_data(300)
df = calculate_risk_score(df)

# Select equipment
selected_equipment = st.selectbox(
    "Choisir un équipement",
    df["equipment_id"]
)

equipment = df[df["equipment_id"] == selected_equipment].iloc[0]

st.subheader(f"Équipement sélectionné: {selected_equipment}")

# Checklist structure
checklist_items = [
    "Identification correcte",
    "Documentation disponible",
    "Historique maintenance complet",
    "État structurel",
    "Organes de levage",
    "Systèmes de sécurité",
    "Essais fonctionnels",
    "Conformité réglementaire",
    "Présence anomalies"
]

# Initialize session state
if "checklist" not in st.session_state:
    st.session_state.checklist = {
        item: "Conforme" for item in checklist_items
    }

st.subheader("Évaluation EVS")

for item in checklist_items:
    st.session_state.checklist[item] = st.selectbox(
        item,
        ["Conforme", "Non conforme", "Non applicable"],
        key=item
    )

# Convert to DataFrame
checklist_df = pd.DataFrame({
    "item": checklist_items,
    "status": list(st.session_state.checklist.values())
})

# Compute compliance
applicable = checklist_df[checklist_df["status"] != "Non applicable"]
conforme = applicable[applicable["status"] == "Conforme"]

if len(applicable) > 0:
    compliance_score = len(conforme) / len(applicable) * 100
else:
    compliance_score = 0

non_conformities = checklist_df[checklist_df["status"] == "Non conforme"]

st.markdown("---")

col1, col2 = st.columns(2)

col1.metric("Score de conformité", f"{round(compliance_score,1)}%")
col2.metric("Non-conformités", len(non_conformities))

st.subheader("Résultat détaillé")

st.dataframe(checklist_df)

# Highlight issues
st.subheader("Points critiques")

if len(non_conformities) > 0:
    for _, row in non_conformities.iterrows():
        st.error(f"Non conforme: {row['item']}")
else:
    st.success("Aucune non-conformité détectée")

st.markdown("---")

st.subheader("Recommandation EVS")

if compliance_score < 60:
    st.error("Non conforme → arrêt recommandé + intervention immédiate")
elif compliance_score < 80:
    st.warning("Conformité partielle → corrections nécessaires")
else:
    st.success("Conforme → exploitation autorisée")