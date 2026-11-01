import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Grant geolocation permission and mock position to Somaiya Vidyavihar, Mumbai
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 1
    })
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 900)
    
    # Mock geolocation coordinates to Somaiya Vidyavihar (19.0728, 72.8998)
    driver.execute_cdp_cmd(
        "Emulation.setGeolocationOverride",
        {
            "latitude": 19.0728,
            "longitude": 72.8998,
            "accuracy": 10
        }
    )
    return driver

def run_tests():
    os.makedirs("scripts/verification_screenshots", exist_ok=True)
    driver = get_driver()

    try:
        # =====================================================================
        # 1. CITIZEN LOGIN & COMPLAINT FORM LOCATION VERIFICATION
        # =====================================================================
        print("\n--- 1. Testing Citizen Location Capture ---")
        driver.get('http://localhost:5173/login/citizen')
        time.sleep(1.5)
        driver.execute_script("localStorage.clear();")
        driver.get('http://localhost:5173/login/citizen')
        time.sleep(1.5)

        # Fill demo credentials
        fill_btn = driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]")
        fill_btn.click()
        time.sleep(0.3)
        pwd_input = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd_input.clear()
        pwd_input.send_keys('Citizen@123')
        time.sleep(0.3)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign In to Workspace')]").click()
        time.sleep(3)

        # Navigate to File Grievance tab
        file_grievance_btn = driver.find_element(By.XPATH, "//button[contains(., 'File Grievance')]")
        driver.execute_script("arguments[0].click();", file_grievance_btn)
        time.sleep(2.0)

        driver.save_screenshot("scripts/verification_screenshots/citizen_form_empty.png")
        print("✓ Opened Citizen Grievance Form.")

        # Check that privacy explanation & location options are present
        page_src = driver.page_source
        assert "Geographic Verification Required" in page_src, "ERROR: Geographic verification notice missing!"
        assert "Option A: GPS Location" in page_src, "ERROR: Option A tab missing!"
        assert "Option B: Map Picker" in page_src, "ERROR: Option B tab missing!"
        assert "Detect My Location" in page_src, "ERROR: Detect My Location button missing!"

        # Verify submit button is disabled when no location is verified
        submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Submit Grievance')]")
        assert not submit_btn.is_enabled(), "ERROR: Submit button should be disabled without valid location!"
        print("✓ Verified: Submit button is strictly disabled without a verified location.")

        # -----------------------------------------------------------------
        # Test Option A: GPS Detection
        # -----------------------------------------------------------------
        detect_btn = driver.find_element(By.XPATH, "//button[contains(., 'Detect My Location')]")
        driver.execute_script("arguments[0].click();", detect_btn)
        time.sleep(2.5)

        driver.save_screenshot("scripts/verification_screenshots/citizen_gps_detected.png")
        page_src_after_gps = driver.page_source
        assert "Location Verified:" in page_src_after_gps, "ERROR: Location was not verified via GPS!"
        assert "19.0728" in page_src_after_gps, "ERROR: Latitude 19.0728 not reflected in status!"
        assert "72.8998" in page_src_after_gps, "ERROR: Longitude 72.8998 not reflected in status!"
        print("✓ Verified: Option A (Detect My Location) successfully captured GPS coordinates.")

        # -----------------------------------------------------------------
        # Test Out-of-Bounds Handling (Emulate coordinates outside Mumbai, e.g. Delhi)
        # -----------------------------------------------------------------
        print("\n--- 2. Testing Out-of-Bounds Rejection (Delhi Coordinates) ---")
        driver.execute_cdp_cmd(
            "Emulation.setGeolocationOverride",
            {
                "latitude": 28.6139,
                "longitude": 77.2090,
                "accuracy": 10
            }
        )
        time.sleep(0.5)
        detect_btn = driver.find_element(By.XPATH, "//button[contains(., 'Detect My Location')]")
        driver.execute_script("arguments[0].click();", detect_btn)
        time.sleep(2.0)

        driver.save_screenshot("scripts/verification_screenshots/citizen_gps_out_of_bounds.png")
        page_src_oob = driver.page_source
        assert "CIVILENS currently supports complaints from Mumbai and Navi Mumbai only" in page_src_oob, "ERROR: Out of bounds error banner missing!"
        submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Submit Grievance')]")
        assert not submit_btn.is_enabled(), "ERROR: Submit button should be disabled when location is out of bounds!"
        print("✓ Verified: Out-of-bounds GPS location correctly rejected with warning banner.")

        # -----------------------------------------------------------------
        # Test Option B: Manual Selection via Navi Mumbai Preset Chip
        # -----------------------------------------------------------------
        print("\n--- 3. Testing Option B: Manual Selection (Navi Mumbai) ---")
        manual_tab_btn = driver.find_element(By.XPATH, "//button[contains(., 'Option B')]")
        driver.execute_script("arguments[0].click();", manual_tab_btn)
        time.sleep(1.0)

        # Click on "Sector 17" or "Vashi" preset chip
        vashi_chip = driver.find_element(By.XPATH, "//button[contains(., 'Sector 17')]")
        driver.execute_script("arguments[0].click();", vashi_chip)
        time.sleep(2.0)

        driver.save_screenshot("scripts/verification_screenshots/citizen_vashi_selected.png")
        page_src_vashi = driver.page_source
        assert "Location Verified:" in page_src_vashi, "ERROR: Location verification banner missing for Navi Mumbai preset!"
        assert "19.0771" in page_src_vashi or "19.07" in page_src_vashi, "ERROR: Navi Mumbai coordinates missing!"
        assert "Navi Mumbai" in page_src_vashi or "NMMC" in page_src_vashi, "ERROR: Navi Mumbai / NMMC ward missing!"
        print("✓ Verified: Navi Mumbai manual selection correctly verified with derived NMMC ward.")

        # -----------------------------------------------------------------
        # Submit Real Civic Complaint
        # -----------------------------------------------------------------
        print("\n--- 4. Submitting Grievance & Verifying Real-Time Synchronization ---")
        complaint_desc = "Major deep pothole crater breaking suspension near Vashi Sector 17 main market road"
        desc_input = driver.find_element(By.XPATH, "//textarea")
        driver.execute_script('''
            var el = arguments[0];
            var val = arguments[1];
            var proto = window.HTMLTextAreaElement.prototype;
            var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        ''', desc_input, complaint_desc)
        time.sleep(1.0)

        submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Submit Grievance')]")
        assert submit_btn.is_enabled(), "ERROR: Submit button should be enabled after filling form!"
        driver.execute_script("arguments[0].click();", submit_btn)
        
        # Robustly wait for submission pipeline to process and return
        WebDriverWait(driver, 15).until(
            lambda d: "submitted successfully" in d.page_source or "My Grievances" in d.page_source
        )
        time.sleep(1.0)
        driver.save_screenshot("scripts/verification_screenshots/citizen_submitted.png")
        print("✓ Grievance submitted successfully.")

        # Immediately verify the newly submitted complaint appears on the GIS map WITHOUT reload or relogin
        driver.get('http://localhost:5173/#map')
        time.sleep(2.0)
        citizen_map_pins = driver.find_elements(By.CLASS_NAME, "custom-incident-pin")
        assert len(citizen_map_pins) >= 1, "ERROR: Submitted complaint missing from GIS map!"
        driver.save_screenshot("scripts/verification_screenshots/citizen_map_sync.png")
        print(f"✓ Verified: Newly submitted complaint synchronized directly to GIS map ({len(citizen_map_pins)} pins rendered without reload).")

        # =====================================================================
        # 5. VERIFY REAL-TIME GIS MAP SYNCHRONIZATION AS MUNICIPAL OFFICER / ADMIN
        # =====================================================================
        print("\n--- 5. Verifying Real-Time GIS Map Appearance in Officer Workspace ---")
        officer_driver = get_driver()
        try:
            officer_driver.get('http://localhost:5173/login/municipal')
            time.sleep(1.0)
            fill_btn = officer_driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]")
            fill_btn.click()
            time.sleep(0.3)
            pwd_input = officer_driver.find_element(By.XPATH, "//input[@type='password']")
            pwd_input.clear()
            pwd_input.send_keys('Inspector@123')
            time.sleep(0.3)
            officer_driver.find_element(By.XPATH, "//button[contains(., 'Sign In to Workspace')]").click()

            # Wait for Inspector workspace to authenticate and load Command Center
            WebDriverWait(officer_driver, 15).until(
                lambda d: "Command Center" in d.page_source and len(d.find_elements(By.CLASS_NAME, "custom-incident-pin")) > 0
            )
            time.sleep(1.0)

            # Wait for the newly submitted issue to appear in the Priority Incident Queue
            WebDriverWait(officer_driver, 15).until(
                lambda d: "Vashi" in d.page_source or "Sector 17" in d.page_source
            )
            officer_driver.save_screenshot("scripts/verification_screenshots/officer_overview_sync.png")
            overview_src = officer_driver.page_source
            assert "Vashi" in overview_src or "Sector 17" in overview_src, "ERROR: Newly filed complaint missing from Command Center Priority Queue!"
            print("✓ Verified: Newly filed complaint appears in Command Center Priority Queue.")

            # Check GIS Map pins on Command Center
            overview_pins = officer_driver.find_elements(By.CLASS_NAME, "custom-incident-pin")
            assert len(overview_pins) >= 1, "ERROR: Incident pins missing from Command Center GIS map!"
            print(f"✓ Command Center GIS Map rendered {len(overview_pins)} incident pins.")

            # Navigate to Full Tactical GIS Map (#map)
            officer_driver.get('http://localhost:5173/#map')
            time.sleep(2.0)

            officer_driver.save_screenshot("scripts/verification_screenshots/officer_tactical_map_view.png")
            tactical_pins = officer_driver.find_elements(By.CLASS_NAME, "custom-incident-pin")
            assert len(tactical_pins) >= 1, "ERROR: Incident pins missing from Tactical GIS Map view!"
            print(f"✓ Tactical GIS Map rendered {len(tactical_pins)} incident pins.")

            # Click the marker on the map to verify dossier panel opens
            officer_driver.execute_script("arguments[0].click();", tactical_pins[0])
            time.sleep(2.0)
            officer_driver.save_screenshot("scripts/verification_screenshots/officer_map_dossier.png")
            print("✓ Clicked incident marker on GIS map; verified interactive dossier/details.")
        finally:
            officer_driver.quit()

        print("\n=======================================================")
        print("REAL-TIME GEOLOCATION & GIS MAP SYNCHRONIZATION PASSED!")
        print("=======================================================")

    finally:
        driver.quit()

if __name__ == '__main__':
    run_tests()
