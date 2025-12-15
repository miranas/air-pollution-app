"""
ARSO XML Parser
===============
Module for parsing XML data from Slovenian Environment state Agency (ARSO).

WHAT IT DOES:
- fetches XML data from ARSO API (real-time air quality data)


"""

import requests
from xml.etree import ElementTree as ET
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass 
from utils.decorators import handle_exceptions, add_timing, handle_http_request_exception
from data.stations import decode_unicode_escapes

# import existing constants
from utils.config import  (
    ARSO_STATIONS_URL,        # "https://www.arso.gov.si/xml/zrak/ones_zrak_urni_podatki_zadnji.xml"
    REQUEST_TIMEOUT,          # 10 seconds
    
)

#=================================================================================
# XML FETCHING - Download data from ARSO
# ================================================================================

@handle_exceptions
@handle_http_request_exception
@add_timing
def fetch_arso_xml() -> Tuple[bool, Optional[str], Optional[str]]:
    
    """
       RETURNS:
            Tuple[success[bool],xml_data[str], error[str]]
            -True, <xml>..</xml> on success
            -False, None, error message on afailure    
    """

    logging.info(f"Fetching ARSO xml data from {ARSO_STATIONS_URL}")

    response = requests.get(ARSO_STATIONS_URL, timeout=REQUEST_TIMEOUT)
    response.encoding = 'utf-8'

    response.raise_for_status() #raise request exception for HTTP errors

    logging.info(f"Successfully fetched ARSO xml data Length: {len(response.text)} characters")
    
    return True, response.text, None

    




















# =================================================================================
# DATA STRUCTURES (Dataclassess) autogenerate __init__, __repr__, __eq__, __hash__
#==================================================================================


@dataclass
class StationInfo:
    
    """
    Represents information about a single air_quality monitoring station (name, id, coordinates)

    PROCESSING:
    - __post_init__() runs after __init__() object creation
    - Decodes UTF-8 escapes in name field with decode_unicode_escapes() imported method from stations.py
    - Validates station data (raises ValueError if invalid)
    - Adds computed fields
    """
            
    id: str # station ID like #E405"
    name: str # Station name like "LJ Be\u017eigrad" (will be decoded)

    def __post__init__(self):

        #Decoding UTF-8 escapes in name
        original_name = self.name # before decoding
        self.name = decode_unicode_escapes(self.name) # decode UTF-8 escapes

        if original_name != self.name:
            logging.info(f"UTF-8 decoded station name: {original_name} -> {self.name}")

        # Cleaning whitespace
        self.name = self.name.strip()





    
    

