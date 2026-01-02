name: Mozzart Scraper Debug

on:
  workflow_dispatch: # ručno pokretanje

jobs:
  scrape:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pandas playwright
          playwright install chromium

      - name: Run future matches debug
        run: |
          python scripts/future_matches_debug.py
