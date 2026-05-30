import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "./DemoFiles")).resolve()


def wait_for_download(download_dir: Path, timeout_seconds: int = 900) -> Path:
    end_time = time.time() + timeout_seconds

    while time.time() < end_time:
        candidates = [
            p for p in download_dir.iterdir()
            if p.is_file()
            and not p.name.startswith(".")
            and not p.name.endswith(".crdownload")
            and p.suffix.lower() in [".zip", ".rar", ".dem", ".7z"]
        ]

        partial_downloads = [
            p for p in download_dir.iterdir()
            if p.is_file()
            and (
                p.name.endswith(".crdownload")
                or p.name.startswith(".com.google.Chrome")
            )
        ]

        if candidates and not partial_downloads:
            newest = max(candidates, key=lambda p: p.stat().st_mtime)

            size_1 = newest.stat().st_size
            time.sleep(2)
            size_2 = newest.stat().st_size

            if size_1 == size_2 and size_2 > 0:
                return newest

        time.sleep(1)

    raise TimeoutError(f"No completed download found in {download_dir}")


def download_demo_zip(url: str) -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    chrome_options = Options()

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1365,768")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    

    prefs = {
        "download.default_directory": str(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }

    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        options=chrome_options,
    )

    try:
        print(f"Opening {url}")
        driver.get(url)

        downloaded_file = wait_for_download(DOWNLOAD_DIR)

        print(f"DOWNLOADED_FILE={downloaded_file}")
        return downloaded_file

    finally:
        driver.quit()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise ValueError("Usage: python download_demo_browser.py <hltv-demo-download-url>")

    download_demo_zip(sys.argv[1])