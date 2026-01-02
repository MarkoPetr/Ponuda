import re
import pandas as pd

# --- Ovde ubaciš ceo sirovi tekst sa sajta ---
raw_text = """
OVDE IDE TVOJ TEKST SA MOZZARTA
"""

# Regularni izrazi za datum, vreme i dan
date_pattern = re.compile(r'(\d{2}\.\d{2}\.)')       # npr. 20.01.
time_pattern = re.compile(r'(\d{2}:\d{2})')         # npr. 17:45
day_pattern = re.compile(r'(Pon|Uto|Sre|Čet|Pet|Sub|Ned)')  # dan u nedelji
league_pattern = re.compile(r'([A-ZŠĐČĆŽa-zšđčćž0-9\s]+)') # ime lige

lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

matches = []
current_date = None
current_league = None
i = 0
while i < len(lines):
    line = lines[i]

    # --- Datum i vreme ---
    date_match = re.match(r'(\d{2}\.\d{2}\.)\s*(\w+)?\s*(\d{2}:\d{2})?', line)
    if date_match:
        current_date = date_match.group(1)
        current_day = date_match.group(2)
        current_time = date_match.group(3)
        if current_time is None and i+1 < len(lines):
            # moguće da je vreme u sledećoj liniji
            next_line_time = re.match(time_pattern, lines[i+1])
            if next_line_time:
                current_time = next_line_time.group(1)
                i += 1
        i += 1
        # Sada očekujemo ligu i timove
        if i < len(lines):
            current_league = lines[i]
            i += 1
        if i+1 < len(lines):
            home = lines[i]
            away = lines[i+1]
            matches.append({
                'Datum': current_date,
                'Vreme': current_time,
                'Liga': current_league,
                'Home': home,
                'Away': away
            })
            i += 2
        continue

    # --- Linija sa danom u nedelji i vremenom (koristi prethodni datum) ---
    day_time_match = re.match(r'(Pon|Uto|Sre|Čet|Pet|Sub|Ned)\s*(\d{2}:\d{2})', line)
    if day_time_match and current_date is not None:
        current_time = day_time_match.group(2)
        # Sada očekujemo ligu i timove
        if i < len(lines):
            current_league = lines[i]
            i += 1
        if i+1 < len(lines):
            home = lines[i]
            away = lines[i+1]
            matches.append({
                'Datum': current_date,
                'Vreme': current_time,
                'Liga': current_league,
                'Home': home,
                'Away': away
            })
            i += 2
        continue

    i += 1

# --- Kreiranje DataFrame i CSV ---
df = pd.DataFrame(matches)
df.to_csv("mecevi.csv", index=False, encoding="utf-8-sig")
print(df)
