from typing import Any, Dict
from backend.network.arso_client import fetch_arso_xml
from backend.parsers.station_parser import parse_stations_from_xml


def fetch_and_parse_stations() -> Dict[str, Any]:
    """Fetch ARSO XML data and parse stations"""
    try:
        success, xml_content, error = fetch_arso_xml()
        if not success or xml_content is None:
            return {
                "success": False,
                "stations": None,
                "error": f"failed to fetch ARSO XML data {error}"
            }

        parsed_stations = parse_stations_from_xml(xml_content)
        if not parsed_stations:
            return {
                "success": False,
                "stations": None,
                "error": f"Failed to parse ARSO XML data {error}"
            }
        
        return {
            "success": True,
            "stations": parsed_stations.data, #data is ParseResult class attribute
            "error": None
        }
    
    except Exception as error:
        return {
            "success": False,
            "stations": None,
            "error": f"Unexpected error during fetching and parsing {error}"
        }

        
    
if __name__ == "__main__":
    result = fetch_and_parse_stations()
    print (result)

   

