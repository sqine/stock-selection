from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"

SETUP = r'''import sys, yaml
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib import font_manager
for f in ["AppleGothic", "Malgun Gothic", "NanumGothic", "Noto Sans CJK KR", "Noto Sans CJK JP", "Noto Serif CJK JP"]:
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = f; break
plt.rcParams["axes.unicode_minus"] = False
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)
CFG = yaml.safe_load(open(ROOT / "configs/base.yaml"))
RES = ROOT / "results"; (RES / "figures").mkdir(parents=True, exist_ok=True)'''


def md(s):
    return nbf.v4.new_markdown_cell(s)


def code(s):
    return nbf.v4.new_code_cell(s)


def weekly():
    cells = [
        md("""# 01. 주간 종목 추천 평가 (2025-2 투자공학, 2026-1 금융공학)

- 매주 과제로 1종목을 추천했다. 평가 규칙: **추천 마감 후 첫 금요일 시가 매수 → 다음 목요일 종가 매도**.
- 추천 종목·주차·마감일은 LearnUs 과제 제출 내역과 제출 파일명에서 옮겨 `configs/picks.csv` 에 적었다.
- 보유 구간이 중간·기말고사 주간과 겹친 주는 실제로 평가하지 않았으므로 제외한다(2026-1 5·11주차).
- 가격: 네이버 금융 일봉(수정주가). 비용: 매수 0.015%, 매도 0.195%(수수료+거래세).
- 방법론 설명과 한계는 README 3·5절에 있다."""),
        code(SETUP + "\n" + r'''from stock_selection.data import load_prices
from stock_selection.backtest import evaluate_picks
from stock_selection import metrics as M
W = CFG["weekly_picks"]
picks = pd.read_csv(ROOT / W["picks_file"], dtype={"ticker": str}, parse_dates=["ref_date"])
picks[["semester", "week", "ref_date", "ticker", "name", "candidate_source", "exam_overlap"]]'''),
        md("## 1. 주차별 매매 결과"),
        code(r'''trades_all = evaluate_picks(picks, load_prices, buy_cost=W["costs"]["buy"], sell_cost=W["costs"]["sell"], benchmark=W["benchmark"])
trades = trades_all[~trades_all["exam_overlap"]].reset_index(drop=True) if W["exclude_exam_weeks"] else trades_all
cols = ["semester", "week", "name", "buy_date", "buy_price", "sell_date", "sell_price", "gross_return", "net_return", "benchmark_return", "exam_overlap"]
trades_all[cols].to_csv(RES / "weekly_trades.csv", index=False)
trades_all[cols].style.format({"buy_price": "{:,.0f}", "sell_price": "{:,.0f}", "gross_return": "{:+.2%}", "net_return": "{:+.2%}", "benchmark_return": "{:+.2%}"})'''),
        md("## 2. 학기별 성과표 (시험 주간 제외)"),
        code(r'''def col(g):
    turn = M.turnover(pd.DataFrame(np.tile([[1.0], [0.0]], (len(g), 1)), columns=["pos"]))
    s = M.summary(g["net_return"].reset_index(drop=True), W["periods_per_year"], benchmark=g["benchmark_return"],
                  n_trades=2 * len(g), turnover_per_rebal=turn, rf_annual=W["rf_annual"])
    s["누적수익률(비용 전)"] = M.cumulative_return(g["gross_return"])
    s["아웃샘플 기간"] = f'{g["buy_date"].min()} ~ {g["sell_date"].max()}'
    return s
table = {f"{k} ({len(g)}주)": col(g) for k, g in trades.groupby("semester")}
table[f"전체 ({len(trades)}주)"] = col(trades)
md_table = M.to_markdown(table)
(RES / "weekly_summary.md").write_text(md_table + "\n")
print(md_table)'''),
        md("## 3. 민감도: 시험 주간 포함 / 단순 합산"),
        code(r'''rows = {}
for k, g in trades_all.groupby("semester"):
    ex = g[~g["exam_overlap"]]
    rows[k] = {"시험 주간 제외(본 결과)": M.cumulative_return(ex["net_return"]),
               "시험 주간 포함": M.cumulative_return(g["net_return"]),
               "단순 합산(제외 기준)": ex["net_return"].sum()}
sens = pd.DataFrame(rows)
sens.to_csv(RES / "weekly_sensitivity.csv")
sens.style.format("{:+.2%}")'''),
        md("""## 4. 결과가 무엇에 기대고 있는가

- 2026-1은 9주 중 5주가 SK하이닉스다. 같은 기간 SK하이닉스 단순 보유, KOSPI 보유와 비교한다.
- 상위 몇 주를 빼면 결과가 얼마나 남는지(집중도)를 본다."""),
        code(r'''def contrib(g, top=3):
    r = g.sort_values("net_return", ascending=False)["net_return"]
    return {"전체 누적": M.cumulative_return(g["net_return"]),
            f"상위 {top}주 제외 누적": M.cumulative_return(r.iloc[top:]),
            "상위 1주 제외 누적": M.cumulative_return(r.iloc[1:])}
conc = pd.DataFrame({k: contrib(g) for k, g in trades.groupby("semester")})

g26 = trades[trades["semester"] == "2026-1"]
hx = g26[g26["ticker"] == "000660"]
px = load_prices("000660"); kospi = load_prices("KOSPI")
d0, d1 = pd.Timestamp(hx["buy_date"].min()), pd.Timestamp(hx["sell_date"].max())
bh = {"SK하이닉스 주간 매매(본 전략, 비용 후)": M.cumulative_return(hx["net_return"]),
      "SK하이닉스 단순 보유(같은 구간)": px.at[d1, "close"] / px.at[d0, "open"] - 1,
      "KOSPI 단순 보유(같은 구간)": kospi.at[d1, "close"] / kospi.at[d0, "open"] - 1}
s0, s1 = pd.Timestamp(g26["buy_date"].min()), pd.Timestamp(g26["sell_date"].max())
bh["KOSPI 단순 보유(2026-1 전체 평가 구간)"] = kospi.at[s1, "close"] / kospi.at[s0, "open"] - 1
print(f"SK하이닉스 구간: {d0.date()} ~ {d1.date()}")
display(conc.style.format("{:+.2%}"), pd.Series(bh).to_frame("누적").style.format("{:+.2%}"))
conc.to_csv(RES / "weekly_concentration.csv"); pd.Series(bh).to_csv(RES / "weekly_vs_buyhold.csv")'''),
        md("## 5. 누적 곡선"),
        code(r'''fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for ax, (k, g) in zip(axes, trades.groupby("semester")):
    x = range(1, len(g) + 1)
    ax.plot(x, (1 + g["net_return"]).cumprod().values - 1, marker="o", label="추천 종목(비용 후)")
    ax.plot(x, (1 + g["benchmark_return"]).cumprod().values - 1, marker="s", label="KOSPI(같은 주)")
    ax.set_title(f"{k} 주간 추천 누적수익률"); ax.set_xlabel("평가 주 순서"); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.grid(alpha=.3); ax.legend()
plt.tight_layout(); plt.savefig(RES / "figures/weekly_cumulative.png", dpi=150); plt.show()'''),
    ]
    return cells


def main():
    NB.mkdir(exist_ok=True)
    for name, cells in [("01_weekly_picks.ipynb", weekly())]:
        nb = nbf.v4.new_notebook(); nb.cells = cells
        nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
        nbf.write(nb, NB / name)
        print("wrote", NB / name)


if __name__ == "__main__":
    main()
