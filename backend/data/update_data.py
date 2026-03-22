from backend.network.arso_client import fetch_arso_xml
from backend.parsers.station_parser import parse_stations_from_xml
from backend.parsers.measurments_parser import parse_measurements_from_xml
from backend.parsers.stations_and_measurments_merger import merge_stations_and_measurements
from backend.utils.serialization import to_serializable
from typing import Any, List, Tuple, cast
import json
from flask import current_app
import logging
logging.basicConfig(level=logging.INFO)
from backend.utils.redis import insert_merged_data_into_cache




def update_data():
    # Fetch XML from ARSO
    # Call the ARSO client and normalize possible return shapes.
    # fetch_arso_xml() may return (success, xml_content, error) or just xml_content.
    fetch_result = fetch_arso_xml()

    # Normalize fetch_arso_xml return which may be a str or a (success, xml_content, error) tuple.
    # Prefer checking for str to avoid isinstance checks against typing.Tuple in type checkers.
    if isinstance(fetch_result, str):
        # fetch_result is a plain string (XML content) — cast for the type checker.
        xml_content = cast(str, fetch_result)
        success = bool(xml_content)
        error = None if success else "Failed to fetch XML"
    else:
        try:
            success, xml_content, error = fetch_result
        except Exception:
            # Unexpected tuple shape — treat as failure.
            xml_content = None
            success = False
            error = "Unexpected fetch_arso_xml return object"

    if not success or not xml_content:
        logging.error(f"Error fetching XML: {str(error)}")
        return False
        

    station_result = parse_stations_from_xml(xml_content)
    if not station_result.success:
        logging.error(f"Error parsing stations: {station_result.error_message}")
        return False

    # parse measurements return Measurement
    measurement_result = parse_measurements_from_xml(xml_content)
    if not measurement_result.success:
        logging.error(f"Error parsing measurements: {measurement_result.error_message}")
        return False

    # merge stations and measurements
    merged_data = merge_stations_and_measurements(
        station_result.data,
        measurement_result.data)

    # save into Redis or SimpleCache
    insert_merged_data_into_cache(merged_data)

    if not merged_data:
        logging.info("No merged data available")
        return False
    else:
        # summary log
        logging.info(f"Merged data for {len(merged_data)} stations")

        # key: value iteration through merged_data as station_id as key and station_info as value
        for station_id, station_info in merged_data.items():
            logging.debug(f"Station ID: {station_id}")
            logging.debug(f"Name: {station_info['info'].station_name}")
            logging.debug(f"Measurements ({len(station_info['measurements_list'])}):")

            for m in station_info['measurements_list'][:23]:
                logging.debug(f"    {m}")
            if len(station_info['measurements_list']) > 5:
                logging.debug(f"    ...and {len(station_info['measurements_list']) - 5} more\n")
            else:
                logging.debug("")

        # Build all_parsed_data from merged_data for insertion
        all_parsed_data: List[Tuple[Any, Any]] = []

        for station_id, station_and_measuremnents_data in merged_data.items():
            station_data = station_and_measuremnents_data["info"]
            for measurement_data in station_and_measuremnents_data["measurements_list"]:
                all_parsed_data.append((station_data, measurement_data))

        # Insert into storage
        try:
            from backend.parsers.insert_data import insert_all_data
            insert_all_data(all_parsed_data)
        except Exception as e:
            logging.exception(f"Failed to insert data: {e}")
            # continue to attempt caching the merged data even if DB insert failed

        