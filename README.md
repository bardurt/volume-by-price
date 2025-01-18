# volume-by-price
Python Script to Analyze Stock Data

This script calculates and visualizes Volume by Price for a given asset, allowing users to identify price levels by volume.
Additionally, it computes and plots the average monthly percentage change in price over the years.

![Volume By Price](images/preview.png)


### Getting Started

This script uses the `requests` and `matplotlib`, please make sure to install these librares with `pip` before running the script

```
pip install requests
```
and
```
pip install matplotlib
```

The script requires 2 start up arguments

```[SYMBOL] [API KEY FROM ALPHA VANTAGE]```
The first argument is the symbol to analyze: TSLA, AAPL, MSFT etc. The second argument is the Api Key that you can get from https://www.alphavantage.co/ for free.

Run the script by executing the below command in bash (make sure to use your api key, the one in the sample is not real)

```python vp.py AAPL 21321asdavvv```
