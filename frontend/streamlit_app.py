import streamlit as st
from data_handler import get_raw_data, json_to_dataframe

st.title("Zrakomer")

# Get data from backend
json_data = get_raw_data()
st.write("DEBUG: Podatki iz backend-a:")
st.json(json_data)

# Convert to DataFrame and display
df = json_to_dataframe(json_data)
if df.empty:
    st.error("Ni podatkov za prikaz.")
else:
    st.dataframe(df)