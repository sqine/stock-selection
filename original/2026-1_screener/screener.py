import FinanceDataReader as fdr
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def get_keltner_breakouts():
    # 1. Get KOSPI list
    df_krx = fdr.StockListing('KOSPI')
    tickers = df_krx['Code'].tolist()
    names = dict(zip(df_krx['Code'], df_krx['Name']))
    
    breakouts = []
    
    # Limit to top 200 by market cap for efficiency if too many
    # But let's try top 400
    df_krx = df_krx.sort_values(by='MarCap', ascending=False).head(400)
    tickers = df_krx['Code'].tolist()

    print(f"Screening top {len(tickers)} KOSPI stocks...")
    
    period = 20
    multiplier = 2.0
    
    for ticker in tickers:
        try:
            # Fetch last 40 days of daily data
            df = fdr.DataReader(ticker).iloc[-40:]
            if len(df) < period: continue
            
            # Calculate ATR
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
            
            current_close = df['Close'].iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            
            # Calculate Keltner Position: (Close - Lower) / (Upper - Lower)
            # If Upper == Lower (no volatility), avoid div by zero
            if (current_upper - current_lower) != 0:
                k_pos = (current_close - current_lower) / (current_upper - current_lower)
            else:
                k_pos = 0

            # Condition: Upper < Close AND Position >= 0.8
            if current_close > current_upper and k_pos >= 0.8:
                breakouts.append({
                    'Ticker': ticker,
                    'Name': names.get(ticker),
                    'Close': int(current_close),
                    'Upper': round(current_upper, 2),
                    'Position': round(k_pos, 3),
                    'Change': round(((current_close - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100, 2)
                })
        except Exception:
            continue
            
    return pd.DataFrame(breakouts)

results = get_keltner_breakouts()
if not results.empty:
    print(results.to_markdown())
else:
    print("No stocks found matching the criteria.")
