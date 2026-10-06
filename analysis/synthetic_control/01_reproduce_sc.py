#!/usr/bin/env python3
"""
Reproduce the archived canonical synthetic control (primary outcome).

Input (stored, not modified):
  results/synthetic_control/country_day_donor_pool.parquet
    country-day active_rate_pp, Bangladesh + 14 donors, May 1 - Sep 4, 2024

Design (as archived):
  pre-period   : May 1 - Jul 17, 2024 (78 days)
  treatment    : Jul 18 - Jul 23, 2024 (6 days)
  weights      : w >= 0, sum(w) = 1, minimizing mean squared pre-period gap
                 on the daily outcome (no covariates, no V-matrix)
  ATT          : mean daily gap over the treatment window (pp)
  relative     : 100 * ATT / mean synthetic outcome over the treatment window
  pre_RMSPE    : sqrt(mean squared gap), pre-period
  post_RMSPE   : sqrt(mean squared gap), treatment window
  in-space     : each donor treated in turn; donor pool = the other 13 donors
                 (Bangladesh excluded); rank p = share of the 15 units with
                 |ATT| (or RMSPE ratio) >= Bangladesh's
  leave-one-out: Bangladesh SC re-estimated without each donor

The script stops (non-zero exit) if any archived headline number is not
reproduced. Archived references:
  results/final/table_primary_SC_weights.csv
  results/final/table_primary_SC_leave_one_out.csv
  results/synthetic_control/sc_inspace_placebos.csv
  results/synthetic_control/actual_vs_synthetic_daily.csv
  results/final/FINAL_COPY_READY_RESULTS.txt (2.021 / 15.277 / 3.260 / 4.192)

Outputs (new files only): results/synthetic_control/reproduced/
  sc_weights.csv, sc_summary.csv, sc_inspace_placebos.csv,
  sc_leave_one_out.csv, sc_daily_path_full.csv (May 1 - Sep 4, descriptive),
  sc_weekly_gaps.csv (weekly mean gaps, descriptive)

The module also exposes fit_sc() and sc_stats() for the in-time placebos.

Usage (repository root):
  python analysis/synthetic_control/01_reproduce_sc.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

REPO = Path(__file__).resolve().parents[2]
SC_DIR = REPO / "results" / "synthetic_control"
FINAL = REPO / "results" / "final"
OUT = SC_DIR / "reproduced"

PRE_START, PRE_END = pd.Timestamp("2024-05-01"), pd.Timestamp("2024-07-17")
SHUT_START, SHUT_END = pd.Timestamp("2024-07-18"), pd.Timestamp("2024-07-23")
TREATED = "Bangladesh"


def load_panel() -> pd.DataFrame:
    d = pd.read_parquet(SC_DIR / "country_day_donor_pool.parquet")
    d["date"] = pd.to_datetime(d["date"])
    return d.pivot(index="date", columns="country", values="active_rate_pp").sort_index()


def fit_sc(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Simplex-constrained least squares: min sum (y - Xw)^2, w >= 0, sum w = 1.

    Solved exactly with non-negative least squares on an augmented system whose
    extra row (scaled by a large constant) enforces sum(w) = 1.
    """
    big = 1e6 * max(1.0, float(np.abs(X).max()))
    Xa = np.vstack([X, big * np.ones((1, X.shape[1]))])
    ya = np.append(y, big)
    w, _ = nnls(Xa, ya, maxiter=100 * X.shape[1])
    if abs(w.sum() - 1.0) > 1e-8:
        raise RuntimeError(f"SC weights do not sum to one: {w.sum()}")
    return w / w.sum()


def sc_stats(w: pd.DataFrame, treated: str, donors: list[str],
             fit_start, fit_end, post_start, post_end) -> dict:
    fit = w.loc[fit_start:fit_end]
    post = w.loc[post_start:post_end]
    wt = fit_sc(fit[treated].to_numpy(), fit[donors].to_numpy())
    gap_pre = fit[treated] - fit[donors] @ wt
    synth_post = post[donors] @ wt
    gap_post = post[treated] - synth_post
    pre_rmspe = float(np.sqrt(np.mean(gap_pre ** 2)))
    post_rmspe = float(np.sqrt(np.mean(gap_post ** 2)))
    return {
        "weights": pd.Series(wt, index=donors),
        "actual": float(post[treated].mean()),
        "counterfactual": float(synth_post.mean()),
        "ATT": float(gap_post.mean()),
        "relative_effect_pct": float(100 * gap_post.mean() / synth_post.mean()),
        "pre_RMSPE": pre_rmspe,
        "post_RMSPE": post_rmspe,
        "RMSPE_ratio": post_rmspe / pre_rmspe,
    }


FAILURES: list[str] = []


def check(label: str, got: float, expected: float, tol: float) -> None:
    ok = np.isclose(got, expected, atol=tol)
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: reproduced {got:.6f} | archived {expected:.6f}")
    if not ok:
        FAILURES.append(label)


def main() -> None:
    w = load_panel()
    donors = [c for c in w.columns if c != TREATED]
    if len(donors) != 14:
        sys.exit(f"Expected 14 donors, found {len(donors)}")
    window = (PRE_START, PRE_END, SHUT_START, SHUT_END)

    # --- Primary SC -------------------------------------------------------
    main_sc = sc_stats(w, TREATED, donors, *window)
    print("Primary synthetic control")
    arch_w = pd.read_csv(FINAL / "table_primary_SC_weights.csv").set_index("country")["weight"]
    for c in donors:
        check(f"weight {c}", main_sc["weights"][c], arch_w.get(c, 0.0), 1e-4)
    plc_arch = pd.read_csv(SC_DIR / "sc_inspace_placebos.csv").set_index("country")
    loo_arch = pd.read_csv(FINAL / "table_primary_SC_leave_one_out.csv").set_index("removed")
    bd = plc_arch.loc[TREATED]
    check("actual (%)", main_sc["actual"], 2.021, 5e-4)
    check("counterfactual (%)", main_sc["counterfactual"], 15.277, 5e-4)
    check("ATT (pp)", main_sc["ATT"], bd.ATT, 1e-4)
    check("relative effect (%)", main_sc["relative_effect_pct"],
          loo_arch.loc["Indonesia", "relative_effect_pct"], 1e-3)  # zero-weight donor row = baseline
    check("pre-RMSPE", main_sc["pre_RMSPE"], bd.pre_RMSPE, 1e-4)
    check("post-RMSPE", main_sc["post_RMSPE"], bd.post_RMSPE, 1e-4)
    check("RMSPE ratio", main_sc["RMSPE_ratio"], bd.RMSPE_ratio, 1e-4)

    daily_arch = pd.read_csv(SC_DIR / "actual_vs_synthetic_daily.csv", parse_dates=["date"]).set_index("date")
    synth_full = w[donors] @ main_sc["weights"]
    max_dev = float((synth_full.loc[daily_arch.index] - daily_arch["Synthetic_Control"]).abs().max())
    check("max |daily synthetic - archived| (May 1-Jul 23)", max_dev, 0.0, 1e-3)

    # --- In-space placebos ----------------------------------------------
    print("In-space placebos (donor pool = other 13 donors)")
    rows = [{"country": TREATED, **{k: v for k, v in main_sc.items() if k != "weights"}}]
    for c in donors:
        others = [d for d in donors if d != c]
        s = sc_stats(w, c, others, *window)
        rows.append({"country": c, **{k: v for k, v in s.items() if k != "weights"}})
        check(f"placebo ATT {c}", s["ATT"], plc_arch.loc[c, "ATT"], 1e-3)
        check(f"placebo RMSPE ratio {c}", s["RMSPE_ratio"], plc_arch.loc[c, "RMSPE_ratio"], 1e-3)
    plc = pd.DataFrame(rows)
    n = len(plc)
    p_att = float((plc.ATT.abs() >= abs(main_sc["ATT"])).sum() / n)
    p_ratio = float((plc.RMSPE_ratio >= main_sc["RMSPE_ratio"]).sum() / n)
    check("rank p, |ATT|", p_att, 1 / 15, 1e-12)
    check("rank p, RMSPE ratio", p_ratio, 1 / 15, 1e-12)

    # --- Leave-one-out ----------------------------------------------------
    print("Leave-one-out")
    loo_rows = []
    for c in donors:
        s = sc_stats(w, TREATED, [d for d in donors if d != c], *window)
        loo_rows.append({"removed": c, **{k: v for k, v in s.items() if k != "weights"}})
        check(f"LOO ATT without {c}", s["ATT"], loo_arch.loc[c, "ATT"], 1e-3)
    loo = pd.DataFrame(loo_rows)

    # --- Outputs ------------------------------------------------------------
    OUT.mkdir(parents=True, exist_ok=True)
    main_sc["weights"].rename("weight").rename_axis("country").reset_index().to_csv(
        OUT / "sc_weights.csv", index=False)
    pd.DataFrame([{k: v for k, v in main_sc.items() if k != "weights"}
                  | {"rank_p_ATT": p_att, "rank_p_RMSPE_ratio": p_ratio}]).to_csv(
        OUT / "sc_summary.csv", index=False)
    plc.to_csv(OUT / "sc_inspace_placebos.csv", index=False)
    loo.to_csv(OUT / "sc_leave_one_out.csv", index=False)
    pd.DataFrame({"date": w.index.date, "Bangladesh": w[TREATED].to_numpy(),
                  "Synthetic_Control": synth_full.to_numpy(),
                  "gap": (w[TREATED] - synth_full).to_numpy()}).to_csv(
        OUT / "sc_daily_path_full.csv", index=False)

    # Weekly mean gaps with the archived weights (descriptive; same bins as the
    # aggregate event study: 7-day bins ending Jul 17, shutdown Jul 18-23,
    # 7-day bins from Jul 24; Sep 4 is a partial bin and is dropped).
    gap = w[TREATED] - synth_full
    bins = [(k, (PRE_END - pd.Timedelta(days=7 * (-k - 1) + 6)) if k > -11 else PRE_START,
             PRE_END - pd.Timedelta(days=7 * (-k - 1))) for k in range(-11, 0)]
    bins.append((0, SHUT_START, SHUT_END))
    start = SHUT_END + pd.Timedelta(days=1)
    for k in range(1, 7):
        bins.append((k, start, start + pd.Timedelta(days=6)))
        start += pd.Timedelta(days=7)
    pd.DataFrame([{"event_week": k, "start": a.date(), "end": b.date(),
                   "bangladesh": w.loc[a:b, TREATED].mean(), "synthetic": synth_full.loc[a:b].mean(),
                   "gap": gap.loc[a:b].mean()} for k, a, b in bins]).to_csv(
        OUT / "sc_weekly_gaps.csv", index=False)

    if FAILURES:
        sys.exit(f"\nFAILED: {len(FAILURES)} archived values not reproduced: {FAILURES}")
    print(f"\nAll archived SC values reproduced. Outputs in {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
