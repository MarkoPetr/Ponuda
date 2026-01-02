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

def human_sleep(min_sec=3, max_sec=6):
    time.sleep(random.uniform(min_sec, max_sec))

# Pretvara "Sub 15:00" ili "Ned 12:30" u tačan datum i vreme
def day_time_to_datetime(day_str, time_str):
    weekdays = {"Pon":0, "Uto":1, "Sre":2, "Čet":3, "Pet":4, "Sub":5, "Ned":6}
    today = datetime.now()
    day_offset = weekdays.get(day_str, 0) - today.weekday()
    if day_offset < 0:
        day_offset += 7
    dt = today + timedelta(days=day_offset)
    hour, minute = map(int, time_str.split(":"))
    dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
    # Ako je vreme već prošlo danas, uzmi sledeću nedelju
    if dt < today:
        dt += timedelta(days=7)
    return dt

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

    # parsiranje linija
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    parsing = False
    current_liga = ""
    
    i = 0
    while i < len(lines):
        line = lines[i]

        # Početak pravih mečeva
        if not parsing and line == "Ishod meča":
            parsing = True
            # preskoči sledeće dve linije "1 X 2"
            i += 3
            continue

        if parsing:
            # nova liga (pre datuma linije su imena liga)
            if any(substr in line for substr in ["Liga šampiona","Liga evrope","Engleska","Italija","Španija","Nemačka","Francuska"]):
                current_liga = line
                i += 1
                continue

            # datum linija: DD.MM. Ddd HH:MM
            parts = line.split()
            if len(parts) == 3 and ":" in parts[2]:
                date_str, day_str, time_str = parts
                try:
                    dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m. %H:%M")
                except:
                    # fallback za format bez godine
                    dt = datetime.strptime(f"{date_str}.{datetime.now().year} {time_str}", "%d.%m.%Y %H:%M")
                
                # home i away timovi
                if i+2 < len(lines):
                    home = lines[i+1]
                    away = lines[i+2]
                    # preskoči kvote
                    if any(char.isdigit() for char in home) or any(char.isdigit() for char in away):
                        i += 1
                        continue
                    matches.append({
                        "Datum": dt.date().strftime("%Y-%m-%d"),
                        "Vreme": dt.time().strftime("%H:%M"),
                        "Liga": current_liga,
                        "Home": home,
                        "Away": away
                    })
                    i += 3
                    continue
        i += 1

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
