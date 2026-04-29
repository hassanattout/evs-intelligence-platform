import streamlit as st

st.set_page_config(
    page_title="EVS Intelligence Platform",
    page_icon="🏗️",
    layout="wide"
)

st.title("EVS Intelligence Platform")

st.caption(
    "Hassan Attout — Master MEE Énergétique, Sorbonne Université | Renault Group\n"
    "Digitalisation de l’Évaluation Spéciale des ponts roulants"
)

st.markdown("""
## Synthèse exécutive

Cette plateforme transforme un suivi EVS principalement basé sur Excel en un **outil interactif d’aide à la décision industrielle**.

Elle permet de structurer:
- la priorisation des équipements,
- l’évaluation du risque réglementaire,
- l’arbitrage CAPEX,
- la planification EVS dans le temps,
- la génération automatique d’un rapport de synthèse.

### Objectif industriel

L’objectif n’est pas de remplacer l’expertise métier, mais de fournir un support structuré pour orienter les décisions techniques, budgétaires et réglementaires.

👉 Utilisez le module **Planification EVS CAPEX** dans la barre latérale.
""")

st.warning(
    "Cet outil constitue une aide à la décision. "
    "Les résultats doivent être validés par les équipes métier compétentes avant toute décision technique, réglementaire ou budgétaire."
)

st.markdown("---")

st.markdown("""
## Déroulement de la démonstration

1. Importer le fichier Excel CAPEX  
2. Analyser les équipements prioritaires  
3. Identifier les sites critiques  
4. Simuler un budget disponible  
5. Générer un rapport PDF  
""")

st.markdown("---")

st.markdown(
    """
    <div style='text-align: center; font-size: 12px; color: grey;'>
    © 2026 Hassan Attout — EVS Intelligence Platform<br>
    Projet académique — Sorbonne Université — Renault Group<br>
    Outil d’aide à la décision basé sur des hypothèses simplifiées.
    </div>
    """,
    unsafe_allow_html=True
)