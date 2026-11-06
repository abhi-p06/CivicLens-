import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
driver = webdriver.Chrome(options=options)
driver.set_window_size(1600, 900)

try:
    driver.get("http://localhost:5173/login/citizen")
    time.sleep(1)
    driver.execute_script("localStorage.clear(); sessionStorage.clear();")
    driver.get("http://localhost:5173/login/citizen")
    time.sleep(2)

    fill_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Fill demo account')]")
    if fill_btn:
        fill_btn[0].click()
        time.sleep(0.5)

    pwd = driver.find_element(By.XPATH, "//input[@type='password']")
    pwd.clear()
    pwd.send_keys("Citizen@123")
    time.sleep(0.5)

    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(3)

    driver.get("http://localhost:5173/#citizen_portal")
    time.sleep(2)

    print("Initial Body Text:")
    print(driver.find_element(By.TAG_NAME, "body").text[:500])

    # Find buttons
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print("\nButtons on page:")
    for b in buttons:
        print("BUTTON:", repr(b.text))

    file_btn = [b for b in buttons if "File Grievance" in b.text or "File your first complaint" in b.text]
    if file_btn:
        print("\nClicking:", file_btn[0].text)
        file_btn[0].click()
        time.sleep(2)

    print("\nBody Text after clicking:")
    print(driver.find_element(By.TAG_NAME, "body").text[:800])
finally:
    driver.quit()

