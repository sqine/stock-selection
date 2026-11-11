import FinanceDataReader as fdr
import pandas as pd
import warnings
from datetime import datetime
import time

warnings.filterwarnings('ignore')

def get_market_list():
    print("Fetching stock listings from KOSPI and KOSDAQ...")
    max_retries = 3
    df_kospi = None
    df_kosdaq = None
    
    for attempt in range(max_retries):
        try:
            if df_kospi is None:
                df_kospi = fdr.StockListing('KOSPI')
            if df_kosdaq is None:
                df_kosdaq = fdr.StockListing('KOSDAQ')
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)
            
    if df_kospi is None or df_kosdaq is None:
        print("Failed to fetch from KRX. Using fallback list.")
        # Minimal fallback
        return pd.DataFrame([
            {'Code': '005930', 'Name': 'Samsung Electronics', 'Market': 'KOSPI', 'Marcap': 500000000000000},
            {'Code': '000660', 'Name': 'SK Hynix', 'Market': 'KOSPI', 'Marcap': 100000000000000}
        ])
    
    df_kospi['Market'] = 'KOSPI'
    df_kosdaq['Market'] = 'KOSDAQ'
    
    df_all = pd.concat([df_kospi, df_kosdaq])
    
    # Clean up
    df_all = df_all[['Code', 'Name', 'Market', 'Marcap']]
    # Sort by Market Cap and take top 800 for a thorough investigation
    df_all = df_all.sort_values(by='Marcap', ascending=False).head(800)
    
    return df_all

def screen_keltner(stock_list):
    period = 20
    multiplier = 2.0
    breakouts = []
    
    print(f"Screening {len(stock_list)} stocks with Keltner Channel criteria...")
    
    total = len(stock_list)
    for i, row in stock_list.iterrows():
        ticker = row['Code']
        name = row['Name']
        market = row['Market']
        
        if (i+1) % 100 == 0:
            print(f"Progress: {i+1}/{total}...")
            
        try:
            # Download enough data for 20-day EMA and ATR
            df = fdr.DataReader(ticker).iloc[-60:]
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
                change_1d = ((current_close - prev_close) / prev_close) * 100
                
                # Volume comparison (Current vs 20d average)
                avg_vol = df['Volume'].rolling(window=period).mean().iloc[-1]
                vol_ratio = df['Volume'].iloc[-1] / avg_vol if avg_vol != 0 else 0
                
                breakouts.append({
                    'Market': market,
                    'Code': ticker,
                    'Name': name,
                    'Close': int(current_close),
                    'Upper': round(current_upper, 2),
                    'Pos': round(k_pos, 3),
                    'Chg(1d)%': round(change_1d, 2),
                    'Vol_Ratio': round(vol_ratio, 2)
                })
        except Exception:
            continue
            
    return pd.DataFrame(breakouts)

if __name__ == "__main__":
    stocks = get_market_list()
    results = screen_keltner(stocks)
    
    if not results.empty:
        print("\n=== Keltner Channel Breakout Candidates ===")
        # Sort by Volume Ratio then 1d Change
        results = results.sort_values(by=['Vol_Ratio', 'Chg(1d)%'], ascending=False)
        print(results.to_markdown(index=False))
        
        # Save to CSV
        filename = f"keltner_results_{datetime.now().strftime('%Y%m%d')}.csv"
        results.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\nSaved {len(results)} matches to {filename}")
    else:
        print("\nNo stocks found matching the breakout criteria.")
