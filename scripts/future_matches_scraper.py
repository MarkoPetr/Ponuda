from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# --- Podešavanja za Chrome ---
chrome_options = Options()
chrome_options.add_argument("--headless")  # ukloni ako hoćeš da vidiš browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# Putanja do chromedrivera
service = Service("/path/to/chromedriver")  # promeni na tvoju putanju

driver = webdriver.Chrome(service=service, options=chrome_options)

# Otvori stranicu sa budućim mečevima
driver.get("https://www.mozzartbet.com/sr/sport/fudbal/najava")  # promeni URL ako treba

# Sačekaj da se mečevi učitaju (do 20 sekundi)
wait = WebDriverWait(driver, 20)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.upcoming-match")))  # primer selektora

# Skroluj malo da se svi učitaju (ako ima infinite scroll)
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Prikupljanje podataka
matches = []
match_elements = driver.find_elements(By.CSS_SELECTOR, "div.upcoming-match")  # primer selektora

for meč in match_elements:
    try:
        date = meč.find_element(By.CSS_SELECTOR, ".match-date").text
        time_ = meč.find_element(By.CSS_SELECTOR, ".match-time").text
        league = meč.find_element(By.CSS_SELECTOR, ".match-league").text
        home = meč.find_element(By.CSS_SELECTOR, ".home-team").text
        away = meč.find_element(By.CSS_SELECTOR, ".away-team").text
        matches.append({
            "Datum": date,
            "Vreme": time_,
            "Liga": league,
            "Home": home,
            "Away": away
        })
    except:
        continue

driver.quit()

# Spremi u CSV
df = pd.DataFrame(matches)
df.to_csv("future_matches.csv", index=False)
print(df)
