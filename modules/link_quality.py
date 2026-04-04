"""SYNTHETIC DATA ONLY — Link-quality trend generator."""
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

_WARN_THRESHOLD = 30
_CRIT_THRESHOLD = 15


def generate_link_quality(satellite_names: list, hours: int = 72) -> pd.DataFrame:
    """
    Generate synthetic link-quality time-series over a rolling window.

    Columns: timestamp (UTC ISO-8601), name, quality_score, alert_level
    quality_score: arbitrary units 0–100.
    alert_level: 'Normal' | 'Warning' (< 30) | 'Critical' (< 15).
    One data point per hour per satellite.
    """
    now = datetime.now(timezone.utc)
    rows = []
    for name in satellite_names:
        seed = hash(name) % 9999
        rng = np.random.default_rng(seed)
        base = float(rng.uniform(65, 90))
        scores = [base]
        for _ in range(hours - 1):
            delta = float(rng.uniform(-6, 6))
            next_score = float(np.clip(scores[-1] + delta, 0, 100))
            scores.append(next_score)

        for i, score in enumerate(scores):
            ts = now - timedelta(hours=(hours - 1 - i))
            score_rounded = round(score, 1)
            if score_rounded < _CRIT_THRESHOLD:
                alert_level = "Critical"
            elif score_rounded < _WARN_THRESHOLD:
                alert_level = "Warning"
            else:
                alert_level = "Normal"
            rows.append(
                {
                    "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "name": name,
                    "quality_score": score_rounded,
                    "alert_level": alert_level,
                }
            )
    return pd.DataFrame(rows)
