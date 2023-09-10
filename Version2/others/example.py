import pandas as pd
import ccxt

def fetch_order_book_data(exchange, symbol):
    order_book = exchange.fetch_l2_order_book(symbol)
    bids_prices, bids_quantities = zip(*order_book['bids'])
    asks_prices, asks_quantities = zip(*order_book['asks'])
    cumulative_bids = [sum(bids_quantities[:i + 1]) for i in range(len(bids_quantities))]
    cumulative_asks = [sum(asks_quantities[:i + 1]) for i in range(len(asks_quantities))]
    return bids_prices, cumulative_bids, asks_prices, cumulative_asks

# Create a Binance exchange object
exchange = ccxt.binance()

# Set the symbol for the order book
symbol = 'BTC/USDT'

# Fetch order book data
bids_prices, cumulative_bids, asks_prices, cumulative_asks = fetch_order_book_data(exchange, symbol)

# Create DataFrame with candlestick chart data (example)
candlestick_data = pd.DataFrame({
    'timestamp': ['2023-07-01 00:00:00', '2023-07-01 01:00:00', '2023-07-01 02:00:00'],
    'open': [40000, 40100, 40300],
    'high': [40500, 40550, 40700],
    'low': [39800, 40090, 40250],
    'close': [40200, 40350, 40500],
    'volume': [100, 150, 200]
})

# Create DataFrame with order book data
order_book_data = pd.DataFrame({
    'bids_prices': bids_prices,
    'cumulative_bids': cumulative_bids,
    'asks_prices': asks_prices,
    'cumulative_asks': cumulative_asks
})

# Combine the two DataFrames
combined_data = pd.concat([candlestick_data, order_book_data], axis=1)

# Save the combined data to a CSV file
combined_data.to_csv('combined_data.csv', index=False)