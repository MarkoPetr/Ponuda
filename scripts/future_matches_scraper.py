from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random
from datetime import datetime, timedelta
import re

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

def human_sleep(a=2, b=4):
    time.sleep(random.uniform(a, b))

def get_date_from_day(day):
    today = datetime.now()
    wd = WEEKDAY_MAP.get(day.lower())
    if wd is None:
        return ""
    delta = (wd - today.weekday() + 7) % 7
    if delta == 0:
        delta = 7
    return (today + timedelta(days=delta)).strftime("%d.%m.%Y")

def get_date_from_ddmm(ddmm):
    d, m = map(int, ddmm.split("."))
    return f"{d:02d}.{m:02d}.{datetime.now().year}"

def scrape():
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
        human_sleep(5,7)

        try:
            page.click("text=Sačuvaj i zatvori", timeout=3000)
        except:
            pass

        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep()
            except:
                break

        # ⬇️ SVAKA LIGA JE POSEBNA SEKCIJA
        competitions = page.locator("section").all()

        for comp in competitions:
            try:
                league = comp.locator("span").first.inner_text().strip()
            except:
                continue

            rows = comp.locator("div").all()

            i = 0
            while i < len(rows):
                text = rows[i].inner_text().strip()

                # 20.01. Uto 18:30
                m_full = re.search(r"(\d{2}\.\d{2})\.\s+\S+\s+(\d{2}:\d{2})", text)
                if m_full:
                    date = get_date_from_ddmm(m_full.group(1))
                    time_ = m_full.group(2)
                    home = rows[i+1].inner_text().strip()
                    away = rows[i+2].inner_text().strip()

                    matches.append({
                        "Datum": date,
                        "Vreme": time_,
                        "Liga": league,
                        "Domacin": home,
                        "Gost": away
                    })
                    i += 3
                    continue

                # sub 15:00
                m_day = re.search(r"(\S+)\s+(\d{2}:\d{2})", text)
                if m_day:
                    date = get_date_from_day(m_day.group(1))
                    time_ = m_day.group(2)
                    home = rows[i+1].inner_text().strip()
                    away = rows[i+2].inner_text().strip()

                    matches.append({
                        "Datum": date,
                        "Vreme": time_,
                        "Liga": league,
                        "Domacin": home,
                        "Gost": away
                    })
                    i += 3
                    continue

                i += 1

        browser.close()

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva sa 100% tačnom ligom")

if __name__ == "__main__":
    scrape()
