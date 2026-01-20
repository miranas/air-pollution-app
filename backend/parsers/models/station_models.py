from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any, Dict
from datetime import datetime
from xml.etree import ElementTree
from backend.parsers.xml_utils import decode_unicode_escapes


#=============================================================================
# ARSO METADATA FROM ROOT ELEMENT
#=============================================================================


@dataclass
class ARSOMetadata:
    """
    Metadata from the root ARSO XML document
    """
    # CLASS FIELD DEFINITIONS (what every ARSOMetadata object has)
    version: Optional[str] = None   # <verzija> attribute
    source: Optional[str] = None    # <vir> element
    suggested_fetch_time: Optional[str] = None # <predlagan_zajem> element
    suggested_update_fetch_interval: Optional[str] = None # <predlagan_zajem_perioda> element
    preparation_timestamp: Optional[datetime] = None # <datum_priprave> element


    def __post_init__(self):
        """
        VALIDATES AND CLEAN meatadata after object creation

        This runs AUTOMATICALLY after any ARSOMetadata object is created,
        whether from from_xml_root or direct instantiation."""

        # Clean version string (remove extra whitespaces)
        if self.version:
            self.version = self.version.strip()
        # Decode unicode escapes in source string and clean it from whitespaces
        if self.source:
            self.source = self.source.strip()
            self.source = decode_unicode_escapes(self.source)
        
        # Clean suggested fetch time
        if self.suggested_fetch_time:
            self.suggested_fetch_time = self.suggested_fetch_time.strip()

        # Clean suggested update fetch interval and decode it
        if self.suggested_update_fetch_interval:
            self.suggested_update_fetch_interval = self.suggested_update_fetch_interval.strip()
            self.suggested_update_fetch_interval = decode_unicode_escapes(self.suggested_update_fetch_interval)
        
           
    @classmethod
    def from_xml_root(cls, root_element: ElementTree.Element) -> ARSOMetadata:
        """
        Extract ARSO metadata from root XML element
        and returns ARSOMetadata class instance

        Args:
            root_element: Root <arsopodatki> element  

        Returns:
            ARSOmetadata class instance with extracted metadata
            from the root element

        """
        # LOCAL VARIABLES (temporary extraction from XML)
        version = root_element.get('verzija')  # Extracts version from XML attribute
        source = root_element.findtext('vir')  # Extracts source from XML element <vir>
        suggested_fetch_time = root_element.findtext('predlagan_zajem')  #  Extracts  from XML element <predlagan_zajem>
        suggested_update_fetch_interval = root_element.findtext('predlagan_zajem_perioda')
        preparation_timestamp = root_element.findtext('datum_priprave') or None

        if preparation_timestamp is not None:
            try:
                # Convert STRING to DATETIME object with proper format strptime
                preparation_timestamp = datetime.strptime(preparation_timestamp, "%d-%m-%Y @ %H:%M")
            except ValueError:
                # If the string doesn't match our expected format, keep as None
                preparation_timestamp = None

        # CREATE and RETURN new instance of the class using extracted data
        # These are local variables being parse to CLASS FIELD definitions
        return cls(
            version=version,
            source=source,
            suggested_fetch_time=suggested_fetch_time,
            suggested_update_fetch_interval=suggested_update_fetch_interval,
            preparation_timestamp=preparation_timestamp,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """ Convert ARSO metadata to dictionary for JSON serialization
            Class fields values are mapped to dictionary keys/value """
        return {
            'version': self.version,  
            'source': self.source,
            'suggested_fetch_time': self.suggested_fetch_time,
            'suggested_update_fetch_interval': self.suggested_update_fetch_interval,
            'preparation_timestamp': self.preparation_timestamp.isoformat() if self.preparation_timestamp else None

            }
    
#================================================================================
# ARSO METADATA-STATION INFORMATION
#===============================================================================
                                                     
@dataclass
class ParsedStationModel:
    """
    This class focuses ONLY on ARSO station metadata and not measurements.
    Measurements are handled separately in the measurements module.
    """

    # Required fields
    station_id: Optional[str] = None # sifra
    station_name: Optional[str] = None # merilno_mesto (from child element)

    # WGS coordinates (international standard for GPS)
    latitude: Optional[float] = None   #wgs84_sirina
    longitude: Optional[float] = None  #wgs84 dolžina

    # Slovenian national coordinates (D96/TM)
    d96_easting: Optional[float] = None  # d96_e
    d96_northing: Optional[float] = None # d96_n

    # Elevation above see level height
    elevation_meters: Optional[int] = None  # nadm_visina


    def __post_init__(self):
        """
        Validate and clean station data after object creation

        This runs AUTOMATICALY after StationInfo object is created,
        no matter how it was created 
        """
        # Validation of id
        if not self.station_id or not str(self.station_id).strip():
            raise ValueError("Station ID is empty")
        self.station_id = str(self.station_id.strip())
        
        # Validation of name
        if not self.station_name or not str(self.station_name).strip():
            raise ValueError("Station name is empty!")
        self.station_name = self.station_name.strip()
        self.station_name = decode_unicode_escapes(self.station_name)
        
        
        
                

    @classmethod 
    def from_xml_element(cls, element: ElementTree.Element) -> "ParsedStationModel":
        """
        Extract XML data from <postaja> element
        Args:
            element: XML element <postaja> and its attributes representing a single station
        Returns:
            ARSO StationInfo class instance with extracted data
        """
        station_id = element.get("sifra")
        station_name = element.findtext("merilno_mesto") #child element in the <postaja> XML structure
        lat_str = element.get("wgs84_sirina")
        lon_str = element.get("wgs84_dolzina")
        d96_e_str = element.get("d96_e")
        d96_n_str = element.get("d96_n")
        elev_str = element.get("nadm_visina")

        # Convert string values to proper numeric types for typing safety.
        latitude: Optional[float] = None
        if lat_str is not None and str(lat_str).strip() != "":
            try:
                latitude = float(lat_str)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid latitude value: {lat_str}")

        longitude: Optional[float] = None
        if lon_str is not None and str(lon_str).strip() != "":
            try:
                longitude = float(lon_str)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid longitude value: {lon_str}")

        d96_easting: Optional[float] = None
        if d96_e_str is not None and str(d96_e_str).strip() != "":
            try:
                d96_easting = float(d96_e_str)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid d96_easting value: {d96_e_str}")

        d96_northing: Optional[float] = None
        if d96_n_str is not None and str(d96_n_str).strip() != "":
            try:
                d96_northing = float(d96_n_str)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid d96_northing value: {d96_n_str}")

        elevation_meters: Optional[int] = None
        if elev_str is not None and str(elev_str).strip() != "":
            try:
                elevation_meters = int(float(elev_str))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid elevation_meters value: {elev_str}")

        return cls(
            station_id = station_id,
            station_name = station_name,
            latitude = latitude,
            longitude = longitude,
            d96_easting = d96_easting,
            d96_northing = d96_northing,
            elevation_meters = elevation_meters

        )
    
    


        
                                   




        


            
        
        

        



    




