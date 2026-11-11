"""주간 추천 평가: 추천 마감일 이후 첫 금요일 시가 매수 → 다음 목요일 종가 매도.

실제 과제 평가 규칙과 같다. 금요일이 휴장이면 다음 거래일 시가, 목요일이 휴장이면
직전 거래일 종가를 쓴다.
"""
from __future__ import annotations

from typing import Callable

import pandas as pd

from .metrics import apply_costs


def holding_window(prices: pd.DataFrame, ref_date: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    ref = pd.Timestamp(ref_date)
    friday = ref + pd.Timedelta(days=(4 - ref.weekday()) % 7)
    thursday = friday + pd.Timedelta(days=6)
    idx = prices.index
    i_in = idx.searchsorted(friday)
    i_out = idx.searchsorted(thursday, side="right") - 1
    if i_in >= len(idx) or i_out < i_in:
        raise ValueError(f"{ref.date()}: 보유 구간 가격이 없음")
    return idx[i_in], idx[i_out]


def evaluate_picks(picks: pd.DataFrame, load: Callable[[str], pd.DataFrame], *,
                   buy_cost: float, sell_cost: float, benchmark: str = "KOSPI") -> pd.DataFrame:
    """picks: ref_date(추천 파일 저장일/마감일), ticker, name 열을 가진 표. 한 행 = 한 주."""
    bm = load(benchmark)
    out = []
    for row in picks.itertuples(index=False):
        px = load(row.ticker)
        d_in, d_out = holding_window(px, row.ref_date)
        p_in, p_out = px.at[d_in, "open"], px.at[d_out, "close"]
        gross = p_out / p_in - 1
        out.append({
            **row._asdict(),
            "buy_date": d_in.date(), "buy_price": p_in,
            "sell_date": d_out.date(), "sell_price": p_out,
            "gross_return": gross,
            "net_return": float(apply_costs(pd.Series([gross]), buy_cost, sell_cost).iloc[0]),
            "benchmark_return": bm.at[d_out, "close"] / bm.at[d_in, "open"] - 1,
        })
    return pd.DataFrame(out)
