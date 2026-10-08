#!/usr/bin/env python3
"""
Create advisor-ready sector recovery outputs from the three classifier thresholds.

Inputs expected:
  results/sector_recovery/sectorwide/
  results/sector_recovery/sectorwide_070/
  results/sector_recovery/sectorwide_090/

Main specification:
  historical README + classifier score >= 0.80

Main sectors:
  Finance
  Information
  Education
  Health
  Retail
  Accommodation & Food
  Real Estate

Professional/Scientific and Administrative Support are kept in robustness tables
but excluded from the main figure because the >=0.90 classifier threshold sharply
reduces support (125 and 48 pre users respectively).
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path("results/sector_recovery")
OUT = ROOT / "final"
OUT.mkdir(parents=True, exist_ok=True)

PATHS = {
    "0.70": ROOT / "sectorwide_070",
    "0.80": ROOT / "sectorwide",
    "0.90": ROOT / "sectorwide_090",
}

MAIN_SECTORS = [
    "Finance and Insurance",
    "Information",
    "Educational Services",
    "Health Care and Social Assistance",
    "Retail Trade",
    "Accommodation and Food Services",
    "Real Estate and Rental",
]

ALL_SECTORS = [
    "Finance and Insurance",
    "Information",
    "Educational Services",
    "Professional, Scientific, Technical Services",
    "Health Care and Social Assistance",
    "Retail Trade",
    "Accommodation and Food Services",
    "Real Estate and Rental",
    "Administrative and Support Services",
]

SHORT = {
    "Finance and Insurance": "Finance",
    "Information": "Information",
    "Educational Services": "Education",
    "Professional, Scientific, Technical Services": "Professional/Scientific",
    "Health Care and Social Assistance": "Health",
    "Retail Trade": "Retail",
    "Accommodation and Food Services": "Accommodation/Food",
    "Real Estate and Rental": "Real Estate",
    "Administrative and Support Services": "Admin Support",
}

# -----------------------
# Load summaries
# -----------------------
summaries = {}
events = {}

for thr, folder in PATHS.items():
    s = pd.read_csv(folder / "sectorwide_recovery_summary.csv")
    s["threshold"] = thr
    summaries[thr] = s

    if thr == "0.80":  # only the main threshold's event study is used below
        e = pd.read_csv(folder / "sectorwide_user_eventstudy.csv")
        e["threshold"] = thr
        events[thr] = e

long_summary = pd.concat(summaries.values(), ignore_index=True)
long_summary.to_csv(OUT / "sector_threshold_robustness_full.csv", index=False)

# -----------------------
# Main table (.80)
# -----------------------
main = summaries["0.80"].copy()
main = main[main["sector"].isin(MAIN_SECTORS)].copy()
main["sector_label"] = main["sector"].map(SHORT)

main = main[[
    "sector", "sector_label", "pre_users",
    "shutdown_recovery_index",
    "week1_recovery_index",
    "week2_recovery_index",
    "week4_recovery_index",
    "week8_recovery_index",
    "first_week_ge_80",
    "first_sustained2_ge_80",
]].copy()

for c in [
    "shutdown_recovery_index", "week1_recovery_index",
    "week2_recovery_index", "week4_recovery_index",
    "week8_recovery_index"
]:
    main[c] = main[c].round(1)

main.to_csv(OUT / "table_sector_recovery_main.csv", index=False)

# LaTeX advisor-ready table
latex = main.rename(columns={
    "sector_label": "Sector",
    "pre_users": "Pre users",
    "shutdown_recovery_index": "Shutdown",
    "week1_recovery_index": "Week +1",
    "week2_recovery_index": "Week +2",
    "week4_recovery_index": "Week +4",
    "week8_recovery_index": "Week +8",
    "first_sustained2_ge_80": "Sustained >=80%",
})[[
    "Sector", "Pre users", "Shutdown", "Week +1", "Week +2",
    "Week +4", "Week +8", "Sustained >=80%"
]]

latex_text = latex.to_latex(
    index=False,
    escape=True,
    na_rep="--",
    float_format=lambda x: f"{x:.1f}",
    caption=(
        "Sectoral recovery of observable GitHub PushEvent activity. "
        "Recovery indices normalize each sector's mean activity over the final "
        "eight pre-shutdown weeks to 100."
    ),
    label="tab:sector_recovery",
)
(OUT / "table_sector_recovery_main.tex").write_text(latex_text, encoding="utf-8")

# -----------------------
# Threshold robustness table
# -----------------------
rob_rows = []
for thr, s in summaries.items():
    for _, r in s[s["sector"].isin(ALL_SECTORS)].iterrows():
        rob_rows.append({
            "sector": SHORT.get(r["sector"], r["sector"]),
            "threshold": thr,
            "pre_users": r["pre_users"],
            "week1": r["week1_recovery_index"],
            "week4": r["week4_recovery_index"],
            "week8": r["week8_recovery_index"],
            "sustained80": r["first_sustained2_ge_80"],
        })

rob = pd.DataFrame(rob_rows)
rob.to_csv(OUT / "table_sector_threshold_robustness_long.csv", index=False)

# -----------------------
# Main recovery-index figure
# -----------------------
e80 = events["0.80"]
plot = e80[
    e80["sector"].isin(MAIN_SECTORS)
    & e80["event_time"].between(-8, 8)
].copy()

fig, ax = plt.subplots(figsize=(11, 7))
for sector in MAIN_SECTORS:
    g = plot[plot["sector"].eq(sector)].sort_values("event_time")
    ax.plot(
        g["event_time"],
        g["recovery_index"],
        marker="o",
        label=SHORT[sector],
    )

ax.axhline(100, linewidth=1)
ax.axvline(0, linewidth=1, linestyle="--")
ax.set_xlabel("Event time (0 = Jul 18-23 shutdown; +1 = Jul 24-30)")
ax.set_ylabel("Recovery index (8-week pre-shutdown mean = 100)")
ax.set_title("Recovery of observable software activity by repository sector")
ax.legend(fontsize=9, ncol=2)
fig.tight_layout()
fig.savefig(OUT / "figure_sector_recovery_index_main.png", dpi=300)
plt.close(fig)

# -----------------------
# Advisor-style coefficient plots
# one file per sector
# -----------------------
for sector in MAIN_SECTORS:
    g = e80[
        e80["sector"].eq(sector)
        & e80["event_time"].between(-8, 8)
    ].sort_values("event_time")

    fig, ax = plt.subplots(figsize=(9, 5.4))
    ax.errorbar(
        g["event_time"],
        g["beta_vs_pre8_pp"],
        yerr=1.959963984540054 * g["se_pp"],
        fmt="o",
        capsize=3,
    )
    ax.axhline(0, linewidth=1)
    ax.axvline(0, linewidth=1, linestyle="--")
    ax.set_xlabel("Event time (0 = shutdown; +1 = first week after restoration)")
    ax.set_ylabel("Change from 8-week pre-shutdown mean (percentage points)")
    ax.set_title(f"Sector recovery event study: {SHORT[sector]}")
    fig.tight_layout()

    safe = (
        SHORT[sector]
        .replace("/", "_")
        .replace(" ", "_")
        .replace("&", "and")
    )
    fig.savefig(OUT / f"figure_eventstudy_{safe}.png", dpi=300)
    plt.close(fig)

# -----------------------
# Compact interpretation audit
# -----------------------
audit = rob.pivot(
    index="sector",
    columns="threshold",
    values=["pre_users", "week1", "week8", "sustained80"],
)
audit.to_csv(OUT / "table_sector_threshold_robustness_wide.csv")

print("\nMAIN TABLE (.80)")
print(main.to_string(index=False))

print("\nROBUSTNESS CHECK")
for sector in [SHORT[s] for s in MAIN_SECTORS]:
    z = rob[rob["sector"].eq(sector)].sort_values("threshold")
    print("\n", sector)
    print(z[["threshold", "pre_users", "week1", "week4", "week8", "sustained80"]].to_string(index=False))

print("\nSaved advisor-ready outputs in:", OUT)
for p in sorted(OUT.iterdir()):
    print(" ", p)
