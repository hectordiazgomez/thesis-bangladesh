#!/usr/bin/env python3
"""
Build repo-sector recovery panels from:
  1) GH Archive user x repo x day x event_type panel
  2) SQLite repository NAICS predictions

Main classification:
  prediction_status='ok'
  readme_status='ok'
  score >= 0.80

Outputs:
  - repo_naics_predictions.parquet/csv
  - sector_day_main.parquet
  - sector_week_main.parquet/csv
  - sector_recovery_summary.csv
  - sector_sample_sizes.csv
  - user_pre_sector_weights.parquet/csv
  - sector_recovery_index_top10.png
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PRE_END = pd.Timestamp("2024-07-17")
SHUTDOWN_START = pd.Timestamp("2024-07-18")
SHUTDOWN_END = pd.Timestamp("2024-07-23")
RESTORE = pd.Timestamp("2024-07-24")
LAST_PRE_BASELINE_WEEKS = 8


def pre_week_index(d: pd.Timestamp) -> int:
    delta = (PRE_END.normalize() - d.normalize()).days
    return -(delta // 7 + 1)


def post_week_index(d: pd.Timestamp) -> int:
    return (d.normalize() - RESTORE).days // 7


def classify_period_week(d: pd.Timestamp):
    d = pd.Timestamp(d).normalize()
    if d <= PRE_END:
        return "pre", pre_week_index(d)
    if SHUTDOWN_START <= d <= SHUTDOWN_END:
        return "shutdown", np.nan
    if d >= RESTORE:
        return "recovery", post_week_index(d)
    return "outside", np.nan


def first_week_reaching(g: pd.DataFrame, threshold: float):
    x = g[
        (g["period"] == "recovery")
        & g["recovery_index_events"].notna()
        & (g["recovery_index_events"] >= threshold)
    ]
    if len(x) == 0:
        return np.nan
    return int(x["week_index"].min())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--threshold", type=float, default=0.80)
    ap.add_argument("--top-sectors", type=int, default=10)
    args = ap.parse_args()

    events_path = Path(args.events).expanduser()
    db_path = Path(args.db).expanduser()
    out = Path(args.outdir).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    print("Loading event panel...")
    ev = pd.read_parquet(events_path)
    ev["event_date"] = pd.to_datetime(ev["event_date"]).dt.normalize()
    ev["event_count"] = pd.to_numeric(ev["event_count"], errors="coerce").fillna(0).astype("int64")

    required = {"event_date", "login_lower", "repo_name", "event_type", "event_count"}
    missing = required - set(ev.columns)
    if missing:
        raise SystemExit(f"Missing event columns: {sorted(missing)}")

    print("Loading NAICS predictions...")
    con = sqlite3.connect(db_path)
    pred = pd.read_sql_query(
        """
        SELECT
            repo_name,
            first_activity,
            last_activity,
            target_date,
            total_events,
            pre_events,
            shutdown_events,
            recovery_events,
            readme_status,
            prediction_status,
            naics_code,
            sector,
            score,
            second_code,
            second_score,
            score_margin,
            high_confidence,
            model_name,
            model_revision
        FROM repos
        """,
        con,
    )
    con.close()

    pred["score"] = pd.to_numeric(pred["score"], errors="coerce")
    pred.to_parquet(out / "repo_naics_predictions.parquet", index=False)
    pred.to_csv(out / "repo_naics_predictions.csv", index=False)

    main_pred = pred[
        pred["prediction_status"].eq("ok")
        & pred["readme_status"].eq("ok")
        & pred["score"].ge(args.threshold)
    ].copy()

    print(f"All canonical repos: {len(pred):,}")
    print(f"Main classifiable repos: {len(main_pred):,} "
          f"(README ok + score >= {args.threshold:.2f})")

    x = ev.merge(
        main_pred[["repo_name", "naics_code", "sector", "score"]],
        on="repo_name",
        how="inner",
        validate="many_to_one",
    )

    print(f"Matched event rows: {len(x):,}")
    print(f"Matched repos: {x.repo_name.nunique():,}")
    print(f"Matched users: {x.login_lower.nunique():,}")

    tmp = x["event_date"].map(classify_period_week)
    x["period"] = [z[0] for z in tmp]
    x["week_index"] = [z[1] for z in tmp]

    sector_day = (
        x.groupby(["event_date", "sector", "naics_code"], as_index=False)
        .agg(
            total_events=("event_count", "sum"),
            active_repos=("repo_name", "nunique"),
            active_users=("login_lower", "nunique"),
            event_rows=("event_count", "size"),
        )
        .sort_values(["sector", "event_date"])
    )

    all_days = pd.date_range(ev.event_date.min(), ev.event_date.max(), freq="D")
    sectors = main_pred[["sector", "naics_code"]].drop_duplicates().sort_values("sector")
    grid = (
        pd.MultiIndex.from_product(
            [all_days, sectors["sector"].tolist()],
            names=["event_date", "sector"],
        )
        .to_frame(index=False)
        .merge(sectors, on="sector", how="left")
    )
    sector_day = grid.merge(
        sector_day,
        on=["event_date", "sector", "naics_code"],
        how="left",
    )
    for c in ["total_events", "active_repos", "active_users", "event_rows"]:
        sector_day[c] = sector_day[c].fillna(0).astype("int64")

    tmp = sector_day["event_date"].map(classify_period_week)
    sector_day["period"] = [z[0] for z in tmp]
    sector_day["week_index"] = [z[1] for z in tmp]
    sector_day.to_parquet(out / "sector_day_main.parquet", index=False)

    wk = sector_day[sector_day["period"].isin(["pre", "recovery"])].copy()
    sector_week = (
        wk.groupby(["period", "week_index", "sector", "naics_code"], as_index=False)
        .agg(
            total_events=("total_events", "sum"),
            active_repo_days=("active_repos", "sum"),
            active_user_days=("active_users", "sum"),
        )
    )
    sector_week["week_index"] = sector_week["week_index"].astype(int)

    x_week = x[x["period"].isin(["pre", "recovery"])].copy()
    distinct_week = (
        x_week.groupby(["period", "week_index", "sector", "naics_code"], as_index=False)
        .agg(
            active_repos=("repo_name", "nunique"),
            active_users=("login_lower", "nunique"),
        )
    )
    distinct_week["week_index"] = distinct_week["week_index"].astype(int)
    sector_week = sector_week.merge(
        distinct_week,
        on=["period", "week_index", "sector", "naics_code"],
        how="left",
    )
    for c in ["active_repos", "active_users"]:
        sector_week[c] = sector_week[c].fillna(0).astype(int)

    baseline_weeks = list(range(-LAST_PRE_BASELINE_WEEKS, 0))
    base = (
        sector_week[
            (sector_week["period"] == "pre")
            & sector_week["week_index"].isin(baseline_weeks)
        ]
        .groupby(["sector", "naics_code"], as_index=False)
        .agg(
            baseline_events=("total_events", "mean"),
            baseline_active_repos=("active_repos", "mean"),
            baseline_active_users=("active_users", "mean"),
            baseline_active_user_days=("active_user_days", "mean"),
        )
    )

    sector_week = sector_week.merge(base, on=["sector", "naics_code"], how="left")

    def ratio100(num, den):
        return np.where(den > 0, 100 * num / den, np.nan)

    sector_week["recovery_index_events"] = ratio100(
        sector_week["total_events"], sector_week["baseline_events"]
    )
    sector_week["recovery_index_repos"] = ratio100(
        sector_week["active_repos"], sector_week["baseline_active_repos"]
    )
    sector_week["recovery_index_users"] = ratio100(
        sector_week["active_users"], sector_week["baseline_active_users"]
    )
    sector_week.to_parquet(out / "sector_week_main.parquet", index=False)
    sector_week.to_csv(out / "sector_week_main.csv", index=False)

    pre_x = x[x["event_date"] <= PRE_END]
    sample_sizes = (
        pre_x.groupby(["sector", "naics_code"], as_index=False)
        .agg(
            pre_repos=("repo_name", "nunique"),
            pre_users=("login_lower", "nunique"),
            pre_events=("event_count", "sum"),
            pre_event_rows=("event_count", "size"),
        )
        .sort_values("pre_events", ascending=False)
    )
    sample_sizes.to_csv(out / "sector_sample_sizes.csv", index=False)

    rows = []
    for (sector, code), g in sector_week.groupby(["sector", "naics_code"]):
        rec = g[g["period"].eq("recovery")].copy()

        def at_week(k):
            z = rec.loc[rec["week_index"].eq(k), "recovery_index_events"]
            return float(z.iloc[0]) if len(z) else np.nan

        rows.append({
            "sector": sector,
            "naics_code": code,
            "baseline_events_last8_pre_weeks": float(g["baseline_events"].dropna().iloc[0])
                if g["baseline_events"].notna().any() else np.nan,
            "week0_events_index": at_week(0),
            "week1_events_index": at_week(1),
            "week2_events_index": at_week(2),
            "week3_events_index": at_week(3),
            "week4_events_index": at_week(4),
            "first_week_ge_50pct": first_week_reaching(g, 50),
            "first_week_ge_80pct": first_week_reaching(g, 80),
            "first_week_ge_100pct": first_week_reaching(g, 100),
        })

    summary = (
        pd.DataFrame(rows)
        .merge(sample_sizes, on=["sector", "naics_code"], how="left")
        .sort_values(["pre_events", "sector"], ascending=[False, True])
    )
    summary.to_csv(out / "sector_recovery_summary.csv", index=False)

    recent_pre_start = PRE_END - pd.Timedelta(days=7 * LAST_PRE_BASELINE_WEEKS - 1)
    recent = x[x["event_date"].between(recent_pre_start, PRE_END)].copy()
    user_sector = (
        recent.groupby(["login_lower", "sector", "naics_code"], as_index=False)
        .agg(
            recent_pre_events=("event_count", "sum"),
            recent_pre_active_days=("event_date", "nunique"),
            recent_pre_repos=("repo_name", "nunique"),
        )
    )
    user_totals = (
        user_sector.groupby("login_lower", as_index=False)["recent_pre_events"]
        .sum()
        .rename(columns={"recent_pre_events": "user_recent_pre_events"})
    )
    user_sector = user_sector.merge(user_totals, on="login_lower", how="left")
    user_sector["event_weight"] = (
        user_sector["recent_pre_events"] / user_sector["user_recent_pre_events"]
    )
    user_sector.to_parquet(out / "user_pre_sector_weights.parquet", index=False)
    user_sector.to_csv(out / "user_pre_sector_weights.csv", index=False)

    top = sample_sizes.head(args.top_sectors)["sector"].tolist()
    plot_df = sector_week[
        sector_week["sector"].isin(top)
        & sector_week["week_index"].between(-8, 8)
    ].copy()

    fig, ax = plt.subplots(figsize=(11, 7))
    for sector, g in plot_df.groupby("sector"):
        g = g.sort_values("week_index")
        ax.plot(g["week_index"], g["recovery_index_events"], marker="o", label=sector)

    ax.axhline(100, linewidth=1)
    ax.axvline(-0.5, linewidth=1, linestyle="--")
    ax.set_xlabel("Week relative to restoration (week 0 = Jul 24–30, 2024)")
    ax.set_ylabel("Activity index (last 8 pre-shutdown weeks = 100)")
    ax.set_title("Repository activity recovery by NAICS sector")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out / "sector_recovery_index_top10.png", dpi=200)
    plt.close(fig)

    print("\nSaved outputs:")
    for p in sorted(out.iterdir()):
        print(" ", p)

    print("\nTop sector support:")
    print(sample_sizes.head(args.top_sectors).to_string(index=False))

    print("\nRecovery summary:")
    print(summary.head(args.top_sectors).to_string(index=False))


if __name__ == "__main__":
    main()
