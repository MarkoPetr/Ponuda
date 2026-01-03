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
        browser = p.chromium.launch(headless=False)  # headless=False da vidimo stranicu
        context = browser.new_context(
            user_agent=MOBILE_UA,
            viewport={"width": 412, "height": 915},
            locale="sr-RS"
        )
        page = context.new_page()
        page.goto(URL, timeout=60000)
        time.sleep(8)  # čekamo da se svi mečevi učitaju

        # klik na "Učitaj još" dok postoji
        while True:
            try:
                page.click("text=Učitaj još", timeout=3000)
                time.sleep(2)
            except:
                break

        # pronađemo sve elemente koji izgledaju kao naziv lige
        league_elements = page.query_selector_all("div")  # prvo sve div-ove
        print("===== POTENCIJALNI NAZIVI LIGA =====")
        for el in league_elements:
            text = el.inner_text().strip()
            if len(text) > 0 and len(text) < 50:  # filtriramo preduge tekstove
                # opcionalno možemo tražiti "liga", "šampiona", "evrope" itd. da su relevantni
                if "Liga" in text or "liga" in text or "Superkup" in text or "kup" in text:
                    print("===", text, "===")
        browser.close()

if __name__ == "__main__":
    inspect_leagues()
