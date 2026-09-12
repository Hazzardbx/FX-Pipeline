import requests
import pandas as pd
import time
import os
import psycopg2 # pyright: ignore[reportMissingModuleSource] #runs in docker container, need to install psycopg2-binary in requirements.txt
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger # CronTrigger = can specify a time and date to run the job
#runs in docker container, need to install APScheduler in requirements.txt

#Source of API: https://docs.apilayer.com/exchangeratesapi/docs/api-documentation
#APScheduler docs: https://apscheduler.com/#how%20it%20works


def run_pipeline():
    ## EXTRACT -------------------------------------------------------------------------------------

    url = "https://api.frankfurter.dev/v2/rates"
    params = {"from": "2024-01-01", "base": "EUR", "quotes": "USD,GBP,JPY,CHF,CNY"}

    for i in range(5):
        response = requests.get(url, params=params)
        if response.status_code == 200: #200 = success
            break
        elif response.status_code >= 400 and response.status_code < 500:
            print(f"Error: {response.status_code}")
            break
        elif response.status_code >= 500 and response.status_code < 600:
            print(f"Server error, retrying...[{i}]")
            time.sleep(2 ** i) # exponential backoff
        else:
            print("No errors")

    if response.status_code != 200:
        print(f"Failed to fetch data after {i+1} attempts. Status code: {response.status_code}")
        return # exit the function without terminating the entire script

    xchangerate = []
    for curr in response.json():
        daily_rate = {
            "date": curr['date'],
            "base": curr['base'],
            "quote": curr['quote'],
            "rate":  curr['rate']
        }
        xchangerate.append(daily_rate)

    df = pd.DataFrame(xchangerate)
    print(df)

    ## TRANSFORM -------------------------------------------------------------------------------------

    df['date'] = pd.to_datetime(df['date']) # convert date column to datetime format

    if df.isnull().values.any():
        nulls = df.isnull().sum()
        print(f"Data contains null values in {nulls[nulls > 0].index.tolist()}.")
        df.dropna(subset=['date','base','quote','rate'], inplace=True) # subset = columns to check for null values, inplace = not return a new df
        print(f"Null values removed from columns: {nulls[nulls > 0].index.tolist()}.")

    ## LOAD -------------------------------------------------------------------------------------

    create_table_query = """
    create table if NOT EXISTS xchange_rates (
        date DATE not null,
        base varchar(3) not null,
        quote varchar(3) not null,
        rate decimal(10, 6) not null,
        primary key (date, base, quote),
        ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
        )
    """

    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST"),
            database=os.environ.get("POSTGRES_DB"),
            user=os.environ.get("POSTGRES_USER"),
            password=os.environ.get("POSTGRES_PASSWORD")
        )
        print("Connected to the database successfully.")

    except Exception as e:
        print(f"Error connecting to the database: {e}")

    #cursor creates a channel to the DB that allows to send commands and receive results.
    cur = conn.cursor()
    cur.execute(create_table_query)
    conn.commit()

    # ON CONFLICT: if a row with the same date/base/quote already exists, update the rate instead of inserting a duplicate.
    # This is what makes re-running the pipeline safe (idempotent).
    for index, row in df.iterrows():
        cur.execute("INSERT INTO xchange_rates (date, base, quote, rate, ingested_at) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP) ON CONFLICT (date, base, quote) DO UPDATE SET rate = EXCLUDED.rate, ingested_at = EXCLUDED.ingested_at", (row['date'], row['base'], row['quote'], row['rate']))

    conn.commit()
    cur.close()
    conn.close()

run_pipeline()

## ORCHESTRATE -------------------------------------------------------------------------------------
# Runs automatically on weekdays via APScheduler.

def run_daily():
    trigger = CronTrigger(hour=17, minute=0, day_of_week='mon-fri', timezone='Europe/Berlin')
    scheduler = BlockingScheduler()
    scheduler.add_job(run_pipeline, trigger=trigger)
    scheduler.start()

if __name__ == "__main__":
    run_daily()

## SERVE -------------------------------------------------------------------------------------
# See serve/app.py — Streamlit app answering business questions on the data
# (price change, volatility, trend, correlation).
