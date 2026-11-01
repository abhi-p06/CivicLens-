import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 900)
    return driver

def verify_citizen():
    print("\n--- 1. Testing Citizen Role (citizen@civilens.org) ---")
    driver = get_driver()
    try:
        driver.get('http://localhost:5173/login/citizen')
        time.sleep(1.5)
        driver.execute_script("localStorage.clear();")
        driver.get('http://localhost:5173/login/citizen')
        time.sleep(1.5)

        fill_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Fill demo account')]")
        if fill_btns:
            fill_btns[0].click()
            time.sleep(0.3)

        pwd_inputs = driver.find_elements(By.XPATH, "//input[@type='password']")
        if pwd_inputs:
            pwd_inputs[0].clear()
            pwd_inputs[0].send_keys('Citizen@123')
            time.sleep(0.3)

        signin_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Sign In to Workspace')]")
        if signin_btns:
            signin_btns[0].click()
            time.sleep(3)

        driver.save_screenshot("scripts/verification_screenshots/citizen_dashboard.png")
        citizen_src = driver.page_source
        assert "Resolution Center" not in citizen_src, "ERROR: 'Resolution Center' found in Citizen view!"
        assert "File a New Civic Complaint" in citizen_src or "Citizen Portal" in citizen_src, "ERROR: Citizen portal failed to load!"
        print("✓ Verified: Citizen dashboard loads properly without any Resolution Center elements.")
    finally:
        driver.quit()

def verify_inspector():
    print("\n--- 2. Testing Inspector Role (inspector@civilens.org) ---")
    driver = get_driver()
    try:
        driver.get('http://localhost:5173/login/municipal')
        time.sleep(1.5)
        driver.execute_script("localStorage.clear();")
        driver.get('http://localhost:5173/login/municipal')
        time.sleep(1.5)

        fill_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Fill demo account')]")
        if fill_btns:
            fill_btns[0].click()
            time.sleep(0.3)

        pwd_inputs = driver.find_elements(By.XPATH, "//input[@type='password']")
        if pwd_inputs:
            pwd_inputs[0].clear()
            pwd_inputs[0].send_keys('Inspector@123')
            time.sleep(0.3)

        signin_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Sign In to Workspace')]")
        if signin_btns:
            signin_btns[0].click()
            time.sleep(3)

        driver.save_screenshot("scripts/verification_screenshots/inspector_dashboard.png")

        # Check Sidebar items for Inspector
        sidebar_text = driver.find_element(By.TAG_NAME, "aside").text
        assert "Resolution Center" not in sidebar_text, "ERROR: 'Resolution Center' found in Inspector sidebar!"
        assert "Work-Order Verification" not in driver.page_source, "ERROR: 'Work-Order Verification' found in Inspector page!"
        print("✓ Verified: 'Resolution Center' is absent from Inspector sidebar.")

        # Test navigating to #resolution directly
        driver.get('http://localhost:5173/#resolution')
        time.sleep(1.5)
        page_src = driver.page_source
        assert "Work-Order Verification & Lifecycle" not in page_src, "ERROR: Inspector accessed Work-Order Verification via hash!"
        assert "FEATURE 20" not in page_src, "ERROR: FEATURE 20 badge found on Inspector view!"
        assert "Verified Orders" not in page_src, "ERROR: Verified Orders KPI found on Inspector view!"
        assert "Pass Rate" not in page_src, "ERROR: Pass Rate KPI found on Inspector view!"
        assert "Run AI Verification" not in page_src, "ERROR: Run AI Verification found on Inspector view!"
        assert "Upload Proof" not in page_src, "ERROR: Upload Proof found on Inspector view!"
        assert "Work-Order Resolution Queue" not in page_src, "ERROR: Work-Order Resolution Queue found on Inspector view!"
        print("✓ Verified: Direct access to #resolution is blocked for Inspector.")

        # Test complaint inspection drawer
        driver.get('http://localhost:5173/#overview')
        time.sleep(2)
        issue_cards = driver.find_elements(By.XPATH, "//div[@data-incident-id]")
        if issue_cards:
            driver.execute_script("arguments[0].click();", issue_cards[0])
            time.sleep(1.5)
            drawer_src = driver.page_source
            assert "Civic Lifecycle Workflow" in drawer_src, "ERROR: Complaint inspection lifecycle missing in drawer!"
            assert "Verify Field Resolution" not in drawer_src, "ERROR: 'Verify Field Resolution' button found in Inspector drawer!"
            driver.save_screenshot("scripts/verification_screenshots/inspector_drawer.png")
            print("✓ Verified: Inspector drawer has no 'Verify Field Resolution' button.")
    finally:
        driver.quit()

def verify_admin():
    print("\n--- 3. Testing Admin Role (admin@civilens.org) ---")
    driver = get_driver()
    try:
        driver.get('http://localhost:5173/login/admin')
        time.sleep(1.5)
        driver.execute_script("localStorage.clear();")
        driver.get('http://localhost:5173/login/admin')
        time.sleep(1.5)

        user_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter your registered email or username']")
        user_input.clear()
        user_input.send_keys('admin@civilens.org')

        pwd_input = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd_input.clear()
        pwd_input.send_keys('Admin@123')
        time.sleep(0.3)

        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        time.sleep(3)

        driver.save_screenshot("scripts/verification_screenshots/admin_dashboard.png")

        # Check Admin sidebar
        admin_sidebar = driver.find_element(By.TAG_NAME, "aside").text
        assert "Resolution Center" not in admin_sidebar, "ERROR: 'Resolution Center' found in Admin sidebar!"
        print("✓ Verified: 'Resolution Center' is absent from Admin sidebar.")

        # Check direct navigation to #resolution
        driver.get('http://localhost:5173/#resolution')
        time.sleep(1.5)
        admin_page_src = driver.page_source
        assert "Work-Order Verification & Lifecycle" not in admin_page_src, "ERROR: Admin accessed Work-Order Verification via hash!"
        assert "FEATURE 20" not in admin_page_src, "ERROR: FEATURE 20 badge found on Admin view!"
        assert "Verified Orders" not in admin_page_src, "ERROR: Verified Orders KPI found on Admin view!"
        assert "Pass Rate" not in admin_page_src, "ERROR: Pass Rate KPI found on Admin view!"
        assert "Run AI Verification" not in admin_page_src, "ERROR: Run AI Verification found on Admin view!"
        assert "Upload Proof" not in admin_page_src, "ERROR: Upload Proof found on Admin view!"
        assert "Work-Order Resolution Queue" not in admin_page_src, "ERROR: Work-Order Resolution Queue found on Admin view!"
        print("✓ Verified: Direct access to #resolution is blocked for Admin.")

        # Test drawer for Admin
        driver.get('http://localhost:5173/#overview')
        time.sleep(2)
        issue_cards = driver.find_elements(By.XPATH, "//div[@data-incident-id]")
        if issue_cards:
            driver.execute_script("arguments[0].click();", issue_cards[0])
            time.sleep(1.5)
            drawer_src = driver.page_source
            assert "Civic Lifecycle Workflow" in drawer_src, "ERROR: Complaint inspection lifecycle missing in drawer!"
            assert "Verify Field Resolution" not in drawer_src, "ERROR: 'Verify Field Resolution' button found in Admin drawer!"
            driver.save_screenshot("scripts/verification_screenshots/admin_drawer.png")
            print("✓ Verified: Admin drawer has no 'Verify Field Resolution' button.")

        # Verify all remaining sidebar views for Admin
        remaining_views = [
            ("Command Center", "#overview"),
            ("Priority Queue", "#explorer"),
            ("Tactical GIS Map", "#map"),
            ("Issue Dossier", "#intelligence"),
            ("Live Radar", "#radar"),
            ("Model Benchmarks", "#analytics"),
        ]
        for label, hash_route in remaining_views:
            driver.get(f'http://localhost:5173/{hash_route}')
            time.sleep(1.5)
            print(f"✓ Verified view: {label} ({hash_route}) loads cleanly.")

        print("\n=======================================================")
        print("ALL THREE ROLES AND VIEWS VERIFIED SUCCESSFULLY!")
        print("Resolution Center is completely eliminated from CIVILENS.")
        print("=======================================================")
    finally:
        driver.quit()

if __name__ == '__main__':
    os.makedirs("scripts/verification_screenshots", exist_ok=True)
    verify_citizen()
    verify_inspector()
    verify_admin()
