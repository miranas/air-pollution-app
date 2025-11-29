#Slovenia air quality monitoring stations Data Module
from typing import List, Dict, Optional
import requests
from xml.etree import ElementTree as ET
import logging
import time
from utils.decorators import handle_service_exception

# Cache for stations data, loaded from API
_station_cache: Optional[List[Dict[str,str]]] = None
_cache_timestamp: Optional[float] = None
CACHE_DURATION = 3600 #1 HOUR





@handle_service_exception
def fetch_stations_from_arso() -> Optional[List[Dict[str,str]]]:
    """Fetch stataion List from ARSo API"""
    try:
        #make http request to ARSO API
        arso_stations_url = "https://www.arso.gov.si/xml/zrak/ones_zrak_urni_podatki_zadnji.xml"
        response = requests.get(arso_stations_url, timeout = 10)
        response.raise_for_status() #Raise exception if HTTP error

        #Parse XML response
        stations=[]
        #parses xml into a tree structure now root is the top-level <arsopodatki>
        root = ET.fromstring(response.content)
        
        #Iterate over each <postaja> element to extract stataions info
        for postaja in root.findall('.//postaja'):
            # Get station ID from 'sifra' attribute of postaja
            station_id = postaja.get('sifra')

            #Get station name from the child element of the <postaja>
            station_name = postaja.find('merilno_mesto').text

            if station_id and station_name: #if both exists
                #Check if station ID already exists in the list
                if not any(s['id'] == station_id for s in stations):
                    stations.append(
                        {
                            'id': station_id,
                            'name': station_name.strip()
                    }
                   )
        logging.info(f"Loaded {len(stations)} stations from ARSO API")
        return stations
    

    except requests.RequestException as e:
        logging.error(f"Failed to fetch stations from ARSO: {e} ")
        return None
    except ET.ParseError as e:
        logging.error(f"Failed to parse ARSO XML:{e}")
        return None
    


def is_cache_valid() -> bool:
    """Check if the cache is still valid."""
    if _cache_timestamp is None:
        return False
    return (time.time() - _cache_timestamp) < CACHE_DURATION

@handle_service_exception
def get_all_stations() -> List[Dict[str,str]]:
    """Get a list of all stations from cache or ARSO API"""
    global _station_cache, _cache_timestamp

    #Check if cache needs refresh
    if not is_cache_valid() or _station_cache is None:
        #Cache is invalid, refresh it from ARSO API
        fresh_stations = fetch_stations_from_arso()

        if fresh_stations: #if we got data from ARSO
            _station_cache = fresh_stations #Define the cache
            _cache_timestamp = time.time() #Update timestamp
            logging.info("Station cache refreshed from ARSO")
        else:
            #If API fails 
            logging.info("Failed to load stations from ARSO API")
            return [] #Return empty list
    return _station_cache.copy() if _station_cache else [] # Return a copy of the cached stations list
     
        



@handle_service_exception
def get_station_by_id(station_id: str):
    stations = get_all_stations() #Get dynamic data from API first
    return next((station for station in stations if station["id"] == station_id), None)


@handle_service_exception
def get_station_by_name(station_name: str):
    stations = get_all_stations()
    return next((station for station in stations if station["name"] == station_name), None)

      