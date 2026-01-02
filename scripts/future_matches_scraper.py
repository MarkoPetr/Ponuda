from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random
import re
from datetime import datetime, timedelta

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days&sort=bytime"
OUTPUT_DIR = "output"
EXCEL_FILE = os.path.join(OUTPUT_DIR, "future_matches.xlsx")

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

# mape dana na engleski (Python datetime)
DAY_MAP = {
    "Pon": 0, "Uto": 1, "Sre": 2, "Čet": 3, "Pet": 4, "Sub": 5, "Ned": 6
}

def human_sleep(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def get_full_date(day_name, day_month_str):
    """Pretvara dd.mm. i dan u nedelji u puni datum sa godinom"""
    today = datetime.today()
    day, month = map(int, day_month_str.split("."))
    candidate = datetime(today.year, month, day)

    # ako je datum već prošao ove godine, prebaci na sledeću
    if candidate < today - timedelta(days=1):
        candidate = datetime(today.year + 1, month, day)

    # proveri da li dan u nedelji odgovara (Pon=0, Ned=6)
    target_weekday = DAY_MAP.get(day_name, candidate.weekday())
    delta_days = (target_weekday - candidate.weekday()) % 7
    full_date = candidate + timedelta(days=delta_days)
    return full_date.strftime("%Y-%m-%d")

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

        # zatvaranje kolačića ako postoji
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1,2)
        except:
            pass

        # učitavanje svih mečeva
        while True:
            try:
                page.click("text=Učitaj još", timeout=5000)
                human_sleep(2,4)
            except:
                break

        # dohvat celog sadržaja ispod "Ishod meča"
        body_text = page.inner_text("body")
        browser.close()

    lines = [line.strip() for line in body_text.splitlines() if line.strip()]
    matches = []
    current_league = None
    start_parsing = False

    for i, line in enumerate(lines):
        if "Ishod meča" in line:
            start_parsing = True
            continue
        if not start_parsing:
            continue

        # linija koja izgleda kao liga
        if re.match(r"[A-Za-zšŠčČćĆđĐžŽ0-9\s\-]+$", line) and len(line) < 30:
            current_league = line
            continue

        # datum format dd.mm. i opcionalno dan u nedelji i vreme
        date_match = re.match(r"(\d{2}\.\d{2}\.)\s*(\S+)?\s*(\d{2}:\d{2})?", line)
        if date_match:
            try:
                day_month = date_match.group(1)
                day_name = date_match.group(2)
                time_str = date_match.group(3)
                home_team = lines[i+1]
                away_team = lines[i+2]

                full_date = get_full_date(day_name, day_month)

                matches.append({
                    "Date": full_date,
                    "Time": time_str,
                    "League": current_league,
                    "Home": home_team,
                    "Away": away_team
                })
            except IndexError:
                continue

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
