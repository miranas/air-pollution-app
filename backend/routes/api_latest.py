from flask import  Blueprint, Response, jsonify
from backend.app import cache


api_latest_bp = Blueprint('api_latest', __name__)

@api_latest_bp.route('/api/latest')
def get_latest_data():
    latest_data = cache.get('latest_merged_data')
    if latest_data:
        if isinstance(latest_data,str):
            # If the latst data is string returnas JSON
            return Response(latest_data, mimetype='application/json')
        # if it's a dict/list jsonify it
        return jsonify(latest_data)
    return jsonify({"error": "No data"})

