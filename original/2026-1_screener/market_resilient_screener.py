import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime
import time
import os

warnings.filterwarnings('ignore')

def get_tickers():
    stocks = []
    if os.path.exists('temp_tickers.txt'):
        with open('temp_tickers.txt', 'r') as f:
            for line in f:
                if '|' in line:
                    name, code = line.strip().split('|')
                    stocks.append({'Code': code.strip() + ".KS", 'Name': name.strip()})
    return pd.DataFrame(stocks)

def screen_resilient_stocks(stock_list):
    print("Fetching KOSPI Index (^KS11) data...")
    kospi = yf.download("^KS11", period="1mo", interval="1d", progress=False)
    kospi_pct = kospi['Close'].pct_change()
    
    # 지수 하락일 필터 (최근 5일 중)
    kospi_down_days = kospi_pct.iloc[-5:][kospi_pct.iloc[-5:] < 0].index
    
    period = 20
    multiplier = 2.0
    results = []
    
    tickers = stock_list['Code'].tolist()
    print(f"Screening {len(tickers)} stocks for Resilience & Keltner Breakout...")
    
    # 배치 처리
    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        try:
            data = yf.download(batch, period="3mo", interval="1d", progress=False, group_by='ticker')
            
            for ticker in batch:
                try:
                    df = data[ticker].dropna()
                    if len(df) < 21: continue
                    
                    # 1. 지수 대비 수익률 (RS) > 0 (최근 5일)
                    stock_ret_5d = (df['Close'].iloc[-1] / df['Close'].iloc[-6] - 1)
                    kospi_ret_5d = (kospi['Close'].iloc[-1] / kospi['Close'].iloc[-6] - 1)
                    if isinstance(stock_ret_5d, pd.Series): stock_ret_5d = stock_ret_5d.iloc[0]
                    if isinstance(kospi_ret_5d, pd.Series): kospi_ret_5d = kospi_ret_5d.iloc[0]
                    
                    rs_score = stock_ret_5d - kospi_ret_5d
                    if rs_score <= 0: continue # 지수보다 약하면 탈락
                    
                    # 2. 시장 하락일 방어력 (Resilience)
                    # 지수가 빠진 날, 종목 수익률 > 지수 수익률인지 확인
                    stock_pct = df['Close'].pct_change()
                    is_resilient = True
                    for day in kospi_down_days:
                        if day in stock_pct.index:
                            if stock_pct.loc[day].item() < kospi_pct.loc[day].item():
                                is_resilient = False
                                break
                    if not is_resilient: continue

                    # 3. 좁은 박스권 유지 (최근 10일 변동폭 < 10%)
                    high_10d = df['High'].iloc[-10:].max()
                    low_10d = df['Low'].iloc[-10:].min()
                    volatility_10d = (high_10d - low_10d) / low_10d
                    if isinstance(volatility_10d, pd.Series): volatility_10d = volatility_10d.iloc[0]
                    if volatility_10d > 0.10: continue # 10% 이상 흔들렸으면 제외 (과열/불안정)

                    # 4. 캘트너 상단 돌파 및 거래량 (EMA 20)
                    high_low = df['High'] - df['Low']
                    high_close = (df['High'] - df['Close'].shift()).abs()
                    low_close = (df['Low'] - df['Close'].shift()).abs()
                    atr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(period).mean()
                    ema = df['Close'].ewm(span=period, adjust=False).mean()
                    upper_band = ema + (multiplier * atr)
                    
                    current_close = df['Close'].iloc[-1].item()
                    current_upper = upper_band.iloc[-1].item()
                    
                    # 돌파 조건 + 거래량 200%
                    avg_vol = df['Volume'].iloc[-21:-1].mean().item()
                    curr_vol = df['Volume'].iloc[-1].item()
                    vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 0
                    
                    if current_close > current_upper and vol_ratio >= 1.5: # 2배는 엄격하므로 1.5배로 소폭 완화
                        name = stock_list[stock_list['Code'] == ticker]['Name'].values[0]
                        results.append({
                            'Code': ticker.split('.')[0],
                            'Name': name,
                            'Close': int(current_close),
                            'RS_Score': round(float(rs_score)*100, 2),
                            'Vol_10d%': round(float(volatility_10d)*100, 2),
                            'Vol_Ratio': round(float(vol_ratio), 2),
                            'Chg%': round(float(stock_pct.iloc[-1])*100, 2)
                        })
                except Exception: continue
        except Exception: continue
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    stocks = get_tickers()
    final_results = screen_resilient_stocks(stocks)
    
    if not final_results.empty:
        print("\n=== [Market Resilience] 지수 하락을 이기는 종목 ===")
        print(final_results.sort_values(by='RS_Score', ascending=False).to_markdown(index=False))
    else:
        print("\n현재 시장 하락을 방어하며 돌파하는 종목이 없습니다. (현금 보유 권장)")
