#!/usr/bin/env python3
"""
In-time (backdated) placebo shutdowns for the canonical synthetic control.

Rule, fixed before results were inspected:
  - pseudo-treatment windows of six consecutive days (same length as the
    real July 18-23 window);
  - non-overlapping, moving backward from immediately before the real
    treatment: the first window is July 12-17, the next July 6-11, etc.;
  - a window is eligible only if at least 28 days (four weeks) of data lie
    between May 1 and the day before the window starts;
  - for each window, SC donor weights are re-estimated using only the days
    from May 1 to the day before the pseudo-treatment window;
  - ATT, pre-RMSPE, post-RMSPE and the RMSPE ratio use exactly the definitions
    of the real treatment (analysis/synthetic_control/01_reproduce_sc.py);
  - every eligible window is reported, including holidays and unusual dates.

The real-treatment row is computed with the same function and must equal
the archived ATT (-13.2559 pp); the script stops otherwise.

Output: results/synthetic_control/reproduced/sc_intime_placebos.csv

Usage (repository root):
  python analysis/synthetic_control/03_intime_placebos.py
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sc", HERE / "01_reproduce_sc.py")
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

WINDOW = 6
MIN_FIT_DAYS = 28


def windows() -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    out, end = [], sc.SHUT_START - pd.Timedelta(days=1)
    while True:
        start = end - pd.Timedelta(days=WINDOW - 1)
        if (start - sc.PRE_START).days < MIN_FIT_DAYS:
            break
        out.append((start, end))
        end = start - pd.Timedelta(days=1)
    return out


def main() -> None:
    w = sc.load_panel()
    hol = pd.read_parquet(sc.SC_DIR / "country_day_donor_pool_with_holidays.parquet")
    hol["date"] = pd.to_datetime(hol["date"])
    bd_hol = hol[(hol.country == sc.TREATED) & (hol.is_holiday == 1)].set_index("date")["holiday_name"]
    donors = [c for c in w.columns if c != sc.TREATED]

    rows = []
    real = sc.sc_stats(w, sc.TREATED, donors, sc.PRE_START, sc.PRE_END, sc.SHUT_START, sc.SHUT_END)
    archived = pd.read_csv(sc.SC_DIR / "sc_inspace_placebos.csv").set_index("country").loc[sc.TREATED, "ATT"]
    if not np.isclose(real["ATT"], archived, atol=1e-4):
        sys.exit(f"Real-treatment ATT {real['ATT']} does not reproduce archived {archived}")
    for kind, (start, end) in [("real", (sc.SHUT_START, sc.SHUT_END))] + [("pseudo", x) for x in windows()]:
        fit_end = start - pd.Timedelta(days=1)
        s = real if kind == "real" else sc.sc_stats(w, sc.TREATED, donors, sc.PRE_START, fit_end, start, end)
        h = bd_hol[(bd_hol.index >= start) & (bd_hol.index <= end)]
        top = s["weights"].sort_values(ascending=False)
        rows.append({
            "type": kind, "start": start.date(), "end": end.date(),
            "fit_days": (fit_end - sc.PRE_START).days + 1,
            "ATT": s["ATT"], "relative_effect_pct": s["relative_effect_pct"],
            "pre_RMSPE": s["pre_RMSPE"], "post_RMSPE": s["post_RMSPE"], "RMSPE_ratio": s["RMSPE_ratio"],
            "bd_holidays_in_window": "; ".join(f"{d:%b %-d} {n}" for d, n in h.items()),
            "top_donors": "; ".join(f"{c} {v:.2f}" for c, v in top[top > 0.005].items()),
        })
    out = pd.DataFrame(rows)
    n = len(out)
    out["rank_abs_ATT"] = out.ATT.abs().rank(ascending=False, method="min").astype(int)
    out["rank_RMSPE_ratio"] = out.RMSPE_ratio.rank(ascending=False, method="min").astype(int)
    r = out[out.type == "real"].iloc[0]
    print(f"Real ATT rank by |ATT|: {r.rank_abs_ATT}/{n}; by RMSPE ratio: {r.rank_RMSPE_ratio}/{n}")
    out.to_csv(sc.OUT / "sc_intime_placebos.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.drop(columns=["top_donors"]).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
