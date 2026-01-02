from playwright.sync_api import sync_playwright
import os
import time
import random

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
OUTPUT_DIR = "debug_output"

def human_sleep(a=2, b=4):
    time.sleep(random.uniform(a, b))

def scrape_everything():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            viewport={"width": 412, "height": 915},
            locale="sr-RS"
        )

        page = context.new_page()
        page.goto(URL, timeout=60000)
        human_sleep(5, 8)

        # pokušaj zatvaranja kolačića
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            human_sleep(1, 2)
        except:
            pass

        # učitaj sve mečeve
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                human_sleep(2, 4)
            except:
                break

        # 🔴 UZIMAMO SVE
        full_text = page.inner_text("body")
        full_html = page.content()

        browser.close()

    # snimanje
    with open(os.path.join(OUTPUT_DIR, "page_text.txt"), "w", encoding="utf-8") as f:
        f.write(full_text)

    with open(os.path.join(OUTPUT_DIR, "page_html.html"), "w", encoding="utf-8") as f:
        f.write(full_html)

    print("✅ Gotovo")
    print("📄 Sačuvano:")
    print("- debug_output/page_text.txt")
    print("- debug_output/page_html.html")

if __name__ == "__main__":
    scrape_everything()
