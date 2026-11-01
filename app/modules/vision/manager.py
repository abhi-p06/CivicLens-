import os
import time
import logging
from typing import Dict, Any, Optional, List
from PIL import Image

from app.config import settings
from app.models.issue import VisualDetectionDetail, IssueCategory
from app.modules.vision.road_detector import RoadDamageDetector
from app.modules.vision.waste_detector import WasteDetector
from app.modules.vision.flooding_detector import FloodingDetector
from app.modules.vision.roboflow_adapter import roboflow_adapter

logger = logging.getLogger("civilens.vision.manager")

class VisionPipelineManager:
    """
    Modular Vision Pipeline Manager:
    
    Uploaded Image
          |
          v
    Image Validation (Path, Format, Integrity)
          |
          v
    Visual Task Selection
          |
          +-- Road Damage Detector (YOLOv8s RDD2022: Potholes, Cracks)
          |
          +-- Garbage / Waste Detector (YOLO TACO: Bags, Bottles, Cans, Cartons)
          |
          +-- Visible Flooding Detector (Explicitly Unsupported / Manual Review)
          |
          v
    Normalized Detection Results (Standardized Schema)
          |
          v
    Text-Image Cross-Validation & Priority Engine
    """

    def __init__(self):
        self.road_detector = RoadDamageDetector()
        self.waste_detector = WasteDetector()
        self.flooding_detector = FloodingDetector()
        self.roboflow_adapter = roboflow_adapter

    def is_task_supported(self, category_str: str) -> bool:
        c_lower = category_str.lower()
        if any(k in c_lower for k in ["road", "footpath", "pothole", "crack"]):
            return True
        if any(k in c_lower for k in ["sanitation", "garbage", "waste", "litter"]):
            return True
        return False

    def compare_models(
        self,
        image_path: str,
        category_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes explicit side-by-side comparison between local and hosted Roboflow candidate.
        Does NOT merge predictions or mutate production priority logic.
        """
        cat_lower = (category_hint or "").lower()
        if any(k in cat_lower for k in ["sanitation", "garbage", "waste", "trash", "litter"]):
            local_result = self.waste_detector.detect(image_path)
        else:
            local_result = self.road_detector.detect(image_path)

        hosted_result = self.roboflow_adapter.infer(image_path, category_hint=category_hint)

        local_objs = local_result.get("detectedObjects", [])
        hosted_objs = hosted_result.get("detectedObjects", [])

        summary = {
            "localModel": local_result.get("sourceModel", "local_detector"),
            "hostedModel": f"{hosted_result.get('modelId', 'unknown')} ({hosted_result.get('architecture', 'hosted')})",
            "task": hosted_result.get("task", local_result.get("task", "UNKNOWN")),
            "localDetectionCount": len(local_objs),
            "hostedDetectionCount": len(hosted_objs),
            "localPrimaryDetection": local_result.get("visualDetection"),
            "hostedPrimaryDetection": hosted_result.get("visualDetection"),
            "localConfidence": local_result.get("visualConfidence", 0.0),
            "hostedConfidence": hosted_result.get("visualConfidence", 0.0),
            "localLatencyMs": local_result.get("inferenceTimeMs", 0.0),
            "hostedLatencyMs": hosted_result.get("inferenceTimeMs", 0.0),
            "hostedStatus": hosted_result.get("status", "UNAVAILABLE"),
            "hostedCached": hosted_result.get("cached", False)
        }

        return {
            "mode": "compare",
            "imagePath": image_path,
            "categoryHint": category_hint,
            "comparisonSummary": summary,
            "local": local_result,
            "hosted": hosted_result
        }

    def detect(
        self,
        image_path_or_url: Optional[str],
        category_hint: Optional[str] = None,
        is_demo: bool = False,
        enable_comparison: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Coordinates genuine visual detection across task-specific models.
        Modes:
        - local: Default production mode using local YOLO models.
        - compare: Runs local baseline and attaches hosted candidate separately without merging.
        - hosted: Attempts hosted inference with safe fallback to local on failure.
        """
        provider = (getattr(settings, "civilens_vision_provider", None) or "local").lower()
        should_compare = enable_comparison if enable_comparison is not None else (provider == "compare")

        fallback_triggered = False
        fallback_reason = None
        fallback_error_cat = None

        # 1. Hosted Provider Mode (with safe local fallback)
        if provider == "hosted" and image_path_or_url and os.path.exists(image_path_or_url):
            try:
                hosted_res = self.roboflow_adapter.infer(image_path_or_url, category_hint=category_hint)
                if hosted_res.get("status") in ("SUCCESS", "EMPTY"):
                    return {
                        "visualDetection": hosted_res.get("visualDetection") or "No visible issues detected",
                        "visualConfidence": hosted_res.get("visualConfidence", 0.0),
                        "detectedObjects": hosted_res.get("detectedObjects", []),
                        "visionExecutionMode": "roboflow_hosted_inference",
                        "imageDimensions": hosted_res.get("imageDimensions", [640, 640]),
                        "inferenceTimeMs": hosted_res.get("inferenceTimeMs", 0.0),
                        "detectedClasses": hosted_res.get("detectedClasses", []),
                        "classCounts": hosted_res.get("classCounts", {}),
                        "task": hosted_res.get("task", "UNKNOWN"),
                        "sourceModel": f"roboflow_{hosted_res.get('modelId', 'hosted')}",
                        "provider": "roboflow"
                    }
                else:
                    fallback_triggered = True
                    fallback_reason = hosted_res.get("error", "Hosted model returned error status")
                    fallback_error_cat = hosted_res.get("errorCategory", "UNKNOWN")
                    logger.warning(
                        f"Roboflow hosted inference failed (category={fallback_error_cat}, error={fallback_reason}); falling back to local detector."
                    )
            except Exception as e:
                fallback_triggered = True
                fallback_reason = str(e)
                fallback_error_cat = "UNKNOWN"
                logger.warning(f"Roboflow hosted inference exception ({e}); falling back to local detector.")

        # 2. Local baseline execution (always preserved)
        local_out = self._execute_local_detection(image_path_or_url, category_hint=category_hint, is_demo=is_demo)

        if fallback_triggered:
            local_out["fallbackTriggered"] = True
            local_out["fallbackReason"] = fallback_reason
            local_out["hostedErrorCategory"] = fallback_error_cat

        # 3. Compare mode: attach separate hosted comparison without mutating local detections or severity
        if should_compare and image_path_or_url and os.path.exists(image_path_or_url):
            try:
                comp = self.compare_models(image_path_or_url, category_hint=category_hint)
                local_out["visionComparison"] = comp
                local_out["hosted"] = comp.get("hosted")
            except Exception as e:
                local_out["visionComparison"] = {
                    "mode": "compare",
                    "status": "UNAVAILABLE",
                    "error": str(e)
                }

        return local_out

    def _execute_local_detection(
        self,
        image_path_or_url: Optional[str],
        category_hint: Optional[str] = None,
        is_demo: bool = False
    ) -> Dict[str, Any]:
        # -------------------------------------------------------------
        # 0. EXPLICIT DEMO MODE (Isolated Fallback)
        # -------------------------------------------------------------
        if is_demo:
            target_hint = f"{image_path_or_url or ''} {category_hint or ''}".lower()
            if any(k in target_hint for k in ["garbage", "trash", "waste", "sanitation"]):
                primary = "Garbage Debris Pile (Demo)"
                conf = 0.88
                detections = [
                    VisualDetectionDetail(
                        label="Garbage Debris Pile (Demo)",
                        confidence=0.88,
                        bbox=[0.30, 0.20, 0.75, 0.85],
                        task="SANITATION",
                        source_model="demo_synthetic",
                        execution_mode="deterministic_demo_fallback"
                    ),
                    VisualDetectionDetail(
                        label="Overflow Litter (Demo)",
                        confidence=0.82,
                        bbox=[0.60, 0.40, 0.85, 0.90],
                        task="SANITATION",
                        source_model="demo_synthetic",
                        execution_mode="deterministic_demo_fallback"
                    )
                ]
            elif any(k in target_hint for k in ["water", "leak", "drain", "sewage", "pipeline"]):
                primary = "Water Pipeline Leak / Flooding (Demo)"
                conf = 0.91
                detections = [
                    VisualDetectionDetail(
                        label="Water Pipeline Leak (Demo)",
                        confidence=0.91,
                        bbox=[0.40, 0.25, 0.80, 0.75],
                        task="WATER_SUPPLY",
                        source_model="demo_synthetic",
                        execution_mode="deterministic_demo_fallback"
                    )
                ]
            else:
                primary = "Pothole (D40) (Demo)"
                conf = 0.94
                detections = [
                    VisualDetectionDetail(
                        label="Pothole (D40) (Demo)",
                        confidence=0.94,
                        bbox=[0.38, 0.22, 0.76, 0.80],
                        task="ROAD_DAMAGE",
                        source_model="demo_synthetic",
                        execution_mode="deterministic_demo_fallback"
                    )
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
                "task": "DEMO",
                "sourceModel": "demo_synthetic"
            }

        # -------------------------------------------------------------
        # 1. Image Validation
        # -------------------------------------------------------------
        if not image_path_or_url:
            return {
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "visionExecutionMode": "no_image_provided",
                "imageDimensions": None,
                "inferenceTimeMs": 0.0,
                "detectedClasses": [],
                "classCounts": {},
                "task": "NONE",
                "sourceModel": "none"
            }

        if not os.path.exists(image_path_or_url):
            return {
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "visionExecutionMode": "invalid_image_path",
                "imageDimensions": None,
                "inferenceTimeMs": 0.0,
                "detectedClasses": [],
                "classCounts": {},
                "task": "NONE",
                "sourceModel": "none"
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
                "task": "NONE",
                "sourceModel": "none"
            }

        # -------------------------------------------------------------
        # 2. Visual Task Selection & Execution
        # -------------------------------------------------------------
        hint = (category_hint or "").lower()

        # A. Sanitation & Garbage
        if any(k in hint for k in ["sanitation", "garbage", "waste", "trash", "litter"]):
            # Run Waste Detector first
            out = self.waste_detector.detect(image_path_or_url)
            if out.get("detectedObjects"):
                return out

            # Cross-modal check: Check if image contains road damage (e.g. category mismatch)
            road_out = self.road_detector.detect(image_path_or_url)
            if road_out.get("detectedObjects"):
                return road_out

            return out

        # B. Water Supply / Street Flooding / Storm Water
        elif any(k in hint for k in ["water", "flood", "drain", "pipe", "leak", "sewage"]):
            # Check if image actually contains road damage (e.g. pothole on water complaint)
            road_out = self.road_detector.detect(image_path_or_url)
            if road_out.get("detectedObjects"):
                return road_out

            # Check if image contains significant waste dump (confidence >= 0.40)
            waste_out = self.waste_detector.detect(image_path_or_url)
            if waste_out.get("detectedObjects") and waste_out.get("visualConfidence", 0.0) >= 0.40:
                return waste_out

            # If no alternative defect detected, invoke honest flooding detector
            return self.flooding_detector.detect(image_path_or_url)

        # C. Road Damage or Default
        elif any(k in hint for k in ["road", "footpath", "pothole", "crack"]):
            road_out = self.road_detector.detect(image_path_or_url)
            if road_out.get("detectedObjects"):
                return road_out

            # Cross-modal check: Check if image contains waste (e.g. reported pothole, photo is garbage)
            waste_out = self.waste_detector.detect(image_path_or_url)
            if waste_out.get("detectedObjects"):
                return waste_out

            return road_out

        # D. Other / Unspecified Categories (Electricity, Traffic, etc.)
        else:
            # Check road detector
            road_out = self.road_detector.detect(image_path_or_url)
            if road_out.get("detectedObjects"):
                return road_out

            # Check waste detector
            waste_out = self.waste_detector.detect(image_path_or_url)
            if waste_out.get("detectedObjects"):
                return waste_out

            return {
                "visualDetection": None,
                "visualConfidence": 0.0,
                "detectedObjects": [],
                "visionExecutionMode": "unsupported_visual_category",
                "imageDimensions": img_dims,
                "inferenceTimeMs": 0.0,
                "detectedClasses": [],
                "classCounts": {},
                "task": "UNSUPPORTED",
                "sourceModel": "none"
            }

vision_manager = VisionPipelineManager()
