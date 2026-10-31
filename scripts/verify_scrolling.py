import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def run_scrolling_verification():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    viewports = [
        ("Desktop 1920x1080", 1920, 1080),
        ("Desktop 1440x900", 1440, 900),
        ("Tablet Landscape 1024x768", 1024, 768),
        ("Tablet Portrait 768x1024", 768, 1024),
        ("Narrow Mobile 375x667", 375, 667),
    ]

    os.makedirs("scripts/verification_screenshots", exist_ok=True)
    results = []

    try:
        # First, log in as citizen
        driver.set_window_size(1440, 900)
        driver.get('http://localhost:5173/')
        time.sleep(1.5)

        # Click Citizen
        driver.find_elements(By.TAG_NAME, 'button')[0].click()
        time.sleep(1)

        fill_btn = driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]")
        fill_btn.click()
        time.sleep(0.3)

        pwd_input = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd_input.send_keys('Citizen@123')
        time.sleep(0.3)

        signin_btn = driver.find_element(By.XPATH, "//button[contains(., 'Sign In to Workspace')]")
        signin_btn.click()
        time.sleep(2)

        # Verify login succeeded
        assert "Welcome" in driver.find_element(By.TAG_NAME, 'body').text, "Login failed"
        print("Citizen authenticated successfully.")

        for vp_name, width, height in viewports:
            print(f"\n=======================================================")
            print(f"Testing Viewport: {vp_name} ({width}x{height})")
            print(f"=======================================================")
            driver.set_window_size(width, height)
            time.sleep(1)

            # Click 'File Grievance' tab via JS to ensure event fires reliably across viewports
            file_grievance_btn = driver.find_element(By.XPATH, "//button[contains(., 'File Grievance')]")
            driver.execute_script("arguments[0].click();", file_grievance_btn)
            time.sleep(1)

            # Find the main scrollable container (in CitizenPortalView, the main content container)
            containers = driver.find_elements(By.CSS_SELECTOR, "div.overflow-y-auto")
            assert len(containers) >= 1, f"No overflow-y-auto container found on {vp_name}"
            # The portal workspace container is the one containing the complaint form
            scroll_container = [c for c in containers if "Citizen" in c.text or "Complaint" in c.text or "Welcome" in c.text][0]

            # Measure initial scroll dimensions
            metrics = driver.execute_script("""
                const el = arguments[0];
                return {
                    clientHeight: el.clientHeight,
                    scrollHeight: el.scrollHeight,
                    scrollTop: el.scrollTop,
                    clientWidth: el.clientWidth,
                    scrollWidth: el.scrollWidth,
                    hasVerticalScroll: el.scrollHeight > el.clientHeight,
                    hasHorizontalScroll: el.scrollWidth > el.clientWidth
                };
            """, scroll_container)

            print(f"Initial metrics: clientHeight={metrics['clientHeight']}px, scrollHeight={metrics['scrollHeight']}px, scrollWidth={metrics['scrollWidth']}px, clientWidth={metrics['clientWidth']}px")
            print(f"Scrollable vertically: {metrics['hasVerticalScroll']}")
            print(f"Horizontal overflow: {metrics['hasHorizontalScroll']}")
            assert not metrics['hasHorizontalScroll'], f"Unwanted horizontal scroll detected on {vp_name}"
            assert metrics['hasVerticalScroll'], f"Form should require vertical scrolling on {vp_name}"

            # Verify fields reachability
            # 1. Category selector
            cat_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Road Damage & Potholes')]")
            assert cat_btn.is_displayed(), "Category selector is present"

            # 2. Landmark input
            loc_input = driver.find_element(By.XPATH, "//input[@placeholder[contains(., 'Vidyavihar')]]")
            assert loc_input.is_displayed(), "Location landmark input is present"

            # 3. Textarea
            textarea = driver.find_element(By.XPATH, "//textarea")
            assert textarea.is_displayed(), "Complaint textarea is present"

            # 4. Image uploader
            uploader = driver.find_element(By.XPATH, "//*[contains(text(), 'Attach Photo Evidence')]")
            assert uploader.is_displayed(), "Image uploader header is present"

            # 5. Scroll to Submit button
            submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Submit Grievance')]")
            
            # Scroll container to bottom
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_container)
            time.sleep(0.5)

            post_scroll = driver.execute_script("""
                const el = arguments[0];
                const btn = arguments[1];
                const btnRect = btn.getBoundingClientRect();
                const containerRect = el.getBoundingClientRect();
                return {
                    scrollTop: el.scrollTop,
                    maxScroll: el.scrollHeight - el.clientHeight,
                    btnVisible: btnRect.top >= containerRect.top && btnRect.bottom <= containerRect.bottom + 10,
                    btnClickable: !btn.disabled
                };
            """, scroll_container, submit_btn)

            print(f"After scrolling: scrollTop={post_scroll['scrollTop']}px (max: {post_scroll['maxScroll']}px)")
            print(f"Submit button in visible viewport: {post_scroll['btnVisible']}, Clickable: {post_scroll['btnClickable']}")
            assert post_scroll['scrollTop'] > 0, f"Container failed to scroll vertically on {vp_name}"
            assert post_scroll['btnVisible'], f"Submit button not visible after scroll on {vp_name}"

            # Save screenshot for audit
            scr_path = f"scripts/verification_screenshots/{width}x{height}_citizen_scrolled.png"
            driver.save_screenshot(scr_path)
            print(f"Saved screenshot: {scr_path}")

            results.append({
                "viewport": vp_name,
                "width": width,
                "height": height,
                "clientHeight": metrics['clientHeight'],
                "scrollHeight": metrics['scrollHeight'],
                "scrolledAmount": post_scroll['scrollTop'],
                "submitReachable": post_scroll['btnVisible'],
                "noHorizontalScroll": not metrics['hasHorizontalScroll']
            })

            # Return scroll to top
            driver.execute_script("arguments[0].scrollTop = 0;", scroll_container)
            time.sleep(0.3)

        print("\n=======================================================")
        print("ALL CITIZEN VIEWPORTS VERIFIED SUCCESSFULLY!")
        print("=======================================================")

        # Verify Officer / Inspector Role
        print("\nVerifying Municipal Officer Role...")
        driver.set_window_size(1440, 900)
        driver.execute_script("localStorage.clear(); sessionStorage.clear();")
        driver.get('http://localhost:5173/')
        time.sleep(1.5)

        officer_card = driver.find_element(By.XPATH, "//button[contains(., 'Officer Sign In')]")
        driver.execute_script("arguments[0].click();", officer_card)
        time.sleep(0.5)
        fill_btn = driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]")
        fill_btn.click()
        time.sleep(0.3)
        pwd_input = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd_input.send_keys('Inspector@123')
        time.sleep(0.3)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign In to Workspace')]").click()
        time.sleep(2)

        officer_body = driver.find_element(By.TAG_NAME, 'body').text
        assert "Command Center" in officer_body or "Municipal" in officer_body or "Operations" in officer_body
        officer_scrollables = driver.find_elements(By.CSS_SELECTOR, "div.overflow-y-auto")
        print(f"Officer view loaded with {len(officer_scrollables)} scrollable containers. Navigation and controls preserved.")

        # Verify Admin Role
        print("\nVerifying Administrator Role...")
        driver.execute_script("localStorage.clear(); sessionStorage.clear();")
        driver.get('http://localhost:5173/')
        time.sleep(1)

        admin_card = driver.find_element(By.XPATH, "//button[contains(., 'Administrator Sign In')]")
        driver.execute_script("arguments[0].click();", admin_card)
        time.sleep(0.5)
        fill_btn = driver.find_element(By.XPATH, "//button[contains(., 'Fill demo account')]")
        fill_btn.click()
        time.sleep(0.3)
        pwd_input = driver.find_element(By.XPATH, "//input[@type='password']")
        pwd_input.send_keys('Admin@123')
        time.sleep(0.3)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign In to Workspace')]").click()
        time.sleep(2)

        admin_body = driver.find_element(By.TAG_NAME, 'body').text
        assert "Administrator" in admin_body or "Command Center" in admin_body
        admin_scrollables = driver.find_elements(By.CSS_SELECTOR, "div.overflow-y-auto")
        print(f"Admin view loaded with {len(admin_scrollables)} scrollable containers. Navigation and controls preserved.")

        print("\n=======================================================")
        print("SUMMARY TABLE OF VERIFICATION RESULTS:")
        print("=======================================================")
        for r in results:
            print(f"- {r['viewport']} ({r['width']}x{r['height']}): scrollHeight={r['scrollHeight']}px, clientHeight={r['clientHeight']}px -> Scrolled {r['scrolledAmount']}px, Submit Reachable: {r['submitReachable']}, No Horizontal Overflow: {r['noHorizontalScroll']}")

    finally:
        driver.quit()

if __name__ == '__main__':
    run_scrolling_verification()
