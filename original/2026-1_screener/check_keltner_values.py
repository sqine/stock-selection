import yfinance as yf
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

tickers = [('005930.KS', 'Samsung Electronics'), ('066970.KS', 'L&F')]

for ticker, name in tickers:
    df = yf.download(ticker, period='2mo', interval='1d', progress=False)
    period = 20
    multiplier = 2.0
    
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    ema = df['Close'].ewm(span=period, adjust=False).mean()
    upper_band = ema + (multiplier * atr)
    lower_band = ema - (multiplier * atr)
    
    current_close = df['Close'].iloc[-1].item()
    current_upper = upper_band.iloc[-1].item()
    current_lower = lower_band.iloc[-1].item()
    k_pos = (current_close - current_lower) / (current_upper - current_lower)
    
    print(f"[{name}] Close: {current_close}, Upper: {round(current_upper, 2)}, Pos: {round(k_pos, 3)}")
