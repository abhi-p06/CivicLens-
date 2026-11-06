import time
import os
import shutil
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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

def login_user(driver, role='citizen', email='citizen@civilens.org', password='Citizen@123'):
    target_url = f"http://localhost:5173/login/{role}"
    driver.get(target_url)
    time.sleep(1)
    driver.execute_script("localStorage.clear(); sessionStorage.clear();")
    driver.get(target_url)
    time.sleep(2)

    fill_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Fill demo account')]")
    if fill_btn:
        fill_btn[0].click()
        time.sleep(0.5)

    pwd = driver.find_element(By.XPATH, "//input[@type='password']")
    pwd.clear()
    pwd.send_keys(password)
    time.sleep(0.5)

    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(3)
    print(f"✓ Logged in as {role} ({email})")

if __name__ == "__main__":
    driver = get_driver()
    try:
        login_user(driver, 'citizen')
        save_and_copy(driver, "test_citizen_home.png")
        print("Page title:", driver.title)
    finally:
        driver.quit()
