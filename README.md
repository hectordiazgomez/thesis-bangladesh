# Bangladesh Internet Shutdown and Software-Development Activity

## Thesis project

**Internet Shutdowns and Software Development:  
Evidence from Bangladesh**

Author: Hector Alberto Diaz Gomez

This repository contains the manuscript, processed data, empirical results,
robustness checks, and mechanism analysis for my economics thesis.

## Current manuscript

The current manuscript is `paper/latex/main.tex` and its included sections,
with the review PDF at `paper/latex/thesis.pdf`.
`paper/thesis.docx` and `paper/thesis.txt` are **obsolete historical drafts**,
retained for provenance only. They are not synchronized and must not be used
as the current thesis or as an input to revisions.

Install main-analysis dependencies with Python 3.14:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/materialize_sector_inputs.py
.venv/bin/python analysis/tables/make_all_tables.py
.venv/bin/python analysis/figures/make_all_figures.py
cd paper/latex
latexmk -xelatex main.tex
```

XeLaTeX, latexmk and the LaTeX packages used by main.tex are separate system
requirements. The output is thesis.pdf. Downstream analyses use versioned
inputs; full upstream replication remains incomplete (see
`archive/upstream_local/README.md`, `notes/round2_R2.md`, and the round-2
clean-clone audit). Versioned snapshots in `data/replication/sector/` permit downstream sector rebuilding
after materialization; original ignored files are never replaced. README retrieval and
classification from scratch still require external services. `db-dtypes` registers
the historical BigQuery date extension; import `db_dtypes` before reading
those historical files directly. Heavy sector dependencies are in
`requirements_sector.txt`.

Round-2 diagnostics write only new files under `results/diagnostics/round2/`.
They do not replace the headline specification. `notes/advisor_decisions_round2.md`
records pending methodological decisions. Stage new versioned files, then run
`python scripts/update_manifest.py`: `manifest.csv` lists every versioned file
and retains known export provenance; a blank original_path means unknown or
repository-created provenance, not an invented Google Drive location. The manifest's own byte-size fields are blank to avoid circular self-sizing.

## Main empirical design

The primary empirical design is Synthetic Control.

The main outcome is observable productive GitHub activity among accounts
associated with Bangladesh.

Headline Synthetic Control result:

- Bangladesh during treatment: approximately 2.02%
- Synthetic counterfactual: approximately 15.28%
- ATT: approximately -13.26 percentage points
- Relative change: approximately -86.8%

The repository also contains:

- international Difference-in-Differences
- event-study diagnostics
- Regression Discontinuity in Time robustness
- secondary outcome analyses
- commit author-time versus push-time mechanism analysis
- within-Bangladesh sectoral recovery analysis (descriptive; see below)
- synthetic-control placebo tests
- leave-one-donor-out robustness checks

## Repository structure

`paper/`
Current thesis manuscript.

`results/final/`
Consolidated final result tables used for manuscript verification.

`results/synthetic_control/`
Synthetic-control, placebo, donor-weight, DiD, and related outputs.
The canonical synthetic control now reproduces exactly from the stored
country-day panel: `analysis/synthetic_control/01_reproduce_sc.py` refits the
weights and stops unless the archived weights, ATT (-13.2559 pp), relative
effect, RMSPEs, in-space placebos and leave-one-out estimates are reproduced.
In-time placebos (`03_intime_placebos.py`) and a check of the archived SDID
estimate (`02_sdid_archived_check.py`) write to `reproduced/`.
`04_secondary_outcomes_eligible.py` rebuilds the secondary outcomes with
eligible users in numerator and denominator (referee comment R1) and writes
`country_day_outcomes_eligible.parquet` and `results/final/*_eligible.csv`;
the archived secondary-outcome files are kept unchanged for comparison.

`results/mechanism/`
Commit-timing and push-timing mechanism results and robustness checks.

`results/sector_recovery/`
Sectoral recovery outputs; `final/` holds the advisor-ready tables and
threshold-robustness files used in the manuscript.

`results/did/`
Aggregate international DiD event study and in-space placebo inference,
computed by `analysis/did/01_aggregate_did_eventstudy.py` from the stored
country-day panel (reproduces the archived DiD ATT exactly).

`results/rdit/`
Archived preferred RDiT result and documentation. The archived estimates are
reproduced exactly by `analysis/rdit/01_reproduce_rdit.py`, which also writes
the daily series plotted in the manuscript (`rdit_daily_series.csv`).

`data/processed/`
Processed datasets used in the empirical analysis.

`data/users/`
GitHub user-location inputs.

`other/`
Figures from earlier stages of the analysis.

`notes/`
Advisor feedback and revision log.

`analysis/`
Reserved for analysis and replication code. This directory is currently
incomplete and the repository should not yet be interpreted as a complete
one-command replication package.

`references/`
Reserved for supporting literature files. Bibliographic references are
currently contained in the manuscript itself.

`manifest.csv`
Maps files exported from the original Google Drive research directory to
their organized repository locations.

## Sectoral recovery extension

A within-Bangladesh analysis traces observable PushEvent activity after
connectivity returned, by the NAICS sector of the repositories in which
activity occurs (historical-README classifier, confidence >= 0.80), for a
fixed sample of 20,000 accounts selected on pre-shutdown activity. It
describes heterogeneity in recovery relative to each sector's own
pre-shutdown baseline; it is not a sector-specific causal estimate and does
not replace the synthetic-control headline result. Pipeline:
`README_sector_pipeline.md` and `analysis/sector_recovery/`.

The LaTeX manuscript (`paper/latex/`, compiled to `paper/latex/thesis.pdf`)
includes this extension; `paper/thesis.docx` and `paper/thesis.txt` do not.
Figures and tables are regenerated with `analysis/figures/make_all_figures.py`
and `analysis/tables/make_all_tables.py`.

## Interpretation

The empirical outcomes measure observable public GitHub activity rather
than total software productivity.

GitHub profile location is self-reported, and private repositories and
non-GitHub software-development work are not observed.

The main shutdown episode also coincided with broader domestic disruption,
which is discussed explicitly as an identification limitation in the thesis.

## Revision status

The repository is under active thesis development.

Empirical result files should be treated as fixed research outputs unless a
new analysis is explicitly documented.

Manuscript revisions are tracked through Git commits.

## Contact

Hector Alberto Diaz Gomez
