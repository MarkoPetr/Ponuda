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

# --- Helper functions ---
def human_sleep(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

def get_next_weekday(weekday: int):
    """Vraća datum narednog weekday (0=ponedeljak, 6=nedelja) od danas."""
    today = datetime.now()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)

def parse_date(line: str):
    """Parsira datum iz linije. Ako nema pun datum, računa prvi odgovarajući dan od danas."""
    # format pun datum: 20.01. Uto 15:30
    m = re.match(r"(\d{2}\.\d{2}\.)\s+(\S+)\s+(\d{2}:\d{2})", line)
    if m:
        day, month = map(int, m.group(1).split(".")[:2])
        year = datetime.now().year
        return f"{day:02d}.{month:02d}.{year}", m.group(3)
    
    # format samo dan: Sub 15:00
    m2 = re.match(r"(\S+)\s+(\d{2}:\d{2})", line)
    if m2:
        weekday_str = m2.group(1).lower()
        time_str = m2.group(2)
        weekdays = {
            "pon":0, "uto":1, "sre":2, "čet":3, "pet":4, "sub":5, "ned":6
        }
        if weekday_str[:3] in weekdays:
            dt = get_next_weekday(weekdays[weekday_str[:3]])
            return dt.strftime("%d.%m.%Y"), time_str
    return None, None

# --- Scraping ---
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

        # zatvori kolačiće
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1,2)
        except:
            pass

        # scroll do kraja
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2,4)
            except:
                break

        text = page.inner_text("body")
        browser.close()

    # --- Parsiranje ---
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    current_league = ""
    i = 0

    # Predefinisane lige
    known_leagues = [
        "Liga šampiona","Liga evrope","Engleska 1","Španija 1","Italija 1",
        "Nemačka 1","Francuska 1","Engleska 2","Afrika kup nacija","Portugalija 1",
        "Engleska fa kup","Španija 2","Španija 3","Španija 4","Španija superkup",
        "Italija 2","Italija 3","Francuska 2","Holandija 1","Australija 1","Škotska 1"
    ]

    while i < len(lines):
        line = lines[i]

        # Ako je linija naziv lige
        if line in known_leagues:
            current_league = line
            i += 1
            continue

        # Pokušaj da parsira datum i vreme
        date_str, time_str = parse_date(line)
        if date_str and time_str:
            # Sledeće dve linije su timovi
            try:
                home_team = lines[i+1]
                away_team = lines[i+2]
                matches.append({
                    "Datum": date_str,
                    "Vreme": time_str,
                    "Liga": current_league,
                    "Domacin": home_team,
                    "Gost": away_team
                })
                i += 3
                continue
            except IndexError:
                i += 1
                continue

        i += 1

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
