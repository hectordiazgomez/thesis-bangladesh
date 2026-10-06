#!/usr/bin/env python3
"""
Verify and decompose the archived synthetic difference-in-differences (SDID)
estimate. No SDID weights are re-estimated.

Inputs (stored, not modified):
  results/synthetic_control/main_synthetic_results.csv  (archived SDID ATT)
  results/synthetic_control/sdid_time_weights.csv       (lambda_t, May 1-Jul 17)
  results/synthetic_control/donor_weights.csv           (SDID and SC unit weights)
  results/synthetic_control/sdid_estimation_panel.parquet

SDID point estimate from the archived weights:
  tau = [mean_post Y_BD - sum_t lambda_t Y_BD,t]
        - sum_j omega_j [mean_post Y_j - sum_t lambda_t Y_j,t]

The script stops unless this reproduces the archived ATT, then reports the
estimate under alternative combinations of unit weights (SDID, SC, equal)
and time weights (SDID, uniform) to show which component drives the
difference from canonical SC.

Output: results/synthetic_control/reproduced/sdid_decomposition.csv,
        results/synthetic_control/reproduced/sdid_time_weights_summary.csv

Usage (repository root):
  python analysis/synthetic_control/02_sdid_archived_check.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SC = REPO / "results" / "synthetic_control"
OUT = SC / "reproduced"


def main() -> None:
    panel = pd.read_parquet(SC / "sdid_estimation_panel.parquet")
    panel["date"] = pd.to_datetime(panel["date"])
    Y = panel.pivot(index="date", columns="country", values="active_rate_pp")
    lam = pd.read_csv(SC / "sdid_time_weights.csv", parse_dates=["date"]).set_index("date")["lambda"]
    w = pd.read_csv(SC / "donor_weights.csv").set_index("country")
    archived = pd.read_csv(SC / "main_synthetic_results.csv").set_index("method").loc["Synthetic DiD", "ATT_pp"]

    post = Y.loc["2024-07-18":"2024-07-23"]
    pre = Y.loc[lam.index]
    donors = list(w.index)

    def tau(omega: pd.Series, lam_t: pd.Series) -> float:
        bd = post["Bangladesh"].mean() - (lam_t * pre["Bangladesh"]).sum()
        dn = sum(omega[c] * (post[c].mean() - (lam_t * pre[c]).sum()) for c in donors)
        return float(bd - dn)

    uniform = pd.Series(1.0 / len(lam), index=lam.index)
    equal = pd.Series(1.0 / len(donors), index=donors)
    est = tau(w["SDID_weight"], lam)
    print(f"SDID from archived weights: {est:.6f} | archived {archived:.6f}")
    if not np.isclose(est, archived, atol=1e-4):
        sys.exit("FAILED: archived SDID weights do not reproduce the archived ATT")

    rows = []
    for ulab, om in [("SDID", w["SDID_weight"]), ("SC", w["SC_weight"]), ("Equal", equal)]:
        for tlab, lt in [("SDID", lam), ("Uniform", uniform)]:
            rows.append({"unit_weights": ulab, "time_weights": tlab, "ATT_pp": tau(om, lt)})
    dec = pd.DataFrame(rows)

    summary = pd.DataFrame([{
        "lambda_mass_jul01_17": lam.loc["2024-07-01":].sum(),
        "lambda_jul02": lam.loc["2024-07-02"],
        "lambda_jul10": lam.loc["2024-07-10"],
        "n_days_positive_lambda": int((lam > 0).sum()),
        "bd_lambda_weighted_pre_pp": (lam * pre["Bangladesh"]).sum(),
        "bd_uniform_pre_mean_pp": pre["Bangladesh"].mean(),
        "bd_shutdown_mean_pp": post["Bangladesh"].mean(),
    }])
    OUT.mkdir(parents=True, exist_ok=True)
    dec.to_csv(OUT / "sdid_decomposition.csv", index=False)
    summary.to_csv(OUT / "sdid_time_weights_summary.csv", index=False)
    print(dec.round(3).to_string(index=False))
    print(summary.round(4).T.to_string(header=False))


if __name__ == "__main__":
    main()
