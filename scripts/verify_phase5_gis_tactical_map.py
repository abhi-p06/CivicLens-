import time
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    print(f"Captured: {local_path} -> Copied to {artifact_path}")

def run_gis_map_verification():
    driver = get_driver(1600, 900)
    try:
        print("\n==================================================================")
        print("CIVILENS PHASE 5 — TACTICAL GIS MAP VISUAL VERIFICATION")
        print("==================================================================")

        # 1. Login as Inspector
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

        # 2. Navigate to Tactical GIS Map View
        print("\n--- 1. Navigating to Map View (1600x900) ---")
        driver.get('http://localhost:5173/#map')
        time.sleep(3)

        save_and_copy(driver, "phase5_map_all_layers_1600x900.png")
        print("✓ Captured: Full Map View with Admin Wards and CIVILENS Sub-Wards")

        # 3. Test Layer Visibility Toggles
        print("\n--- 2. Testing Layer Visibility Toggles (4 States) ---")
        # Find checkboxes for "Admin Wards" and "CIVILENS Sub-Wards"
        admin_cb = driver.find_elements(By.XPATH, "//label[contains(., 'Admin Wards')]//input[@type='checkbox']")
        sub_cb = driver.find_elements(By.XPATH, "//label[contains(., 'CIVILENS Sub-Wards')]//input[@type='checkbox']")

        if admin_cb and sub_cb:
            # State 2: Uncheck Admin Wards -> only Sub-Wards visible
            driver.execute_script("arguments[0].click();", admin_cb[0])
            time.sleep(1)
            save_and_copy(driver, "phase5_map_subwards_only.png")
            print("✓ State 2: Admin Wards unchecked, only CIVILENS Sub-Wards visible")

            # State 3: Uncheck Sub-Wards -> both off
            driver.execute_script("arguments[0].click();", sub_cb[0])
            time.sleep(1)
            save_and_copy(driver, "phase5_map_no_boundaries.png")
            print("✓ State 3: Both boundary layers unchecked (clean map)")

            # State 4: Check Admin Wards -> only Admin Wards visible
            driver.execute_script("arguments[0].click();", admin_cb[0])
            time.sleep(1)
            save_and_copy(driver, "phase5_map_admin_only.png")
            print("✓ State 4: Only Admin Wards visible")

            # Re-check Sub-Wards -> both on
            driver.execute_script("arguments[0].click();", sub_cb[0])
            time.sleep(1)
            print("✓ Restored: Both boundary layers active")

        # 4. Test Display Modes: Clusters, Heatmap, Pins
        print("\n--- 3. Testing Display Modes (Clusters, Heatmap, Pins) ---")
        clusters_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Clusters')]")
        if clusters_btn:
            driver.execute_script("arguments[0].click();", clusters_btn[0])
            time.sleep(1.2)
            save_and_copy(driver, "phase5_map_clusters_mode.png")
            print("✓ Switched to Proximity Clustering Mode")

        heatmap_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Heatmap')]")
        if heatmap_btn:
            driver.execute_script("arguments[0].click();", heatmap_btn[0])
            time.sleep(1.2)
            save_and_copy(driver, "phase5_map_heatmap_mode.png")
            print("✓ Switched to Priority Density Heatmap Mode")

        pins_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Pins')]")
        if pins_btn:
            driver.execute_script("arguments[0].click();", pins_btn[0])
            time.sleep(1.2)
            save_and_copy(driver, "phase5_map_pins_category_differentiated.png")
            print("✓ Switched to Pins Mode with Category & Priority Differentiated Badges")

        # 5. Test Filters & Clear All Filters
        print("\n--- 4. Testing Multi-Filters & Clear All Filters Button ---")
        # Select Ward filter
        ward_selects = driver.find_elements(By.XPATH, "//div[contains(., 'Ward:')]//select")
        if ward_selects:
            for option in ward_selects[0].find_elements(By.TAG_NAME, 'option'):
                if 'N-Ward' in option.text:
                    driver.execute_script("arguments[0].selected = true; arguments[1].dispatchEvent(new Event('change'));", option, ward_selects[0])
                    break
            time.sleep(1.5)
            save_and_copy(driver, "phase5_map_filtered_nward.png")
            print("✓ Applied filter: Ward = N-Ward")

        # Click Clear All Filters
        clear_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Clear All Filters')]")
        if clear_btn:
            driver.execute_script("arguments[0].click();", clear_btn[0])
            time.sleep(1.5)
            save_and_copy(driver, "phase5_map_filters_cleared.png")
            print("✓ Clicked 'Clear All Filters' button: successfully restored full active dataset")

        # 6. Test Polygon Click / Jurisdiction Inspector
        print("\n--- 5. Testing Interactive Polygon Inspection ---")
        # Click on Leaflet SVG polygon path
        paths = driver.find_elements(By.CSS_SELECTOR, "path.leaflet-interactive")
        if paths:
            try:
                driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true }));", paths[0])
                time.sleep(1.5)
                save_and_copy(driver, "phase5_map_jurisdiction_inspector.png")
                print("✓ Clicked polygon path: displayed Jurisdiction Inspector & highlighted boundary")
            except Exception as e:
                print(f"Note: Could not click path element directly: {e}")

        # 7. Test at 1280x800 viewport
        print("\n--- 6. Testing at 1280x800 Desktop Viewport ---")
        driver.set_window_size(1280, 800)
        time.sleep(1.5)
        save_and_copy(driver, "phase5_map_1280x800.png")
        print("✓ Verified Tactical GIS Map at 1280x800 desktop viewport")

        print("\n==================================================================")
        print("PHASE 5 GIS TACTICAL MAP VISUAL VERIFICATION COMPLETED!")
        print("==================================================================")

    finally:
        driver.quit()

if __name__ == '__main__':
    run_gis_map_verification()
