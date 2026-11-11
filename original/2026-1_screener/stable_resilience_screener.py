import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from datetime import datetime
import os

warnings.filterwarnings('ignore')

def get_ticker_list():
    """기존 분석된 주요 종목 리스트를 가져오거나 기본 종목을 반환합니다."""
    if os.path.exists('temp_tickers.txt'):
        stocks = []
        with open('temp_tickers.txt', 'r') as f:
            for line in f:
                if '|' in line:
                    name, code = line.strip().split('|')
                    stocks.append({'Code': code.strip() + ".KS", 'Name': name.strip()})
        return pd.DataFrame(stocks)
    else:
        # 파일이 없을 경우를 대비한 최소한의 우량주 리스트
        return pd.DataFrame([
            {'Code': '005930.KS', 'Name': '삼성전자'},
            {'Code': '000660.KS', 'Name': 'SK하이닉스'},
            {'Code': '005380.KS', 'Name': '현대차'},
            {'Code': '005490.KS', 'Name': 'POSCO홀딩스'},
            {'Code': '055550.KS', 'Name': '신한지주'}
        ])

def run_stable_screener():
    print(f"--- 스크리닝 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # 1. 지수 데이터 확보 (코스피)
    print("KOSPI 지수 분석 중...")
    kospi = yf.download("^KS11", period="6mo", interval="1d", progress=False)
    kospi_pct = kospi['Close'].pct_change()
    
    # 최근 10일 중 지수 하락일 특정
    recent_kospi_pct = kospi_pct.iloc[-10:]
    down_days = recent_kospi_pct[recent_kospi_pct < 0].index
    
    # 2. 종목 리스트 로드
    stock_df = get_ticker_list()
    tickers = stock_df['Code'].tolist()
    results = []

    print(f"총 {len(tickers)}개 종목의 하방 경직성 분석 중...")
    
    # 데이터 일괄 다운로드 (효율성)
    data = yf.download(tickers, period="6mo", interval="1d", progress=False, group_by='ticker')

    for ticker in tickers:
        try:
            df = data[ticker].dropna()
            if len(df) < 60: continue
            
            # A. 하방 경직성 점수 (Resilience Score)
            # 지수 하락일에 지수보다 수익률이 높았던 비율
            stock_pct = df['Close'].pct_change()
            win_count = 0
            valid_days = 0
            for day in down_days:
                if day in stock_pct.index:
                    valid_days += 1
                    if stock_pct.loc[day].item() > kospi_pct.loc[day].item():
                        win_count += 1
            
            resilience_score = win_count / valid_days if valid_days > 0 else 0
            
            # B. 상대 강도 (RS)
            stock_ret_1m = (df['Close'].iloc[-1] / df['Close'].iloc[-21] - 1).item()
            kospi_ret_1m = (kospi['Close'].iloc[-1] / kospi['Close'].iloc[-21] - 1).item()
            rs_1m = stock_ret_1m - kospi_ret_1m
            
            # C. 추세 및 변동성
            ma60 = df['Close'].rolling(60).mean().iloc[-1].item()
            current_close = df['Close'].iloc[-1].item()
            
            # 최근 10일 변동성 (표준편차)
            volatility = stock_pct.iloc[-10:].std()
            
            # 선정 조건:
            # 1. 하방 경직성 점수 0.7 이상 (지수 하락일의 70% 이상 방어)
            # 2. 1개월 상대강도 양수 (시장보다 강함)
            # 3. 주가가 60일 이평선 위 (우상향 혹은 중기 지지)
            if resilience_score >= 0.7 and rs_1m > 0 and current_close > ma60:
                name = stock_df[stock_df['Code'] == ticker]['Name'].values[0]
                results.append({
                    '종목코드': ticker.split('.')[0],
                    '종목명': name,
                    '방어성공률': f"{int(resilience_score*100)}%",
                    '상대강도(1M)': f"{round(rs_1m*100, 2)}%",
                    '현재가': int(current_close),
                    '60일선이격': round((current_close/ma60 - 1)*100, 2),
                    '변동성': round(volatility, 4)
                })
        except:
            continue

    # 결과 출력
    res_df = pd.DataFrame(results)
    if not res_df.empty:
        # 방어성공률과 상대강도가 높은 순으로 정렬
        res_df = res_df.sort_values(by=['방어성공률', '상대강도(1M)'], ascending=False)
        print("\n[ 결과: 시장 하락에도 잘 빠지지 않는 '방어주' 리스트 ]")
        print(res_df.to_markdown(index=False))
        print("\n* 방어성공률: 지수가 하락할 때 지수보다 수익률이 좋았던 확률입니다.")
    else:
        print("\n현재 조건(방어력 70% 이상)을 만족하는 종목이 없습니다.")

if __name__ == "__main__":
    run_stable_screener()
