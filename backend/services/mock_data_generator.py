"""Mock data generator for air quality testing  """
import random
from datetime import datetime
from typing import Dict, Any
from data.stations import get_all_stations

class MockDataGenerator:
    """Generates realistic random mock air quality data for testing purposes"""
    def __init__(self):

        self.pollutant_ranges: Dict[str, Dict[str, float]] = {             
            
            "pm2.5": {"min": 3, "max": 35, "typical": 18},
            "pm10": {"min": 5, "max": 45, "typical": 25},
            "no2": {"min": 10, "max": 60, "typical": 30},
            "o3": {"min": 20, "max": 180, "typical": 80},
            "so2": {"min": 1, "max": 20, "typical": 8},
            "co": {"min": 0.1, "max": 2.0, "typical": 0.8}            
        }

    def _get_air_quality_status(self, value: float, pollutant: str) -> str:
         """Determine air quality status based on EU tresholds"""

         thresholds: Dict[str, Dict[str, float]] = {
              
              "pm2.5": {"good": 15, "moderate": 25},
              "pm10": {"good": 20, "moderate": 50},
              "no2": {"good": 40, "moderate": 80},
              "o3": {"good": 80, "moderate": 120},
              "so2": {"good": 20, "moderate": 50},
              "co": {"good": 1.0, "moderate": 1.5}        
            
         }         
         
         if pollutant in thresholds:
              if value <= thresholds[pollutant]["good"]:
                   return "good"
              elif value <= thresholds[pollutant]["moderate"]:
                   return "moderate"
              else:
                   return "poor"
              
         return "unknown"


    def generate_pollutant_value(self, pollutant: str) -> float:
         """Generate value for specific pollutant"""
         if pollutant not in self.pollutant_ranges:
              raise ValueError(f"Unknown pollutant: {pollutant}")
                  
         ranges = self.pollutant_ranges[pollutant]  # source of ranges, Gets: {"min": 5, "max": 45, "typical": 25}
         return self._generate_realistic_value(ranges)  


    
    def _generate_realistic_value(self, ranges: Dict[str, float]) -> float: 
            
            """Generate realistic values within given ranges
            Args: ranges (Dict[str, float]): Dictionary with min, max, and typical values
            Returns: a realistic air quality measurement mock value"""

            if random.random() < 0.7:
                typical = ranges["typical"] #gets value from passed dictionary
                min_typical = typical * 0.7
                max_typical = typical * 1.3
                return round(random.uniform(min_typical, max_typical),1)
            else:
                 return round(random.uniform(ranges["min"], ranges["max"]),1)      

      
     
    def generate_all_stations_data(self, station_id:str) -> Dict[str,Any]:
         """Generate complete air quality data for a station (ALl pollutants)"""

         random.seed(hash(station_id) % 10000)

         stations = get_all_stations()
         station = next((s for s in stations if s["id"] == station_id), None)

         if station is None:
             
             return {
                  
                 "timestamp": datetime.now().isoformat(),
                 "station_id": station_id,
                 "station_name": "Unknown",
                 "measurements": {},
                 "datasource": "mock"
             }

         measurements = {}

         for pollutant in self.pollutant_ranges.keys():

             value = self.generate_pollutant_value(pollutant)

             status = self._get_air_quality_status(value, pollutant)

             measurements[pollutant] = {

                 "value": f"{value} {'μg/m³' if pollutant != 'co' else 'mg/m³'}",
                 "status": status,
                 "unit": "μg/m³" if pollutant != "co" else "mg/m³"

             }

         return {

             "timestamp": datetime.now().isoformat(),
             "station_id": station["id"],
             "station_name": station["name"],
             "measurements": measurements,
             "datasource": "mock"

         }

                            
         

              
           
   
    

   
            
    
    





                                      


        