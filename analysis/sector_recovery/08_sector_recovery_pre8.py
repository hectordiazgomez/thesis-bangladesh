#!/usr/bin/env python3
"""
Corrected sector recovery analysis using an 8-week pre-shutdown baseline.

Main sample:
- repo classification: historical README + score >= threshold
- repo cohort: at least one PushEvent during the last 8 complete pre-shutdown weeks

Outcome:
- repo daily PushEvent activity rate within each event period
- each repo's baseline = its mean weekly activity rate over weeks -8,...,-1
- coefficient at period k = mean(repo_rate_k - repo_baseline)
- 95% CI from repo-level paired differences

Also reports recovery index:
  100 * sector mean activity rate at k / sector mean pre-baseline activity rate

Event time:
-8 ... -1 : complete pre weeks
 0          : shutdown Jul 18-23 (6 days)
 +1         : Jul 24-30
 +2         : Jul 31-Aug 6
 ...
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

DEFAULT_MAIN_SECTORS = [
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
        m = dates.between(r.start, r.end)
        out.loc[m] = int(r.event_time)
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


def first_recovery_week(g: pd.DataFrame, threshold: float) -> float:
    z = g[
        (g["event_time"] >= 1)
        & g["recovery_index"].notna()
        & (g["recovery_index"] >= threshold)
    ]
    if z.empty:
        return np.nan
    return int(z["event_time"].min())


def first_sustained_recovery_week(g: pd.DataFrame, threshold: float, n_weeks: int = 2) -> float:
    z = g[g["event_time"] >= 1].sort_values("event_time")
    vals = z["recovery_index"].to_numpy()
    ets = z["event_time"].to_numpy()
    for i in range(len(vals) - n_weeks + 1):
        block = vals[i:i+n_weeks]
        if np.all(np.isfinite(block)) and np.all(block >= threshold):
            return int(ets[i])
    return np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--threshold", type=float, default=0.80)
    ap.add_argument("--min-pre-repos", type=int, default=200)
    args = ap.parse_args()

    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    ev = pd.read_parquet(Path(args.events).expanduser())
    ev["event_date"] = pd.to_datetime(ev["event_date"]).dt.normalize()
    ev["event_count"] = pd.to_numeric(ev["event_count"], errors="coerce").fillna(0)

    pred = load_predictions(Path(args.db).expanduser(), args.threshold)

    # MAIN outcome = PushEvent only.
    x = ev[ev["event_type"].eq("PushEvent")].merge(
        pred[["repo_name", "sector", "naics_code", "score"]],
        on="repo_name",
        how="inner",
        validate="many_to_one",
    )

    periods = build_periods(ev["event_date"].max())
    x["event_time"] = assign_event_time(x["event_date"], periods)
    x = x[x["event_time"].notna()].copy()
    x["event_time"] = x["event_time"].astype(int)

    # Pre-treatment cohort only.
    pre = x[x["event_time"].between(-N_PRE_WEEKS, -1)]
    cohort = pre[["repo_name", "sector", "naics_code"]].drop_duplicates()

    support = (
        cohort.groupby(["sector", "naics_code"], as_index=False)
        .agg(pre_repos=("repo_name", "nunique"))
        .sort_values("pre_repos", ascending=False)
    )
    keep = support.loc[support["pre_repos"] >= args.min_pre_repos, "sector"].tolist()
    cohort = cohort[cohort["sector"].isin(keep)].copy()

    # Repo x event period active days.
    rd = (
        x[x["repo_name"].isin(cohort["repo_name"])]
        .groupby(
            ["repo_name", "sector", "naics_code", "event_time", "event_date"],
            as_index=False
        )
        .agg(events=("event_count", "sum"))
    )
    rd["active"] = 1

    rp = (
        rd.groupby(["repo_name", "sector", "naics_code", "event_time"], as_index=False)
        .agg(
            active_days=("active", "sum"),
            events=("events", "sum"),
        )
    )

    # Balanced repo-period grid.
    pm = periods[["event_time", "period", "days"]].copy()
    frames = []
    for sector, repos in cohort.groupby("sector"):
        r = repos[["repo_name", "sector", "naics_code"]].drop_duplicates().copy()
        r["_k"] = 1
        p = pm.copy()
        p["_k"] = 1
        frames.append(r.merge(p, on="_k").drop(columns="_k"))
    panel = pd.concat(frames, ignore_index=True)

    panel = panel.merge(
        rp,
        on=["repo_name", "sector", "naics_code", "event_time"],
        how="left",
    )
    panel["active_days"] = panel["active_days"].fillna(0)
    panel["events"] = panel["events"].fillna(0)
    panel["active_day_rate"] = panel["active_days"] / panel["days"]

    # Each repo's 8-week pre mean.
    pre_baseline = (
        panel[panel["event_time"].between(-N_PRE_WEEKS, -1)]
        .groupby("repo_name", as_index=False)
        .agg(
            repo_pre_mean_rate=("active_day_rate", "mean"),
            repo_pre_sd_rate=("active_day_rate", "std"),
        )
    )
    panel = panel.merge(pre_baseline, on="repo_name", how="left", validate="many_to_one")
    panel["diff_from_pre_pp"] = 100 * (
        panel["active_day_rate"] - panel["repo_pre_mean_rate"]
    )

    # Coefficients.
    rows = []
    for (sector, code, et), g in panel.groupby(["sector", "naics_code", "event_time"]):
        d = g["diff_from_pre_pp"].dropna().to_numpy()
        n = len(d)
        beta = float(d.mean()) if n else np.nan
        se = float(d.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan

        mean_rate = float(g["active_day_rate"].mean())
        mean_base = float(g["repo_pre_mean_rate"].mean())
        recovery_index = 100 * mean_rate / mean_base if mean_base > 0 else np.nan

        rows.append({
            "sector": sector,
            "naics_code": code,
            "event_time": int(et),
            "n_repos": n,
            "mean_active_day_rate_pct": 100 * mean_rate,
            "mean_pre8_baseline_rate_pct": 100 * mean_base,
            "beta_vs_pre8_pp": beta,
            "se_pp": se,
            "ci_low_pp": beta - Z * se if np.isfinite(se) else np.nan,
            "ci_high_pp": beta + Z * se if np.isfinite(se) else np.nan,
            "recovery_index": recovery_index,
        })

    coef = pd.DataFrame(rows).merge(
        periods[["event_time", "period", "start", "end"]],
        on="event_time",
        how="left",
    )
    coef.to_csv(outdir / "sector_eventstudy_pre8_baseline.csv", index=False)
    panel.to_parquet(outdir / "repo_period_panel_pre8_baseline.parquet", index=False)
    support.to_csv(outdir / "sector_support_push_recentpre.csv", index=False)

    # Summary table.
    summary_rows = []
    for (sector, code), g in coef.groupby(["sector", "naics_code"]):
        def val(et, col):
            z = g.loc[g["event_time"].eq(et), col]
            return float(z.iloc[0]) if len(z) else np.nan

        summary_rows.append({
            "sector": sector,
            "naics_code": code,
            "n_repos": int(g["n_repos"].max()),
            "pre8_baseline_rate_pct": val(-1, "mean_pre8_baseline_rate_pct"),
            "shutdown_recovery_index": val(0, "recovery_index"),
            "week1_recovery_index": val(1, "recovery_index"),
            "week2_recovery_index": val(2, "recovery_index"),
            "week4_recovery_index": val(4, "recovery_index"),
            "week8_recovery_index": val(8, "recovery_index"),
            "shutdown_beta_pp": val(0, "beta_vs_pre8_pp"),
            "shutdown_ci_low_pp": val(0, "ci_low_pp"),
            "shutdown_ci_high_pp": val(0, "ci_high_pp"),
            "first_week_ge_50": first_recovery_week(g, 50),
            "first_week_ge_80": first_recovery_week(g, 80),
            "first_week_ge_100": first_recovery_week(g, 100),
            "first_sustained2_ge_80": first_sustained_recovery_week(g, 80, 2),
        })

    summary = pd.DataFrame(summary_rows).sort_values("n_repos", ascending=False)
    summary.to_csv(outdir / "sector_recovery_summary_pre8.csv", index=False)

    # Main advisor-facing coefficient figure: supported sectors, excluding Arts by default.
    main_sectors = [s for s in DEFAULT_MAIN_SECTORS if s in keep]
    plot_df = coef[
        coef["sector"].isin(main_sectors)
        & coef["event_time"].between(-8, 8)
    ].copy()

    # One figure per sector, coefficient style.
    for sector in main_sectors:
        g = plot_df[plot_df["sector"].eq(sector)].sort_values("event_time")
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
        ax.set_xlabel("Event time (0 = shutdown; +1 = Jul 24–30)")
        ax.set_ylabel("Difference from 8-week pre mean (pp)")
        ax.set_title(f"Recovery event study: {sector}")
        fig.tight_layout()
        fig.savefig(outdir / f"eventstudy_pre8_{slugify(sector)}.png", dpi=200)
        plt.close(fig)

    # Recovery-index figure for top main sectors.
    fig, ax = plt.subplots(figsize=(11, 7))
    for sector in main_sectors:
        g = plot_df[plot_df["sector"].eq(sector)].sort_values("event_time")
        ax.plot(g["event_time"], g["recovery_index"], marker="o", label=sector)
    ax.axhline(100, linewidth=1)
    ax.axvline(0, linewidth=1, linestyle="--")
    ax.set_xlabel("Event time (0 = shutdown; +1 = Jul 24–30)")
    ax.set_ylabel("Recovery index (8-week pre mean = 100)")
    ax.set_title("Recovery of repository activity by sector")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(outdir / "sector_recovery_index_pre8.png", dpi=200)
    plt.close(fig)

    print("\nMAIN SUMMARY")
    cols = [
        "sector", "n_repos",
        "shutdown_recovery_index",
        "week1_recovery_index",
        "week2_recovery_index",
        "week4_recovery_index",
        "week8_recovery_index",
        "first_week_ge_80",
        "first_sustained2_ge_80",
    ]
    print(summary[summary["sector"].isin(main_sectors)][cols].to_string(index=False))

    print("\nSaved to:", outdir)


if __name__ == "__main__":
    main()
