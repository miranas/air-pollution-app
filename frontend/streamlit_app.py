import streamlit as st
from datetime import datetime
from data_handler import get_raw_data, json_to_dataframe
import pandas as pd
from config import THRESHOLDS, WHO_THRESHOLDS

st.set_page_config(page_title="Zrakomer", layout="wide")

st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

            .stApp {
                background:
                    radial-gradient(1200px 500px at 10% -10%, rgba(0, 170, 150, 0.20), transparent 60%),
                    radial-gradient(900px 400px at 100% 0%, rgba(255, 155, 66, 0.20), transparent 60%),
                    linear-gradient(180deg, #f8fbfc 0%, #eef3f4 100%);
            }

            html, body, [class*="css"] {
                font-family: 'Space Grotesk', sans-serif;
            }

            .hero-card {
                border: 1px solid rgba(18, 52, 59, 0.12);
                border-radius: 18px;
                padding: 1rem 1.2rem;
                background: rgba(255, 255, 255, 0.78);
                backdrop-filter: blur(2px);
                box-shadow: 0 10px 24px rgba(10, 35, 40, 0.08);
            }

            .hero-title {
                margin: 0;
                letter-spacing: -0.02em;
                color: #11343b;
                font-size: 2.2rem;
                font-weight: 700;
            }

            .hero-subtitle {
                margin: 0.25rem 0 0.2rem;
                color: #33535a;
                font-size: 1rem;
            }

            /* ── Table styling ─────────────────────────────────── */
            [data-testid="stTable"] table {
                border-radius: 12px;
                overflow: hidden;
                border: none !important;
                box-shadow: 0 4px 18px rgba(10, 35, 40, 0.08);
                width: 100%;
            }
            [data-testid="stTable"] th {
                background-color: #11343b !important;
                color: #e8f4f5 !important;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 0.72rem;
                letter-spacing: 0.07em;
                padding: 0.65rem 1.1rem !important;
                border: none !important;
                position: sticky;
                top: 0;
                z-index: 2;
            }
            [data-testid="stTable"] td {
                padding: 0.48rem 1.1rem !important;
                border-bottom: 1px solid rgba(18, 52, 59, 0.07) !important;
                border-top: none !important;
                border-left: none !important;
                border-right: none !important;
                font-size: 0.92rem;
            }
            [data-testid="stTable"] tr:last-child td {
                border-bottom: none !important;
            }
            [data-testid="stTable"] tr:hover td {
                background-color: rgba(0, 170, 150, 0.045) !important;
            }
            [data-testid="stTable"] > div {
                max-height: 520px;
                overflow-y: auto;
            }

        </style>
        """,
        unsafe_allow_html=True,
)

st.markdown(
        f"""
        <div class="hero-card" style="display:flex; align-items:center; gap:1.4rem;">
            <span style="font-size:3.6rem; line-height:1; flex-shrink:0;">🇸🇮</span>
            <div style="flex:1">
                <h1 class="hero-title">Zrakomer</h1>
                <p class="hero-subtitle">Pregled kakovosti zraka po merilnih postajah v Sloveniji v realnem času</p>
            </div>
            <div style="flex-shrink:0; display:flex; flex-direction:column; align-items:center; gap:0.2rem;">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 300" width="178" height="118"
                   style="filter: drop-shadow(0 4px 10px rgba(10,35,40,0.14));">
                <defs>
                  <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#e9f6f8"/>
                    <stop offset="100%" stop-color="#d8ecf1"/>
                  </linearGradient>
                  <linearGradient id="land" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#c7e4ea"/>
                    <stop offset="100%" stop-color="#a9d1da"/>
                  </linearGradient>
                </defs>
                <rect x="4" y="4" width="452" height="292" rx="16" fill="url(#sea)" stroke="#9dc5cf"/>

                <path d="M76 196 L112 178 L159 185 L186 172 L220 176 L246 166 L283 173 L313 160 L350 164 L384 181 L391 209 L363 231 L322 237 L287 252 L244 244 L214 257 L177 248 L137 257 L96 244 L70 220 Z"
                    fill="url(#land)" stroke="#7aaab6" stroke-width="1.5"/>
                <path d="M181 79 L210 62 L241 74 L250 104 L231 124 L198 117 L178 97 Z"
                    fill="url(#land)" stroke="#7aaab6" stroke-width="1.5"/>
                <path d="M130 101 L147 89 L160 101 L157 118 L141 124 L129 113 Z"
                    fill="url(#land)" stroke="#7aaab6" stroke-width="1.5"/>
                <path d="M146 201 L165 194 L179 209 L174 230 L157 238 L143 224 Z"
                    fill="url(#land)" stroke="#7aaab6" stroke-width="1.2"/>
                <path d="M256 201 L267 194 L279 201 L283 220 L272 231 L261 219 Z"
                    fill="url(#land)" stroke="#7aaab6" stroke-width="1.2"/>

                <circle cx="265" cy="194" r="11" fill="#ff8b61" opacity="0.22"/>
                <circle cx="265" cy="194" r="7" fill="#ff6b35" opacity="0.35"/>
                <circle cx="265" cy="194" r="3.8" fill="#ff6b35" stroke="#ffffff" stroke-width="1.4"/>
                <rect x="257" y="173" width="16" height="10" rx="3" fill="#00aa96" stroke="#007a6e" stroke-width="0.8"/>
                <text x="265" y="181" text-anchor="middle" font-size="7" font-weight="700" fill="#ffffff" font-family="sans-serif">SI</text>

                <text x="228" y="286" text-anchor="middle" font-size="10" font-weight="600" fill="#2f5862" font-family="sans-serif">Evropa • Slovenija</text>
                </svg>
                <span style="font-size:0.65rem; color:#0a5c6e; font-weight:600; letter-spacing:0.05em;">SLOVENIJA</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
)

# Header actions
_, _btn_col = st.columns([6, 1])
with _btn_col:
    if st.button("Osveži", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with st.spinner("Nalagam podatke..."):
    json_data = get_raw_data()

# Convert to DataFrame and display
df = json_to_dataframe(json_data)

if "last_good_df" not in st.session_state:
    st.session_state.last_good_df = None

if not df.empty:
    st.session_state.last_good_df = df.copy()
elif st.session_state.last_good_df is not None:
    df = st.session_state.last_good_df
    st.warning("Backend trenutno ni vrnil novih podatkov. Prikazujem zadnje uspesne podatke.")

if df.empty:
    st.error("Ni podatkov za prikaz. Preveri backend povezavo ali poskusi znova.")
else:
    numeric_cols = ["PM10", "PM2.5", "O3", "NO2", "CO", "BENZEN", "SO2"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Controls row ────────────────────────────────────────────
    station_names = sorted(df.index.astype(str).tolist())
    station_filter = st.selectbox("Filtriraj po postaji", ["Vse postaje"] + station_names, index=0)

    ctrl_left, ctrl_right = st.columns([3, 1])
    with ctrl_left:
        pollutant_options = ["", "Vse postaje", "PM10", "PM2.5", "O3", "NO2", "SO2", "CO", "BENZEN"]
        pollutant = st.selectbox(
            "Razvrsti postaje po onesnažilu",
            options=pollutant_options,
            index=0,
        )
    with ctrl_right:
        use_who = st.checkbox("Priporočila Svetovne zdravstvene organizacije (WHO) 2021", value=False)

    active_thresholds = WHO_THRESHOLDS if use_who else THRESHOLDS

    pollutant_key_map = {
        "PM10": "pm10",
        "PM2.5": "pm25",
        "O3": "o3",
        "NO2": "no2",
        "SO2": "so2",
        "CO": "co",
        "BENZEN": "benzen",
    }

    def cell_color(value, col_name: str) -> str:
        v = pd.to_numeric(value, errors="coerce")
        if pd.isna(v):
            return "background-color: #eef1f4; color: #5b6770;"
        key = pollutant_key_map.get(col_name)
        limits = active_thresholds.get(key, []) if key else []
        if len(limits) < 2:
            return ""
        if v <= limits[0]:
            return "background-color: #d9f5e6; color: #0f5132;"
        if v <= limits[1]:
            return "background-color: #fff4d6; color: #7a5d00;"
        return "background-color: #ffe1df; color: #8a1f1f;"

    def state_label(value, col_name: str) -> str:
        v = pd.to_numeric(value, errors="coerce")
        if pd.isna(v):
            return "Ni podatka"
        key = pollutant_key_map.get(col_name)
        limits = active_thresholds.get(key, []) if key else []
        if len(limits) < 2:
            return "–"
        if v <= limits[0]:
            return "Dobro"
        if v <= limits[1]:
            return "Zmerno"
        return "Slabo"

    # ── Metrics ──────────────────────────────────────────────────
    stations_count = len(df)
    if pollutant in ["", "Vse postaje"]:
        st.metric("Število postaj", stations_count)
    else:
        series = df[pollutant] if pollutant in df.columns else pd.Series(dtype=float)
        avg_val = float(series.mean()) if series.notna().any() else None
        peak_val, peak_name = None, "Ni podatka"
        if series.notna().any():
            idx = series.idxmax()
            peak_name = str(idx)
            peak_val = float(df.loc[idx, pollutant])
        c1, c2, c3 = st.columns(3)
        c1.metric("Število postaj", stations_count)
        c2.metric(f"Povprečni {pollutant}", f"{avg_val:.1f}" if avg_val is not None else "Ni podatka")
        c3.metric(f"Najvišji {pollutant}", f"{peak_val:.1f}" if peak_val is not None else "Ni podatka", delta=peak_name)

    st.caption(f"Zadnja osvežitev: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ── Table ────────────────────────────────────────────────────
    ranking_df = df.reset_index().rename(columns={"index": "Postaja"})
    ranking_df["Postaja"] = ranking_df["Postaja"].astype(str)
    poll_display_cols = [c for c in ["PM10", "PM2.5", "O3", "NO2", "SO2", "CO", "BENZEN"] if c in ranking_df.columns]

    if station_filter != "Vse postaje":
        ranking_df = ranking_df[ranking_df["Postaja"] == station_filter]

    ranking_df = ranking_df.sort_values(by="Postaja", ascending=True, kind="stable")

    if pollutant not in ["", "Vse postaje"] and pollutant in ranking_df.columns:
        ranking_df[pollutant] = pd.to_numeric(ranking_df[pollutant], errors="coerce")
        ranking_df = ranking_df.sort_values(
            by=[pollutant, "Postaja"],
            ascending=[False, True],
            na_position="last",
            kind="stable",
        )

    if pollutant in ["", "Vse postaje"]:
        st.subheader("Pregled vseh postaj")
        overview_df = ranking_df[["Postaja"] + poll_display_cols].copy()
        overview_df.insert(0, "Rang", range(1, len(overview_df) + 1))
        overview_df = overview_df.reset_index(drop=True)
        for col in poll_display_cols:
            overview_df[col] = pd.to_numeric(overview_df[col], errors="coerce")
            overview_df[col] = overview_df[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "Ni podatka")
        st.dataframe(overview_df, use_container_width=True, height=520, hide_index=True)
    else:
        compact_df = ranking_df[["Postaja", pollutant]].copy()
        compact_df.insert(0, "Rang", range(1, len(compact_df) + 1))
        compact_df[pollutant] = pd.to_numeric(compact_df[pollutant], errors="coerce")
        compact_df["Stanje"] = compact_df[pollutant].apply(lambda x: state_label(x, pollutant))
        compact_df[pollutant] = compact_df[pollutant].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "Ni podatka")
        compact_df = compact_df.reset_index(drop=True)
        st.subheader(f"Postaje — {pollutant}")
        st.dataframe(compact_df, use_container_width=True, height=520, hide_index=True)