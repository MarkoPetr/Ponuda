from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random
import re
from datetime import datetime, timedelta

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
OUTPUT_DIR = "output"
EXCEL_FILE = os.path.join(OUTPUT_DIR, "future_matches.xlsx")

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

# Mape za dan u nedelji na srpski
DAYS_MAP = {
    "Pon": 0,
    "Uto": 1,
    "Sre": 2,
    "Čet": 3,
    "Pet": 4,
    "Sub": 5,
    "Ned": 6
}

def human_sleep(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def get_next_weekday(day_name):
    """Ako je datum samo dan i vreme, vraća datum prve sledeće te nedelje"""
    today = datetime.now()
    target_weekday = DAYS_MAP.get(day_name, 0)
    days_ahead = (target_weekday - today.weekday() + 7) % 7
    if days_ahead == 0:  # ako je danas, uzmi sledeću nedelju
        days_ahead = 7
    target_date = today + timedelta(days=days_ahead)
    return target_date.strftime("%d.%m.%Y")

def get_full_date(day_month_str):
    """Pretvara 'dd.mm.' u 'dd.mm.gggg' sa trenutnom godinom"""
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
        human_sleep(5, 8)

        # zatvori kolačiće ako postoji
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1, 2)
        except:
            pass

        # scroll do kraja stranice
        previous_height = 0
        while True:
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            human_sleep(1, 2)
            current_height = page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break
            previous_height = current_height

        # uzmi ceo tekst
        text = page.inner_text("body")
        browser.close()

    # Parsiranje linija
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    current_league = ""
    i = 0

    while i < len(lines):
        line = lines[i]

        # Ako je linija naziv lige
        if re.match(r".*(Liga|Engleska|Španija|Italija|Nemačka|Francuska|Holandija|Australija|Škotska|Afrika|Portugalija).*", line, re.I):
            current_league = line
            i += 1
            continue

        # Ako linija sadrži datum i vreme: "20.01. Uto 15:30"
        date_match = re.match(r"(?:(\d{2}\.\d{2}\.)\s+)?(\w{3})\s+(\d{2}:\d{2})", line)
        if date_match:
            day_month = date_match.group(1)
            day_name = date_match.group(2)
            time_str = date_match.group(3)

            # odredi puni datum
            if day_month:
                full_date = get_full_date(day_month)
            else:
                full_date = get_next_weekday(day_name)

            try:
                home_team = lines[i + 1]
                away_team = lines[i + 2]

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
