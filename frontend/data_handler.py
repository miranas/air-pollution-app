import json
from urllib import response
import requests
import pandas as pd
from config import BACKEND_URL
from typing import Dict, Any, List
import streamlit


@streamlit.cache_data(ttl=3600)
def get_raw_data() -> Dict[str, Any]:
    try:
        response = requests.get(BACKEND_URL, timeout=5)
        print("DEBUG status:", response.status_code)
        print("DEBUG text:", response.text[:200])  # prvih 200 znakov
        # get json packet of latest fetched and parsed data
        return response.json()
    except requests.RequestException:
        return {}
    

def json_to_dataframe(json_data: Dict[str,Any]) -> pd.DataFrame:
    if not json_data:
        print("No valid data received from backend.")
        return pd.DataFrame()  # Return empty DataFrame if no data
    
    # initialize a list to hold the rows
    rows: List[Dict[str, Any]] = []

    for key, content in json_data.items():
        print(f"{key}: {type(content)}")

        if isinstance(content, str):
            try:
                content = json.loads(content)
            except Exception as e:
                print(f"Error parsing content for key {key}: {e}")
                continue  # skip this entry if parsing fails
        
        if content.get('measurements_list') and len(content['measurements_list']) > 0:
            info = content.get('info', {})
            measurements = content.get('measurements_list', [])

            if measurements:
                measurement = measurements[0]  # get the latest measurements
                
                row = {            

                    "Postaja": info.get("station_name"),
                    "Lat": info.get("latitude"),
                    "Lon": info.get("longitude"),
                    "PM10": measurement.get("pm10"),
                    "PM2.5": measurement.get("pm25"),
                    "O3": measurement.get("o3"),
                    "NO2": measurement.get("nox"),
                    "CO": measurement.get("co"),
                    "BENZEN": measurement.get("benzen"),
                    "SO2": measurement.get("so2")                
                }

                rows.append(row)

    df = pd.DataFrame(rows)

    if not df.empty:
        df.set_index("Postaja", inplace=True)
    return df


json_data = get_raw_data()
df = json_to_dataframe(json_data)


print(type(json_data))
print(json_data)




"""
Pythonic way

def process_to_dataframe(json_data: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "station_id": sid, 
            **content['info'],  # Unpack from 'info'(name, lat, lon)
            **content['measurements_list'][0] # Unpack from measurements(pm10, no2...)
        }
        for sid, content in json_data.items() 
        if content.get('measurements_list')
    ])
"""
        