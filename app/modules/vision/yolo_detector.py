"""
CIVILENS Road Damage Detection Subsystem
Provides backward-compatible interface to the RoadDamageDetector module.
"""

from app.modules.vision.road_detector import RoadDamageDetector, RDD2022_CLASSES

YOLORoadDamageDetector = RoadDamageDetector
yolo_detector = RoadDamageDetector()
