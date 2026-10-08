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

## 2026-10-06 — SC reproducibility, SDID, in-time placebos, mechanism weighting

- Advisor comment addressed: none recorded; approved by the author.
- New code (no archived estimate changed):
  - `analysis/synthetic_control/01_reproduce_sc.py`: canonical SC refit from
    `results/synthetic_control/country_day_donor_pool.parquet` (simplex-constrained least
    squares via NNLS). Reproduces exactly: weights (Pakistan 0.4758, Ghana 0.3249,
    Kenya 0.1993; max deviation 0), ATT -13.2559, relative -86.769%, pre-RMSPE 3.2596,
    post-RMSPE 13.6658, ratio 4.1924, 14 in-space placebos (max deviation 1e-6),
    rank p 1/15 for both statistics, 14 leave-one-out ATTs. Fails loudly otherwise.
    Also writes the descriptive full path (May 1-Sep 4) and weekly gaps.
  - `analysis/synthetic_control/02_sdid_archived_check.py`: archived SDID weights reproduce
    the archived SDID ATT (-17.9495); decomposition by unit/time weights.
  - `analysis/synthetic_control/03_intime_placebos.py`: pre-specified in-time placebos
    (8 eligible windows).
  - `analysis/mechanism/01_placebo_weighting_audit.py`: placebo weights identified as
    inverse daily metadata-query rates; all archived rows reproduced exactly.
- Mechanism weighting diagnosis: metadata were queried for a daily sample (7-17%) of
  commits pushed Jul 1-17 and for all commits pushed from Jul 18. The archived
  inverse-probability-weighted placebo rates are the valid comparison; blackout commits
  receive weight one (same estimator). Unweighted placebo means would be 1.73 / 1.33 /
  1.08% (>24/48/72h) instead of 1.10 / 0.72 / 0.46%. Archived numbers unchanged.
- Manuscript changes:
  - Figure 1 extended descriptively to Sep 4 with archived weights; new caption states the
    shutdown interval defines the estimand and post-restoration gaps are descriptive.
    Section 6.1: one sentence on the descriptive post-restoration gap.
  - Section 7.1: one sentence on inverse-probability weighting of placebo rates;
    Table A6 note expanded.
  - Section 8.1: in-time placebo paragraph and SDID paragraph.
  - Appendix: Table A4 (SDID), Figure A1 and Table A5 (in-time placebos). Later appendix
    tables renumbered (mechanism placebo comparison: former A6, now A8).
- New numbers reported: SDID -17.9495 (archived); SDID time-weight shares 72.2% (Jul 1-17),
  27.1% (Jul 2), 30.2% (Jul 10); baselines 22.54% vs 17.25%; decomposition (-13.86 to -17.99);
  in-time pseudo-ATTs -3.076 to +7.349; weekly SC gaps (pre range -2.86 to 5.88;
  weeks +1..+6: -3.11, -2.89, 0.52, 4.24, 4.67, 2.67).
- Not reported: archived SDID SE (0.4999) and p-value (0.0) - computation undocumented.

## 2026-10-06 — Editorial/presentation pass (advisor-ready version)

- Advisor comment addressed: none recorded; requested by the author. No new estimators,
  no re-estimation; all headline estimates unchanged.
- Title: "Internet Shutdowns and Software Development: Evidence from Bangladesh";
  date "Draft -- October 2026". README title updated. CLAUDE.md still lists the old
  title (not edited).
- Abstract rewritten (275 words; fits on page 1), organized around three contributions.
- Introduction: "This paper makes three contributions" paragraph added; mechanism and
  recovery paragraphs relabelled as the second and third contributions; literature
  paragraph cites Allcott et al. (2016) and Akerman et al. (2015); "sustained run" ->
  "two-week run" (also in Section 6.5).
- Section 3 restructured into four paragraphs (Internet as input; outages/shutdowns;
  GitHub measurement; comparative-case inference).
- Citations added (all verified 2026-10-06):
  - abadie2003 AER 93(1):113-132, doi 10.1257/000282803321455188
  - allcott2016 AER 106(3):587-624, doi 10.1257/aer.20140389
  - akerman2015 QJE 130(4):1781-1824, doi 10.1093/qje/qjv028
  - nagle2019 Management Science 65(3):1191-1215, doi 10.1287/mnsc.2017.2977
  - birkholz2026 JDE 180:103708, doi 10.1016/j.jdeveco.2025.103708 (Crossref API)
  - quispe2026naics: author-supplied BibTeX on the Hugging Face model card for
    aquiro1994/naics-github-classifier-multilingual (identical in local clone
    tools/naics-github-train, commit 3a041fb; cached weights snapshot e40747e9). No paper exists.
  - isoc2024pakbal, isoc2024pakpun: Internet Society Pulse pages for Pakistan regional
    shutdowns (Balochistan Jul 14-17; Punjab Jul 16), replacing the Bangladesh page
    previously cited for the Pakistan claim (Section 6.1).
  - kreitmeir2024 updated to SoDa Laboratories WP 2024-01 (+ arXiv:2403.01964); still
    unpublished. gunsilius2023 still arXiv:2309.14630 (v3, May 2025); unchanged.
- Section 2.1: political-context sentence now cites belson2024 (Cloudflare, Aug 1 2024),
  which states that student protests against quotas in government jobs preceded the
  shutdown order; wording aligned with the source.
- Section 4.4: [CITATION NEEDED] replaced by quispe2026naics. Section 8.3: added the
  model card's own caveats (GPT-4.1 training labels; roughly half of confident labels on
  public GitHub may belong to no sector).
- Section 4.2: removed claim that counts are winsorized "in user-level regressions"
  (no user-level regressions are reported).
- Section 5.2: user-level TWFE paragraph and equation removed (and the Section 6.2
  sentence justifying unreported user-day estimates). Equations now: (1) SC ATT,
  (2) aggregate DiD, (3) event study, (4) RDiT, (5) sector recovery.
- Table 3 restructured: Design | Effect (pp) | Relative effect | Inference | Role.
- Table 8 and Table A13: column renamed "First two-week run >= 80".
- Figure notes (main text) shortened by 36% (953 -> 610 words); file provenance replaced
  by "Source: Author's calculations using GH Archive" (provenance remains in code,
  README, and this log).
- Figure 5 extended to week +17; former Figure 6 (sector event study) moved to the
  appendix (Figure A2).
- Section 7 heading: "Mechanism: Offline Work and Delayed Synchronization".
- Source-only TODO comments removed. Open item moved here: the selection script for the
  20,000-account sector sample is not in the repository, and whether bot filters were
  applied is undocumented.
- PDF: 45 pages before and after.

## 2026-10-07 — Referee report: R1, R3 and bibliography

- Comments addressed: R1, R3, and the bibliography section of the referee report.
- R1: `country_day_outcomes_enriched.parquet` summed activity over all 150,017 users but divided by the 59,158 eligible users. New script `analysis/synthetic_control/04_secondary_outcomes_eligible.py` rebuilds the panel on eligible users, after reproducing the archived estimates from the archived panel. New outputs: `results/synthetic_control/country_day_outcomes_eligible.parquet`, `results/final/*_eligible.csv`, `results/final/table_secondary_archived_vs_eligible.csv`. Archived files unchanged; `make_all_tables.py` now reads the `_eligible` files.
- Empirical numbers changed (secondary outcomes only; primary outcome unchanged):
  - Fixed primary weights, ATT: productive -15.179 -> -11.665 pp; shipping -1.333 -> -0.979 pp; collaboration -0.780 -> -0.611 pp; collaboration events -24.095 -> -19.956 and shipping output -23.981 -> -17.913 per 1,000.
  - Outcome-specific weights, relative effect: productive -86.2% -> -86.7%; shipping -92.2% -> -90.5%; collaboration -92.1% -> -91.9%.
  - Placebo ranks: collaboration RMSPE ratio 0.20 -> 0.1333. Now reported for counts: collaboration events 0.2667 (ATT) / 0.1333 (ratio); shipping output 0.0667 / 0.0667.
  - DiD, productive activity: -14.669 -> -11.748 pp (all days); -14.975 -> -12.007 pp (holidays excluded).
  - Text updated: Section 6.4 (both paragraphs) and the introduction.
- R3: `results/sector_recovery/sectorwide/sectorwide_support.csv` and `results/sector_recovery/pre8/sector_recovery_summary_pre8.csv` now versioned (`.gitignore`); `make_all_figures.py` now calls Figure A1; `10_make_sector_results_final.py` reads only the 0.80 event study. The four scripts (04, tables, figures, sector final) run in a fresh clone.
- Bibliography: cloudflare2024 (Belson, July 16, 2024, URL), isoc2024 (specific page), githubevents (GHES 3.14 page with the 20-commit cap), schachenhofer2023 (vol. 98, art. 104101), aceto2018 (Pescapé); VERIFY comments removed; aceto2018 and schachenhofer2023 now cited in Section 3 (\nocite removed). In-text labels are now Belson (2024a) and (2024b).
- Wording aligned with sources: Section 2.1 ("also records"; "fixed-broadband providers"), Table 1 (ISOC for the July 16-17 blocking), Section 3 (Kreitmeir and Raschky: binary indicators because actions are rare), Section 6.3 (Hausman and Rapson urge caution).
- Repository: removed the stray empty file `latex-version` and its `.gitignore` entry.
- PDF rebuilt with XeLaTeX and the same fonts; 45 pages. `paper/thesis.txt` and `paper/thesis.docx` were not modified.

## 2026-10-08 — Referee pending items: literature, R4 counts and July 17 source

- Comments addressed: requested literature additions, R4 sample-count provenance,
  and the unsupported July 17 holiday in Table 1. Sources for R5 collected only;
  M4 inference redesign remains pending advisor approval. Review began October 7.
- Repository: created `referee-pending-items` from `referee-r1-r3-bib` at
  `ba99159`. Pre-existing untracked `all_figures/` left untouched. No push.
- Literature: all seven requested DOI records verified through Crossref and all
  seven abstracts read. Added `abadie2015`, `zhang2011`, `mcdermott2021` to
  `paper/latex/references.bib`; added accurate sentences in Section 3 (Zhang/Zhu,
  McDermott/Hansen) and Section 5.4 (Abadie et al.), with an additional Abadie
  citation at the in-time placebo discussion in Section 8.1. Files:
  `sections/03_literature.tex`, `sections/05_empirical_strategy.tex`,
  `sections/08_robustness.tex` under `paper/latex/`.
- New `notes/pending_literature_M4.md`: verified metadata, proposed BibTeX entries,
  one sentence and insertion location each for Chernozhukov et al. (2021),
  Ferman/Pinto (2021), Ben-Michael et al. (2021), and Conley/Taber (2011).
  None inserted into active bibliography or manuscript; no methodological change.
- R4: new `analysis/sector_recovery/11_sector_sample_counts.py` reads local inputs
  (SQLite explicitly read-only), writes versioned
  `results/sector_recovery/sector_sample_counts.csv`, and records missing files
  or mismatches without altering the manuscript. Existing `.gitignore` already
  permits this new CSV, so no ignore changes were needed.
  - Reproduced: 23,866 pre-active accounts; 168,875 distinct repository names;
    92,979 successful historical README recoveries; 32,491 successful
    classifications with a recovered README and score >= 0.80.
  - Reproduced Arts concentration: 15,376 / 18,638 baseline events =
    82.49812211610688%, matching 82.5% after rounding. The request's description
    as a share of classified repositories differs from the actual Section 8.3
    event-concentration claim; flagged in the audit, not silently substituted.
  - Cross-checked predictions export against SQLite and sample membership against
    the event panel. Missing-input behavior tested: blank values, required paths,
    `matches=unavailable`, exit status 1. All five available-input rows match.
- July 17: panel confirms `is_holiday=1`, `holiday_name=Ashura`; Table 1 now names
  Ashura and cites `dailystar2024ashura` (The Daily Star, updated July 7, 2024).
  Citation also included in its source note. Files: `references.bib` and
  `sections/02_background.tex`. Official gazette not successfully retrieved;
  the authorized reputable-news fallback explicitly confirms public-holiday status.
- New `notes/referee_pending_items_audit.md`: source URLs actually opened,
  verified references, R4 definitions and input fingerprints, local-log/export
  differences, validation and open items. Records R5 evidence only: June 17
  Eid al-Adha; initial August 5-7 holiday announcement; subsequent ISPR reopening
  from August 6 (conflicts with stored August 6-7 holiday labels); renewed
  Internet shutdown August 4-5. June/August text and data were not edited.
- Open items: advisor approval for M4; R5 holiday-label adjudication/second-shutdown
  treatment; missing original sector extraction/selection code and bot-filter
  documentation; preferred government holiday gazette retrieval. All five R4
  manuscript values are now traceable to local inputs.
- Validation: ran `python3 analysis/tables/make_all_tables.py` using the existing
  sector environment; all 22 generated tables unchanged. PDF rebuilt with
  Tectonic (XeTeX/xdvipdfmx), preserving fonts, and saved to
  `paper/latex/thesis.pdf`: 46 pages, no LaTeX errors or undefined citations or
  references. All 29 bibliography entries cited; no `\nocite`; four M4 keys
  absent. Rendered all pages and visually checked changed passages and references;
  no overfull boxes, clipping or overlap. Non-fatal underfull/font/inputenc notices
  remain. `git diff --check` passes.
- Empirical numbers changed in manuscript: none. No archived result, processed
  dataset, treatment date, donor pool or estimator changed. `paper/thesis.txt`
  and `paper/thesis.docx` not modified.

## 2026-10-08 — R5: second shutdown and holiday conflict
- Files: analysis/round2/r5_holidays.py; new results/diagnostics/round2/r5_*; notes/round2_R5.md; LaTeX Figure 1 note, Section 6.5 and bibliography.
- Old: August 5 dip described only as holiday; source of week +2 decline unidentified. New: sourced August 4–5 shutdown and initially declared August 5–7 holidays, with August 6 reopening conflict explicit.
- Numbers: alternative August 6/7 holiday flags 1 → 0 only in the new comparison; original files unchanged. DiD -13.087502 → -13.087502 pp; holiday-excluded DiD -13.379098 → -13.379098 pp. No headline change. Figure/table regeneration and PDF validation scheduled at Phase A close.

## 2026-10-08 — R2: outcome and eligibility definitions
- Section 4.1/4.2 and Table 2 distinguish stored primary productive_events>0 from verified secondary productive_output_active. UTC stated; any-event eligibility reconstructed; missing bot thresholds and exact event-type mapping flagged.
- New audit script, outputs and pending BigQuery query; no original data or outcomes modified.
- Numbers added, not substituted: primary pre-rate 17.254550%, secondary 15.379483%; 60,729 eligibility candidates, 59,158 retained, 1,571 unexplained exclusions; 104,786 of 1,103,680 active days lack documented components. Original headline unchanged. Exact event list and full sample builder remain blocked on upstream provenance.

## 2026-10-08 — R6: recover local upstream/history
- Authorized Documents/Downloads search found legacy thesis scripts and downloaded sector script versions. Added distinct byte-for-byte copies under archive/upstream_local with SHA-256 provenance and duplicate mapping; no upload/push performed, as instructed.
- Added user-supplied report to notes/referee_report.pdf. Documented missing current upstream extraction, definitions, bot filters, seeds and estimator provenance in archive/upstream_local/README.md.
- Empirical numbers: none changed. Historical code is not adopted as the current specification; absent upstream stages remain blocked.

## 2026-10-08 — M5: complete shutdown days and selection
- Added analysis/round2/m5_core_window.py and new diagnostic CSVs; Section 6.1 reports primary and July 19–22 sensitivity side by side with unchanged weights.
- Original: actual 2.021287%, counterfactual 15.277226%, ATT -13.255939 pp (-86.769280%). Additional core window: 0.212382%, 14.686946%, -14.474564 pp (-98.553943%). Neither replaces the headline.
- Residual 21.75 active accounts/day bounds the observed active potentially mislocated component, NOT total location error; Section 8 discusses mean reversion and donor decline -2.145761 pp.

## 2026-10-08 — M1: mechanism in levels and onset cohort
- New m1_levels.py and five diagnostic CSVs/JSON; new author-date figure generator and Section 7 figure. Rewrote mechanism framing in abstract, introduction, Section 7, discussion and conclusion.
- Preserved calendar result 829/2,932 = 28.274216%; added onset cohort 752/1,097 = 68.550593%, 250 users versus calendar 835; 1,835 calendar commits precede onset. Weighted normal six-day level 33,787.497; matched 5.375-day level 30,038.262.
- Added creation changes -91.322234% calendar; -96.753237% onset vs six-day reference; -96.347991% matched (-96.375706% duration-scaled). Backlog/normal 2.453570% calendar, 2.503474% onset matched. Replaced “substantial margin” and displacement claims with these levels and censoring limits.
- Added explanation of 345 onset commits pushed before July 24 (64 users; 246 pushed July 23), and 35 calendar backlog commits pushed August 5–10. No headline SCM, sample, window or donor change.

## 2026-10-08 — M8: cumulative loss and persistence
- Added cumulative daily audit, all five return criteria, and summary under results/diagnostics/round2. Revised abstract, introduction, results, discussion and conclusion; dropped unsupported policy prescriptions and “timestamps reveal all three margins”.
- Old: qualitative first-week return/range framing. Added: 8,145.244 user-day shutdown deficit; first daily crossing July 27, deficit 10,186.006; first seven-day-mean crossing August 13, deficit 12,067.693; first seven consecutive nonnegative days ending August 16. Own-pre-mean crossings August 14/22.
- Added negative area 13,526.274, positive area 9,893.465, net deficit through September 4 of 3,632.809; largest cumulative deficit 13,236.567 on August 9. No causal catch-up claim, no new headline estimator.

## 2026-10-08 — M6: full RDiT grid
- Added reproducible cutoff × bandwidth × series grid (45 fits), preserved 16 archived rows in separate new output, and audited sample overlap. Added both full grids to appendix/table generator and methodological limitations to text; created advisor memo M6 recommendation.
- Original preferred estimate unchanged: -9.2836 pp (SE 5.0344). Added Bangladesh grid range -4.4457 to -19.5230 pp; archived 16-row range -12.4 to -23.7 pp. Conflict: archived h=7 linear/no-donut -14.0 pp vs reproduced -9.2836, distinct unknown provenance. RDiT-only 174 accounts; SCM-only 86. No specification selected by results.

## 2026-10-08 — Minor 1
- Added sourced Pakistan July 31 disruption and implications for recovery counterfactual to Section 8. Original weight 47.6% unchanged; no estimate changed. Source opened: https://blog.cloudflare.com/a-recent-spate-of-internet-disruptions-july-2024/.

## 2026-10-08 — Minor 2
- Replaced unqualified sizable-community claim with verified Ghana 1,373 and Jordan 446 counts and sampling-noise limitation. No donor or estimate changed.

## 2026-10-08 — Minor 3
- Clarified query target versus universe in Section 4.3: 86,065 target = 17,000 sampled pre + 69,065 post; pre universe 134,479, sampling 12.64%. Resolution figures unchanged.

## 2026-10-08 — Minor 4
- Qualified authoredDate/committedDate agreement as dependent metadata fields, not independent clock validation. No numbers changed.

## 2026-10-08 — Minor 6
- Corrected the reversed Finance/Information ordering in Section 6.5: Finance 91.3, Information 94.5; stored results unchanged.
