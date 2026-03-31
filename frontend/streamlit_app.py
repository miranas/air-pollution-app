import streamlit as st
from datetime import datetime
from data_handler import get_raw_data, json_to_dataframe
import pandas as pd
from config import THRESHOLDS

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

        </style>
        """,
        unsafe_allow_html=True,
)

st.markdown(
        f"""
        <div class="hero-card">
            <h1 class="hero-title">Zrakomer</h1>
            <p class="hero-subtitle">Pregled kakovosti zraka po merilnih postajah v realnem času</p>
        </div>
        """,
        unsafe_allow_html=True,
)

# Header actions
left, right = st.columns([4, 1])
with left:
        st.write("Prikaz zadnjih razpolozljivih meritev")
with right:
    if st.button("Osvezi podatke", use_container_width=True):
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

    pollutant = st.selectbox(
        "Razvrsti postaje po onesnazilu",
        options=["PM10", "PM2.5", "O3", "NO2", "SO2", "CO", "BENZEN"],
        index=0,
    )

    pollutant_key_map = {
        "PM10": "pm10",
        "PM2.5": "pm25",
        "O3": "o3",
        "NO2": "no2",
        "SO2": "so2",
        "CO": "co",
        "BENZEN": "benzen",
    }

    def pollutant_state(value: float | None, pollutant_name: str) -> str:
        if pd.isna(value):
            return "Ni podatka"
        key = pollutant_key_map.get(pollutant_name)
        limits = THRESHOLDS.get(key, []) if key else []
        if len(limits) < 2:
            return "Ni praga"
        if value <= limits[0]:
            return "Dobro"
        if value <= limits[1]:
            return "Zmerno"
        return "Slabo"

    def pollutant_color(value: float | None, pollutant_name: str) -> str:
        if pd.isna(value):
            return "background-color: #eef1f4; color: #5b6770;"
        key = pollutant_key_map.get(pollutant_name)
        limits = THRESHOLDS.get(key, []) if key else []
        if len(limits) < 2:
            return ""
        if value <= limits[0]:
            return "background-color: #d9f5e6; color: #0f5132;"
        if value <= limits[1]:
            return "background-color: #fff4d6; color: #7a5d00;"
        return "background-color: #ffe1df; color: #8a1f1f;"

    stations_count = len(df)
    pollutant_series = df[pollutant] if pollutant in df.columns else pd.Series(dtype=float)
    avg_selected = float(pollutant_series.mean()) if pollutant_series.notna().any() else None
    peak_station = "Ni podatka"
    peak_selected = None
    if pollutant_series.notna().any():
        idx = pollutant_series.idxmax()
        peak_station = str(idx)
        peak_selected = float(df.loc[idx, pollutant])

    c1, c2, c3 = st.columns(3)
    c1.metric("Stevilo postaj", f"{stations_count}")
    c2.metric(f"Povprecni {pollutant}", f"{avg_selected:.1f}" if avg_selected is not None else "Ni podatka")
    c3.metric(f"Najvisji {pollutant}", f"{peak_selected:.1f}" if peak_selected is not None else "Ni podatka", delta=peak_station)

    st.caption(f"Zadnja osvezitev: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    ranking_df = df.reset_index().rename(columns={"index": "Postaja"})
    if pollutant in ranking_df.columns:
        ranking_df = ranking_df.sort_values(by=pollutant, ascending=False, na_position="last")

    ranking_df[f"Stanje {pollutant}"] = ranking_df[pollutant].apply(lambda x: pollutant_state(x, pollutant))

    # Keep the table compact to avoid horizontal scrolling.
    compact_df = ranking_df[["Postaja", pollutant, f"Stanje {pollutant}"]].copy()
    compact_df.insert(0, "Rang", range(1, len(compact_df) + 1))
    compact_df[pollutant] = compact_df[pollutant].apply(
        lambda x: f"{float(x):.1f}" if pd.notna(x) else "Ni podatka"
    )

    styled_table = (
        compact_df
        .style
        .hide(axis="index")
        .set_properties(subset=["Rang"], **{"text-align": "center", "width": "70px"})
        .set_properties(subset=["Postaja"], **{"text-align": "left"})
        .set_properties(subset=[pollutant], **{"text-align": "center", "font-weight": "600"})
        .set_properties(subset=[f"Stanje {pollutant}"], **{"text-align": "center", "font-weight": "600"})
        .applymap(lambda v: pollutant_color(v, pollutant), subset=[pollutant])
        .applymap(
            lambda s: "background-color: #d9f5e6; color: #0f5132;" if s == "Dobro"
            else "background-color: #fff4d6; color: #7a5d00;" if s == "Zmerno"
            else "background-color: #ffe1df; color: #8a1f1f;" if s == "Slabo"
            else "background-color: #eef1f4; color: #5b6770;",
            subset=[f"Stanje {pollutant}"],
        )
    )

    st.subheader(f"Top postaje po: {pollutant}")
    st.table(styled_table)