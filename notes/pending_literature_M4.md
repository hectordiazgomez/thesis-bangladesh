# Pending literature for M4: advisor approval required

Verified 2026-10-07. These are proposals only: none of the four BibTeX entries
below is in `paper/latex/references.bib`, and none of the proposed citations is
in the manuscript. The author explicitly reserved the inference redesign for
advisor approval. No estimator or inference procedure was changed.

Metadata for all four works were retrieved by DOI from the Crossref API.
Abstracts were read from the sources linked below. The proposed sentences
summarize the papers; they do not claim that their methods have been implemented
or that their assumptions hold in the Bangladesh application.

## 1. Chernozhukov, Wüthrich and Zhu (2021)

Verified: JASA 116(536), 1849-1864.

- Metadata: https://api.crossref.org/works/10.1080/01621459.2021.1920957
- Abstract: https://scholarworks.brandeis.edu/esploro/outputs/journalArticle/An-Exact-and-Robust-Conformal-Inference/9924115789201921
- Proposed location: `paper/latex/sections/05_empirical_strategy.tex`, Section 5.4,
  after the discussion of the limited resolution of country-placebo inference.
- Proposed sentence:

```latex
\citet*{chernozhukov2021} develop conformal permutation inference for counterfactual and synthetic-control estimators by framing policy evaluation as a counterfactual prediction and structural-break testing problem.
```

```bibtex
@article{chernozhukov2021,
  author  = {Chernozhukov, V. and W{\"u}thrich, K. and Zhu, Y.},
  title   = {An exact and robust conformal inference method for counterfactual and synthetic controls},
  journal = {Journal of the American Statistical Association},
  year    = {2021},
  volume  = {116},
  number  = {536},
  pages   = {1849--1864},
  doi     = {10.1080/01621459.2021.1920957}
}
```

Implementation would require a separately approved specification of the null,
permutations, dependence assumptions, and confidence-set construction. The title
alone does not establish exact validity for this time series.

## 3. Ferman and Pinto (2021)

Verified: Quantitative Economics 12(4), 1197-1221.

- Metadata and abstract: https://api.crossref.org/works/10.3982/QE1596
- Proposed location: `paper/latex/sections/08_robustness.tex`, Section 8.1,
  immediately after the opening discussion of imperfect pre-treatment fit.
- Proposed sentence:

```latex
\citet{ferman2021} show that synthetic-control estimators with imperfect pre-treatment fit can remain biased even with a long pre-treatment period when treatment assignment is correlated with unobserved confounders.
```

```bibtex
@article{ferman2021,
  author  = {Ferman, B. and Pinto, C.},
  title   = {Synthetic controls with imperfect pretreatment fit},
  journal = {Quantitative Economics},
  year    = {2021},
  volume  = {12},
  number  = {4},
  pages   = {1197--1221},
  doi     = {10.3982/QE1596}
}
```

Their abstract also discusses a demeaned estimator and a specification test.
Neither has been added to this thesis.

## 4. Ben-Michael, Feller and Rothstein (2021)

Verified: JASA 116(536), 1789-1803.

- Metadata: https://api.crossref.org/works/10.1080/01621459.2021.1929245
- Authors' preprint abstract: https://arxiv.org/abs/1811.04170
- Proposed location: `paper/latex/sections/03_literature.tex`, comparative-case
  causal inference paragraph, after the existing discussion of pre-treatment fit.
- Proposed sentence:

```latex
\citet*{benmichael2021} propose augmented synthetic control, which uses an outcome model to estimate and correct bias from imperfect pre-treatment fit.
```

```bibtex
@article{benmichael2021,
  author  = {Ben-Michael, E. and Feller, A. and Rothstein, J.},
  title   = {The augmented synthetic control method},
  journal = {Journal of the American Statistical Association},
  year    = {2021},
  volume  = {116},
  number  = {536},
  pages   = {1789--1803},
  doi     = {10.1080/01621459.2021.1929245}
}
```

The journal metadata, rather than the preprint submission year, determine the
bibliographic year. Implementing augmentation would change the estimator and
requires advisor approval, including outcome-model and regularization choices.

## 5. Conley and Taber (2011)

Verified: Review of Economics and Statistics 93(1), 113-125.

- Metadata: https://api.crossref.org/works/10.1162/REST_a_00049
- Published article on an author's university site (abstract, p. 113):
  https://users.ssc.wisc.edu/~taber2/Papers/ctabdd.pdf
- Proposed location: `paper/latex/sections/05_empirical_strategy.tex`, Section 5.2,
  after the paragraph explaining why conventional user-clustered inference is not used.
- Proposed sentence:

```latex
\citet{conley2011} develop difference-in-differences inference for a small number of policy-changing groups using information from a large sample of groups whose policies do not change.
```

```bibtex
@article{conley2011,
  author  = {Conley, T. G. and Taber, C. R.},
  title   = {Inference with ``Difference in Differences'' with a small number of policy changes},
  journal = {Review of Economics and Statistics},
  year    = {2011},
  volume  = {93},
  number  = {1},
  pages   = {113--125},
  doi     = {10.1162/REST_a_00049}
}
```

The large-control-group asymptotic argument does not automatically validate
inference with only fourteen donor countries. Any implementation needs a separate
assessment of applicability. Existing donor-placebo reference intervals are not
relabeled as Conley-Taber confidence intervals.
