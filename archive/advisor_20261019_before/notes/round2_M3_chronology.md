# M3 — sourced chronology and comparison episodes

Dates are UTC where an hour is specified. Political reports often use Bangladesh local dates (UTC+6); do not assign an exact hour to a date-only report.

| Date/time | Documented event | Source and implication |
|---|---|---|
| July 1, local date | Public-university teacher/staff strike over pension arrangements; student quota demonstrations | UNB July 1 and Daily Star July 2; possible pre-period activity/composition shocks, no evidence identifying their GitHub effect |
| July 15–16, local dates | Escalating clashes during quota protests | Amnesty July 17 evidence report; unrest precedes the total connectivity break |
| July 16–17 | Selective service/social-platform disruption | ISOC Pulse chronology, partly drawing on Cloudflare/IODA; not an independent connectivity measurement |
| July 17 late UTC / July 18 early local | Provider-specific mobile outages | Cloudflare provider traces; nationwide treatment is not a single perfectly simultaneous event |
| July 18, approximately 15:00 UTC | Near-total nationwide connectivity collapse | Cloudflare; onset used for hourly diagnostic and alternative mechanism cohort |
| Night July 19–20 local | Nationwide curfew | Amnesty July 30 letter; country-wide curfew follows total connectivity onset, but unrest already overlaps it |
| July 23, approximately 13:00 UTC | Initial fixed-broadband restoration | Cloudflare; trial restoration, not all accounts reconnected |
| July 27, approximately 00:00 UTC | Later restoration in two fixed networks | Cloudflare provider traces |
| July 28, approximately 09:00 UTC | Mobile connectivity begins returning | Cloudflare |
| July 31, 08:30–10:30 UTC | Pakistan national disruption | Cloudflare; threat to post-period synthetic extrapolation, not part of primary treatment window |

The hourly diagnostic uses the available Bangladesh PushEvents only, with the fixed main cohort denominator 10,241. It is not a redefinition of productive_events. There are 182,808 stored rows, 182,807 unique events (one exact duplicate), and 7,750 distinct actors, all inside the primary cohort. New outputs show zero-filled hourly rates and all ±6/12/24-hour comparisons at the three requested connectivity times. The pre-reference is the July 1–17 same-hour-of-week mean. Only two or three occurrences per weekday/hour, early-July instability, circadian effects, phased restoration and uncertain physical locations limit causal interpretation.

Comparable candidate episodes:
- **Shutdown for exams:** Gunsilius and Van Dijcke study Rajasthan, September 26, 2021, 06:00–18:00 local. The shutdown was for an examination rather than protest suppression. This is a useful design contrast, not proof that all contemporaneous shocks were absent. Their economic outcome and population differ from GitHub; a comparable analysis needs verified Rajasthan users and 2021 events.
- **Unrest without a nationwide shutdown:** Cloudflare reports protests after Venezuela's July 28, 2024 election without an accompanying nationwide shutdown; some websites were blocked and traffic fell organically. This could distinguish national disconnection from unrest, but is not a clean unrestricted-Internet control. The required Venezuela cohort and hourly GitHub observations are absent locally.
- Early-July Bangladesh protests before total disconnection offer another within-country timing contrast, but the July 2 break makes them unsuitable as an automatically valid control.

Sources actually opened and read:
- https://unb.com.bd/category/Bangladesh/university-teachers-begin-indefinite-work-abstention-protesting-discriminatory-pension-scheme/138446
- https://www.thedailystar.net/news/bangladesh/news/pension-protest-brings-public-univs-halt-3646701
- https://www.amnesty.org/en/latest/news/2024/07/bangladesh-witness-testimony-video-and-photographic-analysis-confirm-police-used-unlawful-force-against-protesters/
- https://www.amnesty.org/ru/wp-content/uploads/2024/07/ASA1383722024ENGLISH.pdf
- https://pulse.internetsociety.org/en/shutdowns/internet-suspended-in-bangladesh-18-july-2024/
- https://blog.cloudflare.com/a-recent-spate-of-internet-disruptions-july-2024/
- https://arxiv.org/pdf/2309.14630 (version 3, May 2025; original working paper 2023)
- https://www.gharchive.org/ (hourly archive documentation)

OHCHR's preliminary-report URL was attempted but returned 403; it is not treated as a fully opened source. No political quotation or causal claim is inferred from an unavailable document.
