# SES Satellite Payload Monitoring — Prototype Dashboard

> Real TLE look angles · Simulated telemetry workflow

Built by YoungDae Je as a portfolio project while applying for
Engineer, Spacecraft Subsystem, Payload at SES (Req. 19358).

## Live Demo
https://satellite-ses-demo.streamlit.app/

## What's Real vs Simulated

| Feature | Data Type | Source |
|---|---|---|
| Satellite positions (Global Map) | **Real** | Celestrak GP / SGP4 |
| Betzdorf look angles (Alt/Az) | **Real** | Computed from TLE + ground station coordinates |
| Health KPI scores | Simulated | Synthetic — workflow demo only |
| Link-quality trends | Simulated | Synthetic — workflow demo only |
| Anomaly alert log | Simulated | Synthetic — workflow demo only |

## Limitations

- TLE/SGP4 accuracy depends on update cadence and satellite maneuvers
- Position reflects the time of TLE fetch; page refresh updates to latest data
- Look angles indicate geometric visibility only (El > 5°); no link budget or margin data
- All health/link/alert metrics are synthetic and do not represent SES operational data
- Satellite list is a representative sample (12 satellites); not a complete SES fleet
- CATNR values are verified automatically at load time; mismatches are excluded with UI warning

## Satellite Sample List

12 satellites selected for orbital diversity (GEO/MEO coverage):
- GEO (6): SES-12, SES-14, SES-15, SES-17, AMC-9, NSS-12
- MEO (6): O3b mPOWER 1–6

Selection criteria: publicly verifiable via Celestrak GP;
covers GEO and MEO orbit regimes;
represents SES-AMERICOM and O3b mPOWER segments.

## Why I Built This

My background is FPGA/SoC verification and monitoring dashboards
and automation tools (Samsung Electronics, ~12 years).
I have no direct satellite payload experience.

This dashboard demonstrates:
1. I can work with real orbital data (TLE/SGP4/Skyfield)
2. I can design a monitoring → alerting → response pipeline
3. I can build and deploy Python tools quickly

If SES provides actual telemetry data, the KPI/alert/trend modules
can connect to real data sources by replacing the ingestion layer only.

## Tech Stack

Python | Streamlit | Plotly | Skyfield | Celestrak GP

## How to Run Locally

```
pip install -r requirements.txt
streamlit run app.py
```

## TLE Data Pipeline

Satellite TLE data is updated daily via GitHub Actions (UTC 02:00).
The workflow fetches fresh TLE from Celestrak GP and commits
data/tle_snapshot.json. Streamlit Cloud reads this file directly,
avoiding outbound connection restrictions.

To force an update: Actions → update_tle_snapshot → Run workflow
Note: Do not run more frequently than every 2 hours (Celestrak policy).

Current satellite list uses 5-digit NORAD IDs.
If Celestrak transitions to 6-digit IDs or OMM format,
the snapshot schema will require review.

## Quality Check

```
python tools/check_banned_terms.py
```
