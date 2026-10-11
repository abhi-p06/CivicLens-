from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from app.models.issue import VisualDetectionDetail

class BaseVisionDetector(ABC):
    """
    Abstract Base Class for Task-Specific Computer Vision Detectors.
    Defines a shared, standardized interface across civic defect domains:
    - Road Damage (RDD2022)
    - Sanitation & Waste (TACO)
    - Street Flooding & Waterlogging
    """

    task_name: str
    category_name: str
    model_name: str
    model_path: Optional[str] = None

    @abstractmethod
    def is_model_available(self) -> bool:
        """Returns True if genuine model weights are loaded and ready for inference."""
        pass

    @abstractmethod
    def detect(
        self,
        image_path_or_url: Optional[str] = None,
        category_hint: Optional[str] = None,
        is_demo: bool = False
    ) -> Dict[str, Any]:
        """
        Executes genuine object detection or task handling on a validated local image file.
        Returns a standardized dictionary conforming to CIVILENS vision schema.
        """
        pass
