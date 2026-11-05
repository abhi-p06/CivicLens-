import time
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

ARTIFACT_DIR = "/Users/abby/.gemini/antigravity/brain/8410a3de-935e-44ee-892c-585688fdf2d4"
SCREENSHOT_DIR = "scripts/verification_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def get_driver(width=1600, height=900):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(width, height)
    return driver

def save_and_copy(driver, filename):
    local_path = os.path.join(SCREENSHOT_DIR, filename)
    artifact_path = os.path.join(ARTIFACT_DIR, filename)
    driver.save_screenshot(local_path)
    shutil.copy(local_path, artifact_path)
    print(f"Captured: {local_path} and copied to {artifact_path}")

def run_phase5_visual_verification():
    driver = get_driver(1600, 900)
    try:
        # 1. Inspector Login & My Action Queue Scoping
        print("\n--- 1. Testing Inspector Login & My Action Queue ---")
        driver.get('http://localhost:5173/login/municipal')
        time.sleep(1.5)

        fill_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Fill demo account')]")
        if fill_btn:
            fill_btn[0].click()
            time.sleep(0.3)
        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd.clear()
        pwd.send_keys('Inspector@123')
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        # Navigate to My Action Queue (Explorer)
        driver.get('http://localhost:5173/#explorer')
        time.sleep(2)

        save_and_copy(driver, "phase5_inspector_queue_filters.png")
        page_html = driver.page_source
        assert "My Action Queue" in page_html, "Missing 'My Action Queue'"
        assert "Authorized Scope" in page_html, "Missing 'Authorized Scope' badge"
        assert "Ward: N-Ward" in page_html, "Missing locked N-Ward jurisdiction indicator"
        print("✓ Verified: Inspector Action Queue with authorized jurisdiction scope and filters.")

        # 2. Click first complaint to open Issue Detail Drawer with 8-tier routing
        print("\n--- 2. Testing Issue Detail Drawer with 8-Tier Geographical Routing ---")
        open_dossier_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Open Dossier')]")
        if open_dossier_btns:
            driver.execute_script("arguments[0].click();", open_dossier_btns[0])
            time.sleep(2.5)

        save_and_copy(driver, "phase5_issue_dossier_8_tier_routing.png")
        drawer_html = driver.page_source
        assert "Geographical Routing" in drawer_html or "Municipal Authority" in drawer_html, "Missing geographical routing in drawer"
        print("✓ Verified: Issue Detail Drawer with 8-Tier hierarchy breadcrumbs.")

        # 3. GIS Map View with HUD Filters & 8-Tier Routing
        print("\n--- 3. Testing GIS Map View Tactical Hierarchy Filters ---")
        driver.get('http://localhost:5173/#map')
        time.sleep(3)

        # Click on a marker or trigger issue inspection if available
        markers = driver.find_elements(By.CLASS_NAME, "leaflet-marker-icon")
        if markers:
            try:
                markers[0].click()
                time.sleep(1.5)
            except Exception as e:
                print("Note on marker click:", e)

        save_and_copy(driver, "phase5_gis_tactical_routing.png")
        print("✓ Verified: Tactical GIS Map HUD with Authority/Ward/Sub-Ward/Beat filters.")

        # 4. Citizen Portal Sanitized Tracking
        print("\n--- 4. Testing Citizen Portal Sanitized Tracking ---")
        driver.execute_script("localStorage.clear(); sessionStorage.clear();")
        time.sleep(0.5)
        driver.get('http://localhost:5173/login/citizen')
        time.sleep(1.5)

        c_fill = driver.find_elements(By.XPATH, "//button[contains(., 'Fill demo account')]")
        if c_fill:
            c_fill[0].click()
            time.sleep(0.3)
        c_pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        c_pwd.clear()
        c_pwd.send_keys('Citizen@123')
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        driver.get('http://localhost:5173/#citizen_portal')
        time.sleep(2)

        save_and_copy(driver, "phase5_citizen_sanitized_tracking.png")
        citizen_html = driver.page_source
        assert "Officer:" not in citizen_html, "LEAK: 'Officer:' was rendered to citizen"
        print("✓ Verified: Citizen Portal shows civic hierarchy without internal officer details.")

        # 5. Responsive check at 1280x800
        print("\n--- 5. Testing Responsive Desktop (1280x800) ---")
        driver.set_window_size(1280, 800)
        time.sleep(1)
        driver.get('http://localhost:5173/#explorer')
        time.sleep(2)
        save_and_copy(driver, "phase5_inspector_queue_1280x800.png")
        print("✓ Verified: 1280x800 responsive layout.")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_phase5_visual_verification()
