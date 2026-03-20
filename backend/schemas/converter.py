from backend.schemas.pydantic_models import PydanticStationInfoModel, PydanticPollutantModel, PydanticMeasurementsModel
from backend.parsers.station_parser import parse_stations_from_xml
from backend.parsers.measurments_parser import parse_measurements_from_xml
from backend.parsers.stations_and_measurments_merger import merge_stations_and_measurements
from backend.network.arso_client import fetch_arso_xml
from typing import Dict, List
import json

"""Convert parsed data models to Pydantic models."""


def convert_parsed_data_to_pydantic() -> Dict[str, PydanticMeasurementsModel]:

    # Fetch XML from ARSO client and ensure it's a string before parsing
    success, xml_content, error = fetch_arso_xml()
    if not success or xml_content is None:
        raise ValueError(f"Failed to fetch ARSO XML: {error}")    
    
    
    # Get stations 
    stations_parse_result = parse_stations_from_xml(xml_content)
    if not stations_parse_result:
        raise ValueError("Failed to parse station data from XML.") 
    stations = stations_parse_result.data # List of ParsedStationModel objects
  
   
    # Get measurements
    measurements_parse_result = parse_measurements_from_xml(xml_content)
    if not measurements_parse_result:
        raise ValueError(" Failed to parse measurement data from XML.")
    measurements = measurements_parse_result.data # List of ParsedMeasurementModel objects
    

    # Merge stations and measurements
    merged = merge_stations_and_measurements(stations, measurements)   
        

    # Create Pydantic models for each station and its measurements
    pydantic_models: Dict[str, PydanticMeasurementsModel] = {}
    for station_id, merged_data in merged.items():
        
        # Convert station info to Pydantic model
        station_info = PydanticStationInfoModel(**merged_data["info"].__dict__)  
        
        # Create a list to collect pollutant measurements for each pollutant for each station
        station_measurements: List[PydanticPollutantModel] = []

        # Iterate over measurements for the station (use .get to avoid KeyError)
        for m in merged_data["measurements_list"]:
            # require a valid measurement timestamp before creating a PydanticPollutantModel
            if m.time_to is None:
                continue

            for pollutant_name in ["co", "o3", "no2", "so2", "pm10", "pm25", "nox", "benzen"]:
                value = getattr(m, pollutant_name)
                if value is not None:
                    station_measurements.append(
                        PydanticPollutantModel(
                            pollutant=pollutant_name,
                            value=value,
                            measured_at=m.time_to
                        )
                    )

        # Create a PydanticMeasurementsModel instance for the current station and its measurements, and store it in the pydantic_models dictionary with station_id as the key
        pydantic_models[station_id] = PydanticMeasurementsModel(
            info=station_info,
            measurements=station_measurements
        ) 

    return pydantic_models



# ======== for testing purposes only =================================================

if __name__== "__main__":
    models = convert_parsed_data_to_pydantic()
    json_output = {k: v.model_dump() for k, v in models.items()}
    print(json.dumps(json_output, indent=2, default=str, ensure_ascii=False))
       
    
