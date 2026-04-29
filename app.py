from pathlib import Path
from fpdf import FPDF

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


# =========================
# CONFIG
# =========================

st.set_page_config(
    page_title="EVS Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
)

DATA_PATH = Path(__file__).parent.parent / "data" / "evs_data.csv"


# =========================
# HELPERS
# =========================

def normalize(series):
    series = pd.to_numeric(series, errors="coerce").fillna(0)
    if series.max() == series.min():
        return series * 0
    return (series - series.min()) / (series.max() - series.min())


def find_column(df, candidates):
    cleaned_cols = {
        str(col).strip().lower().replace("\n", " "): col
        for col in df.columns
    }

    for candidate in candidates:
        candidate = candidate.lower().replace("\n", " ")
        for cleaned, original in cleaned_cols.items():
            if candidate in cleaned:
                return original
    return None


def clean_text(text):
    return str(text).encode("latin-1", "ignore").decode("latin-1")


def parse_evs_status(value):
    value = str(value).strip().lower()

    if value in ["o", "oui", "yes", "y", "1"]:
        return 1.0
    if value in ["n", "non", "no", "0"]:
        return 0.3
    return 0.6


def is_not_empty(value):
    return str(value).strip().lower() not in ["", "nan", "none", "nat"]


def evs_rule(age):
    if age >= 40:
        return "EVS obligatoire"
    if age >= 35:
        return "EVS à programmer"
    if age >= 30:
        return "Première estimation (budgétaire/opérationnelle)"
    return "Suivi standard (sauf cas particulier)"


def decision(score):
    if score >= 0.60:
        return "Priorité élevée"
    if score >= 0.45:
        return "À planifier"
    if score >= 0.30:
        return "Surveillance renforcée"
    return "Suivi standard"


def action_plan(score):
    if score >= 0.60:
        return "EVS prioritaire + analyse technique"
    if score >= 0.45:
        return "EVS à planifier court terme"
    if score >= 0.30:
        return "Surveillance + maintenance préventive"
    return "Suivi standard"


def deadline(score):
    if score >= 0.60:
        return "0-6 mois"
    if score >= 0.45:
        return "6-12 mois"
    if score >= 0.30:
        return "12-24 mois"
    return "Routine"


def build_budget_selection(sorted_df, budget):
    selected = []
    total = 0

    for _, row in sorted_df.iterrows():
        cost = row["Montant EVS"] if pd.notna(row["Montant EVS"]) else 0

        if total + cost <= budget:
            selected.append(row)
            total += cost

    return pd.DataFrame(selected), total


def generate_pdf(top_site, total_assets, avg_score, avg_age, total_budget, critical_budget, top5):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Rapport EVS Intelligence Platform", ln=True)

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, "Auteur: Hassan Attout", ln=True)
    pdf.cell(0, 8, "Master MEE Energetique, Sorbonne Universite", ln=True)
    pdf.cell(0, 8, "Renault Group, moyens de levage", ln=True)

    pdf.ln(5)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Synthese executive", ln=True)

    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(
        0,
        5,
        clean_text(
            f"Le perimetre analyse contient {total_assets} ponts roulants. "
            f"Le score EVS moyen est de {avg_score:.3f}/1.0 et l'age moyen du parc est de {avg_age:.1f} ans. "
            f"Le site le plus critique est {top_site}. "
            f"Le budget total estime est de {total_budget:,.0f} EUR. "
            f"Le budget critique estime est de {critical_budget:,.0f} EUR."
        ),
    )

    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Top 5 equipements critiques", ln=True)

    pdf.set_font("Arial", "", 10)
    for _, row in top5.iterrows():
        pdf.cell(
            0,
            6,
            clean_text(
                f"{row['Site']} - {row['Pont']} | Age: {row['Age']} | Score: {row['priority_score']}"
            ),
            ln=True,
        )

    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(
        0,
        4,
        clean_text(
            "Ce rapport est genere automatiquement. "
            "Le score EVS est une aide a la decision et doit etre valide par l'expertise metier Renault."
        ),
    )

    return bytes(pdf.output(dest="S"))


# =========================
# LOAD DATA
# =========================

if not DATA_PATH.exists():
    st.error("Fichier data/evs_data.csv introuvable.")
    st.stop()

raw_df = pd.read_csv(DATA_PATH)
raw_df.columns = raw_df.columns.astype(str).str.strip()
raw_df = raw_df.dropna(how="all")

site_col = find_column(raw_df, ["site"])
pont_col = find_column(raw_df, ["pont"])
age_col = find_column(raw_df, ["age"])
evs_year_col = find_column(raw_df, ["evs année", "evs annee"])
evs_status_col = find_column(raw_df, ["evaluation spéciale", "evaluation speciale", "statut evs"])
cost_col = find_column(raw_df, ["e/s montant", "evs montant", "montant"])
country_col = find_column(raw_df, ["pays"])
usage_col = find_column(raw_df, ["usage"])
type_col = find_column(raw_df, ["type"])
roadmap_obs_col = find_column(raw_df, ["obsolescence"])
roadmap_sec_col = find_column(raw_df, ["sécurisation", "securisation"])
comments_col = find_column(raw_df, ["commentaires", "travaux"])

required_cols = [site_col, pont_col, age_col, evs_year_col]

if any(col is None for col in required_cols):
    st.error("Colonnes obligatoires manquantes: Site, Pont, Age, EVS Année.")
    st.write(list(raw_df.columns))
    st.stop()

raw_df = raw_df[raw_df[pont_col].notna()]

df = pd.DataFrame()
df["Pays"] = raw_df[country_col] if country_col else "Non renseigné"
df["Site"] = raw_df[site_col]
df["Pont"] = raw_df[pont_col]
df["Age"] = pd.to_numeric(raw_df[age_col], errors="coerce")
df["EVS Année"] = pd.to_numeric(raw_df[evs_year_col], errors="coerce")
df["Statut EVS"] = raw_df[evs_status_col] if evs_status_col else "NC"
df["Montant EVS"] = pd.to_numeric(raw_df[cost_col], errors="coerce") if cost_col else 0
df["Usage"] = raw_df[usage_col] if usage_col else ""
df["Type"] = raw_df[type_col] if type_col else ""
df["Roadmap obsolescence"] = raw_df[roadmap_obs_col] if roadmap_obs_col else ""
df["Roadmap sécurisation"] = raw_df[roadmap_sec_col] if roadmap_sec_col else ""
df["Commentaires"] = raw_df[comments_col] if comments_col else ""

df = df.dropna(subset=["Age", "EVS Année"])
df["Age"] = df["Age"].fillna(0).astype(int)
df["EVS Année"] = df["EVS Année"].fillna(0).astype(int)
df["Montant EVS"] = df["Montant EVS"].fillna(0).astype(int)

for col in df.columns:
    if df[col].dtype == "object":
        df[col] = df[col].fillna("").astype(str).str.strip()


# =========================
# SCORING
# =========================

df["age_score"] = normalize(df["Age"])
df["evs_urgency"] = 1 - normalize(df["EVS Année"])
df["status_score"] = df["Statut EVS"].apply(parse_evs_status)
df["cost_score"] = normalize(df["Montant EVS"])

df["roadmap_score"] = df.apply(
    lambda row: 1.0
    if is_not_empty(row["Roadmap sécurisation"])
    else 0.7
    if is_not_empty(row["Roadmap obsolescence"])
    else 0.5
    if is_not_empty(row["Commentaires"])
    else 0.0,
    axis=1,
)

df["priority_score"] = (
    0.30 * df["age_score"]
    + 0.30 * df["evs_urgency"]
    + 0.20 * df["status_score"]
    + 0.20 * df["roadmap_score"]
    - 0.10 * df["cost_score"]
).clip(lower=0, upper=1).round(3)

df["Décision règle EVS"] = df["Age"].apply(evs_rule)
df["Décision"] = df["priority_score"].apply(decision)
df["Plan d’action"] = df["priority_score"].apply(action_plan)
df["Délai recommandé"] = df["priority_score"].apply(deadline)


# =========================
# CALCULATED INSIGHTS
# =========================

total_assets = len(df)
country_count = df["Pays"].nunique()
site_count = df["Site"].nunique()
avg_score = df["priority_score"].mean()
avg_age = df["Age"].mean()

evs_required = df[df["Statut EVS"].str.upper().str.strip() == "O"]
evs_required_count = len(evs_required)

evs_late = evs_required[evs_required["EVS Année"] <= 2024]
evs_late_count = len(evs_late)

urgent_evs = df[df["EVS Année"] <= 2026]
urgent_evs_count = len(urgent_evs)
critical_budget = int(urgent_evs["Montant EVS"].sum())

timeline = df[
    (df["EVS Année"] >= 2025)
    & (df["EVS Année"] <= 2030)
].groupby("EVS Année").agg(
    nb_equipements=("Pont", "count"),
    budget_total=("Montant EVS", "sum"),
    score_moyen=("priority_score", "mean"),
).reset_index()

timeline["score_moyen"] = timeline["score_moyen"].round(3)
timeline["budget_total"] = timeline["budget_total"].astype(int)

total_budget = int(timeline["budget_total"].sum())
peak_year = int(timeline.sort_values("budget_total", ascending=False).iloc[0]["EVS Année"])
peak_budget = int(timeline.sort_values("budget_total", ascending=False).iloc[0]["budget_total"])

site_ranking = df.groupby("Site").agg(
    nb_equipements=("Pont", "count"),
    age_moyen=("Age", "mean"),
    score_moyen=("priority_score", "mean"),
    budget_total=("Montant EVS", "sum"),
).reset_index()

site_ranking["criticite_site"] = (
    0.70 * site_ranking["score_moyen"]
    + 0.30 * normalize(site_ranking["age_moyen"])
).round(3)

site_ranking["age_moyen"] = site_ranking["age_moyen"].round(1)
site_ranking["score_moyen"] = site_ranking["score_moyen"].round(3)
site_ranking["budget_total"] = site_ranking["budget_total"].astype(int)

top_site = site_ranking.sort_values("criticite_site", ascending=False).iloc[0]["Site"]

top5 = df.sort_values("priority_score", ascending=False).head(5)


# =========================
# PAGE
# =========================

st.title("Pilotage EVS CAPEX")
st.caption("Priorisation des ponts roulants, arbitrage budgétaire et vision 2025-2030")

st.success("Base EVS chargée automatiquement depuis l’application.")

st.markdown("## 🏗️ État du système")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Équipements analysés", total_assets)
kpi2.metric("Pays / sites", f"{country_count} / {site_count}")
kpi3.metric("Score moyen EVS", f"{avg_score:.3f} / 1.0")
kpi4.metric("Âge moyen du parc", f"{avg_age:.0f} ans")

st.markdown(
    f"""
    Le périmètre analysé couvre **{total_assets} ponts roulants** répartis sur **{country_count} pays** et environ **{site_count} sites**.  
    Le score moyen EVS est de **{avg_score:.3f}/1.0**, avec un âge moyen d’environ **{avg_age:.0f} ans**.
    """
)

st.markdown("## 🚨 Synthèse décisionnelle")

a, b, c = st.columns(3)

a.metric("EVS obligatoires", evs_required_count)
b.metric("EVS dépassées", evs_late_count)
c.metric("Budget urgent ≤ 2026", f"{critical_budget:,.0f} €")

st.warning(
    f"""
    **Insight principal:** le pic budgétaire se situe en **{peak_year}** avec environ **{peak_budget:,.0f} €**.  
    Le site le plus critique selon le score moyen et l’âge du parc est **{top_site}**.  
    La priorité est de traiter les équipements EVS obligatoires, puis les équipements avec échéance EVS inférieure ou égale à 2026.
    """
)

st.markdown("## 📊 Répartition par pays")

country_dist = df["Pays"].value_counts().reset_index()
country_dist.columns = ["Pays", "Nombre d’équipements"]

left, right = st.columns([1, 2])

with left:
    st.dataframe(country_dist, use_container_width=True, hide_index=True)

with right:
    st.bar_chart(country_dist.set_index("Pays"))

st.markdown("## 🏆 Top 5 équipements critiques")

top5_display = top5[[
    "Site",
    "Pont",
    "Age",
    "EVS Année",
    "Statut EVS",
    "Montant EVS",
    "priority_score",
    "Décision",
    "Plan d’action",
]]

st.dataframe(top5_display, use_container_width=True, hide_index=True)

st.markdown("## 💶 Projection budgétaire 2025-2030")

budget_col1, budget_col2, budget_col3 = st.columns(3)

budget_col1.metric("Budget total 2025-2030", f"{total_budget:,.0f} €")
budget_col2.metric("Pic budgétaire", str(peak_year))
budget_col3.metric("Montant du pic", f"{peak_budget:,.0f} €")

chart_df = timeline.set_index("EVS Année")[["budget_total"]]
st.line_chart(chart_df)

with st.expander("Voir le détail budgétaire par année"):
    st.dataframe(timeline, use_container_width=True, hide_index=True)

st.markdown("## 🔥 Heatmap EVS: site vs année")

heatmap_df = df.groupby(["Site", "EVS Année"]).agg(
    score_moyen=("priority_score", "mean")
).reset_index()

heatmap_pivot = heatmap_df.pivot(
    index="Site",
    columns="EVS Année",
    values="score_moyen",
).fillna(0)

fig, ax = plt.subplots(figsize=(14, 6))
image = ax.imshow(heatmap_pivot, aspect="auto")

ax.set_xticks(range(len(heatmap_pivot.columns)))
ax.set_yticks(range(len(heatmap_pivot.index)))
ax.set_xticklabels(heatmap_pivot.columns.astype(int), rotation=45)
ax.set_yticklabels(heatmap_pivot.index)

ax.set_xlabel("Année EVS")
ax.set_ylabel("Site")
ax.set_title("Intensité moyenne du score EVS par site et par année")

fig.colorbar(image, ax=ax, label="Score EVS moyen")
st.pyplot(fig)

st.markdown("## 🎯 Simulation budgétaire")

budget = st.slider(
    "Budget disponible (€)",
    min_value=100000,
    max_value=2000000,
    value=500000,
    step=50000,
)

selected_df, used_budget = build_budget_selection(
    df.sort_values("priority_score", ascending=False),
    budget,
)

coverage = round((len(selected_df) / total_assets) * 100, 1)

sim1, sim2, sim3 = st.columns(3)
sim1.metric("Budget utilisé", f"{used_budget:,.0f} €")
sim2.metric("Équipements couverts", len(selected_df))
sim3.metric("Couverture du parc", f"{coverage} %")

if len(selected_df) > 0:
    st.dataframe(
        selected_df[[
            "Site",
            "Pont",
            "Age",
            "EVS Année",
            "Montant EVS",
            "priority_score",
            "Décision",
            "Délai recommandé",
        ]],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Aucun équipement sélectionné avec ce budget.")

st.markdown("## 📥 Export")

csv = df.to_csv(index=False).encode("utf-8")

col_csv, col_pdf = st.columns(2)

with col_csv:
    st.download_button(
        "Télécharger les données analysées (CSV)",
        data=csv,
        file_name="evs_analysis.csv",
        mime="text/csv",
    )

with col_pdf:
    pdf_bytes = generate_pdf(
        top_site=top_site,
        total_assets=total_assets,
        avg_score=avg_score,
        avg_age=avg_age,
        total_budget=total_budget,
        critical_budget=critical_budget,
        top5=top5,
    )

    st.download_button(
        "Télécharger le rapport PDF",
        data=pdf_bytes,
        file_name="rapport_evs.pdf",
        mime="application/pdf",
    )

with st.expander("Méthodologie du score EVS"):
    st.markdown("""
    Le score EVS est un score multicritère normalisé développé comme outil d’aide à la décision dans le cadre du mémoire.

    **Formule utilisée:**

    `Score EVS = 0.30 × âge + 0.30 × urgence EVS + 0.20 × statut EVS + 0.20 × roadmap/travaux - 0.10 × coût`

    **Interprétation:**
    - l’âge représente le vieillissement mécanique,
    - l’urgence EVS représente la proximité de l’échéance,
    - le statut EVS traduit la situation déclarée,
    - la roadmap/travaux ajoute le contexte d’obsolescence ou de sécurisation,
    - le coût agit comme contrainte CAPEX.

    Ce score ne remplace pas l’expertise métier. Il sert à structurer la priorisation.
    """)

st.caption(
    "⚠️ Outil d’aide à la décision issu du mémoire. Validation métier Renault requise avant tout usage opérationnel."
)
