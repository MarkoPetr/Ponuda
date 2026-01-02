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

def human_sleep(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def get_full_date(day_name, day_month_str):
    # day_month_str expected: '09.01'
    day, month = map(int, day_month_str.split("."))
    now = datetime.now()
    year = now.year
    full_date = datetime(year, month, day)
    # ako datum već prošao, pretpostavi sledeću godinu
    if full_date < now - timedelta(days=1):
        full_date = datetime(year + 1, month, day)
    return full_date.strftime("%d.%m.%Y")

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

        # učitavanje svih mečeva
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2,4)
            except:
                break

        # dohvat celog teksta
        text = page.inner_text("body")
        browser.close()

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    matches = []
    current_league = None
    current_date = None
    pending_time = None

    # regex za liniju datuma i vremena: "09.01. Pet 14:35"
    date_time_pattern = re.compile(r"(\d{2}\.\d{2})\.\s*\w{3}\s*(\d{1,2}:\d{2})")
    
    for line in lines:
        # prepoznaj ligu (ako je linija "Engleska 1", "Španija 4", itd.)
        if re.match(r"^[A-ZŠĆŽ][\w\s\.]+\d*$", line) and not "X" in line and not re.search(r"\d{2}:\d{2}", line):
            current_league = line
            continue

        # ignorisi linije "1 X 2"
        if line == "1 X 2":
            continue

        # prepoznaj datum + vreme
        dt_match = date_time_pattern.search(line)
        if dt_match:
            day_month, time_str = dt_match.groups()
            current_date = get_full_date("", day_month)
            pending_time = time_str
            # sada čekamo timove u sledećim linijama
            continue

        # linija sa timovima (obično "Domacin  Gost")
        if pending_time and "  " in line:
            teams = line.split("  ")
            if len(teams) >= 2:
                home, away = teams[0].strip(), teams[1].strip()
                matches.append({
                    "Datum": current_date,
                    "Vreme": pending_time,
                    "Liga": current_league,
                    "Domacin": home,
                    "Gost": away
                })
                pending_time = None  # reset
            continue

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
