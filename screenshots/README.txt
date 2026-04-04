Screenshots — Instructions
==========================

Add screenshots here before publishing the repository.

Recommended captures:
1. tab1_orbit_map.png       — Tab 1: Global Orbit Map (all satellites + Betzdorf marker visible)
2. tab2_look_angles.png     — Tab 2: Betzdorf Look Angles table
3. tab3_alert_log.png       — Tab 3: Anomaly Alert Log (with Look Angle Deviation row visible)
4. tab4_health_kpi.png      — Tab 4: Health KPI (progress bars + Green/Yellow/Red badges)
5. tab5_link_quality.png    — Tab 5: Link-quality Trend (line chart + threshold lines)
6. banned_terms_check.png   — Terminal output of: python tools/check_banned_terms.py → ✅ No banned terms found.

How to capture:
  streamlit run app.py
  Open http://localhost:8501 in browser
  Screenshot each tab and save into this folder with the names above.

Note: screenshots/ is tracked by git (.gitkeep keeps the folder).
Remove .gitkeep after adding real screenshots.
