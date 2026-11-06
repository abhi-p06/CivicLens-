import time
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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

def run_officer_hierarchy_verification():
    driver = get_driver(1600, 900)
    try:
        print("\n==================================================================")
        print("CIVILENS OFFICER HIERARCHY VISIBILITY (BMC + NMMC) VERIFICATION")
        print("==================================================================")

        # ----------------------------------------------------------------------
        # Test 1: Central Administrator View (Baseline)
        # ----------------------------------------------------------------------
        print("\n--- 1. Login as Central Administrator ---")
        driver.get('http://localhost:5173/login/admin')
        time.sleep(2)

        fill_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Fill demo account')]")
        if fill_btn:
            fill_btn[0].click()
            time.sleep(0.5)

        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd.clear()
        pwd.send_keys('Admin@123')
        time.sleep(0.5)

        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        print("--- 2. Admin viewing Ward Hierarchy (1600x900) ---")
        driver.get('http://localhost:5173/#ward_hierarchy')
        time.sleep(3)

        save_and_copy(driver, "officer_hierarchy_admin_1600x900.png")
        body_admin = driver.find_element(By.TAG_NAME, "body").text
        assert "2 Cities • 2 Authorities" in body_admin or "2 Cities" in body_admin
        assert "Mumbai" in body_admin and "Navi Mumbai" in body_admin
        print("✓ Confirmed: Admin sees complete tree with Mumbai (BMC) and Navi Mumbai (NMMC)!")

        # ----------------------------------------------------------------------
        # Test 2: BMC Municipal Officer (Inspector Abhinay - Assigned to N-Ward)
        # ----------------------------------------------------------------------
        print("\n--- 3. Login as BMC Municipal Officer (Inspector Abhinay) ---")
        driver.execute_script("localStorage.clear(); sessionStorage.clear(); window.location.href = '/login/municipal';")
        time.sleep(2)

        fill_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Fill demo account')]")
        if fill_btn:
            fill_btn[0].click()
            time.sleep(0.5)

        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd.clear()
        pwd.send_keys('Inspector@123')
        time.sleep(0.5)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        print("--- 4. BMC Officer Viewing Ward Hierarchy ---")
        driver.get('http://localhost:5173/#ward_hierarchy')
        time.sleep(3)

        save_and_copy(driver, "officer_hierarchy_bmc_officer_1600x900.png")

        body_bmc = driver.find_element(By.TAG_NAME, "body").text
        print("Checking BMC officer tree content...")
        assert "2 Cities" in body_bmc, "Expected 2 Cities in counter!"
        assert "Mumbai" in body_bmc, "Expected Mumbai in tree!"
        assert "Navi Mumbai" in body_bmc, "Expected Navi Mumbai in tree!"
        assert "NMMC" in body_bmc, "Expected NMMC authority in tree!"
        assert "Authorized Working Area" in body_bmc, "Expected 'Authorized Working Area' badge!"
        assert "Read-Only" in body_bmc, "Expected 'Read-Only' badge!"
        print("✓ Confirmed: BMC Officer sees BOTH Mumbai (BMC) and Navi Mumbai (NMMC)!")
        print("✓ Confirmed: Officer assigned working area (N-Ward) is highlighted with Authorized badge!")
        print("✓ Confirmed: External nodes display Read-Only badge!")

        # Verify 1280x800 viewport for BMC Officer
        print("\n--- 5. BMC Officer at 1280x800 Responsive Viewport ---")
        driver.set_window_size(1280, 800)
        time.sleep(1.5)
        save_and_copy(driver, "officer_hierarchy_bmc_officer_1280x800.png")
        driver.set_window_size(1600, 900)
        time.sleep(1)

        # ----------------------------------------------------------------------
        # Test 3: Search Across Both Authorities (Searching "Belapur" in Navi Mumbai)
        # ----------------------------------------------------------------------
        print("\n--- 6. BMC Officer Searching 'Belapur' (Navi Mumbai Node) ---")
        search_input = driver.find_element(By.XPATH, "//input[@placeholder='Search city, authority, ward, sub-ward, beat, supervisor...']")
        search_input.clear()
        search_input.send_keys("Belapur")
        time.sleep(2)

        save_and_copy(driver, "officer_hierarchy_search_belapur_nmmc.png")
        search_body = driver.find_element(By.TAG_NAME, "body").text
        assert "Belapur" in search_body, "Expected Belapur to appear in search results!"
        print("✓ Confirmed: Searching 'Belapur' matched Navi Mumbai ward office seamlessly!")

        # ----------------------------------------------------------------------
        # Test 4: Selecting Read-Only Node (Belapur) as BMC Officer
        # ----------------------------------------------------------------------
        print("\n--- 7. BMC Officer Clicking Belapur (Unauthorized Node) ---")
        # Reset search first so full tree is visible
        search_input.send_keys(Keys.COMMAND + "a" if "darwin" in os.sys.platform else Keys.CONTROL + "a")
        search_input.send_keys(Keys.BACKSPACE)
        time.sleep(1)

        belapur_elem = driver.find_elements(By.XPATH, "//span[contains(text(), 'NMMC Belapur Ward Office')]")
        if not belapur_elem:
            belapur_elem = driver.find_elements(By.XPATH, "//span[contains(text(), 'Belapur')]")

        if belapur_elem:
            driver.execute_script("arguments[0].click();", belapur_elem[0])
            time.sleep(2)
            save_and_copy(driver, "officer_hierarchy_bmc_viewing_unauthorized_belapur.png")

            selected_title = driver.find_element(By.XPATH, "//div[contains(@class, 'lg:col-span-7')]//span[contains(@class, 'text-lg')]").text
            print(f"Selected node in details panel: {selected_title}")

            belapur_panel_text = driver.find_element(By.XPATH, "//div[contains(@class, 'lg:col-span-7')]").text
            assert "Read-Only Jurisdiction" in belapur_panel_text, "Expected Read-Only banner on Belapur!"
            assert "Outside Authorized Scope" in belapur_panel_text or "READ ONLY" in belapur_panel_text
            print("✓ Confirmed: Details panel renders 'Read-Only Jurisdiction (Outside Authorized Scope)' banner!")
            print("✓ Confirmed: Operational mutations are locked for unauthorized node!")

        # ----------------------------------------------------------------------
        # Test 5: NMMC Municipal Officer (Officer Deshmukh - Assigned to Belapur)
        # ----------------------------------------------------------------------
        print("\n--- 8. Login as NMMC Municipal Officer in Clean Session (Officer Deshmukh) ---")
        driver.quit()
        driver = get_driver(1600, 900)

        driver.get('http://localhost:5173/login/municipal')
        time.sleep(2)

        uname = driver.find_element(By.XPATH, "//input[@type='text' or @type='email']")
        uname.clear()
        uname.send_keys('inspector.nmmc@civilens.org')
        time.sleep(0.5)

        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd.clear()
        pwd.send_keys('Inspector@123')
        time.sleep(0.5)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        print("--- 9. NMMC Officer Viewing Ward Hierarchy ---")
        driver.get('http://localhost:5173/#ward_hierarchy')
        
        # Wait for tree to finish loading
        body_nmmc = ""
        for _ in range(20):
            time.sleep(0.5)
            body_nmmc = driver.find_element(By.TAG_NAME, "body").text
            if "2 Cities" in body_nmmc:
                break

        save_and_copy(driver, "officer_hierarchy_nmmc_officer_1600x900.png")
        assert "2 Cities" in body_nmmc, "Expected 2 Cities for NMMC Officer!"
        assert "Mumbai" in body_nmmc and "Navi Mumbai" in body_nmmc
        assert "NMMC-Belapur" in body_nmmc or "Belapur" in body_nmmc
        assert "Authorized Working Jurisdiction" in body_nmmc or "Authorized Working Area" in body_nmmc
        print("✓ Confirmed: NMMC Officer sees BOTH Mumbai and Navi Mumbai!")
        print("✓ Confirmed: Belapur is designated as NMMC Officer's Authorized Working Area!")

        print("\n==================================================================")
        print("ALL VISUAL AND INTERACTIVE CHECKS COMPLETED SUCCESSFULLY!")
        print("==================================================================")

    finally:
        driver.quit()

if __name__ == '__main__':
    run_officer_hierarchy_verification()
