"""
Slovenia air quality monitoring Data application
This application provides data access ARSO XML API(Agencija republike Slovenije za okolje -
Slovene national environment agency). Data is fetched hourly from the ARSO servers, 
parsed, and cached for efficient access. 

Author: Miran Asanin
Version: 1.0
Last updated: December 2025
"""


from typing import List, Dict, Optional
import requests
from xml.etree import ElementTree as ET
import logging
import time
import re
import codecs
from utils.decorators import handle_service_exception

 

# Configuration constants
ARSO_STATIONS_URL = "https://www.arso.gov.si/xml/zrak/ones_zrak_urni_podatki_zadnji.xml"
CACHE_DURATION = 3600 # 1 hour in seconds
REQUEST_TIMEOUT = 10 # seconds



# Cache for stations data, loaded from API
_station_cache: Optional[List[Dict[str,str]]] = None
_cache_timestamp: Optional[float] = None


# Function to decode Unicode escape sequencec -> UTF-8  
def decode_unicode_escapes(text: str) -> str:
    """
    Decode Unicode escape sequences (\\uXXXX) to proper UTF-8
    
    Args:
        text(str): Input string potentialy Unicode escape sequences
    
    Returns:
        str: Decoded text with proper UTF-8 characters
    
    Example:
        input: "LJ Be\u017eigrad"
        output: "LJ Bežigrad"
    """

    #Check for empty input
    if not text:
        return text
    try:
        print(f"DEBUG: Input: {repr(text)}")  # Debug line
        
        # Method 1: Try direct codecs decode  literal \uXXXX
        if '\\u' in text: # Check for literal \u in the string
            try:
                decoded = codecs.decode(text, 'unicode_escape')
                print(f"DEBUG: Codecs decode result: {repr(decoded)}")
                return decoded
            
            except Exception as e:
                print(f"DEBUG: Codecs decode failed: {e}")
        
                # Method 2: Manual regex replacement for Unicode escapes
                def replace_unicode(match):
                    """Convert unicode escape to character"""
                    code_point = int(match.group(1), 16) # match extracts hex string and converts hex to int, group(1) means first capture group of signs after \u
                    return chr(code_point) # Convert int code_point to character
                
                
                decoded = re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, text)
                print(f"DEBUG: Regex decode result: {repr(decoded)}")
                return decoded
            
        print(f"DEBUG: No escapes found: {repr(text)}")
        return text          
            
           
    except Exception as e:
        logging.warning(f"Failed to decode Unicode escapes in: {text} - Error: {e}")
        # Ensure a string is returned on all code paths
        return text
    


@handle_service_exception
def fetch_stations_from_arso() -> Optional[List[Dict[str,str]]]:
    """Fetch station List from ARSO API"""
    try:
        #make http request to ARSO API
        response = requests.get(ARSO_STATIONS_URL, timeout = 10)
        response.raise_for_status() #Raise exception if HTTP error

        response.encoding = 'utf-8'
        
        #Parse XML response 
        stations: List[Dict[str, str]] = []
        #parses xml into a tree structure now defined as 'tree' variable is the top-level <arsopodatki>
        tree = ET.fromstring(response.text.encode('utf-8'))#content holds the raw bytes of the response body
        
        #Iterate over each <> element to extract stations info
        for postaja in tree.findall('.//postaja'):
            # Get station ID from 'sifra' attribute of postaja
            station_id = postaja.get('sifra')

            #Get station name from the child element of the <postaja>
            station_name = postaja.findtext('merilno_mesto')
            if station_name is not None:
                station_name = station_name.strip()
                station_name = decode_unicode_escapes(station_name)

            if station_id and station_name: #if both exists
                #Check if station ID already exists in the list
                if not any(s['id'] == station_id for s in stations):
                    stations.append(
                        {
                            'id': station_id,
                            'name': station_name
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



# Single function to get station by id or name
@handle_service_exception
def get_station_by_id_or_name(station_id: Optional[str] = None, station_name: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Get station by id or name with one single function
    """    
    # Call the fetch function and annotate the result for proper typing
    stations: List[Dict[str, str]] = get_all_stations()  # single data fetch
    if station_id:
        return next((station for station in stations if station["id"] == station_id), None)
    elif station_name:
        return next((station for station in stations if station["name"] == station_name), None)
    
    return None        


   
