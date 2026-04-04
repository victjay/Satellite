"""SYNTHETIC DATA ONLY — Health KPI generator."""
import random

import pandas as pd


def generate_health_kpi(satellite_names: list) -> pd.DataFrame:
    """
    Generate stable synthetic health KPI scores for each satellite.

    Columns: name, health_score, status, note
    Seed: hash(name) % 1000 per satellite (stable across calls).
    Thresholds: Green >= 80 / Yellow 60–79 / Red < 60.
    """
    rows = []
    for name in satellite_names:
        seed = hash(name) % 1000
        rng = random.Random(seed)
        score = rng.randint(40, 100)
        if score >= 80:
            status = "Green"
            note = "Operating within nominal range"
        elif score >= 60:
            status = "Yellow"
            note = "Minor deviation detected (synthetic)"
        else:
            status = "Red"
            note = "Threshold exceeded (synthetic)"
        rows.append({"name": name, "health_score": score, "status": status, "note": note})
    return pd.DataFrame(rows)
