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

INVALID_LINES_START = [
    "Pomoc", "Registracija", "Prijava", "Klađenje", "Uživo", "NBA", "Kazino", "Aviator",
    "Lucky", "NSoft", "Novo", "Virtuali", "Promocije", "MozzApp", "Izdvojena", "Bonus tiket",
    "Tvoj tiket", "Isprobaj", "Kompletna ponuda", "1 sat", "3 sata", "Sutra", "Danas",
]

def human_sleep(min_sec=3, max_sec=6):
    time.sleep(random.uniform(min_sec, max_sec))

def normalize_date(date_str):
    # datum u formatu DD.MM ili DD.MM.YYYY
    date_str = date_str.strip()
    now = datetime.now()
    year = now.year
    if '.' in date_str:
        parts = date_str.split('.')
        if len(parts) == 2 or (len(parts) == 3 and parts[2] == ''):
            return f"{parts[0]}.{parts[1]}.{year}"
        return date_str
    return date_str

# Pretvori dan u datum (npr. Sub 15:00 -> tačan datum)
def day_time_to_datetime(day_str, time_str):
    days_map = {"Pon":0, "Uto":1, "Sre":2, "Čet":3, "Pet":4, "Sub":5, "Ned":6}
    today = datetime.now()
    # sub, uto itd.
    day_abbr = day_str[:3]
    if day_abbr not in days_map:
        return None
    target_weekday = days_map[day_abbr]
    days_ahead = (target_weekday - today.weekday() + 7) % 7
    if days_ahead == 0 and datetime.strptime(time_str, "%H:%M").time() < today.time():
        days_ahead = 7
    match_date = today + timedelta(days=days_ahead)
    dt_str = match_date.strftime("%d.%m.%Y") + " " + time_str
    return dt_str

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

        # učitaj sve mečeve
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2,4)
            except:
                break

        text = page.inner_text("body")
        browser.close()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    current_date = ""
    current_liga = ""
    i = 0

    while i < len(lines):
        line = lines[i]

        # ignorisi smeće
        if any(line.startswith(x) for x in INVALID_LINES_START):
            i += 1
            continue

        # datum: 20.01. ili pon, uto...
        if any(char.isdigit() for char in line) and '.' in line:
            current_date = normalize_date(line)
            i += 1
            continue

        # dan + vreme (Sub 15:00)
        if line[:3] in ["Pon","Uto","Sre","Čet","Pet","Sub","Ned"]:
            day_time = line.split(' ')
            dt_full = day_time_to_datetime(day_time[0], day_time[1])
            if dt_full:
                current_date = dt_full.split(' ')[0]
                current_time = dt_full.split(' ')[1]
            else:
                current_time = ""
            i += 1
            continue
        else:
            current_time = ""

        # detektuj ligu
        if "Liga" in line or "superkup" in line.lower() or "kup" in line.lower():
            current_liga = line
            i += 1
            continue

        # detektuj meč (home + away)
        if i+1 < len(lines):
            home = lines[i]
            away = lines[i+1]
            # preskoči ako su ovo kvote
            if home.startswith('+') or home.replace('.','',1).isdigit():
                i += 1
                continue
            if away.startswith('+') or away.replace('.','',1).isdigit():
                i += 2
                continue
            matches.append({
                "Datum": current_date,
                "Vreme": current_time,
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
