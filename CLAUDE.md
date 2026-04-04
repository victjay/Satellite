# Project Continuity Rules (SES Payload Monitoring — Prototype Dashboard)

This repository is a portfolio project for:
- Company: SES S.A. (Betzdorf, Luxembourg)
- Role: Engineer, Spacecraft Subsystem, Payload (Req. 19358)

## Single Source of Truth
Follow **CLAUDE_CODE_PROMPT_v1_2_patched3.md** as the authoritative specification.
If anything conflicts, the prompt spec wins.

## Non‑negotiable rules (must always hold)
- Do **NOT** invent any TLE values. Mock TLE data must be manually filled by the user in `data/mock_tles.json`.
- Use **only** this CelesTrak endpoint: `gp.php?CATNR={catnr}&FORMAT=3LE`.
- All timestamps must be **UTC ISO‑8601** (e.g., `2026-04-04T15:20:00Z`).
- Plotly map must use `scatter_geo` only (no mapbox).
- Maintain the Real vs Simulated boundary:
  - Panels 1/2 are based on public TLE geometry.
  - Panels 3/4/5 are synthetic workflow demo only and must show the fixed disclaimer text.
- Keep module function signatures and DataFrame column contracts exactly as specified.
- Always run:
  - `python tools/check_banned_terms.py`
  - `streamlit run app.py`
  before finalizing.

## Two‑run workflow
- Run 1: build scaffold + real-data panels + create mock template, then STOP for human action.
- Human action: fill `data/mock_tles.json` (replace `FILL_MANUALLY`), commit.
- Run 2: complete synthetic panels, integrate all tabs, final polish, checks, deployment readiness.

