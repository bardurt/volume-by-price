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

def calculate_volume_by_price(rows):
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

def calculate_daily_percentage_changes(rows):
    yearly_data = defaultdict(list)

    for row in rows:
        try:
            date = datetime.strptime(row[0], "%Y-%m-%d")
            close_price = float(row[4])
            year_key = date.year
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
    ax1.set_ylabel('Price Levels')
    ax1.set_title('Volume by Price')
    ax1.grid(True)

    # Plot Average Monthly Changes
    ax2 = plt.subplot2grid((3, 2), (0, 1))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    changes = [monthly_changes.get(f"{i:02}", 0) for i in range(1, 13)]

    ax2.bar(months, changes, color='orange')
    ax2.set_ylabel('Average Monthly Change')
    ax2.set_title('Average Monthly Change in Price Over Years')
    ax2.grid(True)

    # Plot Daily Percentage Changes (Averaged)
    ax3 = plt.subplot2grid((3, 1), (1, 0), rowspan=2)
    for interval, changes in daily_changes.items():
        ax3.plot(range(1, len(changes) + 1), changes, label=f'{interval}')

    ax3.set_ylabel('Daily % Change')
    ax3.set_xlabel('Day of Year')
    ax3.legend(loc='upper left')
    ax3.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.suptitle(f'{symbol}', fontsize=18)
    plt.show()

def start(symbol, api_key):
    start_time = time.time()

    rows = fetch_data(symbol, api_key)
    if not rows:
        return

    price_dict = calculate_volume_by_price(rows)
    monthly_changes = calculate_monthly_changes(rows)
    daily_changes = calculate_daily_percentage_changes(rows)

    end_time = time.time() - start_time
    print(f"Time to process data: {end_time:.2f} seconds")

    plot_results(price_dict, monthly_changes, daily_changes, symbol)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Error: Requires 2 arguments (symbol and API key)")
    else:
        symbol = sys.argv[1]
        api_key = sys.argv[2]
        start(symbol, api_key)
