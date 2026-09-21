# Thesis Project Instructions

## Project

This repository contains my economics thesis:

"Causal Effect of a Government Internet Shutdown on Software Production:
Evidence from the July 2024 Nationwide Internet Shutdown in Bangladesh"

Author: Hector Alberto Diaz Gomez.

The research question is whether the July 2024 nationwide Internet
shutdown in Bangladesh affected observable software-development
activity on GitHub.

## Golden rule

NEVER INVENT EMPIRICAL RESULTS.

Every numerical statement must be traceable to:
- `results/`
- analysis code
- or an explicitly identified source.

If the manuscript and result files disagree, FLAG THE CONFLICT.
Do not silently choose one number.

Do not alter:
- treatment dates
- samples
- donor pools
- variable definitions
- specifications

merely to obtain stronger or more statistically significant results.

## Repository structure

- `paper/`
  Current manuscript.

- `results/final/`
  Final consolidated econometric outputs.

- `results/synthetic_control/`
  Synthetic control, DiD, placebo and donor results.

- `results/mechanism/`
  Commit author-time versus push-time mechanism results.

- `data/processed/`
  Processed empirical datasets.

- `data/users/`
  GitHub user-location files.

- `references/`
  Academic literature.

- `notes/advisor_feedback.md`
  Advisor comments.

- `notes/revision_log.md`
  Record of manuscript changes.

- `manifest.csv`
  Maps exported files to their original Google Drive locations.

## Treatment

Primary total-shutdown window:

July 18, 2024 through July 23, 2024.

Connectivity began to return from July 23/24 onward.

Do not redefine this window without explicit instruction.

## Main outcome

The primary outcome is the daily share/probability of eligible GitHub
users with observable productive GitHub activity.

Preferred terminology:

- observable GitHub productive activity
- observable software-development activity on GitHub
- public GitHub activity

Do NOT call this total software productivity.

GitHub does not observe:
- private repositories
- work outside GitHub
- all software-development activity
- exact hours worked

## Main empirical hierarchy

Use this hierarchy when discussing the evidence:

1. Synthetic Control
   Primary causal specification.

2. International Difference-in-Differences
   Confirmatory specification.

3. Event Study
   Dynamics and pre-treatment behavior.

4. Regression Discontinuity in Time
   Temporal robustness.

5. Commit authored-time / committed-time versus push-time
   Mechanism analysis.

These are complementary analyses of the same shock.
Do not describe them as five independent natural experiments.

## Main Synthetic Control result

Approximate headline result:

- Bangladesh actual activity during blackout: 2.02%
- Synthetic counterfactual: 15.28%
- ATT: -13.26 percentage points
- Relative effect: -86.8%

Primary donor weights are approximately:

- Pakistan: 47.6%
- Ghana: 32.5%
- Kenya: 19.9%

VERIFY exact values in `results/final/` before quoting them.

## Synthetic-control inference

There are 14 in-space placebo countries.

Therefore the minimum attainable exact rank p-value is:

1 / 15 = 0.0667

Never report this as p < 0.05.

Correct interpretation:
Bangladesh is the most extreme unit in the placebo distribution, but
the resolution of exact placebo inference is limited by the donor-pool
size.

## Difference-in-Differences

The international DiD estimate for the primary outcome is approximately
-13 percentage points.

Holiday exclusion produces a very similar estimate.

Always verify exact values from result files.

## Secondary outcomes

Secondary outcomes include:

- productive activity
- shipping activity
- collaboration activity
- collaboration-event counts
- shipping-output counts

Present fixed primary-SCM weights before outcome-specific weights.

This prevents the outcome-specific SCM results from appearing to be
selected merely to obtain stronger estimates.

## Mechanism analysis

Strict mechanism sample:

- commit author must equal the Bangladesh PushEvent actor
- authored timestamp must exist
- author-to-push delay must be nonnegative

Approximate main result:

- 2,932 commits authored during July 18-23
- 829 pushed on or after July 24
- backlog share: 28.27%

Using committedDate:
- backlog share approximately 27.16%

Interpret this as evidence CONSISTENT WITH:

offline code production followed by delayed synchronization.

Do NOT claim:

"28.27% of all Bangladeshi software production continued offline."

The estimate refers only to the observable strict commit sample.

## Mechanism placebo results

Approximate long-delay rates:

Blackout:
- >24 hours: 29.71%
- >48 hours: 25.38%
- >72 hours: 22.75%

Pre-shutdown placebo-window means:
- >24 hours: about 1.10%
- >48 hours: about 0.72%
- >72 hours: about 0.46%

Verify exact values before quoting.

## Mechanism concentration

The backlog is not generated only by a few developers.

Approximate results:

- 835 users authored commits during blackout
- 222 users have at least one backlog commit
- 977 repositories contain blackout-authored commits
- 246 repositories contain at least one backlog commit
- largest user accounts for about 2.77% of backlog
- top 10 users account for about 21.47%
- after dropping the top 20 users, backlog share remains about 20.37%

## Push-size result

The backlog is more concentrated in larger pushes.

This is potentially consistent with developers accumulating several
local commits and synchronizing them later.

Do not claim that the backlog estimate is invariant to push size.

## Important identification limitations

Always discuss these honestly:

1. GitHub profile location is self-reported.
   It does not prove physical location during the shutdown.

2. GitHub public activity is a proxy for observable software work,
   not total software productivity.

3. Private repositories and non-GitHub work are unobserved.

4. The shutdown occurred during substantial social and political unrest.
   Concurrent shocks remain an identification threat.

5. Git authoredDate and committedDate are metadata and are not
   externally verified measurements of the physical moment code was
   written.

6. Synthetic-control pre-treatment fit is useful but imperfect.

7. Exact country-placebo inference has limited resolution because only
   14 donor countries are available.

## Political/context claims

Treat claims about:
- government actions
- protests
- shutdown orders
- restoration dates
- political events

as factual claims requiring reliable citations.

Do not use politically loaded language.
Do not infer government motives unless explicitly attributed to a source.

## Citations

NEVER invent:
- authors
- papers
- journals
- page numbers
- DOIs
- URLs
- quotations

If a statement needs a source and no verified source is available,
write:

[CITATION NEEDED]

rather than fabricating a reference.

## Writing style

Use formal academic English appropriate for an economics thesis.

Prefer:

- "the estimates indicate"
- "the evidence is consistent with"
- "observable GitHub activity"
- "estimated effect"
- "synthetic counterfactual"

Avoid:

- "proves"
- "definitively proves"
- "all software production stopped"
- "productivity fell by 87%" without qualification

## Editing rules

Before revising an empirical claim:

1. Read the manuscript passage.
2. Read the relevant result file.
3. Verify the number.
4. Flag inconsistencies.
5. Make the smallest justified change.

Do not modify original result files.

Do not modify raw or processed data unless explicitly instructed.

Do not rerun econometric specifications merely to improve results.

## Advisor feedback workflow

Advisor comments are stored in:

`notes/advisor_feedback.md`

Before implementing feedback:

1. List every advisor comment.
2. Explain what it requires.
3. Identify which section/file is affected.
4. State whether new empirical analysis is required.
5. Wait for approval before major methodological changes.

After edits, update:

`notes/revision_log.md`

with:
- date
- advisor comment addressed
- files changed
- sections changed
- empirical numbers changed, if any

## First-review behavior

When first reviewing the thesis:

DO NOT EDIT ANY FILE.

First produce an audit covering:

1. Unsupported empirical claims
2. Numerical inconsistencies
3. Identification threats
4. Overstated causal language
5. Missing methodological definitions
6. Weak organization
7. Citation problems
8. Results that belong in the appendix
9. Results missing from the main text
10. Prioritized revisions

Only edit after explicit approval.
