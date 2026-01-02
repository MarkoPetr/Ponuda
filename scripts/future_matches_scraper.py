from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random
import re
from datetime import datetime

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

def get_full_date(day_month_str):
    """Pretvara 'dd.mm.' u 'dd.mm.gggg' sa trenutnom godinom"""
    if not day_month_str:
        return ""
    try:
        day, month = map(int, day_month_str.split("."))
        year = datetime.now().year
        return f"{day:02d}.{month:02d}.{year}"
    except:
        return ""

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

        # zatvori kolačiće ako postoji
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1,2)
        except:
            pass

        # učitaj sve mečeve
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2,4)
            except:
                break

        text = page.inner_text("body")
        browser.close()

    # Parsiranje linija
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    current_league = ""
    i = 0

    while i < len(lines):
        line = lines[i]

        # Ako je linija naziv lige (npr. "Liga šampiona")
        if line in [
            "Liga šampiona","Liga evrope","Engleska 1","Španija 1","Italija 1",
            "Nemačka 1","Francuska 1","Engleska 2","Afrika kup nacija","Portugalija 1",
            "Engleska fa kup","Španija 2","Španija 3","Španija 4","Španija superkup",
            "Italija 2","Italija 3","Francuska 2","Holandija 1","Australija 1","Škotska 1"
        ]:
            current_league = line
            i += 1
            continue

        # Ako je linija datum/vreme, format: "20.01. Uto 15:30"
        date_match = re.match(r"(\d{2}\.\d{2}\.)\s+\S+\s+(\d{2}:\d{2})", line)
        if date_match:
            day_month = date_match.group(1)
            time_str = date_match.group(2)

            try:
                home_team = lines[i+1]
                away_team = lines[i+2]

                full_date = get_full_date(day_month)

                matches.append({
                    "Datum": full_date,
                    "Vreme": time_str,
                    "Liga": current_league,
                    "Domacin": home_team,
                    "Gost": away_team
                })
                i += 3
            except IndexError:
                i += 1
            continue

        i += 1

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
