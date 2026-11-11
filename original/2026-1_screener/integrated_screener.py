import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime
import time
import os

warnings.filterwarnings('ignore')

def get_sp500_tickers():
    """Fetch S&P 500 tickers from Wikipedia with User-Agent to avoid 403 Error."""
    print("Fetching S&P 500 tickers from Wikipedia...")
    try:
        import requests
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        tables = pd.read_html(response.text)
        df = tables[0]
        # Some tickers have '.' instead of '-' (e.g., BRK.B), yfinance prefers '-'
        tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        names = df['Security'].tolist()
        return pd.DataFrame({'Code': tickers, 'Name': names, 'Market': 'S&P 500'})
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        return pd.DataFrame()

def get_kospi_tickers():
    """Major KOSPI stocks from the previous screener."""
    stocks = [
        ('005930.KS', 'Samsung Electronics'), ('000660.KS', 'SK hynix'), ('373220.KS', 'LG Energy Solution'),
        ('207940.KS', 'Samsung Biologics'), ('005380.KS', 'Hyundai Motor'), ('000270.KS', 'Kia'),
        ('068270.KS', 'Celltrion'), ('005490.KS', 'POSCO Holdings'), ('035420.KS', 'Naver'),
        ('051910.KS', 'LG Chem'), ('006400.KS', 'Samsung SDI'), ('105560.KS', 'KB Financial'),
        ('055550.KS', 'Shinhan Financial'), ('003550.KS', 'LG'), ('012330.KS', 'Hyundai Mobis'),
        ('032830.KS', 'Samsung Life'), ('000810.KS', 'Samsung Fire'), ('015760.KS', 'KEPCO'),
        ('033780.KS', 'KT&G'), ('003670.KS', 'POSCO Future M'), ('011780.KS', 'Kumho Petrochemical'),
        ('010130.KS', 'Korea Zinc'), ('009150.KS', 'Samsung Electro-Mechanics'), ('034730.KS', 'SK'),
        ('018260.KS', 'Samsung SDS'), ('034220.KS', 'LG Display'), ('066570.KS', 'LG Electronics'),
        ('009540.KS', 'HD Korea Shipbuilding'), ('010950.KS', 'S-Oil'), ('036570.KS', 'NCSoft'),
        ('000720.KS', 'Hyundai E&C'), ('011170.KS', 'Lotte Chemical'), ('004020.KS', 'Hyundai Steel'),
        ('028260.KS', 'Samsung C&T'), ('035720.KS', 'Kakao'), ('001500.KS', 'HMM'),
        ('086790.KS', 'Hana Financial'), ('017670.KS', 'SK Telecom'), ('030200.KS', 'KT'),
        ('010140.KS', 'Samsung Heavy'), ('000100.KS', 'Yuhan'), ('008770.KS', 'Hotel Shilla'),
        ('021240.KS', 'Coway'), ('097950.KS', 'CJ CheilJedang'), ('004170.KS', 'Shinsegae'),
        ('000080.KS', 'HiteJinro'), ('005830.KS', 'DB Insurance'), ('000120.KS', 'CJ Logistics'),
        ('000210.KS', 'DL')
    ]
    return pd.DataFrame([{'Code': code, 'Name': name, 'Market': 'KOSPI'} for code, name in stocks])

def screen_market(stock_list, market_name):
    period = 20
    multiplier = 2.0
    breakouts = []
    
    print(f"\nScreening {len(stock_list)} stocks in {market_name}...")
    
    tickers = stock_list['Code'].tolist()
    batch_size = 50
    
    for i in range(0, len(tickers), batch_size):
        batch_tickers = tickers[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{len(tickers)//batch_size + 1}...")
        try:
            # Download data
            data = yf.download(batch_tickers, period='3mo', interval='1d', progress=False, group_by='ticker')
            
            for ticker in batch_tickers:
                try:
                    # Handle both single and multiple ticker download structures
                    if len(batch_tickers) == 1:
                        df = data
                    else:
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
                    
                    # Position calculation
                    channel_width = current_upper - current_lower
                    k_pos = (current_close - current_lower) / channel_width if channel_width != 0 else 0
                        
                    # Breakout criteria: Close > Upper Band and Relative Position >= 0.8
                    if current_close > current_upper and k_pos >= 0.8:
                        prev_close = df['Close'].iloc[-2]
                        change_1d = ((current_close - prev_close) / prev_close) * 100
                        
                        name = stock_list[stock_list['Code'] == ticker]['Name'].values[0]
                        
                        breakouts.append({
                            'Market': market_name,
                            'Code': ticker,
                            'Name': name,
                            'Close': round(float(current_close), 2),
                            'Upper': round(float(current_upper), 2),
                            'Pos': round(float(k_pos), 3),
                            'Chg(1d)%': round(float(change_1d), 2)
                        })
                except Exception:
                    continue
            time.sleep(0.5) # Avoid hitting API limits
        except Exception as e:
            print(f"Error in batch: {e}")
            continue
            
    return pd.DataFrame(breakouts)

if __name__ == "__main__":
    # 1. Get Tickers
    kospi_stocks = get_kospi_tickers()
    sp500_stocks = get_sp500_tickers()
    
    # 2. Screen Markets
    print("Starting Multi-Market Screening...")
    
    all_results = []
    
    # Screen KOSPI
    kospi_results = screen_market(kospi_stocks, "KOSPI")
    if not kospi_results.empty:
        all_results.append(kospi_results)
        
    # Screen S&P 500
    if not sp500_stocks.empty:
        sp500_results = screen_market(sp500_stocks, "S&P 500")
        if not sp500_results.empty:
            all_results.append(sp500_results)
    
    # 3. Consolidate and Display Results
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        print("\n" + "="*50)
        print("   INTEGRATED SCREENER RESULTS (KELTNER BREAKOUT)   ")
        print("="*50)
        
        # Sort by 1d change within each market
        final_df = final_df.sort_values(by=['Market', 'Chg(1d)%'], ascending=[True, False])
        
        print(final_df.to_markdown(index=False))
        
        # Save to CSV
        filename = f"integrated_results_{datetime.now().strftime('%Y%m%d')}.csv"
        final_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\nSaved {len(final_df)} matches to {filename}")
    else:
        print("\nNo stocks found matching the breakout criteria in any market.")
