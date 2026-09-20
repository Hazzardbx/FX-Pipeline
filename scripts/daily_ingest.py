import requests
import pandas as pd
import psycopg2
import os
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

if last_date is None:
    start_date = "2024-01-01"
else:
    start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d") 

# Fetch new data from API
today = datetime.now().strftime("%Y-%m-%d")
url = f"https://api.frankfurter.app/{start_date}..{today}?base=EUR&symbols=USD,GBP,JPY,CHF,CNY"
response = requests.get(url)
data = response.json()
    
# Transform and load
for date_str, rates in data.get("rates", {}).items():
    for quote, rate in rates.items():
        cursor.execute("""
            INSERT INTO xchange_rates (date, base, quote, rate)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (date, base, quote) DO UPDATE SET rate = %s;
        """, ("EUR", quote, float(rate), float(rate)))

conn.commit()
cursor.close()
conn.close()
print("✓ Daily ingest complete")