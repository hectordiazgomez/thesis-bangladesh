#!/usr/bin/env python3
"""
Direct streaming pipeline:
20 concurrent temporary git fetches -> historical README in RAM -> ONE BERT model -> SQLite.
No GitHub metadata stage. No repository is kept on disk. README text is not persisted.
"""

from __future__ import annotations
import argparse, concurrent.futures as cf, datetime as dt, hashlib, json, os, re, shutil, sqlite3, subprocess, tempfile, time
from pathlib import Path

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

README_RE = re.compile(r"^readme(?:\..+)?$", re.I)

def connect(db):
    con = sqlite3.connect(db, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    return con

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def run(cmd, cwd=None, timeout=180):
    return subprocess.run(
        cmd, cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=timeout
    )

def fetch_one(task, timeout=180, max_chars=200_000):
    repo_name, owner, name, target_date = task
    url = f"https://github.com/{owner}/{name}.git"
    result = {
        "repo_name": repo_name, "status": None, "sha": None,
        "readme_path": None, "text": None, "error": None
    }
    try:
        with tempfile.TemporaryDirectory(prefix="thesis_repo_") as td:
            repo_dir = Path(td) / "repo"

            # Fetch only recent history/tree metadata first; blobs are fetched lazily by git show.
            p = run([
                "git","clone","--quiet",
                "--filter=blob:none","--no-tags","--single-branch",
                "--no-checkout","--shallow-since=2024-01-01",
                url, str(repo_dir)
            ], timeout=timeout)

            if p.returncode != 0:
                result["status"] = "clone_error"
                result["error"] = (p.stderr or "")[-500:]
                return result

            target_iso = f"{target_date}T23:59:59Z"
            p = run(["git","rev-list","-1",f"--before={target_iso}","HEAD"], cwd=repo_dir, timeout=timeout)
            sha = p.stdout.strip() if p.returncode == 0 else ""
            if not sha:
                result["status"] = "no_commit_at_target"
                return result

            result["sha"] = sha

            p = run(["git","ls-tree","--name-only",sha], cwd=repo_dir, timeout=timeout)
            if p.returncode != 0:
                result["status"] = "tree_error"
                result["error"] = (p.stderr or "")[-500:]
                return result

            names = [x.strip() for x in p.stdout.splitlines() if x.strip()]
            readme = next((x for x in names if README_RE.match(Path(x).name)), None)

            if not readme:
                result["status"] = "no_root_readme"
                return result

            p = run(["git","show",f"{sha}:{readme}"], cwd=repo_dir, timeout=timeout)
            if p.returncode != 0:
                result["status"] = "readme_error"
                result["error"] = (p.stderr or "")[-500:]
                return result

            text = p.stdout[:max_chars]
            result["status"] = "ok"
            result["readme_path"] = readme
            result["text"] = text
            return result

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        return result
    except Exception as e:
        result["status"] = "error"
        result["error"] = repr(e)[:500]
        return result

def device_auto(requested):
    import torch
    if requested:
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--device", choices=["mps","cuda","cpu"])
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--max-chars", type=int, default=200_000)
    ap.add_argument("--threshold", type=float, default=0.80)
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    try:
        from src.text_format import format_model_input
    except Exception as e:
        raise SystemExit(
            "No puedo importar src.text_format. Activa .venv-sector y asegúrate de haber hecho "
            "`pip install -e tools/naics-github-train`."
        ) from e

    db = Path(args.db).expanduser()
    con = connect(db)
    rows = con.execute("""
        SELECT repo_name, owner, name, target_date
        FROM repos
        WHERE prediction_status IS NULL OR prediction_status='error'
        ORDER BY total_events DESC
    """).fetchall()
    con.close()
    if args.limit:
        rows = rows[:args.limit]

    print(f"Repos pendientes: {len(rows):,}")
    print(f"Download workers: {args.workers}")
    print("Cargando BERT una sola vez...")

    device = device_auto(args.device)
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval().to(device)
    if device in {"mps","cuda"}:
        model.half()
    id2label = {int(k): str(v) for k,v in model.config.id2label.items()}
    print("Device:", device)

    def classify_batch(batch_results):
        texts = []
        for r in batch_results:
            short_name = r["repo_name"].split("/",1)[-1]
            texts.append(format_model_input(
                repo_name=short_name,
                description=None,
                topics=[],
                readme=r["text"]
            ))
        enc = tok(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
        enc = {k:v.to(device) for k,v in enc.items()}
        with torch.inference_mode():
            probs = torch.softmax(model(**enc).logits.float(), dim=-1)
        top2 = torch.topk(probs, k=2, dim=-1)
        vals = top2.values.cpu().numpy()
        idxs = top2.indices.cpu().numpy()
        return vals, idxs

    # Keep a bounded number of clone tasks in flight; classify completed items in batches.
    max_inflight = max(args.workers * 2, 40)
    iterator = iter(rows)
    futures = {}
    buffer = []
    processed = 0
    readme_ok = 0
    t0 = time.time()

    def submit_next(ex):
        try:
            row = next(iterator)
        except StopIteration:
            return False
        fut = ex.submit(fetch_one, row, args.timeout, args.max_chars)
        futures[fut] = row[0]
        return True

    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for _ in range(min(max_inflight, len(rows))):
            if not submit_next(ex):
                break

        while futures:
            done, _ = cf.wait(futures, return_when=cf.FIRST_COMPLETED)
            for fut in done:
                futures.pop(fut, None)
                r = fut.result()
                buffer.append(r)
                submit_next(ex)

            while len(buffer) >= args.batch_size or (not futures and buffer):
                batch = buffer[:args.batch_size]
                del buffer[:args.batch_size]

                vals, idxs = classify_batch(batch)
                con = connect(db)

                for i, r in enumerate(batch):
                    c1 = id2label[int(idxs[i,0])]
                    c2 = id2label[int(idxs[i,1])]
                    s1 = float(vals[i,0]); s2 = float(vals[i,1])
                    raw = (r["text"] or "").encode("utf-8", errors="replace")
                    if r["status"] == "ok":
                        readme_ok += 1

                    con.execute("""
                        UPDATE repos
                        SET readme_status=?,
                            readme_snapshot_sha=?,
                            readme_path=?,
                            readme_chars=?,
                            readme_sha256=?,
                            readme_zlib=NULL,
                            readme_updated_at=?,
                            prediction_status='ok',
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
                    """, (
                        r["status"], r["sha"], r["readme_path"],
                        len(r["text"] or "") if r["text"] is not None else None,
                        hashlib.sha256(raw).hexdigest() if raw else None,
                        now(),
                        c1, NAICS_SECTORS.get(c1,c1), s1,
                        c2, s2, s1-s2, int(s1 >= args.threshold),
                        MODEL_NAME, getattr(model.config, "_commit_hash", None),
                        now(), r["repo_name"]
                    ))
                    processed += 1

                con.commit()
                con.close()

                if processed % 500 < args.batch_size:
                    elapsed = max(time.time() - t0, 1)
                    rate = processed / elapsed
                    remaining = len(rows) - processed
                    eta_h = remaining / rate / 3600 if rate > 0 else float("nan")
                    print(
                        f"processed {processed:,}/{len(rows):,} | "
                        f"README ok {readme_ok:,} | "
                        f"{rate:.2f} repos/s | ETA {eta_h:.1f} h",
                        flush=True
                    )

    print("DONE")
    print("Processed:", processed)
    print("README ok:", readme_ok)

if __name__ == "__main__":
    main()
