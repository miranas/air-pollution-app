from flask import Flask, Response
from flask.json.provider import DefaultJSONProvider
import logging
from backend.network.arso_client import fetch_arso_xml
from backend.parsers.station_parser import parse_stations_from_xml
from backend.parsers.measurments_parser import parse_measurements_from_xml
from backend.parsers.stations_and_measurments_merger import merge_stations_and_measurements
from backend.parsers.insert_data import insert_all_data
from typing import Any, List, Tuple
# Configure logging
logging.basicConfig(level=logging.INFO)


def create_app() -> Flask:

    # Create Flask app
    app = Flask(__name__)

    # UTF-8 JSON Configuration
    app.config['JSON_AS_ASCII'] = False  # Ensure UTF-8 encoding for JSON responses
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # Better JSON formatting
    app.config['JSON_SORT_KEYS'] = False  # Keep original order of JSON keys
    
    # Import blueprints
    from backend.routes.station_routes import station_bp
    from backend.routes.health_routes import health_bp
    from backend.routes.debug_routes import debug_bp

    # Register blueprints
    app.register_blueprint(station_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(debug_bp)

    
    # Custom JSON provider to ensure UTF-8 encoding   
    class UTF8JsonProvider(DefaultJSONProvider):
        def dumps(self, obj, **kwargs):

            """Custom JSON encoder for UTF-8 support
            This method is called every time jsonify() is used
            Args:
                obj: Python object to convert to json
                **kwargs: JSON formatting options"""
        
            kwargs['ensure_ascii'] = False
            kwargs['indent'] =  2

            return super().dumps(obj, **kwargs)


    # Set custom JSON provider for the app
    app.json_provider_class = UTF8JsonProvider


    # Global UTF-8 header - aplies to all routes automatically Built-in Flask hook -runs after every request
    def _after_request(response: Response) -> Response:

        # only set JSON headers for JSON responses
        if response.content_type and 'application/json' in response.content_type:
            response.headers['Content-Type'] = 'application/json; charset=utf-8'

        # CORS headers for all responses
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

        # Cache control for all responses
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
        return response #single return point


    # Register the after-request handler explicitly so static analyzers detect its usage
    app.after_request(_after_request)

    return app # Return the configured app instance

   

# run the app
if __name__ == "__main__":
    app = create_app()
    #app.run(debug=True)

    # Fetch XML from ARSO
    success, xml_content, error = fetch_arso_xml()
    if not success or not xml_content:
        print(f"Error fetching XML {error}")
        exit(1)

    # Parse stations, returns StationParseResult
    # xml_content is expected to be a valid XML string containing station data
    # in the case of error return StationParseResult from the parse_stations_from_xml method
    # but only error_message variable from that class
    # In the case of success return ParseResult class instance with data variable 
    # containing list of successfully parsed StationInfo objects
    station_result = parse_stations_from_xml(xml_content)
    if not station_result.success:
        print(f"Error parsing stations:{station_result.error_message}")
        exit(1)   


    # parse measuremens return Measurement 
    measurement_result = parse_measurements_from_xml(xml_content)
    if not measurement_result.success:
        print(f"Error parsing measuremnts {str(measurement_result.error_message)}")
        exit(1)    


    # merge stations and mesurements
    merged_data = merge_stations_and_measurements(
        station_result.data, 
        measurement_result.data)
    
    
    if not merged_data:
        print("Not merged data available")
    else:
        print(f"Merged data for len{merge_stations_and_measurements} stations")
   

        for station_id, station_info in merged_data.items():
            print(f"Station ID: {station_id}")
            print(f"  Name: {station_info['info'].station_name}")
            print(f"  Measurements ({len(station_info['measurements_list'])}):")
            
            for m in station_info['measurements_list'][:23]:  # Print first 5 measurements for brevity
                print(f"    {m}")
            if len(station_info['measurements_list']) > 5:
                print(f"    ...and {len(station_info['measurements_list']) - 5} more\n")
            else:
                print()
        # Build all_parsed_data from merged_data for insertion
        all_parsed_data: List[Tuple[Any, Any]] = []

        for station_id, station_and_measuremnents_data in merged_data.items():
            station_data = station_and_measuremnents_data["info"]
            for measurement_data in station_and_measuremnents_data["measurements_list"]:
                all_parsed_data.append((station_data, measurement_data))


        insert_all_data(all_parsed_data)
        print(f"Inserted total of {len(all_parsed_data)} measurement entries into the database.")




    


    

    

    





