from playwright.sync_api import sync_playwright
import time

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
LINES_TO_SHOW = 300  # koliko linija teksta želimo da vidimo

def inspect_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # headless jer nema X server
        context = browser.new_context(
            viewport={"width": 412, "height": 915},  # mobilni viewport
            locale="sr-RS",
        )
        page = context.new_page()
        page.goto(URL, timeout=60000)
        time.sleep(5)  # sačekaj da se svi mečevi učitaju

        # klikni na "Učitaj još" dok se više ne učitava
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                time.sleep(2)
            except:
                break

        # uzmi sav tekst sa body
        full_text = page.inner_text("body")

        # podeli po linijama i prikaži prvih n linija
        lines = full_text.splitlines()
        for i, line in enumerate(lines[:LINES_TO_SHOW]):
            print(f"{i+1:03d}: {line}")

        print(f"\nUkupno linija na stranici: {len(lines)}")
        browser.close()

if __name__ == "__main__":
    inspect_page()
