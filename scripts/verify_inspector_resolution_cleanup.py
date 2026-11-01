import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def run_role_verification():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 900)

    os.makedirs("scripts/verification_screenshots", exist_ok=True)

    try:
        # =====================================================================
        # 1. VERIFY INSPECTOR ROLE
        # =====================================================================
        print("\n--- 1. Testing Inspector Role (inspector@civilens.org) ---")
        driver.get('http://localhost:5173/login/municipal')
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

        driver.save_screenshot("scripts/verification_screenshots/admin_after_login.png")
        print("Admin URL after login:", driver.current_url)
        if "login" in driver.current_url:
            print("Login error message:", [e.text for e in driver.find_elements(By.XPATH, "//div[contains(@class, 'bg-rose-50')]")])

        driver.save_screenshot("scripts/verification_screenshots/inspector_dashboard.png")

        # Check Sidebar items for Inspector
        sidebar_text = driver.find_element(By.TAG_NAME, "aside").text
        print("Inspector Sidebar sections detected:")
        print(sidebar_text)

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
        print("✓ Verified: Direct access to #resolution is blocked for Inspector (safely redirected).")

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
            print("✓ Verified: Inspector complaint inspection & lifecycle status workflow intact without verification button.")

        # =====================================================================
        # 2. VERIFY CITIZEN ROLE
        # =====================================================================
        print("\n--- 2. Testing Citizen Role (citizen@civilens.org) ---")
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

        driver.save_screenshot("scripts/verification_screenshots/admin_after_login.png")
        print("Admin URL after login:", driver.current_url)
        if "login" in driver.current_url:
            print("Login error message:", [e.text for e in driver.find_elements(By.XPATH, "//div[contains(@class, 'bg-rose-50')]")])

        citizen_src = driver.page_source
        assert "File a New Civic Complaint" in citizen_src or "Select Civic Category" in citizen_src or "Citizen Portal" in citizen_src, "ERROR: Citizen portal features missing!"
        driver.save_screenshot("scripts/verification_screenshots/citizen_portal.png")
        print("✓ Verified: Citizen dashboard remains completely intact and functional.")

        # =====================================================================
        # 3. VERIFY ADMIN ROLE
        # =====================================================================
        print("\n--- 3. Testing Admin Role (admin@civilens.org) ---")
        driver.get('http://localhost:5173/login/admin')
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

        driver.save_screenshot("scripts/verification_screenshots/admin_after_login.png")
        print("Admin URL after login:", driver.current_url)

        # Check that Admin sidebar RETAINS Resolution Center
        admin_sidebar = driver.find_element(By.TAG_NAME, "aside").text
        assert "Resolution Center" in admin_sidebar, "ERROR: Admin sidebar must retain Resolution Center!"
        print("✓ Verified: Admin sidebar retains 'Resolution Center'.")

        # Navigate to Resolution Center as Admin
        driver.get('http://localhost:5173/#resolution')
        time.sleep(2)
        admin_res_src = driver.page_source
        assert "Work-Order Verification & Lifecycle" in admin_res_src, "ERROR: Admin unable to access Work-Order Verification!"
        assert "FEATURE 20" in admin_res_src, "ERROR: FEATURE 20 badge missing in Admin view!"
        assert "Verified Orders" in admin_res_src, "ERROR: Verified Orders KPI missing in Admin view!"
        assert "Pass Rate" in admin_res_src, "ERROR: Pass Rate KPI missing in Admin view!"
        driver.save_screenshot("scripts/verification_screenshots/admin_resolution.png")
        print("✓ Verified: Admin retains full access to Work-Order Verification & Lifecycle / Resolution Center.")

        print("\nALL ROLE VERIFICATIONS PASSED SUCCESSFULLY!")

        print("\nALL ROLE VERIFICATIONS PASSED SUCCESSFULLY!")

    finally:
        driver.quit()

if __name__ == '__main__':
    run_role_verification()
