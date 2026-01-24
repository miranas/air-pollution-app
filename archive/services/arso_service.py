#from typing import Dict, Optional, Any, List
#from datetime import datetime
#import requests
#from xml.etree import ElementTree as ET
#import time
#from services.mock_data_generator import MockDataGenerator
#from utils.decorators import handle_exceptions


class AirQualityService(MockDataGenerator):
    """Production ARSO  air quality service"""
    def __init__(self):

        super().__init__()
        self.arso_base_url = "https://www.arso.gov.si/xml/zrak/ones_zrak_urni_podatki_zadnji.xml"
        print("🇸🇮AirQualityService initaialized with ARSO data")

    def get_current_readings(self, station_id: str )-> Optional[Dict[str, Any]]:
        from data.stations import get_station_by_id_or_name

        #Check if stataion exists with the method defined in stations.py
        station = get_station_by_id_or_name(station_id)
    
        if not station:
            print(f"Station {station_id} does not exist!")
            return None
        
        print (f"station {station['name']} found!")

        # For now just return mock data while we build ARSO functionality
        return self.generate_all_stations_data(station_id)
    
    
    def test_arso_connection(self) -> Dict[str, Any]:
        """Test if we can connect to ARSO and fetch XML"""
        try:

            print(f"🌐 Testing conection to {self.arso_base_url}")
            
            start_time = time.time()
            response = requests.get(self.arso_base_url, timeout=10)
            end_time = time.time()

            if response.status_code == 200:
                print("✅ Successfully connected to ARSO!")
                print(f"Response time: {end_time - start_time}")


        except Exception as e:
            print(f"❌ Error connectiong to ARSO: {e}")
            return {"status": "failed", "error": str(e)}


        




        
        


        