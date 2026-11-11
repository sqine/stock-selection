import numpy as np
import pandas as pd
import pytest

from stock_selection import metrics as m


def test_cumulative_and_costs():
    r = pd.Series([0.10, -0.05])
    assert m.cumulative_return(r) == pytest.approx(1.1 * 0.95 - 1)
    net = m.apply_costs(pd.Series([0.10]), 0.001, 0.002).iloc[0]
    assert net == pytest.approx(0.999 * 1.1 * 0.998 - 1)


def test_max_drawdown_includes_start():
    r = pd.Series([-0.10, 0.05, -0.20])
    eq = np.array([1, 0.9, 0.945, 0.756])
    assert m.max_drawdown(r) == pytest.approx(eq.min() - 1)


def test_sharpe_and_vol():
    r = pd.Series([0.01, 0.03, -0.01, 0.02])
    assert m.annualized_vol(r, 52) == pytest.approx(r.std(ddof=1) * np.sqrt(52))
    assert m.sharpe(r, 52) == pytest.approx(r.mean() / r.std(ddof=1) * np.sqrt(52))


def test_turnover_full_replacement():
    w = pd.DataFrame([{"A": 1.0}, {"B": 1.0}, {"B": 1.0}])
    assert m.turnover(w) == pytest.approx(2 / 3)


def test_summary_short_sample_and_markdown():
    r = pd.Series([0.02, -0.01, 0.03])
    s = m.summary(r, 52, benchmark=pd.Series([0.01, 0.0, 0.01]), n_trades=6)
    assert np.isnan(s["연환산수익률"]) and np.isnan(s["칼마"])
    assert s["벤치마크 초과 기간"] == 2
    md = m.to_markdown({"전략": s})
    assert md.splitlines()[0] == "| 지표 | 전략 |"
    assert "| 거래 횟수 | 6 |" in md
