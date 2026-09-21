# Regression Discontinuity in Time Results

This directory documents the preferred RDiT specification used in the
thesis.

These values are transcribed from the original RDiT estimation output.
No regression was re-estimated when this directory was added to the
replication repository.

## Preferred specification

Main Bangladesh local-linear RDiT:

- cutoff: 2024-07-17
- bandwidth: 7 days
- polynomial degree: 1
- donut: no
- number of daily observations: 15
- effect: -0.092836
- HAC standard error: 0.050344
- 95% CI: [-0.191508, 0.005835]
- HAC p-value: 0.065175
- HAC lags: 2
- Durbin-Watson: 1.207410
- Ljung-Box p-value: 0.336958

Interpretation: approximately -9.28 percentage points.

## Controlled specification

Bangladesh minus Philippines active-rate gap:

- effect: -0.091600
- HAC SE: 0.049802
- p-value: 0.065873

Interpretation: approximately -9.16 percentage points.

## Geographic placebo

Philippines active rate:

- effect: -0.001236
- HAC SE: 0.014922
- p-value: 0.933998

Interpretation: approximately -0.12 percentage points.

## Related files

Sensitivity specifications are stored in:

`data/processed/table3_rdit_sensitivity.csv`

Temporal placebo estimates are stored in:

`data/processed/placebos_rdit.csv`

RDiT is a temporal robustness exercise, not the primary causal design.
The headline design remains Synthetic Control.
