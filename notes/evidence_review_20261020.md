# Evidence and manuscript extension — 20 October 2026

The author requested all country/domain figures, a stronger source review, and
individual investigation of residual activity for automation. This extends the
uncommitted October 19 manuscript without replacing its empirical inputs.

## Main findings and their scope

- Complete atlas: 15 countries × 20 defined groups, including unclassified;
  300 panels, 45 empty cells and 144 nonempty cells with fewer than 30 users.
  The same 59,158 accounts, dates, definitions and sector memberships are used.
- Review universe: 40 July 19–22 publishers plus 250 strict onset authors,
  overlap 15, union 275. Retrieved 1,210 of 1,232 exact commit objects and 314
  of 321 repository snapshots; 165 of 180 core head commits have file lists.
- Direct automated-publication evidence: 113/180 core pushes (62.78%) from
  18 accounts. This is 47.68% of all 237 primary events. Categories: 55
  dependency updates, 31 profile graphics, 15 profile-metric updates, 8
  deployments and 4 generated-data updates.
- Retaining all other primary events: 237→124 events; 40→29 accounts with
  events; 87→48 active user-days; 0.2123816%→0.1171761% daily activity.
  These are diagnostic counts, not a replacement national estimate. A head
  audit does not classify every commit in a push. All 57 non-push events stay.
- The other heads are 48 with no identified automation, 4 suggestive and 15
  unavailable. No-direct-evidence does not mean proven human. The account
  status table additionally marks a mixed case and creation-only evidence.
- The highest-volume residual publisher has 42 primary events, of which 41
  have dependency-bot heads. This changes the interpretation of concentration.
- Pre-period active-day means: all core accounts 36.76%; directly automated
  core accounts 52.35%; other core accounts 24.01%; other eligible users 17.18%.
  Median pushes respectively 47.5, 79.5, 20.5 and 21. Higher prior activity
  is partly associated with automatic publication, not demonstrated resilience.
- Strict author identity matching does not remove every generated commit:
  1,097→1,096 after one directly documented generated bibliography import;
  1,086 after also excluding ten README duration-only edits from another
  account. Those ten are not asserted to be confirmed bots.
- Explicit exercise/learning repository-name markers: 83/250 authors,
  87 repositories, 384/1,097 commits. This characterizes content, not jobs,
  student status or training-program membership. Generic fitness templates
  without explicit markers are not automatically classified as coursework.

## Conflicts and repairs

1. Cloudflare's August report says July 23 13:00 UTC; its Q3 account says
   12:00 UTC. Both are reported. Author cohorts ending at 12:00 and 13:00
   contain 899 and 904 commits, from 211 accounts in either case; 123 pushes
   precede either endpoint. The original endpoint retains 1,097 commits and
   250 authors. No duration-normalized effect is claimed for the new counts.
2. The October 19 ancillary weekend feature used Saturday–Sunday. New files
   use Bangladesh's Friday–Saturday weekend. Core mean share 24.3161→24.0808%;
   all-eligible 27.7211→25.9592%; onset 28.0080→24.5871%. Original results remain
   unchanged. This feature had not appeared in the existing manuscript table.
3. Continued public posting is not equivalent to human coding or local access.
   The abstract, introduction, mechanism, discussion and conclusion now reflect
   direct evidence of automation. No account holder is classified as a bot.
4. The existing August 6–7 holiday-label/reopening conflict remains flagged.
   BSS's August 5 report announces opening August 6; input labels are untouched.
5. Source coverage is not exhaustive. Kenya, Nepal, Malaysia and Pakistan have
   documented connectivity events in the observation period. Donor countries
   omitted from the reviewed summaries are not certified unaffected. Post-period
   outages can affect apparent catch-up; no donor is removed on that basis.

## Case-review procedure and limits

`analysis/evidence_20261020/README.md` records the rubric. The assistant inspected
275 individual dossiers (identities/messages and available historical workflow
content); every retrievable core head also has changed-file evidence. Selected
ambiguous cases received additional historical tree, script or diff inspection.
This is an AI-assisted case review, not independent human validation. It is not
a trained or validated detector. All onset changes were not inspected line by line.

Machine identities are corroborated by files/messages; tests, repository topics,
high activity or short repeated messages alone are insufficient. GitHub UI
commits are not automatically bots. A host-list script and example crontab are
suggestive, but their deployment is unverified. Current profiles are dated 2026
and cannot prove 2024 residence or employment. No private repository is queried
for content, no workflow is executed, and credentials are not saved.

The replication records include `individual_case_review.csv`, exact-commit
API responses, historical workflows, supplementary cases, a corrected feature
file, endpoint counts and `audit_summary.json`. Primary data and all earlier
result files remain byte-identical to the pre-extension snapshot. The main
ATT remains −13.255939pp (−86.76928%), with unchanged sample/window/donors.

## Sources actually opened

Dates above use UTC unless the source explicitly supplies a local calendar date.
The bdnews24 page has a 2024 publication date and a 2026 update: it is contextual
reporting, not an archived frozen 2024 text or evidence about sampled individuals.
The two secondary links opened from Cloudflare are retained below for audit;
claims in the manuscript are supported by the readable Cloudflare report.

- [Cloudflare August report](https://blog.cloudflare.com/a-recent-spate-of-internet-disruptions-july-2024/)
- [Cloudflare Q2](https://blog.cloudflare.com/q2-2024-internet-disruption-summary/)
- [Cloudflare Q3](https://blog.cloudflare.com/q3-2024-internet-disruption-summary/)
- [Reuters via ThePrint](https://theprint.in/world/bangladesh-partially-restores-telecommunication-services-as-protests-taper-off/2188524/)
- [UNB university strike](https://unb.com.bd/category/Bangladesh/university-teachers-begin-indefinite-work-abstention-protesting-discriminatory-pension-scheme/138446)
- [Amnesty July 17](https://www.amnesty.org/en/latest/news/2024/07/bangladesh-witness-testimony-video-and-photographic-analysis-confirm-police-used-unlawful-force-against-protesters/)
- [bdnews24, published July 2024; updated August 2026](https://bdnews24.com/business/08b8a4b9144f)
- [BSS reopening](https://www.bssnews.net/news/top-news/202726)
- [Dey et al.](https://arxiv.org/abs/2003.03172)
- [Golzadeh et al.](https://arxiv.org/abs/2103.11779)
- [GitHub workflow documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Dhaka Tribune, opened as Cloudflare reference](https://www.dhakatribune.com/bangladesh/352554/broadband-internet-restored-in-limited-areas-after)
- [The Business Standard, opened as Cloudflare reference](https://www.tbsnews.net/bangladesh/mobile-data-be-restored-3pm-today-palak-904901)

The full list of opened API endpoints is in
`results/evidence_20261020/opened_sources.csv`. GraphQL shares one endpoint;
repository names, requested SHAs and retrieval timestamps are recorded per
response in `data/evidence_20261020/`. Commit-page links in the case register
identify the public objects returned by those API calls.
