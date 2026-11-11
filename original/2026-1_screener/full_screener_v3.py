import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime
import time
import os

warnings.filterwarnings('ignore')

def get_tickers_from_file():
    stocks = []
    if os.path.exists('temp_tickers.txt'):
        with open('temp_tickers.txt', 'r') as f:
            for line in f:
                if '|' in line:
                    name, code = line.strip().split('|')
                    stocks.append({'Code': code.strip() + ".KS", 'Name': name.strip()})
    
    # Add some major KOSDAQ stocks manually if not in the list
    # The list from keltner_screening.py seems to be mostly KOSPI
    # But for this task, it's a solid start.
    if not stocks:
        return pd.DataFrame([
            {'Code': '005930.KS', 'Name': 'Samsung Electronics'},
            {'Code': '000660.KS', 'Name': 'SK Hynix'}
        ])
    return pd.DataFrame(stocks)

def screen_keltner(stock_list):
    period = 20
    multiplier = 2.0
    breakouts = []
    
    print(f"Screening {len(stock_list)} stocks with Keltner Channel criteria...")
    
    # Download in batches for efficiency
    tickers = stock_list['Code'].tolist()
    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch_tickers = tickers[i:i+batch_size]
        print(f"Downloading batch {i//batch_size + 1}...")
        try:
            data = yf.download(batch_tickers, period='3mo', interval='1d', progress=False, group_by='ticker')
            
            for ticker in batch_tickers:
                try:
                    df = data[ticker]
                    if df.empty or len(df) < period + 1: continue
                    df = df.dropna()
                    if len(df) < period + 1: continue

                    # ATR (20)
                    high_low = df['High'] - df['Low']
                    high_close = (df['High'] - df['Close'].shift()).abs()
                    low_close = (df['Low'] - df['Close'].shift()).abs()
                    ranges = pd.concat([high_low, high_close, low_close], axis=1)
                    true_range = ranges.max(axis=1)
                    atr = true_range.rolling(window=period).mean()
                    
                    # EMA (20)
                    ema = df['Close'].ewm(span=period, adjust=False).mean()
                    
                    # Keltner Channels
                    upper_band = ema + (multiplier * atr)
                    lower_band = ema - (multiplier * atr)
                    
                    # Latest values
                    current_close = df['Close'].iloc[-1]
                    current_upper = upper_band.iloc[-1]
                    current_lower = lower_band.iloc[-1]
                    
                    if isinstance(current_close, pd.Series): current_close = current_close.iloc[0]
                    if isinstance(current_upper, pd.Series): current_upper = current_upper.iloc[0]
                    if isinstance(current_lower, pd.Series): current_lower = current_lower.iloc[0]

                    # Position
                    channel_width = current_upper - current_lower
                    if channel_width != 0:
                        k_pos = (current_close - current_lower) / channel_width
                    else:
                        k_pos = 0
                        
                    # Conditions:
                    # 1. Close > Upper (Breakout)
                    # 2. Position >= 0.8 (Strong momentum)
                    if current_close > current_upper and k_pos >= 0.8:
                        prev_close = df['Close'].iloc[-2]
                        if isinstance(prev_close, pd.Series): prev_close = prev_close.iloc[0]
                        change_1d = ((current_close - prev_close) / prev_close) * 100
                        
                        name = stock_list[stock_list['Code'] == ticker]['Name'].values[0]
                        
                        breakouts.append({
                            'Code': ticker.split('.')[0],
                            'Name': name,
                            'Close': int(current_close),
                            'Upper': round(float(current_upper), 2),
                            'Pos': round(float(k_pos), 3),
                            'Chg(1d)%': round(float(change_1d), 2)
                        })
                except Exception:
                    continue
            time.sleep(0.2)
        except Exception:
            continue
            
    return pd.DataFrame(breakouts)

if __name__ == "__main__":
    stocks = get_tickers_from_file()
    results = screen_keltner(stocks)
    
    if not results.empty:
        print("\n=== Keltner Channel Breakout Candidates ===")
        results = results.sort_values(by='Chg(1d)%', ascending=False)
        print(results.to_markdown(index=False))
        
        filename = f"keltner_results_{datetime.now().strftime('%Y%m%d')}.csv"
        results.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\nSaved {len(results)} matches to {filename}")
    else:
        print("\nNo stocks found matching the breakout criteria among the selected list.")
