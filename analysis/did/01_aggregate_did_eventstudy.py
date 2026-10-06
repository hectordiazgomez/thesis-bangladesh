#!/usr/bin/env python3
"""
Aggregate international DiD event study and in-space placebo inference.

Input (stored, not modified):
  results/synthetic_control/country_day_donor_pool_with_holidays.parquet
  (country-day primary outcome, May 1 - Sep 4, 2024, Bangladesh + 14 donors)

Definitions (identical to the archived international DiD in
results/final/table_DiD_all_outcomes.csv):
  pre-period  : May 1 - Jul 17, 2024
  shutdown    : Jul 18 - Jul 23, 2024
  control     : equal-weighted mean of the 14 donor countries

Event study (weekly bins):
  k = -11..-1 : 7-day bins ending Jul 17 (k = -11 also contains May 1)
  k = 0       : shutdown, Jul 18-23 (6 days)
  k = +1..+6  : 7-day bins from Jul 24 (Sep 4 is a partial bin and is dropped)

  theta_k = [Y_BD,k - Y_BD,pre] - mean_j [Y_j,k - Y_j,pre]

theta_0 equals the archived DiD ATT; the script stops if it does not.

Inference: in-space placebos. Each donor j is treated as if it were
Bangladesh and compared with the equal-weighted mean of the other 13
donors. Reported per period: placebo standard deviation, the
placebo-based 95% interval theta_k +/- 1.96 * sd, and the rank of
|theta_BD,k| among the 15 units (rank / 15; minimum attainable 1/15).

Also reports each unit's standard deviation of its pre-shutdown weekly
estimates (did_pre_period_volatility.csv).

Usage (repository root):
  python analysis/did/01_aggregate_did_eventstudy.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "results" / "synthetic_control" / "country_day_donor_pool_with_holidays.parquet"
FINAL = REPO / "results" / "final" / "table_DiD_all_outcomes.csv"
OUT = REPO / "results" / "did"

PRE_START, PRE_END = pd.Timestamp("2024-05-01"), pd.Timestamp("2024-07-17")
SHUT_START, SHUT_END = pd.Timestamp("2024-07-18"), pd.Timestamp("2024-07-23")
RESTORE = pd.Timestamp("2024-07-24")
Z = 1.959963984540054


def periods(last: pd.Timestamp) -> pd.DataFrame:
    rows = []
    for k in range(-11, 0):
        end = PRE_END - pd.Timedelta(days=7 * (-k - 1))
        start = PRE_START if k == -11 else end - pd.Timedelta(days=6)
        rows.append((k, start, end))
    rows.append((0, SHUT_START, SHUT_END))
    k, start = 1, RESTORE
    while start + pd.Timedelta(days=6) <= last:
        rows.append((k, start, start + pd.Timedelta(days=6)))
        k, start = k + 1, start + pd.Timedelta(days=7)
    return pd.DataFrame(rows, columns=["event_week", "start", "end"])


def did_by_unit(w: pd.DataFrame, mask: pd.Series) -> pd.Series:
    """theta for every unit as treated, vs equal-weighted mean of the other donors."""
    pre = w[(w.index >= PRE_START) & (w.index <= PRE_END)].mean()
    cur = w[mask].mean()
    chg = cur - pre
    donors = [c for c in w.columns if c != "Bangladesh"]
    out = {"Bangladesh": chg["Bangladesh"] - chg[donors].mean()}
    for j in donors:
        others = [c for c in donors if c != j]
        out[j] = chg[j] - chg[others].mean()
    return pd.Series(out)


def summarize(theta: pd.Series) -> dict:
    bd = theta["Bangladesh"]
    plc = theta.drop("Bangladesh")
    sd = plc.std(ddof=1)
    return {
        "theta_pp": bd,
        "placebo_sd_pp": sd,
        "ci_low_pp": bd - Z * sd,
        "ci_high_pp": bd + Z * sd,
        "placebo_min_pp": plc.min(),
        "placebo_max_pp": plc.max(),
        "rank_p": (theta.abs() >= abs(bd)).sum() / len(theta),
    }


def main() -> None:
    d = pd.read_parquet(SRC)
    d["date"] = pd.to_datetime(d["date"])
    w = d.pivot(index="date", columns="country", values="active_rate_pp")
    hol = d.pivot(index="date", columns="country", values="is_holiday").astype(bool)
    archived = pd.read_csv(FINAL)
    archived = archived[archived.outcome == "active_rate_pp"].set_index("remove_holidays")

    # Main DiD (all days and holidays removed) with placebo inference.
    shut = (w.index >= SHUT_START) & (w.index <= SHUT_END)
    rows = []
    for flag, panel in [(False, w), (True, w.mask(hol))]:
        theta = did_by_unit(panel, shut)
        if not np.isclose(theta["Bangladesh"], archived.loc[flag, "ATT"], atol=1e-9):
            raise SystemExit(f"DiD does not reproduce archived ATT (holidays removed={flag})")
        rows.append({"remove_holidays": flag, **summarize(theta)})
    main_tab = pd.DataFrame(rows)

    # Weekly event study, all days.
    per = periods(w.index.max())
    es, by_unit = [], {}
    for r in per.itertuples(index=False):
        mask = (w.index >= r.start) & (w.index <= r.end)
        theta = did_by_unit(w, mask)
        by_unit[r.event_week] = theta
        es.append({"event_week": r.event_week, "start": r.start.date(), "end": r.end.date(),
                   "days": int(mask.sum()), **summarize(theta)})
    es = pd.DataFrame(es)
    if not np.isclose(es.loc[es.event_week == 0, "theta_pp"].iloc[0],
                      archived.loc[False, "ATT"], atol=1e-9):
        raise SystemExit("Event-week 0 does not reproduce archived DiD ATT")

    # Pre-period volatility of each unit's weekly estimates (as-if-treated).
    th = pd.DataFrame(by_unit).T
    vol = (th[th.index < 0].std(ddof=1).rename("pre_weekly_sd_pp")
           .rename_axis("country").reset_index().sort_values("pre_weekly_sd_pp"))

    OUT.mkdir(parents=True, exist_ok=True)
    vol.to_csv(OUT / "did_pre_period_volatility.csv", index=False)
    main_tab.to_csv(OUT / "did_main_placebo_inference.csv", index=False)
    es.to_csv(OUT / "did_eventstudy_weekly.csv", index=False)
    pd.set_option("display.width", 200)
    print(main_tab.round(4).to_string(index=False))
    print(es.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
