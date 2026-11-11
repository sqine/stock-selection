import pandas as pd
import pytest

from stock_selection.backtest import evaluate_picks, holding_window


def _prices(dates, base=100.0):
    idx = pd.to_datetime(dates)
    return pd.DataFrame({"open": [base + i for i in range(len(idx))],
                         "close": [base + i + 0.5 for i in range(len(idx))]}, index=idx)


def test_window_friday_to_thursday():
    px = _prices(pd.bdate_range("2025-10-13", "2025-10-31"))
    d_in, d_out = holding_window(px, pd.Timestamp("2025-10-16"))  # 목요일 마감
    assert (d_in.date().isoformat(), d_out.date().isoformat()) == ("2025-10-17", "2025-10-23")


def test_window_holidays():
    # 금요일 휴장 → 다음 거래일 시가, 목요일 휴장 → 직전 거래일 종가
    days = [d for d in pd.bdate_range("2025-10-01", "2025-10-31") if d.date().isoformat() not in ("2025-10-10", "2025-10-16")]
    d_in, d_out = holding_window(_prices(days), pd.Timestamp("2025-10-09"))
    assert (d_in.date().isoformat(), d_out.date().isoformat()) == ("2025-10-13", "2025-10-15")


def test_evaluate_uses_open_and_close():
    px = _prices(pd.bdate_range("2025-10-13", "2025-10-31"))
    picks = pd.DataFrame({"ref_date": [pd.Timestamp("2025-10-16")], "ticker": ["X"], "name": ["x"]})
    out = evaluate_picks(picks, lambda s: px, buy_cost=0.0, sell_cost=0.0)
    buy, sell = px.at[pd.Timestamp("2025-10-17"), "open"], px.at[pd.Timestamp("2025-10-23"), "close"]
    assert out.loc[0, "gross_return"] == pytest.approx(sell / buy - 1)
    assert out.loc[0, "net_return"] == pytest.approx(out.loc[0, "gross_return"])
