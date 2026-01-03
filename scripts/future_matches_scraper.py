from playwright.sync_api import sync_playwright
import pandas as pd
import re
from datetime import datetime

URL = "https://www.mozzartbet.com/sr/kladjenje"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(5000)

        text = page.inner_text("body")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        browser.close()

    matches = []
    current_league = None
    i = 0

    date_re = re.compile(r"\d{2}\.\d{2}\.\s+\w+\s+\d{2}:\d{2}")

    while i < len(lines):
        line = lines[i]

        # PREPOZNAVANJE LIGE
        if (
            line.lower().startswith(("liga ", "engleska", "španija", "italija", "nemačka",
                                      "francuska", "portugalija", "afrika", "holandija",
                                      "australija", "saudijska", "egipat", "turska",
                                      "grčka", "škotska", "izrae", "katar", "kipar",
                                      "meksiko", "oman", "uae", "vels", "tajland"))
            and len(line) < 40
        ):
            current_league = line
            i += 1
            continue

        # PREPOZNAVANJE MEČA
        if date_re.match(line):
            try:
                dt = datetime.strptime(line, "%d.%m. %a %H:%M")
                date = dt.strftime("%d.%m.%Y")
                time = dt.strftime("%H:%M")

                home = lines[i + 1]
                away = lines[i + 2]

                matches.append({
                    "Datum": date,
                    "Vreme": time,
                    "Liga": current_league,
                    "Domacin": home,
                    "Gost": away
                })

                i += 3
                continue
            except:
                pass

        i += 1

    df = pd.DataFrame(matches)
    df.to_excel("output/future_matches.xlsx", index=False)
    print(f"✅ Sačuvano {len(df)} mečeva")

if __name__ == "__main__":
    scrape()
