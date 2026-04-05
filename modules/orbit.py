"""
orbit.py — TLE loading, CATNR verification, and position computation.
Uses CelesTrak GP endpoint only: gp.php?CATNR={catnr}&FORMAT=3LE

Load priority:
  1. data/tle_snapshot.json  (committed via GitHub Actions)
  2. Live Celestrak fetch     (fallback when snapshot absent)
  3. data/mock_tles.json     (emergency fallback)
"""
import json
import re
import time as _time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st
from skyfield.api import EarthSatellite, load

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=3LE"
SNAPSHOT_PATH = Path("data/tle_snapshot.json")
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


def _build_satellites(entries, ts):
    """
    Build satellites dict from a list of (json_name, orbit, line0, line1, line2).
    Returns (satellites dict, catnr_warnings list).
    Applies EarthSatellite construction + normalize_name verification.
    """
    satellites = {}
    warnings = []
    for (json_name, orbit, line0, line1, line2) in entries:
        try:
            earth_sat = EarthSatellite(line1, line2, line0, ts)
        except Exception as e:
            warnings.append({
                "json_name": json_name,
                "celestrak_line0": line0,
                "reason": f"EarthSatellite init failed: {e}",
            })
            continue
        norm_line0 = normalize_name(line0)
        norm_json = normalize_name(json_name)
        if not (norm_json in norm_line0 or norm_line0 in norm_json):
            warnings.append({
                "json_name": json_name,
                "celestrak_line0": line0,
                "reason": "Name mismatch after normalize_name()",
            })
            continue
        satellites[json_name] = {"sat": earth_sat, "orbit": orbit}
    return satellites, warnings


def _fetch_tle(catnr: int) -> tuple | None:
    """
    Fetch 3LE from CelesTrak for a single CATNR.
    Returns (line0, line1, line2) on success, None on any failure.
    Prints diagnostic info on non-200 or exception for Cloud debugging.
    """
    url = CELESTRAK_URL.format(catnr=catnr)
    try:
        r = requests.get(url, timeout=10, headers=_HEADERS)
        print(f"[CELESTRAK] CATNR={catnr} status={r.status_code} text={r.text[:100]}", flush=True)
        if r.status_code != 200 or not r.text.strip():
            return None
        return _parse_3le(r.text)
    except Exception as e:
        print(f"[CELESTRAK] CATNR={catnr} exception={type(e).__name__}: {e}", flush=True)
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


def _latest_epoch_str(satellites: dict) -> str:
    """Return UTC ISO-8601 string of the most recent TLE epoch, or 'N/A'."""
    try:
        epochs = [v["sat"].epoch.utc_datetime() for v in satellites.values()]
        if epochs:
            return max(epochs).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass
    return "N/A"


def load_tles(satellite_list) -> tuple:
    """
    Load TLEs with session_state TTL cache (7200s).

    satellite_list: tuple of (name, catnr, orbit) tuples.

    Returns:
        [0] satellites: dict[str, dict]  — verified satellites only
        [1] fetch_ts: str                — UTC ISO-8601 (snapshot _updated_at or fetch time)
        [2] latest_epoch_str: str        — UTC ISO-8601 or 'N/A'
        [3] data_source: str             — 'snapshot' | 'live' | 'mock'
        [4] catnr_warnings: list[dict]
    """
    now = _time.time()
    fetched_at = st.session_state.get("tle_fetched_at", 0)
    cached = st.session_state.get("tle_cache")
    if cached is not None and (now - fetched_at) < 7200:
        return cached

    print("[CELESTRAK] load_tles() called - fetching fresh TLEs", flush=True)
    ts = load.timescale()
    sat_entries = [(e[0], e[1], e[2]) for e in satellite_list]
    satellites = {}
    catnr_warnings = []
    data_source = "live"
    fetch_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── 1순위: tle_snapshot.json ────────────────────────────────────────────
    if SNAPSHOT_PATH.exists():
        print("[CELESTRAK] Using tle_snapshot.json", flush=True)
        try:
            snap = json.loads(SNAPSHOT_PATH.read_text())
            snap_by_catnr = {s["catnr"]: s for s in snap.get("satellites", [])}
            entries = []
            for (json_name, catnr, orbit) in sat_entries:
                s = snap_by_catnr.get(catnr)
                if s:
                    entries.append((json_name, orbit, s["line0"], s["line1"], s["line2"]))
                else:
                    catnr_warnings.append({
                        "json_name": json_name,
                        "celestrak_line0": "N/A",
                        "reason": f"CATNR {catnr} not in snapshot",
                    })
            satellites, build_warns = _build_satellites(entries, ts)
            catnr_warnings.extend(build_warns)
            # snapshot _warnings → also surface in UI
            for w in snap.get("_warnings", []):
                catnr_warnings.append({
                    "json_name": f"CATNR {w.get('catnr', '?')}",
                    "celestrak_line0": "N/A",
                    "reason": f"[snapshot] {w.get('error_type', '')}: {w.get('message', '')}",
                })
            fetch_ts = snap.get("_updated_at", fetch_ts)
            data_source = "snapshot"
        except Exception as e:
            print(f"[CELESTRAK] snapshot read failed: {e}", flush=True)
            satellites = {}   # fall through to live

    # ── 2순위: Celestrak 직접 호출 ─────────────────────────────────────────
    if not satellites:
        print("[CELESTRAK] Snapshot absent or empty — trying live Celestrak", flush=True)
        fetch_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        live_ok = False
        try:
            probe = requests.get(
                CELESTRAK_URL.format(catnr=sat_entries[0][1]),
                timeout=8, headers=_HEADERS,
            )
            live_ok = probe.status_code == 200 and probe.text.strip() != ""
            if not live_ok:
                print(
                    f"[orbit] Celestrak probe failed: HTTP {probe.status_code} "
                    f"body={probe.text[:200]!r}", flush=True
                )
        except Exception as exc:
            print(f"[orbit] Celestrak probe exception {type(exc).__name__}: {exc}", flush=True)

        if live_ok:
            entries = []
            for (json_name, catnr, orbit) in sat_entries:
                parsed = _fetch_tle(catnr)
                if parsed is None:
                    catnr_warnings.append({
                        "json_name": json_name,
                        "celestrak_line0": "N/A",
                        "reason": "HTTP error or empty response (see server log)",
                    })
                    continue
                entries.append((json_name, orbit, parsed[0], parsed[1], parsed[2]))
            satellites, build_warns = _build_satellites(entries, ts)
            catnr_warnings.extend(build_warns)
            data_source = "live"

    # ── 3순위: mock_tles.json ───────────────────────────────────────────────
    if not satellites:
        print("[CELESTRAK] Falling back to mock_tles.json", flush=True)
        fetch_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            mock_sats = _load_mock_tles()
            mock_by_catnr = {m["catnr"]: m for m in mock_sats}
            entries = []
            for (json_name, catnr, orbit) in sat_entries:
                m = mock_by_catnr.get(catnr)
                if m:
                    entries.append((json_name, orbit, m["line0"], m["line1"], m["line2"]))
            satellites, build_warns = _build_satellites(entries, ts)
            catnr_warnings.extend(build_warns)
            data_source = "mock"
        except RuntimeError as e:
            catnr_warnings.append({
                "json_name": "ALL", "celestrak_line0": "N/A", "reason": str(e),
            })

    epoch_str = _latest_epoch_str(satellites)
    result = (satellites, fetch_ts, epoch_str, data_source, catnr_warnings)
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
        rows.append({
            "name": name,
            "orbit": orbit,
            "lat": lat,
            "lon": lon,
            "altitude_km": round(alt_km, 1),
            "velocity_kms": round(vel_kms, 3),
            "catnr": getattr(sat, "model", None) and sat.model.satnum or "N/A",
        })
    return pd.DataFrame(rows)
