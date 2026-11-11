"""성과 지표와 README용 결과표.

모든 함수는 '기간 수익률' 시리즈(단순수익률, 0.01 = 1%)를 입력으로 받는다.
periods_per_year 는 주간 52, 일간 252.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def apply_costs(gross: pd.Series, buy_cost: float, sell_cost: float) -> pd.Series:
    """왕복 1회 거래(매수 후 매도)를 가정해 비용을 차감한 수익률."""
    return (1 - buy_cost) * (1 + gross) * (1 - sell_cost) - 1


def cumulative_return(r: pd.Series) -> float:
    return float((1 + r).prod() - 1)


def annualized_return(r: pd.Series, periods_per_year: int) -> float:
    n = len(r)
    if n == 0:
        return float("nan")
    return float((1 + cumulative_return(r)) ** (periods_per_year / n) - 1)


def annualized_vol(r: pd.Series, periods_per_year: int) -> float:
    return float(r.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe(r: pd.Series, periods_per_year: int, rf_annual: float = 0.0) -> float:
    rf = (1 + rf_annual) ** (1 / periods_per_year) - 1
    ex = r - rf
    sd = ex.std(ddof=1)
    return float(ex.mean() / sd * np.sqrt(periods_per_year)) if sd > 0 else float("nan")


def max_drawdown(r: pd.Series) -> float:
    """복리 누적 자산곡선 기준 최대낙폭 (음수). 시작 자산 1을 고점 후보에 포함."""
    eq = np.concatenate([[1.0], (1 + r).cumprod().values])
    peak = np.maximum.accumulate(eq)
    return float((eq / peak - 1).min())


def calmar(r: pd.Series, periods_per_year: int) -> float:
    mdd = max_drawdown(r)
    return float(annualized_return(r, periods_per_year) / abs(mdd)) if mdd < 0 else float("nan")


def turnover(weights: pd.DataFrame) -> float:
    """리밸런싱 1회당 평균 편도 회전율 = max(매수 비중 합, 매도 비중 합).

    weights: 행=리밸런싱 시점, 열=종목(현금 제외), 값=목표비중. 첫 행은 전액 현금에서 시작.
    현금→A 전액 매수 = 100%, A→B 전액 교체 = 100%, 변화 없음 = 0%.
    """
    w = weights.fillna(0.0)
    d = w - w.shift(1).fillna(0.0)
    buys, sells = d.clip(lower=0).sum(axis=1), (-d).clip(lower=0).sum(axis=1)
    return float(np.maximum(buys, sells).mean())


def summary(r: pd.Series, periods_per_year: int, *, benchmark: pd.Series | None = None,
            n_trades: int | None = None, turnover_per_rebal: float | None = None,
            rf_annual: float = 0.0, min_periods_for_annualized: int = 52) -> dict:
    """README 결과표 한 열에 들어갈 값.

    표본이 min_periods_for_annualized 미만이면 연환산 수익률·칼마는 NaN으로 둔다
    (짧은 표본의 연환산은 의미가 없다).
    """
    short = len(r) < min_periods_for_annualized
    out = {
        "기간 수": len(r),
        "누적수익률": cumulative_return(r),
        "연환산수익률": float("nan") if short else annualized_return(r, periods_per_year),
        "연환산변동성": annualized_vol(r, periods_per_year),
        "샤프": sharpe(r, periods_per_year, rf_annual),
        "MDD": max_drawdown(r),
        "칼마": float("nan") if short else calmar(r, periods_per_year),
        "승률": float((r > 0).mean()),
    }
    if benchmark is not None:
        b = benchmark.reset_index(drop=True)
        out["벤치마크 누적"] = cumulative_return(b)
        out["벤치마크 초과 기간"] = int((r.reset_index(drop=True) > b).sum())
    if n_trades is not None:
        out["거래 횟수"] = n_trades
    if turnover_per_rebal is not None:
        out["회전율(회당)"] = turnover_per_rebal
    return out


_SIGNED_PCT = {"누적수익률", "누적수익률(비용 전)", "연환산수익률", "MDD", "벤치마크 누적", "수익률(엑셀 정의: 손익/필요현금)"}
_PCT = _SIGNED_PCT | {"연환산변동성", "승률", "회전율(회당)"}


def _fmt(key: str, v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if key in _PCT:
        return f"{v:+.2%}" if key in _SIGNED_PCT else f"{v:.2%}"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def to_markdown(cols: dict[str, dict]) -> str:
    """{열 이름: summary() 결과} → 마크다운 표 (행=지표)."""
    keys: list[str] = []
    for d in cols.values():
        for k in d:
            if k not in keys:
                keys.append(k)
    head = "| 지표 | " + " | ".join(cols) + " |"
    sep = "|---|" + "---|" * len(cols)
    rows = ["| " + k + " | " + " | ".join(_fmt(k, d.get(k)) for d in cols.values()) + " |" for k in keys]
    return "\n".join([head, sep, *rows])
