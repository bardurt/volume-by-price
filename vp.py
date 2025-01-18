import requests
import csv
import time
from collections import defaultdict
import matplotlib.pyplot as plt

OPEN_WEIGHT = 0.3
HIGH_WEIGHT = 0.2
LOW_WEIGHT = 0.2
CLOSE_WEIGHT = 0.3

# Fetch data from AlphaVantage
# symbol : the name of the stock to analyze
# api_key : api key from AlphaVantage
def fetch_data(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}&outputsize=full&datatype=csv"
    
    try:
        response = requests.get(url)
        response.raise_for_status() 
        return list(csv.reader(response.text.splitlines()))[1:]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

# Create Volume by Price from dataset
def process_data(rows):
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

# Plot a Volume by Price chart
def plot_results(price_dict):
    prices = list(price_dict.keys())
    weighted_volumes = list(price_dict.values())
    
    sorted_prices, sorted_volumes = zip(*sorted(zip(prices, weighted_volumes)))
    
    plt.figure(figsize=(10, 6))
    plt.barh(sorted_prices, sorted_volumes, color='blue') 
    plt.ylabel('Price Levels')
    plt.xlabel('Weighted Volume')
    plt.title('Volume by Price')
    plt.suptitle(f'{symbol}', fontsize=18)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def start(symbol, api_key):
    start_time = time.time()
    
    rows = fetch_data(symbol, api_key)
    if not rows:
        return

    price_dict = process_data(rows)
    
    end_time = time.time() - start_time
    print(f"Time to run: {end_time:.2f} seconds")
    
    plot_results(price_dict)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Error: Requires 2 arguments (symbol and API key)")
    else:
        symbol = sys.argv[1]
        api_key = sys.argv[2]
        start(symbol, api_key)
