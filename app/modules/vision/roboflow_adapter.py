import os
import time
import json
import hashlib
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image

from app.config import settings
from app.models.issue import VisualDetectionDetail

logger = logging.getLogger("civilens.vision.roboflow")

def compute_image_sha256(image_path: str) -> str:
    """Computes SHA-256 hash of an image file for deterministic caching."""
    h = hashlib.sha256()
    with open(image_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def mask_api_key(key: str) -> str:
    """Masks API key for safe logging (e.g. 'NIae...0duw')."""
    if not key or len(key) < 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"

def log_roboflow_diagnostic(
    model_id: str,
    response_status: Any,
    latency_ms: float,
    prediction_count: int,
    success: bool,
    cached: bool = False,
    error_category: Optional[str] = None,
    error_message: Optional[str] = None
) -> None:
    """
    Emits structured diagnostic telemetry for Roboflow serverless calls.
    Guarantees private API keys and image byte contents are never logged.
    """
    sanitized_error = error_message
    if sanitized_error and settings.roboflow_api_key and settings.roboflow_api_key in sanitized_error:
        sanitized_error = sanitized_error.replace(settings.roboflow_api_key, mask_api_key(settings.roboflow_api_key))

    record = {
        "provider": "roboflow_serverless",
        "model_id": model_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "response_status": response_status,
        "latency_ms": round(latency_ms, 2),
        "prediction_count": prediction_count,
        "success": success,
        "cached": cached,
        "error_category": error_category,
        "error_message": sanitized_error
    }
    print(f"[ROBOFLOW_DIAGNOSTIC] {json.dumps(record)}", flush=True)
    if success:
        logger.info(f"[ROBOFLOW_DIAGNOSTIC] {json.dumps(record)}")
    else:
        logger.warning(f"[ROBOFLOW_DIAGNOSTIC] {json.dumps(record)}")

class RoboflowHostedAdapter:
    """
    Modular Adapter for Roboflow Hosted Inference Models:
    1. Potholes: 'potholes-krmk8/2' (YOLO26 Object Detection)
    2. Garbage: 'garbage_detection-wvzwv-n8vsv/1' (RF-DETR Nano)

    Features:
    - Lazy singleton HTTP client initialization with header-based auth
    - Persistent deterministic SHA-256 result caching to protect API credit quotas
    - Explicit HTTP 401/403/404/429 status and transient error handling
    - Bounding-box normalization to CIVILENS standard: [ymin, xmin, ymax, xmax] in [0.0, 1.0]
    - Zero synthetic/fake fallback boxes: honest empty list when no targets detected
    """

    def __init__(self):
        self.api_key = settings.roboflow_api_key
        self.api_url = getattr(settings, "roboflow_api_url", "https://serverless.roboflow.com")
        self.pothole_model_id = settings.roboflow_pothole_model_id
        self.garbage_model_id = settings.roboflow_garbage_model_id
        self.timeout_sec = settings.roboflow_timeout_sec
        self._client = None
        self._lock = threading.Lock()
        self._cache_lock = threading.Lock()

        # Cache file
        self.cache_dir = Path(settings.roboflow_cache_dir)
        self.cache_file = self.cache_dir / "roboflow_predictions_cache.json"
        self._cache: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self):
        with self._cache_lock:
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                if self.cache_file.exists():
                    with open(self.cache_file, "r", encoding="utf-8") as f:
                        self._cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load Roboflow cache: {e}")
                self._cache = {}

    def _save_cache(self):
        with self._cache_lock:
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save Roboflow cache: {e}")

    def is_configured(self) -> bool:
        """Checks if valid Roboflow API key is configured."""
        return bool(self.api_key and len(self.api_key.strip()) >= 8)

    def _get_client(self):
        """Thread-safe lazy initialization of InferenceHTTPClient with header-based auth."""
        with self._lock:
            if self._client is None and self.is_configured():
                try:
                    import warnings
                    from inference_sdk import InferenceHTTPClient, InferenceConfiguration
                    from inference_sdk.http.client import InferenceSDKGuidanceWarning
                    warnings.filterwarnings("ignore", category=InferenceSDKGuidanceWarning)
                    config = InferenceConfiguration(api_key_transport="both")
                    client = InferenceHTTPClient(
                        api_url=self.api_url,
                        api_key=self.api_key.strip()
                    )
                    client.use_configuration(config)
                    self._client = client
                    logger.info(f"Initialized Roboflow client at {self.api_url} with key {mask_api_key(self.api_key)}")
                except Exception as e:
                    logger.error(f"Failed to initialize Roboflow client: {e}")
                    self._client = None
            return self._client

    def resolve_model_info(self, task_or_category: str) -> Tuple[str, str, str, str]:
        """
        Maps civic category to appropriate Roboflow hosted model:
        Returns: (model_id, architecture, task_name, target_class)
        """
        cat_lower = (task_or_category or "").lower()
        if any(k in cat_lower for k in ["sanitation", "garbage", "waste", "trash", "litter"]):
            return (
                self.garbage_model_id,
                "RF-DETR Nano",
                "SANITATION",
                "garbage"
            )
        else:
            # Default to road damage / pothole model
            return (
                self.pothole_model_id,
                "YOLO26",
                "ROAD_DAMAGE",
                "Pothole"
            )

    def infer(
        self,
        image_path: str,
        category_hint: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Executes Roboflow hosted serverless inference with normalized coordinates,
        structured diagnostic logging, and persistent result caching.
        """
        model_id, architecture, task, primary_target = self.resolve_model_info(category_hint or "")

        if not os.path.exists(image_path):
            log_roboflow_diagnostic(
                model_id=model_id,
                response_status=404,
                latency_ms=0.0,
                prediction_count=0,
                success=False,
                error_category="IMAGE_NOT_FOUND",
                error_message=f"Image file not found: {image_path}"
            )
            return {
                "provider": "roboflow",
                "status": "ERROR",
                "error": f"Image file not found: {image_path}",
                "errorCategory": "IMAGE_NOT_FOUND",
                "modelId": model_id,
                "architecture": architecture,
                "task": task,
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "imageDimensions": None,
                "inferenceTimeMs": 0.0,
                "cached": False
            }

        # Check API key configuration
        if not self.is_configured():
            log_roboflow_diagnostic(
                model_id=model_id,
                response_status=401,
                latency_ms=0.0,
                prediction_count=0,
                success=False,
                error_category="AUTH_ERROR",
                error_message="ROBOFLOW_API_KEY is not configured or invalid."
            )
            return {
                "provider": "roboflow",
                "status": "UNAVAILABLE",
                "error": "ROBOFLOW_API_KEY is not configured or invalid.",
                "errorCategory": "AUTH_ERROR",
                "modelId": model_id,
                "architecture": architecture,
                "task": task,
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "imageDimensions": None,
                "inferenceTimeMs": 0.0,
                "cached": False
            }

        # 1. Deterministic image hashing
        try:
            img_hash = compute_image_sha256(image_path)
        except Exception as e:
            log_roboflow_diagnostic(
                model_id=model_id,
                response_status=500,
                latency_ms=0.0,
                prediction_count=0,
                success=False,
                error_category="UNKNOWN",
                error_message=f"Failed to compute image hash: {e}"
            )
            return {
                "provider": "roboflow",
                "status": "ERROR",
                "error": f"Failed to compute image hash: {e}",
                "errorCategory": "UNKNOWN",
                "modelId": model_id,
                "architecture": architecture,
                "task": task,
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "imageDimensions": None,
                "inferenceTimeMs": 0.0,
                "cached": False
            }

        cache_key = f"{img_hash}:{model_id}"
        cache_enabled = getattr(settings, "roboflow_cache_enabled", True)

        # 2. Check cache
        if use_cache and cache_enabled and cache_key in self._cache:
            cached_data = self._cache[cache_key]
            logger.info(f"Using cached Roboflow prediction for {Path(image_path).name} ({cache_key[:16]}...)")
            raw_cached_preds = cached_data.get("raw_response", {}).get("predictions", [])
            log_roboflow_diagnostic(
                model_id=model_id,
                response_status=200,
                latency_ms=cached_data.get("latency_ms", 0.0),
                prediction_count=len(raw_cached_preds),
                success=True,
                cached=True
            )
            return self._normalize_predictions(
                raw_response=cached_data["raw_response"],
                image_path=image_path,
                model_id=model_id,
                architecture=architecture,
                task=task,
                latency_ms=cached_data.get("latency_ms", 0.0),
                cached=True
            )

        # 3. Execute hosted inference
        client = self._get_client()
        if client is None:
            log_roboflow_diagnostic(
                model_id=model_id,
                response_status=500,
                latency_ms=0.0,
                prediction_count=0,
                success=False,
                error_category="UNKNOWN",
                error_message="Roboflow client could not be initialized."
            )
            return {
                "provider": "roboflow",
                "status": "ERROR",
                "error": "Roboflow client could not be initialized.",
                "errorCategory": "UNKNOWN",
                "modelId": model_id,
                "architecture": architecture,
                "task": task,
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "imageDimensions": None,
                "inferenceTimeMs": 0.0,
                "cached": False
            }

        t0 = time.time()
        max_retries = 2
        raw_res = None
        last_error = None
        last_status_code = None
        error_cat = "UNKNOWN"

        for attempt in range(max_retries):
            try:
                raw_res = client.infer(image_path, model_id=model_id)
                break
            except Exception as e:
                err_str = str(e)
                status_code = getattr(e, "status_code", None)
                if status_code is None and hasattr(e, "response") and hasattr(e.response, "status_code"):
                    status_code = e.response.status_code

                err_lower = err_str.lower()
                # Categorize error
                if status_code in (401, 403) or "401" in err_str or "403" in err_str or "unauthorized" in err_lower or "forbidden" in err_lower:
                    last_status_code = status_code or 401
                    error_cat = "AUTH_ERROR"
                    last_error = f"Authentication failed (HTTP {last_status_code}): Invalid or inactive Roboflow API key."
                    logger.error(f"Roboflow 401/403: {last_error}")
                    break
                elif status_code == 404 or "404" in err_str or "not found" in err_lower:
                    last_status_code = status_code or 404
                    error_cat = "MODEL_NOT_FOUND"
                    last_error = f"Model not found (HTTP 404): Check model ID '{model_id}'."
                    logger.error(f"Roboflow 404: {last_error}")
                    break
                elif status_code == 429 or "429" in err_str or "rate limit" in err_lower or "quota" in err_lower:
                    last_status_code = status_code or 429
                    error_cat = "RATE_LIMIT"
                    last_error = "Rate limit / quota exceeded (HTTP 429): Monthly free API credit exhausted."
                    logger.error(f"Roboflow 429: {last_error}")
                    break
                elif status_code in (408, 504) or isinstance(e, (TimeoutError, ConnectionError)) or "timeout" in err_lower or "timed out" in err_lower or "connection" in err_lower:
                    last_status_code = status_code or 504
                    error_cat = "NETWORK_TIMEOUT"
                    last_error = f"Network timeout connecting to Roboflow serverless gateway: {err_str}"
                    logger.warning(f"Roboflow timeout attempt {attempt + 1}: {err_str}")
                    if attempt < max_retries - 1:
                        time.sleep(1.0)
                else:
                    last_status_code = status_code or 500
                    error_cat = "UNKNOWN"
                    last_error = f"Inference request error: {err_str}"
                    logger.warning(f"Roboflow request attempt {attempt + 1} failed: {err_str}")
                    if attempt < max_retries - 1:
                        time.sleep(1.0)

        elapsed_ms = (time.time() - t0) * 1000.0

        if raw_res is None:
            log_roboflow_diagnostic(
                model_id=model_id,
                response_status=last_status_code or 500,
                latency_ms=elapsed_ms,
                prediction_count=0,
                success=False,
                cached=False,
                error_category=error_cat,
                error_message=last_error
            )
            return {
                "provider": "roboflow",
                "status": "ERROR",
                "error": last_error or "Unknown error calling Roboflow API",
                "errorCategory": error_cat,
                "modelId": model_id,
                "architecture": architecture,
                "task": task,
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "imageDimensions": None,
                "inferenceTimeMs": round(elapsed_ms, 2),
                "cached": False
            }

        # 4. Save to cache
        if use_cache and cache_enabled:
            self._cache[cache_key] = {
                "raw_response": raw_res,
                "latency_ms": round(elapsed_ms, 2),
                "timestamp": time.time()
            }
            self._save_cache()

        # 5. Log success telemetry
        raw_preds = raw_res.get("predictions", [])
        log_roboflow_diagnostic(
            model_id=model_id,
            response_status=200,
            latency_ms=elapsed_ms,
            prediction_count=len(raw_preds),
            success=True,
            cached=False
        )

        # 6. Normalize results
        return self._normalize_predictions(
            raw_response=raw_res,
            image_path=image_path,
            model_id=model_id,
            architecture=architecture,
            task=task,
            latency_ms=round(elapsed_ms, 2),
            cached=False
        )

    def _normalize_predictions(
        self,
        raw_response: Dict[str, Any],
        image_path: str,
        model_id: str,
        architecture: str,
        task: str,
        latency_ms: float,
        cached: bool
    ) -> Dict[str, Any]:
        """
        Normalizes Roboflow pixel-center bounding boxes into CIVILENS format:
        [ymin, xmin, ymax, xmax] in normalized range [0.0, 1.0].
        """
        # Read image dimensions
        img_info = raw_response.get("image", {})
        img_w = img_info.get("width")
        img_h = img_info.get("height")

        if not img_w or not img_h:
            try:
                with Image.open(image_path) as im:
                    img_w, img_h = im.width, im.height
            except Exception:
                img_w, img_h = 640, 640

        preds = raw_response.get("predictions", [])
        detected_objects: List[VisualDetectionDetail] = []
        detected_classes = set()
        class_counts = {}

        for p in preds:
            cls_name = p.get("class", "object")
            conf = float(p.get("confidence", 0.0))

            # Bounding box in Roboflow: x, y (center in pixels), width, height (in pixels)
            px = float(p.get("x", 0.0))
            py = float(p.get("y", 0.0))
            pw = float(p.get("width", 0.0))
            ph = float(p.get("height", 0.0))

            # Convert to normalized [ymin, xmin, ymax, xmax]
            xmin = max(0.0, min(1.0, (px - pw / 2.0) / img_w))
            ymin = max(0.0, min(1.0, (py - ph / 2.0) / img_h))
            xmax = max(0.0, min(1.0, (px + pw / 2.0) / img_w))
            ymax = max(0.0, min(1.0, (py + ph / 2.0) / img_h))

            # Guard against invalid box geometry
            if xmax <= xmin or ymax <= ymin:
                continue

            norm_box = [round(ymin, 4), round(xmin, 4), round(ymax, 4), round(xmax, 4)]

            # UI label formatting
            if task == "ROAD_DAMAGE":
                ui_label = "Pothole (Hosted Roboflow)"
            else:
                ui_label = "Municipal Waste (Hosted Roboflow)"

            detail = VisualDetectionDetail(
                label=ui_label,
                confidence=round(conf, 4),
                bbox=norm_box,
                task=task,
                class_id=p.get("class_id", 0),
                class_name=cls_name,
                source_model=f"roboflow_{model_id}",
                execution_mode="roboflow_hosted_inference"
            )
            detected_objects.append(detail)
            detected_classes.add(cls_name)
            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

        # Sort detections by confidence descending
        detected_objects.sort(key=lambda d: d.confidence, reverse=True)

        primary_detection = detected_objects[0].label if detected_objects else None
        primary_confidence = detected_objects[0].confidence if detected_objects else 0.0

        return {
            "provider": "roboflow",
            "status": "SUCCESS" if detected_objects else "EMPTY",
            "modelId": model_id,
            "architecture": architecture,
            "task": task,
            "visualDetection": primary_detection,
            "visualConfidence": primary_confidence,
            "detectedObjects": detected_objects,
            "detectedClasses": list(detected_classes),
            "classCounts": class_counts,
            "imageDimensions": [img_w, img_h],
            "inferenceTimeMs": latency_ms,
            "cached": cached,
            "rawPredictionCount": len(preds)
        }

roboflow_adapter = RoboflowHostedAdapter()
