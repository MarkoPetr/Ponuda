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
    return (today + timedelta(days=days_ahead)).strftime("%d.%m.%Y")

def get_full_date_from_ddmm(ddmm_str):
    try:
        day, month = map(int, ddmm_str.split("."))
        year = datetime.now().year
        return f"{day:02d}.{month:02d}.{year}"
    except:
        return ""

def scrape_future_matches():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    matches = []

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

        # uzmi sve sekcije sporta
        sports_sections = page.locator("section").all()

        for section in sports_sections:
            sport_title = section.locator("h2").first.inner_text().strip()
            if "fudbal" not in sport_title.lower():
                continue  # ignorisi sve osim fudbala

            league_elements = section.locator("span").all()
            rows = section.locator("div").all()

            current_league = ""
            i = 0
            while i < len(rows):
                text = rows[i].inner_text().strip()

                # ako linija liči na naziv lige (span element)
                if any(text in le.inner_text() for le in league_elements):
                    current_league = text
                    i += 1
                    continue

                # PUN DATUM: "20.01. Uto 16:30"
                m_full = re.match(r"(\d{2}\.\d{2})\.\s+\S+\s+(\d{2}:\d{2})", text)
                if m_full:
                    date = get_full_date_from_ddmm(m_full.group(1))
                    time_ = m_full.group(2)
                    try:
                        home = rows[i+1].inner_text().strip()
                        away = rows[i+2].inner_text().strip()
                        matches.append({
                            "Datum": date,
                            "Vreme": time_,
                            "Liga": current_league,
                            "Domacin": home,
                            "Gost": away
                        })
                        i += 3
                        continue
                    except IndexError:
                        i += 1

                # SAMO DAN + VREME: "sub 15:00"
                m_day = re.match(r"(\S+)\s+(\d{2}:\d{2})", text)
                if m_day:
                    date = get_full_date_from_day(m_day.group(1))
                    time_ = m_day.group(2)
                    try:
                        home = rows[i+1].inner_text().strip()
                        away = rows[i+2].inner_text().strip()
                        matches.append({
                            "Datum": date,
                            "Vreme": time_,
                            "Liga": current_league,
                            "Domacin": home,
                            "Gost": away
                        })
                        i += 3
                        continue
                    except IndexError:
                        i += 1

                i += 1

        browser.close()

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} fudbalskih mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
