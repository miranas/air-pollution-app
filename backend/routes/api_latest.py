from flask import  Blueprint, Response, jsonify
from flask import current_app
import json
from backend.data.update_data import update_data
from backend.database.session import SessionLocal
from backend.database.db_models import DbModelStation, DbModelMeasurement, DbModelPollutant
from sqlalchemy import func
from backend.utils.redis import insert_merged_data_into_cache



api_latest_bp = Blueprint('api_latest', __name__)


def _build_latest_from_db() -> dict:
    db = SessionLocal()
    try:
        latest_ts = db.query(func.max(DbModelMeasurement.measured_at)).scalar()
        if latest_ts is None:
            return {}

        rows = (
            db.query(DbModelStation, DbModelMeasurement, DbModelPollutant)
            .join(DbModelMeasurement, DbModelMeasurement.station_id == DbModelStation.id)
            .join(DbModelPollutant, DbModelPollutant.id == DbModelMeasurement.pollutant_id)
            .filter(DbModelMeasurement.measured_at == latest_ts)
            .all()
        )

        result: dict = {}
        for station, measurement, pollutant in rows:
            station_key = station.station_id
            if station_key not in result:
                result[station_key] = {
                    "info": {
                        "station_id": station.station_id,
                        "station_name": station.station_name,
                        "latitude": station.latitude,
                        "longitude": station.longitude,
                        "d96_easting": station.d96_easting,
                        "d96_northing": station.d96_northing,
                        "elevation_meters": station.elevation_meters,
                    },
                    "measurements_list": [
                        {
                            "station_id": station.station_id,
                            "station_name": station.station_name,
                            "time_to": latest_ts.isoformat(),
                        }
                    ],
                }

            result[station_key]["measurements_list"][0][pollutant.name] = measurement.value

        return result
    finally:
        db.close()

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

    # Final fallback: build API payload from DB even if cache missed.
    if latest_data is None:
        try:
            db_payload = _build_latest_from_db()
            if db_payload:
                insert_merged_data_into_cache(db_payload)
                latest_data = json.dumps(db_payload, ensure_ascii=False)
        except Exception as e:
            current_app.logger.exception(f"DB fallback failed in /api/latest: {e}")

    if latest_data:
        if isinstance(latest_data,bytes):
            latest_data = latest_data.decode('utf-8')        
        return Response(latest_data, mimetype='application/json')        
    return jsonify({"error": "No data available yet"}), 503

