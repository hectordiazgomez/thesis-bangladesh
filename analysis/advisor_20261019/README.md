# Advisor revision analysis, 19 October 2026

This extension preserves the original 15-country eligible sample, national
SCM specification, July 18-23 treatment dates and archived empirical outputs.
New results are written to `results/advisor_20261019/`. The original manuscript
and notes are preserved under `archive/advisor_20261019_before/`.

## Reproduction

Use the repository's `.venv-sector/bin/python` (Python 3.14 in this run). The
additional requirements are `google-cloud-bigquery`, `google-auth`, `requests`,
`python-dotenv` and `pymupdf`; the original sector requirements supply torch,
transformers, pandas and pyarrow. `db-dtypes` registers the archived date type.
All model inference uses the pinned revision recorded in `analysis_design.json`.
`requirements_advisor.txt` records the package versions used. The unmodified
MIT-licensed formatter is preserved as `text_format_snapshot.py` with its license.
For a fresh machine, download the model once with
`huggingface_hub.snapshot_download('aquiro1994/naics-github-classifier-multilingual', revision='e40747e90bbc547e56b7145d2b97494bff69b42d')`.

1. `python analysis/advisor_20261019/retrieve_international.py` retrieves the
   unchanged eligible sample's repository-day-event-type history from GH Archive.
   It uses existing Application Default Credentials, project `olah-aac6b`, and a
   30 GB maximum-bytes-billed cap. A pre-existing local extract is reused. The
   job metadata and SQL are retained; no cloud source tables are changed.
2. `python analysis/advisor_20261019/sector_classify.py prepare` fixes each user's
   dominant repository using pre-treatment activity only. It can reconstruct
   membership directly from the downloaded panel.
3. `python analysis/advisor_20261019/sector_classify.py fetch` retrieves historical
   root READMEs into a separate SQLite cache. Authentication uses `GH_TOKEN` or
   the user-authorized `.env` in `Documents/retrieve-info`. No token is logged.
   Completed rows resume; query errors can be retried. No clone or file deletion
   is used. Historical text unavailable today is recorded explicitly. Empty
   README files are excluded from the main assignment.
4. `python analysis/advisor_20261019/sector_classify.py stream` runs a single
   resident classifier and can overlap network retrieval. It batches similar
   input sizes, preserving the same 512-token truncation and model. The model
   formatter was copied unchanged from `tools/naics-github-train`; its exact
   hash is recorded. Retrieval errors must be resolved/retried before
   estimation; missing public repositories remain explicitly unavailable.
   After retrieval, `sector_classify.py finish` completes pending rows using
   exact token-length batches to reduce padding and memory use; it preserves
   the same text, model, 512-token limit and floating-point precision.
5. `python analysis/advisor_20261019/account_metadata.py` retrieves only account
   creation dates for Bangladesh users. It does not retrieve private data,
   profile biographies, contact details or organizational affiliations.
6. `python analysis/advisor_20261019/supporting_analysis.py` reproduces national
   lag diagnostics and residual-user cohort comparisons.
7. `python analysis/advisor_20261019/validate_and_characterize.py` verifies the
   recovered event map and calculates historical account-age summaries. Current
   account creation dates that conflict with observed 2024 activity are excluded.
8. `python analysis/advisor_20261019/sector_estimation.py` fits all supported
   country-domain controls, country placebos, leave-one-out estimates and
   classifier-threshold sensitivities. It stops if classification is incomplete.
9. `python analysis/advisor_20261019/make_supporting_tables.py` and
   `python analysis/advisor_20261019/make_sector_report.py` regenerate the new
   tables, figures and sector results text.
10. Run `latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex` inside
    `paper/latex/`, then visually inspect the rebuilt PDF.

## Interpretation and design

The primary activity basket is now recovered from the original query history:
PushEvent, PullRequestEvent, PullRequestReviewEvent,
PullRequestReviewCommentEvent, IssuesEvent, ReleaseEvent and CreateEvent.
The re-extraction reproduces all 799,417 overlapping eligible user-day counts.
The 1,571 additional historical account exclusions remain unresolved.

The international sector analysis partitions users by their most active
pre-treatment repository, not by employer. Ties use event counts and lexical
repository order. Main assignment requires historical README text and score
at least 0.80; other users remain unclassified. At least 30 Bangladesh users,
30 users per donor group and five donor countries are required. All supported
groups are reported, regardless of estimated effect or pre-fit. The observed
national numerator is an exact sum across the partition; sector-specific
counterfactuals need not sum to the national SCM because their weights differ.

July 19-22 publication, July 18 at 15:00 UTC onward commit authorship, and
delayed publication from July 24 are separate, overlapping cohorts. Authored
timestamps are metadata, and eventual publication is censored at August 10.
Pre-activity and account-age comparisons are descriptive, not causal.

## Source provenance

`upstream_queries/` retains relevant original SQL obtained from the project's
BigQuery job history. `57c0227d-1da7-4f7a-930e-a44a40a53c37.sql` supplies the
recovered primary event map. These historical queries are evidence; reproducing
the new analyses does not require rerunning all of them.

Literature additions were checked against publisher/author sources, including
the AEA pages for Hjort and Poulsen (2019), Allcott et al. (2016), and Zhang and
Zhu (2011); NBER for Akerman et al. (2015) and McDermott and Hansen (2021);
arXiv version 2403.01964v2 for Kreitmeir and Raschky; and the publisher DOI
10.3982/QE1596 for Ferman and Pinto (2021). Repository-domain interpretation is
checked against the classifier's published model card, not inferred from its
confidence score.

The historical snapshot follows the currently available default branch backward to
the cutoff. It does not reconstruct historical branch-default settings. This is
a documented retrieval limitation, not a claim of perfect historical coverage.

## Legacy-cache repair

A status flag in the old replication cache did not imply source-text availability.
All 4,840 seeded records marked `ok` contained empty cached bytes; the initial
comparison therefore had an artificial Bangladesh coverage deficit. The first
pass is preserved separately, and all 7,133 seeded legacy records were freshly
retrieved and reclassified. `cache_seed_audit.parquet` preserves their former
state. Preparation now reuses only demonstrably nonempty cached text. Never
substitute a prior status flag for the underlying README.

## Final results and validation

The repaired historical-text extract has 35,160 nonempty READMEs; every selected
repository was freshly attempted through the same GitHub API procedure. The main
rule assigns 2,163 Bangladesh users (21.12%). Eight named domains with 1,822 users
meet the support rule; their July 18-23 gaps range from -11.31 to -16.84 pp.
All donor-omission estimates remain negative. These comparisons do not establish
a statistically significant ranking or identify employment industries.

`python analysis/advisor_20261019/verify_revision.py` passes 29 checks. It includes
an independent constrained-optimizer comparison and verifies that every successful
historical README has nonempty source bytes. Final output packaging follows PDF
compilation and visual review, using `package_revision.py`.
