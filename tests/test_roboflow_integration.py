import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.config import settings
from app.modules.vision.roboflow_adapter import RoboflowHostedAdapter, compute_image_sha256, mask_api_key
from app.modules.vision.manager import vision_manager

PROJECT_ROOT = Path(__file__).resolve().parent.parent

@pytest.fixture
def test_image_path():
    path = str(PROJECT_ROOT / "data" / "test_samples" / "repair_pothole_before.jpg")
    assert os.path.exists(path), f"Test image {path} must exist"
    return path

class TestRoboflowIntegration:
    """
    Test suite for Phase 14: Roboflow Hosted Model Integration & Security.
    """

    def test_model_id_selection_by_category(self):
        """Test correct model ID selection based on civic category."""
        adapter = RoboflowHostedAdapter()

        # Road damage / pothole
        model_id, arch, task, target = adapter.resolve_model_info("Roads & Footpaths")
        assert model_id == settings.roboflow_pothole_model_id
        assert arch == "YOLO26"
        assert task == "ROAD_DAMAGE"
        assert target == "Pothole"

        # Waste / Sanitation
        w_model_id, w_arch, w_task, w_target = adapter.resolve_model_info("Sanitation & Garbage")
        assert w_model_id == settings.roboflow_garbage_model_id
        assert w_arch == "RF-DETR Nano"
        assert w_task == "SANITATION"
        assert w_target == "garbage"

    def test_prediction_schema_normalization(self):
        """Test conversion of Roboflow center pixel coordinates to normalized [ymin, xmin, ymax, xmax]."""
        adapter = RoboflowHostedAdapter()
        raw_response = {
            "image": {"width": 200, "height": 400},
            "predictions": [
                {
                    "x": 100.0,
                    "y": 100.0,
                    "width": 50.0,
                    "height": 80.0,
                    "confidence": 0.92,
                    "class": "Pothole",
                    "class_id": 0
                }
            ]
        }

        # x: center 100 in 200w -> xmin = (100 - 25)/200 = 0.375, xmax = (100 + 25)/200 = 0.625
        # y: center 100 in 400h -> ymin = (100 - 40)/400 = 0.150, ymax = (100 + 40)/400 = 0.350
        norm = adapter._normalize_predictions(
            raw_response=raw_response,
            image_path="dummy.jpg",
            model_id="potholes-krmk8/2",
            architecture="YOLO26",
            task="ROAD_DAMAGE",
            latency_ms=120.0,
            cached=False
        )

        assert norm["status"] == "SUCCESS"
        assert len(norm["detectedObjects"]) == 1
        obj = norm["detectedObjects"][0]
        assert obj.bbox == [0.15, 0.375, 0.35, 0.625]
        assert obj.confidence == 0.92
        assert obj.task == "ROAD_DAMAGE"
        assert obj.source_model == "roboflow_potholes-krmk8/2"
        assert obj.execution_mode == "roboflow_hosted_inference"

    def test_bounding_box_coordinate_clamping(self):
        """Test boundary clamping to [0.0, 1.0] and rejection of inverted boxes."""
        adapter = RoboflowHostedAdapter()
        raw_response = {
            "image": {"width": 100, "height": 100},
            "predictions": [
                # Overflows boundary
                {"x": 10.0, "y": 10.0, "width": 50.0, "height": 50.0, "confidence": 0.85, "class": "Pothole"},
                # Invalid zero/negative width
                {"x": 50.0, "y": 50.0, "width": 0.0, "height": 20.0, "confidence": 0.80, "class": "Pothole"}
            ]
        }

        norm = adapter._normalize_predictions(
            raw_response=raw_response,
            image_path="dummy.jpg",
            model_id="potholes-krmk8/2",
            architecture="YOLO26",
            task="ROAD_DAMAGE",
            latency_ms=50.0,
            cached=False
        )

        assert len(norm["detectedObjects"]) == 1  # Invalid box dropped
        box = norm["detectedObjects"][0].bbox
        assert box[0] >= 0.0 and box[1] >= 0.0 and box[2] <= 1.0 and box[3] <= 1.0

    def test_missing_or_invalid_api_configuration(self, test_image_path):
        """Test behavior when ROBOFLOW_API_KEY is not configured."""
        adapter = RoboflowHostedAdapter()
        adapter.api_key = ""  # simulate missing key

        res = adapter.infer(test_image_path, category_hint="Roads & Footpaths")
        assert res["status"] == "UNAVAILABLE"
        assert "not configured" in res["error"]
        assert len(res["detectedObjects"]) == 0

    def test_network_timeout_and_server_errors(self, test_image_path):
        """Test graceful error handling when Roboflow API throws 500/502/ConnectionError."""
        adapter = RoboflowHostedAdapter()
        adapter.api_key = "dummy_valid_format_key_12345"

        mock_client = MagicMock()
        mock_client.infer.side_effect = ConnectionError("Connection refused by hosted endpoint")

        with patch.object(adapter, "_get_client", return_value=mock_client):
            res = adapter.infer(test_image_path, category_hint="Roads & Footpaths", use_cache=False)
            assert res["status"] == "ERROR"
            assert ("Inference request error" in res["error"]) or ("Network timeout" in res["error"])
            assert res.get("errorCategory") == "NETWORK_TIMEOUT"
            assert len(res["detectedObjects"]) == 0
            # Ensure fake boxes are never produced
            assert res["visualDetection"] is None

    def test_rate_limit_responses(self, test_image_path):
        """Test handling of HTTP 429 rate limit / quota exceeded."""
        adapter = RoboflowHostedAdapter()
        adapter.api_key = "dummy_valid_format_key_12345"

        class MockHTTPError(Exception):
            status_code = 429

        mock_client = MagicMock()
        mock_client.infer.side_effect = MockHTTPError("Too Many Requests")

        with patch.object(adapter, "_get_client", return_value=mock_client):
            res = adapter.infer(test_image_path, category_hint="Roads & Footpaths", use_cache=False)
            assert res["status"] == "ERROR"
            assert "Rate limit / quota exceeded" in res["error"]
            assert len(res["detectedObjects"]) == 0

    def test_empty_prediction_results(self, test_image_path):
        """Test behavior when image has no detections."""
        adapter = RoboflowHostedAdapter()
        adapter.api_key = "dummy_valid_format_key_12345"

        mock_client = MagicMock()
        mock_client.infer.return_value = {
            "image": {"width": 640, "height": 640},
            "predictions": []
        }

        with patch.object(adapter, "_get_client", return_value=mock_client):
            res = adapter.infer(test_image_path, category_hint="Roads & Footpaths", use_cache=False)
            assert res["status"] == "EMPTY"
            assert len(res["detectedObjects"]) == 0
            assert res["visualDetection"] is None
            assert res["visualConfidence"] == 0.0

    def test_caching_of_repeated_image_model_pairs(self, test_image_path):
        """Test that repeated calls on identical image hash use deterministic cache without extra API calls."""
        adapter = RoboflowHostedAdapter()
        img_hash = compute_image_sha256(test_image_path)
        cache_key = f"{img_hash}:{adapter.pothole_model_id}"

        # Manually seed cache
        adapter._cache[cache_key] = {
            "raw_response": {
                "image": {"width": 640, "height": 480},
                "predictions": [
                    {"x": 320, "y": 240, "width": 100, "height": 80, "confidence": 0.88, "class": "Pothole"}
                ]
            },
            "latency_ms": 45.0,
            "timestamp": 123456789.0
        }

        res = adapter.infer(test_image_path, category_hint="Roads & Footpaths", use_cache=True)
        assert res["cached"] is True
        assert len(res["detectedObjects"]) == 1
        assert res["detectedObjects"][0].label == "Pothole (Hosted Roboflow)"

    def test_no_fake_fallback_detections(self):
        """Confirm that adapter never outputs synthetic fallback bounding boxes on missing/error images."""
        adapter = RoboflowHostedAdapter()
        res = adapter.infer("non_existent_file_path.jpg", category_hint="Roads & Footpaths")
        assert res["status"] == "ERROR"
        assert len(res["detectedObjects"]) == 0
        assert res["visualDetection"] is None

    def test_no_api_credentials_in_frontend_assets(self):
        """Security Scan: Verify that ROBOFLOW_API_KEY is never leaked into frontend source or build output."""
        frontend_dir = PROJECT_ROOT / "frontend"
        if not frontend_dir.exists():
            return

        api_key = settings.roboflow_api_key
        assert api_key, "ROBOFLOW_API_KEY should be present in environment for test"

        # Search frontend src and dist
        for folder in ["src", "dist"]:
            p = frontend_dir / folder
            if not p.exists():
                continue
            for file_p in p.rglob("*"):
                if file_p.is_file() and file_p.suffix in [".ts", ".tsx", ".js", ".html", ".css", ".json"]:
                    content = file_p.read_text(encoding="utf-8", errors="ignore")
                    assert api_key not in content, f"SECURITY LEAK: Found Roboflow API key in frontend file {file_p}!"

    def test_local_detector_operation_when_roboflow_unavailable(self, test_image_path):
        """Verify that production local detector functions normally even when Roboflow is unavailable."""
        with patch.object(vision_manager.roboflow_adapter, "is_configured", return_value=False):
            # Local detection should succeed uninterrupted
            res = vision_manager.detect(test_image_path, category_hint="Roads & Footpaths", enable_comparison=False)
            assert res["sourceModel"] in ["YOLOv8s RDD2022", "yolov8s_rdd2022.pt"]
            assert res.get("detectedObjects") is not None
            # Hosted failure must not degrade local output
            assert "visionComparison" not in res

    def test_vision_compare_models_side_by_side(self, test_image_path):
        """Verify compare_models provides side-by-side local and hosted outputs."""
        comp = vision_manager.compare_models(test_image_path, category_hint="Roads & Footpaths")
        assert comp["mode"] == "compare"
        assert "local" in comp
        assert "hosted" in comp
        assert "comparisonSummary" in comp

        summary = comp["comparisonSummary"]
        assert "localModel" in summary
        assert "hostedModel" in summary
        assert "localDetectionCount" in summary
        assert "hostedDetectionCount" in summary

    def test_hosted_mode_with_safe_local_fallback(self, test_image_path):
        """Verify that if civilens_vision_provider='hosted' and hosted API fails, it falls back safely to local YOLO."""
        with patch.object(settings, "civilens_vision_provider", "hosted"):
            mock_res = {
                "provider": "roboflow",
                "status": "ERROR",
                "error": "Hosted API request timed out (HTTP 504)",
                "detectedObjects": [],
                "visualDetection": None
            }
            with patch.object(vision_manager.roboflow_adapter, "infer", return_value=mock_res):
                res = vision_manager.detect(test_image_path, category_hint="Roads & Footpaths", enable_comparison=False)
                # Must safely fall back to local detector
                assert res["sourceModel"] in ["YOLOv8s RDD2022", "yolov8s_rdd2022.pt"]
                assert res["visionExecutionMode"] == "real_yolo_inference"
                assert res.get("detectedObjects") is not None

    def test_compare_mode_separation_of_predictions(self, test_image_path):
        """Verify that in compare mode, local and hosted detections remain separate and are not merged."""
        with patch.object(settings, "civilens_vision_provider", "compare"):
            res = vision_manager.detect(test_image_path, category_hint="Roads & Footpaths")
            assert "visionComparison" in res
            assert "hosted" in res
            # Baseline detectedObjects belongs strictly to local model
            local_objs = res.get("detectedObjects", [])
            for obj in local_objs:
                assert obj.source_model in ["YOLOv8s RDD2022", "yolov8s_rdd2022.pt"]
                assert obj.execution_mode == "real_yolo_inference"

    def test_hosted_fallback_auth_error_no_mislabeling(self, test_image_path):
        """Verify that simulated 401 AUTH_ERROR logs category, triggers fallback, and never mislabels local YOLO."""
        from app.core.pipeline import pipeline
        from app.models.issue import IssueCreate

        with patch.object(settings, "civilens_vision_provider", "hosted"):
            mock_401 = {
                "provider": "roboflow",
                "status": "ERROR",
                "error": "Authentication failed (HTTP 401): Invalid or inactive Roboflow API key.",
                "errorCategory": "AUTH_ERROR",
                "modelId": "potholes-krmk8/2",
                "architecture": "YOLO26",
                "task": "ROAD_DAMAGE",
                "detectedObjects": [],
                "visualDetection": None,
                "visualConfidence": 0.0,
                "inferenceTimeMs": 150.0,
                "cached": False
            }
            with patch.object(vision_manager.roboflow_adapter, "infer", return_value=mock_401):
                res = vision_manager.detect(test_image_path, category_hint="Roads & Footpaths", enable_comparison=False)
                assert res.get("fallbackTriggered") is True
                assert res.get("hostedErrorCategory") == "AUTH_ERROR"
                assert "Authentication failed" in res.get("fallbackReason", "")
                # Must be local YOLO, NEVER mislabeled as Roboflow
                assert res["visionExecutionMode"] == "real_yolo_inference"
                assert res["sourceModel"] in ["YOLOv8s RDD2022", "yolov8s_rdd2022.pt"]

    def test_complaint_pipeline_stores_comparison_in_metadata(self):
        """Verify real complaint pipeline stores separate comparison outputs in issue.metadata."""
        from app.core.pipeline import pipeline
        from app.models.issue import IssueCreate

        with patch.object(settings, "civilens_vision_provider", "compare"):
            payload = IssueCreate(
                complaintText="Severe crater pothole causing vehicle alignment damage on LBS Marg",
                location="LBS Marg, Kurla West, Mumbai",
                latitude=19.0700,
                longitude=72.8800,
                imageUrl="data/test_samples/repair_pothole_before.jpg",
                category="Roads & Footpaths"
            )
            issue = pipeline.process_complaint(payload)
            assert issue.issueId.startswith("CIVIC-")
            assert "visionComparison" in issue.metadata
            assert "hosted" in issue.metadata
            assert issue.metadata["visionComparison"]["mode"] == "compare"
            # Baseline remains local YOLO
            assert issue.visionMode in ["real_yolo_inference", "deterministic_demo_fallback"]

