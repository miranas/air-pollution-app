"""
Measurements parser module
==========================
Parses measurements data from ARSO XML and converts
them to Measurement dataclass instances 
"""
from xml.etree import ElementTree as ET
from typing import List
from datetime import datetime
from backend.parsers.models.measurement_model import Measurement

# ===============================================================
# PARSING METHODS
# ===============================================================

def parse_measurements_from_xml(xml_content: str) -> 