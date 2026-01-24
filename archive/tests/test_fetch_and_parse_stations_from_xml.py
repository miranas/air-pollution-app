import pytest
from backend.services.station_service import fetch_and_parse_stations

def test_fetch_and_parse_stations_from_xml():
    result = fetch_and_parse_stations()
    

    
