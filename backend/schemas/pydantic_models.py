from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PydanticStationInfoModel(BaseModel):
    station_id: str
    station_name: str
    latitude: Optional[float]
    longitude: Optional[float]
    d96_easting: Optional[float]
    d96_northing: Optional[float]
    elevation_meters: Optional[float]

class PydanticPollutantModel(BaseModel):
    pollutant: str
    value: Optional[float]
    measured_at: datetime

class PydanticMeasurementsModel(BaseModel):
    info: PydanticStationInfoModel # Information about a station
    measurements: List[PydanticPollutantModel] # list of measurements for many pollutants, every hour


    







