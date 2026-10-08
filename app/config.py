import os
from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "CiviLens — Civic Issue Intelligence Platform"
    version: str = "1.0.0"
    env: str = os.getenv("CIVILENS_ENV", "development")
    enable_demo_fallback: bool = os.getenv("ENABLE_DEMO_FALLBACK", "true").lower() == "true"
    enable_yolo: bool = os.getenv("ENABLE_YOLO_INFERENCE", "false").lower() == "true"
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "models/yolov8n_rdd.pt")
    default_lat: float = float(os.getenv("DEFAULT_LATITUDE", "19.0760"))
    default_lng: float = float(os.getenv("DEFAULT_LONGITUDE", "72.8777"))

settings = Settings()
