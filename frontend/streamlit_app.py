import streamlit as st
from datetime import datetime
from data_handler import get_raw_data, json_to_dataframe
import pandas as pd

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
        st.write("Prikaz zadnjih razpolozljivih meritev iz backend API-ja.")
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

    stations_count = len(df)
    avg_pm10 = float(df["PM10"].mean()) if "PM10" in df.columns and df["PM10"].notna().any() else 0.0
    peak_station = "-"
    peak_pm10 = None
    if "PM10" in df.columns and df["PM10"].notna().any():
        idx = df["PM10"].idxmax()
        peak_station = str(idx)
        peak_pm10 = float(df.loc[idx, "PM10"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Stevilo postaj", f"{stations_count}")
    c2.metric("Povprecni PM10", f"{avg_pm10:.1f}")
    c3.metric("Najvisji PM10", f"{peak_pm10:.1f}" if peak_pm10 is not None else "-", delta=peak_station)

    st.caption(f"Zadnja osvezitev: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    pollutant = st.selectbox(
        "Razvrsti postaje po onesnazilu",
        options=["PM10", "PM2.5", "O3", "NO2", "SO2", "CO", "BENZEN"],
        index=0,
    )

    ranking_df = df.reset_index().rename(columns={"index": "Postaja"})
    if pollutant in ranking_df.columns:
        ranking_df = ranking_df.sort_values(by=pollutant, ascending=False, na_position="last")

    st.subheader(f"Top postaje po: {pollutant}")
    st.dataframe(
        ranking_df[["Postaja", "PM10", "PM2.5", "O3", "NO2", "SO2", "CO", "BENZEN"]],
        use_container_width=True,
        hide_index=True,
    )