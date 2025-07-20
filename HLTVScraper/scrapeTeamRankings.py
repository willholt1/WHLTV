import os
import psycopg2
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import undetected_chromedriver as uc
from dotenv import load_dotenv
load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432")
}



def fetch_ranking_page():
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = uc.Chrome(options=options)

    driver.get("https://www.hltv.org/ranking/teams")

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
            EC.presence_of_element_located((By.CLASS_NAME, "ranked-team"))
        )
    except Exception as e:
        print("Timeout waiting for ranked-team elements")
        with open("debug_hltv.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.quit()
        raise


    html = driver.page_source
    driver.quit()

    return BeautifulSoup(html, "html.parser")


def parse_rankings(soup):
    teams = []
    for team_div in soup.select('.ranked-team'):
        try:
            rank = int(team_div.select_one('.position').text.strip('#'))
            name = team_div.select_one('.name').text.strip()

            points_text = team_div.select_one('.points').text
            points = int(''.join(filter(str.isdigit, points_text)))

            teams.append((name, rank, points))
        except Exception as e:
            print(f"Skipping team due to parse error: {e}")
            continue
    return teams


def update_database(teams):

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    for name, rank, points in teams:
        cur.execute("""
            CALL dbo.InsertTeamRanking(%s, %s, %s, %s, %s, %s)
        """, (name, points, rank, None, None, None))

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    print("Loading HLTV rankings with Selenium...")
    soup = fetch_ranking_page()

    print("Parsing rankings...")
    teams = parse_rankings(soup)

    print(f"Inserting {len(teams)} teams into the database...")
    update_database(teams)

    print("Done.")
