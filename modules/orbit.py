import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st
from skyfield.api import EarthSatellite, load

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=3LE"
MOCK_TLE_PATH = Path("data/mock_tles.json")
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ses-demo/1.0)"}


def normalize_name(s: str) -> str:
    """Uppercase and remove spaces/hyphens for name comparison."""
    return re.sub(r"[\s\-]", "", s).upper()


def _parse_3le(text: str):
    """Parse a 3LE text block; return (line0, line1, line2) or None."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if len(lines) >= 3:
        return lines[0], lines[1], lines[2]
    return None


def _load_mock_tles():
    """
    Load mock TLE data from data/mock_tles.json.
    Raises RuntimeError if any FILL_MANUALLY placeholder remains.
    """
    data = json.loads(MOCK_TLE_PATH.read_text())
    for sat in data["mock_satellites"]:
        if "FILL_MANUALLY" in (sat["line0"], sat["line1"], sat["line2"]):
            raise RuntimeError(
                "Mock TLE not initialized — please fill data/mock_tles.json manually"
            )
    return data["mock_satellites"]


def _fetch_tle(catnr: int) -> tuple | None:
    """
    Fetch 3LE from CelesTrak for a single CATNR.
    Returns (line0, line1, line2) on success, None on any failure.
    Prints diagnostic info on non-200 or exception for Cloud debugging.
    """
    url = CELESTRAK_URL.format(catnr=catnr)
    try:
        r = requests.get(url, timeout=10, headers=_HEADERS)
        #print(f"[CELESTRAK] CATNR={catnr} status={r.status_code} text={r.text[:100]}")
        print(f"[CELESTRAK] CATNR={catnr} status={r.status_code} text={r.text[:100]}", flush=True)
        if r.status_code != 200 or not r.text.strip():
            return None
        return _parse_3le(r.text)
    except Exception as e:
        #print(f"[CELESTRAK] CATNR={catnr} exception={type(e).__name__}: {e}")
        print(f"[CELESTRAK] CATNR={catnr} exception={type(e).__name__}: {e}", flush=True)
        return None


def load_tles(satellite_list) -> tuple:
    """
    Load TLEs for all satellites. TTL cache via st.session_state (7200s).

    satellite_list: tuple of (name, catnr, orbit) tuples.

    Returns:
        [0] satellites: dict[str, dict]  — verified satellites only, values: {sat, orbit}
        [1] fetch_timestamp: str         — UTC ISO-8601
        [2] latest_epoch_str: str        — UTC ISO-8601 or 'N/A'
        [3] is_mock_data: bool
        [4] catnr_warnings: list[dict]
    """
    import time as _time
    now = _time.time()
    fetched_at = st.session_state.get("tle_fetched_at", 0)
    cached = st.session_state.get("tle_cache")
    if cached is not None and (now - fetched_at) < 7200:
        return cached

    #print("[CELESTRAK] load_tles() called - fetching fresh TLEs")
    print("[CELESTRAK] load_tles() called - fetching fresh TLEs", flush=True)
    ts = load.timescale()
    fetch_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    satellites = {}
    catnr_warnings = []
    is_mock_data = False

    # Normalize input to list of (name, catnr, orbit) tuples
    sat_entries = [(e[0], e[1], e[2]) for e in satellite_list]

    # Try live Celestrak first (probe with first satellite)
    live_ok = False
    try:
        probe = requests.get(
            CELESTRAK_URL.format(catnr=sat_entries[0][1]),
            timeout=8,
            headers=_HEADERS,
        )
        live_ok = probe.status_code == 200 and probe.text.strip() != ""
        if not live_ok:
            #print(
            #    f"[orbit] Celestrak probe failed: HTTP {probe.status_code} "
            #    f"body={probe.text[:200]!r}"
            #)
            print(
                f"[orbit] Celestrak probe failed: HTTP {probe.status_code} "
                f"body={probe.text[:200]!r}", flush=True
            )
    except Exception as exc:
        #print(f"[orbit] Celestrak probe exception {type(exc).__name__}: {exc}")
        print(f"[orbit] Celestrak probe exception {type(exc).__name__}: {exc}", flush=True)
        live_ok = False

    if live_ok:
        for (json_name, catnr, orbit) in sat_entries:
            parsed = _fetch_tle(catnr)
            if parsed is None:
                catnr_warnings.append(
                    {
                        "catnr": catnr,
                        "json_name": json_name,
                        "celestrak_line0": "N/A",
                        "reason": "HTTP error or empty response (see server log)",
                    }
                )
                continue
            line0, line1, line2 = parsed
            # Step A: construct EarthSatellite
            try:
                earth_sat = EarthSatellite(line1, line2, line0, ts)
            except Exception as e:
                catnr_warnings.append(
                    {
                        "catnr": catnr,
                        "json_name": json_name,
                        "celestrak_line0": line0,
                        "reason": f"EarthSatellite init failed: {e}",
                    }
                )
                continue
            # Step B: name verification
            norm_line0 = normalize_name(line0)
            norm_json = normalize_name(json_name)
            if not (norm_json in norm_line0 or norm_line0 in norm_json):
                catnr_warnings.append(
                    {
                        "catnr": catnr,
                        "json_name": json_name,
                        "celestrak_line0": line0,
                        "reason": "Name mismatch after normalize_name()",
                    }
                )
                continue
            # Store with original json name for consistent display
            satellites[json_name] = {"sat": earth_sat, "orbit": orbit}
    else:
        # Fallback to mock
        is_mock_data = True
        try:
            mock_sats = _load_mock_tles()
        except RuntimeError as e:
            # Can't use mock either — return empty with warning
            catnr_warnings.append(
                {"catnr": "ALL", "json_name": "ALL", "celestrak_line0": "N/A", "reason": str(e)}
            )
            return satellites, fetch_ts, "N/A", is_mock_data, catnr_warnings

        # Build lookup by catnr
        mock_by_catnr = {m["catnr"]: m for m in mock_sats}
        for (json_name, catnr, orbit) in sat_entries:
            mock = mock_by_catnr.get(catnr)
            if mock is None:
                continue
            line0, line1, line2 = mock["line0"], mock["line1"], mock["line2"]
            try:
                earth_sat = EarthSatellite(line1, line2, line0, ts)
            except Exception as e:
                catnr_warnings.append(
                    {
                        "catnr": catnr,
                        "json_name": json_name,
                        "celestrak_line0": line0,
                        "reason": f"EarthSatellite init failed: {e}",
                    }
                )
                continue
            satellites[json_name] = {"sat": earth_sat, "orbit": orbit}

    # Compute latest_epoch_str
    latest_epoch_str = "N/A"
    try:
        epochs = []
        for v in satellites.values():
            ep = v["sat"].epoch.utc_datetime()
            epochs.append(ep)
        if epochs:
            latest_dt = max(epochs)
            latest_epoch_str = latest_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        latest_epoch_str = "N/A"

    result = (satellites, fetch_ts, latest_epoch_str, is_mock_data, catnr_warnings)
    st.session_state["tle_cache"] = result
    st.session_state["tle_fetched_at"] = now
    return result


def compute_positions(satellites: dict, ts) -> pd.DataFrame:
    """
    Compute current geocentric positions for all loaded satellites.

    Columns: name, orbit, lat, lon, altitude_km, velocity_kms, catnr
    lat clipped to [-90, 90]; lon clipped to [-180, 180].
    """
    rows = []
    t_now = ts.now()
    for name, v in satellites.items():
        sat = v["sat"]
        orbit = v["orbit"]
        try:
            geo = sat.at(t_now)
            subpoint = geo.subpoint()
            lat = float(np.clip(subpoint.latitude.degrees, -90, 90))
            lon = float(np.clip(subpoint.longitude.degrees, -180, 180))
            alt_km = float(subpoint.elevation.km)
            vel_kms = float(geo.velocity.km_per_s.dot(geo.velocity.km_per_s) ** 0.5)
        except Exception:
            continue
        rows.append(
            {
                "name": name,
                "orbit": orbit,
                "lat": lat,
                "lon": lon,
                "altitude_km": round(alt_km, 1),
                "velocity_kms": round(vel_kms, 3),
                "catnr": getattr(sat, "model", None) and sat.model.satnum or "N/A",
            }
        )
    return pd.DataFrame(rows)
