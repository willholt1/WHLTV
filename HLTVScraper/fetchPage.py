from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import undetected_chromedriver as uc

def fetchPage(url, className):
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = uc.Chrome(options=options)

    driver.get(url)

    from selenium.common.exceptions import NoSuchElementException

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
        print("Timeout waiting for event elements")
        with open("debug_hltv.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.quit()
        raise


    html = driver.page_source
    driver.quit()

    return BeautifulSoup(html, "html.parser")