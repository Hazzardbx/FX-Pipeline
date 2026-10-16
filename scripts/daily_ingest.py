import os
import sys
import time #added 16/10/26 - for exponential backoff


import requests
import pandas as pd
import psycopg2
from datetime import datetime, timedelta

# Get last date in DB
conn = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST"),
    port=5432,
    database=os.environ.get("POSTGRES_DATABASE"),
    user=os.environ.get("POSTGRES_USER"),
    password=os.environ.get("POSTGRES_PASSWORD"),
)
cursor = conn.cursor()
cursor.execute("SELECT MAX(date) FROM xchange_rates;")

last_date = cursor.fetchone()[0]
today = datetime.now().strftime("%Y-%m-%d")


if last_date is None:
    start_date = "2024-01-01"
else:
    start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d") 

if start_date > today:
   print("Already up to date, nothing to ingest")
   cursor.close()
   conn.close()
   sys.exit(0)

# Fetch new data from API

url = f"https://api.frankfurter.app/{start_date}..{today}?base=EUR&symbols=USD,GBP,JPY,CHF,CNY"

response = None
last_error = None
for i in range(5):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        break
    except requests.exceptions.RequestException as e:
        last_error = e
        print(f"Attempt {i} failed: {e}")
        time.sleep(2 ** i)  # exponential backoff
else:
    raise RuntimeError(f"Failed to fetch data from API after 5 attempts. Last error: {last_error}")
#added 16/10/26 - raises an error if the API request fails after 5 attempts, with the status code of the last attempt.

data = response.json()  
    
# Transform and load
rows = 0
for date_str, rates in data.get("rates", {}).items():
    for quote, rate in rates.items():
        cursor.execute("""
            INSERT INTO xchange_rates (date, base, quote, rate)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (date, base, quote) DO UPDATE SET rate = %s;
        """, (date_str, "EUR", quote, float(rate), float(rate)))
        rows += 1
if rows == 0:
    print(f"ERROR: API returned no rates for {start_date} -> {today}")
    cursor.close()
    conn.close()
    sys.exit(1)

conn.commit()
cursor.close()
conn.close()
print(f"✓ Daily ingest complete ({rows} rows upserted, {start_date} -> {today})")