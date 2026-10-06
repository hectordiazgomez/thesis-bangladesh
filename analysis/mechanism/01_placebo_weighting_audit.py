#!/usr/bin/env python3
"""
Audit of the weighting in the mechanism placebo-window comparison.

Finding: commit metadata were requested for a SAMPLE of first-push repo-SHA
pairs whose push date is July 1-17, 2024 (7-17% per day) and for ALL pairs
pushed on or after July 18. The archived placebo rows
(results/final/table_mechanism_placebos.csv) use inverse-probability weights

    w = (# clean first-push pairs on push date d) / (# pairs requested on d)

so that each window estimates the population share of strict-sample commits
authored in the window whose author-to-push delay exceeds h. Commits
authored July 18-23 can only be pushed on or after July 18, where w = 1, so
the blackout row uses the same estimator with all weights equal to one.

Without the weights, placebo windows over-represent long delays: a commit
authored July 1-6 and pushed after July 18 is kept with certainty, whereas
one pushed the same week is kept with probability of about 0.12.

The script reproduces every archived row exactly (stops otherwise), reports
weighted and unweighted rates side by side, and checks that requested pairs
resemble the universe on observables within the sampled days.

Inputs (stored, not modified):
  results/mechanism/clean_repo_sha_first_push.parquet   (sampling universe)
  results/mechanism/commit_sha_author_push_master.parquet (requested pairs)
Output: results/mechanism/placebo_weighting_audit.csv

Usage (repository root):
  python analysis/mechanism/01_placebo_weighting_audit.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MECH = REPO / "results" / "mechanism"
FINAL = REPO / "results" / "final"
HOURS = [24, 48, 72, 120]


def main() -> None:
    uni = pd.read_parquet(MECH / "clean_repo_sha_first_push.parquet")
    m = pd.read_parquet(MECH / "commit_sha_author_push_master.parquet")
    uni["push_time"] = pd.to_datetime(uni["push_time"], utc=True)
    for col in ["push_time", "authored_time"]:
        m[col] = pd.to_datetime(m[col], utc=True)
    uni["pdate"] = uni.push_time.dt.date.astype(str)
    m["pdate"] = m.push_time.dt.date.astype(str)

    rate = (m.groupby("pdate").size() / uni.groupby("pdate").size()).rename("request_rate")
    m = m.join(rate, on="pdate")
    m["w"] = 1.0 / m["request_rate"]

    s = m[m.found & m.authored_time.notna()
          & m.author_equals_pusher.fillna(False).astype(bool)
          & (m.author_to_push_hours >= 0)].copy()
    s["adate"] = s.authored_time.dt.date.astype(str)

    arch = pd.read_csv(FINAL / "table_mechanism_placebos.csv")
    windows = list(arch[["window", "start", "end"]].itertuples(index=False, name=None))
    if "REAL_BLACKOUT" not in {w[0] for w in windows}:
        windows.append(("REAL_BLACKOUT", "2024-07-18", "2024-07-23"))
    arch = arch.set_index("window")

    rows, fail = [], []
    for name, a, b in windows:
        g = s[(s.adate >= a) & (s.adate <= b)]
        r = {"window": name, "start": a, "end": b, "N_observed": len(g),
             "weighted_N": g.w.sum(),
             "pushed_on_or_after_jul18_pct": 100 * (g.pdate >= "2024-07-18").mean()}
        for h in HOURS:
            r[f"ipw_delay_gt{h}h_pct"] = 100 * (g.w * (g.author_to_push_hours > h)).sum() / g.w.sum()
            r[f"unweighted_delay_gt{h}h_pct"] = 100 * (g.author_to_push_hours > h).mean()
        rows.append(r)
        if name in arch.index:
            for got, ref in [(r["N_observed"], arch.loc[name, "N_observed"]),
                             (r["weighted_N"], arch.loc[name, "weighted_N"])] + \
                            [(r[f"ipw_delay_gt{h}h_pct"], arch.loc[name, f"delay_gt{h}h_pct"]) for h in HOURS]:
                if not np.isclose(got, ref, atol=1e-6):
                    fail.append((name, got, ref))
    out = pd.DataFrame(rows)
    plc = out[out.window.str.startswith("PLACEBO")]
    mean_row = {"window": "PLACEBO_MEAN"} | plc.drop(columns=["window", "start", "end"]).mean().to_dict()
    out = pd.concat([out, pd.DataFrame([mean_row])], ignore_index=True)

    # Blackout weights must all equal one (same estimator, trivial weights).
    bw = s[(s.adate >= "2024-07-18") & (s.adate <= "2024-07-23")].w
    if not np.allclose(bw, 1.0):
        fail.append(("blackout weights != 1", bw.min(), bw.max()))

    # Within-day sampling: requested pairs vs universe on sampled days.
    pre_u, pre_m = uni[uni.pdate <= "2024-07-17"], m[m.pdate <= "2024-07-17"]
    print("Sampled days (Jul 1-17): universe vs requested")
    print(f"  mean push size     {pre_u.push_size.mean():.3f} vs {pre_m.push_size.mean():.3f}")
    print(f"  distinct-commit %  {100*pre_u.distinct_commit.mean():.2f} vs {100*pre_m.distinct_commit.mean():.2f}")
    print(f"  mean push hour     {pre_u.push_time.dt.hour.mean():.2f} vs {pre_m.push_time.dt.hour.mean():.2f}")
    print(f"  daily request rate {rate[rate.index <= '2024-07-17'].min():.3f}-{rate[rate.index <= '2024-07-17'].max():.3f}; "
          f"from Jul 18: {rate[rate.index >= '2024-07-18'].min():.3f}")

    out.to_csv(MECH / "placebo_weighting_audit.csv", index=False)
    pd.set_option("display.width", 220)
    print(out[["window", "N_observed", "weighted_N", "pushed_on_or_after_jul18_pct"]
              + [f"{k}_delay_gt{h}h_pct" for h in [24, 48, 72] for k in ["ipw", "unweighted"]]]
          .round(2).to_string(index=False))
    if fail:
        sys.exit(f"FAILED to reproduce archived rows: {fail}")
    print("All archived placebo rows reproduced with inverse-request-rate weights.")


if __name__ == "__main__":
    main()
