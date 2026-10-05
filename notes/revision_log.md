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
