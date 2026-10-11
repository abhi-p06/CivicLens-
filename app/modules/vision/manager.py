import os
import time
from typing import Dict, Any, Optional, List
from PIL import Image

from app.models.issue import VisualDetectionDetail, IssueCategory
from app.modules.vision.road_detector import RoadDamageDetector
from app.modules.vision.waste_detector import WasteDetector
from app.modules.vision.flooding_detector import FloodingDetector

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

    def is_task_supported(self, category_str: str) -> bool:
        c_lower = category_str.lower()
        if any(k in c_lower for k in ["road", "footpath", "pothole", "crack"]):
            return True
        if any(k in c_lower for k in ["sanitation", "garbage", "waste", "litter"]):
            return True
        return False

    def detect(
        self,
        image_path_or_url: Optional[str],
        category_hint: Optional[str] = None,
        is_demo: bool = False
    ) -> Dict[str, Any]:
        """
        Coordinates genuine visual detection across task-specific models.
        """
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
