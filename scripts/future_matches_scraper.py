from playwright.sync_api import sync_playwright
import time
import random

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

def human_sleep(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def inspect_page_lines():
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

        # pokušaj učitavanja svih mečeva
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2, 4)
            except:
                break

        # uzmi sav tekst
        text = page.inner_text("body")
        browser.close()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    print(f"Ukupno linija na stranici: {len(lines)}\n")
    
    # prikaži prvih 1000 linija sa brojem linije
    for idx, line in enumerate(lines[:1000]):
        print(f"{idx+1}: {line}")

if __name__ == "__main__":
    inspect_page_lines()
