from flask import  Blueprint, Response, jsonify
from flask import current_app
import json
from backend.data.update_data import update_data



api_latest_bp = Blueprint('api_latest', __name__)

@api_latest_bp.route('/api/latest')
def get_latest_data():  
    redis_client = current_app.extensions.get('redis_client')
    latest_data = None

    def _read_latest_from_cache() -> object:
        cached = None
        if redis_client is not None:
            try:
                cached = redis_client.get('latest_merged_data')
            except Exception as e:
                current_app.logger.exception(f"Failed to get latest_merged_data from redis: {e}")

        # Fallback to Flask-Caching backend (SimpleCache when Redis is unavailable)
        if cached is None:
            cache_ext = current_app.extensions.get('cache')
            if cache_ext and hasattr(cache_ext, 'cache') and hasattr(cache_ext.cache, 'get'):
                try:
                    cached = cache_ext.cache.get('latest_merged_data')
                except Exception as e:
                    current_app.logger.exception(f"Failed to get latest_merged_data from cache: {e}")
        return cached

    latest_data = _read_latest_from_cache()

    # On cold start or after cache eviction, repopulate once and retry.
    if latest_data is None:
        try:
            update_data()
        except Exception as e:
            current_app.logger.exception(f"update_data() failed during /api/latest refresh: {e}")
        latest_data = _read_latest_from_cache()

    if latest_data:
        if isinstance(latest_data,bytes):
            latest_data = latest_data.decode('utf-8')        
        return Response(latest_data, mimetype='application/json')        
    return jsonify({"error": "No data available yet"}), 503

