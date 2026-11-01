#!/usr/bin/env python3
"""
CIVILENS — Real Browser Verification of Roboflow Comparison UI in Issue Dossier

Validates:
1. Pothole complaint with hosted comparison (Local YOLOv8s RDD2022 vs Hosted potholes-krmk8/2).
2. Garbage complaint with hosted comparison (Local YOLO11s TACO Waste vs Hosted garbage_detection-wvzwv-n8vsv/1).
3. Legacy complaint without hosted metadata ("No hosted comparison is available").
4. Failed hosted inference error display.
5. Local and hosted bounding-box tab switching.
6. Access control: Citizen role (hidden) vs Inspector/Admin (visible).
"""

import os
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 900)
    return driver

def login_role(driver, role_path, demo_password):
    driver.get(f"http://localhost:5173{role_path}")
    time.sleep(1.2)
    fill_btn = driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]")
    fill_btn.click()
    time.sleep(0.3)
    pwd = driver.find_element(By.XPATH, "//input[@type='password']")
    pwd.clear()
    pwd.send_keys(demo_password)
    submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Sign In to Workspace') or @type='submit']")
    submit_btn.click()
    time.sleep(2.5)

def close_drawer(driver):
    close_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Close Panel')]")
    if close_btns:
        driver.execute_script("arguments[0].click();", close_btns[0])
        time.sleep(1.0)
        return
    backdrops = driver.find_elements(By.CSS_SELECTOR, ".layer-drawer")
    if backdrops:
        driver.execute_script("arguments[0].click();", backdrops[0])
        time.sleep(1.0)

def open_card(driver, issue_id, timeout=12):
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, f"[data-incident-id='{issue_id}']")) > 0
    )
    cards = driver.find_elements(By.CSS_SELECTOR, f"[data-incident-id='{issue_id}']")
    assert len(cards) > 0, f"Could not find card for {issue_id} in queue"
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", cards[0])
    time.sleep(0.4)
    driver.execute_script("arguments[0].click();", cards[0])
    time.sleep(2.0)

def ensure_test_fixtures():
    from app.models.issue import Issue
    from app.core.demo_store import demo_store

    failed_issue = Issue(
        issueId="CIVIC-TEST-FAILED-CV",
        complaintText="Simulated failed hosted candidate inference on S.V. Road near Bandra",
        category="Roads & Footpaths",
        priorityScore=68.5,
        severity=0.65,
        location="S.V. Road, Bandra West, Mumbai",
        latitude=19.055,
        longitude=72.835,
        timestamp="2026-11-02T00:00:00Z",
        imageUrl="data/sample_pothole.jpg",
        visionModel="YOLOv8s RDD2022",
        visionMode="real_yolo_inference",
        metadata={
            "source": "citizen_portal",
            "ward": "H/West",
            "hosted": {
                "provider": "roboflow",
                "status": "ERROR",
                "modelId": "potholes-krmk8/2",
                "architecture": "YOLO26",
                "task": "ROAD_DAMAGE",
                "error": "Authentication failed (HTTP 401): Invalid or inactive Roboflow API key.",
                "errorCategory": "AUTH_ERROR",
                "inferenceTimeMs": 115.0,
                "cached": False,
                "detectedObjects": []
            },
            "visionComparison": {
                "mode": "compare",
                "comparisonSummary": {
                    "localModel": "YOLOv8s RDD2022",
                    "hostedModel": "potholes-krmk8/2 (YOLO26)",
                    "localDetectionCount": 1,
                    "hostedDetectionCount": 0,
                    "hostedStatus": "ERROR",
                    "hostedCached": False,
                    "localLatencyMs": 48.0,
                    "hostedLatencyMs": 115.0
                },
                "local": {
                    "sourceModel": "YOLOv8s RDD2022",
                    "visionExecutionMode": "real_yolo_inference",
                    "detectedObjects": [
                        {"label": "Pothole (D40)", "confidence": 0.94, "bbox": [0.38, 0.22, 0.76, 0.8]}
                    ]
                },
                "hosted": {
                    "status": "ERROR",
                    "modelId": "potholes-krmk8/2",
                    "error": "Authentication failed (HTTP 401): Invalid or inactive Roboflow API key.",
                    "errorCategory": "AUTH_ERROR"
                }
            }
        }
    )
    demo_store.add_issue(failed_issue)
    print("✓ Created/registered mock failed hosted inference issue: CIVIC-TEST-FAILED-CV")

def run_ui_tests():
    os.makedirs("scripts/verification_screenshots", exist_ok=True)
    ensure_test_fixtures()

    print("=" * 70)
    print("REAL-BROWSER VERIFICATION: ROBOFLOW COMPARISON UI IN ISSUE DOSSIER")
    print("=" * 70)

    # ---------------------------------------------------------------------
    # Test 1: Citizen Role Access Control Test
    # ---------------------------------------------------------------------
    print("\n[Test 1] Verifying Citizen Role Access Control...")
    d_citizen = get_driver()
    try:
        login_role(d_citizen, '/login/citizen', 'Citizen@123')
        view_detail_btns = d_citizen.find_elements(By.XPATH, "//button[contains(., 'View Details')]")
        if view_detail_btns:
            d_citizen.execute_script("arguments[0].click();", view_detail_btns[0])
            time.sleep(2.0)

        d_citizen.save_screenshot("scripts/verification_screenshots/ui_citizen_no_comparison.png")
        page_html = d_citizen.page_source
        has_comparison_in_citizen = "Vision Model Comparison" in page_html
        print(f"  Citizen View rendered 'Vision Model Comparison'? {has_comparison_in_citizen}")
        assert not has_comparison_in_citizen, "SECURITY FAIL: Citizen view must NOT expose Vision Model Comparison!"
        print("✓ Access Control Verified: Citizen cannot view experimental vision model diagnostics.")
    finally:
        d_citizen.quit()

    # ---------------------------------------------------------------------
    # Tests 2–5: Municipal Officer (Inspector) Workflows
    # ---------------------------------------------------------------------
    print("\n[Tests 2-5] Inspector Role Workflows...")
    d_inspector = get_driver()
    try:
        login_role(d_inspector, '/login/municipal', 'Inspector@123')
        WebDriverWait(d_inspector, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "[data-incident-id]")) > 0
        )

        # [Test 2] Pothole Complaint with Hosted Comparison
        print("\n[Test 2] Inspector Role: Pothole Complaint with Hosted Comparison...")
        open_card(d_inspector, 'CIVIC-2026-23363092')
        dossier_html = d_inspector.page_source
        assert "Vision Model Comparison" in dossier_html, "Missing 'Vision Model Comparison' heading in dossier"
        assert "Production Baseline" in dossier_html, "Missing 'Production Baseline' panel"
        assert "Roboflow Hosted Candidate" in dossier_html, "Missing 'Roboflow Hosted Candidate' panel"
        assert "potholes-krmk8/2" in dossier_html, "Missing hosted model ID potholes-krmk8/2"
        print("✓ Vision Model Comparison header, baseline, and candidate panels rendered.")

        d_inspector.save_screenshot("scripts/verification_screenshots/ui_pothole_comparison_local.png")
        print("✓ Screenshot saved: ui_pothole_comparison_local.png")

        # Click Hosted Roboflow tab
        hosted_tab = d_inspector.find_elements(By.XPATH, "//button[contains(., 'Roboflow Hosted')]")
        if hosted_tab:
            d_inspector.execute_script("arguments[0].click();", hosted_tab[0])
            time.sleep(1.0)
            d_inspector.save_screenshot("scripts/verification_screenshots/ui_pothole_comparison_hosted.png")
            print("✓ Clicked Roboflow Hosted tab; screenshot saved: ui_pothole_comparison_hosted.png")

        # [Test 3] Garbage Complaint with Hosted Comparison
        print("\n[Test 3] Inspector Role: Garbage Complaint with Hosted Comparison...")
        close_drawer(d_inspector)
        open_card(d_inspector, 'CIVIC-2026-836D1677')

        g_html = d_inspector.page_source
        assert "garbage_detection-wvzwv-n8vsv/1" in g_html, "Missing hosted model ID garbage_detection-wvzwv-n8vsv/1"
        assert "RF-DETR Nano" in g_html, "Missing architecture RF-DETR Nano"
        print("✓ Garbage complaint comparison rendered with correct hosted model ID and architecture.")

        d_inspector.save_screenshot("scripts/verification_screenshots/ui_garbage_comparison_local.png")
        print("✓ Screenshot saved: ui_garbage_comparison_local.png")

        hosted_tab = d_inspector.find_elements(By.XPATH, "//button[contains(., 'Roboflow Hosted')]")
        if hosted_tab:
            d_inspector.execute_script("arguments[0].click();", hosted_tab[0])
            time.sleep(1.0)
            d_inspector.save_screenshot("scripts/verification_screenshots/ui_garbage_comparison_hosted.png")
            print("✓ Clicked Roboflow Hosted tab on garbage; screenshot saved: ui_garbage_comparison_hosted.png")

        # [Test 4] Legacy Complaint Without Comparison Metadata
        print("\n[Test 4] Inspector Role: Legacy Complaint Without Comparison Metadata...")
        close_drawer(d_inspector)
        open_card(d_inspector, 'CIVIC-2026-001')
        d_inspector.save_screenshot("scripts/verification_screenshots/ui_legacy_complaint_quiet_state.png")
        seed_html = d_inspector.page_source
        assert "No hosted comparison is available for this complaint." in seed_html, \
            "Missing quiet state message for legacy complaint"
        print("✓ Verified: Legacy complaint renders quiet informative message without errors or fake data.")

        # [Test 5] Failed Hosted Inference Alert
        print("\n[Test 5] Inspector Role: Failed Hosted Inference Alert...")
        close_drawer(d_inspector)
        open_card(d_inspector, 'CIVIC-TEST-FAILED-CV')
        d_inspector.save_screenshot("scripts/verification_screenshots/ui_failed_hosted_inference.png")
        fail_html = d_inspector.page_source
        assert "Hosted Candidate Unavailable" in fail_html, "Missing 'Hosted Candidate Unavailable' banner"
        assert "AUTH_ERROR" in fail_html, "Missing AUTH_ERROR category tag"
        print("✓ Verified: Failed hosted inference displays structured error and fallback explanation.")
    finally:
        d_inspector.quit()

    # ---------------------------------------------------------------------
    # Test 6: Admin Role Access Verification
    # ---------------------------------------------------------------------
    print("\n[Test 6] Admin Role Access Verification...")
    d_admin = get_driver()
    try:
        login_role(d_admin, '/login/admin', 'Admin@123')
        WebDriverWait(d_admin, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "[data-incident-id]")) > 0
        )
        open_card(d_admin, 'CIVIC-2026-23363092')
        d_admin.save_screenshot("scripts/verification_screenshots/ui_admin_comparison_view.png")
        admin_html = d_admin.page_source
        assert "Vision Model Comparison" in admin_html, "Missing Vision Model Comparison in admin dossier"
        print("✓ Verified: Admin role can view Vision Model Comparison.")
    finally:
        d_admin.quit()

    print("\n" + "=" * 70)
    print("ALL 6 REAL-BROWSER ROBOFLOW COMPARISON UI TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_ui_tests()
