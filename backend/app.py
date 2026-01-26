import time
import os
from flask import Flask, Response
from flask.json.provider import DefaultJSONProvider
import logging
from backend.network.arso_client import fetch_arso_xml
from backend.parsers.station_parser import parse_stations_from_xml
from backend.parsers.measurments_parser import parse_measurements_from_xml
from backend.parsers.stations_and_measurments_merger import merge_stations_and_measurements
from backend.parsers.insert_data import insert_all_data
from typing import Any, List, Tuple
from flask_caching import Cache
logging.basicConfig(level=logging.INFO)
from  apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[reportMissingTypeStubs]
from redis import Redis
from redis.exceptions import ConnectionError
from prometheus_flask_exporter import PrometheusMetrics


# Initialize cache instance
cache = Cache()

def update_data():
    # Fetch XML from ARSO
    success, xml_content, error = fetch_arso_xml()
    if not success or not xml_content:
        logging.error(f"Error fetching XML: {error}")
        return False

    station_result = parse_stations_from_xml(xml_content)
    if not station_result.success:
        logging.error(f"Error parsing stations: {station_result.error_message}")
        return False

    # parse measurements return Measurement
    measurement_result = parse_measurements_from_xml(xml_content)
    if not measurement_result.success:
        logging.error(f"Error parsing measurements: {measurement_result.error_message}")
        return False

    # merge stations and measurements
    merged_data = merge_stations_and_measurements(
        station_result.data,
        measurement_result.data)

    if not merged_data:
        logging.info("No merged data available")
        return False
    else:
        # summary log
        logging.info(f"Merged data for {len(merged_data)} stations")

        for station_id, station_info in merged_data.items():
            logging.debug(f"Station ID: {station_id}")
            logging.debug(f"  Name: {station_info['info'].station_name}")
            logging.debug(f"  Measurements ({len(station_info['measurements_list'])}):")

            for m in station_info['measurements_list'][:23]:
                logging.debug(f"    {m}")
            if len(station_info['measurements_list']) > 5:
                logging.debug(f"    ...and {len(station_info['measurements_list']) - 5} more\n")
            else:
                logging.debug("")

        # Build all_parsed_data from merged_data for insertion
        all_parsed_data: List[Tuple[Any, Any]] = []

        for station_id, station_and_measuremnents_data in merged_data.items():
            station_data = station_and_measuremnents_data["info"]
            for measurement_data in station_and_measuremnents_data["measurements_list"]:
                all_parsed_data.append((station_data, measurement_data))

        # Insert into storage
        try:
            insert_all_data(all_parsed_data)
        except Exception as e:
            logging.exception(f"Failed to insert data: {e}")
            # continue to attempt caching the merged data even if DB insert failed

        # put the merged data into the cache if available
        try:
            cache.set('latest_merged_data', merged_data)# type: ignore
        except Exception:
            logging.exception("Failed to update cache for latest_merged_data")

        logging.info(f"Inserted total of {len(all_parsed_data)} measurement entries into the database.")
        return True


# =======================================================================


def create_app() -> Flask:

    # Create Flask app
    app = Flask(__name__)

    # Prometheus metrics
    metrics = PrometheusMetrics(app)  # type: ignore


    # Caching
    # if there is no redis available use SimpleCache
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')

    # 
    use_redis = False

    if redis_url:
        attempts = 10
        for attempt in range(attempts):
            try:
                redis_client: Redis = Redis.from_url(redis_url)  #type: ignore
                if redis_client.ping(): #type: ignore
                    use_redis = True
                    logging.info(f"Connected to redis in {attempt +1} st attempt ")
                    break
                else:
                    time.sleep(2) # wait before retrying

            except ConnectionError:
                logging.warning("Redis not ready")


        if use_redis:            
            app.config['CACHE_TYPE'] = 'RedisCache'
            app.config['CACHE_REDIS_URL'] = redis_url
            logging.info(f"Using Redis cache at {redis_url}")
        
        else:
            app.config['CACHE_TYPE'] = "SimpleCache"           
            logging.info(f"Using SimpleCache ")
        
        

    app.config['CACHE_DEFAULT_TIMEOUT'] = 3600

    # Initialize cache instance with app
    cache.init_app(app)  # type: ignore


    # UTF-8 JSON Configuration
    app.config['JSON_AS_ASCII'] = False  # Ensure UTF-8 encoding for JSON responses
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # Better JSON formatting
    app.config['JSON_SORT_KEYS'] = False  # Keep original order of JSON keys
    
    """
    # Import blueprints
    from backend.routes.station_routes import station_bp
    from backend.routes.health_routes import health_bp
    from backend.routes.debug_routes import debug_bp

    # Register blueprints
    app.register_blueprint(station_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(debug_bp)
    """
    
    # Custom JSON provider to ensure UTF-8 encoding   
    class UTF8JsonProvider(DefaultJSONProvider):
        def dumps(self, obj: Any, **kwargs: Any) -> str:

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


    # Register the after-request handler 
    app.after_request(_after_request)


    
    # Start background scheduler for hourly updates    
    scheduler: Any = BackgroundScheduler()

    # Ensure scheduled jobs run inside the Flask application context so DB/cache usage is valid
    def _run_update_data_in_app_context() -> None:
        try:
            with app.app_context():
                update_data()
        except Exception:
            logging.exception("Scheduled update_data failed")

    scheduler.add_job(func=_run_update_data_in_app_context, trigger='interval', hours=1)
    scheduler.start()

    logging.info("Background scheduler started for hourly data updates")


    # Optionally run an initial data update when the app starts
    with app.app_context():
        update_data()

    return app # Return the configured app instance

#=======================================================================================
# main block
app = create_app()

if __name__ == '__main__':    
    app.run(debug=False,host="0.0.0.0", port=5000)

   





    


    

    

    





