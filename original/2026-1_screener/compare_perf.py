import yfinance as yf
import pandas as pd

def get_perf(ticker):
    # Fetch data including last Friday (Mar 13) to today (Mar 19)
    df = yf.download(ticker, start='2026-03-13', end='2026-03-20', progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    fri_open = df['Open'].iloc[0]
    thu_close = df['Close'].iloc[-1]
    perf = ((thu_close - fri_open) / fri_open) * 100
    return fri_open, thu_close, perf

stocks = {'003030.KS': 'SeAH Steel Holdings', '007340.KS': 'DN Automotive'}
results = []
for t, name in stocks.items():
    o, c, p = get_perf(t)
    results.append({'Name': name, 'Fri Open': int(o), 'Thu Close': int(c), 'Weekly Perf(%)': round(p, 2)})

print(pd.DataFrame(results).to_markdown(index=False))
