from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random
from datetime import datetime, timedelta

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
OUTPUT_DIR = "output"
EXCEL_FILE = os.path.join(OUTPUT_DIR, "future_matches.xlsx")

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

DAYS_MAP = {"Pon":0,"Uto":1,"Sre":2,"Čet":3,"Pet":4,"Sub":5,"Ned":6}

def human_sleep(min_sec=3, max_sec=6):
    time.sleep(random.uniform(min_sec, max_sec))

def normalize_date(date_str):
    """Vraca DD.MM.YYYY format"""
    today = datetime.today()
    date_str = date_str.strip()

    # Dan u nedelji + vreme, npr. "Pon 20:00"
    if date_str[:3] in DAYS_MAP:
        target_weekday = DAYS_MAP[date_str[:3]]
        # pronadji najblizi datum od danas
        days_ahead = (target_weekday - today.weekday() + 7) % 7
        if days_ahead == 0:  # danasnji dan, ali mozda vec proslo vreme
            match_time = datetime.strptime(date_str[4:], "%H:%M").time()
            if match_time < today.time():
                days_ahead = 7
        match_date = today + timedelta(days=days_ahead)
        return match_date.strftime("%d.%m.%Y")

    # Datum sa danom i mesecem, npr. "22.01." ili "22.01.2026"
    parts = date_str.split(".")
    if len(parts) >= 2:
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2]) if len(parts) == 3 else today.year
        return f"{day:02d}.{month:02d}.{year}"

    return date_str  # fallback, nepoznat format

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

        # pokušaj zatvaranja kolačića
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

    # parsiranje mečeva
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    i = 0
    current_league = ""
    while i < len(lines):
        line = lines[i]

        # prepoznaj ligu (linija zavrsava na brojeve ili poznata imena)
        if any(x in line for x in ["Liga","Engleska","Španija","Italija","Nemačka","Francuska"]):
            current_league = line
            i += 1
            continue

        # datum ili dan u nedelji + vreme
        if line[:3] in DAYS_MAP or "." in line:
            try:
                match = {
                    "Datum": normalize_date(line),
                    "Liga": current_league,
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
