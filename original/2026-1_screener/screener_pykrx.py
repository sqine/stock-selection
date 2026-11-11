from pykrx import stock
import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

def screen_kospi200():
    # 1. Get KOSPI 200 list from KRX
    # We use a recent date to get the list
    today = datetime.now().strftime("%Y%m%d")
    tickers = stock.get_index_portfolio_deposit_file("1028") # KOSPI 200
    
    # 2. Convert to yfinance tickers
    yf_tickers = [t + ".KS" for t in tickers]
    
    # 3. Get Names
    names = {}
    for t in tickers:
        try:
            names[t + ".KS"] = stock.get_market_ticker_name(t)
        except:
            names[t + ".KS"] = t

    breakouts = []
    period = 20
    multiplier = 2.0
    
    print(f"Screening {len(yf_tickers)} KOSPI 200 stocks...")
    
    for ticker_code in yf_tickers:
        try:
            # Fetch last 40 days of daily data
            df = yf.download(ticker_code, period='2mo', interval='1d', progress=False)
            if len(df) < period: continue
            
            # Calculate ATR (20)
            high_low = df['High'] - df['Low']
            high_close = (df['High'] - df['Close'].shift()).abs()
            low_close = (df['Low'] - df['Close'].shift()).abs()
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            # Calculate Keltner Channels (EMA 20)
            ema = df['Close'].ewm(span=period, adjust=False).mean()
            upper_band = ema + (multiplier * atr)
            lower_band = ema - (multiplier * atr)
            
            # Use the last row
            current_close = df['Close'].iloc[-1].item()
            current_upper = upper_band.iloc[-1].item()
            current_lower = lower_band.iloc[-1].item()
            
            # Keltner Position
            if (current_upper - current_lower) != 0:
                k_pos = (current_close - current_lower) / (current_upper - current_lower)
            else:
                k_pos = 0

            # Condition: Upper < Close AND Position >= 0.8
            if current_close > current_upper and k_pos >= 0.8:
                prev_close = df['Close'].iloc[-2].item()
                change = ((current_close - prev_close) / prev_close) * 100
                breakouts.append({
                    'Ticker': ticker_code.replace('.KS', ''),
                    'Name': names.get(ticker_code),
                    'Close': int(current_close),
                    'Upper': round(current_upper, 2),
                    'Position': round(k_pos, 3),
                    'Change(%)': round(change, 2)
                })
        except Exception:
            continue
            
    return pd.DataFrame(breakouts)

results = screen_kospi200()
if not results.empty:
    print(results.to_markdown(index=False))
else:
    print("No KOSPI 200 stocks found matching the criteria.")
