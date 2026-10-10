#!/usr/bin/env python3
"""
Rebuild the secondary outcomes on eligible users only (referee comment R1).

Problem corrected
  results/synthetic_control/country_day_outcomes_enriched.parquet sums the
  activity of all 150,017 users in the user-day file but divides by the number
  of eligible users (59,158). The primary outcome
  (country_day_donor_pool.parquet) uses eligible users in both. This script
  rebuilds the secondary panel with eligible users in numerator and
  denominator and re-runs the archived estimators on it.

Inputs (read only)
  data/processed/github_activity_international_enriched.parquet   user-day activity
  results/synthetic_control/eligible_users_donors.parquet          eligible users
  results/synthetic_control/country_day_outcomes_enriched.parquet  archived panel
  results/synthetic_control/country_day_donor_pool_with_holidays.parquet
  results/final/table_primary_SC_weights.csv                       primary weights
  results/final/table_secondary_*.csv, table_DiD_all_outcomes.csv  archived results

Design (same as the archived specifications)
  SC: fit_sc() and sc_stats() from 01_reproduce_sc.py; fit May 1 - Jul 17,
      treatment Jul 18 - Jul 23, 2024.
  Fixed weights: primary active-rate weights applied to each outcome.
  Outcome-specific weights: re-estimated per outcome; in-space placebos with
      the other 13 donors; rank p = share of the 15 units at least as extreme.
  DiD: Bangladesh change minus the equal-weighted mean donor change; the
      holiday variant drops each country's own holidays.

The script first checks that (i) the archived panel equals the all-user
construction and (ii) the archived estimates are reproduced from it, and stops
otherwise.

Outputs (new files only; archived files are not modified)
  results/synthetic_control/country_day_outcomes_eligible.parquet
  results/final/table_secondary_fixed_SC_eligible.csv
  results/final/table_secondary_specific_SC_eligible.csv
  results/final/table_secondary_SC_weights_eligible.csv
  results/final/table_secondary_placebos_all_eligible.csv
  results/final/table_secondary_placebo_summary_eligible.csv
  results/final/table_DiD_all_outcomes_eligible.csv
  results/final/table_secondary_archived_vs_eligible.csv

Usage (repository root):
  python analysis/synthetic_control/04_secondary_outcomes_eligible.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data" / "processed"
SC_DIR = REPO / "results" / "synthetic_control"
FINAL = REPO / "results" / "final"

_spec = importlib.util.spec_from_file_location("sc01", Path(__file__).with_name("01_reproduce_sc.py"))
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)
TREATED = sc.TREATED
WINDOW = (sc.PRE_START, sc.PRE_END, sc.SHUT_START, sc.SHUT_END)

# outcome -> (user-day column, scale): rates in % of users, counts per 1,000 users
OUTCOMES = {
    "productive_active_rate_pp": ("productive_output_active", 100),
    "shipping_active_rate_pp": ("shipping_active", 100),
    "collaboration_active_rate_pp": ("collaboration_active", 100),
    "collaboration_events_per_1000": ("collaboration_events", 1000),
    "shipping_output_per_1000": ("shipping_output", 1000),
}

FAILURES: list[str] = []


def check(label: str, got: float, expected: float, tol: float) -> None:
    ok = bool(np.isclose(got, expected, atol=tol))
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: {got:.6f} | expected {expected:.6f}")
    if not ok:
        FAILURES.append(label)


def build_panel(ud: pd.DataFrame, users: pd.DataFrame | None, n_users: pd.Series,
                dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Country-day outcomes: numerator summed over `users` (all if None), denominator n_users."""
    cols = list(dict.fromkeys(c for c, _ in OUTCOMES.values()))
    sub = ud if users is None else ud.merge(users, on=["country", "login"], how="inner")
    idx = pd.MultiIndex.from_product([n_users.index, dates], names=["country", "date"])
    p = sub.groupby(["country", "date"])[cols].sum().reindex(idx, fill_value=0).reset_index()
    p["n_users"] = p.country.map(n_users)
    for o, (c, scale) in OUTCOMES.items():
        p[o] = scale * p[c] / p.n_users
    return p


def wide(panel: pd.DataFrame, col: str) -> pd.DataFrame:
    return panel.pivot(index="date", columns="country", values=col).sort_index()


def fixed_stats(w: pd.DataFrame, weights: pd.Series) -> dict:
    fit = w.loc[sc.PRE_START:sc.PRE_END]
    post = w.loc[sc.SHUT_START:sc.SHUT_END]
    d = list(weights.index)
    gap_pre = fit[TREATED] - fit[d] @ weights
    synth_post = post[d] @ weights
    gap_post = post[TREATED] - synth_post
    pre = float(np.sqrt(np.mean(gap_pre ** 2)))
    return {"actual": float(post[TREATED].mean()), "counterfactual": float(synth_post.mean()),
            "ATT": float(gap_post.mean()),
            "relative_effect_pct": float(100 * gap_post.mean() / synth_post.mean()),
            "pre_RMSPE": pre, "RMSPE_ratio": float(np.sqrt(np.mean(gap_post ** 2))) / pre}


def did(w: pd.DataFrame, hol: pd.DataFrame | None) -> dict:
    if hol is not None:
        w = w.mask(hol.reindex(index=w.index, columns=w.columns).astype(bool))
    pre = w.loc[sc.PRE_START:sc.PRE_END].mean()
    post = w.loc[sc.SHUT_START:sc.SHUT_END].mean()
    change = post - pre
    cc = float(change.drop(TREATED).mean())
    att = float(change[TREATED] - cc)
    cf = float(pre[TREATED] + cc)
    return {"BD_pre": float(pre[TREATED]), "BD_blackout": float(post[TREATED]), "control_change": cc,
            "ATT": att, "counterfactual": cf, "relative_effect_pct": 100 * att / cf}


def estimate(panel: pd.DataFrame, primary_w: pd.Series, hol: pd.DataFrame) -> dict:
    fx, sp, wts, plc, summ, dd = [], [], [], [], [], []
    for o in OUTCOMES:
        w = wide(panel, o)
        donors = [c for c in w.columns if c != TREATED]
        fx.append({"outcome": o, **fixed_stats(w, primary_w.reindex(donors).fillna(0.0))})
        s = sc.sc_stats(w, TREATED, donors, *WINDOW)
        sp.append({"treated": TREATED, "outcome": o, **{k: v for k, v in s.items() if k != "weights"}})
        ws = s["weights"][s["weights"] > 1e-10].sort_values(ascending=False)
        wts += [{"outcome": o, "country": c, "weight": v, "weight_pct": 100 * v} for c, v in ws.items()]
        rows = []
        for c in donors:
            p = sc.sc_stats(w, c, [x for x in donors if x != c], *WINDOW)
            rows.append({"outcome": o, "country": c, "ATT": p["ATT"], "pre_RMSPE": p["pre_RMSPE"],
                         "RMSPE_ratio": p["RMSPE_ratio"]})
        plc += rows
        att = np.r_[s["ATT"], [r["ATT"] for r in rows]]
        ratio = np.r_[s["RMSPE_ratio"], [r["RMSPE_ratio"] for r in rows]]
        summ.append({"outcome": o, "actual_ATT": s["ATT"], "actual_pre_RMSPE": s["pre_RMSPE"],
                     "actual_RMSPE_ratio": s["RMSPE_ratio"],
                     "ATT_rank_p": float(np.mean(np.abs(att) >= abs(s["ATT"]))),
                     "RMSPE_rank_p": float(np.mean(ratio >= s["RMSPE_ratio"])),
                     "N_placebos": len(rows)})
        for rh in (False, True):
            dd.append({"outcome": o, "remove_holidays": rh, **did(w, hol if rh else None)})
    return {k: pd.DataFrame(v) for k, v in
            zip(["fixed", "specific", "weights", "placebos", "summary", "did"], [fx, sp, wts, plc, summ, dd])}


def main() -> None:
    cols = list(dict.fromkeys(c for c, _ in OUTCOMES.values()))
    ud = pd.read_parquet(DATA / "github_activity_international_enriched.parquet",
                         columns=["country", "login", "date", "productive_events"] + cols)
    ud["date"] = pd.to_datetime(ud["date"])
    elig = pd.read_parquet(SC_DIR / "eligible_users_donors.parquet", columns=["country", "login"])
    arch = pd.read_parquet(SC_DIR / "country_day_outcomes_enriched.parquet")
    arch["date"] = pd.to_datetime(arch["date"])
    n_users = arch.groupby("country").n_users.first()
    dates = pd.DatetimeIndex(sorted(arch.date.unique()))
    hol = arch.pivot(index="date", columns="country", values="is_holiday").sort_index()
    primary_w = pd.read_csv(FINAL / "table_primary_SC_weights.csv").set_index("country")["weight"]

    print(f"User-day file: {ud.login.nunique():,} users; eligible users: {len(elig):,}")
    check("eligible users = archived denominators", float(n_users.sum()), float(len(elig)), 0)
    check("eligible users by country = denominators",
          float((elig.country.value_counts().reindex(n_users.index) - n_users).abs().max()), 0.0, 0)

    # The eligible filter reproduces the primary outcome's sample exactly.
    pool = pd.read_parquet(SC_DIR / "country_day_donor_pool_with_holidays.parquet")
    pool["date"] = pd.to_datetime(pool["date"])
    act = (ud.merge(elig, on=["country", "login"]).assign(active=lambda d: d.productive_events > 0)
           .groupby(["country", "date"]).active.sum()
           .reindex(pd.MultiIndex.from_frame(pool[["country", "date"]]), fill_value=0))
    check("primary active_users = eligible users with productive_events > 0 (max abs diff)",
          float(np.abs(act.to_numpy() - pool.active_users.to_numpy()).max()), 0.0, 0)

    # (i) The archived panel is the all-user construction.
    print("Archived panel construction")
    allp = build_panel(ud, None, n_users, dates).set_index(["country", "date"])
    a = arch.set_index(["country", "date"]).loc[allp.index]
    for o in OUTCOMES:
        check(f"archived {o} = all-user numerator (max abs diff)", float((allp[o] - a[o]).abs().max()), 0.0, 1e-9)

    # (ii) The archived estimates are reproduced from the archived panel.
    print("Archived estimates reproduced from the archived panel")
    rep = estimate(arch, primary_w, hol)
    fx_a = pd.read_csv(FINAL / "table_secondary_fixed_SC.csv").set_index("outcome")
    sp_a = pd.read_csv(FINAL / "table_secondary_specific_SC.csv").set_index("outcome")
    pl_a = pd.read_csv(FINAL / "table_secondary_placebo_summary.csv").set_index("outcome")
    did_a = pd.read_csv(FINAL / "table_DiD_all_outcomes.csv")
    for o in OUTCOMES:
        f, s = rep["fixed"].set_index("outcome").loc[o], rep["specific"].set_index("outcome").loc[o]
        check(f"fixed ATT {o}", f.ATT, fx_a.loc[o, "ATT"], 1e-4)
        check(f"specific ATT {o}", s.ATT, sp_a.loc[o, "ATT"], 1e-4)
        if o in pl_a.index:
            r = rep["summary"].set_index("outcome").loc[o]
            check(f"rank p |ATT| {o}", r.ATT_rank_p, pl_a.loc[o, "ATT_rank_p"], 1e-9)
            check(f"rank p ratio {o}", r.RMSPE_rank_p, pl_a.loc[o, "RMSPE_rank_p"], 1e-9)
        for rh in (False, True):
            got = rep["did"][(rep["did"].outcome == o) & (rep["did"].remove_holidays == rh)].ATT.iloc[0]
            exp = did_a[(did_a.outcome == o) & (did_a.remove_holidays == rh)].ATT.iloc[0]
            check(f"DiD ATT {o} holidays_removed={rh}", got, exp, 1e-9)

    # Primary-outcome DiD rows (unaffected by R1) are carried over after verification.
    wp = wide(pool, "active_rate_pp")
    hp = pool.pivot(index="date", columns="country", values="is_holiday").sort_index()
    did_primary = pd.DataFrame([{"outcome": "active_rate_pp", "remove_holidays": rh,
                                 **did(wp, hp if rh else None)} for rh in (False, True)])
    for r in did_primary.itertuples():
        exp = did_a[(did_a.outcome == "active_rate_pp") & (did_a.remove_holidays == r.remove_holidays)].ATT.iloc[0]
        check(f"primary DiD ATT holidays_removed={r.remove_holidays}", r.ATT, exp, 1e-9)

    if FAILURES:
        sys.exit(f"\nFAILED: {len(FAILURES)} checks: {FAILURES}")

    # Corrected panel: eligible users in numerator and denominator.
    elp = build_panel(ud, elig, n_users, dates)
    elp = elp.merge(arch[["country", "date", "is_holiday", "holiday_name", "dow"]], on=["country", "date"])
    elp.to_parquet(SC_DIR / "country_day_outcomes_eligible.parquet", index=False)
    est = estimate(elp, primary_w, hol)

    est["fixed"].to_csv(FINAL / "table_secondary_fixed_SC_eligible.csv", index=False)
    est["specific"].to_csv(FINAL / "table_secondary_specific_SC_eligible.csv", index=False)
    est["weights"].to_csv(FINAL / "table_secondary_SC_weights_eligible.csv", index=False)
    est["placebos"].to_csv(FINAL / "table_secondary_placebos_all_eligible.csv", index=False)
    est["summary"].to_csv(FINAL / "table_secondary_placebo_summary_eligible.csv", index=False)
    pd.concat([did_primary, est["did"]], ignore_index=True).to_csv(
        FINAL / "table_DiD_all_outcomes_eligible.csv", index=False)

    # Archived versus corrected, for the revision log and the response to the referee.
    cmp_rows = []
    for spec, new, old in [("SC fixed weights", est["fixed"], rep["fixed"]),
                           ("SC outcome-specific weights", est["specific"], rep["specific"]),
                           ("DiD, all days", est["did"][~est["did"].remove_holidays], rep["did"][~rep["did"].remove_holidays]),
                           ("DiD, holidays excluded", est["did"][est["did"].remove_holidays], rep["did"][rep["did"].remove_holidays])]:
        n, o_ = new.set_index("outcome"), old.set_index("outcome")
        for o in OUTCOMES:
            cmp_rows.append({"specification": spec, "outcome": o,
                             "ATT_archived": o_.loc[o, "ATT"], "ATT_eligible": n.loc[o, "ATT"],
                             "relative_archived_pct": o_.loc[o, "relative_effect_pct"],
                             "relative_eligible_pct": n.loc[o, "relative_effect_pct"],
                             "ATT_change_pct": 100 * (n.loc[o, "ATT"] / o_.loc[o, "ATT"] - 1)})
    cmp = pd.DataFrame(cmp_rows)
    cmp.to_csv(FINAL / "table_secondary_archived_vs_eligible.csv", index=False)

    pd.set_option("display.width", 160)
    print("\nArchived versus eligible-only estimates")
    print(cmp.round(3).to_string(index=False))
    print("\nPlacebo ranks, eligible-only panel")
    print(est["summary"][["outcome", "ATT_rank_p", "RMSPE_rank_p"]].round(4).to_string(index=False))
    print("\nWrote results/synthetic_control/country_day_outcomes_eligible.parquet and "
          "results/final/*_eligible.csv")


if __name__ == "__main__":
    main()
