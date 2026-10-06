#!/usr/bin/env python3
"""
Reproduce the archived preferred RDiT estimates (results/rdit/main_rdit_summary.csv).

No new specification is estimated: the script recovers the archived design
and stops unless every archived row is reproduced to six decimals.

Recovered design (archived README: cutoff 2024-07-17, bandwidth 7, degree 1,
no donut, N = 15, HAC lags 2):
  series   : daily share of users with productive_events > 0 in
             data/processed/panel_user_day_bangladesh.parquet
             (and panel_user_day_philippines.parquet)
  window   : July 10 - July 24, 2024 (t = date - July 17, |t| <= 7)
  treatment: D = 1{t >= 0}, i.e. July 17 is on the post-cutoff side
  model    : y_t = a + tau*D + g1*t + g2*D*t
  inference: Newey-West HAC, 2 lags (Bartlett), small-sample factor n/(n-k)

Output: results/rdit/rdit_daily_series.csv (daily series plotted in the RDiT
figure, July 3-31, 2024, in percent).

Usage (repository root):
  python analysis/rdit/01_reproduce_rdit.py
"""

from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
PROC = REPO / "data" / "processed"
RDIT = REPO / "results" / "rdit"
CUT = pd.Timestamp("2024-07-17")
BW, LAGS = 7, 2


def daily_rate(name: str) -> pd.Series:
    u = pd.read_parquet(PROC / name, columns=["date", "productive_events"])
    u["date"] = pd.to_datetime(u["date"])
    return (u["productive_events"] > 0).groupby(u["date"]).mean()


def rd(y: pd.Series) -> dict:
    idx = pd.date_range(CUT - pd.Timedelta(days=BW), CUT + pd.Timedelta(days=BW))
    t = (idx - CUT).days.to_numpy(float)
    d = (t >= 0).astype(float)
    X = np.column_stack([np.ones_like(t), d, t, d * t])
    yy = y.loc[idx].to_numpy(float)
    b = np.linalg.lstsq(X, yy, rcond=None)[0]
    e = yy - X @ b
    n, k = X.shape
    S = (X * e[:, None]).T @ (X * e[:, None])
    for lag in range(1, LAGS + 1):
        G = (X[lag:] * e[lag:, None]).T @ (X[:-lag] * e[:-lag, None])
        S += (1 - lag / (LAGS + 1)) * (G + G.T)
    B = np.linalg.inv(X.T @ X)
    se = np.sqrt((B @ S @ B)[1, 1] * n / (n - k))
    z = 1.959963984540054
    return {"effect": b[1], "se_hac": se, "ci_low": b[1] - z * se, "ci_high": b[1] + z * se,
            "p_hac": 2 * (1 - 0.5 * (1 + erf(abs(b[1] / se) / sqrt(2)))),
            "durbin_watson": np.sum(np.diff(e) ** 2) / np.sum(e ** 2), "N_time": n}


def main() -> None:
    bd = daily_rate("panel_user_day_bangladesh.parquet")
    ph = daily_rate("panel_user_day_philippines.parquet")
    arch = pd.read_csv(RDIT / "main_rdit_summary.csv").set_index("specification")
    for spec, y in [("Main local linear", bd), ("Controlled local linear", bd - ph),
                    ("Geographic placebo", ph)]:
        got, ref = rd(y), arch.loc[spec]
        for col in ["effect", "se_hac", "ci_low", "ci_high", "p_hac", "durbin_watson", "N_time"]:
            if not np.isclose(got[col], ref[col], atol=5e-7):
                raise SystemExit(f"{spec} {col}: {got[col]} != archived {ref[col]}")
        print(f"reproduced {spec}: effect {got['effect']:.6f}, HAC SE {got['se_hac']:.6f}")

    window = pd.date_range("2024-07-03", "2024-07-31")
    out = pd.DataFrame({"date": window.date,
                        "bangladesh_pct": 100 * bd.loc[window].to_numpy(),
                        "philippines_pct": 100 * ph.loc[window].to_numpy()})
    out.to_csv(RDIT / "rdit_daily_series.csv", index=False)
    print("wrote", (RDIT / "rdit_daily_series.csv").relative_to(REPO))


if __name__ == "__main__":
    main()
