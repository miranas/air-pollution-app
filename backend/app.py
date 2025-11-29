from flask import Flask, jsonify, request
from data.stations import get_all_stations, get_station_by_id, get_station_by_name
import logging
from utils.decorators import add_timing,handle_exceptions
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)


# Create Flask app
app = Flask(__name__)



#Route 1: Home page
@app.route("/")
@add_timing
@handle_exceptions
def hello():
    return  "Hello from Slovenia Air Quality"

#Route 2: Health check
@app.route("/api/health")
@add_timing
@handle_exceptions
def health():
    return jsonify({
        "status": "OK",
        "message": "Slovenia Air Quality Monitoring",
        "version": "1.0"
    })

@app.route("/api/stations")
@add_timing
@handle_exceptions
def get_stations():
    station_id = request.args.get('id')
    station_name = request.args.get('name')

    if station_id:
        station = get_station_by_id(station_id)
        if station:
            return jsonify(station), 200
        else:
            return jsonify({"error": "Station not found"}), 404

    elif station_name:
        station = get_station_by_name(station_name)
        if station:
            return jsonify(station), 200
        else:
            return jsonify({"error": "Station name not found"}), 404
    else:
        stations = get_all_stations()
        return jsonify({
            "stations":stations}), 200
   


# run the app
if __name__ == "__main__":
    app.run(debug=True)




