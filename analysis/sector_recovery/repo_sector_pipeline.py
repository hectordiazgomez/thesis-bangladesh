#!/usr/bin/env python3
"""
Repository sector-classification pipeline for the Bangladesh shutdown thesis.

Stages
------
1) prepare:
   Build one canonical task per repo_name from the GH Archive event panel.
   Target README snapshot:
      - repos observed on/before 2024-07-17 -> snapshot at 2024-07-17
      - repos first observed after 2024-07-17 -> snapshot at first observed activity date

2) metadata:
   Fetch current GitHub description/topics/default branch with batched GraphQL.
   Uses 20 concurrent network workers by default and checkpoints to SQLite.

3) readmes:
   Fetch a historical root README using temporary filtered git clones.
   Uses 20 concurrent I/O workers by default. Each clone is deleted immediately.
   No repository is retained on disk.

4) classify:
   Load the Hugging Face multilingual NAICS classifier once and classify in batches.
   DO NOT run 20 copies of the 568M-parameter model.

5) export:
   Export repository predictions to parquet/csv.

Requirements:
  - git
  - gh (authenticated) OR GITHUB_TOKEN environment variable
  - Python packages in requirements_sector.txt
  - alexanderquispe/naics-github-train installed editable so src.text_format is importable
"""

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures as cf
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


CUTOFF = pd.Timestamp("2024-07-17")
MODEL_NAME = "aquiro1994/naics-github-classifier-multilingual"

NAICS_SECTORS = {
    "11": "Agriculture, Forestry, Fishing and Hunting",
    "21": "Mining, Quarrying, Oil and Gas Extraction",
    "22": "Utilities",
    "23": "Construction",
    "31-33": "Manufacturing",
    "42": "Wholesale Trade",
    "44-45": "Retail Trade",
    "48-49": "Transportation and Warehousing",
    "51": "Information",
    "52": "Finance and Insurance",
    "53": "Real Estate and Rental",
    "54": "Professional, Scientific, Technical Services",
    "56": "Administrative and Support Services",
    "61": "Educational Services",
    "62": "Health Care and Social Assistance",
    "71": "Arts, Entertainment, and Recreation",
    "72": "Accommodation and Food Services",
    "81": "Other Services",
    "92": "Public Administration",
}


def connect_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS repos (
            repo_name TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            name TEXT NOT NULL,
            first_activity TEXT,
            last_activity TEXT,
            target_date TEXT,
            total_events INTEGER DEFAULT 0,
            pre_events INTEGER DEFAULT 0,
            shutdown_events INTEGER DEFAULT 0,
            recovery_events INTEGER DEFAULT 0,

            metadata_status TEXT,
            description TEXT,
            topics_json TEXT,
            default_branch TEXT,
            is_fork INTEGER,
            is_archived INTEGER,
            metadata_updated_at TEXT,

            readme_status TEXT,
            readme_snapshot_sha TEXT,
            readme_path TEXT,
            readme_chars INTEGER,
            readme_sha256 TEXT,
            readme_zlib BLOB,
            readme_updated_at TEXT,

            prediction_status TEXT,
            naics_code TEXT,
            sector TEXT,
            score REAL,
            second_code TEXT,
            second_score REAL,
            score_margin REAL,
            high_confidence INTEGER,
            model_name TEXT,
            model_revision TEXT,
            prediction_updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_repos_metadata_status
            ON repos(metadata_status);
        CREATE INDEX IF NOT EXISTS idx_repos_readme_status
            ON repos(readme_status);
        CREATE INDEX IF NOT EXISTS idx_repos_prediction_status
            ON repos(prediction_status);
        """
    )
    return con


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def split_repo(repo_name: str) -> tuple[str, str] | None:
    if not isinstance(repo_name, str):
        return None
    parts = repo_name.strip().split("/", 1)
    if len(parts) != 2 or not all(parts):
        return None
    return parts[0], parts[1]


def stage_prepare(args: argparse.Namespace) -> None:
    events_path = Path(args.events).expanduser()
    db_path = Path(args.db).expanduser()

    df = pd.read_parquet(events_path)
    required = {"repo_name", "event_date", "event_type", "event_count"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing columns in {events_path}: {sorted(missing)}")

    df = df.copy()
    df["event_date"] = pd.to_datetime(df["event_date"])
    df["event_count"] = pd.to_numeric(df["event_count"], errors="coerce").fillna(0).astype("int64")
    df = df[df["repo_name"].notna()]
    df = df[df["repo_name"].astype(str).str.contains("/", regex=False)]

    # Canonicalize by repo_name, not repo_id. The pre-period extraction did not retain repo_id,
    # so the same repo can otherwise appear twice (NULL repo_id pre + numeric repo_id post).
    df["repo_name"] = df["repo_name"].astype(str).str.strip()
    df["period"] = pd.cut(
        df["event_date"],
        bins=[
            pd.Timestamp.min,
            pd.Timestamp("2024-07-17 23:59:59"),
            pd.Timestamp("2024-07-23 23:59:59"),
            pd.Timestamp.max,
        ],
        labels=["pre", "shutdown", "recovery"],
    )

    base = (
        df.groupby("repo_name")
        .agg(
            first_activity=("event_date", "min"),
            last_activity=("event_date", "max"),
            total_events=("event_count", "sum"),
        )
        .reset_index()
    )

    pvt = (
        df.pivot_table(
            index="repo_name",
            columns="period",
            values="event_count",
            aggfunc="sum",
            fill_value=0,
            observed=True,
        )
        .reset_index()
    )
    pvt.columns.name = None
    for c in ["pre", "shutdown", "recovery"]:
        if c not in pvt:
            pvt[c] = 0

    base = base.merge(pvt[["repo_name", "pre", "shutdown", "recovery"]], on="repo_name", how="left")
    base = base.rename(
        columns={
            "pre": "pre_events",
            "shutdown": "shutdown_events",
            "recovery": "recovery_events",
        }
    )

    base["target_date"] = base["first_activity"].map(
        lambda x: CUTOFF if pd.Timestamp(x) <= CUTOFF else pd.Timestamp(x).normalize()
    )

    con = connect_db(db_path)
    inserted = 0
    skipped = 0

    for r in base.itertuples(index=False):
        parts = split_repo(r.repo_name)
        if not parts:
            skipped += 1
            continue
        owner, name = parts
        con.execute(
            """
            INSERT INTO repos(
                repo_name, owner, name, first_activity, last_activity, target_date,
                total_events, pre_events, shutdown_events, recovery_events
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo_name) DO UPDATE SET
                first_activity=excluded.first_activity,
                last_activity=excluded.last_activity,
                target_date=excluded.target_date,
                total_events=excluded.total_events,
                pre_events=excluded.pre_events,
                shutdown_events=excluded.shutdown_events,
                recovery_events=excluded.recovery_events
            """,
            (
                r.repo_name,
                owner,
                name,
                pd.Timestamp(r.first_activity).date().isoformat(),
                pd.Timestamp(r.last_activity).date().isoformat(),
                pd.Timestamp(r.target_date).date().isoformat(),
                int(r.total_events),
                int(r.pre_events),
                int(r.shutdown_events),
                int(r.recovery_events),
            ),
        )
        inserted += 1
        if inserted % 5000 == 0:
            con.commit()
            print(f"prepared {inserted:,}")

    con.commit()
    n = con.execute("SELECT COUNT(*) FROM repos").fetchone()[0]
    con.close()

    print(f"Canonical repositories in DB: {n:,}")
    print(f"Invalid repo names skipped: {skipped:,}")
    print(f"DB: {db_path}")


def get_github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token.strip()

    gh = shutil.which("gh")
    if not gh:
        raise SystemExit(
            "Need GitHub authentication. Either export GITHUB_TOKEN or install/login with gh."
        )
    p = subprocess.run([gh, "auth", "token"], capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        raise SystemExit("Could not obtain token from `gh auth token`.")
    return p.stdout.strip()


def gql_escape(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def build_metadata_query(rows: list[tuple[str, str, str]]) -> str:
    blocks = []
    for i, (_repo_name, owner, name) in enumerate(rows):
        blocks.append(
            f"""
            r{i}: repository(owner: {gql_escape(owner)}, name: {gql_escape(name)}) {{
              nameWithOwner
              description
              isFork
              isArchived
              defaultBranchRef {{ name }}
              repositoryTopics(first: 20) {{
                nodes {{ topic {{ name }} }}
              }}
            }}
            """
        )
    return "query {\n" + "\n".join(blocks) + "\n}"


async def gql_request(session, token: str, query: str, sem: asyncio.Semaphore, max_tries=8):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "bangladesh-thesis-sector-pipeline",
    }
    backoff = 2.0

    for attempt in range(max_tries):
        async with sem:
            try:
                async with session.post(url, json={"query": query}, headers=headers, timeout=90) as resp:
                    payload = await resp.json(content_type=None)
                    if resp.status == 200 and not payload.get("errors"):
                        return payload, dict(resp.headers)

                    retry_after = resp.headers.get("retry-after")
                    remaining = resp.headers.get("x-ratelimit-remaining")
                    reset = resp.headers.get("x-ratelimit-reset")

                    if retry_after:
                        wait = float(retry_after)
                    elif remaining == "0" and reset:
                        wait = max(2.0, float(reset) - time.time() + 2)
                    else:
                        wait = backoff

                    if resp.status in {403, 429} or payload.get("errors"):
                        await asyncio.sleep(wait)
                        backoff = min(backoff * 2, 120)
                        continue

                    return payload, dict(resp.headers)
            except Exception:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 120)

    return {"errors": [{"message": "max retries exceeded"}]}, {}


async def metadata_async(args: argparse.Namespace) -> None:
    import aiohttp

    db_path = Path(args.db).expanduser()
    con = connect_db(db_path)
    q = """
        SELECT repo_name, owner, name
        FROM repos
        WHERE metadata_status IS NULL
           OR metadata_status IN ('error', 'rate_limited')
        ORDER BY total_events DESC
    """
    rows = con.execute(q).fetchall()
    con.close()

    if args.limit:
        rows = rows[: args.limit]

    batches = [rows[i:i + args.batch_repos] for i in range(0, len(rows), args.batch_repos)]
    print(f"Repos needing metadata: {len(rows):,}")
    print(f"GraphQL batches: {len(batches):,} ({args.batch_repos} repos/query)")
    if not batches:
        return

    token = get_github_token()
    sem = asyncio.Semaphore(args.workers)
    db_lock = asyncio.Lock()

    connector = aiohttp.TCPConnector(limit=max(args.workers * 2, 40))
    timeout = aiohttp.ClientTimeout(total=120)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        async def handle_batch(batch):
            query = build_metadata_query(batch)
            payload, headers = await gql_request(session, token, query, sem)

            async with db_lock:
                con = connect_db(db_path)
                if payload.get("errors") and not payload.get("data"):
                    for repo_name, _, _ in batch:
                        con.execute(
                            "UPDATE repos SET metadata_status=?, metadata_updated_at=? WHERE repo_name=?",
                            ("error", iso_now(), repo_name),
                        )
                else:
                    data = payload.get("data") or {}
                    for i, (repo_name, _, _) in enumerate(batch):
                        obj = data.get(f"r{i}")
                        if obj is None:
                            con.execute(
                                """
                                UPDATE repos
                                SET metadata_status=?, metadata_updated_at=?
                                WHERE repo_name=?
                                """,
                                ("not_found", iso_now(), repo_name),
                            )
                            continue

                        topics = []
                        for node in ((obj.get("repositoryTopics") or {}).get("nodes") or []):
                            topic = (node or {}).get("topic") or {}
                            if topic.get("name"):
                                topics.append(topic["name"])

                        default_branch = ((obj.get("defaultBranchRef") or {}).get("name"))
                        con.execute(
                            """
                            UPDATE repos
                            SET metadata_status='ok',
                                description=?,
                                topics_json=?,
                                default_branch=?,
                                is_fork=?,
                                is_archived=?,
                                metadata_updated_at=?
                            WHERE repo_name=?
                            """,
                            (
                                obj.get("description"),
                                json.dumps(topics, ensure_ascii=False),
                                default_branch,
                                int(bool(obj.get("isFork"))),
                                int(bool(obj.get("isArchived"))),
                                iso_now(),
                                repo_name,
                            ),
                        )
                con.commit()
                con.close()

        done = 0
        for start in range(0, len(batches), args.queue_batches):
            chunk = batches[start:start + args.queue_batches]
            await asyncio.gather(*(handle_batch(b) for b in chunk))
            done += len(chunk)
            print(f"metadata batches {done:,}/{len(batches):,}")


def stage_metadata(args: argparse.Namespace) -> None:
    asyncio.run(metadata_async(args))


README_RE = re.compile(r"^readme(?:\..+)?$", re.IGNORECASE)


@dataclass
class ReadmeResult:
    repo_name: str
    status: str
    sha: str | None = None
    path: str | None = None
    text: str | None = None
    error: str | None = None


def run_cmd(cmd: list[str], cwd: Path | None = None, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )


def extract_historical_readme(task: tuple[str, str, str, str], timeout: int, max_chars: int) -> ReadmeResult:
    repo_name, owner, name, target_date = task
    url = f"https://github.com/{owner}/{name}.git"

    try:
        with tempfile.TemporaryDirectory(prefix="thesis_repo_") as td:
            td_path = Path(td)
            repo_dir = td_path / "repo"

            clone_cmd = [
                "git", "clone",
                "--quiet",
                "--filter=blob:none",
                "--no-tags",
                "--single-branch",
                "--no-checkout",
                "--shallow-since=2024-01-01",
                url,
                str(repo_dir),
            ]
            p = run_cmd(clone_cmd, timeout=timeout)
            if p.returncode != 0:
                # Some repositories cannot satisfy shallow-since; retry current default branch depth 1.
                p2 = run_cmd(
                    [
                        "git", "clone", "--quiet",
                        "--filter=blob:none",
                        "--no-tags",
                        "--single-branch",
                        "--no-checkout",
                        "--depth=1",
                        url,
                        str(repo_dir),
                    ],
                    timeout=timeout,
                )
                if p2.returncode != 0:
                    return ReadmeResult(repo_name, "clone_error", error=(p2.stderr or p.stderr)[-1000:])

            target_iso = f"{target_date}T23:59:59Z"
            p = run_cmd(
                ["git", "rev-list", "-1", f"--before={target_iso}", "HEAD"],
                cwd=repo_dir,
                timeout=timeout,
            )
            sha = p.stdout.strip() if p.returncode == 0 else ""

            # Never silently use a future HEAD for the historical snapshot.
            if not sha:
                return ReadmeResult(repo_name, "no_commit_at_target")

            p = run_cmd(
                ["git", "ls-tree", "--name-only", sha],
                cwd=repo_dir,
                timeout=timeout,
            )
            if p.returncode != 0:
                return ReadmeResult(repo_name, "tree_error", sha=sha, error=p.stderr[-1000:])

            names = [x.strip() for x in p.stdout.splitlines() if x.strip()]
            readme = next((x for x in names if README_RE.match(Path(x).name)), None)
            if not readme:
                return ReadmeResult(repo_name, "no_root_readme", sha=sha)

            p = run_cmd(
                ["git", "show", f"{sha}:{readme}"],
                cwd=repo_dir,
                timeout=timeout,
            )
            if p.returncode != 0:
                return ReadmeResult(repo_name, "readme_error", sha=sha, path=readme, error=p.stderr[-1000:])

            text = p.stdout
            if len(text) > max_chars:
                text = text[:max_chars]

            return ReadmeResult(repo_name, "ok", sha=sha, path=readme, text=text)

    except subprocess.TimeoutExpired:
        return ReadmeResult(repo_name, "timeout")
    except Exception as e:
        return ReadmeResult(repo_name, "error", error=repr(e)[:1000])


def stage_readmes(args: argparse.Namespace) -> None:
    db_path = Path(args.db).expanduser()
    con = connect_db(db_path)
    rows = con.execute(
        """
        SELECT repo_name, owner, name, target_date
        FROM repos
        WHERE readme_status IS NULL
           OR readme_status IN ('timeout', 'clone_error', 'tree_error', 'readme_error', 'error')
        ORDER BY total_events DESC
        """
    ).fetchall()
    con.close()

    if args.limit:
        rows = rows[: args.limit]

    print(f"Repos needing README snapshot: {len(rows):,}")
    if not rows:
        return

    # ThreadPool is correct here: workers spend most of their time in git subprocess I/O.
    # Using 20 Python processes would only add overhead and does not make git transfers safer/faster.
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(extract_historical_readme, row, args.timeout, args.max_chars): row[0]
            for row in rows
        }

        con = connect_db(db_path)
        done = 0
        ok = 0

        for fut in cf.as_completed(futures):
            res = fut.result()
            done += 1

            blob = None
            chars = None
            digest = None
            if res.text is not None:
                raw = res.text.encode("utf-8", errors="replace")
                blob = sqlite3.Binary(zlib.compress(raw, level=6))
                chars = len(res.text)
                digest = hashlib.sha256(raw).hexdigest()
                ok += 1

            con.execute(
                """
                UPDATE repos
                SET readme_status=?,
                    readme_snapshot_sha=?,
                    readme_path=?,
                    readme_chars=?,
                    readme_sha256=?,
                    readme_zlib=?,
                    readme_updated_at=?
                WHERE repo_name=?
                """,
                (
                    res.status,
                    res.sha,
                    res.path,
                    chars,
                    digest,
                    blob,
                    iso_now(),
                    res.repo_name,
                ),
            )

            if done % 100 == 0:
                con.commit()
            if done % 500 == 0:
                print(f"README {done:,}/{len(rows):,} | ok {ok:,}")

        con.commit()
        con.close()

    print(f"README stage complete. OK: {ok:,}/{len(rows):,}")


def decompress_readme(blob: bytes | None) -> str | None:
    if blob is None:
        return None
    return zlib.decompress(blob).decode("utf-8", errors="replace")


def choose_device(requested: str | None):
    import torch

    if requested:
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def stage_classify(args: argparse.Namespace) -> None:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    try:
        from src.text_format import format_model_input
    except Exception as e:
        raise SystemExit(
            "Could not import src.text_format.format_model_input. "
            "Install alexanderquispe/naics-github-train with `pip install -e .` first."
        ) from e

    db_path = Path(args.db).expanduser()
    con = connect_db(db_path)

    rows = con.execute(
        """
        SELECT repo_name, name, description, topics_json, readme_zlib
        FROM repos
        WHERE prediction_status IS NULL
           OR prediction_status='error'
        ORDER BY total_events DESC
        """
    ).fetchall()

    if args.limit:
        rows = rows[: args.limit]

    print(f"Repos needing classification: {len(rows):,}")
    if not rows:
        con.close()
        return

    device = choose_device(args.device)
    print("Device:", device)
    print("Model:", MODEL_NAME)

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        local_files_only=args.local_files_only,
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        local_files_only=args.local_files_only,
    )
    model.eval()
    model.to(device)

    use_fp16 = (device in {"mps", "cuda"}) and not args.fp32
    if use_fp16:
        model.half()
        print("Precision: fp16")
    else:
        print("Precision: fp32")

    # The published model config maps classifier IDs to NAICS codes.
    id2label = {int(k): str(v) for k, v in model.config.id2label.items()}

    def make_text(row):
        repo_name, short_name, description, topics_json, blob = row
        try:
            topics = json.loads(topics_json) if topics_json else []
        except Exception:
            topics = []
        readme = decompress_readme(blob)

        # Main specification can exclude current description/topics to avoid post-2024
        # metadata leakage. Use --include-current-metadata only as a secondary specification.
        if not args.include_current_metadata:
            description = None
            topics = []

        return format_model_input(
            repo_name=short_name or repo_name.split("/", 1)[-1],
            description=description,
            topics=topics,
            readme=readme,
        )

    done = 0
    for start in range(0, len(rows), args.batch_size):
        batch = rows[start:start + args.batch_size]
        texts = [make_text(r) for r in batch]

        try:
            enc = tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            enc = {k: v.to(device) for k, v in enc.items()}

            with torch.inference_mode():
                logits = model(**enc).logits
                probs = torch.softmax(logits.float(), dim=-1)

            top2 = torch.topk(probs, k=2, dim=-1)
            values = top2.values.cpu().numpy()
            indices = top2.indices.cpu().numpy()

            for i, row in enumerate(batch):
                repo_name = row[0]
                c1 = id2label[int(indices[i, 0])]
                c2 = id2label[int(indices[i, 1])]
                s1 = float(values[i, 0])
                s2 = float(values[i, 1])

                con.execute(
                    """
                    UPDATE repos
                    SET prediction_status='ok',
                        naics_code=?,
                        sector=?,
                        score=?,
                        second_code=?,
                        second_score=?,
                        score_margin=?,
                        high_confidence=?,
                        model_name=?,
                        model_revision=?,
                        prediction_updated_at=?
                    WHERE repo_name=?
                    """,
                    (
                        c1,
                        NAICS_SECTORS.get(c1, c1),
                        s1,
                        c2,
                        s2,
                        s1 - s2,
                        int(s1 >= args.threshold),
                        MODEL_NAME,
                        getattr(model.config, "_commit_hash", None),
                        iso_now(),
                        repo_name,
                    ),
                )

        except Exception as e:
            for row in batch:
                con.execute(
                    """
                    UPDATE repos
                    SET prediction_status='error',
                        prediction_updated_at=?
                    WHERE repo_name=?
                    """,
                    (iso_now(), row[0]),
                )
            print("batch error:", repr(e)[:500])

        done += len(batch)
        if done % max(args.batch_size * 20, 1000) == 0:
            con.commit()
            print(f"classified {done:,}/{len(rows):,}")

    con.commit()
    con.close()
    print("Classification complete.")


def stage_export(args: argparse.Namespace) -> None:
    db_path = Path(args.db).expanduser()
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    con = connect_db(db_path)
    df = pd.read_sql_query(
        """
        SELECT
            repo_name, first_activity, last_activity, target_date,
            total_events, pre_events, shutdown_events, recovery_events,
            metadata_status, description, topics_json, default_branch,
            is_fork, is_archived,
            readme_status, readme_snapshot_sha, readme_path,
            readme_chars, readme_sha256,
            prediction_status, naics_code, sector, score,
            second_code, second_score, score_margin,
            high_confidence, model_name, model_revision
        FROM repos
        ORDER BY total_events DESC
        """,
        con,
    )
    con.close()

    df.to_parquet(out, index=False)
    csv_path = out.with_suffix(".csv")
    df.to_csv(csv_path, index=False)

    print(f"Exported {len(df):,} repos")
    print(out)
    print(csv_path)

    print("\nPrediction QA")
    print(df["prediction_status"].value_counts(dropna=False))
    if "score" in df:
        print("\nHigh confidence >= 0.8:", int((df["score"] >= 0.8).sum()))
        print("Share:", round(float((df["score"] >= 0.8).mean()), 4))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("prepare")
    a.add_argument("--events", required=True)
    a.add_argument("--db", required=True)
    a.set_defaults(func=stage_prepare)

    a = sub.add_parser("metadata")
    a.add_argument("--db", required=True)
    a.add_argument("--workers", type=int, default=20)
    a.add_argument("--batch-repos", type=int, default=20)
    a.add_argument("--queue-batches", type=int, default=100)
    a.add_argument("--limit", type=int)
    a.set_defaults(func=stage_metadata)

    a = sub.add_parser("readmes")
    a.add_argument("--db", required=True)
    a.add_argument("--workers", type=int, default=20)
    a.add_argument("--timeout", type=int, default=180)
    a.add_argument("--max-chars", type=int, default=200_000)
    a.add_argument("--limit", type=int)
    a.set_defaults(func=stage_readmes)

    a = sub.add_parser("classify")
    a.add_argument("--db", required=True)
    a.add_argument("--device", choices=["mps", "cuda", "cpu"])
    a.add_argument("--batch-size", type=int, default=32)
    a.add_argument("--threshold", type=float, default=0.80)
    a.add_argument("--fp32", action="store_true")
    a.add_argument("--local-files-only", action="store_true")
    a.add_argument("--include-current-metadata", action="store_true")
    a.add_argument("--limit", type=int)
    a.set_defaults(func=stage_classify)

    a = sub.add_parser("export")
    a.add_argument("--db", required=True)
    a.add_argument("--out", required=True)
    a.set_defaults(func=stage_export)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
