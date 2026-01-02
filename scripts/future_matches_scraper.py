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
        human_sleep(5, 8)

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

        # ⚡ Nova logika: dohvat svih elemenata mečeva
        match_elements = page.query_selector_all("div.match-row")  # primer, zavisi od Mozzart DOM
        matches = []

        for el in match_elements:
            # dohvat imena timova
            try:
                home_team = el.query_selector(".home-team").inner_text()
                away_team = el.query_selector(".away-team").inner_text()
            except:
                continue

            # dohvat datuma/vremena
            try:
                dt_text = el.query_selector(".match-time").inner_text()  # npr. "20.01. Uto 16:30" ili "sub 15:00"
            except:
                dt_text = ""

            # parsiranje datuma
            m_full = re.match(r"(\d{2}\.\d{2})\.\s*\S*\s*(\d{2}:\d{2})", dt_text)
            if m_full:
                full_date = get_full_date_from_ddmm(m_full.group(1))
                time_str = m_full.group(2)
            else:
                m_day = re.match(r"(\S+)\s+(\d{2}:\d{2})", dt_text)
                if m_day:
                    full_date = get_full_date_from_day(m_day.group(1))
                    time_str = m_day.group(2)
                else:
                    full_date = ""
                    time_str = ""

            # dohvat lige iz prethodnog sibling elementa koji sadrži "Default Competition flag"
            league_el = el.query_selector("xpath=preceding-sibling::*[contains(text(), 'Default Competition flag')][1]")
            if league_el:
                league_name = league_el.inner_text().replace("Default Competition flag", "").strip()
            else:
                league_name = ""

            matches.append({
                "Datum": full_date,
                "Vreme": time_str,
                "Liga": league_name,
                "Domacin": home_team,
                "Gost": away_team
            })

        df = pd.DataFrame(matches)
        df.to_excel(EXCEL_FILE, index=False)
        print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")
        browser.close()

if __name__ == "__main__":
    scrape_future_matches()
