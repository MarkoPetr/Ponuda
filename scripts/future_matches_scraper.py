import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from playwright.async_api import async_playwright

# Folder za output
output_folder = Path("output")
output_folder.mkdir(exist_ok=True)
output_file = output_folder / "future_matches.xlsx"

# Mapa za dane
DAYS = {
    "pon": 0,
    "uto": 1,
    "sre": 2,
    "čet": 3,
    "pet": 4,
    "sub": 5,
    "ned": 6
}

def next_weekday_date(day_name):
    today = datetime.now().date()
    target = DAYS[day_name.lower()]
    days_ahead = (target - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)

async def scrape_mozzart():
    url = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        print("➡️ Otvaram Mozzart...")
        await page.goto(url)
        await page.wait_for_timeout(5000)  # čekanje da se učita JS

        # Pokušaj klik "Load more" dok postoji
        while True:
            try:
                load_more = await page.query_selector("button:has-text('Učitaj još')")
                if not load_more:
                    break
                await load_more.click()
                await page.wait_for_timeout(2000)
            except:
                break

        print("✅ Svi mečevi učitani. Parsiram...")

        # Parsiranje mečeva
        matches = await page.query_selector_all("div[class*='event-row']")
        for m in matches:
            text = await m.inner_text()
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            # Datum i vreme
            datum = ""
            vreme = ""
            if lines:
                first = lines[0].lower()
                if any(day in first for day in DAYS):
                    # Primer: Sub 15:00
                    day_name, vreme = first.split()[:2]
                    datum = next_weekday_date(day_name).strftime("%d.%m.%Y")
                elif "." in first:
                    # Primer: 20.01. Uto 15:30
                    parts = first.split()
                    datum = parts[0] + ".2026"  # dodaje godinu
                    vreme = parts[-1]

            # Domaćin i Gost
            if len(lines) >= 3:
                domacin = lines[1]
                gost = lines[2]
                results.append({
                    "Datum": datum,
                    "Vreme": vreme,
                    "Liga": "",  # Mozzart ne daje lako ligu
                    "Domacin": domacin,
                    "Gost": gost
                })

        await browser.close()

    # Excel
    if results:
        df = pd.DataFrame(results)
        df.to_excel(output_file, index=False)
        print(f"✅ Sačuvano {len(results)} mečeva u {output_file}")
    else:
        print("⚠️ Nema mečeva za sačuvati.")

if __name__ == "__main__":
    asyncio.run(scrape_mozzart())
