#!/usr/bin/env python3
"""
CIVILENS — Standalone Roboflow Hosted Serverless API Diagnostic Tool

Directly validates serverless inference against:
- Endpoint: https://serverless.roboflow.com
- Potholes Model: potholes-krmk8/2
- Garbage Model:  garbage_detection-wvzwv-n8vsv/1

Security & Integrity:
- Loads API key strictly from environment / .env
- Never logs, prints, or exposes private API keys or raw image bytes
- Reports real HTTP status, latency, prediction count, and returned class labels
"""

import os
import sys
import time
import argparse
import warnings
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from inference_sdk import InferenceHTTPClient, InferenceConfiguration
from inference_sdk.http.client import InferenceSDKGuidanceWarning
warnings.filterwarnings("ignore", category=InferenceSDKGuidanceWarning)

SERVERLESS_API_URL = "https://serverless.roboflow.com"
DEFAULT_POTHOLE_MODEL = "potholes-krmk8/2"
DEFAULT_GARBAGE_MODEL = "garbage_detection-wvzwv-n8vsv/1"

def run_hosted_diagnostic(
    pothole_image_path: str,
    garbage_image_path: str,
    pothole_model_id: str = DEFAULT_POTHOLE_MODEL,
    garbage_model_id: str = DEFAULT_GARBAGE_MODEL
) -> Dict[str, Any]:
    api_key = os.getenv("ROBOFLOW_API_KEY", "").strip()

    print("=" * 70)
    print("CIVILENS ROBOFLOW SERVERLESS HOSTED API DIAGNOSTIC")
    print("=" * 70)
    print(f"Target Gateway:        {SERVERLESS_API_URL}")
    print(f"Pothole Model ID:      {pothole_model_id}")
    print(f"Garbage Model ID:      {garbage_model_id}")
    print(f"API Key Present:       {bool(api_key)} (Length: {len(api_key)} chars)")
    print("=" * 70)

    if not api_key:
        print("\n[ERROR] ROBOFLOW_API_KEY is not configured in backend environment or .env file.")
        print("Set ROBOFLOW_API_KEY in .env before executing hosted diagnostic.")
        return {"status": "FAILED", "error": "MISSING_API_KEY"}

    config = InferenceConfiguration(api_key_transport="both")
    client = InferenceHTTPClient(
        api_url=SERVERLESS_API_URL,
        api_key=api_key
    )
    client.use_configuration(config)

    results = {
        "gateway": SERVERLESS_API_URL,
        "pothole": {},
        "garbage": {},
        "all_succeeded": False
    }

    # --------------------------------------------------------------------------
    # 1. Pothole Model Direct Test
    # --------------------------------------------------------------------------
    print(f"\n[1/2] Testing Pothole Model: {pothole_model_id}")
    print(f"      Image Path: {pothole_image_path}")

    if not os.path.exists(pothole_image_path):
        print(f"      [FAILED] Image file does not exist: {pothole_image_path}")
        results["pothole"] = {
            "status": "FAILED",
            "error_category": "IMAGE_NOT_FOUND",
            "model_id": pothole_model_id
        }
    else:
        t0 = time.time()
        try:
            pothole_res = client.infer(pothole_image_path, model_id=pothole_model_id)
            latency_ms = (time.time() - t0) * 1000.0
            predictions = pothole_res.get("predictions", [])
            class_labels = list({p.get("class", "unknown") for p in predictions})
            confidences = [round(p.get("confidence", 0.0), 4) for p in predictions]

            print(f"      Status:            SUCCESS (HTTP 200 OK)")
            print(f"      Latency:           {latency_ms:.2f} ms ({latency_ms/1000.0:.2f} s)")
            print(f"      Prediction Count:  {len(predictions)}")
            print(f"      Classes Detected:  {class_labels}")
            print(f"      Confidences:       {confidences}")
            print(f"      Inference ID:      {pothole_res.get('inference_id', 'N/A')}")

            results["pothole"] = {
                "status": "SUCCESS",
                "http_status": 200,
                "latency_ms": round(latency_ms, 2),
                "prediction_count": len(predictions),
                "classes": class_labels,
                "model_id": pothole_model_id,
                "inference_id": pothole_res.get("inference_id")
            }
        except Exception as e:
            latency_ms = (time.time() - t0) * 1000.0
            status_code = getattr(e, "status_code", None)
            err_msg = str(e)
            print(f"      [FAILED] Exception during hosted request:")
            print(f"      HTTP Status Code:  {status_code or 'Network / Request Error'}")
            print(f"      Latency:           {latency_ms:.2f} ms")
            print(f"      Exact Error:       {err_msg}")

            error_cat = "AUTH_ERROR" if status_code in (401, 403) else \
                        "MODEL_NOT_FOUND" if status_code == 404 else \
                        "RATE_LIMITED_OR_QUOTA" if status_code == 429 else "API_ERROR"

            results["pothole"] = {
                "status": "FAILED",
                "http_status": status_code,
                "error_category": error_cat,
                "error_message": err_msg,
                "latency_ms": round(latency_ms, 2),
                "model_id": pothole_model_id
            }

    # --------------------------------------------------------------------------
    # 2. Garbage Model Direct Test
    # --------------------------------------------------------------------------
    print(f"\n[2/2] Testing Garbage Model: {garbage_model_id}")
    print(f"      Image Path: {garbage_image_path}")

    if not os.path.exists(garbage_image_path):
        print(f"      [FAILED] Image file does not exist: {garbage_image_path}")
        results["garbage"] = {
            "status": "FAILED",
            "error_category": "IMAGE_NOT_FOUND",
            "model_id": garbage_model_id
        }
    else:
        t0 = time.time()
        try:
            garbage_res = client.infer(garbage_image_path, model_id=garbage_model_id)
            latency_ms = (time.time() - t0) * 1000.0
            predictions = garbage_res.get("predictions", [])
            class_labels = list({p.get("class", "unknown") for p in predictions})
            confidences = [round(p.get("confidence", 4), 4) for p in predictions]

            print(f"      Status:            SUCCESS (HTTP 200 OK)")
            print(f"      Latency:           {latency_ms:.2f} ms ({latency_ms/1000.0:.2f} s)")
            print(f"      Prediction Count:  {len(predictions)}")
            print(f"      Classes Detected:  {class_labels}")
            print(f"      Confidences:       {confidences}")
            print(f"      Inference ID:      {garbage_res.get('inference_id', 'N/A')}")

            results["garbage"] = {
                "status": "SUCCESS",
                "http_status": 200,
                "latency_ms": round(latency_ms, 2),
                "prediction_count": len(predictions),
                "classes": class_labels,
                "model_id": garbage_model_id,
                "inference_id": garbage_res.get("inference_id")
            }
        except Exception as e:
            latency_ms = (time.time() - t0) * 1000.0
            status_code = getattr(e, "status_code", None)
            err_msg = str(e)
            print(f"      [FAILED] Exception during hosted request:")
            print(f"      HTTP Status Code:  {status_code or 'Network / Request Error'}")
            print(f"      Latency:           {latency_ms:.2f} ms")
            print(f"      Exact Error:       {err_msg}")

            error_cat = "AUTH_ERROR" if status_code in (401, 403) else \
                        "MODEL_NOT_FOUND" if status_code == 404 else \
                        "RATE_LIMITED_OR_QUOTA" if status_code == 429 else "API_ERROR"

            results["garbage"] = {
                "status": "FAILED",
                "http_status": status_code,
                "error_category": error_cat,
                "error_message": err_msg,
                "latency_ms": round(latency_ms, 2),
                "model_id": garbage_model_id
            }

    # Summary
    p_ok = results["pothole"].get("status") == "SUCCESS"
    g_ok = results["garbage"].get("status") == "SUCCESS"
    results["all_succeeded"] = bool(p_ok and g_ok)

    print("\n" + "=" * 70)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 70)
    print(f"Pothole Model ({pothole_model_id}): {'SUCCESS' if p_ok else 'FAILED'}")
    print(f"Garbage Model ({garbage_model_id}): {'SUCCESS' if g_ok else 'FAILED'}")
    print(f"Overall Result:                  {'ALL MODELS ACCESSIBLE' if results['all_succeeded'] else 'INSPECTION REQUIRED'}")
    print("=" * 70)

    return results

def main():
    parser = argparse.ArgumentParser(description="Test Roboflow Hosted Serverless Inference Models")
    parser.add_argument(
        "--pothole-image",
        default="frontend/public/sample_pothole.jpg",
        help="Path to pothole test image"
    )
    parser.add_argument(
        "--garbage-image",
        default="data/downloads/taco_batch_1/batch_1/000001.jpg",
        help="Path to garbage test image"
    )
    parser.add_argument(
        "--pothole-model",
        default=os.getenv("ROBOFLOW_POTHOLE_MODEL_ID", DEFAULT_POTHOLE_MODEL),
        help="Roboflow pothole model ID"
    )
    parser.add_argument(
        "--garbage-model",
        default=os.getenv("ROBOFLOW_GARBAGE_MODEL_ID", DEFAULT_GARBAGE_MODEL),
        help="Roboflow garbage model ID"
    )

    args = parser.parse_args()

    res = run_hosted_diagnostic(
        pothole_image_path=args.pothole_image,
        garbage_image_path=args.garbage_image,
        pothole_model_id=args.pothole_model,
        garbage_model_id=args.garbage_model
    )

    if not res.get("all_succeeded"):
        sys.exit(1)

if __name__ == "__main__":
    main()

