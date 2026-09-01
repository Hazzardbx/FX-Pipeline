import sys

import requests
import pandas as pd
import time

#Source of api and documentation
#https://docs.apilayer.com/exchangeratesapi/docs/api-documentation?utm_source=ExchangeratesAPIHomePage&utm_medium=Referral

#API
url = "https://api.frankfurter.dev/v2/rates"

# params = {"base": "EUR", "quotes": "USD", "from": "2026-01-01", "to": "2026-01-05"}
# params = {"from": "2026-01-01", "base": "EUR", "quotes": "USD"}
params = {"from": "2026-01-01", "base": "EUR", "quotes": "XXX"}


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

rate = response.json()[0]["rate"]

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