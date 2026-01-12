from dataclasses import dataclass
from typing import Optional, Union, Dict
from datetime import datetime
from xml.etree import ElementTree
from backend.parsers.xml_utils import decode_unicode_escapes




#============================================================
# MEASUREMENT DATA MODEL
#============================================================
@dataclass
class Measurements:
    """
    This class represents air pollution measurements 
    taken for a single pollutant
    """
    station_id: str # sifra
    station_name:str #merilno_mesto
    time_from: Optional[datetime] # datum_od
    time_to: Optional[datetime] # datum_do
    co: Optional[float] = None
    o3: Optional[int] = None
    no2: Optional[int] = None
    so2: Optional[int] = None
    pm10: Optional[int] = None
    pm25: Optional[int] = None
    nox: Optional[int] = None
    benzen: Optional[float] = None   
    



    def __post_init__(self):
        """
        Validates air pollution measurements data after fetching
        """
        if not self.station_id or not str(self.station_id).strip():
            raise ValueError("Invalid station ID")
        
        self.station_name = self.station_name.strip()
        self.station_name = decode_unicode_escapes(self.station_name)
        
        
        if not self.station_name or not str(self.station_name.strip()):
            raise ValueError("Invalid station name")

        # Validate time range presence and order
        if self.time_from is None or self.time_to is None:
            raise ValueError("Missing time_from or time_to")
        if self.time_from >= self.time_to:
            raise ValueError("Time range is invalid")
        

    @classmethod
    def from_xml_element(cls, element: ElementTree.Element) -> "Measurements":
        # extract attributes
        station_id = element.get("sifra") or ""
        station_name = element.findtext("merilno_mesto") or ""
        time_from_text = element.findtext("datum_od")
        time_to_text = element.findtext("datum_do")
        co_text = element.findtext("co")
        o3_text = element.findtext("o3")
        no2_text = element.findtext("no2")
        so2_text = element.findtext("so2")
        pm25_text = element.findtext("pm2.5")
        pm10_text = element.findtext("pm10")
        benzen_text = element.findtext("benzen")
        nox_text = element.findtext("nox")


        # This helper function takes a string from XML
        # as text variable and tries to convert it to an integer
        def _to_int(text: Optional[str]) -> Optional[int]:
            if not text:
                return None
            try:
                # handles values like "<2"
                if text.strip().startswith("<"):
                    return int(float(text.strip()[1:]))                

                return int(text)
            except ValueError:
                return None

        def _to_float(text: Optional[str]) -> Optional[float]:
            if not text:
                return None
            try:
                # handles values like "<2" 
                if text.strip().startswith("<"):
                    return float(text.strip()[:1])
                return float(text)
            except ValueError:
                return None
            
        

        # Convert time string to datetime objects
        time_from = datetime.strptime(time_from_text, "%Y-%m-%d %H:%M") if time_from_text else None
        time_to = datetime.strptime(time_to_text, "%Y-%m-%d %H:%M") if time_to_text else None

        return cls(            
            station_id=station_id,
            station_name=station_name,
            time_from=time_from,
            time_to=time_to,
            co=_to_float(co_text),
            o3=_to_int(o3_text),
            no2=_to_int(no2_text),
            so2=_to_int(so2_text),
            pm25=_to_int(pm25_text),
            pm10=_to_int(pm10_text),
            benzen=_to_float(benzen_text),
            nox=_to_int(nox_text)
        )















                                 



    










    









