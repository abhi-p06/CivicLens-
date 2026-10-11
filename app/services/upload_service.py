import io
import re
import uuid
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from fastapi import UploadFile, HTTPException, status
from PIL import Image

from app.config import settings, PROJECT_ROOT
from app.db.repository import SqliteIssueRepository

logger = logging.getLogger(__name__)

# Enforce strict decompression bomb protection
Image.MAX_IMAGE_PIXELS = 25_000_000

# UUID format regex for strict upload ID validation
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

# Explicit controlled allowlist for demo fixtures only (active during demo scenarios)
DEMO_FIXTURE_ALLOWLIST = {
    "data/sample_pothole.jpg",
    "data/sample_garbage.jpg",
    "data/sample_water_leak.jpg",
    "data/patrol_survey_pothole.jpg",
    "data/sample_repaired_pothole.jpg",
    "data/sample_cleared_site.jpg",
    "data/test_samples/pothole_multibox.jpg",
    "data/test_samples/alligator_crack.jpg",
    "data/test_samples/pothole_and_crack.jpg",
    "data/test_samples/clean_road.jpg",
    "data/test_samples/repair_pothole_before.jpg",
    "data/test_samples/repair_pothole_after_repaired.jpg",
    "data/test_samples/incompatible_scene.jpg",
    "data/test_samples/corrupt_file.jpg",
    "data/test_samples/litter.jpg",
    "data/test_samples/bottle.jpg",
    "data/test_samples/cup.jpg",
    "data/test_samples/street_flooding.jpg",
    "data/repaired_road_patch.jpg",
    "data/pothole_still_broken.jpg",
    "/sample_pothole.jpg",
    "/sample_repaired_pothole.jpg",
    "sample_pothole.jpg",
    "sample_repaired_pothole.jpg"
}

ALLOWED_FORMAT_MAPPING = {
    "JPEG": (".jpg", "image/jpeg"),
    "PNG": (".png", "image/png"),
    "WEBP": (".webp", "image/webp")
}

class UploadService:
    """
    Secure Image Upload and Storage Service.
    Enforces chunked reading, file size limits, decompression bomb defenses,
    decoded byte format verification, and safe server-generated path resolution.
    """

    def __init__(self, repository: Optional[SqliteIssueRepository] = None):
        self.repository = repository or SqliteIssueRepository()

    async def save_image_upload(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validates and safely stores an uploaded image file.
        Returns upload metadata including uploadId, previewUrl, contentType, sizeBytes.
        """
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        chunk_size = 64 * 1024  # 64 KB chunks
        buffer = bytearray()

        # 1. Bounded chunked reading to prevent memory exhaustion
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            buffer.extend(chunk)
            if len(buffer) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail=f"Uploaded image exceeds maximum allowed size of {settings.max_upload_size_mb} MB"
                )

        if len(buffer) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )

        # 2. Verify decoded image bytes and format using Pillow
        try:
            with Image.open(io.BytesIO(buffer)) as img:
                img.verify()
        except Image.DecompressionBombError:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="Image dimensions exceed safety limit (decompression bomb protection)"
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupt or invalid image content"
            )

        # Re-open for format and dimension verification
        try:
            with Image.open(io.BytesIO(buffer)) as img:
                raw_format = (img.format or "").upper()
                width, height = img.size
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to decode image headers"
            )

        if raw_format not in ALLOWED_FORMAT_MAPPING:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported image format '{raw_format}'. Accepted formats are JPEG, PNG, and WebP."
            )

        # Dimension safety limit: maximum 6000x6000px or 25 million pixels
        if width > 6000 or height > 6000 or (width * height) > 25_000_000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image dimensions ({width}x{height}) exceed maximum allowed dimension limit of 6000x6000px."
            )

        ext, content_type = ALLOWED_FORMAT_MAPPING[raw_format]
        upload_id = str(uuid.uuid4())
        stored_filename = f"{upload_id}{ext}"
        upload_dir = settings.resolved_upload_dir
        target_path = upload_dir / stored_filename

        # Path traversal guard
        if not target_path.resolve().is_relative_to(upload_dir.resolve()):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid target storage resolution"
            )

        # Sanitize original filename for audit logging
        orig_name = Path(file.filename or "unknown").name if file.filename else None

        # 3. Safe write to disk with cleanup on failure
        try:
            with open(target_path, "wb") as f:
                f.write(buffer)
        except Exception as e:
            logger.error(f"Failed to write uploaded file to disk: {e}")
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist uploaded image to disk"
            )

        # 4. Save metadata in SQLite
        try:
            self.repository.save_upload(
                upload_id=upload_id,
                filename=stored_filename,
                content_type=content_type,
                size_bytes=len(buffer),
                original_filename=orig_name
            )
        except Exception as e:
            logger.error(f"Failed to save upload metadata to database: {e}")
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist upload metadata"
            )

        return {
            "uploadId": upload_id,
            "previewUrl": f"/api/v1/uploads/{upload_id}",
            "contentType": content_type,
            "sizeBytes": len(buffer)
        }

    def resolve_upload_file(self, upload_id: str) -> Tuple[Path, str]:
        """
        Safely retrieves the disk path and MIME type for an upload ID.
        Rejects unknown IDs, path traversals, or files outside the upload directory.
        """
        clean_id = str(upload_id).strip()
        if not UUID_PATTERN.match(clean_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Upload '{clean_id}' not found"
            )

        record = self.repository.get_upload(clean_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Upload '{clean_id}' not found"
            )

        upload_dir = settings.resolved_upload_dir
        file_path = upload_dir / record.filename

        if not file_path.resolve().is_relative_to(upload_dir.resolve()) or not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stored image file missing from server"
            )

        return file_path, record.content_type

    def resolve_image_reference(
        self,
        upload_id: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Validates and resolves image references submitted for complaint analysis.
        Returns:
            (server_filesystem_path, preview_url, upload_id)
        
        Strictly forbids:
        - Arbitrary filesystem paths (e.g. '../../etc/passwd')
        - Arbitrary remote URLs that could introduce SSRF
        """
        # 1. Primary: Direct uploadId
        if upload_id and str(upload_id).strip():
            clean_id = str(upload_id).strip()
            path, mime = self.resolve_upload_file(clean_id)
            return str(path), f"/api/v1/uploads/{clean_id}", clean_id

        # 2. Secondary: imageUrl reference
        if image_url and str(image_url).strip():
            clean_url = str(image_url).strip()

            # Check if this points to an uploaded preview URL (/api/v1/uploads/<uuid>)
            if "/uploads/" in clean_url:
                extracted_id = clean_url.split("/uploads/")[-1].split("?")[0].strip()
                path, mime = self.resolve_upload_file(extracted_id)
                return str(path), f"/api/v1/uploads/{extracted_id}", extracted_id

            # Check against controlled demo fixture allowlist or internal demo domain
            norm_path = clean_url.lstrip("/")
            is_demo_fixture = (
                clean_url in DEMO_FIXTURE_ALLOWLIST
                or norm_path in DEMO_FIXTURE_ALLOWLIST
                or clean_url.startswith(("https://civic.internal/", "http://civic.internal/"))
            )

            if settings.civilens_demo_mode and is_demo_fixture:
                if not clean_url.startswith(("https://", "http://")):
                    resolved_fixture = PROJECT_ROOT / norm_path
                    if not resolved_fixture.resolve().is_relative_to(PROJECT_ROOT.resolve()):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Path traversal detected in demo fixture reference"
                        )
                    return str(resolved_fixture), clean_url, None
                return clean_url, clean_url, None

            # Untrusted remote URL or arbitrary local path
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image reference '{clean_url}'. Arbitrary paths and remote URLs are prohibited. Please upload your image via POST /api/v1/upload or choose a supported demo scenario."
            )

        return None, None, None

upload_service = UploadService()
