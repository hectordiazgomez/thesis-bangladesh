# Evidence extension, 20 October 2026

The author requested a substantive revision: full country-by-domain figures,
sourced connectivity context, and an individual examination of continued
publication and author-time activity for signs of automation.

## Scope and invariants

- The original eligible sample, primary outcome, July 18–23 window, donor pool,
  fitted national weights and headline estimate remain unchanged.
- New descriptive outputs and audit responses go to `results/evidence_20261020/`
  and `data/evidence_20261020/`. Earlier results are read-only.
- The international domain figures use the existing October 19 frozen
  `historical_readme_080` membership, including all small and empty cells.
- Two overlapping audit cohorts are kept separate: 40 accounts with a primary
  event on July 19–22, and 250 strict authors dated from July 18 15:00 UTC to
  July 24 00:00 UTC. Their union is 275; author metadata is not proof of local
  human work. The latter window includes part of the July 23 restoration.
- Current profile objects are dated retrieval evidence, not 2024 location or
  occupation. No personal location, employment or political affiliation is
  inferred. Historical workflows are read as text, never executed.

## Automation review rubric

This is a documented case audit, not a preregistered or validated bot detector.
Accounts can contain both manual and automated activity. Labels describe the
audited activity, not whether a person is a "bot."

1. **Direct evidence of automated publication:** an explicit machine identity
   or a historical workflow that schedules/generates and commits the observed
   output, corroborated by matching messages/files. Ordinary `web-flow` GitHub
   web commits are not sufficient.
2. **Suggestive pattern only:** repeated templates, profile-only commits or
   regular timing without an independently identified generation mechanism.
3. **No direct evidence found:** inspected changes have no identified
   automation mechanism. This does not establish human authorship.
4. **Unavailable/insufficient evidence:** historical objects or relevant
   context cannot be recovered.

Having CI tests, a dependency file, a repository about test automation, or a
high commit count is not in itself evidence of autonomous publication.
Activity-level exclusions are descriptive sensitivities shown beside the
original counts; they do not redefine the national outcome or sample.

## Execution

1. `prepare_audit.py`: freeze account, commit and repository audit targets.
2. `fetch_public_evidence.py`: retrieve public profile objects, exact commit
   objects and historical workflow/readme snapshots; use `gh` credentials
   only in memory. Cache failures explicitly.
3. `country_atlas.py`: reconstruct every country/domain daily rate, verify the
   existing synthetic paths, and generate the full appendix atlas.
4. `analyze_audit.py`: reproduce the recorded case decisions, activity-level
   decomposition, endpoint and weekend diagnostics, and manuscript tables.
5. `verify_evidence.py`: validate identities and compare 119 frozen input and
   result files against their pre-extension hashes.

The individual review was performed by the coding assistant (AI-assisted).
There is no second independent human annotation, measured classifier precision
or verified physical location. All 275 dossiers were inspected for messages and
identities, with historical workflows where recoverable; core heads additionally
have file-level evidence. Onset changes were not all line-by-line code-reviewed.
The 87 explicit learning-marker repositories use the documented name rule;
they are examples of project content, not an occupational classification.

The historical host-list update script and example crontab strengthen a
suggestive case but do not establish deployment of that schedule. Its four
pushes are therefore retained. The ten duration-only README edits are separately
excluded only in an onset-count sensitivity, not declared confirmed bots.

The manual case decisions, evidence links, subsequent scripts and numerical
validation are retained alongside the outputs. Reproduction of cached analyses
does not require API access; refreshing public evidence is a separate step.
