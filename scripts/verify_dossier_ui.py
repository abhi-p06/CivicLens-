import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def run_dossier_ui_verification():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 900)

    os.makedirs("scripts/verification_screenshots", exist_ok=True)

    try:
        driver.get('http://localhost:5173/')
        time.sleep(2)

        # Log in as Inspector / Municipal Staff
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        # Click on role or signin
        print("Page title:", driver.title)
        
        # Click Officer Sign In
        officer_btn = driver.find_element(By.XPATH, "//button[contains(., 'Officer Sign In')]")
        officer_btn.click()
        time.sleep(1)

        # Fill credentials if login form is present
        fill_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Fill demo account')]")
        if fill_btns:
            fill_btns[0].click()
            time.sleep(0.3)

        pwd_inputs = driver.find_elements(By.XPATH, "//input[@type='password']")
        if pwd_inputs:
            pwd_inputs[0].send_keys('Inspector@123')
            time.sleep(0.3)

        signin_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Sign In to Workspace')]")
        if signin_btns:
            signin_btns[0].click()
            time.sleep(2.5)

        print("Dashboard loaded. Looking for issues in queue...")
        # Screenshot the main dashboard
        driver.save_screenshot("scripts/verification_screenshots/dashboard_view.png")

        # Find the first incident card in the queue and click it via JS
        card = driver.find_element(By.CSS_SELECTOR, "[data-incident-id]")
        print("Clicking incident card:", card.get_attribute("data-incident-id"))
        driver.execute_script("arguments[0].click();", card)
        time.sleep(2)

        # Save screenshot of the Issue Detail Drawer
        driver.save_screenshot("scripts/verification_screenshots/dossier_verified.png")
        print("Saved screenshot to scripts/verification_screenshots/dossier_verified.png")

        # Extract text from drawer to verify elements
        body_text = driver.find_element(By.TAG_NAME, 'body').text
        assert "Verification locked:" in body_text, "Explanatory verification lock message missing from UI!"
        assert "Duplicate ()" not in body_text, "Empty Duplicate () string found in UI!"
        print("Visual elements verified successfully!")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_dossier_ui_verification()
