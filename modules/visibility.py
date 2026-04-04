"""
visibility.py — Betzdorf ground station look angle computation.
Coordinates: lat=49.7°N, lon=6.4°E, elevation=300m (approximate).
"""
import re

import numpy as np
import pandas as pd
from skyfield.api import Topos, load

BETZDORF_LAT = 49.7
BETZDORF_LON = 6.4
BETZDORF_ELEV_M = 300
VISIBILITY_ELEVATION_DEG = 5.0
GEO_DELTA_THRESHOLD_DEG = 0.1
LOOK_AHEAD_MINUTES = 10


def normalize_name(s: str) -> str:
    """Uppercase and remove spaces/hyphens for name comparison."""
    return re.sub(r"[\s\-]", "", s).upper()


def compute_look_angles(satellites: dict, ts) -> pd.DataFrame:
    """
    Compute Alt/Az look angles from Betzdorf for each satellite.

    Columns: name, orbit, elevation_deg, azimuth_deg, is_visible, geo_flag

    geo_flag logic (measurement-based):
        delta_el = |el(t_now) - el(t_now + 10 min)|
        delta_el < 0.1° → geo_flag=True  ("Near-constant (GEO)")
        delta_el >= 0.1° → geo_flag=False ("Dynamic (MEO)")

    is_visible: elevation_deg > 5.0
    """
    ground_station = Topos(
        latitude_degrees=BETZDORF_LAT,
        longitude_degrees=BETZDORF_LON,
        elevation_m=BETZDORF_ELEV_M,
    )

    t_now = ts.now()
    # t_plus10: 10 minutes later
    t_plus10 = ts.tt_jd(t_now.tt + LOOK_AHEAD_MINUTES / 1440.0)

    rows = []
    for name, v in satellites.items():
        sat = v["sat"]
        orbit = v["orbit"]
        try:
            diff_now = sat - ground_station
            topocentric_now = diff_now.at(t_now)
            alt_now, az_now, _ = topocentric_now.altaz()

            diff_later = sat - ground_station
            topocentric_later = diff_later.at(t_plus10)
            alt_later, _, _ = topocentric_later.altaz()

            el_now = float(alt_now.degrees)
            az_now_deg = float(az_now.degrees)
            el_later = float(alt_later.degrees)
            delta_el = abs(el_now - el_later)
            geo_flag = delta_el < GEO_DELTA_THRESHOLD_DEG
            is_visible = el_now > VISIBILITY_ELEVATION_DEG
        except Exception:
            continue

        rows.append(
            {
                "name": name,
                "orbit": orbit,
                "elevation_deg": round(el_now, 2),
                "azimuth_deg": round(az_now_deg, 2),
                "is_visible": is_visible,
                "geo_flag": geo_flag,
            }
        )
    return pd.DataFrame(rows)
