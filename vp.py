import requests
import csv
import time
from collections import defaultdict, OrderedDict
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
from urllib.parse import quote
from io import StringIO

OPEN_WEIGHT = 0.25
HIGH_WEIGHT = 0.2
MID_WEIGHT = 0.1
LOW_WEIGHT = 0.2
CLOSE_WEIGHT = 0.25

def fetch_data_av(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}&outputsize=full&datatype=csv"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return list(csv.reader(response.text.splitlines()))[1:]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
    
def fetch_data_crypto(symbol):
    url = f"https://www.cryptodatadownload.com/cdd/Bitstamp_{quote(symbol.upper(), safe='')}USD_d.csv"
    
    try:
        print(f"Fetching data from: {url}")
        
        response = requests.get(url)
        response.raise_for_status()
        
        csv_data = StringIO(response.text)
        
        df = pd.read_csv(csv_data, skiprows=1)
     
        df['date'] = pd.to_datetime(df['date']).dt.date.astype(str)
        
        # Normalize the data set
        result = df[['date', 'open', 'high', 'low', 'close', 'Volume USD']]
        
        # Convert DataFrame to list of lists
        array_format = result.values.tolist()
        
        return array_format

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
    except pd.errors.ParserError as e:
        print(f"Error parsing CSV: {e}")
        return []
    

def calculate_volume_by_price(rows):
    price_dict = defaultdict(int)

    for row in rows:
        try:
            volume = int(row[5])

            open_price = float(row[1])
            high_price = float(row[2])
            low_price = float(row[3])
            close_price = float(row[4])
            mid_price = (high_price - low_price) / 2

            price_dict[open_price] += int(volume * OPEN_WEIGHT)
            price_dict[high_price] += int(volume * HIGH_WEIGHT)
            price_dict[mid_price] += int(volume * MID_WEIGHT)
            price_dict[low_price] += int(volume * LOW_WEIGHT)
            price_dict[close_price] += int(volume * CLOSE_WEIGHT)

        except ValueError:
            continue

    return price_dict

def calculate_monthly_changes(rows):
    monthly_data = defaultdict(list)

    for row in rows:
        try:
            date = datetime.strptime(row[0], "%Y-%m-%d")
            open_price = float(row[1])
            close_price = float(row[4])

            month_key = date.strftime("%Y-%m")
            monthly_data[month_key].append((date, open_price, close_price))

        except ValueError:
            continue

    monthly_changes = defaultdict(float)

    for month_key, entries in monthly_data.items():
        entries.sort(key=lambda x: x[0])
        first_day_open = entries[0][1]
        last_day_close = entries[-1][2]
        monthly_changes[month_key] = last_day_close - first_day_open

    aggregated_changes = defaultdict(list)

    for month_key, change in monthly_changes.items():
        month = month_key.split("-")[1]
        aggregated_changes[month].append(change)

    average_monthly_changes = {
        month: sum(changes) / len(changes)
        for month, changes in aggregated_changes.items()
    }

    return average_monthly_changes

def calculate_daily_percentage_changes(rows):
    yearly_data = defaultdict(list)

    year_end = datetime.strptime(rows[0][0], "%Y-%m-%d").year
    year_start = datetime.strptime(rows[len(rows)-1][0], "%Y-%m-%d").year

    for row in rows:
        try:
            date = datetime.strptime(row[0], "%Y-%m-%d")
            close_price = float(row[4])
            year_key = date.year
              # Only append if it's not the first or last item
            if year_key != year_end and year_key != year_start:
                yearly_data[year_key].append((date, close_price))

        except ValueError:
            continue

    daily_percentage_changes = {}

    for year, entries in yearly_data.items():
        entries.sort(key=lambda x: x[0])
        first_day_close = entries[0][1]

        daily_changes = [
            ((close - first_day_close) / first_day_close) * 100
            for _, close in entries
        ]
        daily_percentage_changes[year] = daily_changes

    return daily_percentage_changes

def plot_results(price_dict, monthly_changes, daily_changes, symbol):
    fig = plt.figure(figsize=(20, 16))

    # Plot Volume by Price
    ax1 = plt.subplot2grid((3, 2), (0, 0))
    prices = list(price_dict.keys())
    weighted_volumes = list(price_dict.values())
    sorted_prices, sorted_volumes = zip(*sorted(zip(prices, weighted_volumes)))

    ax1.barh(sorted_prices, sorted_volumes, color='blue')
    ax1.set_ylabel('Price')
    ax1.set_title('Volume by Price')
    ax1.grid(True)

    # Plot Average Monthly Changes
    ax2 = plt.subplot2grid((3, 2), (0, 1))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    changes = [monthly_changes.get(f"{i:02}", 0) for i in range(1, 13)]

    ax2.bar(months, changes, color='orange')
    ax2.set_ylabel('%')
    ax2.set_title('Average Monthly Change')
    ax2.grid(True)

    # Plot Daily Percentage Changes (Averaged)
    ax3 = plt.subplot2grid((3, 1), (1, 0), rowspan=2)
    for interval, changes in daily_changes.items():
        ax3.plot(range(1, len(changes) + 1), changes, label=f'{interval}')

    ax3.set_ylabel('%')
    ax3.set_xlabel('Day of Year')
    ax3.legend(loc='upper left')
    ax3.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.suptitle(f'{symbol}', fontsize=18)
    plt.show()

def start(symbol, api_key):
    start_time = time.time()

    if api_key == "":
        rows = fetch_data_crypto(symbol)
    else: 
        rows = fetch_data_av(symbol, api_key)

    if len(rows) < 3:
        print("Data invalid, please check if Symbol is correct or access valid")
        return

    if not rows:
        print("Could not fetch data")
        return
    
    print("fetched ", len(rows), " rows")

    print("Preparing Volume By Price")
    price_dict = calculate_volume_by_price(rows)
    print("Volume By Price ready!")

    print("Preparing Monthly Bias")
    monthly_changes = calculate_monthly_changes(rows)
    print("Monthly Bias ready")

    print("Preparing Seasonality")
    daily_changes = calculate_daily_percentage_changes(rows)
    print("Seasonality ready")
    
    end_time = time.time() - start_time
    print(f"Time to process data: {end_time:.2f} seconds")

    plot_results(price_dict, monthly_changes, daily_changes, symbol)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Error: Requires at least 1 arguments (symbol)")
    else:
        if len(sys.argv)== 3:
            symbol = sys.argv[1]
            api_key = sys.argv[2]
            start(symbol, api_key)
        else:
            symbol = sys.argv[1]
            start(symbol, "")
