from typing import Dict, List, Any
from backend.parsers.models.station_models import ParsedStationModel
from backend.parsers.models.measurement_model import ParsedMeasurementModel
import logging

#================================================================
# MERGE STATIONS AND MEASUREMENTS DATA
#================================================================

def merge_stations_and_measurements(
        stations: List[ParsedStationModel], 
        measurements: List[ParsedMeasurementModel]

) -> Dict[str, Dict[str, Any]]: # Return type: 
    """
    Merges station information with their corresponding measuremnets data

    Args:
        stations List[ParsedStationModel] a list of station information from ParsedStationModel dataclass
        measurements List[ParsedMeasurementModel] a list of ParsedMeasurementModel dataclass objects

    Returns:
        Dict[str,[str,Object]] a dictionary where the key of the outer is the station_id
        and the inner dictionary has the following 'key:value' structure:
        "info": [ParsedStationModel] 
        "measurement": [ParsedMeasurementModel]
    """

    # Create a dictionary for merged data
    merged_data: Dict[str, Dict[str, Any]] = {}

    for single_station in stations: # Create a lookup for every station in stations list which contains ParsedStationModel objects for every station
        # skip entries with no station_id to satisfy type checker and avoid None keys
        if single_station.station_id is None:
            continue

        # For single_station in stations list which is made of ParsedStationModel objects
        # create a dictionary named merged_data 
        # where each key is a station_id from ParsedStationModel object,
        # value is a inner dictionary with keys "info"
        # and "measurements" fromParsedStationModel object
        # within measurements empty list
        merged_data[single_station.station_id] = {
            "info": single_station,

            # Initialize measurements as an empty list
            "measurements_list": []
        }

    # Append measurrements to coresponding station:
    # for each Measurement object in measurements list
    # check if the station_id already exists in merged_data dictionary    
    for single_measurement in measurements: 
        if single_measurement.station_id in merged_data:


            # access the merged_data dictionary with ParsedStationModel objects
            # get the station_id from every Measurement object [single_measurement.station_id]
            # access the list of measurements for that station ["measurements_list"]
            # add the current measurements to that list '.append(single_measurement)'
            merged_data[single_measurement.station_id]["measurements_list"].append(single_measurement)

        else:
            # Log warning 
            logging.warning(f"No station info found for {single_measurement.station_id}")


    return merged_data


        
