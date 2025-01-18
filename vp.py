# Python Script to Analyze Stock Data
# This script calculates and visualizes Volume by Price for a given asset, allowing users to identify price levels by volume.
# Additionally, it computes and plots the average monthly percentage change in price over the years.

import requests
import csv
import time
from collections import defaultdict, OrderedDict
import matplotlib.pyplot as plt
from datetime import datetime

OPEN_WEIGHT = 0.3
HIGH_WEIGHT = 0.2
LOW_WEIGHT = 0.2
CLOSE_WEIGHT = 0.3

def fetch_data(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}&outputsize=full&datatype=csv"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return list(csv.reader(response.text.splitlines()))[1:]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def cacluate_volume_by_price(rows):
    price_dict = defaultdict(int)
    total_volume = 0

    for row in rows:
        try:
            volume = int(row[5])
            total_volume += volume

            open_price = float(row[1])
            high_price = float(row[2])
            low_price = float(row[3])
            close_price = float(row[4])

            price_dict[open_price] += int(volume * OPEN_WEIGHT)
            price_dict[high_price] += int(volume * HIGH_WEIGHT)
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

def plot_results(price_dict, monthly_changes, symbol):
    fig, axes = plt.subplots(1, 2, figsize=(20, 6))

    prices = list(price_dict.keys())
    weighted_volumes = list(price_dict.values())
    sorted_prices, sorted_volumes = zip(*sorted(zip(prices, weighted_volumes)))

    axes[0].barh(sorted_prices, sorted_volumes, color='blue')
    axes[0].set_ylabel('Price Levels')
    axes[0].set_xlabel('Weighted Volume')
    axes[0].set_title('Volume by Price')
    axes[0].grid(True)
    axes[0].xaxis.set_ticklabels([])

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    changes = [monthly_changes.get(f"{i:02}", 0) for i in range(1, 13)]

    axes[1].bar(months, changes, color='orange')
    axes[1].set_ylabel('Average Monthly Change')
    axes[1].set_xlabel('Month')
    axes[1].set_title('Average Monthly Change in Price Over Years')
    axes[1].grid(True)

    plt.tight_layout()
    plt.suptitle(f'{symbol}', fontsize=18)
    plt.show()

def start(symbol, api_key):
    start_time = time.time()

    rows = fetch_data(symbol, api_key)
    if not rows:
        return

    price_dict = cacluate_volume_by_price(rows)
    monthly_changes = calculate_monthly_changes(rows)
    
    end_time = time.time() - start_time
    print(f"Time to process data: {end_time:.2f} seconds")
    
    plot_results(price_dict, monthly_changes, symbol)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Error: Requires 2 arguments (symbol and API key)")
    else:
        symbol = sys.argv[1]
        api_key = sys.argv[2]
        start(symbol, api_key)
