from fpdf import FPDF
from pathlib import Path
import sys
import os

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="EVS Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# =========================
# HEADER
# =========================

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
- charger automatiquement une base EVS intégrée à l’application,
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
    - Les données sont chargées automatiquement depuis une base CSV intégrée à l’application.
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


# =========================
# FUNCTIONS
# =========================

def normalize(series):
    series = pd.to_numeric(series, errors="coerce").fillna(0)
    if series.max() == series.min():
        return series * 0
    return (series - series.min()) / (series.max() - series.min())


def clean_text(text):
    return str(text).encode("latin-1", "ignore").decode("latin-1")


def find_column(df, candidates):
    cleaned_cols = {
        str(col).strip().lower().replace("\n", " "): col
        for col in df.columns
    }

    for candidate in candidates:
        candidate_clean = candidate.lower().replace("\n", " ")
        for cleaned, original in cleaned_cols.items():
            if candidate_clean in cleaned:
                return original
    return None


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


def is_not_empty(value):
    return str(value).strip().lower() not in ["", "nan", "none", "nat"]


def apply_evs_rules(row):
    age = row["Age"]

    if age >= 40:
        return "EVS obligatoire"
    elif age >= 35:
        return "EVS à programmer"
    elif age >= 30:
        return "Première estimation (budgétaire/opérationnelle)"
    else:
        return "Suivi standard (sauf cas particulier)"


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


# =========================
# DATA LOADING
# =========================

data_path = Path(__file__).parent.parent / "data" / "evs_data.csv"

if not data_path.exists():
    st.error("Fichier data/evs_data.csv introuvable.")
    st.stop()

df = pd.read_csv(data_path)

st.success("Base EVS chargée automatiquement depuis l’application.")

df.columns = df.columns.astype(str).str.strip()
df = df.dropna(how="all")

site_col = find_column(df, ["site"])
pont_col = find_column(df, ["pont"])
age_col = find_column(df, ["age"])
evs_flag_col = find_column(df, ["evaluation spéciale", "evaluation speciale", "statut evs"])
evs_year_col = find_column(df, ["evs année", "evs annee"])
cost_col = find_column(df, ["e/s montant", "evs montant", "montant"])
country_col = find_column(df, ["pays"])
usage_col = find_column(df, ["usage"])
type_col = find_column(df, ["type"])
roadmap_obs_col = find_column(df, ["obsolescence"])
roadmap_sec_col = find_column(df, ["securisation", "sécurisation"])
comments_col = find_column(df, ["commentaires", "travaux"])

required_cols = [site_col, pont_col, age_col, evs_year_col]

if any(col is None for col in required_cols):
    st.error("La base ne contient pas toutes les colonnes nécessaires: Site, Pont, Age, EVS Année.")
    st.write("Colonnes détectées:")
    st.write(list(df.columns))
    st.stop()

df = df[df[pont_col].notna()]

clean_df = pd.DataFrame()
clean_df["Site"] = df[site_col]
clean_df["Pont"] = df[pont_col]
clean_df["Age"] = pd.to_numeric(df[age_col], errors="coerce")
clean_df["EVS Année"] = pd.to_numeric(df[evs_year_col], errors="coerce")

clean_df["Pays"] = df[country_col] if country_col is not None else "Non renseigné"
clean_df["Statut EVS"] = df[evs_flag_col] if evs_flag_col is not None else "NC"
clean_df["Montant EVS"] = pd.to_numeric(df[cost_col], errors="coerce") if cost_col is not None else 0
clean_df["Usage"] = df[usage_col] if usage_col is not None else "Non renseigné"
clean_df["Type"] = df[type_col] if type_col is not None else "Non renseigné"
clean_df["Roadmap obsolescence"] = df[roadmap_obs_col] if roadmap_obs_col is not None else ""
clean_df["Roadmap sécurisation"] = df[roadmap_sec_col] if roadmap_sec_col is not None else ""
clean_df["Commentaires"] = df[comments_col] if comments_col is not None else ""

clean_df = clean_df.dropna(subset=["Age", "EVS Année"])
clean_df["Age"] = clean_df["Age"].fillna(0).astype(int)
clean_df["EVS Année"] = clean_df["EVS Année"].fillna(0).astype(int)
clean_df["Montant EVS"] = clean_df["Montant EVS"].fillna(0).astype(int)

for col in clean_df.columns:
    if clean_df[col].dtype == "object":
        clean_df[col] = clean_df[col].fillna("").astype(str).str.strip()


# =========================
# SCORING
# =========================

clean_df["age_score"] = normalize(clean_df["Age"])
clean_df["evs_urgency"] = 1 - normalize(clean_df["EVS Année"])
clean_df["status_risk"] = clean_df["Statut EVS"].apply(parse_evs_flag)
clean_df["cost_score"] = normalize(clean_df["Montant EVS"])

clean_df["roadmap_risk"] = clean_df.apply(
    lambda row: 1.0
    if is_not_empty(row["Roadmap sécurisation"])
    else 0.7
    if is_not_empty(row["Roadmap obsolescence"])
    else 0.5
    if is_not_empty(row["Commentaires"])
    else 0.0,
    axis=1
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


# =========================
# METHODOLOGY
# =========================

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


# =========================
# KPI
# =========================

total_assets = len(clean_df)
avg_priority = round(clean_df["priority_score"].mean(), 2)
urgent_assets = len(clean_df[clean_df["priority_score"] >= 0.75])
total_budget_estimate = int(clean_df["Montant EVS"].sum())
critical_budget = int(clean_df[clean_df["priority_score"] >= 0.75]["Montant EVS"].sum())

st.markdown("## État du système")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Équipements analysés", total_assets)
col2.metric("Score moyen", avg_priority)
col3.metric("EVS critiques", urgent_assets)
col4.metric("Budget critique estimé", f"{critical_budget:,.0f} €")

st.metric("Budget total estimé", f"{total_budget_estimate:,.0f} €")


# =========================
# SITE ANALYSIS
# =========================

site_summary = clean_df.groupby("Site").agg(
    nombre_equipements=("Pont", "count"),
    age_moyen=("Age", "mean"),
    score_moyen=("priority_score", "mean"),
    budget_total=("Montant EVS", "sum")
).reset_index()

site_summary["age_moyen"] = site_summary["age_moyen"].round(1)
site_summary["score_moyen"] = site_summary["score_moyen"].round(2)
site_summary["budget_total"] = site_summary["budget_total"].astype(int)

site_ranking = clean_df.groupby("Site").agg(
    score_moyen=("priority_score", "mean"),
    age_moyen=("Age", "mean"),
    budget_total=("Montant EVS", "sum")
).reset_index()

site_ranking["criticite"] = (
    0.7 * site_ranking["score_moyen"]
    + 0.3 * normalize(site_ranking["age_moyen"])
).round(2)

site_ranking["score_moyen"] = site_ranking["score_moyen"].round(2)
site_ranking["age_moyen"] = site_ranking["age_moyen"].round(1)
site_ranking["budget_total"] = site_ranking["budget_total"].astype(int)

top_site = site_ranking.sort_values(by="criticite", ascending=False).iloc[0]["Site"]


# =========================
# EXECUTIVE SUMMARY
# =========================

st.markdown("## Synthèse décisionnelle")

st.warning(f"""
**Insight principal:** le site **{top_site}** présente le niveau de criticité moyen le plus élevé.

- **{urgent_assets}** équipements dépassent le seuil critique de priorité EVS.
- Le budget total estimé du périmètre analysé est de **{total_budget_estimate:,.0f} €**.
- Le budget nécessaire pour couvrir uniquement les équipements critiques est estimé à **{critical_budget:,.0f} €**.

**Décision recommandée:** concentrer l’analyse technique sur les équipements critiques et arbitrer le budget CAPEX à partir des sites les plus exposés.
""")


# =========================
# ALERT PANEL
# =========================

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


# =========================
# MAIN TABLES
# =========================

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
    use_container_width=True
)


# =========================
# ROADMAP
# =========================

st.subheader("Roadmap stratégique EVS")

timeline_df = clean_df.copy()
timeline_df["Année action"] = timeline_df["EVS Année"]

timeline_summary = timeline_df.groupby("Année action").agg(
    nb_equipements=("Pont", "count"),
    budget_total=("Montant EVS", "sum"),
    score_moyen=("priority_score", "mean")
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


# =========================
# HEATMAP
# =========================

st.subheader("Heatmap EVS: site vs année")

heatmap_df = clean_df.groupby(["Site", "EVS Année"]).agg(
    score_moyen=("priority_score", "mean")
).reset_index()

heatmap_pivot = heatmap_df.pivot(
    index="Site",
    columns="EVS Année",
    values="score_moyen"
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


# =========================
# BUDGET SIMULATION
# =========================

st.markdown("---")
st.subheader("Moteur de simulation budgétaire EVS")

budget = st.slider(
    "Budget disponible (€)",
    100000,
    2000000,
    500000,
    step=50000
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
            "Couverture (%)": round((scenario_count / total_assets) * 100, 1)
        })

    st.dataframe(pd.DataFrame(scenario_results), use_container_width=True)

else:
    st.warning("Aucun équipement sélectionné avec ce budget.")


# =========================
# EXPORT CSV
# =========================

st.markdown("---")
st.subheader("Exporter les données enrichies")

csv = clean_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "Télécharger les données analysées (CSV)",
    data=csv,
    file_name="evs_analysis.csv",
    mime="text/csv",
)


# =========================
# PDF
# =========================

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
        )
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
            ln=True
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
            ln=True
        )

    pdf.ln(4)

    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(
        0,
        4,
        clean_text(
            "Ce rapport est genere automatiquement par EVS Intelligence Platform. "
            "Il constitue une aide a la decision et ne remplace pas une expertise technique ou reglementaire."
        )
    )

    return bytes(pdf.output(dest="S"))


pdf_bytes = generate_pdf_report()

st.download_button(
    "Télécharger PDF",
    data=pdf_bytes,
    file_name="rapport_evs.pdf",
    mime="application/pdf"
)


# =========================
# DEBUG
# =========================

with st.expander("Données internes du modèle"):
    st.dataframe(clean_df, use_container_width=True)


# =========================
# FOOTER
# =========================

st.markdown("---")
st.caption("© 2026 Hassan Attout, EVS Intelligence Platform, Projet M2")
