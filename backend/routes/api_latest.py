from flask import  Blueprint, Response, jsonify
from flask import current_app
import json



api_latest_bp = Blueprint('api_latest', __name__)

@api_latest_bp.route('/api/latest')
def get_latest_data():  
    redis_client = current_app.extensions.get('redis_client')
    if redis_client is None:
        current_app.logger.error("Redis client not configured in current_app.extensions")
        return jsonify({"error": "Redis client not configured"}), 503

    try:
        latest_data = redis_client.get('latest_merged_data')
    except Exception as e:
        current_app.logger.exception(f"Failed to get latest_merged_data from redis: {e}")
        return jsonify({"error": "Failed to retrieve data"}), 500

    print(f"DEBUG latest_data: type={type(latest_data).__name__} value={latest_data!r}")
    if latest_data:
        if isinstance(latest_data,bytes):
            latest_data = latest_data.decode('utf-8')        
        return Response(latest_data, mimetype='application/json')        
    return jsonify({"error": "No data"})

