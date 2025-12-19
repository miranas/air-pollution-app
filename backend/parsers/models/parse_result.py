from dataclasses import dataclass
from typing import Any, Optional

#=====================================================================
# RESULT OF PARSING OPERATION
#=====================================================================

@dataclass
class ParseResult:
    """ Result of parsing operation"""
    success: bool                            # Whether parsing succeeded or not
    data: Any                                # Parsed data (Any type or data allowed)
    error_message: Optional[str] = None      # Error message can be string or None(becouse of Optional),default is None
    items_parsed: int = 0                    # How many items were parsed successfully
    processing_time_ms: Optional[float] = None #time taken to process in miliseconds