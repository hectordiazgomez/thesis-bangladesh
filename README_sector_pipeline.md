# Local repo sector pipeline

## Inputs from Google Drive

Download these files into:

`~/Documents/thesis-bangladesh/data/sector_recovery/`

- `bangladesh_preactive_sample_20000.parquet`
- `bd_preactive20000_repo_event_day_metadata.parquet`
- `bd_preactive20000_repo_universe.parquet`

The pipeline uses the event-day file as its source of truth for repo names and timing.

## Why it does not keep full repositories

There are about 168,875 unique `repo_name` values in the final event panel.
Keeping full clones is unnecessary for this classifier and can consume huge disk space.

The `readmes` stage uses temporary filtered clones:
- 20 concurrent I/O workers by default;
- extracts only a root README snapshot at the relevant historical date;
- immediately deletes the temporary clone;
- stores the README compressed in SQLite.

The BERT model is loaded ONCE and run in batches. Do not run 20 model processes.

## Setup on macOS

```bash
cd ~/Documents/thesis-bangladesh

mkdir -p analysis/sector_recovery data/sector_recovery results/sector_recovery tools

python3 -m venv .venv-sector
source .venv-sector/bin/activate

pip install -r requirements_sector.txt

git clone https://github.com/alexanderquispe/naics-github-train.git tools/naics-github-train
pip install -e tools/naics-github-train
```

GitHub authentication:

```bash
gh auth status
```

The script uses `gh auth token` automatically. Do not print or hard-code the token.

## 1. Prepare canonical repo tasks

This deliberately deduplicates by `repo_name`, because the pre-period files did not preserve `repo_id`
while the post-period files did. That is why the earlier repo-universe table showed more rows than
unique repo names.

```bash
python analysis/sector_recovery/repo_sector_pipeline.py prepare \
  --events data/sector_recovery/bd_preactive20000_repo_event_day_metadata.parquet \
  --db data/sector_recovery/repo_sector.sqlite
```

## 2. Fetch GitHub metadata (optional but useful)

20 concurrent network workers, 20 repositories per GraphQL query:

```bash
python analysis/sector_recovery/repo_sector_pipeline.py metadata \
  --db data/sector_recovery/repo_sector.sqlite \
  --workers 20 \
  --batch-repos 20
```

If GitHub returns secondary-rate-limit errors, rerun with `--workers 5`. The stage resumes.

## 3. Historical README snapshots

First test 200 repositories:

```bash
python analysis/sector_recovery/repo_sector_pipeline.py readmes \
  --db data/sector_recovery/repo_sector.sqlite \
  --workers 20 \
  --limit 200
```

If QA looks good, continue without `--limit`:

```bash
python analysis/sector_recovery/repo_sector_pipeline.py readmes \
  --db data/sector_recovery/repo_sector.sqlite \
  --workers 20
```

Each repository is a temporary clone and is deleted immediately.

For repos observed pre-shutdown, the target snapshot date is 2024-07-17.
For repos first observed after the shutdown, the target is their first observed activity date.

## 4. Model test

Download/cache the model and classify 500 repos:

```bash
python analysis/sector_recovery/repo_sector_pipeline.py classify \
  --db data/sector_recovery/repo_sector.sqlite \
  --device mps \
  --batch-size 32 \
  --limit 500
```

Then classify the rest:

```bash
python analysis/sector_recovery/repo_sector_pipeline.py classify \
  --db data/sector_recovery/repo_sector.sqlite \
  --device mps \
  --batch-size 32
```

Main specification intentionally uses repo name + historical README only.
Current GitHub description/topics are omitted to avoid post-2024 metadata leakage.

A secondary specification can include them:

```bash
python analysis/sector_recovery/repo_sector_pipeline.py classify \
  --db data/sector_recovery/repo_sector.sqlite \
  --device mps \
  --batch-size 32 \
  --include-current-metadata
```

Do not overwrite the main classification when doing the secondary specification; copy the DB first.

## 5. Export

```bash
python analysis/sector_recovery/repo_sector_pipeline.py export \
  --db data/sector_recovery/repo_sector.sqlite \
  --out results/sector_recovery/repo_naics_predictions.parquet
```
