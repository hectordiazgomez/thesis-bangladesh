#!/usr/bin/env python3
"""
Repo-level recovery event study by NAICS sector.

Main specification:
- repository sector: historical README classifier, score >= threshold
- cohort: repos active during the last 8 complete pre-shutdown weeks
- main production outcome: PushEvent active-day rate
- reference period: Jul 11-17, 2024 (event week -1)
- shutdown period: Jul 18-23 (6 days, duration-adjusted as daily rate)
- recovery week +1: Jul 24-30
- +2: Jul 31-Aug 6, etc.
- coefficients are within-repo paired differences from week -1
- SE = standard error of repo-level paired differences
- 95% normal CI

Also produces:
- any-event robustness
- sector concentration audit
- post-shutdown new-repo entry by sector
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
PRE_WEEKS = 8
Z = 1.959963984540054


def slugify(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s[:80]


def build_periods(last_date: pd.Timestamp):
    periods = []

    # -8 ... -1, with -1 = Jul 11-17
    for k in range(-PRE_WEEKS, 0):
        end = PRE_END - pd.Timedelta(days=7 * (-k - 1))
        start = end - pd.Timedelta(days=6)
        periods.append({
            "event_time": k,
            "period": f"pre_{k}",
            "start": start,
            "end": end,
            "days": 7,
            "label": str(k),
        })

    periods.append({
        "event_time": 0,
        "period": "shutdown",
        "start": SHUTDOWN_START,
        "end": SHUTDOWN_END,
        "days": 6,
        "label": "shutdown",
    })

    k = 1
    start = RESTORE
    while start + pd.Timedelta(days=6) <= last_date:
        end = start + pd.Timedelta(days=6)
        periods.append({
            "event_time": k,
            "period": f"post_{k}",
            "start": start,
            "end": end,
            "days": 7,
            "label": f"+{k}",
        })
        k += 1
        start = end + pd.Timedelta(days=1)

    return pd.DataFrame(periods)


def assign_period(dates: pd.Series, periods: pd.DataFrame):
    out = pd.Series(pd.NA, index=dates.index, dtype="Int64")
    for r in periods.itertuples(index=False):
        mask = dates.between(r.start, r.end)
        out.loc[mask] = int(r.event_time)
    return out


def load_predictions(db_path: Path, threshold: float):
    con = sqlite3.connect(db_path)
    pred = pd.read_sql_query(
        """
        SELECT
            repo_name, readme_status, prediction_status,
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


def event_study_for_mode(
    ev: pd.DataFrame,
    pred: pd.DataFrame,
    periods: pd.DataFrame,
    mode: str,
    min_pre_repos: int,
    outdir: Path,
):
    assert mode in {"push", "any"}

    x = ev.merge(
        pred[["repo_name", "sector", "naics_code", "score"]],
        on="repo_name",
        how="inner",
        validate="many_to_one",
    )

    if mode == "push":
        x = x[x["event_type"].eq("PushEvent")].copy()

    x["event_time"] = assign_period(x["event_date"], periods)
    x = x[x["event_time"].notna()].copy()
    x["event_time"] = x["event_time"].astype(int)

    # Recent-pre cohort only, so post-treatment activity never determines inclusion.
    recent_pre = x[x["event_time"].between(-PRE_WEEKS, -1)]
    cohort = recent_pre[["repo_name", "sector", "naics_code"]].drop_duplicates()

    support = (
        cohort.groupby(["sector", "naics_code"], as_index=False)
        .agg(pre_repos=("repo_name", "nunique"))
        .sort_values("pre_repos", ascending=False)
    )
    keep_sectors = support.loc[support["pre_repos"] >= min_pre_repos, "sector"].tolist()
    cohort = cohort[cohort["sector"].isin(keep_sectors)].copy()

    # Repo x day activity indicator.
    repo_day = (
        x[x["repo_name"].isin(cohort["repo_name"])]
        .groupby(["repo_name", "sector", "naics_code", "event_date", "event_time"], as_index=False)
        .agg(events=("event_count", "sum"))
    )
    repo_day["active"] = 1

    # Aggregate active days and event counts per repo-period.
    rp = (
        repo_day.groupby(["repo_name", "sector", "naics_code", "event_time"], as_index=False)
        .agg(
            active_days=("active", "sum"),
            events=("events", "sum"),
        )
    )

    # Complete balanced repo x period panel with zeros.
    period_meta = periods[["event_time", "days", "label", "period"]].copy()
    frames = []
    for sector, c in cohort.groupby("sector"):
        repos = c[["repo_name", "sector", "naics_code"]].drop_duplicates()
        repos["_key"] = 1
        pm = period_meta.copy()
        pm["_key"] = 1
        g = repos.merge(pm, on="_key", how="outer").drop(columns="_key")
        frames.append(g)
    panel = pd.concat(frames, ignore_index=True)

    panel = panel.merge(
        rp,
        on=["repo_name", "sector", "naics_code", "event_time"],
        how="left",
    )
    panel["active_days"] = panel["active_days"].fillna(0)
    panel["events"] = panel["events"].fillna(0)

    # Duration-adjusted outcomes.
    panel["active_day_rate"] = panel["active_days"] / panel["days"]
    panel["events_per_day"] = panel["events"] / panel["days"]

    # Reference week -1 at repo level.
    ref = panel[panel["event_time"].eq(-1)][
        ["repo_name", "active_day_rate", "events_per_day"]
    ].rename(
        columns={
            "active_day_rate": "ref_active_day_rate",
            "events_per_day": "ref_events_per_day",
        }
    )
    panel = panel.merge(ref, on="repo_name", how="left", validate="many_to_one")
    panel["diff_active_pp"] = 100 * (panel["active_day_rate"] - panel["ref_active_day_rate"])
    panel["diff_events_per_day"] = panel["events_per_day"] - panel["ref_events_per_day"]

    # Paired difference coefficients and CIs.
    rows = []
    for (sector, code, et), g in panel.groupby(["sector", "naics_code", "event_time"]):
        vals = g["diff_active_pp"].dropna().to_numpy()
        n = len(vals)
        beta = float(vals.mean()) if n else np.nan
        se = float(vals.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan
        rows.append({
            "mode": mode,
            "sector": sector,
            "naics_code": code,
            "event_time": int(et),
            "n_repos": n,
            "beta_active_day_pp": beta,
            "se_active_day_pp": se,
            "ci_low_active_day_pp": beta - Z * se if np.isfinite(se) else np.nan,
            "ci_high_active_day_pp": beta + Z * se if np.isfinite(se) else np.nan,
            "mean_active_day_rate_pct": 100 * float(g["active_day_rate"].mean()),
            "mean_ref_active_day_rate_pct": 100 * float(g["ref_active_day_rate"].mean()),
            "mean_events_per_day": float(g["events_per_day"].mean()),
        })

    coef = pd.DataFrame(rows)
    coef = coef.merge(
        period_meta[["event_time", "label", "period"]],
        on="event_time",
        how="left",
    )
    coef.to_csv(outdir / f"repo_reactivation_eventstudy_{mode}.csv", index=False)
    panel.to_parquet(outdir / f"repo_period_panel_{mode}.parquet", index=False)
    support.to_csv(outdir / f"sector_support_recentpre_{mode}.csv", index=False)

    # Summary at selected post periods.
    sel = [0, 1, 2, 4, 8]
    summary = coef[coef["event_time"].isin(sel)].pivot(
        index=["sector", "naics_code", "n_repos"],
        columns="event_time",
        values="mean_active_day_rate_pct",
    ).reset_index()
    summary.columns.name = None
    summary = summary.rename(columns={
        0: "shutdown_active_day_rate_pct",
        1: "week1_active_day_rate_pct",
        2: "week2_active_day_rate_pct",
        4: "week4_active_day_rate_pct",
        8: "week8_active_day_rate_pct",
    })
    summary.to_csv(outdir / f"repo_reactivation_summary_{mode}.csv", index=False)

    # One clean coefficient figure per supported sector.
    for sector in keep_sectors:
        g = coef[coef["sector"].eq(sector)].sort_values("event_time")
        fig, ax = plt.subplots(figsize=(9, 5.5))
        ax.errorbar(
            g["event_time"],
            g["beta_active_day_pp"],
            yerr=Z * g["se_active_day_pp"],
            fmt="o",
            capsize=3,
        )
        ax.axhline(0, linewidth=1)
        ax.axvline(0, linewidth=1, linestyle="--")
        ax.set_xlabel("Event period (0 = Jul 18–23 shutdown; +1 = Jul 24–30)")
        ax.set_ylabel("Change in daily repo activity probability (pp), relative to week -1")
        ax.set_title(f"Repository recovery event study: {sector}")
        fig.tight_layout()
        fig.savefig(
            outdir / f"eventstudy_{mode}_{slugify(sector)}.png",
            dpi=200,
        )
        plt.close(fig)

    return coef, panel, support


def concentration_audit(ev, pred, outdir):
    x = ev.merge(
        pred[["repo_name", "sector", "naics_code"]],
        on="repo_name",
        how="inner",
        validate="many_to_one",
    )
    x = x[
        x["event_date"].between(
            PRE_END - pd.Timedelta(days=7 * PRE_WEEKS - 1),
            PRE_END,
        )
    ].copy()

    repo = (
        x.groupby(["sector", "naics_code", "repo_name"], as_index=False)
        .agg(pre_events=("event_count", "sum"))
    )

    rows = []
    for (sector, code), g in repo.groupby(["sector", "naics_code"]):
        vals = np.sort(g["pre_events"].to_numpy())[::-1]
        total = vals.sum()
        rows.append({
            "sector": sector,
            "naics_code": code,
            "pre_repos": len(vals),
            "pre_events": int(total),
            "top1_repo_share_pct": 100 * vals[:1].sum() / total if total else np.nan,
            "top5_repo_share_pct": 100 * vals[:5].sum() / total if total else np.nan,
            "top10_repo_share_pct": 100 * vals[:10].sum() / total if total else np.nan,
            "top20_repo_share_pct": 100 * vals[:20].sum() / total if total else np.nan,
        })
    audit = pd.DataFrame(rows).sort_values("pre_events", ascending=False)
    audit.to_csv(outdir / "sector_concentration_recentpre.csv", index=False)
    return audit


def new_repo_entry(ev, pred, periods, outdir):
    x = ev.merge(
        pred[["repo_name", "sector", "naics_code"]],
        on="repo_name",
        how="inner",
        validate="many_to_one",
    )
    first = (
        x.groupby(["repo_name", "sector", "naics_code"], as_index=False)
        .agg(first_observed=("event_date", "min"))
    )
    first = first[first["first_observed"] >= RESTORE].copy()
    first["event_time"] = assign_period(first["first_observed"], periods)
    first = first[first["event_time"].notna()].copy()
    first["event_time"] = first["event_time"].astype(int)

    out = (
        first.groupby(["sector", "naics_code", "event_time"], as_index=False)
        .agg(new_repos=("repo_name", "nunique"))
        .sort_values(["sector", "event_time"])
    )
    out.to_csv(outdir / "new_repo_entry_by_sector_week.csv", index=False)
    return out


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
    periods = build_periods(ev["event_date"].max())

    print(f"High-confidence historical-README repos: {len(pred):,}")
    print("Periods:")
    print(periods[["event_time", "start", "end", "days"]].to_string(index=False))

    audit = concentration_audit(ev, pred, outdir)
    print("\nConcentration audit:")
    print(audit.head(12).to_string(index=False))

    for mode in ["push", "any"]:
        print(f"\nBuilding {mode} event study...")
        coef, panel, support = event_study_for_mode(
            ev=ev,
            pred=pred,
            periods=periods,
            mode=mode,
            min_pre_repos=args.min_pre_repos,
            outdir=outdir,
        )
        print(
            support[support["pre_repos"] >= args.min_pre_repos]
            .head(12)
            .to_string(index=False)
        )

    entry = new_repo_entry(ev, pred, periods, outdir)
    print("\nNew post-shutdown repo entry sample:")
    print(entry.head(20).to_string(index=False))

    print("\nDone. Outputs in:", outdir)


if __name__ == "__main__":
    main()
