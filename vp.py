import math
import numpy as np
import requests
import csv
import time
from collections import defaultdict
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
            mid_price = (high_price + low_price) / 2

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
            if year_key != year_start:
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


def euclidean_distance(list1, list2):
    min_length = min(len(list1), len(list2))
    list1 = list1[:min_length]
    list2 = list2[:min_length]
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(list1, list2)))

def pearson_correlation(list1, list2):
    min_length = min(len(list1), len(list2))
    list1 = list1[:min_length]
    list2 = list2[:min_length]
    return np.corrcoef(list1, list2)[0, 1]

def find_closest_year(daily_percentage_changes, year_end, method="euclidean"):
    current_year_changes = daily_percentage_changes.get(year_end)
    if current_year_changes is None:
        return None, None 

    closest_changes = None
    closest_year = None
    if method == "euclidean":
        best_similarity_score = float('inf')
    elif method == "pearson":
        best_similarity_score = float('-inf')

    for year, changes in daily_percentage_changes.items():
        if year == year_end:
            continue 

        if method == "euclidean":
            similarity_score = euclidean_distance(current_year_changes, changes)
            if similarity_score < best_similarity_score:
                best_similarity_score = similarity_score
                closest_changes = changes
                closest_year = year
        elif method == "pearson":
            similarity_score = pearson_correlation(current_year_changes, changes)
            if similarity_score > best_similarity_score: 
                best_similarity_score = similarity_score
                closest_changes = changes
                closest_year = year
        else:
            raise ValueError("Invalid method. Use 'euclidean' or 'pearson'.")

    return current_year_changes, closest_changes, closest_year


def plot_results(price_dict, monthly_changes, daily_changes, current_year_changes, year_for_analysis, closest_year_changes, closest_year, symbol, method):
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
    ax2.set_ylabel('Avg Change')
    ax2.grid(True)
    canvas2 = FigureCanvasTkAgg(fig2, master=tab2)
    canvas2.get_tk_widget().pack(fill="both", expand=True)
    canvas2.draw()

    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text="Seasonality")
    fig3 = plt.Figure(figsize=(10, 6)) 
    ax3 = fig3.add_subplot(111)
    canvas3 = FigureCanvasTkAgg(fig3, master=tab3)
    canvas3.get_tk_widget().pack(side=tk.RIGHT, fill="both", expand=True)

    checkbox_frame = ttk.Frame(tab3)
    checkbox_frame.pack(side=tk.LEFT, fill="y", padx=10)

    year_vars = {}

    def update_seasonality_plot():
        ax3.clear()
        for year, changes in daily_changes.items():
            if year_vars[year].get():
                ax3.plot(range(1, len(changes) + 1), changes, label=str(year))
        ax3.set_ylabel('%')
        ax3.set_xlabel('Day of Year')
        ax3.grid(True)
        ax3.legend(
            loc='center left',
            bbox_to_anchor=(1.05, 0.5),
            title="Year",
            frameon=False,
            fontsize='small',
        )
        fig3.tight_layout(pad=1)
        canvas3.draw()

    for year in sorted(daily_changes.keys()):
        var = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(
            checkbox_frame,
            text=str(year),
            variable=var,
            command=update_seasonality_plot
        )
        chk.pack(anchor="w")
        year_vars[year] = var

    update_seasonality_plot()

    if(closest_year_changes):

        if method == "euclidean":
            closeset_match_info = "Euclidan Distance"
        elif method == "pearson":
           closeset_match_info = "Pearson Correlation"
        
        tab5 = ttk.Frame(notebook)
        notebook.add(tab5, text="Closest Match")
        fig5 = plt.Figure(figsize=(10, 6))
        ax5 = fig5.add_subplot(111)
        ax5.plot(range(1, len(current_year_changes) + 1), current_year_changes, label=f'Current Year ({symbol})', color='blue', linestyle='-')
        ax5.plot(range(1, len(closest_year_changes) + 1), closest_year_changes, label=f'Closest Year ({closest_year})', color='red', linestyle='-')
        ax5.set_xlabel('Day of Year')
        ax5.set_ylabel('Percentage Change')
        ax5.set_title(f'Daily Percentage Changes: {symbol} {year_for_analysis} vs Closest Match ({closest_year}) - {closeset_match_info}')
        ax5.legend(loc='upper left')
        ax5.grid(True)
        canvas5 = FigureCanvasTkAgg(fig5, master=tab5)
        canvas5.get_tk_widget().pack(fill="both", expand=True)
        canvas5.draw()

    root.mainloop()

    

def read_api_key(file_path):
        try:
            with open(file_path, 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            return ""

def start(symbol, asset, method):
    start_time = time.time()

    if asset == "c":
        print("Fetching data for Crypto")
        rows = fetch_data_crypto(symbol)
    else: 
        print("Fetching data from AlphaVantage")
        print("Reading api key")
        api_key = read_api_key("avkey.txt")
        if not api_key:
            print("Error: API key is missing.")
            sys.exit(1)
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

    print("Finding Seasonality match")
    year_end = datetime.now().year
    current_year_changes, closest_year_changes, closest_year = find_closest_year(daily_changes, year_end, method)
    print(f"The closest year to {year_end} based on ${method} distance is {closest_year}.")
    print("Finding match completed")

    end_time = time.time() - start_time
    print(f"Time to process data: {end_time:.2f} seconds")

    print("Preparing chats...")
    plot_results(price_dict, monthly_changes, daily_changes, current_year_changes, year_end, closest_year_changes, closest_year, symbol, method)

def show_help():
    print("")
    print("Help")
    print("-----------------------------------------------------")
    print("Usage: python vp.py <symbol> <asset type>")
    print("  <symbol>       e.g., BTC or AAPL")
    print("  <asset type>   'c' for crypto, anything else for stock (uses Alpha Vantage)")
    print("\nExample:")
    print("  python vp.py BTC c (Crypto Currency)")
    print("  python vp.py AAPL s (Stock)")
    print("\nNote:")
    print("If using Alpha Vantage (stocks), make sure you have your API key saved in a file named 'avkey.txt' in the same folder as this script.")
    print("-----------------------------------------------------")
    print("")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
       show_help()
    else:
        symbol = sys.argv[1]
        asset = sys.argv[2]
        method = sys.argv[3] if len(sys.argv) > 3 else "euclidean"
        if method not in ["euclidean", "pearson"]:
            print("Invalid method. Use 'euclidean' or 'pearson'. Defaulting to euclidean.")
            method = "euclidean"
        start(symbol, asset, method)
