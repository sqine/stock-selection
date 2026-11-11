"""엑셀 원본 수식과 Python 이식본이 같은 값을 내는지 확인. 데이터가 없으면 건너뛴다."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stock_selection.ga import EXCEL_SOLUTION, evaluate, simulate

DATA = Path(__file__).resolve().parents[1] / "data" / "raw" / "ga_kospi200.csv"
pytestmark = pytest.mark.skipif(not DATA.exists(), reason="data/raw/ga_kospi200.csv 없음 (scripts/extract_ga_excel.py 실행 필요)")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(DATA, parse_dates=["date"])


def test_rowwise_match_excel(df):
    res = simulate(df, EXCEL_SOLUTION)
    assert np.allclose(res["trade"], df["xl_trade"])
    assert np.allclose(res["pnl"], df["xl_pnl"])
    assert np.allclose(res["return_rate"], df["xl_return_rate"])


def test_final_numbers_match_excel(df):
    ev = evaluate(df, EXCEL_SOLUTION)
    assert ev["pnl"] == pytest.approx(533.31, abs=0.01)          # 엑셀 E2
    assert ev["return_rate"] == pytest.approx(0.31631, abs=1e-5)  # 엑셀 E3
    assert ev["n_buys"] == 18                                     # 엑셀 E4
