import os
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.modules.vision.yolo_detector import YOLORoadDamageDetector, yolo_detector, RDD2022_CLASSES
from app.modules.vision.severity import visual_severity_estimator
from app.core.pipeline import pipeline
from app.models.issue import VisualDetectionDetail, IssueCreate


@pytest.fixture
def client():
    return TestClient(app)


def test_1_successful_model_loading():
    """Verify genuine YOLO checkpoint is loaded and exposes RDD2022 classes."""
    assert os.path.exists(yolo_detector.model_path), f"Checkpoint missing at {yolo_detector.model_path}"
    assert yolo_detector.is_model_available() is True
    model = yolo_detector._get_model()
    assert model is not None
    assert hasattr(model, "names")
    # Verify RDD2022 class mapping
    names = model.names
    assert 0 in names and names[0] == "D00"
    assert 1 in names and names[1] == "D10"
    assert 2 in names and names[2] == "D20"
    assert 3 in names and names[3] == "D40"


def test_2_missing_checkpoint_handling():
    """Verify detector handles missing checkpoint explicitly without crash or fabricated detections."""
    dummy_detector = YOLORoadDamageDetector(model_path="models/nonexistent_dummy_weights.pt")
    assert dummy_detector.is_model_available() is False
    res = dummy_detector.detect("data/test_samples/pothole_multibox.jpg", is_demo=False)
    assert res["visionExecutionMode"] == "unavailable_model"
    assert res["visualDetection"] is None
    assert res["visualConfidence"] == 0.0
    assert res["detectedObjects"] == []


def test_3_invalid_image_reference_rejection():
    """Verify nonexistent image path is handled safely."""
    res = yolo_detector.detect("nonexistent_path_file.jpg", is_demo=False)
    assert res["visionExecutionMode"] == "invalid_image_path"
    assert res["visualDetection"] is None
    assert res["detectedObjects"] == []


def test_4_corrupt_image_handling(tmp_path):
    """Verify corrupt image file is safely rejected with unreadable_image_file mode."""
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"CORRUPT_NOT_AN_IMAGE_HEADER_XYZ")
    res = yolo_detector.detect(str(corrupt_file), is_demo=False)
    assert res["visionExecutionMode"] == "unreadable_image_file"
    assert res["visualDetection"] is None
    assert res["detectedObjects"] == []


def test_5_real_pothole_detection():
    """Verify real inference on genuine road pothole image."""
    img_path = "data/test_samples/pothole_multibox.jpg"
    assert os.path.exists(img_path)
    res = yolo_detector.detect(img_path, is_demo=False)

    assert res["visionExecutionMode"] == "real_yolo_inference"
    assert res["inferenceTimeMs"] > 0.0
    assert len(res["detectedObjects"]) > 0
    primary = res["detectedObjects"][0]
    assert "D40" in primary.label or "Pothole" in primary.label
    assert primary.confidence > 0.15
    assert len(primary.bbox) == 4


def test_6_real_crack_detection():
    """Verify real inference on genuine road crack image (D20 Alligator Crack)."""
    img_path = "data/test_samples/alligator_crack.jpg"
    assert os.path.exists(img_path)
    res = yolo_detector.detect(img_path, is_demo=False)

    assert res["visionExecutionMode"] == "real_yolo_inference"
    assert len(res["detectedObjects"]) > 0
    primary = res["detectedObjects"][0]
    assert "D20" in primary.label or "Crack" in primary.label
    assert primary.confidence > 0.15


def test_7_clean_road_empty_detection():
    """Verify normal road without defects produces 0 detections and does not fabricate detections."""
    img_path = "data/test_samples/clean_road.jpg"
    assert os.path.exists(img_path)
    res = yolo_detector.detect(img_path, is_demo=False)

    assert res["visionExecutionMode"] == "real_yolo_inference"
    assert res["visualDetection"] is None
    assert res["visualConfidence"] == 0.0
    assert res["detectedObjects"] == []


def test_8_normalized_bounding_box_format():
    """Verify bounding boxes conform to [ymin, xmin, ymax, xmax] in [0.0, 1.0]."""
    img_path = "data/test_samples/pothole_multibox.jpg"
    res = yolo_detector.detect(img_path, is_demo=False)
    for obj in res["detectedObjects"]:
        ymin, xmin, ymax, xmax = obj.bbox
        assert 0.0 <= ymin <= 1.0
        assert 0.0 <= xmin <= 1.0
        assert 0.0 <= ymax <= 1.0
        assert 0.0 <= xmax <= 1.0
        assert ymin <= ymax
        assert xmin <= xmax


def test_9_class_name_mapping():
    """Verify RDD2022 class display name translation."""
    assert yolo_detector.get_class_display_name("D00") == "Longitudinal Crack (D00)"
    assert yolo_detector.get_class_display_name("D10") == "Transverse Crack (D10)"
    assert yolo_detector.get_class_display_name("D20") == "Alligator Crack (D20)"
    assert yolo_detector.get_class_display_name("D40") == "Pothole (D40)"
    assert yolo_detector.get_class_display_name("custom_defect") == "Custom_Defect"


def test_10_visual_severity_with_real_detections():
    """Verify visual severity estimator calculates dynamic score from real detections and returns 0 on empty."""
    # Empty detections
    assert visual_severity_estimator.estimate_severity([]) == 0.0

    # Real pothole detection
    pothole_res = yolo_detector.detect("data/test_samples/pothole_multibox.jpg", is_demo=False)
    sev = visual_severity_estimator.estimate_severity(pothole_res["detectedObjects"])
    assert 0.30 <= sev <= 0.95

    # Real crack detection
    crack_res = yolo_detector.detect("data/test_samples/alligator_crack.jpg", is_demo=False)
    sev_crack = visual_severity_estimator.estimate_severity(crack_res["detectedObjects"])
    assert 0.30 <= sev_crack <= 0.95


def test_11_explicit_demo_mode_behavior():
    """Verify explicit demo mode produces demo fallback and marks executionMode correctly."""
    res = yolo_detector.detect("data/sample_pothole.jpg", is_demo=True)
    assert res["visionExecutionMode"] == "deterministic_demo_fallback"
    assert "Demo" in res["visualDetection"]
    assert res["visualConfidence"] == 0.94


def test_12_pipeline_integration_with_real_road_image():
    """Verify end-to-end cognitive pipeline with a real road damage image."""
    payload = IssueCreate(
        complaintText="Severe road crater causing danger to two wheelers near crossing",
        location="Ghatkopar West",
        imageUrl="data/test_samples/pothole_multibox.jpg"
    )
    analysis = pipeline.analyze(payload)
    assert analysis["visionMode"] == "real_yolo_inference"
    assert analysis["visualConfidence"] > 0.15
    assert len(analysis["detectedObjects"]) > 0
    assert analysis["visualSeverity"] > 0.0
    assert analysis["priorityScore"] > 0


def test_13_pipeline_clean_road_handles_empty_detection():
    """Verify cognitive pipeline handles clean road without crashing or fabricating severity."""
    payload = IssueCreate(
        complaintText="Routine inspection check on road sector",
        location="BKC Central Corridor",
        imageUrl="data/test_samples/clean_road.jpg"
    )
    analysis = pipeline.analyze(payload)
    assert analysis["visionMode"] == "real_yolo_inference"
    assert analysis["visualDetection"] is None
    assert analysis["visualConfidence"] == 0.0
    assert len(analysis["detectedObjects"]) == 0
    assert analysis["visualSeverity"] == 0.0


def test_14_api_health_endpoint_reports_real_yolo_online(client):
    """Verify /api/v1/health reflects the active Ultralytics YOLOv8s RDD2022 engine."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    vision_subsystem = data["subsystems"]["vision_detector"]
    assert vision_subsystem["status"] == "ONLINE"
    assert vision_subsystem["is_model_available"] is True
    assert vision_subsystem["measurement_status"] == "measured"
    assert "0.4643" in vision_subsystem["metric_display"]


def test_15_api_analyze_with_real_upload(client):
    """Verify uploading a real pothole image and running analysis through API."""
    with open("data/test_samples/pothole_multibox.jpg", "rb") as f:
        img_bytes = f.read()

    upload_res = client.post(
        "/api/v1/upload",
        files={"file": ("real_pothole.jpg", img_bytes, "image/jpeg")}
    )
    assert upload_res.status_code == 200
    upload_id = upload_res.json()["uploadId"]

    analyze_res = client.post(
        "/api/v1/analyze",
        json={
            "complaintText": "Major road defect near market lane",
            "location": "Dadar Market",
            "uploadId": upload_id
        }
    )
    assert analyze_res.status_code == 200
    analysis = analyze_res.json()
    assert analysis["visionMode"] == "real_yolo_inference"
    assert analysis["uploadId"] == upload_id
    assert len(analysis["detectedObjects"]) > 0
    assert analysis["visualConfidence"] > 0.15
