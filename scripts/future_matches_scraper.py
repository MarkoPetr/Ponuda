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

DAN_MAP = {
    "Pon": 0,
    "Uto": 1,
    "Sre": 2,
    "Čet": 3,
    "Pet": 4,
    "Sub": 5,
    "Ned": 6
}

def human_sleep(min_sec=3, max_sec=6):
    time.sleep(random.uniform(min_sec, max_sec))

# normalize datum ako je format DD.MM. ili DD.MM.YYYY
def normalize_date(date_str):
    date_str = date_str.strip()
    now = datetime.now()
    year = now.year
    if '.' in date_str:
        parts = date_str.split('.')
        if len(parts) == 2:
            return f"{parts[0]}.{parts[1]}.{year}"
        elif len(parts) == 3 and parts[2] == '':
            return f"{parts[0]}.{parts[1]}.{year}"
        else:
            return date_str
    return date_str

# izračunava sledeći datum za dati dan u nedelji
def next_weekday(day_abbr):
    today = datetime.now()
    target_day = DAN_MAP.get(day_abbr, None)
    if target_day is None:
        return today
    days_ahead = target_day - today.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)

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

        # zatvori kolačiće ako postoje
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

    # parsiranje
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    current_date = None
    current_liga = ""

    i = 0
    while i < len(lines):
        line = lines[i]

        # linija sa punim datumom
        if any(char.isdigit() for char in line) and '.' in line:
            current_date = normalize_date(line)
            i += 1
            continue

        # linija sa ligom
        if 'Liga' in line or 'superkup' in line or line.lower() in ['liga šampiona','liga evrope','engleska 1','italija 1']:
            current_liga = line
            i += 1
            continue

        # linija sa danom u nedelji + vreme (Sub 15:00)
        if line[:3] in DAN_MAP:
            dt = next_weekday(line[:3])
            current_date = dt.strftime("%d.%m.%Y") + " " + line[4:].strip()
            i += 1
            continue

        # linija sa meč home -> away
        if i + 1 < len(lines):
            home = line
            away = lines[i+1]

            # preskoči kvote i numeričke linije
            if home.startswith('+') or home.replace('.','',1).isdigit():
                i += 1
                continue
            if away.startswith('+') or away.replace('.','',1).isdigit():
                i += 1
                continue

            matches.append({
                "Datum": current_date,
                "Liga": current_liga,
                "Home": home,
                "Away": away
            })
            i += 2
        else:
            i += 1

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
