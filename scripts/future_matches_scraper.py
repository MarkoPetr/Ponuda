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

def human_sleep(min_sec=3, max_sec=6):
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
        human_sleep(5,8)

        # pokušaj zatvaranja kolačića ako postoji
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1,2)
        except:
            pass

        # učitavanje svih mečeva
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2,4)
            except:
                break

        text = page.inner_text("body")
        browser.close()

    # parsiranje samo datuma i timova
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    i = 0
    while i < len(lines):
        # datum/vreme linija u formatu: Ned 10:30
        if lines[i][:3] in ["Pon","Uto","Sre","Čet","Pet","Sub","Ned"]:
            try:
                match = {
                    "DateTime": lines[i],
                    "Home": lines[i+1],
                    "Away": lines[i+2]
                }
                matches.append(match)
                i += 3
            except:
                i += 1
        else:
            i += 1

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
