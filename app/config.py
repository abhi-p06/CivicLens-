import os
from pathlib import Path
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    app_name: str = "CiviLens — Civic Issue Intelligence Platform"
    version: str = "1.0.0"
    env: str = os.getenv("CIVILENS_ENV", "development")
    enable_demo_fallback: bool = os.getenv("ENABLE_DEMO_FALLBACK", "true").lower() == "true"
    enable_yolo: bool = os.getenv("ENABLE_YOLO_INFERENCE", "true").lower() == "true"
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "models/yolov8s_rdd2022.pt")
    waste_model_path: str = os.getenv("WASTE_MODEL_PATH", "models/taco_yolo11s.pt")
    yolo_confidence_threshold: float = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.15"))
    waste_confidence_threshold: float = float(os.getenv("WASTE_CONFIDENCE_THRESHOLD", "0.20"))
    yolo_iou_threshold: float = float(os.getenv("YOLO_IOU_THRESHOLD", "0.45"))
    yolo_image_size: int = int(os.getenv("YOLO_IMAGE_SIZE", "640"))
    yolo_device: str = os.getenv("YOLO_DEVICE", "cpu")
    default_lat: float = float(os.getenv("DEFAULT_LATITUDE", "19.0760"))
    default_lng: float = float(os.getenv("DEFAULT_LONGITUDE", "72.8777"))
    db_path: str = os.getenv("CIVILENS_DB_PATH", "data/civic_issues.db")
    civilens_demo_mode: bool = os.getenv("CIVILENS_DEMO_MODE", "true").lower() in ("true", "1", "yes")
    upload_dir: str = os.getenv("CIVILENS_UPLOAD_DIR", "uploads")
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    cors_allowed_origins: str = os.getenv(
        "CIVILENS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )
    auth_secret_key: str = os.getenv("CIVILENS_AUTH_SECRET_KEY", "dev-insecure-secret-key-change-in-production")
    inspector_api_key: str = os.getenv("CIVILENS_INSPECTOR_API_KEY", "")
    admin_api_key: str = os.getenv("CIVILENS_ADMIN_API_KEY", "")
    allow_dev_tokens: bool = os.getenv("CIVILENS_ALLOW_DEV_TOKENS", "true").lower() in ("true", "1", "yes")

    @property
    def resolved_db_path(self) -> Path:
        p = Path(self.db_path)
        if not p.is_absolute():
            return PROJECT_ROOT / p
        return p

    @property
    def resolved_upload_dir(self) -> Path:
        p = Path(self.upload_dir)
        target = p if p.is_absolute() else (PROJECT_ROOT / p)
        target.mkdir(parents=True, exist_ok=True)
        return target

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

settings = Settings()

