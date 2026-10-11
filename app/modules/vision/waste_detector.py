import os
import time
import threading
from typing import List, Optional, Dict, Any
from PIL import Image

from app.config import settings
from app.models.issue import VisualDetectionDetail
from app.modules.vision.base import BaseVisionDetector

TACO_CIVIC_CLASSES = {
    0: "Plastic Waste / Wrapper",
    1: "Litter Debris",
    2: "Bottle / Container",
    3: "Bottle Cap / Small Plastic",
    4: "Metal Can Debris",
    5: "Plastic Scrap",
    6: "Discarded Carton / Box",
    7: "Disposable Cup",
    8: "Solid Waste / Litter",
}

class WasteDetector(BaseVisionDetector):
    """
    Task-Specific Sanitation & Waste Accumulation Detector:
    - Trained on TACO (Trash Annotations in Context) municipal waste dataset
    - Architecture: Ultralytics YOLO11s (yolo11s.yaml, C3k2 + C2PSA layers, 9.43M params)
    - Source: fabiocigaina/TACO-yolo11s
    - Detects: Plastic waste, bottles, cans, cartons, cups, packaging debris
    - Normalized coordinate convention: [ymin, xmin, ymax, xmax] in [0.0, 1.0]
    """

    task_name = "SANITATION"
    category_name = "Sanitation & Garbage"
    model_name = "YOLO11s TACO Waste Detector"

    def __init__(self, model_path: Optional[str] = None):
        chosen_path = model_path or settings.waste_model_path
        # Backward compatibility resolution between taco_yolo11s.pt and legacy yolov8_waste.pt
        if not os.path.exists(chosen_path):
            if chosen_path.endswith("taco_yolo11s.pt") and os.path.exists("models/yolov8_waste.pt"):
                chosen_path = "models/yolov8_waste.pt"
            elif chosen_path.endswith("yolov8_waste.pt") and os.path.exists("models/taco_yolo11s.pt"):
                chosen_path = "models/taco_yolo11s.pt"
        self.model_path = chosen_path
        self.conf_threshold = settings.waste_confidence_threshold
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
                        print(f"[Waste Detector] Error loading weights from '{self.model_path}': {e}")
                        self._model = None
            return self._model

    def is_model_available(self) -> bool:
        return self._get_model() is not None

    def get_class_display_name(self, cls_id: int, raw_name: str) -> str:
        if cls_id in TACO_CIVIC_CLASSES:
            return TACO_CIVIC_CLASSES[cls_id]
        return raw_name.title()

    def detect(
        self,
        image_path_or_url: Optional[str] = None,
        category_hint: Optional[str] = None,
        is_demo: bool = False
    ) -> Dict[str, Any]:
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
                    display_name = self.get_class_display_name(cls_id, raw_name)
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
                waste_summary = f"{primary.label} (Confidence: {round(primary.confidence * 100, 1)}%)"
                if len(detections) > 1:
                    waste_summary += f" [+ {len(detections) - 1} items]"

                return {
                    "visualDetection": waste_summary,
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
            print(f"[Waste Detector] Inference error: {e}")
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
