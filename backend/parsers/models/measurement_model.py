from dataclasses import dataclass
from typing import Optional, Union
from datetime import datetime


#============================================================
# MEASUREMENT DATA MODEL
#============================================================
@dataclass
class Measurement:
    """
    Represents air pollution measurements taken for a single station
    """
    station_id: str
    time_from: datetime
    time_to: datetime
    co: Optional[int] = None
    o3: Optional[int] = None
    no2: Optional[int] = None
    so2: Optional[int] = None
    pm10: Optional[int] = None
    pm2_5: Optional[int] = None
    benzen: Optional[float] = None


    def __post_init__(self):
        """
        Validates air pollution measurements data after fetching
        """
        if not self.station_id or not str(self.station_id).strip():
            raise ValueError("Invalid station ID")

        # Validate time range
        if self.time_from >= self.time_to:
            raise ValueError("Time range is invalid")

        # Validate pollutant values: if provided they must be numbers and non-negative
        for pollutant, value in {
            "CO": self.co,
            "O3": self.o3,
            "NO2": self.no2,
            "SO2": self.so2,
            "PM10": self.pm10,
            "PM2_5": self.pm2_5,
            "BENZEN": self.benzen
        }.items():            

            # skip missing values
            if value is None:
                continue

            # ensure numeric type
            if not isinstance(value, (int, float)):
                raise TypeError(f"{pollutant} value must be a number, got {type(value).__name__}")

            # ensure non-negative measurements
            if value < 0:
                raise ValueError(f"{pollutant} value cannot be negative")
            
            try:
                # set the correct type for each pollutant
                if pollutant == "benzen":
                    setattr(self, pollutant, float(value))
                else:
                    setattr(self, pollutant, int(value))                

            except Exception:
                setattr(self,pollutant, None) # Skip invalid values
            




    









