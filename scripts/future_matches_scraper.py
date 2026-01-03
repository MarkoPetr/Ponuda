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

def human_sleep(a=2, b=5):
    time.sleep(random.uniform(a, b))

def get_full_date_from_day(day_str):
    today = datetime.now()
    wd = WEEKDAY_MAP.get(day_str.lower())
    if wd is None:
        return ""
    delta = (wd - today.weekday() + 7) % 7
    if delta == 0:
        delta = 7
    return (today + timedelta(days=delta)).strftime("%d.%m.%Y")

def get_full_date_from_ddmm(ddmm):
    try:
        d, m = map(int, ddmm.split("."))
        return f"{d:02d}.{m:02d}.{datetime.now().year}"
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
        human_sleep(5, 8)

        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
        except:
            pass

        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2, 4)
            except:
                break

        # 🔴 KLJUČNO: uzimamo ligu + njen blok
        league_blocks = page.query_selector_all("section")

        for block in league_blocks:
            try:
                league_name = block.query_selector("button").inner_text().strip()
            except:
                continue

            block_text = block.inner_text()
            lines = [l.strip() for l in block_text.splitlines() if l.strip()]

            i = 0
            while i < len(lines):
                line = lines[i]

                # PUN DATUM
                m_full = re.match(r"(\d{2}\.\d{2})\.\s+\S+\s+(\d{2}:\d{2})", line)
                if m_full:
                    date = get_full_date_from_ddmm(m_full.group(1))
                    time_str = m_full.group(2)
                    try:
                        matches.append({
                            "Datum": date,
                            "Vreme": time_str,
                            "Liga": league_name,
                            "Domacin": lines[i+1],
                            "Gost": lines[i+2]
                        })
                        i += 3
                        continue
                    except:
                        pass

                # SAMO DAN
                m_day = re.match(r"(\S+)\s+(\d{2}:\d{2})", line)
                if m_day:
                    date = get_full_date_from_day(m_day.group(1))
                    time_str = m_day.group(2)
                    try:
                        matches.append({
                            "Datum": date,
                            "Vreme": time_str,
                            "Liga": league_name,
                            "Domacin": lines[i+1],
                            "Gost": lines[i+2]
                        })
                        i += 3
                        continue
                    except:
                        pass

                i += 1

        browser.close()

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva")

if __name__ == "__main__":
    scrape_future_matches()
