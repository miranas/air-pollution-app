import streamlit 
import requests
from typing import Dict, Any

BACKEND_URL = "http://46.225.15.6/api/latest:8501"

streamlit.title("Slovenia air quality measurements")

# Fetch data from the backend API
@streamlit.cache_data(ttl=300)
def get_latest_data() -> Dict[str, Any]:
    response = requests.get(BACKEND_URL)
    if response.status_code == 200:
        return response.json()
    return {"error": "No data"}

data = get_latest_data()
if not data:
    streamlit.error("No data available")
else:
    station_ids= list(data.keys())
    selected_station = streamlit.selectbox("Select a station", station_ids)

    station_info = data[selected_station]["info"]
    measurements = data[selected_station]["measurements_list"]

    streamlit.subheader(f"Merilno mesto: {station_info.get('station_name', selected_station)}")
    streamlit.write("Merilna postaja", station_info)
    streamlit.write("Podatki o zraku", measurements)
                        


