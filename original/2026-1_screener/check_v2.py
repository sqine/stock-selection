import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def check_keltner(ticker):
    df = yf.download(ticker, period='2mo', interval='1d', progress=False)
    # Ensure single index columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    period = 20
    multiplier = 2.0
    
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    ema = df['Close'].ewm(span=period, adjust=False).mean()
    upper = ema + (multiplier * atr)
    lower = ema - (multiplier * atr)
    
    last_close = df['Close'].iloc[-1]
    last_upper = upper.iloc[-1]
    last_lower = lower.iloc[-1]
    
    pos = (last_close - last_lower) / (last_upper - last_lower)
    
    print(f"Ticker: {ticker}")
    print(f"Close: {last_close:.2f}")
    print(f"Upper: {last_upper:.2f}")
    print(f"Position: {pos:.3f}")
    print(f"Above Upper: {last_close > last_upper}")
    print("-" * 20)

check_keltner('005930.KS')
check_keltner('000660.KS')
check_keltner('373220.KS')
