import pandas as pd
import numpy as np

def generate_synthetic_data(n=300):
    np.random.seed(42)

    age = np.random.randint(1, 30, n)
    usage = np.random.randint(500, 5000, n)
    maintenance = np.random.randint(10, 365, n)
    failures = np.random.randint(0, 10, n)
    environment = np.random.choice(
        ["Normal", "Poussiéreux", "Humide", "Sévère"], n
    )
    criticality = np.random.randint(1, 5, n)
    non_conformities = np.random.randint(0, 5, n)

    # Generate failure probability logic
    base_risk = (
        0.3 * (age / 30) +
        0.3 * (usage / 5000) +
        0.2 * (maintenance / 365) +
        0.2 * (failures / 10)
    )

    env_map = {
        "Normal": 0.1,
        "Poussiéreux": 0.3,
        "Humide": 0.4,
        "Sévère": 0.6
    }

    env_factor = np.array([env_map[e] for e in environment])

    total_risk = base_risk + env_factor

    # Convert to probability
    probability = total_risk / total_risk.max()

    failure_next_12m = (probability > 0.6).astype(int)

    data = {
        "equipment_id": [f"CRANE_{i}" for i in range(n)],
        "age_years": age,
        "usage_hours_per_year": usage,
        "last_maintenance_days": maintenance,
        "number_of_failures_3y": failures,
        "environment": environment,
        "criticality_level": criticality,
        "regulatory_non_conformities": non_conformities,
        "failure_next_12m": failure_next_12m
    }

    return pd.DataFrame(data)