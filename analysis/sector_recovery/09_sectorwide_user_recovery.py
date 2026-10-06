#!/usr/bin/env python3
"""
Sector-wide recovery among the fixed 20,000 Bangladesh users.

WHY THIS SCRIPT
---------------
The previous repo-cohort event study answers:
    "Did repositories that were active before the shutdown reactivate?"

That is useful, but old repositories naturally decay and users can switch projects.
This script answers the broader recovery question:
    "How much observable PushEvent activity occurred in each economic sector
     among the same fixed 20,000 users, including activity on NEW post-shutdown repos?"

Main sample:
- fixed 20,000 users selected using PRE-treatment activity only
- repo sector: historical README classifier, score >= threshold
- outcome: probability that a sampled user has >=1 PushEvent on a classified
  repo in sector s on a day

Baseline:
- user's mean daily sector activity over the 56 days in the last 8 complete
  pre-shutdown weeks (May 23-Jul 17, 2024)

Event periods:
-8 ... -1 : complete pre weeks
 0          : shutdown Jul 18-23 (6 days)
 +1         : Jul 24-30
 +2         : Jul 31-Aug 6
 ...

For each sector x event period:
- mean user daily activity probability
- difference from 8-week pre mean (percentage points)
- SE and 95% CI across the fixed 20,000 users
- recovery index (8-week pre mean = 100)

This specification includes:
- continuing old repos
- newly created/first-observed post-shutdown repos
- users switching repositories within a sector
- users switching INTO a different sector
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PRE_END = pd.Timestamp("2024-07-17")
SHUTDOWN_START = pd.Timestamp("2024-07-18")
SHUTDOWN_END = pd.Timestamp("2024-07-23")
RESTORE = pd.Timestamp("2024-07-24")
N_PRE_WEEKS = 8
Z = 1.959963984540054

MAIN_SECTORS = [
    "Information",
    "Educational Services",
    "Retail Trade",
    "Health Care and Social Assistance",
    "Professional, Scientific, Technical Services",
    "Accommodation and Food Services",
    "Finance and Insurance",
    "Real Estate and Rental",
    "Administrative and Support Services",
]


def slugify(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:80]


def build_periods(last_date: pd.Timestamp) -> pd.DataFrame:
    rows = []
    for k in range(-N_PRE_WEEKS, 0):
        end = PRE_END - pd.Timedelta(days=7 * (-k - 1))
        start = end - pd.Timedelta(days=6)
        rows.append((k, f"pre_{k}", start, end, 7))

    rows.append((0, "shutdown", SHUTDOWN_START, SHUTDOWN_END, 6))

    k = 1
    start = RESTORE
    while start + pd.Timedelta(days=6) <= last_date:
        end = start + pd.Timedelta(days=6)
        rows.append((k, f"post_{k}", start, end, 7))
        k += 1
        start = end + pd.Timedelta(days=1)

    return pd.DataFrame(rows, columns=["event_time", "period", "start", "end", "days"])


def assign_event_time(dates: pd.Series, periods: pd.DataFrame) -> pd.Series:
    out = pd.Series(pd.NA, index=dates.index, dtype="Int64")
    for r in periods.itertuples(index=False):
        mask = dates.between(r.start, r.end)
        out.loc[mask] = int(r.event_time)
    return out


def load_predictions(db_path: Path, threshold: float) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    pred = pd.read_sql_query(
        """
        SELECT repo_name, readme_status, prediction_status,
               naics_code, sector, score
        FROM repos
        """,
        con,
    )
    con.close()
    pred["score"] = pd.to_numeric(pred["score"], errors="coerce")
    return pred[
        pred["prediction_status"].eq("ok")
        & pred["readme_status"].eq("ok")
        & pred["score"].ge(threshold)
    ].copy()


def moments_with_implicit_zeros(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
    n_users: int,
) -> tuple[float, float, float, float, int]:
    """
    baseline/current each contain login_lower + rate.
    Missing users have rate 0.
    Returns:
      mean_current, mean_baseline, mean_diff, se_diff, n_users
    """
    z = baseline.merge(current, on="login_lower", how="outer")
    z["baseline_rate"] = z["baseline_rate"].fillna(0.0)
    z["current_rate"] = z["current_rate"].fillna(0.0)
    z["diff"] = z["current_rate"] - z["baseline_rate"]

    # Users absent from both sparse tables contribute zero.
    sum_diff = float(z["diff"].sum())
    sumsq_diff = float((z["diff"] ** 2).sum())
    sum_cur = float(z["current_rate"].sum())
    sum_base = float(z["baseline_rate"].sum())

    mean_diff = sum_diff / n_users
    mean_cur = sum_cur / n_users
    mean_base = sum_base / n_users

    if n_users > 1:
        var = (sumsq_diff - (sum_diff ** 2) / n_users) / (n_users - 1)
        var = max(var, 0.0)
        se = np.sqrt(var / n_users)
    else:
        se = np.nan

    return mean_cur, mean_base, mean_diff, se, n_users


def first_week(g: pd.DataFrame, threshold: float, sustained: int = 1):
    z = g[g["event_time"] >= 1].sort_values("event_time")
    vals = z["recovery_index"].to_numpy()
    ets = z["event_time"].to_numpy()

    for i in range(len(vals) - sustained + 1):
        block = vals[i:i+sustained]
        if np.all(np.isfinite(block)) and np.all(block >= threshold):
            return int(ets[i])
    return np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--threshold", type=float, default=0.80)
    args = ap.parse_args()

    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    print("Loading fixed user sample...")
    sample = pd.read_parquet(Path(args.sample).expanduser())
    sample["login_lower"] = sample["login_lower"].astype(str).str.lower().str.strip()
    users = sample["login_lower"].drop_duplicates()
    n_users = len(users)
    if n_users != 20_000:
        raise SystemExit(f"Expected 20,000 fixed users, got {n_users:,}")
    user_set = set(users)
    print("Fixed users:", f"{n_users:,}")

    print("Loading events...")
    ev = pd.read_parquet(Path(args.events).expanduser())
    ev["event_date"] = pd.to_datetime(ev["event_date"]).dt.normalize()
    ev["login_lower"] = ev["login_lower"].astype(str).str.lower().str.strip()
    ev["event_count"] = pd.to_numeric(ev["event_count"], errors="coerce").fillna(0)
    ev = ev[ev["login_lower"].isin(user_set)]

    print("Loading high-confidence sectors...")
    pred = load_predictions(Path(args.db).expanduser(), args.threshold)
    pred = pred[pred["sector"].isin(MAIN_SECTORS)].copy()
    print("Classified repos in main sectors:", f"{len(pred):,}")

    # PushEvent production outcome.
    x = ev[ev["event_type"].eq("PushEvent")].merge(
        pred[["repo_name", "sector", "naics_code"]],
        on="repo_name",
        how="inner",
        validate="many_to_one",
    )

    periods = build_periods(ev["event_date"].max())
    x["event_time"] = assign_event_time(x["event_date"], periods)
    x = x[x["event_time"].notna()].copy()
    x["event_time"] = x["event_time"].astype(int)

    # user x sector x day binary activity: multiple repos that day still count once.
    usd = (
        x.groupby(
            ["login_lower", "sector", "naics_code", "event_time", "event_date"],
            as_index=False,
        )
        .agg(push_events=("event_count", "sum"))
    )
    usd["active"] = 1

    # sparse user-sector-period active-day rates
    usp = (
        usd.groupby(
            ["login_lower", "sector", "naics_code", "event_time"],
            as_index=False,
        )
        .agg(active_days=("active", "sum"))
        .merge(periods[["event_time", "days"]], on="event_time", how="left")
    )
    usp["rate"] = usp["active_days"] / usp["days"]

    # User-sector baseline = total active days across 8 pre weeks / 56.
    pre_usd = usd[usd["event_time"].between(-N_PRE_WEEKS, -1)]
    baseline = (
        pre_usd.groupby(["login_lower", "sector", "naics_code"], as_index=False)
        .agg(pre_active_days=("active", "sum"))
    )
    baseline["baseline_rate"] = baseline["pre_active_days"] / (N_PRE_WEEKS * 7)

    # Sector support among the fixed users.
    support = (
        baseline.groupby(["sector", "naics_code"], as_index=False)
        .agg(
            pre_users=("login_lower", "nunique"),
            pre_active_user_days=("pre_active_days", "sum"),
        )
        .sort_values("pre_active_user_days", ascending=False)
    )
    support.to_csv(outdir / "sectorwide_support.csv", index=False)

    rows = []
    for sector in MAIN_SECTORS:
        b = baseline[baseline["sector"].eq(sector)][
            ["login_lower", "baseline_rate"]
        ].copy()

        code_vals = pred.loc[pred["sector"].eq(sector), "naics_code"].dropna().unique()
        code = code_vals[0] if len(code_vals) else ""

        for r in periods.itertuples(index=False):
            c = usp[
                usp["sector"].eq(sector)
                & usp["event_time"].eq(r.event_time)
            ][["login_lower", "rate"]].rename(columns={"rate": "current_rate"})

            mean_cur, mean_base, mean_diff, se, n = moments_with_implicit_zeros(
                b, c, n_users
            )

            recovery = 100 * mean_cur / mean_base if mean_base > 0 else np.nan

            rows.append({
                "sector": sector,
                "naics_code": code,
                "event_time": int(r.event_time),
                "period": r.period,
                "start": r.start,
                "end": r.end,
                "n_users_fixed": n,
                "mean_user_daily_activity_pct": 100 * mean_cur,
                "mean_pre8_user_daily_activity_pct": 100 * mean_base,
                "beta_vs_pre8_pp": 100 * mean_diff,
                "se_pp": 100 * se,
                "ci_low_pp": 100 * (mean_diff - Z * se),
                "ci_high_pp": 100 * (mean_diff + Z * se),
                "recovery_index": recovery,
            })

    coef = pd.DataFrame(rows)
    coef.to_csv(outdir / "sectorwide_user_eventstudy.csv", index=False)

    # Summary.
    summary_rows = []
    for sector, g in coef.groupby("sector"):
        def val(et, col):
            z = g.loc[g["event_time"].eq(et), col]
            return float(z.iloc[0]) if len(z) else np.nan

        summary_rows.append({
            "sector": sector,
            "pre8_user_daily_activity_pct": val(-1, "mean_pre8_user_daily_activity_pct"),
            "shutdown_recovery_index": val(0, "recovery_index"),
            "week1_recovery_index": val(1, "recovery_index"),
            "week2_recovery_index": val(2, "recovery_index"),
            "week4_recovery_index": val(4, "recovery_index"),
            "week8_recovery_index": val(8, "recovery_index"),
            "shutdown_beta_pp": val(0, "beta_vs_pre8_pp"),
            "shutdown_ci_low_pp": val(0, "ci_low_pp"),
            "shutdown_ci_high_pp": val(0, "ci_high_pp"),
            "first_week_ge_50": first_week(g, 50, 1),
            "first_week_ge_80": first_week(g, 80, 1),
            "first_week_ge_100": first_week(g, 100, 1),
            "first_sustained2_ge_80": first_week(g, 80, 2),
        })

    summary = pd.DataFrame(summary_rows)
    summary = summary.merge(support[["sector", "pre_users", "pre_active_user_days"]],
                            on="sector", how="left")
    summary = summary.sort_values("pre_active_user_days", ascending=False)
    summary.to_csv(outdir / "sectorwide_recovery_summary.csv", index=False)

    # Advisor-style coefficient plots, one sector each.
    for sector in MAIN_SECTORS:
        g = coef[
            coef["sector"].eq(sector)
            & coef["event_time"].between(-8, 8)
        ].sort_values("event_time")

        fig, ax = plt.subplots(figsize=(9, 5.2))
        ax.errorbar(
            g["event_time"],
            g["beta_vs_pre8_pp"],
            yerr=Z * g["se_pp"],
            fmt="o",
            capsize=3,
        )
        ax.axhline(0, linewidth=1)
        ax.axvline(0, linewidth=1, linestyle="--")
        ax.set_xlabel("Event time (0 = shutdown; +1 = Jul 24-30)")
        ax.set_ylabel("Change from 8-week pre mean (pp)")
        ax.set_title(f"Sector-wide recovery: {sector}")
        fig.tight_layout()
        fig.savefig(outdir / f"sectorwide_eventstudy_{slugify(sector)}.png", dpi=200)
        plt.close(fig)

    # One combined recovery-index figure.
    fig, ax = plt.subplots(figsize=(11, 7))
    for sector in MAIN_SECTORS:
        g = coef[
            coef["sector"].eq(sector)
            & coef["event_time"].between(-8, 8)
        ].sort_values("event_time")
        ax.plot(g["event_time"], g["recovery_index"], marker="o", label=sector)

    ax.axhline(100, linewidth=1)
    ax.axvline(0, linewidth=1, linestyle="--")
    ax.set_xlabel("Event time (0 = shutdown; +1 = Jul 24-30)")
    ax.set_ylabel("Recovery index (8-week pre mean = 100)")
    ax.set_title("Sector-wide observable software activity recovery")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(outdir / "sectorwide_recovery_index.png", dpi=200)
    plt.close(fig)

    print("\nSECTOR-WIDE SUMMARY")
    cols = [
        "sector", "pre_users",
        "shutdown_recovery_index",
        "week1_recovery_index",
        "week2_recovery_index",
        "week4_recovery_index",
        "week8_recovery_index",
        "first_week_ge_80",
        "first_sustained2_ge_80",
    ]
    print(summary[cols].to_string(index=False))

    print("\nSaved to:", outdir)


if __name__ == "__main__":
    main()
