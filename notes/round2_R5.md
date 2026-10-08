# R5 — August 4–7 (2026-10-08)

Cloudflare documents mobile disconnection on August 4 (07:30–08:15 UTC across the observed providers), a nationwide fall around 04:30 UTC August 5, and recovery that morning (broadband around 07:20, mobile around 08:00 UTC). The initial holiday announcement covered August 5–7. BSS's August 5 report relays ISPR's announcement that offices and institutions would open August 6. An announcement to reopen is not proof that every institution actually reopened.

Conflict: the country-day holiday panel still marks August 5, 6 and 7 as Public Holiday; panel_clean also retains August 6–7 holiday flags. Preserve both source data sets. The alternative treats August 6–7 as ordinary days and keeps August 5. `analysis/round2/r5_holidays.py` writes the old and alternative labels and both DiDs to NEW files. Neither the primary May 1–July 23 DiD nor its holiday exclusion uses August observations: ATT remains -13.087502 and -13.379098 pp, respectively. The weekly event study uses all days, and sector recovery does not exclude holidays. No published holiday-based estimate depends on the disputed August labels.

Figure 1 and Section 6.5 now identify the second shutdown and concurrent events; they do not assign its entire decline to either holidays or connectivity. Primary dates, data, outcomes and estimates unchanged.

Sources actually opened:
- https://blog.cloudflare.com/q3-2024-internet-disruption-summary/
- https://www.bssnews.net/news/top-news/202726
- https://bangladeshnews.live/national/news/general-holiday-for-three-consecutive-days-from-tomorrow
