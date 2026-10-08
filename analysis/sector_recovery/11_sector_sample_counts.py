#!/usr/bin/env python3
"""Audit R4 counts without changing source data or rerunning classification.

Run from any directory with the sector environment (pandas + pyarrow):
    .venv-sector/bin/python analysis/sector_recovery/11_sector_sample_counts.py

Classification follows 06_build_sector_recovery_panel.py: recovered README,
successful prediction, score >= 0.80. Arts concentration follows
07_repo_recovery_eventstudy.py: all event types, May 23--July 17, 2024.
The 82.5 figure is an event share for the largest Arts repository, NOT the
share of classified repositories assigned to Arts. Compare at the manuscript's
one-decimal precision; retain the unrounded percentage in the CSV.

Absent local inputs produce a blank value, matches=unavailable, and an explicit
MISSING path in source_file. A mismatch or unavailable input exits with code 1
after writing the audit; it never changes manuscript text.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

import pandas as pd


ACCOUNTS = "data/sector_recovery/bangladesh_full_preactivity_stats.parquet"
EVENTS = "data/sector_recovery/bd_preactive20000_repo_event_day_metadata.parquet"
DATABASE = "data/sector_recovery/repo_sector.sqlite"
OUTPUT = "results/sector_recovery/sector_sample_counts.csv"
FIELDS = ["statistic", "value", "manuscript_value", "source_file", "matches"]


def recompute(root: Path) -> list[dict]:
    cache = {}

    def accounts():
        x = pd.read_parquet(root / ACCOUNTS, columns=["login_lower", "pre_active_days"])
        if x.login_lower.isna().any() or x.login_lower.duplicated().any():
            raise ValueError("Preactivity input must contain one non-null login per account")
        return x.loc[x.pre_active_days.ge(1), "login_lower"].nunique()

    def events():
        if EVENTS not in cache:
            x = pd.read_parquet(root / EVENTS, columns=["repo_name", "event_date", "event_count"])
            if x.isna().any().any() or x.event_count.lt(0).any():
                raise ValueError("Event panel has missing fields or negative counts")
            x["event_date"] = pd.to_datetime(x.event_date).dt.normalize()
            cache[EVENTS] = x
        return cache[EVENTS]

    def predictions():
        if DATABASE not in cache:
            # mode=ro prevents creation or writes to the archived database.
            con = sqlite3.connect((root / DATABASE).resolve().as_uri() + "?mode=ro", uri=True)
            try:
                cache[DATABASE] = pd.read_sql_query(
                    "SELECT repo_name, readme_status, prediction_status, naics_code, score FROM repos", con
                )
            finally:
                con.close()
            x = cache[DATABASE]
            if x.repo_name.isna().any() or x.repo_name.duplicated().any():
                raise ValueError("Repository database must contain unique non-null names")
        return cache[DATABASE]

    def classified():
        x = predictions()
        return x[x.readme_status.eq("ok") & x.prediction_status.eq("ok") & x.score.ge(0.80)]

    def arts_top1():
        x = events()
        p = classified()
        names = p.loc[p.naics_code.eq("71"), "repo_name"]
        pre = x[x.repo_name.isin(names) & x.event_date.between("2024-05-23", "2024-07-17")]
        totals = pre.groupby("repo_name").event_count.sum()
        if totals.empty or totals.sum() <= 0:
            raise ValueError("No positive Arts baseline events; concentration is undefined")
        return 100.0 * totals.max() / totals.sum()

    specifications = [
        ("preactive_accounts", 23866, [ACCOUNTS], accounts),
        ("distinct_panel_repositories", 168875, [EVENTS], lambda: events().repo_name.nunique()),
        ("historical_readmes_recovered", 92979, [DATABASE], lambda: predictions().readme_status.eq("ok").sum()),
        ("classified_repositories_score_ge_0_80_with_readme", 32491, [DATABASE], lambda: len(classified())),
        ("arts_top1_repository_pre_events_share_pct", 82.5, [EVENTS, DATABASE], arts_top1),
    ]
    rows = []
    for name, expected, sources, calculate in specifications:
        missing = [p for p in sources if not (root / p).is_file()]
        if missing:
            value, matches = "", "unavailable"
        else:
            value = calculate()
            matches = str(round(value, 1) == expected if isinstance(expected, float) else value == expected).lower()
        rows.append(dict(zip(FIELDS, [
            name, value, expected,
            "; ".join(("MISSING: " if p in missing else "") + p for p in sources), matches,
        ])))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, help="Optional audit CSV path (default: repo results directory)")
    args = parser.parse_args()
    rows = recompute(args.repo_root)
    output = args.output or args.repo_root / OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(output)
    for row in rows:
        print(f"{row['statistic']}: {row['value']} (manuscript {row['manuscript_value']}; matches={row['matches']})")
    return int(any(row["matches"] != "true" for row in rows))


if __name__ == "__main__":
    raise SystemExit(main())
