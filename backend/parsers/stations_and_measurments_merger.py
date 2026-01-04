from typing import Dict, List, Any
from backend.parsers.models.station_models import StationInfo
from backend.parsers.models.measurement_model import Measurement
import logging

#================================================================
# MERGE STATIONS AND MEASUREMENTS DATA
#================================================================

def merge_stations_and_measurements(
        stations: List[StationInfo], 
        measurements: List[Measurement]

) -> Dict[str, Dict[str, Any]]: # Return type: 
    """
    Merges station information with their corresponding measuremnets data

    Args:
        stations List[StationInfo] a list of station information from StationInfo dataclass
        measurements List[Measurement] a list of measurements data

    Returns:
        Dict[str,[str,Object]] a dictionary where the key of the outer is the station_id
        and the inner dictionary has the following key:value structure:
        "info": [StationInfo] 
        "measurement": [Measurement]
    """

    # Create a dictionary for merged data
    merged_data: Dict[str, Dict[str, Any]] = {}
    
    for single_station in stations: # Create a lookup for every station in stations list which contains StationInfo objects for every station
        # skip entries with no station_id to satisfy type checker and avoid None keys
        if single_station.station_id is None:
            continue

        merged_data[single_station.station_id] = {
            "info": StationInfo(
                # Only for id and name attributes of StationInfo object
                station_id=single_station.station_id,
                station_name=single_station.station_name,
            ),

            # Initialize measurements as an empty list
            "measurements_list": []
        }

    # Append measurrements to coresponding station
    for single_measurement in measurements: # for every Measurement object in Measuremnts list
        if single_measurement.station_id in merged_data:
            merged_data[single_measurement.station_id]["measurements_list"].append(single_measurement)

        else:
            # Log warning 
            logging.warning(f"No station info found for {single_measurement.station_id}")


    return merged_data


        
    if __name__ == "__main__":
        merged = merge_stations_and_measurements(stations, measurements)
        print(merged)
