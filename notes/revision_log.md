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
