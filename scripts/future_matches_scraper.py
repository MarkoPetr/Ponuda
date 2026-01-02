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

# Pretvara "Sub 15:30" u puni datum i vreme (YYYY-MM-DD HH:MM)
def day_time_to_datetime(day_str, time_str):
    today = datetime.now()
    if day_str not in DAYS_MAP:
        return None

    days_ahead = (DAYS_MAP[day_str] - today.weekday() + 7) % 7
    # Ako je dan danas, proveri vreme
    try:
        t = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return None  # nevalidno vreme

    if days_ahead == 0 and t < today.time():
        days_ahead = 7

    dt = today + timedelta(days=days_ahead)
    return dt.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M")

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
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2,4)
            except:
                break

        text = page.inner_text("body")
        browser.close()

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    matches = []
    current_date = ""
    current_time = ""
    current_liga = ""

    for i, line in enumerate(lines):
        # --- datum i vreme ---
        if line[:3] in DAYS_MAP:
            parts = line.split(' ')
            if len(parts) == 2:
                dt_full = day_time_to_datetime(parts[0], parts[1])
                if dt_full:
                    current_date = dt_full.split(' ')[0]
                    current_time = dt_full.split(' ')[1]
            continue

        # --- liga ---
        liga_keywords = ["liga","superkup","fa kup","cup","kup"]
        if any(k.lower() in line.lower() for k in liga_keywords):
            current_liga = line
            continue

        # --- detekcija meča ---
        if i+1 < len(lines):
            home = line
            away = lines[i+1]

            # preskoči linije koje nisu timovi
            skip_keywords = ["+","Kompletna","Sports","Promo","Bonus","Uživo"]
            if any(home.startswith(k) or away.startswith(k) for k in skip_keywords):
                continue
            # preskoči ako je broj/kvota
            if home.replace('.','',1).isdigit() or away.replace('.','',1).isdigit():
                continue

            matches.append({
                "Datum": current_date,
                "Vreme": current_time,
                "Liga": current_liga,
                "Home": home,
                "Away": away
            })

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
