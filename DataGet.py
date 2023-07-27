import ccxt
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.animation import FuncAnimation
import requests
import threading
import time 

'''
TODO
add liquidations levels
'''

def get_order_book():
    global bids_prices, asks_prices, cumulative_bids, cumulative_asks
    # Create a Binance exchange object
    exchange = ccxt.binance()

    # Set the symbol for the order book
    symbol = 'BTC/USDT'
    while True:
        # Fetch the order book data
        order_book = exchange.fetch_l2_order_book(symbol)

        # Get the bid and ask prices and quantities
        bids_prices, bids_quantities = zip(*order_book['bids'])
        asks_prices, asks_quantities = zip(*order_book['asks'])

        # Create a cumulative sum of bid and ask quantities
        cumulative_bids = [sum(bids_quantities[:i + 1]) for i in range(len(bids_quantities))]
        cumulative_asks = [sum(asks_quantities[:i + 1]) for i in range(len(asks_quantities))]

def get_open_interest_long_short_ratio(symbol, period, limit):
    base_url = 'https://fapi.binance.com'  # Binance Futures API base URL

    # Construct the API endpoint URL for long/short ratio
    ratio_url = f'{base_url}/futures/data/globalLongShortAccountRatio?symbol={symbol}&period={period}&limit={limit}'

    # Construct the API endpoint URL for taker buy/sell volume
    volume_url = f'{base_url}/futures/data/takerlongshortRatio?symbol={symbol}&period={period}&limit={limit}'

    # Construct the API endpoint URL for open interest
    open_interest_url = f'{base_url}/fapi/v1/openInterest?symbol={symbol}'

    # Send GET requests to the APIs
    ratio_response = requests.get(ratio_url)
    volume_response = requests.get(volume_url)
    open_interest_response = requests.get(open_interest_url)

    long_short_ratio = 0
    taker_sell_volume = 0
    taker_buy_volume = 0
    open_interest = 0

    # Check if the requests were successful
    if (
        ratio_response.status_code == 200
        and volume_response.status_code == 200
        and open_interest_response.status_code == 200
    ):
        ratio_data = ratio_response.json()
        volume_data = volume_response.json()
        open_interest_data = open_interest_response.json()

        # Extract the most recent values
        if (
            len(ratio_data) > 0
            and len(volume_data) > 0
            and 'openInterest' in open_interest_data
        ):
            long_short_ratio = ratio_data[0]['longShortRatio']
            taker_buy_volume = volume_data[0]['buyVol']
            taker_sell_volume = volume_data[0]['sellVol']
            open_interest = open_interest_data['openInterest']

        else:
            print("Data not found.")
    else:
        print("Failed to fetch data from the API.")
    return long_short_ratio, open_interest, taker_buy_volume, taker_sell_volume

def fetch_data():
    while True:
        global liquidity
        liquidity = get_open_interest_long_short_ratio("BTCUSDT", "5m", 1)
        print(liquidity[0])
        print(liquidity[1])
        print(liquidity[2])
        print(liquidity[3])
        print()

# Function to handle incoming trades and update the DataFrame
def handle_trade(trade, symbol):
    global df, liquidity

    trade_data = {
        'timestamp': pd.to_datetime(trade['timestamp'], unit='ms'),  # Convert timestamp to datetime
        'symbol': symbol,
        'side': trade['side'],
        'price': trade['price'],
        'size': trade['amount'],
        'long_short_ratio': liquidity[0],
        'open_interest': liquidity[1],
        'taker_buy_volume': liquidity[2],
        'taker_sell_volume': liquidity[3]
    }
    df = df.append(trade_data, ignore_index=True)
    print()
    print("Last entry in DataFrame:")
    print(df.tail(1))  # Print the last entry in DataFrame

def update_chart(frame, ax1, ax2, ax3):
    global df, exchange_instance, symbol, bids_prices, asks_prices, cumulative_bids, cumulative_asks

    # Fetch the latest trade
    trades = exchange_instance.fetch_trades(symbol, limit=1)
    if trades:
        handle_trade(trades[0], symbol)

    # Sort the data by timestamp in ascending order
    data = df.sort_values(by='timestamp')

    # Create a new DataFrame with 5-minute interval data (OHLC)
    resampled_data = data.set_index('timestamp').resample('5T').agg({
        'price': 'ohlc',
        'size': 'sum'
    })

    # Rename the columns for the new DataFrame
    resampled_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    # Update the candlestick chart
    ax1.clear()
    mpf.plot(resampled_data, type='candle', ax=ax1, volume=False, show_nontrading=True)
    ax1.set_title('Candlestick Chart')
    ax1.set_ylabel('Price')

    '''# Add horizontal lines to ax1
    maxB = max(cumulative_bids)
    for i in range(len(bids_prices) - 1):  # Adjust the price levels as needed
        b = cumulative_bids[i] / maxB
        ax1.axhline(bids_prices[i], color='green', linestyle='dashed', linewidth=0.2, alpha=b, xmax=10)

    # Add horizontal lines to ax1
    maxA = max(cumulative_asks)
    for i in range(len(asks_prices) - 1):  # Adjust the price levels as needed
        a = cumulative_asks[i] / maxA
        ax1.axhline(asks_prices[i], color='red', linestyle='dashed', linewidth=0.2, alpha=a, xmax=1)'''
    
    maxB = max(cumulative_bids)
    x = 0
    for i in range(len(bids_prices) - 1):
        b = cumulative_bids[i] / maxB
        y = (bids_prices[i] + bids_prices[i+1]) / 2
        segment_length = 0.04 * b  # Adjust the length as needed (0.02 is just an example)
        segment = plt.Line2D([x, x + segment_length], [y, y], transform=ax1.get_yaxis_transform(), color='green', linewidth=0.3, alpha=b)
        ax1.add_line(segment)

    # Add horizontal segments to ax1 for asks
    maxA = max(cumulative_asks)
    for i in range(len(asks_prices) - 1):
        a = cumulative_asks[i] / maxA
        y = (asks_prices[i] + asks_prices[i+1]) / 2
        segment_length = 0.04 * a  # Adjust the length as needed (0.02 is just an example)
        segment = plt.Line2D([x, x + segment_length], [y, y], transform=ax1.get_yaxis_transform(), color='red', linewidth=0.3, alpha=a)
        ax1.add_line(segment)

    # Update the embedded footprint chart
    ax2.clear()
    ax2.fill_between(data['timestamp'], data['price'], where=data['side'] == 'buy', facecolor='g', alpha=0.3, label='Bids')
    ax2.fill_between(data['timestamp'], data['price'], where=data['side'] == 'sell', facecolor='r', alpha=0.3, label='Asks')
    ax2.plot(data['timestamp'], data['long_short_ratio'], color='orange', label='Long/Short Ratio')
    ax2.set_ylabel('Price / Long/Short Ratio')
    ax2.set_title('Embedded Footprint Chart')
    ax2.legend()
    ax2.grid(True)

    # Update the volume chart
    ax3.clear()
    ax3.bar(data['timestamp'], data['size'], color='b', width=0.002, align='center', label='Volume')
    ax3.plot(data['timestamp'], data['open_interest'], color='purple', label='Open Interest')
    ax3.plot(data['timestamp'], data['taker_buy_volume'], color='blue', label='Taker Buy Volume')
    ax3.plot(data['timestamp'], data['taker_sell_volume'], color='red', label='Taker Sell Volume')

    ax3.set_xlabel('Time')
    ax3.set_ylabel('Volume / Open Interest')
    ax3.legend()
    ax3.grid(True)

def subscribe_to_trades(exchange, symbol):
    global df, exchange_instance

    try:
        # Create the exchange instance
        exchange_instance = getattr(ccxt, exchange)()

        # Create an empty DataFrame to store trade data
        columns = ['timestamp', 'symbol', 'side', 'price', 'size', 'long_short_ratio', 'open_interest', 'taker_buy_volume', 'taker_sell_volume']
        df = pd.DataFrame(columns=columns)

        # Create the live chart with all three subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [4, 1, 1]})

        ani = FuncAnimation(fig, update_chart, fargs=(ax1, ax2, ax3), interval=1)  # Update every 5 seconds

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    exchange = "binance"  # Replace with your exchange
    symbol = "BTC/USDT"   # Replace with the trading pair you want

    thread = threading.Thread(target=fetch_data, args=())
    thread.start()

    thread2 = threading.Thread(target=get_order_book, args=())
    thread2.start()

    time.sleep(3)
    subscribe_to_trades(exchange, symbol)
