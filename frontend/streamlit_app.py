import os
import streamlit as st
from datetime import datetime
from data_handler import get_raw_data, json_to_dataframe

st.set_page_config(page_title="Zrakomer", layout="wide")
st.title("Zrakomer")
st.caption("Pregled kakovosti zraka po merilnih postajah")
st.caption(f"Deploy: {os.getenv('APP_COMMIT_SHA', 'local-dev')[:12]}")

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

if df.empty:
    st.error("Ni podatkov za prikaz. Preveri backend povezavo ali poskusi znova.")
else:
    st.success(f"Nalozenih postaj: {len(df)}")
    st.caption(f"Zadnja osvezitev: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.dataframe(df)