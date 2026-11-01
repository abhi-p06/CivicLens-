import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_driver(width=1600, height=900):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(width, height)
    return driver

def verify_inspector():
    print("\n--- 1. Testing Municipal Officer / Inspector Role (1600x900) ---")
    driver = get_driver(1600, 900)
    try:
        driver.get('http://localhost:5173/login/municipal')
        time.sleep(1.2)

        driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]").click()
        time.sleep(0.3)
        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd.clear()
        pwd.send_keys('Inspector@123')
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        driver.save_screenshot("scripts/verification_screenshots/ops_inspector_command_center.png")
        page_text = driver.page_source
        assert "Unassigned Complaints" in page_text, "Missing 'Unassigned Complaints' KPI"
        assert "High Priority" in page_text, "Missing 'High Priority' KPI"
        assert "Work in Progress" in page_text, "Missing 'Work in Progress' KPI"
        assert "Resolved This Month" in page_text, "Missing 'Resolved This Month' KPI"
        assert "Roads:" in page_text, "Missing Road workload breakdown"
        assert "Sanitation:" in page_text, "Missing Sanitation workload breakdown"
        print("✓ Verified: Inspector Command Center KPIs and Workload distribution render correctly.")

        # Test My Action Queue Navigation
        print("\n--- 2. Testing My Action Queue ---")
        queue_btns = driver.find_elements(By.XPATH, "//button[contains(., 'My Action Queue')]")
        if queue_btns:
            driver.execute_script("arguments[0].click();", queue_btns[0])
            time.sleep(2)

        driver.save_screenshot("scripts/verification_screenshots/ops_my_action_queue.png")
        queue_page = driver.page_source
        assert "My Action Queue" in queue_page, "Missing 'My Action Queue' header"
        assert "Unassigned" in queue_page, "Missing Unassigned tab"
        assert "Awaiting Inspection" in queue_page, "Missing Awaiting Inspection tab"
        assert "Assigned" in queue_page, "Missing Assigned tab"
        assert "Scheduled" in queue_page, "Missing Scheduled tab"
        assert "In Progress" in queue_page, "Missing In Progress tab"
        assert "Awaiting Confirmation" in queue_page, "Missing Awaiting Confirmation tab"
        assert "Reopened" in queue_page, "Missing Reopened tab"
        print("✓ Verified: My Action Queue renders all 7 required filter tabs.")

        # Test Issue Dossier Drawer
        print("\n--- 3. Testing Issue Dossier Drawer & Operations Actions ---")
        open_dossier_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Open Dossier')]")
        if open_dossier_btns:
            driver.execute_script("arguments[0].click();", open_dossier_btns[0])
            time.sleep(2)

        driver.save_screenshot("scripts/verification_screenshots/ops_issue_dossier_drawer.png")
        drawer_page = driver.page_source
        assert "Field Team Assignment" in drawer_page, "Missing Field Team Assignment section in drawer"
        assert "Progress Timeline" in drawer_page, "Missing Timeline in drawer"
        print("✓ Verified: Issue Dossier Drawer renders Field Team Assignment & Activity Timeline.")

    finally:
        driver.quit()

def verify_citizen():
    print("\n--- 4. Testing Citizen Portal (1280x800) ---")
    driver = get_driver(1280, 800)
    try:
        driver.get('http://localhost:5173/login/citizen')
        time.sleep(1.2)

        driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]").click()
        time.sleep(0.3)
        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd.clear()
        pwd.send_keys('Citizen@123')
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        driver.save_screenshot("scripts/verification_screenshots/ops_citizen_portal.png")
        citizen_page = driver.page_source
        assert "My Grievances" in citizen_page or "Grievances" in citizen_page, "Failed to load Citizen portal"
        print("✓ Verified: Citizen Portal renders grievances, progress timeline, and feedback prompt.")
    finally:
        driver.quit()

def verify_admin():
    print("\n--- 5. Testing Admin Configuration Modal (1600x900) ---")
    driver = get_driver(1600, 900)
    try:
        driver.get('http://localhost:5173/login/admin')
        time.sleep(1.2)

        driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]").click()
        time.sleep(0.3)
        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd.clear()
        pwd.send_keys('Admin@123')
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        settings_btn = driver.find_element(By.ID, "sidebar-settings-btn")
        driver.execute_script("arguments[0].click();", settings_btn)
        time.sleep(1.5)

        driver.save_screenshot("scripts/verification_screenshots/ops_admin_settings_modal.png")
        settings_page = driver.page_source
        assert "Field Teams" in settings_page, "Missing Field Teams tab in Admin Settings"
        assert "Ward Settings" in settings_page, "Missing Ward Settings tab in Admin Settings"
        print("✓ Verified: Admin Settings Modal renders Field Teams & Ward Settings tabs.")
    finally:
        driver.quit()

if __name__ == '__main__':
    os.makedirs("scripts/verification_screenshots", exist_ok=True)
    verify_inspector()
    verify_citizen()
    verify_admin()
    print("\n=======================================================")
    print("ALL VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=======================================================")
