from flask import  Blueprint, Response, jsonify
from flask import current_app
import json



api_latest_bp = Blueprint('api_latest', __name__)

@api_latest_bp.route('/api/latest')
def get_latest_data():  
    redis_client = current_app.extensions.get('redis_client')
    latest_data = None

    if redis_client is not None:
        try:
            latest_data = redis_client.get('latest_merged_data')
        except Exception as e:
            current_app.logger.exception(f"Failed to get latest_merged_data from redis: {e}")

    # Fallback to Flask-Caching backend (SimpleCache when Redis is unavailable)
    if latest_data is None:
        cache_ext = current_app.extensions.get('cache')
        if cache_ext and hasattr(cache_ext, 'cache') and hasattr(cache_ext.cache, 'get'):
            try:
                latest_data = cache_ext.cache.get('latest_merged_data')
            except Exception as e:
                current_app.logger.exception(f"Failed to get latest_merged_data from cache: {e}")

    print(f"DEBUG latest_data: type={type(latest_data).__name__} value={latest_data!r}")
    if latest_data:
        if isinstance(latest_data,bytes):
            latest_data = latest_data.decode('utf-8')        
        return Response(latest_data, mimetype='application/json')        
    return jsonify({"error": "No data"})

