from playwright.sync_api import sync_playwright
import os

os.makedirs("output", exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days")
    
    # Čekamo da se svi mečevi učitaju, recimo 5s
    page.wait_for_timeout(5000)

    # Snimamo ceo HTML
    html_content = page.content()
    with open("output/debug_full_page.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ Debug HTML sačuvan u output/debug_full_page.html")
    browser.close()
