from playwright.sync_api import sync_playwright
import time

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

def inspect_lines():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # headless=True jer nema X server
        context = browser.new_context(
            user_agent=MOBILE_UA,
            viewport={"width": 412, "height": 915},
            locale="sr-RS"
        )
        page = context.new_page()
        page.goto(URL, timeout=60000)
        time.sleep(5)  # malo sačekamo da se stranica učita

        text = page.inner_text("body")
        browser.close()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    # Prikaz linija od 280 do 700
    for idx, line in enumerate(lines[280:700], start=280):
        print(f"{idx}: {line}")

if __name__ == "__main__":
    inspect_lines()
