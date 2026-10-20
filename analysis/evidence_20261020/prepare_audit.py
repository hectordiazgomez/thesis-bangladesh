"""Freeze the residual-publication and author-time audit universes.

Reads the existing samples without changing them. UTC dates and the seven
recovered primary event types are retained. Outputs are new, descriptive data.
"""
from pathlib import Path
import json
import pandas as pd
import db_dtypes  # register the source parquet date extension

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/evidence_20261020"
DATA = ROOT / "data/evidence_20261020"
TYPES = ["PushEvent", "PullRequestEvent", "PullRequestReviewEvent",
         "PullRequestReviewCommentEvent", "IssuesEvent", "ReleaseEvent", "CreateEvent"]


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    DATA.mkdir(exist_ok=True, parents=True)
    f = pd.read_parquet(ROOT / "results/advisor_20261019/residual_user_characteristics_with_age.parquet")
    f.login = f.login.str.lower()
    target = f[f.core_public_active | f.onset_author].copy().sort_values("login")
    target.to_parquet(OUT / "audit_cohorts.parquet", index=False)
    e = pd.read_parquet(ROOT / "data/advisor_20261019/international_repo_event_day.parquet")
    e.date = pd.to_datetime(e.date)
    core = e[e.country.eq("Bangladesh") & e.login.isin(target.loc[target.core_public_active, "login"])
             & e.date.between("2024-07-19", "2024-07-22")].copy()
    core["primary"] = core.event_type.isin(TYPES)
    core.to_parquet(OUT / "core_repository_events.parquet", index=False)
    m = pd.read_parquet(ROOT / "results/mechanism/commit_sha_author_push_master.parquet")
    m.authored_time = pd.to_datetime(m.authored_time, utc=True)
    m.push_time = pd.to_datetime(m.push_time, utc=True)
    m.pusher_login = m.pusher_login.str.lower()
    onset = m[m.author_equals_pusher.fillna(False) & m.plausible_author_delay.fillna(False)
              & m.authored_time.ge("2024-07-18T15:00:00Z")
              & m.authored_time.lt("2024-07-24T00:00:00Z")].copy()
    onset.to_parquet(OUT / "onset_commits.parquet", index=False)
    pushes = pd.read_parquet(ROOT / "results/mechanism/bd_push_events_20240701_20240810.parquet")
    pushes.push_time = pd.to_datetime(pushes.push_time, utc=True)
    pushes.pusher_login = pushes.pusher_login.str.lower()
    pushes = pushes.drop_duplicates("event_id")
    core_push = pushes[pushes.pusher_login.isin(target.loc[target.core_public_active, "login"])
                       & pushes.push_time.ge("2024-07-19")
                       & pushes.push_time.lt("2024-07-23")].copy()
    core_push.to_parquet(OUT / "core_pushes.parquet", index=False)
    pushes[pushes.pusher_login.isin(target.login)].to_parquet(OUT / "audit_push_history.parquet", index=False)
    commits = onset[["pusher_login", "repo", "sha"]].rename(columns={"pusher_login": "login"})
    commits["source"] = "onset_authored"
    heads = core_push[["pusher_login", "repo", "head_sha"]].rename(columns={"pusher_login": "login", "head_sha": "sha"})
    heads["source"] = "core_push_head"
    commits = pd.concat([commits, heads], ignore_index=True).drop_duplicates(["repo", "sha", "source"])
    commits.to_csv(OUT / "commit_audit_targets.csv", index=False)
    # Repository snapshot = latest observed audited commit, with its SHA retained.
    snaps = pd.concat([
        onset[["repo", "sha", "authored_time"]].rename(columns={"authored_time": "timestamp"}),
        core_push[["repo", "head_sha", "push_time"]].rename(columns={"head_sha": "sha", "push_time": "timestamp"})
    ]).sort_values(["timestamp", "sha"]).drop_duplicates("repo", keep="last")
    snaps.to_csv(OUT / "repository_snapshot_targets.csv", index=False)
    profile_targets = [{"login": x} for x in target.login]
    (DATA / "profile_targets.json").write_text(json.dumps(profile_targets, indent=2))
    summary = dict(audit_users=len(target), core_users=int(target.core_public_active.sum()),
                   onset_users=int(target.onset_author.sum()), overlap=int((target.core_public_active & target.onset_author).sum()),
                   core_primary_events=int(core.loc[core.primary, "event_count"].sum()),
                   core_primary_repositories=int(core.loc[core.primary, "repo_name"].nunique()),
                   core_pushes=len(core_push), onset_commits=len(onset), snapshot_repositories=len(snaps))
    (OUT / "audit_universe.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
