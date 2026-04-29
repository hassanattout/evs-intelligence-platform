import pandas as pd

def normalize(series):
    if series.max() == series.min():
        return series * 0
    return (series - series.min()) / (series.max() - series.min())

def calculate_risk_score(df):
    df = df.copy()

    age_factor = normalize(df["age_years"])
    usage_factor = normalize(df["usage_hours_per_year"])
    maintenance_factor = normalize(df["last_maintenance_days"])
    failure_factor = normalize(df["number_of_failures_3y"])
    regulatory_factor = normalize(df["regulatory_non_conformities"])
    criticality_factor = normalize(df["criticality_level"])

    environment_factor = df["environment"].map({
        "Normal": 0.2,
        "Poussiéreux": 0.5,
        "Humide": 0.6,
        "Sévère": 1.0
    })

    df["risk_score"] = (
        0.20 * age_factor +
        0.20 * usage_factor +
        0.15 * maintenance_factor +
        0.15 * failure_factor +
        0.10 * environment_factor +
        0.10 * regulatory_factor +
        0.10 * criticality_factor
    ) * 100

    df["risk_score"] = df["risk_score"].round(1)

    df["risk_class"] = pd.cut(
        df["risk_score"],
        bins=[0, 30, 60, 80, 100],
        labels=["Faible", "Modéré", "Élevé", "Critique"],
        include_lowest=True
    )

    return df