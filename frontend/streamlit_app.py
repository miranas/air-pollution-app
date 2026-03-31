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
            <span style="font-size:4.5rem; line-height:1; flex-shrink:0;">🌍</span>
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
    ctrl_left, ctrl_right = st.columns([3, 1])
    with ctrl_left:
        pollutant_options = ["Vse postaje", "PM10", "PM2.5", "O3", "NO2", "SO2", "CO", "BENZEN"]
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
    if pollutant == "Vse postaje":
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
    poll_display_cols = [c for c in ["PM10", "PM2.5", "O3", "NO2", "SO2", "CO", "BENZEN"] if c in ranking_df.columns]

    if pollutant == "Vse postaje":
        st.subheader("Pregled vseh postaj")
        overview_df = ranking_df[["Postaja"] + poll_display_cols].copy()
        for col in poll_display_cols:
            overview_df[col] = pd.to_numeric(overview_df[col], errors="coerce")
        fmt = {c: (lambda x, _c=c: f"{x:.1f}" if pd.notna(x) else "Ni podatka") for c in poll_display_cols}
        overview_df.insert(0, "Rang", range(1, len(overview_df) + 1))
        styled = (
            overview_df.style
            .hide(axis="index")
            .format(fmt, na_rep="Ni podatka")
            .set_properties(subset=["Rang"], **{"text-align": "center", "color": "#5b6770"})
            .applymap(lambda _: "background-color: #d6f0ee; color: #0a5c6e; font-weight: 600;", subset=["Postaja"])
        )
        for col in poll_display_cols:
            styled = styled.applymap(lambda v, _c=col: cell_color(v, _c), subset=[col])
        st.table(styled)
    else:
        if pollutant in ranking_df.columns:
            ranking_df = ranking_df.sort_values(by=pollutant, ascending=False, na_position="last")
        compact_df = ranking_df[["Postaja", pollutant]].copy()
        compact_df.insert(0, "Rang", range(1, len(compact_df) + 1))
        compact_df[pollutant] = pd.to_numeric(compact_df[pollutant], errors="coerce")
        compact_df["Stanje"] = compact_df[pollutant].apply(lambda x: state_label(x, pollutant))

        styled_table = (
            compact_df
            .style
            .hide(axis="index")
            .set_properties(subset=["Rang"], **{"text-align": "center", "color": "#5b6770"})
            .set_properties(subset=["Postaja"], **{"text-align": "left"})
            .set_properties(subset=[pollutant], **{"text-align": "center", "font-weight": "600"})
            .set_properties(subset=["Stanje"], **{"text-align": "center", "font-weight": "600"})
            .applymap(lambda _: "background-color: #d6f0ee; color: #0a5c6e; font-weight: 600;", subset=["Postaja"])
            .format({pollutant: lambda x: f"{x:.1f}" if pd.notna(x) else "Ni podatka"}, na_rep="Ni podatka")
            .applymap(lambda v: cell_color(v, pollutant), subset=[pollutant])
            .applymap(
                lambda s: "background-color: #d9f5e6; color: #0f5132;" if s == "Dobro"
                else "background-color: #fff4d6; color: #7a5d00;" if s == "Zmerno"
                else "background-color: #ffe1df; color: #8a1f1f;" if s == "Slabo"
                else "background-color: #eef1f4; color: #5b6770;",
                subset=["Stanje"],
            )
        )
        st.subheader(f"Postaje — {pollutant}")
        st.table(styled_table)