import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.issue import IssueCategory

client = TestClient(app)

def test_mumbai_and_navi_mumbai_coordinates_accepted():
    """Verify complaints within Mumbai and Navi Mumbai boundaries are accepted."""
    # 1. Somaiya Vidyavihar, Mumbai
    res_mumbai = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Deep pothole near Somaiya Vidyavihar campus gate",
            "location": "Somaiya Vidyavihar",
            "latitude": 19.0728,
            "longitude": 72.8998,
            "location_method": "gps",
            "category": "Roads & Footpaths",
            "source": "citizen_portal"
        }
    )
    assert res_mumbai.status_code == 201
    data_mumbai = res_mumbai.json()
    assert data_mumbai["latitude"] == pytest.approx(19.0728, abs=0.001)
    assert data_mumbai["longitude"] == pytest.approx(72.8998, abs=0.001)
    assert data_mumbai["ward"] == "N-Ward"
    assert data_mumbai.get("location_method") == "gps"
    assert data_mumbai["metadata"].get("locationMethod") == "gps"

    # 2. Vashi, Navi Mumbai
    res_vashi = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Overflowing garbage dump in Sector 17 Vashi market",
            "location": "Sector 17, Vashi",
            "latitude": 19.0771,
            "longitude": 72.9986,
            "location_method": "manual",
            "category": "Sanitation & Garbage",
            "source": "citizen_portal"
        }
    )
    assert res_vashi.status_code == 201
    data_vashi = res_vashi.json()
    assert data_vashi["latitude"] == pytest.approx(19.0771, abs=0.001)
    assert data_vashi["longitude"] == pytest.approx(72.9986, abs=0.001)
    assert "Navi Mumbai" in data_vashi["ward"] or "NMMC" in data_vashi["ward"]
    assert data_vashi.get("location_method") == "manual"
    assert data_vashi["metadata"].get("locationMethod") == "manual"

    # 3. CBD Belapur, Navi Mumbai
    res_belapur = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Asphalt depression near Sector 11 CBD Belapur",
            "location": "Sector 11, CBD Belapur",
            "latitude": 19.0144,
            "longitude": 73.0380,
            "location_method": "gps",
            "category": "Roads & Footpaths",
            "source": "citizen_portal"
        }
    )
    assert res_belapur.status_code == 201
    data_belapur = res_belapur.json()
    assert data_belapur["latitude"] == pytest.approx(19.0144, abs=0.001)
    assert data_belapur["longitude"] == pytest.approx(73.0380, abs=0.001)

def test_coordinates_outside_supported_boundary_rejected():
    """Verify complaints with coordinates outside Mumbai/Navi Mumbai are rejected with 400."""
    # Delhi coordinates
    res_delhi = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Pothole on Ring Road New Delhi",
            "location": "New Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "location_method": "gps"
        }
    )
    assert res_delhi.status_code == 400
    assert "CIVILENS currently supports complaints from Mumbai and Navi Mumbai only" in res_delhi.json()["detail"]

    # Pune coordinates
    res_pune = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Garbage issue near FC Road Pune",
            "location": "FC Road Pune",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "location_method": "manual"
        }
    )
    assert res_pune.status_code == 400
    assert "CIVILENS currently supports complaints from Mumbai and Navi Mumbai only" in res_pune.json()["detail"]

def test_missing_location_rejected_by_backend():
    """Verify that a complaint submitted without any location is rejected."""
    res_empty = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "",
            "location": "",
            "latitude": None,
            "longitude": None
        }
    )
    assert res_empty.status_code in [400, 422]

def test_geo_bounds_endpoint():
    """Verify the /api/v1/geo/bounds endpoint returns configured boundary."""
    res = client.get("/api/v1/geo/bounds")
    assert res.status_code == 200
    data = res.json()
    assert "min_lat" in data
    assert "max_lat" in data
    assert "min_lng" in data
    assert "max_lng" in data
    assert data["min_lat"] <= 18.85
    assert data["max_lat"] >= 19.30
    assert data["min_lng"] <= 72.80
    assert data["max_lng"] >= 73.15

def test_geo_reverse_geocode_endpoint():
    """Verify /api/v1/geo/reverse-geocode derives ward and landmark accurately."""
    # In-bounds query
    res = client.get("/api/v1/geo/reverse-geocode?lat=19.0728&lng=72.8998")
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert "ward" in data
    assert "address" in data

    # Out-of-bounds query
    res_out = client.get("/api/v1/geo/reverse-geocode?lat=28.6139&lng=77.2090")
    assert res_out.status_code == 200
    data_out = res_out.json()
    assert data_out["valid"] is False
    assert "CIVILENS currently supports complaints from Mumbai and Navi Mumbai only" in data_out["error"]

def test_geo_search_endpoint():
    """Verify /api/v1/geo/search returns Mumbai and Navi Mumbai suggestions."""
    res = client.get("/api/v1/geo/search?query=vashi")
    assert res.status_code == 200
    results = res.json()
    assert len(results) > 0
    assert any("Vashi" in r["name"] for r in results)

    res_ghatkopar = client.get("/api/v1/geo/search?query=ghatkopar")
    assert res_ghatkopar.status_code == 200
    assert any("Ghatkopar" in r["name"] for r in res_ghatkopar.json())

def test_gis_geojson_reflects_persisted_coordinates():
    """Verify GeoJSON endpoint includes valid coordinates for newly filed issue."""
    # Create issue with distinct coordinates
    res = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Clogged storm drain near Belapur station",
            "location": "CBD Belapur, Navi Mumbai",
            "latitude": 19.0144,
            "longitude": 73.0380,
            "location_method": "gps",
            "category": "Sanitation & Garbage"
        }
    )
    assert res.status_code == 201
    created_id = res.json()["issueId"]

    # Check GeoJSON
    geo_res = client.get("/api/v1/gis/geojson")
    assert geo_res.status_code == 200
    features = geo_res.json()["features"]
    matching = [f for f in features if f["properties"]["issueId"] == created_id]
    assert len(matching) == 1
    coords = matching[0]["geometry"]["coordinates"]
    # GeoJSON is [lng, lat]
    assert coords[0] == pytest.approx(73.0380, abs=0.001)
    assert coords[1] == pytest.approx(19.0144, abs=0.001)

