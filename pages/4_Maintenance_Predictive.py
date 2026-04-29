import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd

from src.data_generator import generate_synthetic_data
from src.risk_scoring import calculate_risk_score

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

st.title("Maintenance Prédictive")

# Load data
df = generate_synthetic_data(300)
df = calculate_risk_score(df)

# Features
FEATURES = [
    "age_years",
    "usage_hours_per_year",
    "last_maintenance_days",
    "number_of_failures_3y",
    "criticality_level",
    "regulatory_non_conformities"
]

TARGET = "failure_next_12m"

X = df[FEATURES]
y = df[TARGET]

# Train model
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_proba)

col1, col2 = st.columns(2)

col1.metric("Accuracy", round(accuracy, 3))
col2.metric("ROC-AUC", round(auc, 3))

st.markdown("---")

# Select equipment
selected_equipment = st.selectbox(
    "Choisir un équipement",
    df["equipment_id"]
)

equipment = df[df["equipment_id"] == selected_equipment]

X_selected = equipment[FEATURES]

proba = model.predict_proba(X_selected)[0][1]

st.subheader("Prédiction")

st.metric(
    "Probabilité de défaillance (12 mois)",
    f"{round(proba * 100, 1)}%"
)

# Interpretation
if proba > 0.7:
    st.error("Risque très élevé → intervention immédiate recommandée")
elif proba > 0.5:
    st.warning("Risque élevé → maintenance à planifier rapidement")
elif proba > 0.3:
    st.info("Risque modéré → surveillance")
else:
    st.success("Risque faible → fonctionnement normal")

# Feature importance
st.subheader("Importance des facteurs")

importance_df = pd.DataFrame({
    "Feature": FEATURES,
    "Importance": model.feature_importances_
}).sort_values(by="Importance", ascending=False)

st.bar_chart(importance_df.set_index("Feature"))