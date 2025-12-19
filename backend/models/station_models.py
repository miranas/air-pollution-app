from dataclasses import dataclass
import logging
from data.stations import decode_unicode_escapes


# =================================================================================
# DATA STRUCTURES (Dataclassess) autogenerate __init__, __repr__, __eq__, __hash__
#==================================================================================


@dataclass
class StationInfo:
    
    """
    Represents information about a single air_quality monitoring station (name, id, coordinates)

    PROCESSING:
    - __post_init__() runs after __init__() object creation
    - Decodes UTF-8 escapes in name field with decode_unicode_escapes() imported method from stations.py
    - Validates station data (raises ValueError if invalid)
    - Adds computed fields
    """
            
    id: str # station ID like #E405"
    name: str # Station name like "LJ Be\u017eigrad" (will be decoded)

    def __post_init__(self):

        #Decoding UTF-8 escapes in name
        original_name = self.name # before decoding

        # decode UTF-8 escapes and strip whitespaces
        self.name = decode_unicode_escapes(self.name).strip() 

        if original_name != self.name:
            logging.info(f"UTF-8 decoded station name: {original_name} -> {self.name}")

       # Validation
        if not self.id or not self.id.strip():
             raise ValueError("Station ID cannot be empty")
        if not self.name or not self.name.strip():
             raise ValueError("Station name cannot be empty")
       
    


