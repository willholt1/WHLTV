import os
import psycopg2
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timezone
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


def fetch_ranking_page(url):
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
            EC.presence_of_element_located((By.CLASS_NAME, "small-event"))
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


def parse_rankings(soup):
    events = []

    for event in soup.select("a.small-event"):
        try:
            # Event URL
            link = event["href"]
            full_url = f"https://www.hltv.org{link}"

            # Event name
            name = event.select_one(".event-col .text-ellipsis").text.strip()

            # Prize pool
            prize_td = event.select_one(".prizePoolEllipsis")
            prize_pool = prize_td["title"].strip() if prize_td and prize_td.has_attr("title") else prize_td.text.strip()

            # Event type (Online, LAN, etc.)
            event_type = event.select_one("td.gtSmartphone-only")
            event_type = event_type.text.strip() if event_type else None

            # Start and end dates
            date_spans = event.select("tr.eventDetails span[data-unix]")

            start_date = datetime.fromtimestamp(int(date_spans[0]["data-unix"]) / 1000, tz=timezone.utc) if len(date_spans) >= 1 else None
            end_date = datetime.fromtimestamp(int(date_spans[1]["data-unix"]) / 1000, tz=timezone.utc) if len(date_spans) >= 2 else None
            
            # Location
            location_span = event.select_one("tr.eventDetails .col-desc")
            location = location_span.text.strip().split("|")[0] if location_span else None

            events.append((
                name,
                prize_pool,
                start_date,
                end_date,
                event_type,
                location,
                full_url
            ))


        except Exception as e:
            print(f"Skipping event due to error: {e}")
            continue

    return events


def update_database(events):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    for name, prize_pool, start_date, end_date, event_type, location, url in events:
        try:
            cur.execute("""
                CALL dbo.usp_InsertEvent(%s::TEXT, %s::TEXT, %s::TIMESTAMPTZ, %s::TIMESTAMPTZ,
                %s::TEXT, %s::TEXT, %s::TEXT)
                """, (
                    name,
                    prize_pool,
                    start_date,
                    end_date,
                    event_type,
                    location,
                    url
                ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Failed to insert event '{name}': {e}")
    
    cur.close()
    conn.close()


if __name__ == "__main__":
    print("Loading HLTV events with Selenium...")
    hltvSoup = fetch_ranking_page("https://www.hltv.org/events/archive")

    print("Parsing events...")
    events = parse_rankings(hltvSoup)

    print(f"Inserting {len(events)} teams into the database...")
    update_database(events)

    print("Done.")
