from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random
from datetime import datetime

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

# normalize datum, dodaje godinu ako nedostaje
def normalize_date(date_str):
    date_str = date_str.strip()
    now = datetime.now()
    year = now.year

    # Ako je format DD.MM. (bez godine)
    if '.' in date_str and date_str.count('.') == 2:
        parts = date_str.split('.')
        if len(parts[2]) == 0:
            return f"{parts[0]}.{parts[1]}.{year}"
        return date_str
    # Ako je format DD.MM (bez poslednje tacke)
    if '.' in date_str and date_str.count('.') == 1:
        parts = date_str.split('.')
        return f"{parts[0]}.{parts[1]}.{year}"
    return date_str

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

        # pokušaj zatvaranja kolačića ako postoji
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1,2)
        except:
            pass

        # učitavanje svih mečeva
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2,4)
            except:
                break

        text = page.inner_text("body")
        browser.close()

    # parsiranje mečeva
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    current_date = ""
    current_liga = ""

    for i, line in enumerate(lines):
        # detektuj datum: format npr. 20.01. ili 20.01.2026
        if any(char.isdigit() for char in line) and ('.' in line):
            current_date = normalize_date(line)
            continue

        # detektuj ligu: linije sa "Liga" ili "superkup" ili broj liga (prilagoditi po potrebi)
        if 'Liga' in line or 'superkup' in line or line.lower() in ['liga šampiona','liga evrope','engleska 1','italija 1']:
            current_liga = line
            continue

        # detektuj meč: pretpostavljamo da svaka linija sa home timom sledi format: Home -> Away
        # Kvota linije ignorišemo
        if i+1 < len(lines):
            home = line
            away = lines[i+1]
            # preskoči ako su ovo kvote (+420, 1.65 itd.)
            if home.startswith('+') or home.replace('.','',1).isdigit():
                continue
            if away.startswith('+') or away.replace('.','',1).isdigit():
                continue
            # dodaj meč
            matches.append({
                "Datum": current_date,
                "Liga": current_liga,
                "Home": home,
                "Away": away
            })

    df = pd.DataFrame(matches)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Sačuvano {len(df)} mečeva u {EXCEL_FILE}")

if __name__ == "__main__":
    scrape_future_matches()
