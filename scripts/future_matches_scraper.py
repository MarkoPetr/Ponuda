from playwright.sync_api import sync_playwright
import pandas as pd
import time, random, os, re
from datetime import datetime, timedelta

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
OUTPUT_DIR = "output"
EXCEL_FILE = os.path.join(OUTPUT_DIR, "future_matches.xlsx")

def human_sleep(a=2, b=5):
    time.sleep(random.uniform(a, b))

DAYS_MAP = {
    "Pon": 0, "Uto": 1, "Sre": 2,
    "Čet": 3, "Pet": 4, "Sub": 5, "Ned": 6
}

def next_weekday(day_name):
    today = datetime.now()
    target = DAYS_MAP[day_name]
    days_ahead = (target - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)

def parse_date_time(text):
    # 20.01. Uto 20:00
    m = re.match(r"(\d{2}\.\d{2}\.)\s+\w+\s+(\d{2}:\d{2})", text)
    if m:
        date = datetime.strptime(
            m.group(1) + str(datetime.now().year),
            "%d.%m.%Y"
        )
        return date.strftime("%d.%m.%Y"), m.group(2)

    # Sub 15:00
    m = re.match(r"(Pon|Uto|Sre|Čet|Pet|Sub|Ned)\s+(\d{2}:\d{2})", text)
    if m:
        d = next_weekday(m.group(1))
        return d.strftime("%d.%m.%Y"), m.group(2)

    return None, None

def scrape():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    matches = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        human_sleep(5, 8)

        # scroll do dna
        last_height = 0
        while True:
            page.mouse.wheel(0, 3000)
            human_sleep(1, 2)
            height = page.evaluate("document.body.scrollHeight")
            if height == last_height:
                break
            last_height = height

        text = page.inner_text("body")
        browser.close()

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    current_liga = None
    current_date = None
    current_time = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # liga
        if re.match(r"^[A-ZŠĐČĆŽ].+\d?$", line) and len(line) < 40:
            current_liga = line
            i += 1
            continue

        # datum / vreme
        d, t = parse_date_time(line)
        if d:
            current_date, current_time = d, t
            i += 1
            continue

        # meč
        if (
            current_liga and current_date and
            i + 1 < len(lines) and
            not re.search(r"\d|\+", line) and
            not re.search(r"\d|\+", lines[i + 1])
        ):
            matches.append({
                "Datum": current_date,
                "Vreme": current_time,
                "Liga": current_liga,
                "Domacin": line,
                "Gost": lines[i + 1]
            })
            i += 2
            continue

        i += 1

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva")

if __name__ == "__main__":
    scrape()
