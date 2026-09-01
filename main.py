import sys

import requests
import pandas as pd
import time

#Source of api and documentation
#https://docs.apilayer.com/exchangeratesapi/docs/api-documentation?utm_source=ExchangeratesAPIHomePage&utm_medium=Referral


## EXTRACT

#API
url = "https://api.frankfurter.dev/v2/rates"

# params = {"base": "EUR", "quotes": "USD", "from": "2026-01-01", "to": "2026-01-05"}
params = {"from": "2026-01-01", "base": "EUR", "quotes": "USD"}
# params = {"from": "2026-01-01", "base": "EUR", "quotes": "XXX"} - # test for error handling


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
    sys.exit(1) # 1 = error exit code (0 = success, other number = failure)


# print(response.json())

# rate = response.json()[0]["rate"] # test leftover: used to test the first rate, replaced by loop -> xchangerate

# print(rate)

xchangerate = []

for curr in response.json()[:10]:
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
    df.dropna(subset=['date','base','quote','rate'], inplace=True) # subset = columns to check for null values, inplace = modify df in place
    print(f"Null values removed from columns: {nulls[nulls > 0].index.tolist()} and added to null_rows variable for debugging.")
    