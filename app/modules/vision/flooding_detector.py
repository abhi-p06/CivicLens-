from typing import Dict, Any, Optional
import os
from PIL import Image

from app.modules.vision.base import BaseVisionDetector

class FloodingDetector(BaseVisionDetector):
    """
    Visible Street Flooding & Waterlogging Handler:
    
    SYSTEM STATUS: EXPLICITLY UNSUPPORTED / OPERATIONALLY UNVALIDATED
    
    Audit & Selection Findings:
    - Pretrained models on public registries (e.g. Hugging Face) for 'flood' are either:
      1. Satellite/aerial remote-sensing segmentation (Sentinel-2, Prithvi, SAR)
      2. Disaster tweet/text classification (SigLIP2, TREC-IS)
    - No open, reliably validated ground-level object detection model exists for
      street-level waterlogging, puddle localization, or subterranean pipe leaks.
    
    POLICY COMPLIANCE:
    - Never fabricates synthetic bounding boxes or pseudo-detections.
    - Explicitly reports 'unsupported_visual_category'.
    - Yields honest MANUAL_REVIEW status for human field engineer dispatch.
    """

    task_name = "STREET_FLOODING"
    category_name = "Water Supply & Drainage"
    model_name = "Street Flooding Detector (Unvalidated Task)"
    model_path = None

    def is_model_available(self) -> bool:
        # Genuinely reports False as no calibrated ground-level model is deployed
        return False

    def detect(
        self,
        image_path_or_url: Optional[str] = None,
        category_hint: Optional[str] = None,
        is_demo: bool = False
    ) -> Dict[str, Any]:
        img_dims = None
        if image_path_or_url and os.path.exists(image_path_or_url):
            try:
                with Image.open(image_path_or_url) as img:
                    img_dims = [img.width, img.height]
            except Exception:
                pass

        return {
            "visualDetection": None,
            "visualConfidence": 0.0,
            "detectedObjects": [],
            "visionExecutionMode": "unsupported_visual_category",
            "imageDimensions": img_dims,
            "inferenceTimeMs": 0.0,
            "detectedClasses": [],
            "classCounts": {},
            "task": self.task_name,
            "sourceModel": self.model_name,
            "diagnosticMessage": (
                "Ground-level street flooding / waterlogging does not have a validated "
                "computer vision object detection checkpoint configured. "
                "Bounding boxes are not fabricated; issue is routed for human manual review."
            )
        }
