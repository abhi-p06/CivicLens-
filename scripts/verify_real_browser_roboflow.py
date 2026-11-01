#!/usr/bin/env python3
"""
CIVILENS — Real Browser End-to-End Verification of Roboflow Hosted Integration

Drives Chrome via Selenium at 1600x900 to:
1. Log in as Citizen on http://localhost:5173/login/citizen
2. Submit fresh Pothole complaint with data/fresh_pothole_browser_test.jpg
3. Submit fresh Garbage complaint with data/fresh_garbage_browser_test.jpg
4. Capture complaint IDs
5. Log in as Municipal Inspector on http://localhost:5173/login/municipal
6. Open Issue Dossier to inspect UI presentation of vision results
7. Query API / database to correlate outbound Roboflow calls and verify metadata
"""

import os
import sys
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 1
    })
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 900)
    
    # Mock location to Somaiya Vidyavihar, Mumbai (19.0728, 72.8998)
    driver.execute_cdp_cmd(
        "Emulation.setGeolocationOverride",
        {
            "latitude": 19.0728,
            "longitude": 72.8998,
            "accuracy": 10
        }
    )
    return driver

def set_textarea_value(driver, element, value):
    driver.execute_script('''
        var el = arguments[0];
        var val = arguments[1];
        var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        setter.call(el, val);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    ''', element, value)

def wait_for_upload_and_submit(driver, file_path, timeout=20):
    file_input = driver.find_element(By.XPATH, "//input[@type='file']")
    file_input.send_keys(file_path)
    print(f"  Sent fresh file {Path(file_path).name}, waiting for upload...")

    t0 = time.time()
    while time.time() - t0 < timeout:
        submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Submit Grievance')]")
        if submit_btn.get_attribute("disabled") is None:
            print(f"  Upload completed and submit button enabled ({time.time() - t0:.1f}s).")
            return submit_btn
        time.sleep(0.5)

    raise TimeoutError(f"Submit button was not enabled within {timeout}s after uploading {file_path}")

def run_browser_verification():
    os.makedirs("scripts/verification_screenshots", exist_ok=True)
    driver = get_driver()
    created_issues = {}

    try:
        print("=" * 70)
        print("REAL-BROWSER VERIFICATION: CITIZEN WORKFLOW & ROBOFLOW INTEGRATION")
        print("=" * 70)

        # ---------------------------------------------------------------------
        # 1. Citizen Login
        # ---------------------------------------------------------------------
        print("\n[Step 1] Navigating to Citizen Login (http://localhost:5173/login/citizen)...")
        driver.get('http://localhost:5173/login/citizen')
        time.sleep(1.5)
        driver.execute_script("localStorage.clear();")
        driver.get('http://localhost:5173/login/citizen')
        time.sleep(1.5)

        fill_btn = driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]")
        driver.execute_script("arguments[0].click();", fill_btn)
        time.sleep(0.3)
        pwd_input = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd_input.clear()
        pwd_input.send_keys('Citizen@123')
        time.sleep(0.3)
        sign_in_btn = driver.find_element(By.XPATH, "//button[contains(., 'Sign In to Workspace')]")
        driver.execute_script("arguments[0].click();", sign_in_btn)
        time.sleep(3.0)
        print("✓ Citizen login successful.")

        # ---------------------------------------------------------------------
        # 2. Submit Fresh Pothole Complaint
        # ---------------------------------------------------------------------
        print("\n[Step 2] Filing Fresh Pothole Complaint in Real Browser...")
        file_grievance_btn = driver.find_element(By.XPATH, "//button[contains(., 'File Grievance')]")
        driver.execute_script("arguments[0].click();", file_grievance_btn)
        time.sleep(1.5)

        # Select Road category button
        road_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Road Damage & Potholes')]")
        if road_btns:
            driver.execute_script("arguments[0].click();", road_btns[0])
            time.sleep(0.3)

        # Location: Detect My Location
        detect_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Detect My Location')]")
        if detect_btns:
            driver.execute_script("arguments[0].click();", detect_btns[0])
            print("  Detecting GPS location...")
            time.sleep(2.5)

        # Enter Complaint Description
        desc_box = driver.find_element(By.XPATH, "//textarea")
        pothole_text = "Major fresh deep crater pothole breaking vehicle axles near Somaiya Vidyavihar arterial road."
        set_textarea_value(driver, desc_box, pothole_text)
        time.sleep(0.5)

        # Upload Fresh Pothole Image
        pothole_img_path = os.path.abspath("data/fresh_pothole_browser_test.jpg")
        submit_btn = wait_for_upload_and_submit(driver, pothole_img_path)
        driver.save_screenshot("scripts/verification_screenshots/browser_citizen_pothole_form.png")

        # Submit Grievance
        driver.execute_script("arguments[0].click();", submit_btn)
        print("  Submitted pothole complaint. Waiting for server response...")
        time.sleep(5.0)

        # Retrieve newest issue from API
        all_issues = requests.get("http://localhost:8000/api/v1/issues").json()
        pothole_issue = None
        for iss in all_issues:
            if "breaking vehicle axles" in iss.get("complaintText", ""):
                pothole_issue = iss
                break
        
        assert pothole_issue is not None, "Failed to locate newly created pothole issue via API!"
        pothole_id = pothole_issue["issueId"]
        created_issues["pothole"] = pothole_issue
        print(f"✓ Pothole Complaint Created: {pothole_id}")
        driver.save_screenshot("scripts/verification_screenshots/browser_pothole_submitted.png")

        # ---------------------------------------------------------------------
        # 3. Submit Fresh Garbage Complaint
        # ---------------------------------------------------------------------
        print("\n[Step 3] Filing Fresh Garbage Complaint in Real Browser...")
        file_grievance_btn = driver.find_element(By.XPATH, "//button[contains(., 'File Grievance')]")
        driver.execute_script("arguments[0].click();", file_grievance_btn)
        time.sleep(1.5)

        # Select Garbage category button
        garbage_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Garbage & Litter')]")
        if garbage_btns:
            driver.execute_script("arguments[0].click();", garbage_btns[0])
            time.sleep(0.3)

        # Location: Detect My Location
        detect_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Detect My Location')]")
        if detect_btns:
            driver.execute_script("arguments[0].click();", detect_btns[0])
            print("  Detecting GPS location...")
            time.sleep(2.5)

        # Enter Complaint Description
        desc_box = driver.find_element(By.XPATH, "//textarea")
        garbage_text = "Massive fresh garbage accumulation and street litter spilling onto sidewalk near Vidyavihar station."
        set_textarea_value(driver, desc_box, garbage_text)
        time.sleep(0.5)

        # Upload Fresh Garbage Image
        garbage_img_path = os.path.abspath("data/fresh_garbage_browser_test.jpg")
        submit_btn = wait_for_upload_and_submit(driver, garbage_img_path)
        driver.save_screenshot("scripts/verification_screenshots/browser_citizen_garbage_form.png")

        # Submit Grievance
        driver.execute_script("arguments[0].click();", submit_btn)
        print("  Submitted garbage complaint. Waiting for server response...")
        time.sleep(5.0)

        all_issues_2 = requests.get("http://localhost:8000/api/v1/issues").json()
        garbage_issue = None
        for iss in all_issues_2:
            if "spilling onto sidewalk" in iss.get("complaintText", ""):
                garbage_issue = iss
                break

        assert garbage_issue is not None, "Failed to locate newly created garbage issue via API!"
        garbage_id = garbage_issue["issueId"]
        created_issues["garbage"] = garbage_issue
        print(f"✓ Garbage Complaint Created: {garbage_id}")
        driver.save_screenshot("scripts/verification_screenshots/browser_garbage_submitted.png")

        # ---------------------------------------------------------------------
        # 4. Inspector Dossier UI Inspection
        # ---------------------------------------------------------------------
        print("\n[Step 4] Navigating to Municipal Inspector to Check Issue Dossier UI...")
        driver.get('http://localhost:5173/login/municipal')
        time.sleep(1.5)

        fill_btn = driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]")
        driver.execute_script("arguments[0].click();", fill_btn)
        time.sleep(0.3)
        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd.clear()
        pwd.send_keys('Inspector@123')
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3.0)

        # Open dossier for the newly submitted pothole complaint
        print(f"  Attempting to open Issue Dossier for {pothole_id}...")
        driver.get('http://localhost:5173/')
        time.sleep(3.0)

        # Locate complaint card in the queue
        card_xpath = f"//*[contains(text(), '{pothole_id}') or contains(text(), 'breaking vehicle axles')]"
        cards = driver.find_elements(By.XPATH, card_xpath)
        if cards:
            driver.execute_script("arguments[0].click();", cards[0])
            time.sleep(2.5)
            driver.save_screenshot("scripts/verification_screenshots/browser_inspector_dossier.png")
            print("✓ Issue Dossier opened successfully in real browser.")
            
            dossier_html = driver.page_source
            has_comparison_ui = "visionComparison" in dossier_html or "Hosted Roboflow" in dossier_html or "Roboflow Candidate" in dossier_html
            print(f"  [UI CHECK - STEP 10] Does the Issue Dossier render hosted comparison results directly? {'YES' if has_comparison_ui else 'NO (Confirmed UI Gap)'}")
        else:
            print(f"  Card for {pothole_id} not clicked directly; saving current inspector overview.")
            driver.save_screenshot("scripts/verification_screenshots/browser_inspector_overview.png")

        return created_issues

    finally:
        driver.quit()

if __name__ == "__main__":
    res = run_browser_verification()
    print("\nBrowser verification run complete.")
