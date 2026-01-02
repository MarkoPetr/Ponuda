from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random
from datetime import datetime

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days&sort=bytime"
OUTPUT_DIR = "output"
EXCEL_FILE = os.path.join(OUTPUT_DIR, "future_matches.xlsx")

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

DAYS_MAP = {
    "Pon": 0, "Uto": 1, "Sre": 2,
    "Čet": 3, "Pet": 4, "Sub": 5, "Ned": 6
}

def human_sleep(a=2, b=4):
    time.sleep(random.uniform(a, b))

def normalize_date(date_text):
    # primer: "22.01. Čet 21:00" ili "Sub 15:00"
    parts = date_text.split()

    today = datetime.now()

    if "." in parts[0]:
        # ima pun datum
        day, month = parts[0].replace(".", "").split()
        year = today.year
        time_part = parts[-1]
        return f"{day.zfill(2)}.{month.zfill(2)}.{year}", time_part

    # nema datum → računamo po danu u nedelji
    day_name = parts[0]
    time_part = parts[1]

    target_weekday = DAYS_MAP[day_name]
    delta = (target_weekday - today.weekday()) % 7
    if delta == 0:
        delta = 7

    match_date = today + pd.Timedelta(days=delta)
    return match_date.strftime("%d.%m.%Y"), time_part

def scrape_future_matches():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=MOBILE_UA,
            viewport={"width": 412, "height": 915},
            locale="sr-RS"
        )
        page = context.new_page()
        page.goto(URL, timeout=60000)
        human_sleep(5, 7)

        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
        except:
            pass

        # učitaj sve
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2, 3)
            except:
                break

        current_league = None

        blocks = page.query_selector_all("div")

        for block in blocks:
            text = block.inner_text().strip()

            # liga
            if block.get_attribute("class") and "league" in block.get_attribute("class"):
                current_league = text
                continue

            # datum + vreme
            if any(day in text for day in DAYS_MAP.keys()) and ":" in text:
                try:
                    date_str, time_str = normalize_date(text)

                    teams = block.evaluate("""
                        el => {
                            let parent = el.parentElement;
                            let teams = parent.querySelectorAll("div");
                            return Array.from(teams).map(t => t.innerText).filter(x => x.length > 1);
                        }
                    """)

                    if len(teams) >= 2:
                        home = teams[0].replace("⚡", "").strip()
                        away = teams[1].replace("⚡", "").strip()

                        data.append({
                            "Datum": date_str,
                            "Vreme": time_str,
                            "Liga": current_league,
                            "Domacin": home,
                            "Gost": away
                        })
                except:
                    continue

        browser.close()

    df = pd.DataFrame(data)
    df.drop_duplicates(inplace=True)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva")

if __name__ == "__main__":
    scrape_future_matches()
