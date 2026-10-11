import os
import time
import threading
from typing import List, Optional, Dict, Any
from PIL import Image

from app.config import settings
from app.models.issue import VisualDetectionDetail
from app.modules.vision.base import BaseVisionDetector

RDD2022_CLASSES = {
    "D00": "Longitudinal Crack",
    "D10": "Transverse Crack",
    "D20": "Alligator Crack",
    "D40": "Pothole",
}

class RoadDamageDetector(BaseVisionDetector):
    """
    Task-Specific Road Surface Damage Detector:
    - Trained on RDD2022 (Road Damage Detection 2022) multi-national dataset
    - Architecture: Ultralytics YOLOv8s
    - Detects: D00 (Longitudinal Crack), D10 (Transverse Crack), D20 (Alligator Crack), D40 (Pothole)
    - Normalized coordinate convention: [ymin, xmin, ymax, xmax] in [0.0, 1.0]
    """

    task_name = "ROAD_DAMAGE"
    category_name = "Roads & Footpaths"
    model_name = "YOLOv8s RDD2022"

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.yolo_model_path
        self.conf_threshold = settings.yolo_confidence_threshold
        self.iou_threshold = settings.yolo_iou_threshold
        self.imgsz = settings.yolo_image_size
        self.device = settings.yolo_device
        self._model = None
        self._load_attempted = False
        self._lock = threading.Lock()
        self._model_classes: Dict[int, str] = {}

    def _get_model(self):
        with self._lock:
            if not self._load_attempted:
                self._load_attempted = True
                if os.path.exists(self.model_path):
                    try:
                        from ultralytics import YOLO
                        self._model = YOLO(self.model_path)
                        self._model_classes = getattr(self._model, "names", {})
                    except Exception as e:
                        print(f"[Road Detector] Error loading weights from '{self.model_path}': {e}")
                        self._model = None
            return self._model

    def is_model_available(self) -> bool:
        return self._get_model() is not None

    def get_class_display_name(self, raw_code: str) -> str:
        code_upper = raw_code.strip().upper()
        if code_upper in RDD2022_CLASSES:
            return f"{RDD2022_CLASSES[code_upper]} ({code_upper})"
        return raw_code.title()

    def detect(
        self,
        image_path_or_url: Optional[str] = None,
        category_hint: Optional[str] = None,
        is_demo: bool = False
    ) -> Dict[str, Any]:
        if is_demo:
            target_hint = f"{image_path_or_url or ''} {category_hint or ''}".lower()
            if any(k in target_hint for k in ["garbage", "trash", "waste", "sanitation"]):
                primary = "Garbage Debris Pile (Demo)"
                conf = 0.88
                detections = [
                    VisualDetectionDetail(label="Garbage Debris Pile (Demo)", confidence=0.88, bbox=[0.30, 0.20, 0.75, 0.85]),
                    VisualDetectionDetail(label="Overflow Litter (Demo)", confidence=0.82, bbox=[0.60, 0.40, 0.85, 0.90])
                ]
            elif any(k in target_hint for k in ["water", "leak", "drain", "sewage", "pipeline"]):
                primary = "Water Pipeline Leak / Flooding (Demo)"
                conf = 0.91
                detections = [
                    VisualDetectionDetail(label="Water Pipeline Leak (Demo)", confidence=0.91, bbox=[0.40, 0.25, 0.80, 0.75])
                ]
            else:
                primary = "Pothole (D40) (Demo)"
                conf = 0.94
                detections = [
                    VisualDetectionDetail(label="Pothole (D40) (Demo)", confidence=0.94, bbox=[0.38, 0.22, 0.76, 0.80])
                ]

            return {
                "visualDetection": primary,
                "visualConfidence": conf,
                "detectedObjects": detections,
                "visionExecutionMode": "deterministic_demo_fallback",
                "imageDimensions": [1280, 720],
                "inferenceTimeMs": 5.0,
                "detectedClasses": ["DEMO"],
                "classCounts": {"DEMO": len(detections)},
                "task": self.task_name,
                "sourceModel": self.model_name
            }
        if not image_path_or_url or not os.path.exists(image_path_or_url):
            return {
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "visionExecutionMode": "no_image_provided" if not image_path_or_url else "invalid_image_path",
                "imageDimensions": None,
                "inferenceTimeMs": 0.0,
                "detectedClasses": [],
                "classCounts": {},
                "task": self.task_name,
                "sourceModel": self.model_name
            }

        img_dims = None
        try:
            with Image.open(image_path_or_url) as img:
                img.verify()
            with Image.open(image_path_or_url) as img:
                img_dims = [img.width, img.height]
        except Exception:
            return {
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "visionExecutionMode": "unreadable_image_file",
                "imageDimensions": None,
                "inferenceTimeMs": 0.0,
                "detectedClasses": [],
                "classCounts": {},
                "task": self.task_name,
                "sourceModel": self.model_name
            }

        model = self._get_model()
        if model is None:
            return {
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "visionExecutionMode": "unavailable_model",
                "imageDimensions": img_dims,
                "inferenceTimeMs": 0.0,
                "detectedClasses": [],
                "classCounts": {},
                "task": self.task_name,
                "sourceModel": self.model_name
            }

        t0 = time.time()
        try:
            with self._lock:
                results = model(
                    image_path_or_url,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    imgsz=self.imgsz,
                    device=self.device,
                    verbose=False
                )
            elapsed_ms = round((time.time() - t0) * 1000.0, 1)

            detections: List[VisualDetectionDetail] = []
            detected_classes: List[str] = []
            class_counts: Dict[str, int] = {}

            if results and len(results) > 0:
                r = results[0]
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    raw_name = model.names.get(cls_id, f"Class_{cls_id}")
                    display_name = self.get_class_display_name(raw_name)
                    conf = float(box.conf[0])

                    # Convert Ultralytics [xmin, ymin, xmax, ymax] to [ymin, xmin, ymax, xmax]
                    xmin, ymin, xmax, ymax = box.xyxyn[0].tolist()
                    normalized_bbox = [
                        round(max(0.0, min(1.0, ymin)), 4),
                        round(max(0.0, min(1.0, xmin)), 4),
                        round(max(0.0, min(1.0, ymax)), 4),
                        round(max(0.0, min(1.0, xmax)), 4),
                    ]

                    detections.append(
                        VisualDetectionDetail(
                            label=display_name,
                            confidence=round(conf, 4),
                            bbox=normalized_bbox,
                            task=self.task_name,
                            class_id=cls_id,
                            class_name=raw_name,
                            source_model=self.model_name,
                            execution_mode="real_yolo_inference"
                        )
                    )
                    detected_classes.append(raw_name)
                    class_counts[raw_name] = class_counts.get(raw_name, 0) + 1

            if detections:
                detections.sort(key=lambda d: d.confidence, reverse=True)
                primary = detections[0]
                return {
                    "visualDetection": f"{primary.label} (Confidence: {round(primary.confidence * 100, 1)}%)",
                    "visualConfidence": primary.confidence,
                    "detectedObjects": detections,
                    "visionExecutionMode": "real_yolo_inference",
                    "imageDimensions": img_dims,
                    "inferenceTimeMs": elapsed_ms,
                    "detectedClasses": list(set(detected_classes)),
                    "classCounts": class_counts,
                    "task": self.task_name,
                    "sourceModel": self.model_name
                }
            else:
                return {
                    "visualDetection": None,
                    "visualConfidence": 0.0,
                    "detectedObjects": [],
                    "visionExecutionMode": "real_yolo_inference",
                    "imageDimensions": img_dims,
                    "inferenceTimeMs": elapsed_ms,
                    "detectedClasses": [],
                    "classCounts": {},
                    "task": self.task_name,
                    "sourceModel": self.model_name
                }
        except Exception as e:
            print(f"[Road Detector] Inference error: {e}")
            return {
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "visionExecutionMode": "inference_error",
                "imageDimensions": img_dims,
                "inferenceTimeMs": round((time.time() - t0) * 1000.0, 1),
                "detectedClasses": [],
                "classCounts": {},
                "task": self.task_name,
                "sourceModel": self.model_name
            }
