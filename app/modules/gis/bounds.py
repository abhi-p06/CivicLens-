"""
Configurable Geographic Boundary Validation for CIVILENS.
Enforces that civic issues and geolocation queries remain strictly within Mumbai and Navi Mumbai.
"""
from typing import Dict, Any, Tuple
from app.config import settings

OUT_OF_BOUNDS_ERROR = "CIVILENS currently supports complaints from Mumbai and Navi Mumbai only."

def get_supported_bounds() -> Dict[str, Any]:
    """Returns the configured bounding box coordinates for Mumbai & Navi Mumbai."""
    return {
        "region": "Mumbai & Navi Mumbai",
        "min_lat": settings.geo_min_lat,
        "max_lat": settings.geo_max_lat,
        "min_lng": settings.geo_min_lng,
        "max_lng": settings.geo_max_lng,
    }

def is_within_supported_bounds(lat: float, lng: float) -> bool:
    """
    Checks if given coordinates fall inside the configured Mumbai & Navi Mumbai bounding region.
    """
    if lat is None or lng is None:
        return False
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (ValueError, TypeError):
        return False

    return (
        settings.geo_min_lat <= lat_f <= settings.geo_max_lat and
        settings.geo_min_lng <= lng_f <= settings.geo_max_lng
    )

