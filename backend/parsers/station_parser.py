"""
Station Parser Module
=====================
Parses only station informations from ARSO XML
and converts them into StationInfo dataclass instances
"""

from xml.etree import ElementTree as ET
import logging
from typing import List


from backend.utils.decorators import handle_exceptions, add_timing
from backend.parsers.models.station_models import StationInfo
from backend.parsers.models.parse_result import ParseResult

# =====================================================================
# XML PARSING METHODS
# ====================================================================

@handle_exceptions
@add_timing
def parse_stations_from_xml(xml_content: str) -> ParseResult: 
        
    try:
        # STEP 1: INITIAL SETUP AND LOGIC
        logging.info("Starting XML parsing for stations")
        
        # STEP 2: PARSE THE XML CONTENT, TREE IS THE ROOT ELEMENT OF THE XML PARSED DOCUMENT
        tree = ET.fromstring(xml_content.encode('utf-8'))
        
        # STEP 3: FIND ALL STATION ELEMENTS IN THE XML TREE, DESCENDATS OF THE 'postaja'                
        all_station_elements = tree.findall('.//postaja')
        logging.info(f"Found {len(all_station_elements)} in XML data")

        # STEP 4; HANDLE CASE OF NO STATIONS FOUND
        if not all_station_elements:
            logging.warning("No station elements found in XML ")
            return ParseResult(
                success=False,
                data=[],
                items_parsed=0,
                error_message="No stations found in XML data"        
            )
        
        # STEP 5: INITIALIZE COLLECTORS AND COUNTERS
        logging.info("Starting to parse individual station elements")
        
        # Empty list to collect successfully parsed stations
        all_parsed_stations: List[StationInfo] = []

        # Counter for stations that couldn't be parsed
        skipped_stations = 0

        # STEP 6: ITERATE THROUGH EACH STATION ELEMENT => all_station_elements = tree.findall('.//postaja')
        for single_station_element in all_station_elements:
            
            try:
                
                #STEP 6E: CREATE STATIONINFO OBJECT FROM STATIONINFO CLASS MODEL:
                single_parsed_station = StationInfo.from_xml_element(single_station_element)

                # STEP 6F: APPEND TO COLLECTOR LIST
                all_parsed_stations.append(single_parsed_station)
                
            
            except Exception as station_error:
                skipped_stations += 1 # Increment skipped counter
                logging.warning(f"Failed to parse station element {str(station_error)}")
                continue #Skip to the next element to prevent total failure
        

        # step 7: BUILD RESULT SUMMARY
        successfully_parsed = len(all_parsed_stations)
        total_stations_found = len(all_station_elements)

        if skipped_stations > 0:
            result_message = f"Parsed {successfully_parsed}/{total_stations_found} stations, skipped: {skipped_stations} stations"
            logging.info(result_message)
        else:
            result_message = f"Successfully parsed all {successfully_parsed} stations"
            logging.info(result_message)


        # STEP 8 RETURN SUCCESS RESULT
        return ParseResult(
            success=True,
            data=all_parsed_stations,
            items_parsed=successfully_parsed,
            error_message=result_message if skipped_stations > 0 else None

        )


    except ET.ParseError as parse_error:
        # XML structure is fundamentaly broken
        error_msg = f"Invalid XML structure: {str(parse_error)}"
        logging.error(error_msg)

        return ParseResult(
            success=False,
            data=[],
            items_parsed=0,
            error_message=error_msg
        )
    

    except UnicodeDecodeError as decode_error:
        # Character decoding problems
        error_msg = f"Character decoding problems: {str(decode_error)}"
        logging.error(error_msg)

        return ParseResult (
            success=False,
            data=[],
            items_parsed=0,
            error_message=error_msg
        )

    except Exception as unexpected_error:
        # Unexpected error (handled by decorator, but explicit for ParseResult class format)
        error_msg = f"Unexpected error during XML parsing {str(unexpected_error)}"
        logging.error(error_msg)

        return ParseResult(
            success=False,
            data=[],
            items_parsed=0,
            error_message=error_msg
        )
        



        



             


    










    



    
    

