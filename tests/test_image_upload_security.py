import io
import uuid
from pathlib import Path
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)

def create_valid_image_bytes(fmt: str = "JPEG", size=(120, 120), color=(200, 50, 50)) -> bytes:
    """Generates valid image bytes in memory."""
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ------------------------------------------------------------------------------
# 1. Valid JPEG Upload
# ------------------------------------------------------------------------------
def test_1_valid_jpeg_upload():
    jpeg_bytes = create_valid_image_bytes(fmt="JPEG")
    files = {"file": ("road_damage.jpg", jpeg_bytes, "image/jpeg")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "uploadId" in data
    assert data["contentType"] == "image/jpeg"
    assert data["previewUrl"] == f"/api/v1/uploads/{data['uploadId']}"
    assert data["sizeBytes"] == len(jpeg_bytes)


# ------------------------------------------------------------------------------
# 2. Valid PNG Upload
# ------------------------------------------------------------------------------
def test_2_valid_png_upload():
    png_bytes = create_valid_image_bytes(fmt="PNG")
    files = {"file": ("pothole.png", png_bytes, "image/png")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "uploadId" in data
    assert data["contentType"] == "image/png"
    assert data["sizeBytes"] == len(png_bytes)


# ------------------------------------------------------------------------------
# 3. Valid WebP Upload
# ------------------------------------------------------------------------------
def test_3_valid_webp_upload():
    webp_bytes = create_valid_image_bytes(fmt="WEBP")
    files = {"file": ("debris.webp", webp_bytes, "image/webp")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "uploadId" in data
    assert data["contentType"] == "image/webp"
    assert data["sizeBytes"] == len(webp_bytes)


# ------------------------------------------------------------------------------
# 4. Corrupt Image Rejection
# ------------------------------------------------------------------------------
def test_4_corrupt_image_rejection():
    corrupt_bytes = b"\xff\xd8\xff\xe0CORRUPT_RANDOM_GARBAGE_BYTES_1234567890"
    files = {"file": ("broken.jpg", corrupt_bytes, "image/jpeg")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 400
    assert "Corrupt or invalid" in res.json()["detail"] or "decode" in res.json()["detail"]


# ------------------------------------------------------------------------------
# 5. Unsupported Format Rejection (e.g. GIF, BMP, TIFF)
# ------------------------------------------------------------------------------
def test_5_unsupported_format_rejection():
    # Create valid GIF
    img = Image.new("P", (50, 50))
    buf = io.BytesIO()
    img.save(buf, format="GIF")
    gif_bytes = buf.getvalue()

    files = {"file": ("animation.gif", gif_bytes, "image/gif")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 415
    assert "Unsupported image format" in res.json()["detail"]


# ------------------------------------------------------------------------------
# 6. Empty Upload Rejection
# ------------------------------------------------------------------------------
def test_6_empty_upload_rejection():
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


# ------------------------------------------------------------------------------
# 7. Oversized Upload Rejection (> 10 MB)
# ------------------------------------------------------------------------------
def test_7_oversized_upload_rejection():
    # 10 MB + 1024 bytes
    oversized_bytes = b"X" * (10 * 1024 * 1024 + 1024)
    files = {"file": ("huge_file.jpg", oversized_bytes, "image/jpeg")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 413
    assert "exceeds maximum allowed size" in res.json()["detail"]


# ------------------------------------------------------------------------------
# 8. Spoofed Content-Type Rejection (HTML/Script labeled as image/jpeg)
# ------------------------------------------------------------------------------
def test_8_spoofed_content_type_rejection():
    script_bytes = b"<html><script>alert('malicious')</script></html>"
    files = {"file": ("not_really_an_image.jpg", script_bytes, "image/jpeg")}
    res = client.post("/api/v1/upload", files=files)
    # Backend must verify actual decoded bytes, rejecting spoofed content
    assert res.status_code == 400
    assert "Corrupt or invalid" in res.json()["detail"]


# ------------------------------------------------------------------------------
# 9. Path-Traversal Filenames Protection
# ------------------------------------------------------------------------------
def test_9_path_traversal_filenames_protected():
    jpeg_bytes = create_valid_image_bytes(fmt="JPEG")
    # Malicious client-submitted filename containing path traversal
    files = {"file": ("../../../../etc/passwd.jpg", jpeg_bytes, "image/jpeg")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    upload_id = data["uploadId"]

    # Verify that the server stored the file using a generated UUID inside upload_dir
    upload_dir = settings.resolved_upload_dir
    stored_path = upload_dir / f"{upload_id}.jpg"
    assert stored_path.exists()
    assert stored_path.resolve().is_relative_to(upload_dir.resolve())
    assert not (upload_dir / "../../../../etc/passwd.jpg").exists()


# ------------------------------------------------------------------------------
# 10. Safe Image Retrieval by Upload ID
# ------------------------------------------------------------------------------
def test_10_safe_image_retrieval_by_upload_id():
    jpeg_bytes = create_valid_image_bytes(fmt="JPEG")
    upload_res = client.post("/api/v1/upload", files={"file": ("test.jpg", jpeg_bytes, "image/jpeg")})
    assert upload_res.status_code == 200
    upload_id = upload_res.json()["uploadId"]

    # Retrieve through safe preview endpoint
    get_res = client.get(f"/api/v1/uploads/{upload_id}")
    assert get_res.status_code == 200
    assert get_res.headers["content-type"] == "image/jpeg"
    assert get_res.content == jpeg_bytes


# ------------------------------------------------------------------------------
# 11. Unknown Upload ID Rejection (404)
# ------------------------------------------------------------------------------
def test_11_unknown_upload_id_rejection():
    random_uuid = str(uuid.uuid4())
    res = client.get(f"/api/v1/uploads/{random_uuid}")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

    # Traversal attempt on GET endpoint
    traversal_res = client.get("/api/v1/uploads/../../etc/passwd")
    assert traversal_res.status_code in [404, 400]


# ------------------------------------------------------------------------------
# 12. Uploaded Image Reference Accepted by Analysis Pipeline
# ------------------------------------------------------------------------------
def test_12_uploaded_image_accepted_by_pipeline():
    jpeg_bytes = create_valid_image_bytes(fmt="JPEG")
    upload_res = client.post("/api/v1/upload", files={"file": ("pothole.jpg", jpeg_bytes, "image/jpeg")})
    assert upload_res.status_code == 200
    upload_id = upload_res.json()["uploadId"]

    # Analyze complaint referencing uploadId
    analyze_res = client.post("/api/v1/analyze", json={
        "complaintText": "Deep road crater causing bike falls",
        "location": "Vidyavihar",
        "uploadId": upload_id
    })
    assert analyze_res.status_code == 200
    data = analyze_res.json()
    assert data["uploadId"] == upload_id
    assert data["imageUrl"] == f"/api/v1/uploads/{upload_id}"


# ------------------------------------------------------------------------------
# 13. Issue Creation Preserves Uploaded-Image Reference
# ------------------------------------------------------------------------------
def test_13_issue_creation_preserves_upload_reference():
    png_bytes = create_valid_image_bytes(fmt="PNG")
    upload_res = client.post("/api/v1/upload", files={"file": ("leak.png", png_bytes, "image/png")})
    upload_id = upload_res.json()["uploadId"]

    # Create issue with uploadId
    create_res = client.post("/api/v1/issues", json={
        "complaintText": "Major pipe overflow flooding pavement on LBS Marg",
        "location": "LBS Marg",
        "uploadId": upload_id,
        "source": "citizen_app"
    })
    assert create_res.status_code == 201
    created_issue = create_res.json()
    assert created_issue["uploadId"] == upload_id
    assert created_issue["imageUrl"] == f"/api/v1/uploads/{upload_id}"

    # Verify retrieval from persistent store retains uploadId
    get_res = client.get(f"/api/v1/issues/{created_issue['issueId']}")
    assert get_res.status_code == 200
    assert get_res.json()["uploadId"] == upload_id


# ------------------------------------------------------------------------------
# 14. Failed Persistence Cleans Up Partial Uploaded Files
# ------------------------------------------------------------------------------
def test_14_failed_persistence_cleans_up_file(monkeypatch):
    from app.services.upload_service import upload_service

    # Monkeypatch repository save_upload to simulate database failure
    def mock_failing_save_upload(*args, **kwargs):
        raise RuntimeError("Simulated database failure during upload persistence")

    monkeypatch.setattr(upload_service.repository, "save_upload", mock_failing_save_upload)

    jpeg_bytes = create_valid_image_bytes(fmt="JPEG")
    files = {"file": ("test_fail.jpg", jpeg_bytes, "image/jpeg")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 500

    # Ensure no orphaned files remain in upload directory
    upload_dir = settings.resolved_upload_dir
    orphans = list(upload_dir.glob("*test_fail*"))
    assert len(orphans) == 0


# ------------------------------------------------------------------------------
# 15. Allowed CORS Origin
# ------------------------------------------------------------------------------
def test_15_allowed_cors_origin():
    res = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"


# ------------------------------------------------------------------------------
# 16. Disallowed CORS Origin
# ------------------------------------------------------------------------------
def test_16_disallowed_cors_origin():
    res = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://malicious-unauthorized-attacker.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    # Disallowed origin must not receive Access-Control-Allow-Origin header
    assert res.headers.get("access-control-allow-origin") is None


# ------------------------------------------------------------------------------
# 17. Frontend Upload Client Matches Backend Contract
# ------------------------------------------------------------------------------
def test_17_frontend_upload_contract_matches():
    jpeg_bytes = create_valid_image_bytes(fmt="JPEG")
    res = client.post("/api/v1/upload", files={"file": ("inspect.jpg", jpeg_bytes, "image/jpeg")})
    assert res.status_code == 200
    data = res.json()

    # Exact contract expected by frontend/src/services/api.ts
    assert isinstance(data["uploadId"], str)
    assert isinstance(data["previewUrl"], str)
    assert data["previewUrl"].startswith("/api/v1/uploads/")
    assert isinstance(data["contentType"], str)
    assert isinstance(data["sizeBytes"], int)


# ------------------------------------------------------------------------------
# 18. Arbitrary Path Traversal & Remote SSRF Reference Rejected
# ------------------------------------------------------------------------------
def test_18_arbitrary_image_path_rejected_in_analysis():
    # Arbitrary local file traversal attempt
    res_traversal = client.post("/api/v1/analyze", json={
        "complaintText": "Pothole near gate",
        "imageUrl": "../../etc/passwd"
    })
    assert res_traversal.status_code == 400
    assert "Invalid image reference" in res_traversal.json()["detail"]

    # Arbitrary external remote SSRF attempt
    res_ssrf = client.post("/api/v1/analyze", json={
        "complaintText": "Pothole near gate",
        "imageUrl": "http://169.254.169.254/latest/meta-data/"
    })
    assert res_ssrf.status_code == 400
    assert "Invalid image reference" in res_ssrf.json()["detail"]
