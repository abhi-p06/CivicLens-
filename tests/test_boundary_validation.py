"""
CIVILENS Phase 2 Geographic Boundary Validation and Ingestion Test Suite.

Validates:
1. BMC 24 administrative ward polygon dataset integrity (CRS, coordinate order, geometry validity).
2. NMMC 8 administrative ward offices and municipal authority boundary.
3. Decoupling of 24 administrative wards from electoral wards (prabhags).
4. Point-in-polygon resolution for Mumbai ward interiors.
5. Point-in-polygon resolution for Navi Mumbai ward interiors.
6. Strict exclusion of neighboring jurisdictions (TMC, MBMC, PMC, CIDCO Kharghar).
7. Sub-ward pending resolution when no sub-ward polygon is configured.
8. Operational sub-ward flags (is_official=False, operational_type=CIVILENS_OPERATIONAL_SUB_WARD).
9. Metadata catalog completeness and provenance.
"""

import os
import json
import pytest
from app.modules.gis.hierarchy_spatial import (
    resolve_coordinates_hierarchy,
    point_in_geometry,
    point_in_polygon,
    OUT_OF_BOUNDS_ERROR
)
from app.modules.gis.hierarchy_data import (
    MUNICIPAL_AUTHORITIES,
    ADMINISTRATIVE_ZONES,
    ADMINISTRATIVE_WARDS,
    CIVILENS_OPERATIONAL_SUB_WARDS
)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "gis"))
BMC_WARDS_FILE = os.path.join(DATA_DIR, "bmc_administrative_wards.geojson")
BMC_AUTH_FILE = os.path.join(DATA_DIR, "bmc_authority_boundary.geojson")
NMMC_AUTH_FILE = os.path.join(DATA_DIR, "nmmc_authority_boundary.geojson")
NMMC_ELECTORAL_FILE = os.path.join(DATA_DIR, "nmmc_electoral_wards_source.geojson")
METADATA_FILE = os.path.join(DATA_DIR, "METADATA.json")


def test_metadata_catalog_provenance():
    """Verify that METADATA.json exists, is valid, and documents all GIS datasets."""
    assert os.path.exists(METADATA_FILE), "METADATA.json must exist in data/gis/"
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert "datasets" in meta
    dataset_ids = {d["id"] for d in meta["datasets"]}
    assert "bmc-24-administrative-wards" in dataset_ids
    assert "nmmc-municipal-authority-boundary" in dataset_ids
    assert "nmmc-111-electoral-wards-source" in dataset_ids
    assert "nmmc-8-administrative-ward-offices" in dataset_ids

    for d in meta["datasets"]:
        assert "license" in d
        assert "verification_status" in d
        assert "coordinate_reference_system" in d


def test_bmc_24_administrative_wards_integrity():
    """Verify BMC administrative wards dataset has exactly 24 valid polygons with proper CRS & coordinate order."""
    assert os.path.exists(BMC_WARDS_FILE)
    with open(BMC_WARDS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    assert len(features) == 24, f"Expected exactly 24 BMC administrative wards, got {len(features)}"

    expected_codes = {
        "A", "B", "C", "D", "E", "F/S", "G/S", "F/N", "G/N",
        "H/E", "H/W", "K/E", "K/W", "L", "M/E", "M/W", "N",
        "P/S", "P/N", "R/S", "R/C", "R/N", "S", "T"
    }
    actual_codes = {f["properties"]["name"] for f in features}
    assert actual_codes == expected_codes, f"Ward code mismatch: {actual_codes ^ expected_codes}"

    for feat in features:
        geom = feat["geometry"]
        assert geom["type"] in ("Polygon", "MultiPolygon")
        coords = geom["coordinates"]
        rings = coords if geom["type"] == "Polygon" else [r for poly in coords for r in poly]
        for ring in rings:
            assert len(ring) >= 4, "Polygon ring must contain at least 4 coordinates"
            # Ring closure check
            assert ring[0] == ring[-1], "Ring must be closed (first coordinate == last coordinate)"
            # Coordinate order check: [longitude, latitude]
            for pt in ring:
                lng, lat = pt[0], pt[1]
                assert 72.7 <= lng <= 73.0, f"Longitude {lng} out of expected Mumbai range"
                assert 18.8 <= lat <= 19.3, f"Latitude {lat} out of expected Mumbai range"


def test_nmmc_eight_administrative_ward_offices():
    """Verify NMMC establishes exactly 8 official administrative ward offices."""
    nmmc_wards = [w for w in ADMINISTRATIVE_WARDS if w["authority_id"] == "AUTH-NMMC"]
    assert len(nmmc_wards) == 8, f"Expected 8 NMMC administrative ward offices, got {len(nmmc_wards)}"

    expected_nmmc_codes = {
        "NMMC-Belapur", "NMMC-Nerul", "NMMC-Turbhe", "NMMC-Vashi",
        "NMMC-KoparKhairane", "NMMC-Ghansoli", "NMMC-Airoli", "NMMC-Digha"
    }
    actual_nmmc_codes = {w["ward_code"] for w in nmmc_wards}
    assert actual_nmmc_codes == expected_nmmc_codes

    # Verify zero overlap between BMC and NMMC ward codes
    bmc_wards = [w for w in ADMINISTRATIVE_WARDS if w["authority_id"] == "AUTH-BMC"]
    bmc_codes = {w["ward_code"] for w in bmc_wards}
    assert bmc_codes.isdisjoint(actual_nmmc_codes), "BMC and NMMC ward codes must not overlap"


def test_mumbai_ward_interiors_point_in_polygon():
    """Verify coordinates inside various Mumbai wards resolve to the correct administrative ward."""
    test_cases = [
        (18.9260, 72.8235, "A-Ward", "Colaba / Marine Drive"),
        (18.9750, 72.8330, "E-Ward", "Byculla"),
        (19.0435, 72.8562, "G/North", "Dharavi"),
        (19.0601, 72.8361, "H/West", "Bandra West"),
        (19.1197, 72.8600, "K/East", "Andheri East"),
        (19.0728, 72.8998, "N-Ward", "Somaiya Vidyavihar"),
        (19.1176, 72.9060, "S-Ward", "Powai Hiranandani"),
        (19.1726, 72.9565, "T-Ward", "Mulund West"),
        (19.2307, 72.8567, "R/Central", "Borivali West"),
    ]

    for lat, lng, expected_ward, label in test_cases:
        res = resolve_coordinates_hierarchy(lat, lng)
        assert res["is_valid"] is True, f"Failed for {label}"
        assert res["authority_code"] == "BMC", f"Failed authority for {label}"
        assert res["ward_code"] == expected_ward, f"Expected {expected_ward} for {label}, got {res['ward_code']}"


def test_navi_mumbai_ward_interiors_resolution():
    """Verify coordinates inside Navi Mumbai resolve to NMMC authority and appropriate ward office."""
    test_cases = [
        (19.0770, 72.9985, "NMMC-Vashi", "Vashi Sector 17"),
        (19.0144, 73.0380, "NMMC-Belapur", "CBD Belapur"),
        (19.0330, 73.0197, "NMMC-Nerul", "Nerul West"),
        (19.1027, 73.0031, "NMMC-KoparKhairane", "Kopar Khairane"),
        (19.1579, 72.9935, "NMMC-Airoli", "Airoli"),
        (19.1865, 72.9999, "NMMC-Digha", "Digha"),
    ]

    for lat, lng, expected_ward, label in test_cases:
        res = resolve_coordinates_hierarchy(lat, lng)
        assert res["is_valid"] is True, f"Failed for {label}"
        assert res["authority_code"] == "NMMC", f"Failed authority for {label}"
        assert res["ward_code"] == expected_ward, f"Expected {expected_ward} for {label}, got {res['ward_code']}"


def test_strict_exclusion_of_neighboring_jurisdictions():
    """Verify that areas outside BMC and NMMC (TMC, MBMC, PMC, CIDCO Kharghar) are rejected."""
    excluded_locations = [
        (19.0473, 73.0699, "Kharghar (CIDCO / Panvel Municipal Corporation)"),
        (18.9894, 73.1175, "Panvel City (Panvel Municipal Corporation)"),
        (19.2183, 72.9781, "Thane City (Thane Municipal Corporation)"),
        (19.2813, 72.8564, "Mira Road (Mira-Bhayandar Municipal Corporation)"),
        (18.9750, 73.0250, "Ulwe (CIDCO jurisdiction outside NMMC)"),
        (28.6139, 77.2090, "Delhi (External national point)"),
        (18.9100, 72.7500, "Offshore Arabian Sea"),
    ]

    for lat, lng, label in excluded_locations:
        res = resolve_coordinates_hierarchy(lat, lng)
        assert res["is_valid"] is False, f"Expected {label} to be rejected, but got is_valid=True"
        assert res["error"] == OUT_OF_BOUNDS_ERROR


def test_sub_ward_pending_behavior():
    """
    Verify that when a coordinate falls inside an administrative ward but has no verified
    sub-ward polygon configured, it returns sub_ward_pending rather than assigning a random nearby unit.
    """
    # Point in Mulund West (T-Ward) where no operational sub-wards are pre-configured
    res = resolve_coordinates_hierarchy(19.1726, 72.9565)
    assert res["is_valid"] is True
    assert res["ward_code"] == "T-Ward"
    assert res["sub_ward_code"] == "SUB-WARD-PENDING"
    assert "Pending" in res["sub_ward_name"]
    assert res["is_official_sub_ward"] is False
    assert res["requires_admin_review"] is True


def test_operational_sub_wards_attributes():
    """Verify all operational sub-wards adhere to non-official designation contracts."""
    assert len(CIVILENS_OPERATIONAL_SUB_WARDS) > 0
    for sw in CIVILENS_OPERATIONAL_SUB_WARDS:
        assert sw["is_official"] is False
        assert sw["operational_type"] == "CIVILENS_OPERATIONAL_SUB_WARD"
        assert sw["id"].startswith("SUB-")
        assert sw["ward_id"]
        assert sw["sub_ward_code"]
        assert sw["name"]

