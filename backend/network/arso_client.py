from utils.decorators import handle_exceptions, add_timing, handle_http_request_exception
from typing import Tuple, Optional
import requests
import logging



# import existing constants
from backend.network.config import  (
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
