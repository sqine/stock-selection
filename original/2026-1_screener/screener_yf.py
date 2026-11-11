import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# List of top KOSPI stocks from search results
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

def screen_stocks(stock_list):
    breakouts = []
    period = 20
    multiplier = 2.0
    
    print(f"Screening {len(stock_list)} major KOSPI stocks...")
    
    for ticker_code, name in stock_list:
        try:
            # Fetch last 40 days of daily data
            df = yf.download(ticker_code, period='2mo', interval='1d', progress=False)
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
            
            # Use the last row for signal
            current_close = df['Close'].iloc[-1].item()
            current_upper = upper_band.iloc[-1].item()
            current_lower = lower_band.iloc[-1].item()
            
            # Keltner Position: (Close - Lower) / (Upper - Lower)
            if (current_upper - current_lower) != 0:
                k_pos = (current_close - current_lower) / (current_upper - current_lower)
            else:
                k_pos = 0

            # Condition: Upper < Close AND Position >= 0.8
            if current_close > current_upper and k_pos >= 0.8:
                prev_close = df['Close'].iloc[-2].item()
                change = ((current_close - prev_close) / prev_close) * 100
                breakouts.append({
                    'Ticker': ticker_code,
                    'Name': name,
                    'Close': int(current_close),
                    'Upper': round(current_upper, 2),
                    'Position': round(k_pos, 3),
                    'Change(%)': round(change, 2)
                })
        except Exception as e:
            # print(f"Error processing {ticker_code}: {e}")
            continue
            
    return pd.DataFrame(breakouts)

results = screen_stocks(stocks)
if not results.empty:
    print(results.to_markdown(index=False))
else:
    print("No major KOSPI stocks found matching the criteria.")
