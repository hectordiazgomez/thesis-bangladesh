"""Read-only public GitHub evidence, cached separately from original datasets.

Uses `gh auth token` in memory; credentials and private repository content are
never saved. Historical commit SHAs, messages and workflow blobs are evidence;
current profile metadata are explicitly dated and cannot establish 2024 location.
Run after prepare_audit.py. Reruns reuse already saved responses.
"""
from pathlib import Path
import concurrent.futures as cf
import base64
import datetime as dt
import json
import subprocess
import time
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/evidence_20261020"
OUT = ROOT / "results/evidence_20261020"
TOKEN = None


def request(method, endpoint, **kwargs):
    url = endpoint if endpoint.startswith("https://") else "https://api.github.com/" + endpoint
    for attempt in range(4):
        try:
            r = requests.request(method, url, headers={
                "Authorization": "Bearer " + TOKEN,
                "Accept": "application/vnd.github+json",
                "User-Agent": "thesis-public-evidence-audit"}, timeout=40, **kwargs)
            if r.status_code in (403, 429, 500, 502, 503):
                time.sleep(min(2 ** attempt, 8))
                continue
            return r.status_code, r.json()
        except (requests.RequestException, ValueError):
            time.sleep(2 ** attempt)
    return 599, {}


def append_rows(path, rows):
    with path.open("a") as f:
        for row in rows:
            row["retrieved_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_rows(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def profiles():
    path = DATA / "public_profiles.jsonl"
    known = {x["requested_login"] for x in read_rows(path)}
    targets = [x["login"] for x in json.loads((DATA / "profile_targets.json").read_text()) if x["login"] not in known]
    def one(login):
        status, p = request("GET", "users/" + login)
        keys = ["login", "id", "type", "created_at", "html_url", "public_repos", "bio"]
        return {"requested_login": login, "status": status, "api_url": "https://api.github.com/users/" + login,
                **{k: p.get(k) for k in keys}}
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for i, row in enumerate(pool.map(one, targets), 1):
            append_rows(path, [row])
            if i % 40 == 0:
                print("profiles", i, "/", len(targets), flush=True)


def gql_batches(kind):
    if kind == "commits":
        targets = pd.read_csv(OUT / "commit_audit_targets.csv").drop_duplicates(["repo", "sha"]).to_dict("records")
    else:
        targets = pd.read_csv(OUT / "repository_snapshot_targets.csv").to_dict("records")
    path = DATA / ("public_" + kind + ".jsonl")
    known = {(x["repo"], x["sha"]) for x in read_rows(path) if x.get("status") != "query_error"}
    targets = [x for x in targets if (x["repo"], x["sha"]) not in known]
    for start in range(0, len(targets), 20):
        batch = targets[start:start + 20]
        fields = []
        for i, row in enumerate(batch):
            owner, name = row["repo"].split("/", 1)
            head = f'r{i}:repository(owner:{json.dumps(owner)},name:{json.dumps(name)}){{isPrivate nameWithOwner'
            if kind == "commits":
                head += ' object(oid:' + json.dumps(row["sha"]) + '){... on Commit{oid url message authoredDate committedDate additions deletions changedFilesIfAvailable author{name user{login}} committer{name user{login}}}}'
            else:
                head += ' isArchived isFork createdAt description'
                for alias, suffix in [("workflows", ".github/workflows"), ("readme", "README.md"), ("readme_lower", "readme.md")]:
                    expr = row["sha"] + ":" + suffix
                    head += f' {alias}:object(expression:{json.dumps(expr)})' + '{... on Tree{entries{name type object{... on Blob{text isTruncated byteSize}}}} ... on Blob{text isTruncated byteSize}}'
            fields.append(head + "}")
        status, p = request("POST", "graphql", json={"query": "query{" + "".join(fields) + "}"})
        rows = []
        for i, row in enumerate(batch):
            node = (p.get("data") or {}).get("r" + str(i))
            error = status != 200 or not p.get("data")
            private = bool(node and node.get("isPrivate"))
            rows.append(dict(repo=row["repo"], sha=row["sha"], status="query_error" if error else "nonpublic" if private else "ok" if node else "unavailable",
                             api_url="https://api.github.com/graphql", data=None if private else node,
                             errors=p.get("errors") if error else None))
        append_rows(path, rows)
        print(kind, min(start + len(batch), len(targets)), "/", len(targets), flush=True)


def core_diffs():
    path = DATA / "public_core_commit_diffs.jsonl"
    targets = pd.read_parquet(OUT / "core_pushes.parquet").drop_duplicates(["repo", "head_sha"])
    known = {(x["repo"], x["sha"]) for x in read_rows(path)}
    # All these repositories are already queried for visibility in the snapshot pass.
    public = {x["repo"] for x in read_rows(DATA / "public_snapshots.jsonl") if x.get("status") == "ok"}
    targets = [r for r in targets.to_dict("records") if (r["repo"], r["head_sha"]) not in known and r["repo"] in public]
    def one(row):
        url = "https://api.github.com/repos/" + row["repo"] + "/commits/" + row["head_sha"]
        status, p = request("GET", url)
        files = [{k: z.get(k) for k in ["filename", "status", "additions", "deletions", "changes", "blob_url"]} for z in p.get("files", [])]
        return dict(repo=row["repo"], sha=row["head_sha"], status=status, api_url=url,
                    message=p.get("commit", {}).get("message"), files=files, files_returned=len(files),
                    stats=p.get("stats"), author_type=(p.get("author") or {}).get("type"),
                    committer_type=(p.get("committer") or {}).get("type"))
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for i, row in enumerate(pool.map(one, targets), 1):
            append_rows(path, [row])
            if i % 40 == 0:
                print("diffs", i, "/", len(targets), flush=True)


def main():
    global TOKEN
    TOKEN = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    profiles()
    gql_batches("commits")
    gql_batches("snapshots")
    core_diffs()
    supplements()
    print("PUBLIC EVIDENCE FETCH COMPLETE", flush=True)


def supplements():
    """Selected follow-up evidence requested by individual case inspection."""
    commits = read_rows(DATA / "public_commits.jsonl")
    path = DATA / "public_supplementary_diffs.jsonl"
    known = {(x["repo"], x["sha"]) for x in read_rows(path)}
    for c in commits:
        if c["repo"].lower().startswith("shadowshahriar/") and (c["repo"], c["sha"]) not in known:
            url = "https://api.github.com/repos/" + c["repo"] + "/commits/" + c["sha"]
            status, p = request("GET", url)
            files = [{k: x.get(k) for k in ["filename", "status", "additions", "deletions", "patch", "blob_url"]}
                     for x in p.get("files", [])]
            append_rows(path, [dict(repo=c["repo"], sha=c["sha"], status=status, api_url=url, files=files)])
    path = DATA / "public_supplementary_trees.jsonl"
    known = {(x["repo"], x["sha"]) for x in read_rows(path)}
    for x in read_rows(DATA / "public_snapshots.jsonl"):
        if (x["repo"].lower().startswith("shadowshahriar/") or x["repo"].lower() == "hrshadhin/hosts") and (x["repo"], x["sha"]) not in known:
            url = "https://api.github.com/repos/" + x["repo"] + "/git/trees/" + x["sha"] + "?recursive=1"
            status, r = request("GET", url)
            append_rows(path, [dict(repo=x["repo"], sha=x["sha"], status=status, api_url=url,
                                   tree=r.get("tree", []), truncated=r.get("truncated"))])
    path = DATA / "public_supplementary_blobs.jsonl"
    known = {x["file"] for x in read_rows(path)}
    for filename in ["crontab.example", "update.sh"]:
        if filename in known:
            continue
        sha = "bebaa5518ab57ceaa43ee74eaddbd5642487d586"
        url = "https://api.github.com/repos/hrshadhin/hosts/contents/" + filename + "?ref=" + sha
        status, r = request("GET", url)
        append_rows(path, [dict(repo="hrshadhin/hosts", sha=sha, file=filename, status=status,
                               api_url=url, text=base64.b64decode(r.get("content", "")).decode())])


if __name__ == "__main__":
    main()
