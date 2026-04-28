from fpdf import FPDF
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
Cet outil fournit un support structuré pour orienter les décisions techniques et budgétaires sans dépendre d'importations manuelles.
""")

# =========================
# DATA SOURCE (HARDCODED)
# =========================
# Remplacement de l'upload par des données spécifiques
data = {
    "Site": ["Douai", "Douai", "Flins", "Maubeuge", "Sandouville", "Cleon", "Cleon"],
    "Pont": ["PONT-01", "PONT-02", "PONT-A5", "PONT-M1", "PONT-S2", "PONT-C1", "PONT-C2"],
    "Age": [42, 12, 38, 22, 36, 45, 10],
    "EVS Année": [2024, 2030, 2025, 2028, 2025, 2024, 2032],
    "Montant EVS": [15000, 5000, 12000, 8000, 14000, 20000, 4500],
    "Statut EVS": ["Non", "Oui", "NC", "Oui", "Non", "Non", "Oui"],
    "Usage": ["Intensif", "Standard", "Intensif", "Faible", "Standard", "Critique", "Standard"],
    "Roadmap sécurisation": ["X", "", "", "", "X", "X", ""],
    "Roadmap obsolescence": ["", "", "X", "", "", "X", ""],
}

df_raw = pd.DataFrame(data)

# =========================
# FUNCTIONS
# =========================

def normalize(series):
    if series.max() == series.min():
        return series * 0
    return (series - series.min()) / (series.max() - series.min())

def clean_text(text):
    return str(text).encode("latin-1", "ignore").decode("latin-1")

def parse_evs_flag(x):
    x = str(x).strip().lower()
    if x in ["n", "non", "no", "0"]: return 1.0
    elif x in ["o", "oui", "yes", "y", "1"]: return 0.3
    else: return 0.6

def apply_evs_rules(row):
    age = row["Age"]
    if age >= 40: return "EVS obligatoire"
    elif age >= 35: return "EVS à programmer"
    elif age >= 30: return "Première estimation"
    else: return "Suivi standard"

def assign_evs_decision(score):
    if score >= 0.75: return "EVS prioritaire immédiate"
    elif score >= 0.55: return "EVS à planifier"
    elif score >= 0.35: return "Surveillance renforcée"
    else: return "Suivi standard"

def generate_action_plan(row):
    score = row["priority_score"]
    if score >= 0.80: return "EVS immédiate + étude remplacement"
    elif score >= 0.65: return "EVS urgente + maintenance corrective"
    elif score >= 0.55: return "EVS à planifier court terme"
    elif score >= 0.35: return "Surveillance + maintenance préventive"
    else: return "Suivi standard"

def generate_deadline(row):
    score = row["priority_score"]
    if score >= 0.80: return "0-3 mois"
    elif score >= 0.65: return "3-6 mois"
    elif score >= 0.55: return "6-12 mois"
    elif score >= 0.35: return "12-24 mois"
    else: return "Routine"

def build_budget_selection(sorted_df, budget):
    selected_projects = []
    total_cost = 0
    for _, row in sorted_df.iterrows():
        cost = row["Montant EVS"]
        if total_cost + cost <= budget:
            selected_projects.append(row)
            total_cost += cost
    return pd.DataFrame(selected_projects), total_cost

# =========================
# PROCESSING
# =========================

clean_df = df_raw.copy()
clean_df["age_score"] = normalize(clean_df["Age"])
clean_df["evs_urgency"] = 1 - normalize(clean_df["EVS Année"])
clean_df["risk_proxy"] = clean_df["Statut EVS"].apply(parse_evs_flag)
clean_df["cost_score"] = normalize(clean_df["Montant EVS"])

clean_df["roadmap_risk"] = clean_df.apply(
    lambda row: 1.0 if str(row["Roadmap sécurisation"]).strip() not in ["", "nan", "None"]
    else 0.7 if str(row["Roadmap obsolescence"]).strip() not in ["", "nan", "None"]
    else 0.0, axis=1
)

st.sidebar.header("Réglage des pondérations")
w_age = st.sidebar.slider("Poids âge", 0.0, 1.0, 0.30, 0.05)
w_evs = st.sidebar.slider("Poids urgence EVS", 0.0, 1.0, 0.30, 0.05)
w_risk = st.sidebar.slider("Poids risque proxy", 0.0, 1.0, 0.20, 0.05)
w_roadmap = st.sidebar.slider("Poids roadmap", 0.0, 1.0, 0.20, 0.05)
w_cost = st.sidebar.slider("Poids coût pénalisant", 0.0, 0.5, 0.10, 0.05)

positive_weight_sum = w_age + w_evs + w_risk + w_roadmap
if positive_weight_sum == 0:
    st.error("Les pondérations positives ne peuvent pas toutes être nulles.")
    st.stop()

clean_df["priority_score"] = (
    (w_age/positive_weight_sum) * clean_df["age_score"]
    + (w_evs/positive_weight_sum) * clean_df["evs_urgency"]
    + (w_risk/positive_weight_sum) * clean_df["risk_proxy"]
    + (w_roadmap/positive_weight_sum) * clean_df["roadmap_risk"]
    - w_cost * clean_df["cost_score"]
).clip(lower=0, upper=1).round(2)

clean_df["Décision règle EVS"] = clean_df.apply(apply_evs_rules, axis=1)
clean_df["Décision score"] = clean_df["priority_score"].apply(assign_evs_decision)
clean_df["Plan d’action"] = clean_df.apply(generate_action_plan, axis=1)
clean_df["Délai recommandé"] = clean_df.apply(generate_deadline, axis=1)

# =========================
# LIVE INDICATOR & KPI
# =========================
avg_score = clean_df["priority_score"].mean()

st.markdown("## État du parc en temps réel")
# Indicateur visuel "Live"
col_ind1, col_ind2 = st.columns([1, 3])
with col_ind1:
    color = "red" if avg_score > 0.7 else "orange" if avg_score > 0.4 else "green"
    st.markdown(f"""
        <div style="padding:20px; border-radius:10px; background-color:{color}; text-align:center;">
            <h1 style="color:white; margin:0;">{avg_score:.2f}</h1>
            <p style="color:white; margin:0;">SCORE GLOBAL LIVE</p>
        </div>
    """, unsafe_allow_html=True)

with col_ind2:
    col1, col2, col3 = st.columns(3)
    col1.metric("Équipements", len(clean_df))
    col2.metric("EVS Critiques", len(clean_df[clean_df["priority_score"] >= 0.75]))
    col3.metric("Budget Total", f"{clean_df['Montant EVS'].sum():,.0f} €")

# =========================
# MAIN TABLES
# =========================

display_cols = ["Site", "Pont", "Age", "EVS Année", "Montant EVS", "priority_score", "Décision score", "Plan d’action", "Délai recommandé"]

st.subheader("Top équipements prioritaires")
st.dataframe(clean_df.sort_values(by="priority_score", ascending=False), use_container_width=True)

# =========================
# HEATMAP
# =========================

st.subheader("Analyse de concentration du risque")
heatmap_df = clean_df.groupby(["Site", "EVS Année"]).agg({"priority_score": "mean"}).reset_index()
heatmap_pivot = heatmap_df.pivot(index="Site", columns="EVS Année", values="priority_score").fillna(0)

fig, ax = plt.subplots(figsize=(10, 4))
cax = ax.imshow(heatmap_pivot, aspect="auto", cmap="YlOrRd")
ax.set_xticks(range(len(heatmap_pivot.columns)))
ax.set_yticks(range(len(heatmap_pivot.index)))
ax.set_xticklabels(heatmap_pivot.columns.astype(int))
ax.set_yticklabels(heatmap_pivot.index)
fig.colorbar(cax, label="Score de priorité")
st.pyplot(fig)

# =========================
# BUDGET SIMULATION
# =========================

st.markdown("---")
st.subheader("Moteur de simulation budgétaire EVS")
budget = st.slider("Budget disponible (€)", 5000, 100000, 30000, step=5000)

sorted_df = clean_df.sort_values(by="priority_score", ascending=False)
selected_df, total_cost = build_budget_selection(sorted_df, budget)

st.write(f"**Budget utilisé:** {int(total_cost):,} € / {budget:,} €")
if not selected_df.empty:
    st.dataframe(selected_df[display_cols], use_container_width=True)

# =========================
# PDF REPORT (UPDATED)
# =========================

def generate_pdf_report():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Rapport EVS Intelligence (Sans Risque Reglementaire)", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Score moyen du parc: {avg_score:.2f}", ln=True)
    pdf.cell(0, 8, f"Budget de simulation: {budget} EUR", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Liste des prioritaires:", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in selected_df.iterrows():
        pdf.cell(0, 6, clean_text(f"{row['Pont']} ({row['Site']}) - Score: {row['priority_score']}"), ln=True)
    
    return bytes(pdf.output(dest="S"))

st.download_button("Télécharger Rapport PDF", data=generate_pdf_report(), file_name="rapport_evs.pdf", mime="application/pdf")

st.markdown("---")
st.caption("© 2026 Hassan Attout, EVS Intelligence Platform")
