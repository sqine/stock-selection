import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime, timedelta
from pykrx import stock
import time

warnings.filterwarnings('ignore')

def get_all_tickers():
    print("Fetching stock lists from KRX...")
    kospi = stock.get_market_ticker_list(market="KOSPI")
    kosdaq = stock.get_market_ticker_list(market="KOSDAQ")
    
    # Filter by market cap (e.g., top 500 from each or those above 100B)
    # To be thorough but efficient, let's get tickers and names
    all_tickers = []
    for ticker in kospi:
        all_tickers.append({'ticker': ticker + ".KS", 'name': stock.get_market_ticker_name(ticker), 'market': 'KOSPI'})
    for ticker in kosdaq:
        all_tickers.append({'ticker': ticker + ".KQ", 'name': stock.get_market_ticker_name(ticker), 'market': 'KOSDAQ'})
    
    return pd.DataFrame(all_tickers)

def screen_stocks(stock_df):
    period = 20
    multiplier = 2.0
    results = []
    
    tickers = stock_df['ticker'].tolist()
    print(f"Downloading data for {len(tickers)} stocks...")
    
    # Download in batches to avoid overwhelming the API
    batch_size = 100
    for i in range(0, len(tickers), batch_size):
        batch_tickers = tickers[i:i+batch_size]
        try:
            # Download 3 months of data to ensure we have enough for 20-day EMA/ATR
            data = yf.download(batch_tickers, period='3mo', interval='1d', progress=False, group_by='ticker')
            
            for ticker in batch_tickers:
                try:
                    df = data[ticker]
                    if df.empty or len(df) < period + 1: continue
                    
                    # Clean data (remove NaNs)
                    df = df.dropna()
                    if len(df) < period + 1: continue

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
                    
                    # Last values
                    current_close = df['Close'].iloc[-1]
                    current_upper = upper_band.iloc[-1]
                    current_lower = lower_band.iloc[-1]
                    
                    # Ensure they are scalar
                    if isinstance(current_close, pd.Series): current_close = current_close.iloc[0]
                    if isinstance(current_upper, pd.Series): current_upper = current_upper.iloc[0]
                    if isinstance(current_lower, pd.Series): current_lower = current_lower.iloc[0]

                    # Keltner Position
                    k_pos = (current_close - current_lower) / (current_upper - current_lower) if (current_upper - current_lower) != 0 else 0
                    
                    # Conditions
                    cond1 = current_close > current_upper
                    cond2 = k_pos >= 0.8
                    
                    if cond1 and cond2:
                        name = stock_df[stock_df['ticker'] == ticker]['name'].values[0]
                        market = stock_df[stock_df['ticker'] == ticker]['market'].values[0]
                        prev_close = df['Close'].iloc[-2]
                        if isinstance(prev_close, pd.Series): prev_close = prev_close.iloc[0]
                        change = ((current_close - prev_close) / prev_close) * 100
                        
                        results.append({
                            'Market': market,
                            'Ticker': ticker.split('.')[0],
                            'Name': name,
                            'Close': int(current_close),
                            'Upper': round(float(current_upper), 2),
                            'Pos': round(float(k_pos), 3),
                            'Change(%)': round(float(change), 2)
                        })
                except Exception as e:
                    # print(f"Error processing {ticker}: {e}")
                    continue
            
            print(f"Processed {min(i+batch_size, len(tickers))}/{len(tickers)}...")
            # Small sleep to be polite
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Batch error: {e}")
            continue
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    stock_df = get_all_tickers()
    
    # Optional: Filter for some basic criteria like market cap or volume
    # But user asked for a thorough investigation, so let's do all for now
    # but maybe focus on those with a name (already done in get_all_tickers)
    
    final_results = screen_stocks(stock_df)
    
    if not final_results.empty:
        print("\n=== Screening Results (Satisfying Keltner Breakout) ===")
        # Sort by Change descending
        final_results = final_results.sort_values(by='Change(%)', ascending=False)
        print(final_results.to_markdown(index=False))
        
        # Save to CSV
        filename = f"keltner_screening_{datetime.now().strftime('%Y%m%d')}.csv"
        final_results.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\nResults saved to {filename}")
    else:
        print("\nNo stocks found matching the criteria today.")
