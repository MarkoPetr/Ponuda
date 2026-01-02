import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime, timedelta

OUTPUT_FILE = "output/future_matches.xlsx"

# Mapa dana u nedelji na engleski/Playwright tekstualni oblik
DAYS_MAP = {"Pon": 0, "Uto": 1, "Sre": 2, "Čet": 3, "Pet": 4, "Sub": 5, "Ned": 6}

def next_weekday(weekday: int):
    """Vrati prvi naredni datum od danas za dati weekday (0=ponedeljak, 6=nedelja)."""
    today = datetime.now().date()
    days_ahead = weekday - today.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)

def parse_match_date(date_str: str):
    """Parsira datum: pun datum 'dd.mm.yyyy' ili samo dan 'Pet 15:00'."""
    date_str = date_str.strip()
    if "." in date_str:  # dd.mm.yyyy
        try:
            return datetime.strptime(date_str, "%d.%m.%Y").date()
        except:
            return None
    else:  # samo dan
        day_abbr = date_str.split()[0]
        weekday = DAYS_MAP.get(day_abbr)
        if weekday is not None:
            return next_weekday(weekday)
    return None

async def scrape_mozzart():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("➡️ Otvaram Mozzart...")
        await page.goto("https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days", timeout=60000)

        # Scroll do kraja stranice
        previous_height = None
        while True:
            current_height = await page.evaluate("document.body.scrollHeight")
            if previous_height == current_height:
                break
            previous_height = current_height
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)  # sačekaj učitavanje novih mečeva

        print("✅ Svi mečevi učitani. Parsiram...")

        matches = []
        current_league = None

        # Selektuj sve blokove (liga nazivi + mečevi)
        elements = await page.query_selector_all("div[class*='event-block'], div[class*='competition-header']")
        for el in elements:
            text = (await el.inner_text()).strip()
            if not text:
                continue
            # Liga
            if "Liga" in text or "Šampiona" in text or "Evrope" in text or "Premijer" in text:
                current_league = text
            else:
                # Meč red
                lines = [l for l in text.split("\n") if l.strip()]
                if len(lines) >= 2:
                    # Prvi deo može biti datum/dan+vreme
                    date_info = lines[0]
                    match_time = None
                    try:
                        match_time = datetime.strptime(date_info[-5:], "%H:%M").time()
                    except:
                        match_time = None
                    match_date = parse_match_date(date_info)
                    if match_date and match_time and len(lines) >= 3:
                        home = lines[1].strip()
                        away = lines[2].strip()
                        matches.append({
                            "Datum": match_date.strftime("%d.%m.%Y"),
                            "Vreme": match_time.strftime("%H:%M"),
                            "Liga": current_league,
                            "Domacin": home,
                            "Gost": away
                        })

        await browser.close()
        print(f"🔹 Pronađeno {len(matches)} mečeva na stranici.")

        if matches:
            df = pd.DataFrame(matches)
            df.to_excel(OUTPUT_FILE, index=False)
            print(f"✅ Sačuvano {len(matches)} mečeva u {OUTPUT_FILE}")
        else:
            print("⚠️ Nema mečeva za sačuvati.")

if __name__ == "__main__":
    asyncio.run(scrape_mozzart())
