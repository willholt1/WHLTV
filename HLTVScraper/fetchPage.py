from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import logging
import random

def randomWait(min_seconds=20, max_seconds=40):
    delay = random.uniform(min_seconds, max_seconds)
    print(f"Waiting {delay:.1f} seconds...")
    time.sleep(delay)

def createDriver():
    print("Setting up Selenium driver...")
    options = Options()

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1365,768")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Create driver with increased command timeouts
    from selenium.webdriver.chrome.service import Service
    service = Service()
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Set longer timeouts
    driver.set_page_load_timeout(120)  # 2 minutes for page loads
    driver.implicitly_wait(10)  # Wait up to 10 seconds for elements
    
    print("Chrome driver initialized successfully")
    return driver

def fetchPage(url, className, driver=None):
    if driver is None:
        driver = createDriver()

    print(f"Loading {url} with Selenium...")
    driver.get(url)

    randomWait()

    print("Page loaded, checking for cookie popup...")

    try:
        # Wait a bit in case the popup needs a moment
        time.sleep(1)
        accept_button = driver.find_element(By.CLASS_NAME, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
        accept_button.click()
        print("Cookie popup accepted.")
        time.sleep(1)  # Give it a moment to apply
    except NoSuchElementException:
        print("No cookie popup found.")

    # Wait for at least one .ranked-team element to be visible
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, className))
        )
    except Exception as e:
        logging.warning(f"Class '{className}' not found on {url}: {e}")
        print(f"WARNING: Could not find '{className}' on page. Possible Cloudflare block.")
        with open("debug_hltv.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Page source saved to debug_hltv.html for inspection.")
        return None

    html = driver.page_source
    driver.quit()
    
    return BeautifulSoup(html, "html.parser")