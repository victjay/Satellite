"""SYNTHETIC DATA ONLY — Anomaly alert log generator."""
import random
from datetime import datetime, timedelta, timezone

import pandas as pd

ANOMALY_TYPES = [
    "Link Quality Drop",
    "Telemetry Gap",
    "Threshold Exceeded",
    "Look Angle Deviation",
    "Data Latency Spike",
]

LOOK_ANGLE_DEVIATION_NOTE = (
    "Synthetic: delta elevation exceeds synthetic threshold (demo only)"
)

_SEVERITIES = ["High", "Medium", "Low"]
_STATUSES = ["Open", "Acknowledged", "Resolved"]
_ACTIONS = [
    "Scheduled maintenance review",
    "Flagged for ops team",
    "Auto-logged",
    "Escalated to engineer",
    "Monitoring in progress",
]


def generate_alerts(satellite_names: list) -> pd.DataFrame:
    """
    Generate 5–10 synthetic anomaly alerts covering the last 24 hours.

    Columns: timestamp, satellite, anomaly_type, severity, status, action_taken, notes
    At least one 'Look Angle Deviation' row is always included.
    """
    rng = random.Random(sum(ord(c) for c in "".join(satellite_names)))
    now = datetime.now(timezone.utc)
    n_alerts = rng.randint(5, 10)

    rows = []
    # Guarantee one Look Angle Deviation first
    lad_sat = rng.choice(satellite_names)
    lad_offset = timedelta(hours=rng.uniform(0, 23))
    rows.append(
        {
            "timestamp": (now - lad_offset).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "satellite": lad_sat,
            "anomaly_type": "Look Angle Deviation",
            "severity": rng.choice(_SEVERITIES),
            "status": rng.choice(_STATUSES),
            "action_taken": rng.choice(_ACTIONS),
            "notes": LOOK_ANGLE_DEVIATION_NOTE,
        }
    )

    # Fill remaining rows with other anomaly types
    other_types = [t for t in ANOMALY_TYPES if t != "Look Angle Deviation"]
    for _ in range(n_alerts - 1):
        offset = timedelta(hours=rng.uniform(0, 24))
        rows.append(
            {
                "timestamp": (now - offset).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "satellite": rng.choice(satellite_names),
                "anomaly_type": rng.choice(other_types),
                "severity": rng.choice(_SEVERITIES),
                "status": rng.choice(_STATUSES),
                "action_taken": rng.choice(_ACTIONS),
                "notes": "",
            }
        )

    df = pd.DataFrame(rows).sort_values("timestamp", ascending=False).reset_index(drop=True)
    return df
