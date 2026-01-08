"""
Measurements parser module
==========================
Parses measurements data from ARSO XML and converts
them to Measurement dataclass instances 
"""
from xml.etree import ElementTree as ET
from typing import List
import logging
from datetime import datetime
from backend.parsers.models.measurement_model import Measurements
from backend.parsers.models.parse_result import ParseResult

# ===============================================================
# PARSING METHODS
# ===============================================================

def parse_measurements_from_xml(xml_content: str) -> ParseResult
    try:
        logging.info("Starting XML parsing for measurements")
        
        tree = ET.fromstring(xml_content.encode('utf-8'))

        all_measurement_elements = tree.findall('.//postaja')
        logging.info(f"Found {len(all_measurement_elements)} measurement elements in XML data")

        if not all_measurement_elements:
            logging.warning("No measurement entries found in XML data")
            return ParseResult(
                success=False,
                data=[],
                items_parsed= 0
                error_message="No measurements found"
            )
        
        # Create a list of parsed measurements
        all_parsed_measurements: List[Measurements] = []

        skipped_elements = 0

        # Parse each measurement element with from_xml_element method
        # of the Measurements class model
        for single_element in all_measurement_elements:
            try:
                single_element_measurement = Measurements.from_xml_element(single_element)
                all_parsed_measurements.append(single_element_measurement)
                
            except Exception as e:
                skipped_elements +=1
                logging.warning(f"Failed toparse measurement element{str(e)}")
                continue

        # Statistics about parsing operation 
        # and log result of the parsing operation        
        successfully_parsed_count = len(all_parsed_measurements)
        total_elements_found = len(all_measurement_elements)

        if skipped_elements > 0:
            result_message = f"Parsed {successfully_parsed_count}/{total_elements_found} measurements successfully, skipped {skipped_elements}."
            logging.info(result_message)
        else:
            result_message = f"Successfully parsed all{successfully_parsed_count} elements"
           
            logging.info(result_message)

        return ParseResult(
            success=True,
            data=all_parsed_measurements,
            items_parsed=successfully_parsed_count,
            error_message=result_message if skipped_elements > 0 else None
        )
    
    except ET.ParseError as parse_error:
        error_msg = f"Invalid XML structure {str(parse_error)}"
        logging.error(error_msg)
        return ParseResult(
            success=False,
            data=[],
            items_parsed=0,
            error_message=error_msg
        )
    
    except UnicodeDecodeError as decode_error:
        error_msg = f"Character decoding problems {str(decode_error)}"
        logging.error(error_msg)
        return ParseResult(
            success=False,
            data=[],
            items_parsed=0,
            error_message=error_msg
        )
    
    except Exception as unexpected_error:
        error_msg = f" Unexpected error during XML parsing {str(unexpected_error)}"
        logging.error(error_msg)
        return ParseResult(
            success=False,
            data=[],
            items_parsed=0,
            error_message=error_msg
        )
            


    
    


