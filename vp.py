import requests
import csv
import time
from collections import defaultdict, OrderedDict
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
from urllib.parse import quote
from io import StringIO
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
        
        result = df[['date', 'open', 'high', 'low', 'close', 'Volume USD']]
        
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


def get_total_change(rows):

    daily_data = []

    for row in rows:
        try:
            date = datetime.strptime(row[0], "%Y-%m-%d")
            open_price = float(row[1])
            daily_data.append((date, open_price))
        except ValueError:
            continue

    return daily_data


def plot_results(price_dict, monthly_changes, daily_changes, total_change, symbol):
    root = tk.Tk()
    root.title(f"Charts for {symbol}")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="Volume by Price")

    fig1 = plt.Figure(figsize=(8, 6))
    ax1 = fig1.add_subplot(111)

    prices = list(price_dict.keys())
    weighted_volumes = list(price_dict.values())
    sorted_prices, sorted_volumes = zip(*sorted(zip(prices, weighted_volumes)))

    ax1.barh(sorted_prices, sorted_volumes, color='blue')
    ax1.set_ylabel('Price')
    ax1.set_title('Volume by Price')
    ax1.set_xticks([]) 
    ax1.grid(True)

    canvas1 = FigureCanvasTkAgg(fig1, master=tab1)
    canvas1.get_tk_widget().pack(fill="both", expand=True)
    canvas1.draw()

    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="Monthly Bias")

    fig2 = plt.Figure(figsize=(8, 6))
    ax2 = fig2.add_subplot(111)

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    changes = [monthly_changes.get(f"{i:02}", 0) for i in range(1, 13)]

    ax2.bar(months, changes, color='orange')
    ax2.set_ylabel('')
    ax2.set_yticks([]) 
    ax2.set_title('Monthly Bias')
    ax2.grid(True)

    canvas2 = FigureCanvasTkAgg(fig2, master=tab2)
    canvas2.get_tk_widget().pack(fill="both", expand=True)
    canvas2.draw()

    # Tab 3: Seasonality
    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text="Seasonality")

    fig3 = plt.Figure(figsize=(10, 6))  # Increase figure width for better spacing
    ax3 = fig3.add_subplot(111)

    for interval, changes in daily_changes.items():
        ax3.plot(range(1, len(changes) + 1), changes, label=f'{interval}')

    ax3.set_ylabel('%')
    ax3.set_xlabel('Day of Year')
    ax3.grid(True)

    # Move legend to the left side and ensure full visibility
    ax3.legend(
        loc='center left',
        bbox_to_anchor=(-0.2, 0.5),  # Adjust position to make space for the legend
        title="Year",
        frameon=False,
        fontsize='small',  # Optional: Reduce font size for better fit
    )

    fig3.tight_layout(pad=1)  # Add padding to avoid clipping

    canvas3 = FigureCanvasTkAgg(fig3, master=tab3)
    canvas3.get_tk_widget().pack(fill="both", expand=True)
    canvas3.draw()

    tab4 = ttk.Frame(notebook)
    notebook.add(tab4, text="History")

    fig4 = plt.Figure(figsize=(8, 6))
    ax4 = fig4.add_subplot(111)

    dates = [entry[0] for entry in total_change]
    changes = [entry[1] for entry in total_change]

    ax4.plot(dates, changes, color='blue', linewidth=1)

    ax4.grid(True)

    canvas4 = FigureCanvasTkAgg(fig4, master=tab4)
    canvas4.get_tk_widget().pack(fill="both", expand=True)
    canvas4.draw()

    root.mainloop()


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
    print("Volume By Price ready")

    print("Preparing Monthly Bias")
    monthly_changes = calculate_monthly_changes(rows)
    print("Monthly Bias ready")

    print("Preparing Seasonality")
    daily_changes = calculate_daily_percentage_changes(rows)
    print("Seasonality ready")

    print("Preparing History")
    total_change = get_total_change(rows)
    print("History ready")
    
    end_time = time.time() - start_time
    print(f"Time to process data: {end_time:.2f} seconds")

    print("Preparing chats...")
    plot_results(price_dict, monthly_changes, daily_changes, total_change, symbol)

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
