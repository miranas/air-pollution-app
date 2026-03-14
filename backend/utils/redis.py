from flask import current_app
import logging
from typing import Any, Dict, Optional
import json
from backend.utils.serialization import to_serializable
from flask import current_app


logging.basicConfig(level=logging.INFO)


def get_redis_client(app: Optional[Any]) -> Optional[Any]:
    """Return Redis client"""
    if app and getattr(app, 'extensions', None):  
        if 'redis_client' in app.extensions:
            return app.extensions['redis_client'] # redis_client is defined in app.py
        return None # don't break an app if there is nothing
    

def get_cache_client(app: Optional[Any]) -> Optional[Any]:
    """Return SimpleCache client"""
    if app and getattr(app, 'extensions', None):
        # check if cache is in app.extensions
        cache = app.extensions.get('cache')  # type: ignore
        if cache:
            return cache
        
    # if not found in extensions, check if app has attribute 'cache' (SimpleCache)
    if app and hasattr(app, 'cache'):
        return getattr(app, 'cache')
    return None



def serialize_merged_data(merged_data: Dict[str, Any]) -> Optional[str]:
    """Serialize merged_data to JSON string with UTF-8 encoding."""
    try:
        return json.dumps(merged_data, default=to_serializable, ensure_ascii=False)
    except Exception:
        logging.exception("Failed to serialize merged_data for caching")
        return None



def insert_merged_data_into_cache(merged_data: Dict[str, Any]) -> bool:
    """Save  merged_data into Redis or SimpleCache, if Redis is not available."""
    try:
        # Access current_app directly; accessing it outside an app context raises RuntimeError
        try:
            app = current_app
        except RuntimeError:
            logging.warning("No Flask app context found.")
            app = None

        redis_client = get_redis_client(app)
        data = serialize_merged_data(merged_data)
        if redis_client:
            redis_client.set('latest_merged_data', data)
            logging.info("Written merged_data to Redis.")
            return True

        cache_client = get_cache_client(app)
        if cache_client and hasattr(cache_client, 'set'):
            cache_client.set('latest_merged_data', data)
            logging.info("Written merged_data to SimpleCache.")
            return True

        logging.warning("No cache client available; skipping cache write for latest_merged_data.")
        return False

    except Exception:
        logging.exception("Failed to update cache for latest_merged_data")
        return False





    

        








