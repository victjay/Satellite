# SES Satellite Payload Monitoring — Prototype Dashboard
## Claude Code 구현 지시서 v1.2 (최종)
##
## 변경이력 v1.1 → v1.2 (7개 수정):
## 수정1: README "real-time monitoring systems" → "monitoring dashboards and automation tools"
## 수정2: Mock TLE "..." 임의 생성 방식 제거 → 수동 커밋 절차 명시
## 수정3: fetch_timestamp 타임존 → UTC ISO-8601 고정
## 수정4: epoch 표시 기준 → 가장 최근 satellite.epoch 단일화
## 수정5: CATNR 이름 유사도 정규화 로직 명시
## 수정6: Look Angle Deviation 알람 방어 문구 추가
## 수정7: 금지어 스캐너 정규식 강화 (공백/대소문자 변형 커버)

---

## 역할 및 목적

너는 시니어 Python 엔지니어다.
아래 명세를 보고 **실제로 동작하고 Streamlit Community Cloud에 배포 가능한** 대시보드를 만든다.
이 프로젝트는 SES S.A. (Betzdorf, Luxembourg) Payload Engineer 포지션 (Req. 19358) 지원용 포트폴리오다.
지원자: YoungDae Je (youngdae-je-fpga)

---

## 절대 원칙 (위반 금지)

1. **과장 금지**: "Framework", "Real-time", "real-time", "REAL TIME", "real time", "Fleet Availability", "통신 가능", "link available" 표현 사용 금지
2. **Simulated 명시 필수**: 합성 데이터 패널에는 반드시 "(Synthetic data — workflow demo only)" 문구 포함
3. **미완성 배포 금지**: 동작하지 않는 기능은 UI에 표시하지 말 것
4. **timestamp 표기 고정**: 모든 시각 표시는 **UTC ISO-8601** 형식 고정 (예: 2026-04-04T15:20:00Z)
5. **API 실패 대비**: Celestrak 연결 실패 시 내장 Mock 데이터(GEO+MEO 2종)로 자동 전환, UI에 명시
6. **mapbox 사용 금지**: Plotly 지도는 반드시 `scatter_geo` 사용
7. **Mock TLE 임의 생성 금지**: Claude는 TLE 수치를 절대 만들어내지 않는다 (아래 절차 참고)

---

## 프로젝트 구조

```
ses-payload-monitoring-demo/
├── README.md
├── requirements.txt
├── app.py
├── modules/
│   ├── orbit.py
│   ├── visibility.py
│   ├── kpi.py
│   ├── link_quality.py
│   └── alerts.py
├── data/
│   ├── ses_satellites_sample.json
│   └── mock_tles.json          ← 수동 커밋 파일 (Claude 생성 금지)
├── tools/
│   └── check_banned_terms.py
└── screenshots/
```

---

## 데이터: ses_satellites_sample.json

```json
{
  "_comment": "SES Fleet Representative Sample — 12 satellites (GEO x6, MEO x6). Not a complete fleet list.",
  "_selection_criteria": "Operational status verifiable from Celestrak; GEO/MEO diversity; covers SES-AMERICOM and O3b mPOWER segments",
  "_catnr_note": "CATNR values are verified by code at load time. Mismatches auto-excluded with UI warning.",
  "satellites": [
    {"name": "SES-12",       "catnr": 43488, "orbit": "GEO", "slot": "95.0°E"},
    {"name": "SES-14",       "catnr": 43175, "orbit": "GEO", "slot": "47.5°W"},
    {"name": "SES-15",       "catnr": 42709, "orbit": "GEO", "slot": "129.0°W"},
    {"name": "SES-17",       "catnr": 49055, "orbit": "GEO", "slot": "67.1°W"},
    {"name": "AMC-9",        "catnr": 27566, "orbit": "GEO", "slot": "83.0°W"},
    {"name": "NSS-12",       "catnr": 32297, "orbit": "GEO", "slot": "57.0°E"},
    {"name": "O3b mPOWER 1", "catnr": 54460, "orbit": "MEO", "slot": "MEO"},
    {"name": "O3b mPOWER 2", "catnr": 54461, "orbit": "MEO", "slot": "MEO"},
    {"name": "O3b mPOWER 3", "catnr": 54462, "orbit": "MEO", "slot": "MEO"},
    {"name": "O3b mPOWER 4", "catnr": 54463, "orbit": "MEO", "slot": "MEO"},
    {"name": "O3b mPOWER 5", "catnr": 54464, "orbit": "MEO", "slot": "MEO"},
    {"name": "O3b mPOWER 6", "catnr": 54465, "orbit": "MEO", "slot": "MEO"}
  ]
}
```

---

## data/mock_tles.json — 수동 커밋 절차 (v1.2 신규)

**Claude는 이 파일의 TLE 수치를 절대 임의로 생성하지 않는다.**

처리 방법:
```
Step A: Claude는 mock_tles.json 파일을 아래 구조의 빈 템플릿으로 생성한다.
Step B: YoungDae Je가 직접 Celestrak gp.php에서 SES-14, O3b mPOWER 1의
        최신 3LE를 복사하여 수동으로 채운다.
Step C: 채워진 mock_tles.json을 Git에 커밋한다.
Step D: orbit.py의 MOCK_TLES는 이 파일을 읽어서 사용한다.
```

빈 템플릿 구조 (Claude가 생성할 형태):
```json
{
  "_instruction": "Fill line0/line1/line2 manually from Celestrak before commit. Do NOT auto-generate TLE values.",
  "_source": "https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=3LE",
  "_committed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "mock_satellites": [
    {
      "name": "SES-14 (Mock)",
      "orbit": "GEO",
      "catnr": 43175,
      "line0": "FILL_MANUALLY",
      "line1": "FILL_MANUALLY",
      "line2": "FILL_MANUALLY"
    },
    {
      "name": "O3b mPOWER 1 (Mock)",
      "orbit": "MEO",
      "catnr": 54460,
      "line0": "FILL_MANUALLY",
      "line1": "FILL_MANUALLY",
      "line2": "FILL_MANUALLY"
    }
  ]
}
```

orbit.py는 FILL_MANUALLY 값이 남아있을 경우 예외를 발생시키고
"Mock TLE not initialized — please fill data/mock_tles.json manually" 메시지를 출력한다.

---

## modules/orbit.py 명세

### CelesTrak 엔드포인트 (확정 — 변경 금지)

```
유일한 공식 엔드포인트:
https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=3LE

사용 금지:
- https://celestrak.org/satcat/tle.php?CATNR=...   ← 레거시, 금지
- 기타 모든 .txt 직접 링크                         ← 금지
```

FORMAT=3LE 응답 구조:
```
Line 0: 위성 이름 (예: SES-14)
Line 1: TLE Line 1 (69자)
Line 2: TLE Line 2 (69자)
```

### CATNR 자동 검증 게이트 (v1.1 유지 + v1.2 정규화 추가)

```python
import re

def normalize_name(s: str) -> str:
    """대문자화 + 공백/하이픈 제거. 이름 대조 전 반드시 적용."""
    return re.sub(r'[\s\-]', '', s).upper()

# 검증 흐름:
# Step A: EarthSatellite 생성 성공 여부 확인
# Step B: normalize_name(line0) vs normalize_name(json["name"]) 비교
#         → 완전 일치 또는 포함 관계이면 통과
# Step C: 실패 시 해당 위성 제외 + catnr_warnings에 추가
#         catnr_warnings 항목: {catnr, json_name, celestrak_line0, reason}
```

### epoch 표시 기준 (v1.2 단일화)

```python
# 배너에 표시할 epoch:
# 로드된 위성 중 satellite.epoch.utc_datetime() 값이
# 가장 최근인 것 1개를 UTC ISO-8601로 표시
# 형식: f"Latest TLE epoch: {epoch_dt.strftime('%Y-%m-%dT%H:%M:%SZ')} UTC"
# 위성이 없거나 epoch 파싱 실패 시: "N/A"
```

### 함수 시그니처

```python
def load_tles(satellite_list: list) -> tuple:
    """
    반환값 순서:
    [0] satellites: dict[str, EarthSatellite]  — 검증 통과 위성만
    [1] fetch_timestamp: str                   — UTC ISO-8601 (예: 2026-04-04T15:20:00Z)
    [2] latest_epoch_str: str                  — UTC ISO-8601 또는 "N/A"
    [3] is_mock_data: bool
    [4] catnr_warnings: list[dict]             — 빈 리스트 가능
    """

def compute_positions(satellites: dict, ts) -> pd.DataFrame:
    """
    컬럼: name, orbit, lat, lon, altitude_km, velocity_kms, catnr
    lat/lon 범위 강제: lat 클리핑(-90~90), lon 클리핑(-180~180)
    """
```

### 캐시 설정

```python
@st.cache_data(ttl=7200)
def load_tles(satellite_list: list):
    ...
# st.cache_data.clear() 전체 삭제 사용 금지
# Refresh 시: load_tles.clear() 만 호출
```

---

## modules/visibility.py 명세

```python
"""
Betzdorf 지상국 기준 앙각/방위각 계산
좌표: lat=49.7°N, lon=6.4°E, elevation=300m (근사값)
"""

def normalize_name(s: str) -> str:
    # orbit.py와 동일한 함수 — utils.py로 분리하거나 복사 사용

def compute_look_angles(satellites: dict, ts) -> pd.DataFrame:
    """
    컬럼: name, orbit, elevation_deg, azimuth_deg, is_visible, geo_flag

    GEO/MEO 판정 (v1.1 유지 — 측정 기반):
    - t_now = ts.now()
    - t_plus10 = ts.utc(... + 10분)
    - delta_el = |el(t_now) - el(t_plus10)|
    - delta_el < 0.1° → geo_flag = True → "Near-constant (GEO)" 배지
    - delta_el >= 0.1° → geo_flag = False → "Dynamic (MEO)" 배지

    is_visible: elevation_deg > 5.0
    """

# 금지 표현 (이 파일 어디에도 사용 금지):
# "통신 가능", "link available", "visible for communication"
# 허용 표현: "Visible (El > 5°)" 만 사용
```

---

## modules/alerts.py 명세

```python
"""
SYNTHETIC DATA ONLY
최근 24시간 기준 5~10개 합성 알람 생성
"""

# anomaly_type 허용 목록 (이 목록만 사용):
ANOMALY_TYPES = [
    "Link Quality Drop",
    "Telemetry Gap",
    "Threshold Exceeded",
    "Look Angle Deviation",   # 반드시 1개 이상 포함
    "Data Latency Spike",
]

# "Look Angle Deviation" 항목에는 반드시 아래 notes 값을 고정:
LOOK_ANGLE_DEVIATION_NOTE = (
    "Synthetic: delta elevation exceeds synthetic threshold (demo only)"
)

# 반환 DataFrame 컬럼:
# timestamp, satellite, anomaly_type, severity, status, action_taken, notes
# notes 컬럼: "Look Angle Deviation" 외 항목은 빈 문자열 허용

def generate_alerts(satellite_names: list) -> pd.DataFrame:
    ...
```

---

## modules/kpi.py 명세

```python
"""SYNTHETIC DATA ONLY"""

def generate_health_kpi(satellite_names: list) -> pd.DataFrame:
    """
    컬럼: name, health_score, status, note
    시드: hash(위성명) % 1000
    임계값: Green >= 80 / Yellow 60~79 / Red < 60
    """
```

---

## modules/link_quality.py 명세

```python
"""SYNTHETIC DATA ONLY"""

def generate_link_quality(satellite_names: list, hours: int = 72) -> pd.DataFrame:
    """
    컬럼: timestamp (UTC ISO-8601), name, quality_score, alert_level
    y축: arbitrary units (0~100)
    금지: "BER", "SNR", "Eb/N0" 등 실제 통신 지표 표현
    임계선: 30 (Warning) / 15 (Critical)
    """
```

---

## app.py 명세

### 전체 레이아웃

```python
import time
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="SES Payload Monitoring — Prototype")

st.title("SES Satellite Payload Monitoring")
st.caption("Prototype Dashboard | Real TLE look angles · Simulated telemetry workflow")

# --- 데이터 로딩 ---
satellites, fetch_ts, epoch_str, is_mock, catnr_warns = load_tles(satellite_list)

# --- 상태 배너 ---
if is_mock:
    st.warning(
        "⚠️ Mock mode: static snapshot TLE (for UI workflow only) — Celestrak unavailable"
    )
else:
    st.info(
        f"TLE fetched: {fetch_ts} UTC | Latest TLE epoch: {epoch_str} UTC"
    )

# --- CATNR 경고 (실패 위성 있을 때만) ---
if catnr_warns:
    with st.expander("⚠️ CATNR Verification Warnings (click to expand)"):
        st.dataframe(pd.DataFrame(catnr_warns))

# --- Refresh 버튼 (30초 쿨다운) ---
last_refresh = st.session_state.get("last_refresh_ts", 0)
cooldown = 30
elapsed = time.time() - last_refresh
if elapsed > cooldown:
    if st.button("🔄 Refresh TLE Data"):
        load_tles.clear()   # 함수 단위 캐시만 제거
        st.session_state["last_refresh_ts"] = time.time()
        st.rerun()
else:
    remaining = int(cooldown - elapsed)
    st.button(f"🔄 Refresh (available in {remaining}s)", disabled=True)

# --- 탭 ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌍 Global Orbit Map",
    "📡 Betzdorf Look Angles",
    "🔴 Anomaly Alert Log",
    "🟢 Health KPI",
    "📈 Link-quality Trend",
])
```

### 패널 1 — Global Orbit Map (tab1)

```python
# 지도: plotly scatter_geo (scatter_mapbox 금지)
# GEO: 파란 점(■) / MEO: 주황 점(●)
# Betzdorf 지상국: 빨간 별(★) 마커
# hover: name, orbit, altitude_km, lat, lon
# 제목: "Current Satellite Positions (Real TLE · SGP4)"
#
# 하단 caption (변경 금지):
# "Position computed from public TLE data (Celestrak GP / SGP4).
#  Position reflects the time of TLE fetch: {fetch_ts} UTC.
#  Accuracy depends on TLE update cadence.
#  GEO positions are near-constant; MEO positions change over time."
```

### 패널 2 — Betzdorf Look Angles (tab2)

```python
# 제목: "Betzdorf Look Angles (Alt/Az)"
# 부제: "Ground station: Betzdorf, Luxembourg (49.7°N, 6.4°E) | Visibility: El > 5°"
# 테이블: Name / Orbit / Elevation (°) / Azimuth (°) / Visible (✅/❌)
# Orbit 배지: GEO → "Near-constant (GEO)" / MEO → "Dynamic (MEO)"
#
# 하단 disclaimer (변경 금지):
# "Look angles computed from public TLE data (Skyfield / SGP4).
#  'Visible' indicates El > 5° only.
#  No link budget, margin, or frequency allocation data is included."
#
# 추가 설명:
# "GEO satellites maintain near-constant look angles from a fixed ground station.
#  MEO satellites (O3b mPOWER) change position over time."
```

### 패널 3 — Anomaly Alert Log (tab3)

```python
# 상단 고정 (변경 금지):
# "ℹ️ Synthetic data — workflow demo only.
#  Demonstrates detection → logging → response pipeline."
#
# 테이블: timestamp / satellite / anomaly_type / severity / status / action_taken / notes
# severity 배지: High=빨강 / Medium=노랑 / Low=초록
# 필터: 위성명 multiselect + severity 필터
```

### 패널 4 — Health KPI (tab4)

```python
# 상단 고정 (변경 금지):
# "ℹ️ Synthetic data — workflow demo only.
#  Demonstrates threshold-based health scoring pipeline."
#
# 위성별 st.progress() + 색상 배지 (Green/Yellow/Red)
# 범례: Green ≥ 80 / Yellow 60~79 / Red < 60
```

### 패널 5 — Link-quality Trend (tab5)

```python
# 상단 고정 (변경 금지):
# "ℹ️ Synthetic time-series — threshold alerting demo only.
#  Not a measured signal metric."
#
# Plotly 라인 차트: x=timestamp / y=quality_score / color=위성명
# 수평선: 30 (Warning) / 15 (Critical)
# 72시간 창 / 위성 선택 드롭다운 (최대 4개 동시 권장)
```

---

## tools/check_banned_terms.py (v1.2 정규식 강화)

```python
"""
check_banned_terms.py — v1.2
금지어 자동 스캐너 (정규식 기반, 대소문자/공백/하이픈 변형 모두 커버)
실행: python tools/check_banned_terms.py
금지어 발견 시 exit(1), 없으면 exit(0)
"""
import sys, pathlib, re

# 정규식 패턴 기반 금지어 (re.IGNORECASE 적용)
BANNED_PATTERNS = [
    r"\breal[\s\-]?time\b",          # real-time / real time / realtime / REAL TIME 모두 커버
    r"\bframework\b",
    r"\bfleet\s+availability\b",
    r"통신\s*가능",
    r"\blink\s+available\b",
    r"\bvisible\s+for\s+communication\b",
    r"\bBER\s+1e",                    # "BER 1e-12" 형태
    r"\bEb/N0\b",
]

SCAN_TARGETS = ["app.py", "modules/", "README.md", "data/"]

EXCLUDE_FILENAMES = {
    "check_banned_terms.py",
    "mock_tles.json",
}

# Prefix-based excludes for prompt/verification artifacts (by filename only)
EXCLUDE_NAME_PREFIXES = (
    "CLAUDE_CODE_PROMPT",
    "GPT_VERIFICATION",
)

# Optional: keep prompts under docs/ and exclude the whole folder from scanning
EXCLUDE_DIRNAMES = {"docs"}


def scan():
    found = []
    for target in SCAN_TARGETS:
        p = pathlib.Path(target)
        if not p.exists():
            continue
        files = list(p.rglob("*.py")) + list(p.rglob("*.md")) + list(p.rglob("*.json")) \
                if p.is_dir() else [p]
        for f in files:
            if (f.name in EXCLUDE_FILENAMES
                or any(f.name.startswith(p) for p in EXCLUDE_NAME_PREFIXES)
                or any(part in EXCLUDE_DIRNAMES for part in f.parts)):
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            for pattern in BANNED_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    found.append(f"{f}: pattern='{pattern}' → found: {matches}")
    return found

if __name__ == "__main__":
    issues = scan()
    if issues:
        print("❌ Banned terms found:")
        for i in issues:
            print(f"  {i}")
        sys.exit(1)
    else:
        print("✅ No banned terms found.")
        sys.exit(0)
```

---

## requirements.txt

```
streamlit>=1.32.0
plotly>=5.20.0
skyfield>=1.46
pandas>=2.0.0
numpy>=1.26.0
requests>=2.31.0
```

---

## README.md (v1.2 최종)

```markdown
# SES Satellite Payload Monitoring — Prototype Dashboard

> Real TLE look angles · Simulated telemetry workflow

Built by YoungDae Je as a portfolio project while applying for
Engineer, Spacecraft Subsystem, Payload at SES (Req. 19358).

## Live Demo
[Streamlit URL — to be added after deployment]

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

pip install -r requirements.txt
streamlit run app.py

## Quality Check

python tools/check_banned_terms.py
```

---

## 구현 순서

```
Step 1:  ses_satellites_sample.json 생성                                    (10분)
Step 2:  data/mock_tles.json 빈 템플릿 생성 (TLE 수치는 Claude 미기입)       (5분)
         ※ YoungDae Je가 Celestrak에서 직접 복사하여 수동으로 채운 후 커밋
Step 3:  tools/check_banned_terms.py 생성                                   (10분)
Step 4:  modules/orbit.py
         - gp.php?FORMAT=3LE 연결
         - normalize_name() 기반 CATNR 자동 검증
         - mock_tles.json 읽기 + FILL_MANUALLY 검사
         - st.cache_data(ttl=7200)
         - UTC ISO-8601 timestamp/epoch                                     (70분)
Step 5:  modules/visibility.py
         - Betzdorf look angles
         - ΔEl 기반 GEO/MEO 판정                                            (40분)
Step 6:  app.py 패널1 + 패널2 + 상태 배너 + Refresh 로직                    (60분)
Step 7:  modules/alerts.py (Look Angle Deviation notes 고정 문구 포함)       (20분)
Step 8:  modules/kpi.py                                                     (20분)
Step 9:  modules/link_quality.py                                            (20분)
Step 10: app.py 패널3 + 패널4 + 패널5 통합                                  (40분)
Step 11: check_banned_terms.py 실행 → "✅ No banned terms found." 확인      (10분)
Step 12: 전체 통합 테스트                                                   (20분)
Step 13: requirements.txt + README.md 완성                                  (20분)
Step 14: GitHub push + Streamlit Cloud 배포                                 (30분)
```

---

## 구현 중 판단 기준

| 상황 | 결정 |
|---|---|
| mock_tles.json에 FILL_MANUALLY 잔존 | 예외 발생 + "please fill mock_tles.json manually" 출력 |
| Celestrak CATNR 응답 비어있음 | CATNR mismatch 처리, UI 경고 후 해당 위성 제외 |
| normalize_name 대조 실패 | catnr_warnings에 추가, 위성 제외. 강제 포함 금지 |
| Plotly scatter_geo 느린 경우 | 마커 크기 축소, animation 제거. mapbox 전환 금지 |
| Skyfield 좌표 계산 오류 | lat/lon 클리핑 후 재시도 |
| Streamlit Cloud 배포 실패 | requirements.txt 버전 고정 후 재시도 |
| Refresh 버튼 쿨다운 중 충돌 | session_state["last_refresh_ts"] 확인 후 조건부 처리 |
| check_banned_terms 패턴 오탐 | EXCLUDE_FILES에 해당 파일 추가 후 재실행 |

---

## 최종 산출물 체크리스트

- [ ] `app.py` — 5개 탭 전부 동작
- [ ] `modules/` — 5개 모듈 import 오류 없음
- [ ] `data/ses_satellites_sample.json` — 존재
- [ ] `data/mock_tles.json` — TLE 수치 수동 입력 완료 (FILL_MANUALLY 없음)
- [ ] `tools/check_banned_terms.py` 실행 → `✅ No banned terms found.`
- [ ] `requirements.txt` — 로컬 pip install 성공
- [ ] `README.md` — Real vs Simulated 테이블 + "monitoring dashboards" 표현 확인
- [ ] Streamlit Community Cloud 배포 — 공개 URL 확보
- [ ] GitHub Public Repository — 공개 상태
- [ ] 상태 배너: fetch_timestamp + latest_epoch_str 모두 UTC ISO-8601 형식 표시
- [ ] Refresh 30초 쿨다운 동작 확인
- [ ] CATNR 자동 검증 게이트 동작 확인
- [ ] Mock fallback (GEO+MEO 2종) 동작 확인
- [ ] scatter_geo 사용 확인 (mapbox 없음)
- [ ] "Look Angle Deviation" 알람 + notes 고정 문구 확인
- [ ] check_banned_terms 스크린샷 → screenshots/ 폴더에 포함
