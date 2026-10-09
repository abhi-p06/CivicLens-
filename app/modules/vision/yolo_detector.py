import os
from typing import List, Optional, Dict, Any, Tuple
from PIL import Image
from app.models.issue import VisualDetectionDetail

class YOLORoadDamageDetector:
    """
    Computer Vision Road Damage & Evidence Detection Engine:
    - Integrates Ultralytics YOLOv8 inference when model weights are provided
    - Explicitly separates Real ML Inference from Centralized Deterministic Demo Fallback
    - Extracts normalized bounding boxes, detection labels, and confidence metrics
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "models/yolov8n_rdd.pt"
        self._model = None
        self._load_attempted = False

    def _get_model(self):
        if not self._load_attempted:
            self._load_attempted = True
            if os.path.exists(self.model_path):
                try:
                    from ultralytics import YOLO
                    self._model = YOLO(self.model_path)
                except Exception:
                    self._model = None
        return self._model

    def detect(
        self,
        image_path_or_url: Optional[str],
        category_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs object detection. Returns structured dictionary with explicit executionMode.
        """
        if not image_path_or_url:
            return {
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "visionExecutionMode": "no_image_provided",
                "imageDimensions": None
            }

        # Check image file dimensions if local path
        img_dims = None
        if os.path.exists(image_path_or_url):
            try:
                with Image.open(image_path_or_url) as img:
                    img_dims = [img.width, img.height]
            except Exception:
                pass

        # -------------------------------------------------------------
        # 1. REAL IMPLEMENTATION: YOLO Model Inference
        # -------------------------------------------------------------
        model = self._get_model()
        if model is not None and os.path.exists(image_path_or_url):
            try:
                results = model(image_path_or_url)
                detections = []
                for r in results:
                    for box in r.boxes:
                        label = model.names[int(box.cls[0])]
                        conf = float(box.conf[0])
                        xyxyn = box.xyxyn[0].tolist()  # [ymin, xmin, ymax, xmax]
                        detections.append(
                            VisualDetectionDetail(
                                label=label,
                                confidence=round(conf, 2),
                                bbox=xyxyn
                            )
                        )
                if detections:
                    primary = detections[0].label
                    conf = max(d.confidence for d in detections)
                    return {
                        "visualDetection": f"{primary.title()} (YOLO Confirmed)",
                        "visualConfidence": round(conf, 2),
                        "detectedObjects": detections,
                        "visionExecutionMode": "real_yolo_inference",
                        "imageDimensions": img_dims
                    }
            except Exception:
                pass

        # -------------------------------------------------------------
        # 2. DEMO FALLBACK: Deterministic Scenario-Aware CV Response
        # -------------------------------------------------------------
        # Resolves appropriate damage classes based on input scenario context
        target_hint = f"{image_path_or_url} {category_hint or ''}".lower()

        if any(k in target_hint for k in ["garbage", "trash", "waste", "sanitation"]):
            primary = "Garbage Debris Pile"
            conf = 0.88
            detections = [
                VisualDetectionDetail(label="refuse_pile", confidence=0.88, bbox=[0.30, 0.20, 0.75, 0.85]),
                VisualDetectionDetail(label="overflow_litter", confidence=0.82, bbox=[0.60, 0.40, 0.85, 0.90])
            ]
        elif any(k in target_hint for k in ["water", "leak", "drain", "sewage", "pipeline"]):
            primary = "Water Pipeline Leak / Flooding"
            conf = 0.91
            detections = [
                VisualDetectionDetail(label="water_leak", confidence=0.91, bbox=[0.40, 0.25, 0.80, 0.75])
            ]
        else:
            # Default road damage / pothole
            primary = "Pothole (Detected)"
            conf = 0.94
            detections = [
                VisualDetectionDetail(label="pothole", confidence=0.94, bbox=[0.38, 0.22, 0.76, 0.80])
            ]

        return {
            "visualDetection": primary,
            "visualConfidence": conf,
            "detectedObjects": detections,
            "visionExecutionMode": "deterministic_demo_fallback",
            "imageDimensions": img_dims
        }

yolo_detector = YOLORoadDamageDetector()
