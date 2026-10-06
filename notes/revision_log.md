# Revision Log


## 2026-10-05 — LaTeX conversion and reproducible figures

- Advisor comment addressed: none (format conversion requested by author; no advisor comments recorded yet).
- Files created:
  - `paper/latex/` (`main.tex`, `references.bib`, `.latexmkrc`, `sections/*.tex`,
    `tables/*.tex`, `figures/*.pdf`, `thesis.pdf`)
  - `analysis/figures/make_all_figures.py` (Figures 1-3)
  - `analysis/tables/make_all_tables.py` (Tables 3-5 and A1-A10)
- Sections changed: none in substance. Text transferred from `paper/thesis.txt`;
  only LaTeX syntax, cross-references to new figures/tables, and figure captions added.
- Additions relative to `paper/thesis.txt`:
  - Three figures (actual vs synthetic; placebo RMSPE ratios; mechanism release
    timing).
  - Appendix tables not in the DOCX/TXT: full SC placebo ranking (A3),
    outcome-specific donor weights (A4), RDiT preferred specification (A5),
    push-listing completeness (A8), push-size robustness (A9), backlog
    concentration (A10). All numbers already appeared in the text or in
    `results/`.
  - RMSPE-ratio placebo-rank column added to the secondary-outcomes table
    (value already reported in Section 6.3).
- Empirical numbers changed: none. All table values are read from `results/`;
  the parametric p = 0.0 in `results/synthetic_control/main_synthetic_results.csv`
  is not reported.
- `paper/thesis.txt` and `paper/thesis.docx` were not modified.

## 2026-10-05 — Cleanup pass before advisor review

- Files changed: `paper/latex/sections/05_empirical_strategy.tex`,
  `paper/latex/sections/06_results.tex`, `analysis/figures/make_all_figures.py`,
  `paper/latex/figures/` (event-study PDF removed), `paper/latex/thesis.pdf`.
- Removed the daily event-study figure: the stored coefficients
  (`data/processed/fig1_daily_zoom.csv`) are not sufficiently documented or
  reproducible. Underlying files were kept. The manuscript sentence on the
  event study is unchanged; only its figure cross-reference was removed.
- Section 6.1: "both countries" -> "both Pakistan and Kenya" (grammatical
  clarification; no change to results or interpretation).
- Added source-only TODO comments (not printed) next to the RDiT
  sensitivity/donut statements (Sections 5.3 and 6.2) and the Pakistan citation
  (Section 6.1).
- Empirical numbers changed: none.

## 2026-10-05 — Advisor-facing cleanup (wording and appendix layout)

- Files changed: `paper/latex/main.tex` (abstract), `paper/latex/sections/01_introduction.tex`,
  `paper/latex/sections/02_background.tex`, `paper/latex/sections/06_results.tex`,
  `paper/latex/sections/10_conclusion.tex`, `analysis/tables/make_all_tables.py`,
  `paper/latex/tables/*.tex` (appendix placement only), `paper/latex/thesis.pdf`.
- Visible "[CITATION NEEDS VERIFICATION]" (Section 2.1) replaced by a non-printing TODO.
- Event study: introduction sentence removed; Section 6.2 paragraph replaced by a
  cautious sentence stating the archived implementation is not fully documented.
- RDiT: donut-sensitivity sentence removed (Section 6.2); preferred estimate unchanged.
- Abstract and conclusion mechanism sentences reworded to "consistent with" /
  "suggest ... within the strict public-commit sample" language.
- Pakistan citation TODO comment reworded; source unchanged.
- Appendix tables placed with [H]; Table A1 widened (tabular*) so notes are readable.
- Note: `paper/thesis.txt` and `paper/thesis.docx` do not yet reflect these wording changes.
- Empirical numbers changed: none.

## 2026-10-06 — Sectoral recovery extension integrated into the LaTeX manuscript

- Advisor comment addressed: none recorded (`notes/advisor_feedback.md` is empty);
  extension requested by the author.
- New empirical content (no existing estimate changed): within-Bangladesh
  sectoral recovery analysis from `results/sector_recovery/` (scripts
  `analysis/sector_recovery/06`-`10`). Main specification: fixed sample of 20,000
  Bangladesh-associated accounts, historical-README NAICS classifier with
  confidence >= 0.80, 8-week pre-shutdown baseline (May 23-Jul 17, 2024).
- Files changed:
  - `paper/latex/main.tex` (one abstract sentence)
  - `paper/latex/sections/01_introduction.tex` (new paragraph)
  - `paper/latex/sections/04_data.tex` (new Section 4.4)
  - `paper/latex/sections/05_empirical_strategy.tex` (new Section 5.5, Eq. 3)
  - `paper/latex/sections/06_results.tex` (new Section 6.4; one sentence added to
    the event-study paragraph in Section 6.2)
  - `paper/latex/sections/08_robustness.tex` (new Section 8.3)
  - `paper/latex/sections/09_discussion.tex` (new paragraph)
  - `paper/latex/sections/10_conclusion.tex` (new paragraph)
  - `paper/latex/sections/appendix.tex` (new Appendix A.4)
  - `analysis/figures/make_all_figures.py` (Figures `fig5_sector_recovery_index`,
    `fig6_sector_eventstudy`; plotted values checked against
    `results/sector_recovery/final/table_sector_recovery_main.csv`)
  - `analysis/tables/make_all_tables.py` (tables `tab_sector_recovery`,
    `tab_sector_threshold`, `tab_sector_fixed_repo`)
  - `paper/latex/figures/fig5_*.pdf`, `fig6_*.pdf`; `paper/latex/tables/tab_sector_*.tex`;
    `paper/latex/thesis.pdf`; `README.md`
- Main-text numbering shifts: new Table 5 and Figures 3-4; former Table 5 and
  Figure 3 (mechanism) become Table 6 and Figure 5; new appendix tables A11-A12.
- Empirical numbers changed: none. Synthetic control, DiD, RDiT, and mechanism
  text and tables untouched. The RDiT sensitivity file was not used.
- Flags:
  - "First week >= 80, 2 wks" is the first week beginning two consecutive weeks
    with index >= 80; several sectors later fall below 80 again (e.g., Real Estate
    31.9-46.7 from week +12), so the manuscript does not call it "sustained recovery".
  - Accommodation/Food has an unstable baseline (week -8 index 254.1); disclosed.
  - Sample-selection script for the 20,000-account sample is not in the
    repository, and bot filtering is undocumented (non-printing TODO in Section 4.4).
  - Classifier reference marked [CITATION NEEDED].
  - Repository coverage counts (168,875 repos; 92,979 with README; 32,491 with
    score >= 0.80) are read from `data/sector_recovery/repo_sector.sqlite`.
- `paper/thesis.txt` and `paper/thesis.docx` were not modified and do not contain
  the sectoral extension.

## 2026-10-06 — Empirical presentation: figure + table for every design

- Advisor comment addressed: none recorded; requested by the author.
- New analysis code and outputs (no archived estimate changed):
  - `analysis/did/01_aggregate_did_eventstudy.py` -> `results/did/`
    (`did_main_placebo_inference.csv`, `did_eventstudy_weekly.csv`,
    `did_pre_period_volatility.csv`). Aggregate DiD and weekly event study from
    `results/synthetic_control/country_day_donor_pool_with_holidays.parquet`;
    the script stops unless the DiD reproduces `results/final/table_DiD_all_outcomes.csv`
    (-13.0875 / -13.3791; reproduced exactly).
  - New numbers reported (in-space placebo inference for the DiD and event study):
    placebo SD 1.17 / 1.19 pp, placebo ATT range -1.72 to 1.60 pp, rank 0.0667;
    weekly event-study coefficients -4.89 to 6.10 pp before the shutdown;
    Bangladesh pre-period weekly SD 3.04 pp vs 0.70-2.18 pp for donors.
  - `results/rdit/figure_rdit_fitted_jumps.csv` (visual-guide fits for the RDiT figure).
- Figures added (`analysis/figures/make_all_figures.py`): `fig3_did_eventstudy.pdf`
  (Figure 3, Section 6.2), `fig7_rdit_cutoff.pdf` (Figure 4, Section 6.3).
- Tables added (`analysis/tables/make_all_tables.py`): `tab_sc_main` (Table 4,
  Section 6.1), `tab_did` (Table 5, Section 6.2), `tab_did_eventstudy_full`
  (Table A4), `tab_did_secondary` (Table A5).
- Tables moved: `tab_rdit` appendix -> Section 6.3 (Table 6); `tab_leave_one_out`
  appendix -> Section 8.1 (Table 10); `tab_main_estimates` moved to the start of
  Section 6 and retitled "Summary of estimates across designs".
- Text: Section 5.2 rewritten with Eqs. (2)-(3) (aggregate DiD and event study,
  placebo inference); original Eq. (4) user-day equation kept. Section 5.3: RDiT
  Eq. (5) added; sentence claiming bandwidth/polynomial/donut/placebo-cutoff
  sensitivity replaced by a statement that those results are not reported.
  Section 6 restructured into 6.1 SC, 6.2 DiD/event study, 6.3 RDiT. Cross-references
  added in Sections 8, 9, 10.
- Flags:
  - Archived RDiT estimate (-0.092836, SE 0.050344) cannot be reproduced exactly from
    stored files (closest: -0.0899 on the SC country-day panel; -0.0925 on
    `data/processed/panel_clean.parquet`). Table reports archived values; figure
    caption discloses the plotted fit (-8.99 pp).
  - Assignment of July 17 (t = 0) to the post-cutoff side is inferred from the
    archived README (N = 15, bandwidth 7) and the reproduction; TODO added.
  - Archived event-study coefficients (`data/processed/fig1_daily_zoom.csv`,
    `fig2_event_study_weekly.csv`) and `other/fig3_rdit.png` remain unused
    (undocumented specifications; the RDiT figure uses a residualized donut series).
- `paper/thesis.txt` and `paper/thesis.docx` not modified.

## 2026-10-06 — Methodological consistency pass (DiD/event study, RDiT)

- Advisor comment addressed: none recorded; requested by the author.
- RDiT reproduced exactly. `analysis/rdit/01_reproduce_rdit.py` recovers the archived
  preferred design and asserts all three rows of `results/rdit/main_rdit_summary.csv`
  (effect, HAC SE, CI, p, Durbin-Watson) to six decimals: series = daily share of users
  with productive_events > 0 in `data/processed/panel_user_day_{bangladesh,philippines}.parquet`
  (balanced panels: 10,329 BD and 3,025 PH accounts); window July 10-24; D = 1{date >= July 17}
  (July 17 on the post-cutoff side); local linear; Newey-West HAC, 2 lags, small-sample
  factor n/(n-k). Main estimate -0.092836 reproduced.
  - New output: `results/rdit/rdit_daily_series.csv`. Removed the earlier untracked
    `results/rdit/figure_rdit_fitted_jumps.csv` (plotted an alternative -8.99 pp jump).
  - `fig7_rdit_cutoff.pdf` rebuilt on the reproduced series; its fitted discontinuity is
    asserted equal to the archived estimate. No alternative RDiT number appears in the paper.
- Unresolved, documented here only: `data/processed/table3_rdit_sensitivity.csv`
  (bandwidth/polynomial/donut grid) is inconsistent with the archived preferred estimate
  (e.g., bandwidth 7, linear, no donut = -0.14 vs -0.0928) and is not used. The source-only
  TODO comments about it were removed from the manuscript.
- Section 5.2: event study described as the country-day estimator actually computed (no
  regression, no user fixed effects); pre-period volatility and absence of a clean
  parallel-trends pattern stated; weekly coefficients framed as diagnostic, not an identified
  dynamic path; intervals renamed donor-placebo reference intervals (not confidence intervals).
- Section 5.3: rewritten to describe only the archived preferred specification, HAC
  inference, the Bangladesh-minus-Philippines controlled specification, and the Philippines
  placebo; no sensitivity grid mentioned.
- Consistency fixes elsewhere: Section 2.1 no longer claims "alternative phase definitions"
  robustness (not reported); Section 3 no longer claims SDID is used as a robustness exercise
  (not reported); Section 8.4 no longer refers to "date fixed effects" (not used by the
  reported estimators); Conclusion labels the event study as diagnostic.
- Tables `tab_did`, `tab_did_eventstudy_full`: "95% interval" relabelled
  "Placebo-based interval" with explanatory notes.
- Empirical numbers changed: none. Section 6.3 daily values now quoted from the RDiT series
  (19.03 / 10.74 / 0.48-1.23) instead of the country-day series.
