# import sys
import requests
import pandas as pd
import time
import os
import psycopg2 #runs in docker container, need to install psycopg2-binary in requirements.txt
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger # CronTrigger = can specify a time and date to run the job
#runs in docker container, need to install APScheduler in requirements.txt

#Source of api and documentation
#https://docs.apilayer.com/exchangeratesapi/docs/api-documentation?utm_source=ExchangeratesAPIHomePage&utm_medium=Referral
#APScheduler guide: https://betterstack.com/community/guides/scaling-python/apscheduler-scheduled-tasks/
#APScheduler how it works: https://apscheduler.com/#how%20it%20works

def run_pipeline():
    ## EXTRACT

    #API
    url = "https://api.frankfurter.dev/v2/rates"

    # params = {"base": "EUR", "quotes": "USD", "from": "2026-01-01", "to": "2026-01-05"}
    # params = {"from": "2026-01-01", "base": "EUR", "quotes": "XXX"} - # test for error handling
    # params = {"from": "2026-01-01", "base": "EUR", "quotes": "USD"}
    params = {"from": "2024-01-01" , "base": "EUR", "quotes": "USD,GBP,JPY,CHF,CNY"}


    for i in range(5):
        response = requests.get(url, params=params)
        if response.status_code == 200: #200 = success
            break
        elif response.status_code >= 400 and response.status_code < 500:
            print(f"Error: {response.status_code}")
            break
        elif response.status_code >= 500 and response.status_code < 600:
            print(f"Server error, retrying...[{i}]")
            time.sleep(2 ** i)
    # Wait for i seconds before retrying
        else: print("No errors")    
        
    if response.status_code != 200:
        print(f"Failed to fetch data after {i+1} attempts. Status code: {response.status_code}")
        # sys.exit(1) # 1 = error exit code (0 = success, other number = failure)
        return # exit the function without terminating the entire script


    # print(response.json())

    # rate = response.json()[0]["rate"] # test leftover: used to test the first rate, replaced by loop -> xchangerate

    # print(rate)

    xchangerate = []

    # for curr in response.json()[:10]: - test leftover: used to test the first 10 rates, removed "[:10]" 
    for curr in response.json():
        daily_rate = {
            "date": curr['date'],
            "base": curr['base'],
            "quote": curr['quote'],
            "rate":  curr['rate']
        } 
        xchangerate.append(daily_rate)
        # print(f"{curr['date']} - {curr['base']} to {curr['quote']}: {curr['rate']}"),
    
    df = pd.DataFrame(xchangerate)


    print(df)


    # append to df -> save -> export
    # add calculator to convert
    # connect to database

    ## TRANSFORM
    
    df['date'] = pd.to_datetime(df['date']) # convert date column to datetime format
    # print(df.dtypes)

    # df['base'][2] = ' ' 
    # df.loc[2, 'base'] = None # test for null values in base column

    if df.isnull().values.any():
        nulls = df.isnull().sum()
        print(f"Data contains null values in {nulls[nulls > 0].index.tolist()}.") 
        null_rows = df[df.isnull().any(axis=1)] # for debugging, to see which rows contain null values
        df.dropna(subset=['date','base','quote','rate'], inplace=True) # subset = columns to check for null values, inplace = not return a new df
        print(f"Null values removed from columns: {nulls[nulls > 0].index.tolist()} and added to null_rows variable for debugging.")

    ## LOAD
    #1.preparing Postgres via docker compose (DONE)
    #2. docker compose up. What it does reminder: "Starts the services defined in the docker-compose.yml file, creating containers as needed." (DONE)
    #3.write Python code to connect to postgres and insert data into a table. use: (insert .. on conflict), in case of duplicates or if job runs 2x. (DONE)

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

    #reminder: after connecting to the DB, create a cursor object to execute SQL queries (DONE)
    #cursor creates a channel to the DB that allows to send commands and receive results. 
    cur = conn.cursor()
    cur.execute(create_table_query)
    conn.commit() #commit the changes to the db
    # cur.close() 


    #insert data into table:
    for index, row in df.iterrows():
        cur.execute("INSERT INTO xchange_rates (date, base, quote) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP) ON CONFLICT (date, base, quote, ingested_at) DO UPDATE SET rate = EXCLUDED.rate, ingested_at = EXCLUDED.ingested_at", (row['date'], row['base'], row['quote'], row['rate']))
        #Insert with ON CONFLICT clause to handle duplicates. If a row with the same date, base, and quote already exists, it will update the rate instead of inserting a new row.
        
    # rate = EXCLUDED.rate replaces the value inside   
    # ON CLONFLICT (columns) = if there's a value in the columns that already exists then it updates.
    # DO UPDATE SET rate = EXCLUDED.rate = update the rate column with the new value from the insert statement.
        
    conn.commit() # commit the changes to the db
    cur.close() # close the cursor to free up resources
    conn.close() # close the connection to the db

run_pipeline()

## ORCHESTRATE the service
#run daily and automatically. 
#

def run_daily():
    from datetime import datetime, timedelta
    now_plus_1 = datetime.now() + timedelta(minutes=1)
    trigger = CronTrigger(hour=now_plus_1.hour, minute=now_plus_1.minute, timezone='Europe/Lisbon') # 1min later testing
    
    
    # trigger = CronTrigger(hour=17, minute=0, day_of_week='mon-fri', timezone='Europe/Berlin')  # Run daily at 5 PM CET (17:00) on weekdays
    #Already ran script with hardcoded time to test. test = OK
    scheduler = BlockingScheduler()
    scheduler.add_job(run_pipeline, trigger=trigger)
    scheduler.start()

run_daily()

#Still need to make sure this runs in the background when I close Docker Desktop. []

## SERVE - show the results
#streamlit app - business questions on the data (ex. most volatile pair, day-over-day change, trend over time)

