"""
CIVILENS Hierarchical Geographical Spatial Engine
Provides strict point-in-polygon validation and multi-tier administrative routing
for Mumbai (BMC) and Navi Mumbai (NMMC).
"""
import math
import re
from typing import Dict, Any, List, Optional, Tuple

from app.modules.gis.hierarchy_data import (
    MUNICIPAL_AUTHORITIES,
    ADMINISTRATIVE_ZONES,
    ADMINISTRATIVE_WARDS,
    CIVILENS_OPERATIONAL_SUB_WARDS,
    LOCALITY_BEATS
)
from app.modules.gis.bounds import OUT_OF_BOUNDS_ERROR

def point_in_polygon(lng: float, lat: float, ring: List[List[float]]) -> bool:
    """
    Ray-casting algorithm (Jordan Curve Theorem) to determine if a point [lng, lat]
    is inside a polygon boundary defined by ring [[lng, lat], ...].
    """
    if len(ring) < 3:
        return False

    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]

        # Check edge crossing with horizontal ray to the right
        if ((yi > lat) != (yj > lat)):
            slope_x = (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
            if lng < slope_x:
                inside = not inside
        j = i

    return inside

def point_in_geometry(lng: float, lat: float, geometry: Dict[str, Any]) -> bool:
    """
    Validates point containment against GeoJSON geometry (Polygon or MultiPolygon).
    Uses bounding box pre-checks for O(1) rejection.
    """
    if not geometry:
        return False

    geom_type = geometry.get("type", "")
    coords = geometry.get("coordinates", [])
    if not coords:
        return False

    if geom_type == "Polygon":
        ring = coords[0]
        if not ring:
            return False
        # Fast bounding box rejection
        min_x = min(p[0] for p in ring)
        max_x = max(p[0] for p in ring)
        min_y = min(p[1] for p in ring)
        max_y = max(p[1] for p in ring)
        if lng < min_x or lng > max_x or lat < min_y or lat > max_y:
            return False

        if not point_in_polygon(lng, lat, ring):
            return False
        for hole in coords[1:]:
            if point_in_polygon(lng, lat, hole):
                return False
        return True

    elif geom_type == "MultiPolygon":
        for poly_coords in coords:
            if not poly_coords or not poly_coords[0]:
                continue
            ring = poly_coords[0]
            min_x = min(p[0] for p in ring)
            max_x = max(p[0] for p in ring)
            min_y = min(p[1] for p in ring)
            max_y = max(p[1] for p in ring)
            if lng < min_x or lng > max_x or lat < min_y or lat > max_y:
                continue

            if point_in_polygon(lng, lat, ring):
                in_hole = False
                for hole in poly_coords[1:]:
                    if point_in_polygon(lng, lat, hole):
                        in_hole = True
                        break
                if not in_hole:
                    return True
        return False

    return False


def _euclidean_distance_sq(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    return (lat1 - lat2) ** 2 + (lng1 - lng2) ** 2


def resolve_coordinates_hierarchy(
    lat: float,
    lng: float,
    authorities: Optional[List[Dict[str, Any]]] = None,
    zones: Optional[List[Dict[str, Any]]] = None,
    wards: Optional[List[Dict[str, Any]]] = None,
    sub_wards: Optional[List[Dict[str, Any]]] = None,
    localities: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Authoritative hierarchical spatial resolution.
    Determines Municipal Authority -> Zone -> Ward -> Sub-Ward -> Locality/Beat.
    Strictly differentiates between BMC (Mumbai) and NMMC (Navi Mumbai).
    Enforces geographic scope: rejects coordinates outside supported municipal boundaries.
    """
    auth_list = authorities if authorities is not None else MUNICIPAL_AUTHORITIES
    zone_list = zones if zones is not None else ADMINISTRATIVE_ZONES
    ward_list = wards if wards is not None else ADMINISTRATIVE_WARDS
    sub_list = sub_wards if sub_wards is not None else CIVILENS_OPERATIONAL_SUB_WARDS
    loc_list = localities if localities is not None else LOCALITY_BEATS

    if lat is None or lng is None:
        return {
            "is_valid": False,
            "error": "Coordinates (latitude and longitude) are required.",
            "requires_admin_review": True,
            "review_reason": "Missing coordinate values."
        }

    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (ValueError, TypeError):
        return {
            "is_valid": False,
            "error": "Invalid numerical coordinates.",
            "requires_admin_review": True,
            "review_reason": "Invalid coordinate format."
        }

    # 1. Determine Municipal Authority via point-in-polygon
    matched_auth: Optional[Dict[str, Any]] = None
    for auth in auth_list:
        geom = auth.get("boundary_geojson")
        if geom and point_in_geometry(lng_f, lat_f, geom):
            matched_auth = auth
            break

    # If point is outside both BMC and NMMC authority boundaries -> REJECT
    if not matched_auth:
        return {
            "is_valid": False,
            "error": OUT_OF_BOUNDS_ERROR,
            "latitude": lat_f,
            "longitude": lng_f,
            "requires_admin_review": False
        }

    auth_id = matched_auth["id"]
    auth_code = matched_auth["code"]
    auth_name = matched_auth["name"]

    # 2. Determine Administrative Ward within the authority
    matched_ward: Optional[Dict[str, Any]] = None
    auth_wards = [w for w in ward_list if w.get("authority_id") == auth_id]

    for w in auth_wards:
        geom = w.get("boundary_geojson")
        if geom and point_in_geometry(lng_f, lat_f, geom):
            matched_ward = w
            break

    is_ambiguous_ward = False
    if not matched_ward:
        # Border corridor, water edge, or ward without vector boundary:
        # Match closest ward using reference node coordinates or polygon centroid
        closest_dist = float("inf")
        for w in auth_wards:
            geom = w.get("boundary_geojson")
            clat = w.get("latitude")
            clng = w.get("longitude")
            if clat is not None and clng is not None:
                d = _euclidean_distance_sq(lat_f, lng_f, clat, clng)
                if d < closest_dist:
                    closest_dist = d
                    matched_ward = w
            elif geom and geom.get("coordinates"):
                coords = geom["coordinates"]
                ring = coords[0] if geom.get("type") == "Polygon" else (coords[0][0] if coords and coords[0] else None)
                if ring:
                    clng = sum(p[0] for p in ring) / len(ring)
                    clat = sum(p[1] for p in ring) / len(ring)
                    d = _euclidean_distance_sq(lat_f, lng_f, clat, clng)
                    if d < closest_dist:
                        closest_dist = d
                        matched_ward = w
        is_ambiguous_ward = True

    if not matched_ward:
        return {
            "is_valid": True,
            "authority_id": auth_id,
            "authority_code": auth_code,
            "authority_name": auth_name,
            "ward_id": None,
            "ward_code": None,
            "ward_name": None,
            "requires_admin_review": True,
            "review_reason": f"Boundary coordinates within {auth_code} could not be resolved to a recognized administrative ward."
        }

    ward_id = matched_ward["id"]
    ward_code = matched_ward["ward_code"]
    ward_name = matched_ward["ward_name"]
    zone_id = matched_ward.get("zone_id")

    # 3. Determine Administrative Zone
    matched_zone: Optional[Dict[str, Any]] = None
    if zone_id:
        matched_zone = next((z for z in zone_list if z["id"] == zone_id), None)
    if not matched_zone:
        auth_zones = [z for z in zone_list if z.get("authority_id") == auth_id]
        for z in auth_zones:
            geom = z.get("boundary_geojson")
            if geom and point_in_geometry(lng_f, lat_f, geom):
                matched_zone = z
                break

    zone_code = matched_zone["code"] if matched_zone else "ZONE-CENTRAL"
    zone_name = matched_zone["name"] if matched_zone else "General Administrative Zone"

    # 4. Determine CIVILENS Operational Sub-Ward
    ward_subs = [s for s in sub_list if s.get("ward_id") == ward_id and s.get("is_active", True)]
    matched_sub: Optional[Dict[str, Any]] = None
    for s in ward_subs:
        geom = s.get("boundary_geojson")
        if geom and point_in_geometry(lng_f, lat_f, geom):
            matched_sub = s
            break

    if matched_sub:
        sub_id = matched_sub["id"]
        sub_code = matched_sub["sub_ward_code"]
        sub_name = matched_sub["name"]
        sub_supervisor = matched_sub.get("supervisor_name") or matched_ward.get("lead_officer", "Area Supervisor")
        default_road_team = matched_sub.get("default_road_team_id")
        default_swm_team = matched_sub.get("default_swm_team_id")
        is_sub_pending = False
    else:
        # Prompt Requirement 6: "If there is no verified sub-ward polygon, return a verified ward with sub_ward_pending, rather than assigning a nearby unit."
        sub_id = None
        sub_code = "SUB-WARD-PENDING"
        sub_name = f"Sub-Ward Pending ({ward_code})"
        sub_supervisor = matched_ward.get("lead_officer", "Area Supervisor")
        default_road_team = None
        default_swm_team = None
        is_sub_pending = True

    # 5. Determine Locality / Operational Service Beat
    sub_locs = [l for l in loc_list if (l.get("sub_ward_id") == sub_id or (not sub_id and l.get("ward_id") == ward_id)) and l.get("is_active", True)]
    matched_loc: Optional[Dict[str, Any]] = None
    closest_loc_dist = float("inf")

    candidate_locs = sub_locs if sub_locs else [l for l in loc_list if l.get("ward_id") == ward_id and l.get("is_active", True)]

    for loc in candidate_locs:
        clat = loc.get("latitude")
        clng = loc.get("longitude")
        if clat is not None and clng is not None:
            d = _euclidean_distance_sq(lat_f, lng_f, clat, clng)
            if d < closest_loc_dist:
                closest_loc_dist = d
                matched_loc = loc

    loc_id = matched_loc["id"] if matched_loc else None
    loc_name = matched_loc["name"] if matched_loc else f"{ward_name} Service Sector"
    landmark = matched_loc.get("landmark") if matched_loc else loc_name

    requires_review = is_ambiguous_ward or is_sub_pending
    review_reason = None
    if is_ambiguous_ward:
        review_reason = f"Location point ({lat_f:.4f}, {lng_f:.4f}) is in border corridor; nearest ward {ward_code} assigned."
    elif is_sub_pending:
        review_reason = f"No operational sub-ward currently configured for this location in {ward_code}. Awaiting Admin creation."

    return {
        "is_valid": True,
        "latitude": lat_f,
        "longitude": lng_f,
        "authority_id": auth_id,
        "authority_code": auth_code,
        "authority_name": auth_name,
        "zone_id": zone_id,
        "zone_code": zone_code,
        "zone_name": zone_name,
        "ward_id": ward_id,
        "ward_code": ward_code,
        "ward_name": ward_name,
        "sub_ward_id": sub_id,
        "sub_ward_code": sub_code,
        "sub_ward_name": sub_name,
        "is_official_sub_ward": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "locality_id": loc_id,
        "locality_name": loc_name,
        "landmark": landmark,
        "supervisor_name": sub_supervisor,
        "default_road_team_id": default_road_team,
        "default_swm_team_id": default_swm_team,
        "is_ambiguous": is_ambiguous_ward,
        "requires_admin_review": requires_review,
        "review_reason": review_reason
    }


def normalize_ward_code(val: Optional[str]) -> str:
    """Normalizes ward code string for accurate matching (e.g. 'N-Ward', 'n ward', 'N' -> 'N-WARD')."""
    if not val:
        return ""
    v = str(val).strip().upper()
    v = re.sub(r"[\s_]+", "-", v)
    if not v.endswith("-WARD") and not v.startswith("NMMC") and len(v) <= 3 and "/" not in v:
        v = f"{v}-WARD"
    return v


def check_ward_mismatch(selected_ward: Optional[str], derived_ward_code: str) -> Dict[str, Any]:
    """
    Compares citizen-selected administrative ward with GPS point-in-polygon derived ward.
    Returns mismatch status and clear diagnostics.
    """
    if not selected_ward or not selected_ward.strip():
        return {
            "has_selection": False,
            "is_mismatch": False,
            "derived_ward_code": derived_ward_code
        }

    norm_selected = normalize_ward_code(selected_ward)
    norm_derived = normalize_ward_code(derived_ward_code)

    # Check for direct or partial match
    is_match = (
        norm_selected == norm_derived or
        norm_derived in norm_selected or
        norm_selected in norm_derived
    )

    return {
        "has_selection": True,
        "is_mismatch": not is_match,
        "selected_ward": selected_ward,
        "derived_ward_code": derived_ward_code,
        "warning_message": (
            f"Location Mismatch: Selected ward '{selected_ward}' does not match GPS-derived jurisdiction '{derived_ward_code}'. "
            f"Complaints will be routed according to verified geographic boundaries."
            if not is_match else None
        )
    }
