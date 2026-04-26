import streamlit as st

st.set_page_config(
    page_title="EVS Intelligence Platform",
    page_icon="🏗️",
    layout="wide"
)

st.title("EVS Intelligence Platform")
st.caption("Outil d’aide à la décision pour la digitalisation de l’évaluation spéciale des ponts roulants")

st.markdown("## Synthèse exécutive")

st.markdown("""
Cette plateforme transforme le suivi EVS, historiquement basé sur des fichiers Excel, en un **outil interactif d’aide à la décision**.

### Fonctionnalités principales
- Priorisation multicritère des équipements: âge, cycle EVS, risque réglementaire, coût
- Simulation budgétaire sous contrainte CAPEX
- Analyse multi-sites
- Planification EVS dans le temps
- Projection du risque réglementaire
- Génération automatique d’un rapport PDF

### Valeur industrielle
- Réduction de l’exposition réglementaire
- Optimisation de l’allocation CAPEX
- Identification des équipements prioritaires
- Appui à une stratégie de maintenance pilotée par les données

👉 Utilisez le module **CAPEX Prioritization** dans la barre latérale pour lancer l’analyse.
""")

st.markdown("---")

st.markdown("## Déroulement de la démonstration")

st.markdown("""
1. Importer le fichier Excel CAPEX  
2. Analyser la priorisation EVS  
3. Simuler un budget disponible  
4. Exporter un rapport PDF  
""")