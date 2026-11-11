"""엑셀 원본(전략결과.xlsx)에서 GA 입력 데이터와 엑셀 계산값을 꺼내 CSV로 저장.

사용: python scripts/extract_ga_excel.py <전략결과.xlsx 경로>
출력: data/raw/ga_kospi200.csv (gitignore 대상)
"""
import sys
from pathlib import Path

import openpyxl
import pandas as pd

SHEET = "KOSPI 200 Future (1)"
ROOT = Path(__file__).resolve().parents[1]


def main(path: str) -> None:
    ws = openpyxl.load_workbook(path, data_only=True)[SHEET]
    rows = []
    for r in range(9, ws.max_row + 1):
        d = ws.cell(r, 2).value
        if d in (None, "INITIAL"):
            continue
        rows.append({
            "date": pd.to_datetime(d, format="%m/%d/%Y"),
            "price": ws.cell(r, 3).value, "open": ws.cell(r, 4).value,
            "high": ws.cell(r, 5).value, "low": ws.cell(r, 6).value, "volume": ws.cell(r, 7).value,
            "mfi": ws.cell(r, 8).value, "bb_width": ws.cell(r, 9).value, "bb_pctb": ws.cell(r, 10).value,
            # 검증용 엑셀 계산값 (R, AE, AF 열)
            "xl_trade": ws.cell(r, 18).value, "xl_pnl": ws.cell(r, 31).value, "xl_return_rate": ws.cell(r, 32).value,
        })
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    out = ROOT / "data" / "raw" / "ga_kospi200.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"saved {out} ({len(df)} rows, {df.date.min().date()} ~ {df.date.max().date()})")


if __name__ == "__main__":
    main(sys.argv[1])
