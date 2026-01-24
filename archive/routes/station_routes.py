from flask import Blueprint, request, jsonify, Response
from typing import List, Dict, Any, Tuple, Union
from backend.data.stations import get_all_stations, get_station_by_id_or_name
from backend.utils.decorators import handle_exceptions, add_timing


# Create blueprint
station_bp = Blueprint('stations', __name__)


@station_bp.route("/api/stations")
@add_timing
@handle_exceptions
def get_stations_api():
    station_id = request.args.get('id')
    station_name = request.args.get('name')

    if station_id or station_name:
        station = get_station_by_id_or_name(station_id, station_name)
        if station:
            return jsonify(station), 200
        else:
            return jsonify({"error": "Station not found"}), 404
   
    else:
        stations = get_all_stations()
        return jsonify({
            "stations":stations}), 200


# Force cache clear api route
@station_bp.route("/api/clear-cache")
@add_timing
@handle_exceptions
def clear_cache():
    """Force clear stations cache"""
    import data.stations as stations_module
    import importlib

    # Reload the stations module to reset in-memory cache without touching private attributes defined in stations.py
    importlib.reload(stations_module)
    
    # Get fresh decoded data
    stations = stations_module.get_all_stations()
    
    return jsonify({

        "message": "Cache cleared and reloaded with UTF-8 decoding",
        "stations_count": len(stations),
        "sample_station": stations[0] if stations else None,
        "cache_status": "Cleared and refreshed"
    
    })



