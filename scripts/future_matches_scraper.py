from playwright.sync_api import sync_playwright
import os
import time
import random

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
OUTPUT_DIR = "output"

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

def human_sleep(min_sec=3, max_sec=6):
    time.sleep(random.uniform(min_sec, max_sec))

def debug_scrape():
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

        # kolačići
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1, 2)
        except:
            pass

        # scroll da se sve učita
        for _ in range(12):
            page.evaluate("window.scrollBy(0, 800)")
            human_sleep(1, 2)

        # snimi HTML
        html = page.content()
        with open(os.path.join(OUTPUT_DIR, "page.html"), "w", encoding="utf-8") as f:
            f.write(html)

        # snimi vidljivi tekst
        text = page.inner_text("body")
        with open(os.path.join(OUTPUT_DIR, "page_text.txt"), "w", encoding="utf-8") as f:
            f.write(text)

        # screenshot
        page.screenshot(path=os.path.join(OUTPUT_DIR, "screenshot.png"), full_page=True)

        browser.close()

    print("✅ DEBUG snimanje gotovo")

if __name__ == "__main__":
    debug_scrape()
