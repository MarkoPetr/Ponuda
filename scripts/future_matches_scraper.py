from playwright.sync_api import sync_playwright

URL = "https://www.mozzartbet.com/sr/kladjenje/sport/1?date=all_days&sort=bytime"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # headless=False da vidiš browser
    context = browser.new_context()
    page = context.new_page()
    page.goto(URL, timeout=60000)

    # čekamo da se učita sadržaj
    page.wait_for_timeout(5000)

    # prikaz celog teksta stranice
    full_text = page.inner_text("body")
    print(full_text)

    browser.close()
