from pykrx import stock
try:
    tickers = stock.get_market_ticker_list(date="20260325", market="KOSPI")
    print(f"Successfully fetched {len(tickers)} KOSPI tickers.")
except Exception as e:
    print(f"Error: {e}")
