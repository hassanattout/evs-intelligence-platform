from fpdf import FPDF
from datetime import datetime
import base64
import gzip
from io import StringIO

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="EVS Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
)

# ============================================================
# REAL DATA HARDCODED IN THE APP
# ============================================================
# This is the processed industrial dataset extracted from:
# Capex pont Roadmap.xlsx / sheet "Ponts".
# No Excel upload is required.
# The data is stored as compressed CSV to keep the code cleaner.

DATA_B64 = (
    "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"
    "uOdhhi4q/Rcx/R9dOiMkWDgAAA=="
)


# ============================================================
# HEADER
# ============================================================

st.title("EVS Intelligence Platform")

st.markdown("""
### Digitalisation de l’Évaluation Spéciale (EVS) des ponts roulants

**Auteur:** Hassan Attout
**Formation:** Master MEE Énergétique, Sorbonne Université
**Entreprise:** Renault Group, apprentissage
**Contexte:** Moyens de levage / maintenance industrielle
""")

st.caption("Outil d’aide à la décision pour la priorisation EVS et l’arbitrage CAPEX")

st.markdown("""
## Objectif de l’outil

Cet outil vise à transformer un suivi EVS principalement basé sur Excel en un **système d’aide à la décision**.

Il permet de:
- exploiter directement une base industrielle intégrée dans l’application,
- prioriser les équipements selon un score multicritère,
- simuler l’impact d’un budget CAPEX limité,
- identifier les sites les plus critiques,
- planifier les EVS dans le temps,
- visualiser les concentrations de criticité,
- générer un rapport PDF exploitable.

L’objectif n’est pas de remplacer l’expertise métier, mais de fournir un support structuré pour orienter les décisions techniques et budgétaires.
""")

st.warning("""
Cet outil constitue une aide à la décision.

Les résultats ne remplacent pas une expertise technique ou réglementaire.
Toute décision doit être validée par les équipes métier compétentes.
""")

st.markdown("---")

with st.expander("Hypothèses et limites de l’outil"):
    st.markdown("""
    Cet outil est un **prototype d’aide à la décision** développé dans le cadre d’un mémoire M2.

    ### Hypothèses principales
    - Les données sont intégrées directement dans le code à partir du fichier CAPEX fourni.
    - Le score EVS est basé sur les données disponibles: âge, année EVS, coût, statut EVS et informations roadmap/travaux.
    - La formule de scoring est une proposition méthodologique développée dans le cadre du mémoire.
    - Les pondérations et les seuils doivent être validés avec les experts métier Renault.
    - Les règles internes Renault, les exigences pays et les spécificités constructeur peuvent nécessiter un paramétrage complémentaire.

    ### Limites
    - L’outil ne remplace pas une expertise technique ou réglementaire.
    - Les résultats ne constituent pas une décision automatique d’arrêt, de remplacement ou d’intervention.
    - Les données de pannes, charges réelles, criticité production et historiques détaillés ne sont pas encore intégrées.
    - Le modèle actuel est une première version destinée à structurer la priorisation EVS.

    ### Utilisation recommandée
    Les résultats doivent être considérés comme un support de discussion pour orienter les priorités, puis validés par les responsables maintenance, méthodes et sécurité.
    """)


# ============================================================
# FUNCTIONS
# ============================================================

def load_hardcoded_data():
    csv_text = gzip.decompress(base64.b64decode(DATA_B64)).decode("utf-8")
    return pd.read_csv(StringIO(csv_text))


def normalize(series):
    series = pd.to_numeric(series, errors="coerce").fillna(0)
    if series.max() == series.min():
        return series * 0
    return (series - series.min()) / (series.max() - series.min())


def clean_text(text):
    return str(text).encode("latin-1", "ignore").decode("latin-1")


def parse_evs_flag(x):
    x = str(x).strip().lower()
    
    if x in ["n", "non", "no", "0"]:
        return 1.0
    elif x in ["o", "oui", "yes", "y", "1"]:
        return 0.3
    elif "interne" in x:
        return 0.6
    elif x in ["nc", "na", "nan", "", "none"]:
        return 0.6
    else:
        return 0.6


def apply_evs_rules(row):
    age = row["Age"]
    
    if age >= 40:
        return "EVS obligatoire"
    elif age >= 35:
        return "EVS à programmer"
    elif age >= 30:
        return "Première estimation"
    else:
        return "Suivi standard"


def assign_evs_decision(score):
    if score >= 0.75:
        return "EVS prioritaire immédiate"
    elif score >= 0.55:
        return "EVS à planifier"
    elif score >= 0.35:
        return "Surveillance renforcée"
    else:
        return "Suivi standard"


def generate_action_plan(row):
    score = row["priority_score"]
    
    if score >= 0.80:
        return "EVS immédiate + analyse technique approfondie"
    elif score >= 0.65:
        return "EVS urgente + arbitrage maintenance"
    elif score >= 0.55:
        return "EVS à planifier court terme"
    elif score >= 0.35:
        return "Surveillance + maintenance préventive"
    else:
        return "Suivi standard"


def generate_deadline(row):
    score = row["priority_score"]
    
    if score >= 0.80:
        return "0-3 mois"
    elif score >= 0.65:
        return "3-6 mois"
    elif score >= 0.55:
        return "6-12 mois"
    elif score >= 0.35:
        return "12-24 mois"
    else:
        return "Routine"


def build_budget_selection(sorted_df, budget):
    selected_projects = []
    total_cost = 0
    
    for _, row in sorted_df.iterrows():
        cost = row["Montant EVS"] if pd.notna(row["Montant EVS"]) else 0
        
        if total_cost + cost <= budget:
            selected_projects.append(row)
            total_cost += cost
            
    return pd.DataFrame(selected_projects), total_cost


def is_not_empty(value):
    return str(value).strip().lower() not in ["", "nan", "none", "nat"]


# ============================================================
# DATA LOADING
# ============================================================

clean_df = load_hardcoded_data()
data_source = "Base industrielle intégrée au code"

# Numeric safety
for col in ["Age", "EVS Année", "Montant EVS", "MES", "Prix neuf", "Roadmap obsolescence", "Roadmap sécurisation"]:
    if col in clean_df.columns:
        clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

clean_df["Age"] = clean_df["Age"].fillna(0).astype(int)
clean_df["EVS Année"] = clean_df["EVS Année"].fillna(0).astype(int)
clean_df["Montant EVS"] = clean_df["Montant EVS"].fillna(0).astype(int)

# String safety
for col in clean_df.columns:
    if clean_df[col].dtype == "object":
        clean_df[col] = clean_df[col].fillna("").astype(str).str.strip()

st.success(f"Source des données: {data_source}")


# ============================================================
# DATA QUALITY
# ============================================================

with st.expander("Qualité des données"):
    st.write(f"Nombre d’équipements intégrés: {len(clean_df)}")
    st.write(f"Valeurs manquantes Age: {clean_df['Age'].isna().sum()}")
    st.write(f"Valeurs manquantes EVS Année: {clean_df['EVS Année'].isna().sum()}")
    st.write(f"Valeurs manquantes Montant EVS: {clean_df['Montant EVS'].isna().sum()}")
    
    st.info("""
    La base utilisée provient du fichier industriel CAPEX fourni. 
    Elle a été préparée pour être intégrée directement dans le code afin que le dashboard affiche toujours les données sans import manuel.
    """)


# ============================================================
# SCORING
# ============================================================

clean_df["age_score"] = normalize(clean_df["Age"])
clean_df["evs_urgency"] = 1 - normalize(clean_df["EVS Année"])
clean_df["status_risk"] = clean_df["Statut EVS"].apply(parse_evs_flag)
clean_df["cost_score"] = normalize(clean_df["Montant EVS"])

clean_df["roadmap_risk"] = clean_df.apply(
    lambda row: 1.0 
    if is_not_empty(row.get("Roadmap sécurisation", "")) 
    else 0.7 
    if is_not_empty(row.get("Roadmap obsolescence", "")) 
    else 0.5 
    if is_not_empty(row.get("Travaux / RG", "")) 
    else 0.0, 
    axis=1,
)

st.sidebar.header("Réglage des pondérations")
st.sidebar.caption("Les pondérations positives sont normalisées automatiquement.")

w_age = st.sidebar.slider("Poids âge", 0.0, 1.0, 0.30, 0.05)
w_evs = st.sidebar.slider("Poids urgence EVS", 0.0, 1.0, 0.30, 0.05)
w_status = st.sidebar.slider("Poids statut EVS", 0.0, 1.0, 0.20, 0.05)
w_roadmap = st.sidebar.slider("Poids roadmap / travaux", 0.0, 1.0, 0.20, 0.05)
w_cost = st.sidebar.slider("Poids coût pénalisant", 0.0, 0.5, 0.10, 0.05)

positive_weight_sum = w_age + w_evs + w_status + w_roadmap

if positive_weight_sum == 0:
    st.error("Les pondérations positives ne peuvent pas toutes être nulles.")
    st.stop()

normalized_age = w_age / positive_weight_sum
normalized_evs = w_evs / positive_weight_sum
normalized_status = w_status / positive_weight_sum
normalized_roadmap = w_roadmap / positive_weight_sum

clean_df["priority_score"] = (
    normalized_age * clean_df["age_score"]
    + normalized_evs * clean_df["evs_urgency"]
    + normalized_status * clean_df["status_risk"]
    + normalized_roadmap * clean_df["roadmap_risk"]
    - w_cost * clean_df["cost_score"]
).clip(lower=0, upper=1).round(2)

clean_df["Décision règle EVS"] = clean_df.apply(apply_evs_rules, axis=1)
clean_df["Décision score"] = clean_df["priority_score"].apply(assign_evs_decision)
clean_df["Plan d’action"] = clean_df.apply(generate_action_plan, axis=1)
clean_df["Délai recommandé"] = clean_df.apply(generate_deadline, axis=1)

clean_df["Risque report 1 an"] = (clean_df["priority_score"] * 1.15).clip(upper=1).round(2)
clean_df["Risque report 2 ans"] = (clean_df["priority_score"] * 1.30).clip(upper=1).round(2)


# ============================================================
# METHODOLOGY
# ============================================================

with st.expander("Méthodologie du score EVS"):
    st.markdown(f"""
    Le score de priorité EVS est un **modèle multicritère d’aide à la décision** développé dans le cadre du mémoire.
    
    Il ne provient pas directement d’une norme ou d’un document Renault. 
    Il est inspiré des principes de l’AMDEC, de la maintenance basée sur le risque et de la priorisation multicritère.

    ### Formule conceptuelle
    
    **Score EVS = âge + urgence EVS + statut EVS + roadmap/travaux - coût**

    ### Critères utilisés
    
    - **Âge de l’équipement:** proxy de vieillissement mécanique.
    - **Urgence EVS:** proximité de l’échéance d’évaluation spéciale.
    - **Statut EVS:** indicateur issu de la situation EVS actuelle.
    - **Roadmap / travaux:** prise en compte des informations d’obsolescence, sécurisation ou travaux.
    - **Coût estimé:** pénalité économique afin d’intégrer la contrainte CAPEX.

    ### Pondérations normalisées utilisées
    
    - Âge: {normalized_age:.2f}
    - Urgence EVS: {normalized_evs:.2f}
    - Statut EVS: {normalized_status:.2f}
    - Roadmap / travaux: {normalized_roadmap:.2f}
    - Pénalité coût: {w_cost:.2f}

    **Limite importante:** ce score constitue une aide à la décision. Il doit être validé par l’expertise métier Renault avant tout usage opérationnel.
    """)


# ============================================================
# KPI AND STATUS
# ============================================================

total_assets = len(clean_df)
avg_priority = round(clean_df["priority_score"].mean(), 2)
urgent_assets = len(clean_df[clean_df["priority_score"] >= 0.75])
total_budget_estimate = int(clean_df["Montant EVS"].sum())
critical_budget = int(clean_df[clean_df["priority_score"] >= 0.75]["Montant EVS"].sum())

st.markdown("## État du système")

status_col1, status_col2, status_col3, status_col4 = st.columns(4)
status_col1.metric("Source des données", data_source)
status_col2.metric("Dernière mise à jour", datetime.now().strftime("%d/%m/%Y %H:%M"))
status_col3.metric("Équipements chargés", total_assets)
status_col4.metric("Alertes critiques", urgent_assets)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Équipements analysés", total_assets)
col2.metric("Score moyen", avg_priority)
col3.metric("EVS critiques", urgent_assets)
col4.metric("Budget critique estimé", f"{critical_budget:,.0f} €")

st.metric("Budget total estimé", f"{total_budget_estimate:,.0f} €")


# ============================================================
# SITE ANALYSIS
# ============================================================

site_summary = clean_df.groupby("Site").agg(
    nombre_equipements=("Pont", "count"),
    age_moyen=("Age", "mean"),
    score_moyen=("priority_score", "mean"),
    budget_total=("Montant EVS", "sum"),
).reset_index()

site_summary["age_moyen"] = site_summary["age_moyen"].round(1)
site_summary["score_moyen"] = site_summary["score_moyen"].round(2)
site_summary["budget_total"] = site_summary["budget_total"].astype(int)

site_ranking = clean_df.groupby("Site").agg(
    score_moyen=("priority_score", "mean"),
    age_moyen=("Age", "mean"),
    budget_total=("Montant EVS", "sum"),
).reset_index()

site_ranking["criticite"] = (
    0.7 * site_ranking["score_moyen"] 
    + 0.3 * normalize(site_ranking["age_moyen"])
).round(2)

site_ranking["score_moyen"] = site_ranking["score_moyen"].round(2)
site_ranking["age_moyen"] = site_ranking["age_moyen"].round(1)
site_ranking["budget_total"] = site_ranking["budget_total"].astype(int)

top_site = site_ranking.sort_values(by="criticite", ascending=False).iloc[0]["Site"]


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

st.markdown("## Synthèse décisionnelle")

st.warning(f"""
**Insight principal:** le site **{top_site}** présente le niveau de criticité moyen le plus élevé.

- **{urgent_assets}** équipements dépassent le seuil critique de priorité EVS.
- Le budget total estimé du périmètre analysé est de **{total_budget_estimate:,.0f} €**.
- Le budget nécessaire pour couvrir uniquement les équipements critiques est estimé à **{critical_budget:,.0f} €**.

**Décision recommandée:** concentrer l’analyse technique sur les équipements critiques et arbitrer le budget CAPEX à partir des sites les plus exposés.
""")


# ============================================================
# ALERT PANEL
# ============================================================

st.markdown("## Alertes critiques")

critical_assets = clean_df[
    (clean_df["priority_score"] >= 0.80) 
    | (clean_df["roadmap_risk"] >= 1.0)
].sort_values(by="priority_score", ascending=False)

display_cols = [
    "Pays",
    "Site",
    "Pont",
    "Age",
    "EVS Année",
    "Montant EVS",
    "Usage",
    "Type",
    "status_risk",
    "roadmap_risk",
    "priority_score",
    "Décision règle EVS",
    "Décision score",
    "Plan d’action",
    "Délai recommandé",
]

if len(critical_assets) > 0:
    st.error(f"{len(critical_assets)} équipements critiques nécessitent une analyse prioritaire.")
    st.dataframe(critical_assets[display_cols].head(20), use_container_width=True)
else:
    st.success("Aucune situation critique détectée avec les paramètres actuels.")


# ============================================================
# MAIN TABLES
# ============================================================

st.subheader("Top équipements prioritaires")
top_assets = clean_df.sort_values(by="priority_score", ascending=False).head(20)
st.dataframe(top_assets[display_cols], use_container_width=True)

st.subheader("Tableau de bord multi-sites")
st.dataframe(site_summary.sort_values(by="score_moyen", ascending=False), use_container_width=True)

st.subheader("Classement stratégique des sites critiques")
st.dataframe(site_ranking.sort_values(by="criticite", ascending=False), use_container_width=True)

st.subheader("Impact du report EVS")
st.info("Cette simulation estime l’évolution du score si l’intervention EVS est repoussée d’un ou deux ans.")

delay_cols = [
    "Site",
    "Pont",
    "Age",
    "priority_score",
    "Risque report 1 an",
    "Risque report 2 ans",
    "Plan d’action",
]

st.dataframe(
    clean_df.sort_values(by="Risque report 2 ans", ascending=False)[delay_cols].head(20),
    use_container_width=True,
)


# ============================================================
# ROADMAP
# ============================================================

st.subheader("Roadmap stratégique EVS")

timeline_df = clean_df.copy()
timeline_df["Année action"] = timeline_df["EVS Année"]

timeline_summary = timeline_df.groupby("Année action").agg(
    nb_equipements=("Pont", "count"),
    budget_total=("Montant EVS", "sum"),
    score_moyen=("priority_score", "mean"),
).reset_index()

timeline_summary["Année action"] = timeline_summary["Année action"].astype(int)
timeline_summary["score_moyen"] = timeline_summary["score_moyen"].round(2)
timeline_summary["budget_total"] = timeline_summary["budget_total"].astype(int)

st.dataframe(timeline_summary.sort_values(by="Année action"), use_container_width=True)

st.subheader("Projection budgétaire EVS par année")
st.line_chart(
    timeline_summary.sort_values(by="Année action").set_index("Année action")["budget_total"]
)

st.subheader("Projection du score moyen par année")
st.line_chart(
    timeline_summary.sort_values(by="Année action").set_index("Année action")["score_moyen"]
)


# ============================================================
# HEATMAP
# ============================================================

st.subheader("Heatmap EVS: site vs année")

heatmap_df = clean_df.groupby(["Site", "EVS Année"]).agg(
    score_moyen=("priority_score", "mean")
).reset_index()

heatmap_pivot = heatmap_df.pivot(
    index="Site", 
    columns="EVS Année", 
    values="score_moyen",
).fillna(0)

fig, ax = plt.subplots(figsize=(14, 6))
cax = ax.imshow(heatmap_pivot, aspect="auto")

ax.set_xticks(range(len(heatmap_pivot.columns)))
ax.set_yticks(range(len(heatmap_pivot.index)))

ax.set_xticklabels(heatmap_pivot.columns.astype(int), rotation=45)
ax.set_yticklabels(heatmap_pivot.index)

ax.set_xlabel("Année EVS")
ax.set_ylabel("Site")
ax.set_title("Intensité moyenne du score EVS par site et par année")

fig.colorbar(cax, ax=ax, label="Score moyen EVS")
st.pyplot(fig)

st.info("Les zones les plus claires indiquent une concentration plus élevée de criticité EVS pour un site et une année donnés.")


# ============================================================
# BUDGET SIMULATION
# ============================================================

st.markdown("---")
st.subheader("Moteur de simulation budgétaire EVS")

with st.expander("Logique de sélection budgétaire"):
    st.markdown("""
    La sélection des équipements est réalisée selon une approche gloutonne. 
    
    Les équipements sont triés par score de criticité décroissant, puis ajoutés progressivement tant que le budget disponible le permet. 
    
    Cette méthode est simple, lisible et adaptée à un outil d’aide à la décision. Elle ne garantit pas une optimisation mathématique parfaite, mais elle permet de représenter une logique de priorisation industrielle.
    """)

budget = st.slider(
    "Budget disponible (€)",
    100000,
    2000000,
    500000,
    step=50000,
)

sorted_df = clean_df.sort_values(by="priority_score", ascending=False)

selected_df, total_cost = build_budget_selection(sorted_df, budget)

treated_assets = len(selected_df)
treated_ratio = round((treated_assets / total_assets) * 100, 1) if total_assets > 0 else 0
residual_assets = total_assets - treated_assets

st.write(f"Budget utilisé: {int(total_cost):,} € / {budget:,} €")
st.write(f"Équipements sélectionnés: {treated_assets} sur {total_assets} ({treated_ratio} %)")
st.write(f"Équipements non couverts par le scénario budgétaire: {residual_assets}")

if len(selected_df) > 0:
    st.dataframe(selected_df[display_cols], use_container_width=True)

    st.markdown("---")
    st.subheader("Comparaison rapide de scénarios budgétaires")

    scenario_budgets = [500000, 1000000, 1500000]
    scenario_results = []

    for scenario_budget in scenario_budgets:
        scenario_selected_df, scenario_cost = build_budget_selection(sorted_df, scenario_budget)
        scenario_count = len(scenario_selected_df)
        
        scenario_results.append({
            "Budget scénario": scenario_budget,
            "Budget utilisé": int(scenario_cost),
            "Équipements couverts": scenario_count,
            "Couverture (%)": round((scenario_count / total_assets) * 100, 1),
        })

    st.dataframe(pd.DataFrame(scenario_results), use_container_width=True)

else:
    st.warning("Aucun équipement sélectionné avec ce budget.")


# ============================================================
# EXPORT CSV
# ============================================================

st.markdown("---")
st.subheader("Exporter les données enrichies")

csv = clean_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "Télécharger les données analysées (CSV)",
    data=csv,
    file_name="evs_analysis.csv",
    mime="text/csv",
)


# ============================================================
# PDF
# ============================================================

st.markdown("---")
st.subheader("Télécharger rapport PDF")


def generate_pdf_report():
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Rapport EVS", ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, "Auteur: Hassan Attout", ln=True)
    pdf.cell(0, 8, "Master MEE Energetique, Sorbonne Universite", ln=True)
    pdf.cell(0, 8, "Renault Group, moyens de levage", ln=True)
    pdf.cell(0, 8, "Copyright 2026 Hassan Attout", ln=True)
    
    pdf.ln(4)
    
    pdf.cell(0, 8, f"Source donnees: {data_source}", ln=True)
    pdf.cell(0, 8, f"Nombre equipements analyses: {total_assets}", ln=True)
    pdf.cell(0, 8, f"Budget total estime: {total_budget_estimate} EUR", ln=True)
    
    pdf.ln(4)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Synthese decisionnelle", ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(
        0, 
        5, 
        clean_text(
            f"Le site le plus critique est {top_site}. "
            f"{urgent_assets} equipements depassent le seuil critique EVS. "
            f"Le budget total estime est de {total_budget_estimate} EUR."
        ),
    )
    
    pdf.ln(4)
    
    top5 = clean_df.sort_values(by="priority_score", ascending=False).head(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Top 5 equipements prioritaires", ln=True)
    
    pdf.set_font("Arial", "", 10)
    for _, row in top5.iterrows():
        pdf.cell(
            0, 
            6, 
            clean_text(f"{row['Site']} - {row['Pont']} (score {row['priority_score']})"), 
            ln=True,
        )
        
    pdf.ln(4)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Sites les plus critiques", ln=True)
    
    top_sites = site_ranking.sort_values(by="criticite", ascending=False).head(5)
    
    pdf.set_font("Arial", "", 10)
    for _, row in top_sites.iterrows():
        pdf.cell(
            0, 
            6, 
            clean_text(f"{row['Site']} (criticite {row['criticite']})"), 
            ln=True,
        )
    
    pdf.ln(4)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(
        0, 
        4, 
        clean_text(
            "Ce rapport est genere automatiquement par EVS Intelligence Platform. "
            "Il constitue une aide a la decision et ne remplace pas une expertise technique ou reglementaire."
        ),
    )
    
    return bytes(pdf.output(dest="S"))


pdf_bytes = generate_pdf_report()

st.download_button(
    "Télécharger PDF",
    data=pdf_bytes,
    file_name="rapport_evs.pdf",
    mime="application/pdf",
)


# ============================================================
# DEBUG
# ============================================================

with st.expander("Données internes du modèle"):
    st.dataframe(clean_df, use_container_width=True)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption("© 2026 Hassan Attout, EVS Intelligence Platform, Projet M2")
