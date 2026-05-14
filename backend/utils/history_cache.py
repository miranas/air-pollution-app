from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
from typing import Any, Optional

from flask import current_app

from backend.database.db_models import DbModelMeasurement, DbModelPollutant, DbModelStation
from backend.database.session import SessionLocal
from backend.utils.serialization import to_serializable


HISTORY_CACHE_KEY_PREFIX = 'history_payload:'
ALLOWED_PERIODS = ('day', 'week', 'month', 'year')

AQI_THRESHOLDS_EU: dict[str, tuple[float, float, float]] = {
    'pm25': (10.0, 20.0, 25.0),
    'pm10': (20.0, 40.0, 50.0),
    'no2': (20.0, 40.0, 60.0),
    'o3': (80.0, 120.0, 180.0),
    'so2': (40.0, 125.0, 350.0),
    'co': (4.0, 7.0, 10.0),
    'nox': (30.0, 60.0, 100.0),
}

AQI_THRESHOLDS_WHO: dict[str, tuple[float, float, float]] = {
    'pm25': (5.0, 10.0, 15.0),
    'pm10': (15.0, 30.0, 45.0),
    'no2': (10.0, 25.0, 40.0),
    'o3': (50.0, 80.0, 120.0),
    'so2': (20.0, 40.0, 80.0),
    'co': (2.0, 4.0, 8.0),
    'nox': (20.0, 40.0, 80.0),
}

MAX_POINTS_BY_PERIOD: dict[str, int] = {
    'day': 192,
    'week': 336,
    'month': 360,
    'year': 365,
}


def _bucket_seconds_for_period(period: str) -> int:
    if period == 'day':
        return 3600  # hourly
    if period == 'week':
        return 3 * 3600  # 3-hour bins
    if period == 'month':
        return 6 * 3600  # 6-hour bins
    return 24 * 3600  # daily for year


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _to_aqi_band_score(value: float, thresholds: tuple[float, float, float]) -> int:
    good_max, ok_max, warn_max = thresholds

    if value <= good_max:
        return round((value / good_max) * 50)
    if value <= ok_max:
        return round(51 + ((value - good_max) / (ok_max - good_max)) * 49)
    if value <= warn_max:
        return round(101 + ((value - ok_max) / (warn_max - ok_max)) * 49)

    hard_cap = warn_max * 2
    if value >= hard_cap:
        return 300
    return round(151 + ((value - warn_max) / (hard_cap - warn_max)) * 149)


def _compute_aqi_index(measurement: dict[str, Any], profile: str) -> Optional[int]:
    thresholds_map = AQI_THRESHOLDS_WHO if profile == 'who' else AQI_THRESHOLDS_EU
    max_score: Optional[int] = None

    for pollutant_key, thresholds in thresholds_map.items():
        numeric_value = _to_float(measurement.get(pollutant_key))
        if numeric_value is None:
            continue
        score = _to_aqi_band_score(numeric_value, thresholds)
        if max_score is None or score > max_score:
            max_score = score

    return max_score


def _attach_aqi_indices(measurements_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for item in measurements_list:
        row = dict(item)
        row['aqi_eu'] = _compute_aqi_index(row, 'eu')
        row['aqi_who'] = _compute_aqi_index(row, 'who')
        enriched.append(row)
    return enriched


def _downsample_measurements(measurements: list[dict[str, Any]], max_points: int) -> list[dict[str, Any]]:
    if len(measurements) <= max_points:
        return measurements

    step = max(1, len(measurements) // max_points)
    sampled = measurements[::step]
    if sampled[-1] != measurements[-1]:
        sampled.append(measurements[-1])
    return sampled[:max_points]


def _aggregate_measurements_by_period(
    measurements_list: list[dict[str, Any]],
    period: str,
) -> list[dict[str, Any]]:
    if not measurements_list:
        return measurements_list

    bucket_seconds = _bucket_seconds_for_period(period)
    metadata_keys = {'station_id', 'station_name', 'time_to', 'time_from'}

    # Work in ascending time order for deterministic bucket aggregation.
    ascending = sorted(measurements_list, key=lambda item: item.get('time_to', ''))
    buckets: dict[int, dict[str, Any]] = {}

    for row in ascending:
        iso_time = row.get('time_to')
        if not iso_time:
            continue
        try:
            dt = datetime.fromisoformat(str(iso_time))
        except Exception:
            continue

        epoch = int(dt.timestamp())
        bucket_epoch = (epoch // bucket_seconds) * bucket_seconds

        bucket = buckets.setdefault(
            bucket_epoch,
            {
                'station_id': row.get('station_id'),
                'station_name': row.get('station_name'),
                'time_to': datetime.fromtimestamp(bucket_epoch + bucket_seconds).isoformat(),
                '_sums': {},
                '_counts': {},
            },
        )

        for key, value in row.items():
            if key in metadata_keys:
                continue
            numeric = _to_float(value)
            if numeric is None:
                continue
            bucket['_sums'][key] = bucket['_sums'].get(key, 0.0) + numeric
            bucket['_counts'][key] = bucket['_counts'].get(key, 0) + 1

    aggregated: list[dict[str, Any]] = []
    for bucket_epoch in sorted(buckets.keys()):
        bucket = buckets[bucket_epoch]
        row: dict[str, Any] = {
            'station_id': bucket.get('station_id'),
            'station_name': bucket.get('station_name'),
            'time_to': bucket.get('time_to'),
        }
        sums = bucket.get('_sums', {})
        counts = bucket.get('_counts', {})
        for pollutant_key, total in sums.items():
            count = counts.get(pollutant_key, 0)
            if count > 0:
                row[pollutant_key] = round(total / count, 2)
        aggregated.append(row)

    # API expects reverse chronological order.
    return list(reversed(aggregated))


def _period_start(period: str) -> datetime:
    now = datetime.now()
    if period == 'day':
        return now - timedelta(days=1)
    if period == 'week':
        return now - timedelta(weeks=1)
    if period == 'month':
        return now - timedelta(days=30)
    if period == 'year':
        return now - timedelta(days=365)
    raise ValueError('Invalid period')


def _get_redis_client() -> Optional[Any]:
    try:
        app = current_app
    except RuntimeError:
        return None

    if app and getattr(app, 'extensions', None):
        return app.extensions.get('redis_client')
    return None


def _get_cache_client() -> Optional[Any]:
    try:
        app = current_app
    except RuntimeError:
        return None

    if app and getattr(app, 'extensions', None):
        cache = app.extensions.get('cache')
        if cache:
            return cache

    if app and hasattr(app, 'cache'):
        return getattr(app, 'cache')
    return None


def _cache_key(period: str) -> str:
    return f'{HISTORY_CACHE_KEY_PREFIX}{period}'


def _serialize_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, default=to_serializable, ensure_ascii=False)


def _deserialize_payload(raw_payload: object) -> Optional[dict[str, Any]]:
    if raw_payload is None:
        return None

    if isinstance(raw_payload, bytes):
        raw_payload = raw_payload.decode('utf-8')

    if isinstance(raw_payload, str):
        try:
            parsed = json.loads(raw_payload)
        except Exception:
            logging.exception('Failed to deserialize cached history payload')
            return None

        if isinstance(parsed, dict):
            return parsed

    if isinstance(raw_payload, dict):
        return raw_payload

    return None


def _read_cached_raw_value(cache_key: str) -> object:
    cached = None
    redis_client = _get_redis_client()
    if redis_client is not None:
        try:
            cached = redis_client.get(cache_key)
        except Exception as e:
            logging.exception(f'Failed to get {cache_key} from redis: {e}')

    if cached is None:
        cache_ext = _get_cache_client()
        if cache_ext and hasattr(cache_ext, 'get'):
            try:
                cached = cache_ext.get(cache_key)
            except Exception as e:
                logging.exception(f'Failed to get {cache_key} from cache: {e}')

    return cached


def _write_cached_raw_value(cache_key: str, payload_json: str) -> bool:
    redis_client = _get_redis_client()
    if redis_client is not None:
        try:
            redis_client.set(cache_key, payload_json)
            return True
        except Exception as e:
            logging.exception(f'Failed to write {cache_key} to redis: {e}')

    cache_ext = _get_cache_client()
    if cache_ext and hasattr(cache_ext, 'set'):
        try:
            cache_ext.set(cache_key, payload_json)
            return True
        except Exception as e:
            logging.exception(f'Failed to write {cache_key} to cache: {e}')

    logging.warning(f'No cache client available; skipping cache write for {cache_key}.')
    return False


def _filter_history_payload(payload: dict[str, Any], station_id_filter: str | None) -> dict[str, Any]:
    if not station_id_filter:
        return payload

    stations = payload.get('stations', {})
    station_payload = stations.get(station_id_filter)
    filtered_payload = dict(payload)
    filtered_payload['stations'] = {station_id_filter: station_payload} if station_payload else {}
    return filtered_payload


def build_history_payload_from_db(period: str, station_id_filter: str | None = None) -> dict:
    db = SessionLocal()
    try:
        start_ts = _period_start(period)
        end_ts = datetime.now()

        query = (
            db.query(DbModelStation, DbModelMeasurement, DbModelPollutant)
            .join(DbModelMeasurement, DbModelMeasurement.station_id == DbModelStation.id)
            .join(DbModelPollutant, DbModelPollutant.id == DbModelMeasurement.pollutant_id)
            .filter(DbModelMeasurement.measured_at >= start_ts)
            .filter(DbModelMeasurement.measured_at <= end_ts)
            .order_by(DbModelStation.station_id.asc(), DbModelMeasurement.measured_at.desc())
        )

        if station_id_filter:
            query = query.filter(DbModelStation.station_id == station_id_filter)

        rows = query.all()

        stations: dict[str, dict[str, Any]] = {}
        for station, measurement, pollutant in rows:
            station_key = station.station_id
            station_bucket = stations.setdefault(
                station_key,
                {
                    'info': {
                        'station_id': station.station_id,
                        'station_name': station.station_name,
                        'latitude': station.latitude,
                        'longitude': station.longitude,
                    },
                    'by_time': {},
                },
            )

            iso_time = measurement.measured_at.isoformat()
            time_bucket = station_bucket['by_time'].setdefault(
                iso_time,
                {
                    'station_id': station.station_id,
                    'station_name': station.station_name,
                    'time_to': iso_time,
                },
            )
            time_bucket[pollutant.name] = measurement.value

        max_points_per_station = MAX_POINTS_BY_PERIOD.get(period, 500)
        payload_stations: dict[str, dict[str, Any]] = {}
        for station_key, station_data in stations.items():
            by_time = station_data['by_time']
            raw_measurements = sorted(
                by_time.values(),
                key=lambda item: item.get('time_to', ''),
                reverse=True,
            )

            aggregated_measurements = _aggregate_measurements_by_period(raw_measurements, period)
            measurements_list = _downsample_measurements(aggregated_measurements, max_points_per_station)
            measurements_list = _attach_aqi_indices(measurements_list)

            payload_stations[station_key] = {
                'info': station_data['info'],
                'measurements_list': measurements_list,
                'total_points': len(by_time),
            }

        return {
            'period': period,
            'from': start_ts.isoformat(),
            'to': end_ts.isoformat(),
            'stations': payload_stations,
        }
    finally:
        db.close()


def cache_history_payload(period: str, payload: dict[str, Any]) -> bool:
    return _write_cached_raw_value(_cache_key(period), _serialize_payload(payload))


def get_cached_history_payload(period: str, station_id_filter: str | None = None) -> Optional[dict[str, Any]]:
    cached_payload = _deserialize_payload(_read_cached_raw_value(_cache_key(period)))
    if cached_payload is None:
        return None

    return _filter_history_payload(cached_payload, station_id_filter)


def get_history_payload(period: str, station_id_filter: str | None = None) -> Optional[dict[str, Any]]:
    cached_payload = get_cached_history_payload(period, station_id_filter)
    if cached_payload is not None:
        return cached_payload

    try:
        payload = build_history_payload_from_db(period)
    except Exception:
        logging.exception('Failed to build history payload from DB')
        return None

    cache_history_payload(period, payload)
    return _filter_history_payload(payload, station_id_filter)


def refresh_history_cache(periods: tuple[str, ...] = ALLOWED_PERIODS) -> bool:
    success = True
    for period in periods:
        try:
            payload = build_history_payload_from_db(period)
            if not cache_history_payload(period, payload):
                success = False
        except Exception:
            success = False
            logging.exception(f'Failed to refresh history cache for period={period}')
    return success