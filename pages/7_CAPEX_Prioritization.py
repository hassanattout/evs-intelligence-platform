from fpdf import FPDF
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("EVS Intelligence Platform")
st.caption("Outil d’aide à la décision pour la digitalisation de l’évaluation spéciale des ponts roulants")

st.markdown("""
### Objectif de l’outil
Cet outil vise à digitaliser l’évaluation spéciale des ponts roulants en combinant:
- une base équipements,
- des règles métier EVS,
- un score de priorité,
- une couche de risque réglementaire,
- une simulation budgétaire,
- une analyse multi-sites,
- une simulation du risque en cas de report,
- une planification EVS dans le temps,
- l’import des règles métier,
- une heatmap site vs année,
- et une génération automatique de rapport.

L’objectif est de passer d’un suivi principalement Excel à une aide à la décision structurée et exploitable.
""")

uploaded_file = st.file_uploader("Upload CAPEX Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name=0, header=8)

    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all")
    df = df[df["Pont"].notna()]

    key_cols = [
        "PAYS",
        "Site",
        "Pont",
        "MES",
        "Age",
        "Evaluation Spéciale O/N",
        "EVS Année",
    ]

    available_cols = [col for col in key_cols if col in df.columns]

    cost_col = None
    for col in df.columns:
        if "montant" in col.lower():
            cost_col = col
            break

    if cost_col is not None:
        available_cols.append(cost_col)

    clean_df = df[available_cols].copy()

    clean_df["Age"] = pd.to_numeric(clean_df["Age"], errors="coerce")
    clean_df["EVS Année"] = pd.to_numeric(clean_df["EVS Année"], errors="coerce")

    if cost_col is not None:
        clean_df[cost_col] = pd.to_numeric(clean_df[cost_col], errors="coerce")
    else:
        clean_df["Montant détecté"] = 0
        cost_col = "Montant détecté"

    clean_df = clean_df.dropna(subset=["Age", "EVS Année"])
    clean_df[cost_col] = clean_df[cost_col].fillna(0).astype(int)

    def normalize(series):
        if series.max() == series.min():
            return series * 0
        return (series - series.min()) / (series.max() - series.min())

    clean_df["age_score"] = normalize(clean_df["Age"])
    clean_df["evs_urgency"] = 1 - normalize(clean_df["EVS Année"])

    clean_df["risk_proxy"] = clean_df["Evaluation Spéciale O/N"].apply(
        lambda x: 1 if str(x).strip().upper() == "N" else 0.3
    )

    clean_df["cost_score"] = normalize(clean_df[cost_col])

    clean_df["regulatory_risk"] = clean_df["Age"].apply(
        lambda x: 1.0 if x >= 35 else 0.5 if x >= 25 else 0.2
    )

    st.sidebar.header("Réglage des pondérations")

    w_age = st.sidebar.slider("Poids âge", 0.0, 1.0, 0.25, 0.05)
    w_evs = st.sidebar.slider("Poids urgence EVS", 0.0, 1.0, 0.25, 0.05)
    w_risk = st.sidebar.slider("Poids risque proxy", 0.0, 1.0, 0.20, 0.05)
    w_reg = st.sidebar.slider("Poids risque réglementaire", 0.0, 1.0, 0.30, 0.05)
    w_cost = st.sidebar.slider("Poids coût (pénalité)", 0.0, 0.5, 0.10, 0.05)

    clean_df["priority_score"] = (
        w_age * clean_df["age_score"]
        + w_evs * clean_df["evs_urgency"]
        + w_risk * clean_df["risk_proxy"]
        + w_reg * clean_df["regulatory_risk"]
        - w_cost * clean_df["cost_score"]
    ).round(2)

    def apply_evs_rules(row):
        age = row["Age"]

        if age >= 40:
            return "EVS obligatoire immediate"
        elif age >= 35:
            return "EVS reglementaire prioritaire"
        elif age >= 30:
            return "EVS a programmer court terme"
        elif age >= 25:
            return "Surveillance renforcee"
        else:
            return "Suivi standard"

    def assign_evs_decision(score):
        if score >= 0.75:
            return "EVS prioritaire immediate"
        elif score >= 0.55:
            return "EVS a planifier"
        elif score >= 0.35:
            return "Surveillance renforcee"
        else:
            return "Suivi standard"

    def generate_action_plan(row):
        score = row["priority_score"]
        regulatory_risk = row["regulatory_risk"]

        if score >= 0.80 or regulatory_risk >= 1.0:
            return "ARRET si necessaire + EVS immediate + etude remplacement"
        elif score >= 0.65:
            return "EVS urgente + maintenance corrective"
        elif score >= 0.55:
            return "EVS a planifier court terme"
        elif score >= 0.35:
            return "Surveillance + maintenance preventive"
        else:
            return "Suivi standard"

    def generate_deadline(row):
        score = row["priority_score"]
        regulatory_risk = row["regulatory_risk"]

        if score >= 0.80 or regulatory_risk >= 1.0:
            return "0-3 mois"
        elif score >= 0.65:
            return "3-6 mois"
        elif score >= 0.55:
            return "6-12 mois"
        elif score >= 0.35:
            return "12-24 mois"
        else:
            return "Routine"

    clean_df["evs_rule_decision"] = clean_df.apply(apply_evs_rules, axis=1)
    clean_df["decision_evs"] = clean_df["priority_score"].apply(assign_evs_decision)
    clean_df["action_plan"] = clean_df.apply(generate_action_plan, axis=1)
    clean_df["deadline"] = clean_df.apply(generate_deadline, axis=1)

    clean_df["risk_if_delayed_1y"] = (clean_df["priority_score"] * 1.15).round(2)
    clean_df["risk_if_delayed_2y"] = (clean_df["priority_score"] * 1.30).round(2)

    total_assets = len(clean_df)
    avg_priority = round(clean_df["priority_score"].mean(), 2)
    urgent_assets = len(clean_df[clean_df["decision_evs"] == "EVS prioritaire immediate"])
    high_regulatory_assets = len(clean_df[clean_df["regulatory_risk"] >= 1.0])
    total_budget_estimate = int(clean_df[cost_col].sum())

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Équipements analysés", total_assets)
    col2.metric("Score moyen", avg_priority)
    col3.metric("EVS prioritaires", urgent_assets)
    col4.metric("Risque réglementaire élevé", high_regulatory_assets)
    col5.metric("Budget total estimé", f"{total_budget_estimate:,} €")

    display_cols = [
        "Site",
        "Pont",
        "Age",
        "EVS Année",
        cost_col,
        "regulatory_risk",
        "evs_rule_decision",
        "priority_score",
        "decision_evs",
        "action_plan",
        "deadline",
    ]

    st.subheader("Priorisation EVS")
    st.dataframe(
        clean_df.sort_values(by="priority_score", ascending=False)[display_cols].head(20).astype(str),
        use_container_width=True
    )

    st.subheader("Synthèse par site")
    site_summary = clean_df.groupby("Site").agg(
        nombre_equipements=("Pont", "count"),
        age_moyen=("Age", "mean"),
        score_moyen=("priority_score", "mean"),
        risque_reglementaire_moyen=("regulatory_risk", "mean"),
        budget_total=(cost_col, "sum")
    ).reset_index()

    site_summary["age_moyen"] = site_summary["age_moyen"].round(1)
    site_summary["score_moyen"] = site_summary["score_moyen"].round(2)
    site_summary["risque_reglementaire_moyen"] = site_summary["risque_reglementaire_moyen"].round(2)
    site_summary["budget_total"] = site_summary["budget_total"].astype(int)

    st.dataframe(
        site_summary.sort_values(by="score_moyen", ascending=False).astype(str),
        use_container_width=True
    )

    st.subheader("Classement des sites les plus critiques")

    site_ranking = clean_df.groupby("Site").agg(
        score_moyen=("priority_score", "mean"),
        risque_reglementaire=("regulatory_risk", "mean"),
        budget_total=(cost_col, "sum")
    ).reset_index()

    site_ranking["criticite"] = (
        0.5 * site_ranking["score_moyen"]
        + 0.5 * site_ranking["risque_reglementaire"]
    ).round(2)

    site_ranking["score_moyen"] = site_ranking["score_moyen"].round(2)
    site_ranking["risque_reglementaire"] = site_ranking["risque_reglementaire"].round(2)
    site_ranking["budget_total"] = site_ranking["budget_total"].astype(int)

    st.dataframe(
        site_ranking.sort_values(by="criticite", ascending=False).astype(str),
        use_container_width=True
    )

    st.subheader("Simulation du risque en cas de report")
    delay_cols = [
        "Site",
        "Pont",
        "Age",
        "priority_score",
        "risk_if_delayed_1y",
        "risk_if_delayed_2y",
        "action_plan",
    ]

    st.dataframe(
        clean_df.sort_values(by="risk_if_delayed_2y", ascending=False)[delay_cols].head(20).astype(str),
        use_container_width=True
    )

    st.subheader("Planification EVS dans le temps")

    timeline_df = clean_df.copy()
    timeline_df["annee_action"] = timeline_df["EVS Année"]

    timeline_summary = timeline_df.groupby("annee_action").agg(
        nb_equipements=("Pont", "count"),
        budget_total=(cost_col, "sum"),
        score_moyen=("priority_score", "mean"),
        risque_reglementaire_moyen=("regulatory_risk", "mean")
    ).reset_index()

    timeline_summary["annee_action"] = timeline_summary["annee_action"].astype(int)
    timeline_summary["score_moyen"] = timeline_summary["score_moyen"].round(2)
    timeline_summary["risque_reglementaire_moyen"] = timeline_summary["risque_reglementaire_moyen"].round(2)
    timeline_summary["budget_total"] = timeline_summary["budget_total"].astype(int)

    st.dataframe(
        timeline_summary.sort_values(by="annee_action").astype(str),
        use_container_width=True
    )

    st.subheader("Projection budgétaire EVS par année")
    st.line_chart(
        timeline_summary.sort_values(by="annee_action").set_index("annee_action")["budget_total"]
    )

    st.subheader("Projection du risque réglementaire moyen par année")
    st.line_chart(
        timeline_summary.sort_values(by="annee_action").set_index("annee_action")["risque_reglementaire_moyen"]
    )

    st.subheader("Heatmap EVS: site vs année")

    heatmap_df = clean_df.groupby(["Site", "EVS Année"]).agg(
        score_moyen=("priority_score", "mean")
    ).reset_index()

    heatmap_pivot = heatmap_df.pivot(
        index="Site",
        columns="EVS Année",
        values="score_moyen"
    ).fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))
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

    st.markdown("---")
    st.subheader("Règles EVS importées")

    try:
        rules_df = pd.read_excel(uploaded_file, sheet_name="Règles")
        rules_df = rules_df.dropna(how="all")
        rules_df.columns = rules_df.columns.astype(str).str.strip()

        st.dataframe(rules_df.astype(str), use_container_width=True)

    except Exception as e:
        st.warning("La feuille 'Règles' n’a pas pu être importée.")
        st.write(str(e))

    st.markdown("---")
    st.subheader("Simulation budget EVS")

    budget = st.slider(
        "Budget (€)",
        100000, 2000000, 500000, step=50000
    )

    sorted_df = clean_df.sort_values(by="priority_score", ascending=False)

    selected_projects = []
    total_cost = 0

    for _, row in sorted_df.iterrows():
        cost = row[cost_col] if pd.notna(row[cost_col]) else 0
        if total_cost + cost <= budget:
            selected_projects.append(row)
            total_cost += cost

    selected_df = pd.DataFrame(selected_projects)

    st.write(f"Budget utilisé: {int(total_cost)} € / {budget} €")
    st.write(f"Nombre d'équipements sélectionnés: {len(selected_df)}")

    if len(selected_df) > 0:
        st.dataframe(selected_df[display_cols].astype(str), use_container_width=True)

        st.markdown("---")
        st.subheader("Télécharger rapport PDF")

        def clean_text(text):
            return str(text).encode("latin-1", "ignore").decode("latin-1")

        def generate_pdf_report():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Rapport EVS", ln=True)

            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, f"Budget: {int(total_cost)} / {budget} EUR", ln=True)
            pdf.cell(0, 8, f"Nombre equipements: {len(selected_df)}", ln=True)
            pdf.ln(4)

            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, "Synthese", ln=True)

            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(
                0,
                5,
                clean_text(
                    f"Ce rapport presente une priorisation EVS basee sur un score multicritere "
                    f"integrant l'age, l'urgence EVS, le risque reglementaire et la contrainte budgetaire. "
                    f"Nombre total d'equipements selectionnes: {len(selected_df)}."
                )
            )
            pdf.ln(4)

            top5 = selected_df.sort_values(by="priority_score", ascending=False).head(5)

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

            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, "Equipements selectionnes", ln=True)

            pdf.set_font("Arial", "", 10)

            for _, row in selected_df.iterrows():
                pdf.cell(0, 6, clean_text(f"{row['Pont']} - {row['Site']}"), ln=True)
                pdf.multi_cell(0, 5, clean_text(
                    f"Age: {row['Age']} | EVS: {row['EVS Année']} | Score: {row['priority_score']}\n"
                    f"Risque reglementaire: {row['regulatory_risk']}\n"
                    f"Regle EVS: {row['evs_rule_decision']}\n"
                    f"Decision: {row['decision_evs']}\n"
                    f"Action: {row['action_plan']} | Delai: {row['deadline']}"
                ))
                pdf.ln(2)

            return bytes(pdf.output(dest="S"))

        pdf_bytes = generate_pdf_report()

        st.download_button(
            "Télécharger PDF",
            data=pdf_bytes,
            file_name="rapport_evs.pdf",
            mime="application/pdf"
        )

    else:
        st.warning("Aucun équipement sélectionné")

else:
    st.info("Importer le fichier Excel pour commencer")