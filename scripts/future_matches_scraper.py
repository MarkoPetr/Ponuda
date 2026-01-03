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

        # učitaj sve mečeve
        prev_count = 0
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2, 4)
                current_count = len(page.query_selector_all("div.match-row"))
                if current_count == prev_count:
                    break
                prev_count = current_count
            except:
                break

        # uzmi sve blokove liga
        league_blocks = page.query_selector_all("div.competition-block")
        for block in league_blocks:
            # naziv lige je u zaglavlju
            league_name_el = block.query_selector("div.competition-header")
            league_name = league_name_el.inner_text().strip() if league_name_el else "Nepoznato"

            # svi mečevi unutar tog bloka
            match_rows = block.query_selector_all("div.match-row")
            for row in match_rows:
                text = row.inner_text().strip().split("\n")
                # parsiraj datum, vreme, domacin, gost
                date_str, home_team, away_team = "", "", ""
                for line in text:
                    if "." in line and any(day in line.lower() for day in WEEKDAY_MAP):
                        date_str = line.split()[0]  # dd.mm.
                        day_name = line.split()[1]
                        time_str = line.split()[2]
                        full_date = get_full_date_from_ddmm(date_str)
                        date_val = full_date
                        time_val = time_str
                    elif home_team == "":
                        home_team = line
                    elif away_team == "":
                        away_team = line
                matches.append({
                    "Datum": date_val,
                    "Vreme": time_val,
                    "Liga": league_name,
                    "Domacin": home_team,
                    "Gost": away_team
                })

        browser.close()

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
