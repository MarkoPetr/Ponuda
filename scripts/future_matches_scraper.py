from playwright.sync_api import sync_playwright
import time

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"

def inspect_leagues():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # otvara browser da vidimo sta se desava
        context = browser.new_context(
            viewport={"width": 1200, "height": 800},  # desktop velicina
            locale="sr-RS"
        )
        page = context.new_page()
        page.goto(URL, timeout=60000)
        time.sleep(8)  # sačekamo da se JS izvrši i učita stranica

        # Pokusaj da uzmemo sve elemente koji imaju ligu
        league_elements = page.locator("text=/.*Liga.*/").all()  # regex za text koji sadrži "Liga"
        
        print(f"Pronađeno {len(league_elements)} mogućih liga (uzorak do 3):\n")
        for i, el in enumerate(league_elements[:3]):  # samo prva 3 da vidimo pattern
            print(f"--- Liga {i+1} ---")
            # ispisujemo innerHTML da vidimo sve oko naziva
            html = el.inner_html()
            text = el.inner_text()
            print("INNER HTML:")
            print(html)
            print("INNER TEXT:")
            print(text)
            print("\n\n")

        browser.close()

if __name__ == "__main__":
    inspect_leagues()
