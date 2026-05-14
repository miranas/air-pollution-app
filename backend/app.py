from datetime import datetime
import os
from flask import Flask, Response, request
import logging
from typing import Any
from flask_caching import Cache
logging.basicConfig(level=logging.INFO)
from  apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[reportMissingTypeStubs]

from prometheus_flask_exporter import PrometheusMetrics
from flask import current_app
from backend.data.update_data import update_data
from dotenv import load_dotenv
load_dotenv()
from backend.utils.response_headers import after_request
from backend.utils.serialization import UTF8JsonProvider


# Initialize cache instance (will be configured in create_app)
cache: Any = Cache()


def create_app() -> Flask:

    # Create Flask app
    app = Flask(__name__)

    # Configure Redis cache
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    try:

        from redis import Redis

        # Create Redis client
        redis_client = Redis.from_url(redis_url) # type: ignore
        
        # Test connection to Redis
        redis_client.ping() # type: ignore

        # Set Flask_Cache configuration to use Redis
        app.config["CACHE_TYPE"] = "RedisCache"
        app.config["CACHE_REDIS_URL"] = redis_url

        # Attach the redis client to the app so it's accessible in other modules via current_app.extensions['redis_client']
        app.extensions['redis_client'] = redis_client
        logging.info("Cache: Redis (%s)", redis_url)

    except Exception:

        # fallback to SimpleCache if Redis is not available, and log a warning
        logging.warning("Cache: Redis ni dostopen, uporabljam SimpleCache")
        app.config["CACHE_TYPE"] = "SimpleCache"            


    # Initialize cache with the app 
    cache.init_app(app)           

   
    # ======================Prometheus metrics ===============================
    
    metrics = PrometheusMetrics(app)  # type: ignore   
                 
    #====================== Register blueprints ==============================
    
    try:
        # Import the blueprint lazily so create_app can still function if the module is missing
        from backend.routes.api_latest import api_latest_bp  # type: ignore
        from typing import cast
        from flask import Blueprint
        # Cast to Blueprint so static type checkers understand the argument type
        app.register_blueprint(cast(Blueprint, api_latest_bp))
    except Exception:
        logging.warning("api_latest_bp not available; skipping blueprint registration")
    
    
    
    # Set custom JSON provider for the app
    app.json_provider_class = UTF8JsonProvider


    # Register the after-request handler 
    app.after_request(after_request)

    
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
#============================== main block ===============================================

app = create_app()

redis_client = app.extensions.get('redis_client')
print(f"Redis client type: {type(redis_client).__name__ if redis_client is not None else 'None'}")
print(f"Cache type: {type(cache).__name__}")
   

@app.route('/api/status')
def status():
    return {
        "project": "ARSO air quality monitoring app",
        "current_time": datetime.now().isoformat(),
        "note": "For testting purposes only. App is running! "    }


if __name__ == '__main__':    
    app.run(debug=False,host="0.0.0.0", port=5000)
    





    


    

    

    





