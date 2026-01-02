from playwright.sync_api import sync_playwright
import pandas as pd
import os, time, random
from datetime import datetime, timedelta

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
OUTPUT_DIR = "output"
EXCEL_FILE = os.path.join(OUTPUT_DIR, "future_matches.xlsx")

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

DAYS_MAP = {
    "Pon": 0,
    "Uto": 1,
    "Sre": 2,
    "Čet": 3,
    "Pet": 4,
    "Sub": 5,
    "Ned": 6
}

def human_sleep(a=2, b=4):
    time.sleep(random.uniform(a, b))

def next_weekday(target):
    today = datetime.now()
    days_ahead = (target - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)

def scrape_future_matches():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rows = []

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

        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2, 3)
            except:
                break

        elements = page.locator("body *").all_inner_texts()
        browser.close()

    current_liga = ""
    current_date = ""
    current_time = ""

    i = 0
    while i < len(elements):
        line = elements[i].strip()

        # LIGA
        if line and line[0].isupper() and len(line) < 40 and " " in line:
            if any(x in line.lower() for x in ["liga", "engleska", "španija", "italija", "nemačka"]):
                current_liga = line
                i += 1
                continue

        # DATUM + VREME (22.01. Čet 21:00)
        if "." in line and ":" in line:
            try:
                parts = line.split()
                date_part = parts[0]
                time_part = parts[-1]

                d, m = map(int, date_part.split("."))
                year = datetime.now().year
                current_date = f"{d:02d}.{m:02d}.{year}"
                current_time = time_part
            except:
                pass
            i += 1
            continue

        # DAN + VREME (Sub 16:00)
        if line[:3] in DAYS_MAP and ":" in line:
            day = line[:3]
            time_part = line.split()[-1]
            target_date = next_weekday(DAYS_MAP[day])
            current_date = target_date.strftime("%d.%m.%Y")
            current_time = time_part
            i += 1
            continue

        # MEČ (2 linije timova)
        if current_liga and current_date and current_time:
            if i + 1 < len(elements):
                home = line
                away = elements[i + 1].strip()

                if home.isalpha() or " " in home:
                    rows.append({
                        "Datum": current_date,
                        "Vreme": current_time,
                        "Liga": current_liga,
                        "Domacin": home,
                        "Gost": away
                    })
                    i += 2
                    continue

        i += 1

    df = pd.DataFrame(rows)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva → {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
