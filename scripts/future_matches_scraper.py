from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random

URL = "https://www.mozzartbet.com/sr/fudbal"  # Mozzart stranica sa ponudom budućih mečeva
OUTPUT_DIR = "output"
EXCEL_FILE = os.path.join(OUTPUT_DIR, "future_matches.xlsx")

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

def human_sleep(min_sec=3, max_sec=6):
    time.sleep(random.uniform(min_sec, max_sec))

def scrape_future_matches():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    matches = []

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

        # zatvaranje popupa sa kolačićima
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1,2)
        except:
            pass

        # Scroll i učitavanje svih mečeva
        while True:
            try:
                page.evaluate("window.scrollBy(0, 600)")
                human_sleep(1,2)
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2,4)
            except:
                break

        # Prikupljanje imena timova
        events = page.query_selector_all(".event-row")  # prilagodi selektor po strukturi sajta
        for e in events:
            try:
                home = e.query_selector(".home-team")  # selektor za domaći tim
                away = e.query_selector(".away-team")  # selektor za gostujući tim
                matches.append({
                    "Home": home.inner_text().strip() if home else "",
                    "Away": away.inner_text().strip() if away else ""
                })
            except:
                continue

        browser.close()

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
