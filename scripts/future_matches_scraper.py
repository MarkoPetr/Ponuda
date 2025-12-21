from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days&sort=bytime"
OUTPUT_DIR = "output"
EXCEL_FILE = os.path.join(OUTPUT_DIR, "future_matches.xlsx")

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

def human_sleep(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def scrape_future_matches():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=MOBILE_UA,
            viewport={"width": 412, "height": 915},
            locale="sr-RS"
        )
        page = context.new_page()
        page.goto(URL, timeout=60000)
        time.sleep(random.uniform(5, 8))

        # zatvori kolačiće ako postoji popup
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1, 2)
        except:
            pass

        # Scroll + click "Učitaj još"
        while True:
            try:
                scroll_height = random.randint(400, 700)
                page.evaluate(f"window.scrollBy(0, {scroll_height})")
                human_sleep(1, 2)
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2, 4)
            except:
                break

        # Uzmi sve timove
        matches = []
        rows = page.query_selector_all("div.event-row")  # svaki meč
        for row in rows:
            try:
                home = row.query_selector("span.event-team.home").inner_text().strip()
                away = row.query_selector("span.event-team.away").inner_text().strip()
                matches.append({"Home": home, "Away": away})
            except:
                continue

        browser.close()

    # Sačuvaj u Excel
    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
