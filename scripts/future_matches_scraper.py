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

# mapiranje skraćenih dana na int (Python weekday, 0=ponedeljak)
WEEKDAY_MAP = {
    "pon": 0, "uto": 1, "sre": 2, "čet": 3, "pet": 4, "sub": 5, "ned": 6
}

def human_sleep(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def get_full_date_from_day(day_str):
    today = datetime.now()
    target_weekday = WEEKDAY_MAP.get(day_str.lower())
    if target_weekday is None:
        return ""
    days_ahead = (target_weekday - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    match_date = today + timedelta(days=days_ahead)
    return match_date.strftime("%d.%m.%Y")

def get_full_date_from_ddmm(ddmm_str):
    try:
        day, month = map(int, ddmm_str.split("."))
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
        human_sleep(5,8)

        # zatvori kolačiće ako postoji
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1,2)
        except:
            pass

        # učitaj sve mečeve (scroll "kao čovek")
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2,4)
            except:
                break

        # uzmi tekst sa stranice
        text = page.inner_text("body")
        browser.close()

    # Parsiranje linija
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    current_league = ""
    i = 0

    while i < len(lines):
        line = lines[i]

        # ✅ Nova logika: sve što nije datum ili dan+vreme tretiramo kao ligu
        m_full = re.match(r"(\d{2}\.\d{2})\.\s+\S+\s+(\d{2}:\d{2})", line)
        m_day = re.match(r"(\S+)\s+(\d{2}:\d{2})", line)

        if m_full or m_day:
            # ovo je meč, ne liga
            if m_full:
                ddmm = m_full.group(1)
                time_str = m_full.group(2)
                full_date = get_full_date_from_ddmm(ddmm)
            else:
                day_name = m_day.group(1)
                time_str = m_day.group(2)
                full_date = get_full_date_from_day(day_name)

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
            except IndexError:
                i += 1
            continue

        # 🔹 Sve ostalo je liga
        current_league = line
        i += 1

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
