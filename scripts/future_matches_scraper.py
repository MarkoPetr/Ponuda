# scripts/future_matches_debug_auto.py
import subprocess
import sys
import time
import random
from playwright.sync_api import sync_playwright

# --- AUTOMATSKA INSTALACIJA ---
def install_packages():
    try:
        import playwright
    except ImportError:
        print("➡️ Instaliram playwright...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    except Exception as e:
        print(f"❌ Greška pri instalaciji browsera: {e}")

install_packages()

# --- SETTINGS ---
URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

def human_sleep(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

# --- SCRAPING ---
def scrape_debug():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=MOBILE_UA,
            viewport={"width": 412, "height": 915},
            locale="sr-RS"
        )
        page = context.new_page()
        print("➡️ Otvaram Mozzart...")
        page.goto(URL, timeout=60000)
        human_sleep(5, 8)

        # pokušaj zatvaranja kolačića ako postoji
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1,2)
        except:
            pass

        # klikni sve "Učitaj još"
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2,4)
            except:
                break

        print("✅ Svi mečevi učitani. Parsiram...")

        # dohvat svih mečeva (ispod "Ishod meča")
        matches_elements = page.query_selector_all("div.coupon-row__content")
        print(f"🔹 Pronađeno {len(matches_elements)} mečeva na stranici.\n")

        for idx, el in enumerate(matches_elements, start=1):
            try:
                date_time = el.query_selector("div.coupon-row__date")
                league = el.query_selector("div.coupon-row__league")
                home = el.query_selector("div.coupon-row__team--home")
                away = el.query_selector("div.coupon-row__team--away")

                date_time_txt = date_time.inner_text().strip() if date_time else "N/A"
                league_txt = league.inner_text().strip() if league else "N/A"
                home_txt = home.inner_text().strip() if home else "N/A"
                away_txt = away.inner_text().strip() if away else "N/A"

                print(f"{idx}. {date_time_txt} | {league_txt} | {home_txt} vs {away_txt}")
            except Exception as e:
                print(f"❌ Greška kod meča {idx}: {e}")

        browser.close()
        print("\n🎯 Debug scraping završен.")

if __name__ == "__main__":
    scrape_debug()
