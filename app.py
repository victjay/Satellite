"""
app.py — SES Satellite Payload Monitoring Prototype Dashboard
5 tabs: Global Orbit Map · Betzdorf Look Angles · Anomaly Alert Log · Health KPI · Link-quality Trend
"""
import json
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from skyfield.api import load as skyfield_load

from modules.alerts import generate_alerts
from modules.kpi import generate_health_kpi
from modules.link_quality import generate_link_quality
from modules.orbit import compute_positions, load_tles
from modules.visibility import compute_look_angles

st.set_page_config(layout="wide", page_title="SES Payload Monitoring — Prototype")

st.title("SES Satellite Payload Monitoring")
st.caption("Prototype Dashboard | Real TLE look angles · Simulated telemetry workflow")

# --- Load satellite list ---
with open("data/ses_satellites_sample.json") as f:
    sat_data = json.load(f)
satellite_list = sat_data["satellites"]

# --- Load TLEs ---
# Pass as a hashable tuple of frozen dicts (st.cache_data requires hashable args)
_sat_key = tuple((s["name"], s["catnr"], s["orbit"]) for s in satellite_list)
satellites, fetch_ts, epoch_str, data_source, catnr_warns = load_tles(_sat_key)

# --- Status banner ---
if data_source == "snapshot":
    st.info(f"TLE snapshot: {fetch_ts} (auto-updated daily) | Latest TLE epoch: {epoch_str} UTC")
elif data_source == "live":
    st.info(f"TLE fetched: {fetch_ts} UTC (2h cache) | Latest TLE epoch: {epoch_str} UTC")
else:  # mock
    st.warning("⚠️ Mock mode: static snapshot TLE (for UI workflow only) — Celestrak unavailable")

# --- CATNR / snapshot warnings ---
if catnr_warns:
    with st.expander("⚠️ TLE Snapshot Warnings (click to expand)"):
        st.dataframe(pd.DataFrame(catnr_warns))

# --- Refresh button with 30s cooldown ---
last_refresh = st.session_state.get("last_refresh_ts", 0)
cooldown = 30
elapsed = time.time() - last_refresh
if elapsed > cooldown:
    if st.button("🔄 Refresh TLE Data"):
        st.session_state["tle_fetched_at"] = 0
        st.session_state["last_refresh_ts"] = time.time()
        st.rerun()
else:
    remaining = int(cooldown - elapsed)
    st.button(f"🔄 Refresh (available in {remaining}s)", disabled=True)

# --- Timescale ---
ts = skyfield_load.timescale()

# --- Satellite names for synthetic modules ---
sat_names = list(satellites.keys())

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌍 Global Orbit Map",
    "📡 Betzdorf Look Angles",
    "🔴 Anomaly Alert Log",
    "🟢 Health KPI",
    "📈 Link-quality Trend",
])

# ── Tab 1: Global Orbit Map ──────────────────────────────────────────────────
with tab1:
    st.subheader("Current Satellite Positions (Real TLE · SGP4)")

    pos_df = compute_positions(satellites, ts)

    if pos_df.empty:
        st.warning("No satellite position data available.")
    else:
        geo_df = pos_df[pos_df["orbit"] == "GEO"]
        meo_df = pos_df[pos_df["orbit"] == "MEO"]

        fig = go.Figure()

        # GEO satellites — blue squares
        if not geo_df.empty:
            fig.add_trace(
                go.Scattergeo(
                    lat=geo_df["lat"],
                    lon=geo_df["lon"],
                    mode="markers",
                    marker=dict(size=10, color="royalblue", symbol="square"),
                    name="GEO",
                    text=geo_df["name"],
                    customdata=geo_df[["orbit", "altitude_km", "lat", "lon"]].values,
                    hovertemplate=(
                        "<b>%{text}</b><br>"
                        "Orbit: %{customdata[0]}<br>"
                        "Altitude: %{customdata[1]} km<br>"
                        "Lat: %{customdata[2]:.2f}°<br>"
                        "Lon: %{customdata[3]:.2f}°<extra></extra>"
                    ),
                )
            )

        # MEO satellites — orange circles
        if not meo_df.empty:
            fig.add_trace(
                go.Scattergeo(
                    lat=meo_df["lat"],
                    lon=meo_df["lon"],
                    mode="markers",
                    marker=dict(size=9, color="darkorange", symbol="circle"),
                    name="MEO",
                    text=meo_df["name"],
                    customdata=meo_df[["orbit", "altitude_km", "lat", "lon"]].values,
                    hovertemplate=(
                        "<b>%{text}</b><br>"
                        "Orbit: %{customdata[0]}<br>"
                        "Altitude: %{customdata[1]} km<br>"
                        "Lat: %{customdata[2]:.2f}°<br>"
                        "Lon: %{customdata[3]:.2f}°<extra></extra>"
                    ),
                )
            )

        # Betzdorf ground station — red star
        fig.add_trace(
            go.Scattergeo(
                lat=[49.7],
                lon=[6.4],
                mode="markers",
                marker=dict(size=14, color="red", symbol="star"),
                name="Betzdorf GS",
                hovertemplate="<b>Betzdorf Ground Station</b><br>Lat: 49.7°N, Lon: 6.4°E<extra></extra>",
            )
        )

        fig.update_layout(
            geo=dict(
                showland=True,
                landcolor="rgb(230,230,230)",
                showocean=True,
                oceancolor="rgb(200,220,255)",
                showcoastlines=True,
                coastlinecolor="gray",
                projection_type="natural earth",
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(orientation="h", y=-0.05),
            height=520,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        f"Position computed from public TLE data (Celestrak GP / SGP4). "
        f"Position reflects the time of TLE fetch: {fetch_ts} UTC. "
        "Accuracy depends on TLE update cadence. "
        "GEO positions are near-constant; MEO positions change over time."
    )

# ── Tab 2: Betzdorf Look Angles ───────────────────────────────────────────────
with tab2:
    st.subheader("Betzdorf Look Angles (Alt/Az)")
    st.markdown(
        "**Ground station:** Betzdorf, Luxembourg (49.7°N, 6.4°E) | "
        "**Visibility:** El > 5°"
    )

    look_df = compute_look_angles(satellites, ts)

    if look_df.empty:
        st.warning("No look angle data available.")
    else:
        # Build display DataFrame
        display_rows = []
        for _, row in look_df.iterrows():
            orbit_badge = (
                "Near-constant (GEO)" if row["geo_flag"] else "Dynamic (MEO)"
            )
            visible_icon = "✅" if row["is_visible"] else "❌"
            display_rows.append(
                {
                    "Name": row["name"],
                    "Orbit": orbit_badge,
                    "Elevation (°)": row["elevation_deg"],
                    "Azimuth (°)": row["azimuth_deg"],
                    "Visible (El > 5°)": visible_icon,
                }
            )
        st.dataframe(pd.DataFrame(display_rows), use_container_width=True)

    st.caption(
        "Look angles computed from public TLE data (Skyfield / SGP4). "
        "'Visible' indicates El > 5° only. "
        "No link budget, margin, or frequency allocation data is included."
    )
    st.info(
        "GEO satellites maintain near-constant look angles from a fixed ground station. "
        "MEO satellites (O3b mPOWER) change position over time."
    )

# ── Tab 3: Anomaly Alert Log ──────────────────────────────────────────────────
with tab3:
    st.subheader("Anomaly Alert Log")
    st.info(
        "ℹ️ Synthetic data — workflow demo only.\n"
        "Demonstrates detection → logging → response pipeline."
    )

    if not sat_names:
        st.warning("No satellite data loaded.")
    else:
        alert_df = generate_alerts(sat_names)

        # Filters
        col_a, col_b = st.columns(2)
        with col_a:
            selected_sats = st.multiselect(
                "Filter by satellite",
                options=sorted(alert_df["satellite"].unique()),
                default=sorted(alert_df["satellite"].unique()),
            )
        with col_b:
            selected_sev = st.multiselect(
                "Filter by severity",
                options=["High", "Medium", "Low"],
                default=["High", "Medium", "Low"],
            )

        filtered = alert_df[
            alert_df["satellite"].isin(selected_sats)
            & alert_df["severity"].isin(selected_sev)
        ]

        def _sev_badge(val: str) -> str:
            colours = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
            return f"{colours.get(val, '')} {val}"

        display_alert = filtered.copy()
        display_alert["severity"] = display_alert["severity"].apply(_sev_badge)
        st.dataframe(display_alert, use_container_width=True)

# ── Tab 4: Health KPI ────────────────────────────────────────────────────────
with tab4:
    st.subheader("Satellite Health KPI")
    st.info(
        "ℹ️ Synthetic data — workflow demo only.\n"
        "Demonstrates threshold-based health scoring pipeline."
    )
    st.caption("Legend: 🟢 Green ≥ 80 · 🟡 Yellow 60–79 · 🔴 Red < 60")

    if not sat_names:
        st.warning("No satellite data loaded.")
    else:
        kpi_df = generate_health_kpi(sat_names)
        for _, row in kpi_df.iterrows():
            colour_map = {"Green": "🟢", "Yellow": "🟡", "Red": "🔴"}
            icon = colour_map.get(row["status"], "⚪")
            label = f"{icon} **{row['name']}** — {row['status']} ({row['health_score']}/100)"
            st.markdown(label)
            st.progress(int(row["health_score"]))
            if row["note"]:
                st.caption(row["note"])

# ── Tab 5: Link-quality Trend ────────────────────────────────────────────────
with tab5:
    st.subheader("Link-quality Trend")
    st.info(
        "ℹ️ Synthetic time-series — threshold alerting demo only.\n"
        "Not a measured signal metric."
    )

    if not sat_names:
        st.warning("No satellite data loaded.")
    else:
        selected_lq = st.multiselect(
            "Select satellites (max 4 recommended)",
            options=sat_names,
            default=sat_names[:4] if len(sat_names) >= 4 else sat_names,
        )

        if not selected_lq:
            st.info("Select at least one satellite to display the trend.")
        else:
            lq_df = generate_link_quality(selected_lq, hours=72)

            fig_lq = go.Figure()
            for name in selected_lq:
                sat_lq = lq_df[lq_df["name"] == name]
                fig_lq.add_trace(
                    go.Scatter(
                        x=sat_lq["timestamp"],
                        y=sat_lq["quality_score"],
                        mode="lines",
                        name=name,
                    )
                )

            # Threshold lines
            fig_lq.add_hline(
                y=30,
                line_dash="dash",
                line_color="orange",
                annotation_text="Warning (30)",
                annotation_position="bottom right",
            )
            fig_lq.add_hline(
                y=15,
                line_dash="dash",
                line_color="red",
                annotation_text="Critical (15)",
                annotation_position="bottom right",
            )

            fig_lq.update_layout(
                xaxis_title="Time (UTC)",
                yaxis_title="Quality Score (arbitrary units)",
                yaxis=dict(range=[0, 105]),
                legend=dict(orientation="h", y=-0.2),
                height=420,
                margin=dict(l=0, r=0, t=20, b=0),
            )
            st.plotly_chart(fig_lq, use_container_width=True)
