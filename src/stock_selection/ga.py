from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd


def mfi(df: pd.DataFrame, n: int = 14) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    mf = tp * df["volume"]
    pos = mf.where(tp > tp.shift(1), 0.0).rolling(n).sum()
    neg = mf.where(tp < tp.shift(1), 0.0).rolling(n).sum()
    return 100 - 100 / (1 + pos / neg)


def bollinger(close: pd.Series, n: int = 20, k: float = 2.0) -> tuple[pd.Series, pd.Series]:
    m = close.rolling(n).mean()
    s = close.rolling(n).std(ddof=0)
    up, lo = m + k * s, m - k * s
    return (up - lo) / m, (close - lo) / (up - lo)


@dataclass
class Params:
    mfi_lo: float
    mfi_hi: float
    bbw_lo: float
    pctb_lo: float
    first_buy: int
    after_buy: int
    first_sell: int
    after_sell: int
    K: int
    N: int
    bbw_hi: float = 1.0
    init_cash: float = 0.0


BOUNDS = {
    "mfi_lo": (20, 90), "mfi_hi": (20, 90), "bbw_lo": (0.01, 0.2), "pctb_lo": (-0.2, 0.8),
    "first_buy": (1, 20), "after_buy": (0, 10), "first_sell": (1, 20), "after_sell": (1, 10),
    "K": (1, 5), "N": (1, 4),
}
INT_KEYS = {"first_buy", "after_buy", "first_sell", "after_sell", "K", "N"}

EXCEL_SOLUTION = Params(mfi_lo=32.35968852991223, mfi_hi=50.066213253916345,
                        bbw_lo=0.11663104606635452, pctb_lo=0.21639738083649301,
                        first_buy=1, after_buy=0, first_sell=1, after_sell=1, K=2, N=3)


def _arrays(df: pd.DataFrame):
    return (df["price"].to_numpy(float), df["mfi"].to_numpy(float),
            df["bb_width"].to_numpy(float), df["bb_pctb"].to_numpy(float))


def _core(c, mfi_v, bbw_v, pctb_v, p: Params, keep_rows: bool):
    sig = ((mfi_v <= p.mfi_hi).astype(int) + (mfi_v >= p.mfi_lo).astype(int)
           + ((bbw_v >= p.bbw_lo) & (bbw_v <= p.bbw_hi)).astype(int) + (pctb_v >= p.pctb_lo).astype(int))
    P = (sig >= p.N).astype(int)
    n = len(c)
    rows = np.zeros((n, 5)) if keep_rows else None
    q, prevP, pos, prevR = 0, 0, 0.0, 0.0
    v = y = loan = prevX = 0.0
    cash = p.init_cash
    for t in range(n):
        q = q + 1 if P[t] == prevP else 1
        if q >= p.K:
            if P[t] > 0:
                r = p.first_buy if pos == 0 else p.after_buy
            else:
                r = -min(p.after_sell if prevR < 0 else p.first_sell, pos)
        else:
            r = 0
        pos += r
        ab = r * c[t] if r > 0 else 0.0
        ac = max(ab - cash, 0.0)
        cash = cash + ac - ab + prevX
        x = -r * c[t] if r < 0 else 0.0
        v += ab; y += x; loan += ac
        if keep_rows:
            rows[t] = (r, pos, v, y, loan)
        prevP, prevR, prevX = P[t], r, x
    if not keep_rows:
        pnl = pos * c[-1] + y - v
        return pnl / loan if loan else 0.0
    return P, rows


def simulate(df: pd.DataFrame, p: Params) -> pd.DataFrame:
    c, mv, bw, pb = _arrays(df)
    P, rows = _core(c, mv, bw, pb, p, keep_rows=True)
    R, S, V, Y, AD = rows.T
    AE = S * c + Y - V
    AF = np.divide(AE, AD, out=np.zeros(len(c)), where=AD != 0)
    return pd.DataFrame({"date": df["date"].to_numpy(), "price": c, "signal": P, "trade": R,
                         "position": S, "pnl": AE, "needed_cash": AD, "return_rate": AF})


def evaluate(df: pd.DataFrame, p: Params) -> dict:
    res = simulate(df, p)
    capital = res["needed_cash"].iloc[-1]
    equity = capital + res["pnl"] if capital > 0 else pd.Series(np.ones(len(res)))
    daily = equity.pct_change().fillna(0.0)
    return {
        "return_rate": float(res["return_rate"].iloc[-1]),
        "pnl": float(res["pnl"].iloc[-1]),
        "needed_cash": float(capital),
        "n_buys": int((res["trade"] > 0).sum()),
        "n_sells": int((res["trade"] < 0).sum()),
        "max_position": float(res["position"].max()),
        "daily_returns": daily,
        "result": res,
    }


def _decode(x: np.ndarray) -> Params:
    keys = list(BOUNDS)
    d = {}
    for k, v in zip(keys, x):
        lo, hi = BOUNDS[k]
        v = float(np.clip(v, lo, hi))
        d[k] = int(round(v)) if k in INT_KEYS else v
    return Params(**d)


def optimize(df: pd.DataFrame, *, pop: int = 60, gens: int = 80, elite: int = 4,
             mut_rate: float = 0.2, seed: int = 0) -> tuple[Params, float, list[float]]:
    rng = np.random.default_rng(seed)
    lo = np.array([b[0] for b in BOUNDS.values()], float)
    hi = np.array([b[1] for b in BOUNDS.values()], float)
    X = rng.uniform(lo, hi, size=(pop, len(lo)))
    arrs = _arrays(df)

    def fit(x):
        return _core(*arrs, _decode(x), keep_rows=False)

    f = np.array([fit(x) for x in X])
    history = []
    for _ in range(gens):
        order = np.argsort(-f)
        X, f = X[order], f[order]
        history.append(float(f[0]))
        children = [X[i].copy() for i in range(elite)]
        while len(children) < pop:
            a, b = (X[min(rng.integers(0, pop, 3))] for _ in range(2))
            mask = rng.random(len(lo)) < 0.5
            child = np.where(mask, a, b)
            m = rng.random(len(lo)) < mut_rate
            child = child + m * rng.normal(0, 0.1 * (hi - lo))
            children.append(np.clip(child, lo, hi))
        X = np.array(children)
        f = np.array([fit(x) for x in X])
    best = int(np.argmax(f))
    history.append(float(f[best]))
    return _decode(X[best]), float(f[best]), history


def params_table(ps: dict[str, Params]) -> pd.DataFrame:
    return pd.DataFrame({k: {kk: vv for kk, vv in asdict(v).items() if kk in BOUNDS} for k, v in ps.items()})
