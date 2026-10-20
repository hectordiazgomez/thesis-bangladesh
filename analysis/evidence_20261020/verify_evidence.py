"""Offline, read-only validation of new audit counts and frozen inputs."""
from pathlib import Path
import hashlib
import json
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/evidence_20261020"
checks = []


def check(name, value):
    checks.append({"check": name, "passed": bool(value)})
    assert value, name


def main():
    cases = pd.read_csv(OUT / "individual_case_review.csv")
    p = pd.read_parquet(OUT / "core_push_audit.parquet")
    ev = pd.read_parquet(OUT / "core_event_decomposition.parquet")
    onset = pd.read_parquet(OUT / "onset_commits.parquet")
    summary = json.loads((OUT / "audit_summary.json").read_text())
    check("275 unique audited accounts", len(cases) == 275 and cases.login.nunique() == 275)
    check("Original overlapping cohorts", cases.core.sum() == 40 and cases.onset.sum() == 250
          and (cases.core & cases.onset).sum() == 15)
    check("Every account has a case reason", cases.reason.notna().all())
    check("Every direct core head has evidence", p.loc[p.audit_status.eq("direct"), "evidence_url"].str.startswith("https://github.com/").all())
    check("180 distinct core PushEvents", len(p) == p.event_id.nunique() == 180)
    check("All pushes partitioned", p.audit_status.value_counts().to_dict() == {
        "direct": 113, "no_direct_evidence": 48, "unavailable": 15, "suggestive": 4})
    check("Primary event accounting", ev.event_count.sum() == 237 and ev.remaining_events.sum() == 124)
    check("Non-push primary events retained", ev.loc[ev.event_type.ne("PushEvent"), "auto_heads"].sum() == 0)
    check("Original and sensitivity active user-days", len(ev[["login","date"]].drop_duplicates()) == 87
          and len(ev.loc[ev.remaining_events.gt(0), ["login","date"]].drop_duplicates()) == 48)
    check("Automation types sum to audited heads", sum(summary["auto_kind_counts"].values()) == 113)
    check("All sensitivity counts use original 10241 denominator",
          all(abs(r["daily_rate_pct"]-100*r["active_user_days"]/(4*10241)) < 1e-12 for r in summary["core_sensitivity"]))
    check("Original onset cohort retained", len(onset) == 1097 and onset.pusher_login.nunique() == 250)
    check("Original onset push partition", onset.push_time.ge("2024-07-24").sum() == 752
          and onset.push_time.lt("2024-07-24").sum() == 345
          and onset.push_time.lt("2024-07-23").sum() == 99)
    check("Alternative endpoints monotone and explicit",
          [r["commits"] for r in summary["timing"]] == [899, 904, 1097])
    delta = pd.read_parquet(OUT / "country_domain_daily.parquet")
    check("Every country-domain-date included", len(delta) == 15*20*127)
    check("Empty denominators remain missing rates", delta.loc[delta.eligible_users.eq(0), "rate_pct"].isna().all())
    check("Rates valid for nonempty cells", delta.loc[delta.eligible_users.gt(0), "rate_pct"].between(0,100).all())
    check("Every date partitions original sample", delta.groupby("date").eligible_users.sum().eq(59158).all())
    atlas = json.loads((OUT / "country_atlas_validation.json").read_text())
    check("Existing synthetic paths reproduced", atlas["max_synthetic_path_difference"] < 1e-9)
    check("All 300 support cells disclosed", atlas["zero_cells"] == 45 and atlas["small_nonzero_cells"] == 144)
    feature = pd.read_parquet(OUT / "residual_features_corrected_weekend.parquet")
    check("Corrected weekend bounded", feature.frisa.le(feature.active).all())
    # Fixed content hashes, taken before this extension, include Oct 19 inputs.
    frozen = json.loads((OUT / "frozen_inputs_sha256.json").read_text())
    for x in frozen:
        check("Preserved "+x["path"], hashlib.sha256((ROOT/x["path"]).read_bytes()).hexdigest() == x["sha256"])
    report = {"checks": checks, "count": len(checks), "all_passed": all(x["passed"] for x in checks)}
    (OUT / "verification.json").write_text(json.dumps(report, indent=2))
    print(f"PASS: {len(checks)} checks; {len(frozen)} original/input files byte-identical.")


if __name__ == "__main__":
    main()
