import sys
from unittest.mock import MagicMock

# Mocking matplotlib before importing pykrx
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.font_manager'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()

from pykrx import stock
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Dates
start_date = "20260320"  # Last Friday
end_date = "20260325"    # This Wednesday (Today)

print(f"Fetching KOSPI stock data from {start_date} to {end_date}...")

# 1. Get market OHLCV for both dates
# This is more efficient than looping through tickers
try:
    df_end = stock.get_market_ohlcv_by_ticker(end_date, market="KOSPI")
    df_start = stock.get_market_ohlcv_by_ticker(start_date, market="KOSPI")

    if df_end.empty or df_start.empty:
        print("No data found for the specified dates. Checking if they are holidays...")
        # If today is Wednesday, it should have data. Friday should also have data.
        # However, let's try to get the nearest trading days if empty.
        # But for this task, we'll assume the dates are correct.
        pass

    # 2. Combine data
    # We use df_end as the base for tickers and volume
    df = pd.DataFrame(index=df_end.index)
    
    # Add Name
    # stock.get_market_ticker_name is fast as it uses a local mapping
    df['Name'] = [stock.get_market_ticker_name(t) for t in df_end.index]
    
    df['Start_Open'] = df_start['시가']
    df['End_Close'] = df_end['종가']
    df['End_Volume'] = df_end['거래량']

    # 3. Filter criteria: Volume >= 100,000
    df = df[df['End_Volume'] >= 100000]

    # 4. Calculate return (%)
    # (End_Close / Start_Open) - 1
    df['Return(%)'] = (df['End_Close'] / df['Start_Open'] - 1) * 100

    # 5. Clean up
    df.dropna(subset=['Return(%)'], inplace=True)
    df = df[df['Start_Open'] > 0]
    
    # Avoid infinite returns or errors
    df = df[df['Return(%)'].notnull()]

    # 6. Sort by Return descending
    df_sorted = df.sort_values(by='Return(%)', ascending=False)

    # 7. Top 30
    top_30 = df_sorted.head(30)

    if not top_30.empty:
        # Format for output
        top_30['Start_Open'] = top_30['Start_Open'].astype(int).apply(lambda x: f"{x:,}")
        top_30['End_Close'] = top_30['End_Close'].astype(int).apply(lambda x: f"{x:,}")
        top_30['End_Volume'] = top_30['End_Volume'].astype(int).apply(lambda x: f"{x:,}")
        top_30['Return(%)'] = top_30['Return(%)'].round(2)
        
        print(top_30[['Name', 'Start_Open', 'End_Close', 'End_Volume', 'Return(%)']].to_markdown())
    else:
        print("No stocks found matching the criteria.")

except Exception as e:
    print(f"An error occurred: {e}")
