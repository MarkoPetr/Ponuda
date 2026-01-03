from playwright.sync_api import sync_playwright
import time

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-A166B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

def inspect_leagues():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # headless: True
        context = browser.new_context(
            user_agent=MOBILE_UA,
            viewport={"width": 412, "height": 915},
            locale="sr-RS"
        )
        page = context.new_page()
        page.goto(URL, timeout=60000)
        time.sleep(5)  # malo čekanja da se učita sadržaj

        # zatvori kolačiće ako postoje
        try:
            page.click("text=Sačuvaj i zatvori", timeout=5000)
            time.sleep(1)
        except:
            pass

        # učitaj sve mečeve
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                time.sleep(2)
            except:
                break

        # uzmi tekst sa stranice
        text = page.inner_text("body")

        # splituj po linijama
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        print("=== MOGUĆI NAZIVI LIGA ===")
        for i, line in enumerate(lines):
            # prepoznaj liniju "Default Competition flag" i liniju ispod
            if "Default Competition flag" in line:
                if i + 1 < len(lines):
                    liga = lines[i + 1]
                    print(liga)

        browser.close()

if __name__ == "__main__":
    inspect_leagues()
