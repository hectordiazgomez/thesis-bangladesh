# Referee pending-items audit

Review begun 2026-10-07 and completed 2026-10-08, America/Los_Angeles.
Base: `referee-r1-r3-bib`, commit `ba99159`; work branch:
`referee-pending-items`. `notes/advisor_feedback.md` contains only a placeholder;
the actionable instructions are the author's pasted request.

## Scope of the requested comments

| Item | Requirement and affected files | New empirical analysis? |
| --- | --- | --- |
| Literature | Verify seven DOI records and abstracts; cite works 2, 6, 7 in Sections 3, 5.4 and 8.1; prepare works 1, 3, 4, 5 in `notes/pending_literature_M4.md` | No; M4 implementation explicitly deferred for advisor approval |
| R4 | Trace Section 4.4 sample counts and Section 8.3 Arts concentration; add a read-only audit script and small versioned CSV | Descriptive recount only; no new estimator, sample selection or classification |
| July 17 / R5 preparation | Verify the holiday label, cite a reliable source in Table 1, and collect sources on June 17 and August 4-7 in this note | No; June/August manuscript passages and holiday data unchanged |

## Literature verification

All seven Crossref API records were opened successfully by DOI, and at least the
abstract of every work was read. API rate-limit errors on the first parallel
attempt were resolved by sequential retrieval. Metadata match the requested
works. For Abadie et al., 2014 is the online-first year; 2015 is the journal
issue year used in the bibliography. No publication month was added because the
API print-month field and the published PDF's April issue label differ.

| No. | Work | Verified journal/report metadata | Action and sentence location |
| --- | --- | --- | --- |
| 1 | Chernozhukov, Wüthrich and Zhu (2021) | JASA 116(536):1849-1864 | Deferred M4; proposed Section 5.4 |
| 2 | Abadie, Diamond and Hainmueller (2015) | AJPS 59(2):495-510 | `abadie2015`; Section 5.4 sentence on RMSPE ratios and in-time placebos; also cited at their discussion in Section 8.1 |
| 3 | Ferman and Pinto (2021) | Quantitative Economics 12(4):1197-1221 | Deferred M4; proposed Section 8.1 |
| 4 | Ben-Michael, Feller and Rothstein (2021) | JASA 116(536):1789-1803 | Deferred M4; proposed Section 3 |
| 5 | Conley and Taber (2011) | Review of Economics and Statistics 93(1):113-125 | Deferred M4; proposed Section 5.2 |
| 6 | Zhang and Zhu (2011) | AER 101(4):1601-1615 | `zhang2011`; Section 3, infrastructure outages paragraph; distinguishes nonblocked contributors |
| 7 | McDermott and Hansen (2021) | NBER Working Paper 29598, December 2021 | `mcdermott2021`; Section 3, GitHub measurement paragraph; weekend/out-of-hours activity |

Abadie et al.'s published full text (pp. 499, 504-505) supports the methodological
sentence. It illustrates the diagnostics; the manuscript does not claim that
this 2015 article originated every placebo procedure. The publisher also links
a correction dated October 5, 2026 (DOI 10.1111/ajps.70083), which was opened and
read. It corrects GDP units and descriptive donor-pool averages in the German
application, not the description of RMSPE ratios or in-time placebos cited here.
It is recorded here rather than added as an uncited bibliography entry.

The proposed M4 note includes each complete BibTeX entry, one citation sentence,
a source link and a specific insertion location. None of the four entries or
citations was inserted into the manuscript. The current inference was not
redesigned or represented as implementing these methods.

## R4: local reproduction

Command (from the repository root, using the existing environment):

```sh
.venv-sector/bin/python analysis/sector_recovery/11_sector_sample_counts.py
```

Output: `results/sector_recovery/sector_sample_counts.csv`. Its five columns are
`statistic,value,manuscript_value,source_file,matches`. It is not excluded by the
existing `.gitignore`, so no ignore-rule change is necessary. All existing
archived results and data are read-only inputs.

| Statistic | Recomputed | Manuscript | Match | Input/definition |
| --- | ---: | ---: | --- | --- |
| Pre-active accounts | 23,866 | 23,866 | Yes | Unique non-null `login_lower` with `pre_active_days >= 1` in `data/sector_recovery/bangladesh_full_preactivity_stats.parquet` |
| Distinct repositories | 168,875 | 168,875 | Yes | Unique `repo_name` in `data/sector_recovery/bd_preactive20000_repo_event_day_metadata.parquet` |
| Historical READMEs recovered | 92,979 | 92,979 | Yes | `readme_status='ok'` in `data/sector_recovery/repo_sector.sqlite`, table `repos` |
| Classified repositories | 32,491 | 32,491 | Yes | `readme_status='ok' AND prediction_status='ok' AND score >= 0.80` in the same database |
| Arts largest-repository share of baseline events (%) | 82.49812211610688 | 82.5 | Yes, to one decimal | Sum `event_count` by repository within NAICS 71, all event types, May 23-July 17, 2024; apply the same classification filter |

The Arts numerator is 15,376 events in `Contest-Hive/__contest-hive-backend`,
and the denominator is 18,638 events across 374 baseline-active Arts
repositories. This reproduces `07_repo_recovery_eventstudy.py`'s
`concentration_audit` and the ignored local output
`results/sector_recovery/eventstudy/sector_concentration_recentpre.csv`.

**Definition conflict in the request:** Section 8.3 does not claim that 82.5%
of classified repositories belong to Arts. It says one repository accounts for
82.5% of pre-shutdown events within that sector. Arts has 1,386 of the 32,491
valid classified repositories overall (4.265796682158136%); this is a different
statistic, not a replacement for the manuscript's event-concentration measure.
No R4 manuscript number was changed.

Other files checked and traps resolved:

- `README_sector_pipeline.md` identifies the event-day panel as the canonical
  repository universe and warns that `repo_id` was not preserved consistently.
  The separate universe parquet has 183,088 rows, so counting its rows would
  not recover the 168,875 distinct repository names.
- `results/sector_recovery/repo_naics_predictions.parquet` independently agrees
  with the SQLite totals. A score-only filter would count 40,431 repositories;
  7,940 of these lack a successful README and are excluded by the actual pipeline.
- The final lines of `logs/repo_sector_stream.log` report 168,775 processed
  repositories and 92,911 successful READMEs for that streaming run. Those are
  not the complete database totals. The existing database also contains 100
  other rows and 68 more successful README statuses than the run totals.
- `repo_sector_stream.py` stores README status, length and hash but clears the
  compressed README after classification. This audit reproduces recorded
  recovery success, not a fresh download of every historical README.
- `bangladesh_preactive_sample_20000.parquet` contains 20,000 accounts, records
  the eligibility rule as at least one selected GH Archive active day from
  January 18 through July 17, 2024, and records sample seed 20240718. The event
  panel spans January 18-November 23 and contains those 20,000 accounts.
- `tools/naics-github-train` contains the model code, mappings and documentation;
  it does not replace the event panel, prediction database or upstream account
  selection code. `manifest.csv` has no sector-recovery mapping.

The script opens SQLite with `mode=ro`. It writes only the new audit CSV. A
missing-input check in an empty temporary root produced five unavailable rows,
blank values, explicit required paths and exit status 1, rather than guessing.
A numeric mismatch likewise yields `matches=false` and exit status 1. The
script compares percentages at the manuscript's displayed precision.

## Holiday verification and sources reserved for R5

The Bangladesh rows in
`results/synthetic_control/country_day_donor_pool_with_holidays.parquet` contain:

| Date | is_holiday | holiday_name |
| --- | ---: | --- |
| 2024-06-17 | 1 | Eid al-Adha |
| 2024-07-17 | 1 | Ashura |
| 2024-08-05 | 1 | Public Holiday |
| 2024-08-06 | 1 | Public Holiday |
| 2024-08-07 | 1 | Public Holiday |

- **July 17:** The Daily Star, "Holy Ashura to be observed on July 17," updated
  July 7, 2024, explicitly identifies the date and public-holiday status and
  reports the National Moon Sighting Committee's decision. Added
  `dailystar2024ashura` to the bibliography and cited it in the July 16-17 row
  and Table 1 source note. BSS's July 6 report independently confirms the date.
  Searches for the official Cabinet/MoPA holiday gazette did not yield a
  successfully inspected national gazette. A CAAB national-holiday PDF was
  located but could not be opened (web 502 / local certificate failure), so it
  is not used as evidence. The requested reputable-news fallback was used.
- **June 17:** BSS, June 7, 2024, confirms Eid-ul-Azha on June 17 following the
  National Moon Sighting Committee's decision. No manuscript or data change.
- **August 5-7:** BSS, datelined August 4, 2024, reports the announcement of a
  three-day general holiday for Monday-Wednesday (August 5-7). Its headline
  and relative-day wording are awkward; the explicit weekday sequence and
  dateline are the basis for the calendar mapping, not the word "today."
- **Subsequent reopening:** BSS, August 5, 2024, reports an ISPR press release
  that government, semi-government, autonomous, private offices, factories
  and educational institutions would open the following day, August 6.
  **R5 conflict:** the stored labels for August 6-7 do not reflect this
  subsequent reopening announcement. This needs adjudication before any
  revision of the holiday control. Labels were not changed here.
- **Second shutdown:** Cloudflare's Q3 2024 disruption summary reports mobile
  traffic dropping on August 4 at approximately 13:30-14:15 Bangladesh time,
  a full outage around 10:30 on August 5, and recovery beginning around 13:20
  for broadband and 14:00 for mobile on August 5. This is a separate episode
  to consider under R5; the thesis's July 18-23 treatment window is unchanged.

## Open items

1. Advisor approval for the M4 inference redesign and associated four citations.
   Literature proposals are complete; no implementation was authorized.
2. R5 must reconcile the August 6-7 labels with the reopening announcement and
   address the August 4-5 shutdown. Source collection is complete; adjudication
   and empirical changes are explicitly outside this request.
3. The upstream extraction/selection script for the sector accounts remains
   absent, as already noted in the revision log. The local aggregate files
   reproduce the requested counts, but do not fully document their original
   construction or whether bot filters were applied. Obtain the original
   export/selection code or query from the author/Drive archive for that audit.
4. The preferred national government holiday gazette was not successfully
   retrieved. This does not leave July 17 unsupported: the requested fallback
   provides both holiday name and public-holiday status.

No R4 numeric discrepancy remains under the manuscript's actual definitions.

## Sources opened and used

All URLs below were opened and their relevant content read, using the web tool
or direct HTTP retrieval (Crossref and the NBER page). Search snippets alone
were not used to support manuscript additions.

### DOI metadata

1. https://api.crossref.org/works/10.1080/01621459.2021.1920957
2. https://api.crossref.org/works/10.1111/ajps.12116
3. https://api.crossref.org/works/10.3982/QE1596 (also supplies the abstract)
4. https://api.crossref.org/works/10.1080/01621459.2021.1929245
5. https://api.crossref.org/works/10.1162/REST_a_00049
6. https://api.crossref.org/works/10.1257/aer.101.4.1601 (also supplies the abstract)
7. https://api.crossref.org/works/10.3386/w29598

### Abstracts, full text and publisher correction

8. https://scholarworks.brandeis.edu/esploro/outputs/journalArticle/An-Exact-and-Robust-Conformal-Inference/9924115789201921
9. https://onlinelibrary.wiley.com/doi/abs/10.1111/ajps.12116
10. https://economics.mit.edu/sites/default/files/publications/Comparative%20Politics%20and%20the%20Synthetic%20Control.pdf
11. https://arxiv.org/abs/1811.04170
12. https://users.ssc.wisc.edu/~taber2/Papers/ctabdd.pdf
13. https://www.aeaweb.org/articles?id=10.1257/aer.101.4.1601
14. https://www.nber.org/papers/w29598 (web tool failed; direct HTTP succeeded and abstract was extracted)
15. https://onlinelibrary.wiley.com/doi/10.1111/ajps.70083

### Bangladesh chronology

16. https://www.thedailystar.net/news/bangladesh/news/holy-ashura-be-observed-july-17-3650606
17. https://www.bssnews.net/news/198839
18. https://www.bssnews.net/news/193915
19. https://www.bssnews.net/news-flash/202642
20. https://www.bssnews.net/news/202726
21. https://blog.cloudflare.com/q3-2024-internet-disruption-summary/

## Validation and local input fingerprints

- Ran `python3 analysis/tables/make_all_tables.py` with `.venv-sector/bin` first
  on PATH. All 22 generated table fragments are identical to the base commit.
  No table-result input changed; Table 1 is a manually authored table.
- Built from `paper/latex` with `tectonic --keep-logs --keep-intermediates -o
  <scratch-directory> main.tex`, then installed the resulting `main.pdf` as
  `paper/latex/thesis.pdf`. The XeTeX/xdvipdfmx output has 46 pages (previously 45).
- Final LaTeX log: no errors, undefined citations/references, overfull boxes or
  rerun-required warnings. BibTeX log has no warnings. Non-fatal underfull-box
  and font/inputenc notices remain. The PDF has no unresolved `??` markers.
- Rendered all pages for a layout overview and inspected the edited passages,
  Table 1 and bibliography at readable size; no clipping or overlap found.
- All 29 bibliography entries are cited; no `\nocite`; all four M4 keys are
  absent from both the active bibliography and manuscript.
- Independently compared the ignored predictions parquet to SQLite: repository
  names, README statuses, prediction statuses and scores match. The event panel
  and 20,000-account sample have identical account membership, contained in the
  full preactivity account file.

SHA-256 of the local audit inputs (to identify the ignored files used):

```text
837f0b1d8f9c89d365edfc9bf60a55977b7ec602690eb37b75350f0c37435fe3  data/sector_recovery/bangladesh_full_preactivity_stats.parquet
3f86ed1caf85829e4d2bb1b04506a2fe5ffc9c8388fa1c8fd41ed5d8d1ddbfbd  data/sector_recovery/bd_preactive20000_repo_event_day_metadata.parquet
dc0773b7b55b1cdb7390decc72693947ec68836e35faf247e56210ad1f19faff  data/sector_recovery/repo_sector.sqlite
```
