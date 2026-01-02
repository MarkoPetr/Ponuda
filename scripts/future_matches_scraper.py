from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random
from datetime import datetime, timedelta
import re

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
OUTPUT_DIR = "output"
EXCEL_FILE = os.path.join(OUTPUT_DIR, "future_matches.xlsx")

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

def human_sleep(min_sec=2, max_sec=4):
    time.sleep(random.uniform(min_sec, max_sec))

def get_next_weekday(weekday_name):
    """Vrati datum prve naredne dane u nedelji (Mon-Sun) od danas"""
    weekdays = {
        "pon": 0, "uto": 1, "sre": 2, "čet": 3, "pet": 4, "sub": 5, "ned": 6
    }
    today = datetime.now()
    target_weekday = weekdays[weekday_name.lower()]
    days_ahead = target_weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)

def parse_date_line(line):
    """Vrati datum i vreme iz linije tipa '20.01. Uto 15:30' ili 'sub 15:00'"""
    full_date = ""
    time_str = ""

    # pun datum
    m1 = re.match(r"(\d{2}\.\d{2}\.)\s+\S+\s+(\d{2}:\d{2})", line)
    if m1:
        day_month = m1.group(1)
        time_str = m1.group(2)
        day, month = map(int, day_month.split("."))
        year = datetime.now().year
        full_date = f"{day:02d}.{month:02d}.{year}"
        return full_date, time_str

    # samo dan i vreme
    m2 = re.match(r"([a-zA-Z]{3})\s+(\d{2}:\d{2})", line)
    if m2:
        weekday = m2.group(1)
        time_str = m2.group(2)
        date_obj = get_next_weekday(weekday)
        full_date = date_obj.strftime("%d.%m.%Y")
        return full_date, time_str

    return "", ""

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
        human_sleep(5, 8)

        # zatvori kolačiće ako postoji
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1,2)
        except:
            pass

        # scroll do kraja stranice
        last_height = page.evaluate("() => document.body.scrollHeight")
        while True:
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            human_sleep(2,4)
            new_height = page.evaluate("() => document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        text = page.inner_text("body")
        browser.close()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    current_league = ""
    i = 0

    # lista poznatih liga
    known_leagues = [
        "Liga šampiona","Liga evrope","Engleska 1","Španija 1","Italija 1",
        "Nemačka 1","Francuska 1","Engleska 2","Afrika kup nacija","Portugalija 1",
        "Engleska fa kup","Španija 2","Španija 3","Španija 4","Španija superkup",
        "Italija 2","Italija 3","Francuska 2","Holandija 1","Australija 1","Škotska 1"
    ]

    while i < len(lines):
        line = lines[i]

        if line in known_leagues:
            current_league = line
            i += 1
            continue

        # pokušaj parsirati datum i vreme
        full_date, time_str = parse_date_line(line)
        if full_date or time_str:
            try:
                home_team = lines[i+1]
                away_team = lines[i+2]

                matches.append({
                    "Datum": full_date,
                    "Vreme": time_str,
                    "Liga": current_league,
                    "Domacin": home_team,
                    "Gost": away_team
                })
                i += 3
                continue
            except IndexError:
                i += 1
        else:
            i += 1

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
