from flask import Blueprint, Response, jsonify
from flask import current_app, request
import json
import time
from collections import defaultdict, deque
from threading import Lock
from backend.data.update_data import update_data
from backend.database.session import SessionLocal
from backend.database.db_models import DbModelStation, DbModelMeasurement, DbModelPollutant
from sqlalchemy import func
from backend.utils.redis import insert_merged_data_into_cache
from backend.utils.redis import get_latest_merged_data_fallback
from backend.utils.history_cache import get_history_payload


api_latest_bp = Blueprint('api_latest', __name__)

_HISTORY_RATE_LIMIT = 120
_HISTORY_RATE_WINDOW_SECONDS = 60
_history_rate_lock = Lock()
_history_requests_by_ip: dict[str, deque[float]] = defaultdict(deque)


def _allow_history_request(client_ip: str) -> tuple[bool, int]:
    now = time.monotonic()
    with _history_rate_lock:
        queue = _history_requests_by_ip[client_ip]
        while queue and (now - queue[0]) > _HISTORY_RATE_WINDOW_SECONDS:
            queue.popleft()

        if len(queue) >= _HISTORY_RATE_LIMIT:
            retry_after = max(1, int(_HISTORY_RATE_WINDOW_SECONDS - (now - queue[0])))
            return False, retry_after

        queue.append(now)
        return True, 0


def _history_cache_control(period: str) -> str:
    if period == 'day':
        return 'public, max-age=30, stale-while-revalidate=60'
    return 'public, max-age=120, stale-while-revalidate=300'


def _build_latest_from_db() -> dict:
    db = SessionLocal()
    # check if there are any measurements at all, if not return empty dict to avoid unnecessary joins
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
    cache_only = request.args.get('cache_only', '0') in ('1', 'true', 'True', 'yes')

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

        # Flask-Caching instance fallback (used when extension registry shape differs)
        if cached is None:
            try:
                from backend.app import cache as app_cache
                if hasattr(app_cache, 'get'):
                    cached = app_cache.get('latest_merged_data')
            except Exception as e:
                current_app.logger.exception(f"Failed to get latest_merged_data via app cache: {e}")

        if cached is None:
            cached = get_latest_merged_data_fallback()
        return cached

    latest_data = _read_latest_from_cache()

    # On cold start or after cache eviction, repopulate once, then re-check cache.
    if latest_data is None and not cache_only:
        try:
            update_data()
        except Exception as e:
            current_app.logger.exception(f"update_data() failed during /api/latest refresh: {e}")
        latest_data = _read_latest_from_cache()

    # Final fallback: build API payload from DB even if cache missed.
    if latest_data is None and not cache_only:
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


@api_latest_bp.route('/api/history')
def get_history_data():
    period = request.args.get('period', 'day').lower()
    station_id = request.args.get('station_id')
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()

    if period not in {'day', 'week', 'month', 'year'}:
        return jsonify({'error': 'Invalid period. Use day|week|month|year'}), 400

    allowed, retry_after = _allow_history_request(client_ip)
    if not allowed:
        response = jsonify({'error': 'Too many requests. Please retry shortly.'})
        response.status_code = 429
        response.headers['Retry-After'] = str(retry_after)
        return response

    try:
        payload = get_history_payload(period, station_id)
        if payload is None:
            return jsonify({'error': 'Failed to load history'}), 500

        response = jsonify(payload)
        response.headers['Cache-Control'] = _history_cache_control(period)
        response.headers['Vary'] = 'Accept-Encoding'
        return response
    except Exception as e:
        current_app.logger.exception(f"Failed to build history payload: {e}")
        return jsonify({'error': 'Failed to load history'}), 500

