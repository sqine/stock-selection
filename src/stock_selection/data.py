"""가격 데이터 수집. 네이버 금융 일봉 차트(fchart)를 받아 data/raw/prices/ 에 캐시한다.

- 종목: 6자리 코드 (예: '000660'), 지수: 'KOSPI'
- 가격은 네이버가 제공하는 수정주가(액면분할·무상증자 반영)다.
- data/raw 는 .gitignore 대상이다. 재현 시 이 모듈이 다시 받아온다.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

import pandas as pd

URL = "https://fchart.stock.naver.com/sise.nhn?symbol={symbol}&timeframe=day&count={count}&requestType=0"
ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "raw" / "prices"


def _download(symbol: str, count: int) -> pd.DataFrame:
    with urllib.request.urlopen(URL.format(symbol=symbol, count=count), timeout=20) as resp:
        text = resp.read().decode("euc-kr", errors="ignore")
    rows = re.findall(r'item data="([^"]*)"', text)
    if not rows:
        raise RuntimeError(f"{symbol}: 가격 데이터가 비어 있음")
    df = pd.DataFrame([r.split("|") for r in rows], columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    return df.set_index("date").astype(float)


def load_prices(symbol: str, *, count: int = 800, refresh: bool = False) -> pd.DataFrame:
    """일봉 OHLCV. 캐시가 있으면 캐시를 쓴다."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{symbol}.csv"
    if path.exists() and not refresh:
        return pd.read_csv(path, index_col="date", parse_dates=["date"])
    df = _download(symbol, count)
    df.to_csv(path)
    return df
