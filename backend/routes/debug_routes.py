from flask import Blueprint, jsonify
from utils.decorators import handle_exceptions, add_timing 
import re


# Create blueprint
debug_bp = Blueprint('debug', __name__)


#debug route to test UTF-8 in all browsers
@debug_bp.route("/api/utf-8-exception-test")
@add_timing
@handle_exceptions
def test_utf8_exception():
    raise ValueError("Test exception with UTF-8-exception-test: čevapčiči, šampinjoni, žličniki")
 

# debug route to test UTF-8 handling in JSON responses  
@debug_bp.route("/api/utf8-test")
@add_timing
@handle_exceptions
def test_utf8():
    sample_text = "Čevapčiči šampinjoni, žličnik"
    return jsonify({
        "sample_utf8_text": sample_text,  # ✅ Fixed formatting
        "browser_compatibility": "Chrome and Firefox",
        "test_characters": ["č", "š", "ž", "Č", "Š", "Ž"]
    })


@debug_bp.route("/api/test-decode-direct")
@add_timing
@handle_exceptions
def test_decode_direct():
    """Test Unicode decoding directly"""
    test_string = "LJ Be\\u017eigrad"  # Example from your output
    
    import re
    def replace_unicode(match):
        return chr(int(match.group(1), 16))
    
    decoded = re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, test_string)
    
    return jsonify({
        "original": test_string,
        "decoded": decoded,
        "method_works": decoded != test_string
    })



@debug_bp.route("/api/debug-stations-processing")
@add_timing
@handle_exceptions
def debug_stations_processing():
    """Debug what happens during station processing"""
    from data.stations import fetch_stations_from_arso
    
    # Get fresh data directly (bypass cache)
    fresh_stations = fetch_stations_from_arso()
    
    if fresh_stations and len(fresh_stations) > 0:
        first_station = fresh_stations[0]
        return jsonify({

            "debug": "Station processing test",
            "first_station": first_station,
            "station_name": first_station.get('name', 'NO_NAME'),
            "has_unicode_escapes": '\\u' in first_station.get('name', ''),
            "decode_function_called": "Check terminal for DEBUG prints"
        })
    
    else:
        return jsonify({"error": "No stations fetched"})
    


