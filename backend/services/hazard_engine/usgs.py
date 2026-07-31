"""
hazard_engine/usgs.py

USGS Earthquake Catalog client with graceful degradation.
On any network/API/parse failure the engine continues with an empty event list.
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import logging
import socket
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
from .utils import haversine_distance

logger = logging.getLogger(__name__)

# Keep USGS calls short so the overall hazard pipeline stays responsive.
USGS_TIMEOUT_SECONDS = 6.0


def query_usgs_catalog(
    latitude: float,
    longitude: float,
    search_radius_km: float = 100.0,
    historical_years: float = 50.0,
    min_magnitude: float = 4.0
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """
    Query the USGS FDSN event catalog.

    Always returns a 3-tuple. On failure, events is [] and status/warnings
    describe the degradation so callers can continue scoring.
    """
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    start_date = datetime.now(timezone.utc) - timedelta(days=365.25 * historical_years)
    start_str = start_date.replace(tzinfo=None).isoformat().split(".")[0]

    max_radius_deg = search_radius_km / 111.12

    params = {
        "format": "geojson",
        "latitude": latitude,
        "longitude": longitude,
        "maxradius": max_radius_deg,
        "starttime": start_str,
        "minmagnitude": min_magnitude,
        "orderby": "time-asc",
    }

    events: List[Dict[str, Any]] = []
    status: Dict[str, Any] = {"status": "success"}
    warnings: List[str] = []

    try:
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"

        req = urllib.request.Request(
            full_url,
            headers={"User-Agent": "EarthquakeHazardEngine/1.0"},
        )
        with urllib.request.urlopen(req, timeout=USGS_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                status = {"status": "error", "http_status": response.status}
                warnings.append(f"USGS API returned status code {response.status}")
                logger.warning("USGS catalog non-200 status: %s", response.status)
                return events, status, warnings

            body = response.read().decode("utf-8")
            data = json.loads(body)
            features = data.get("features", [])

            for feature in features:
                try:
                    props = feature.get("properties") or {}
                    geom = feature.get("geometry") or {}
                    coords = geom.get("coordinates") or [0, 0, 0]

                    ev_lon = coords[0] if len(coords) > 0 else 0.0
                    ev_lat = coords[1] if len(coords) > 1 else 0.0
                    ev_depth = coords[2] if len(coords) > 2 else 10.0

                    # Skip malformed magnitude entries rather than failing the batch
                    mag = props.get("mag")
                    if mag is None:
                        continue

                    dist = haversine_distance(latitude, longitude, ev_lat, ev_lon)

                    time_ms = props.get("time") or 0
                    try:
                        date_str = (
                            datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc)
                            .isoformat()
                            .replace("+00:00", "Z")
                        )
                    except (OverflowError, OSError, ValueError):
                        date_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

                    events.append({
                        "id": feature.get("id", "unknown"),
                        "magnitude": float(mag),
                        "distance_km": dist,
                        "depth_km": float(ev_depth) if ev_depth is not None else 10.0,
                        "date": date_str,
                        "place": props.get("place") or "Unknown Event Place",
                        "max_mmi": props.get("mmi"),
                    })
                except Exception as feature_err:
                    logger.debug("Skipping malformed USGS feature: %s", feature_err)
                    continue

            events = [e for e in events if e["distance_km"] <= search_radius_km]
            status = {"status": "success", "event_count": len(events)}

    except socket.timeout:
        status = {"status": "timeout"}
        warnings.append("USGS API query timed out.")
        logger.warning("USGS catalog query timed out after %.1fs", USGS_TIMEOUT_SECONDS)
    except TimeoutError:
        status = {"status": "timeout"}
        warnings.append("USGS API query timed out.")
        logger.warning("USGS catalog query timed out after %.1fs", USGS_TIMEOUT_SECONDS)
    except urllib.error.HTTPError as e:
        status = {"status": "error", "http_status": e.code}
        warnings.append(f"USGS API HTTP error {e.code}: {e.reason}")
        logger.warning("USGS catalog HTTP error: %s %s", e.code, e.reason)
    except urllib.error.URLError as e:
        reason = e.reason
        reason_str = str(reason).lower() if reason is not None else ""
        if isinstance(reason, (TimeoutError, socket.timeout)) or "timed out" in reason_str:
            status = {"status": "timeout"}
            warnings.append("USGS API query timed out.")
            logger.warning("USGS catalog URL timeout: %s", e)
        else:
            status = {"status": "failure"}
            warnings.append(f"USGS API query failed: {e}")
            logger.warning("USGS catalog URL error: %s", e)
    except json.JSONDecodeError as e:
        status = {"status": "failure"}
        warnings.append("USGS API returned invalid JSON.")
        logger.warning("USGS catalog JSON decode failed: %s", e)
    except Exception as e:
        status = {"status": "failure"}
        warnings.append(f"USGS API query failed: {e}")
        logger.warning("USGS catalog unexpected failure: %s", e, exc_info=True)

    return events, status, warnings
