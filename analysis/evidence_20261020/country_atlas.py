"""Every country and repository domain, including unsupported small cells.

Descriptive plots only: no refitting, donor exclusions, sample changes or new
causal estimates. Cohorts are exactly the frozen historical_readme_080 groups.
"""
from pathlib import Path
import importlib.util
import json
import numpy as np
import pandas as pd
import db_dtypes
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/evidence_20261020"
FIG = ROOT / "paper/latex/figures"
TEX = ROOT / "paper/latex/sections"
NAMES = {"11": "Agriculture", "21": "Mining", "22": "Utilities", "23": "Construction",
         "31-33": "Manufacturing", "42": "Wholesale", "44-45": "Retail", "48-49": "Transport",
         "51": "Information", "52": "Finance", "53": "Real estate", "54": "Professional services",
         "56": "Administrative support", "61": "Education", "62": "Health",
         "71": "Arts and recreation", "72": "Accommodation and food", "81": "Other services",
         "92": "Public administration", "Unclassified": "Unclassified"}


def panel(ax, dates, rate, country, n, ymax):
    color = "#1c4b68" if country == "Bangladesh" else "#466774"
    ax.axvspan(pd.Timestamp("2024-07-18"), pd.Timestamp("2024-07-24"), color="#d6d6d6", alpha=.65, lw=0)
    if n:
        ax.plot(dates, rate, color="#9a9a9a", lw=.45, alpha=.8)
        ax.plot(dates, pd.Series(rate).rolling(7, min_periods=7).mean(), color=color,
                lw=1.2, ls="-" if n >= 30 else "--")
    else:
        ax.text(.5, .5, "No assigned users", transform=ax.transAxes, ha="center", va="center", fontsize=7.5)
    ax.set_title(f"{country}  (N={n:,})", fontsize=8, loc="left", fontweight="bold" if country == "Bangladesh" else "normal")
    ax.set_ylim(0, ymax)
    ax.set_xlim(dates[0], dates[-1])
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.tick_params(labelsize=7, length=2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dddddd", lw=.4)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Serif", "axes.labelsize": 9, "pdf.fonttype": 42})
    members = pd.read_parquet(ROOT / "results/advisor_20261019/sector_membership_historical_readme_080.parquet")
    members.group = members.group.astype(str)
    countries = ["Bangladesh"] + sorted(x for x in members.country.unique() if x != "Bangladesh")
    dates = pd.date_range("2024-05-01", "2024-09-04")
    ns = members.groupby(["group", "country"]).size().unstack(fill_value=0).reindex(index=NAMES, columns=countries, fill_value=0)
    ns.rename_axis("domain_code").to_csv(OUT / "country_domain_counts.csv")
    d = pd.read_parquet(ROOT / "data/processed/github_activity_international_enriched.parquet")
    d.date = pd.to_datetime(d.date)
    d = d.merge(members[["country", "login", "group"]], on=["country", "login"], validate="many_to_one")
    d["active"] = d.productive_events.gt(0)
    numerator = d.groupby(["group", "country", "date"]).active.sum()
    ix = pd.MultiIndex.from_product([list(NAMES), countries, dates], names=["group", "country", "date"])
    grid = numerator.reindex(ix, fill_value=0).rename("active_users").reset_index()
    grid = grid.merge(ns.stack().rename("eligible_users").reset_index(), on=["group", "country"], validate="many_to_one")
    grid["rate_pct"] = 100 * grid.active_users / grid.eligible_users.replace(0, np.nan)
    assert len(grid) == 20 * 15 * 127
    national = d.groupby(["country", "date"]).active.sum()
    grouped = grid.groupby(["country", "date"]).active_users.sum()
    assert np.allclose(grouped, national.reindex(grouped.index, fill_value=0))
    grid.to_parquet(OUT / "country_domain_daily.parquet", index=False)
    # Reproduce every stored main-variant synthetic path from the published weights.
    weights = pd.read_csv(ROOT / "results/advisor_20261019/sector_sc_weights.csv", dtype={"code": str})
    paths = pd.read_csv(ROOT / "results/advisor_20261019/sector_sc_paths.csv", dtype={"code": str}, parse_dates=["date"])
    errors = []
    for code, z in weights[weights.variant.eq("historical_readme_080")].groupby("code"):
        wide = grid[grid.group.eq(code)].pivot(index="date", columns="country", values="rate_pct")
        w = z.set_index("country").weight
        expected = paths[paths.variant.eq("historical_readme_080") & paths.code.eq(code)].set_index("date")
        errors.append(float(np.abs(wide[w.index] @ w - expected.synthetic).max()))
        assert np.allclose(wide.Bangladesh, expected.actual)
    assert max(errors) < 1e-9
    with PdfPages(FIG / "fig_evidence_country_sectors.pdf") as pdf:
        for code, name in NAMES.items():
            fig, axes = plt.subplots(5, 3, figsize=(8.1, 9.1), sharex=True, sharey=True)
            z = grid[grid.group.eq(code)]
            ymax = max(10, float(np.ceil(z.rate_pct.max() / 10) * 10)) if z.rate_pct.notna().any() else 10
            for ax, country in zip(axes.flat, countries):
                x = z[z.country.eq(country)].sort_values("date")
                panel(ax, dates, x.rate_pct.to_numpy(), country, int(ns.loc[code, country]), ymax)
            fig.supylabel("Daily active users (% of fixed country-domain cohort)", x=.005, fontsize=9)
            fig.supxlabel("2024 (UTC)", y=.008, fontsize=9)
            fig.tight_layout(pad=1.3, rect=(.02, .02, 1, 1))
            pdf.savefig(fig)
            plt.close(fig)
    totals = members.groupby("country").size()
    fig, axes = plt.subplots(5, 3, figsize=(8.1, 9.1), sharex=True, sharey=True)
    national_max = max(float(100 * national.loc[c].max() / totals[c]) for c in countries)
    national_ymax = float(np.ceil(national_max / 5) * 5)
    for ax, country in zip(axes.flat, countries):
        rate = 100 * national.loc[country].reindex(dates, fill_value=0) / totals[country]
        panel(ax, dates, rate.to_numpy(), country, int(totals[country]), national_ymax)
    fig.supylabel("Daily active users (% of fixed eligible country cohort)", x=.005, fontsize=9)
    fig.supxlabel("2024 (UTC)", y=.008, fontsize=9)
    fig.tight_layout(pad=1.3, rect=(.02, .02, 1, 1))
    fig.savefig(FIG / "fig_evidence_country_national.pdf")
    plt.close(fig)
    # A numeric support matrix exposes missing/small cells instead of hiding them.
    fig, ax = plt.subplots(figsize=(10, 7.2))
    ax.imshow(np.log10(1 + ns.to_numpy()), cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(countries)), countries, rotation=55, ha="right", fontsize=8)
    ax.set_yticks(range(len(NAMES)), list(NAMES.values()), fontsize=8)
    for i in range(len(NAMES)):
        for j in range(len(countries)):
            n = int(ns.iloc[i, j])
            ax.text(j, i, str(n), ha="center", va="center", fontsize=6.5,
                    color="white" if n >= 500 else "#222222")
    ax.tick_params(length=0)
    fig.tight_layout()
    fig.savefig(FIG / "fig_evidence_country_domain_support.pdf")
    plt.close(fig)
    tex = [
        r"\subsection{Country-by-country activity and complete domain coverage}",
        r"\label{app:country_atlas}",
        "The following figures show every country and every defined repository domain, including cells that do not qualify for a synthetic-control estimate. Cohorts and denominators are fixed before July 18 using the historical-text assignment described in Section~\\ref{sec:international_sector_data}. A small or empty cell is shown explicitly; it is not replaced by a zero causal effect. These plots describe measured public activity and do not identify employment industries.",
        r"\begin{figure}[H]\centering",
        r"\caption{Eligible accounts by country and pre-treatment repository domain}",
        r"\label{fig:country_domain_support}",
        r"\includegraphics[width=\textwidth]{fig_evidence_country_domain_support.pdf}",
        r"\fignote{Numbers are fixed cohort sizes. Colour represents $\log_{10}(1+N)$ for readability. All 59,158 eligible users are assigned exactly once, including the unclassified group. The existing estimation screen requires at least 30 Bangladesh users and five donor countries with at least 30 users each; these descriptive figures apply no such deletion.}",
        r"\end{figure}\clearpage",
        r"\begin{figure}[p]\centering",
        r"\caption{Daily public activity in Bangladesh and every donor country}",
        r"\label{fig:country_national}",
        r"\includegraphics[width=\textwidth,height=.81\textheight,keepaspectratio]{fig_evidence_country_national.pdf}",
        r"\fignote{Thin grey lines: daily rates; coloured lines: trailing seven-day means, shown only after seven observations. Grey shading: July 18--23. All days and rates use UTC and the original country denominators. The smoothing is descriptive and is not used to re-estimate the primary model.}",
        r"\end{figure}\clearpage",
    ]
    for page, (code, name) in enumerate(NAMES.items(), 1):
        tex.extend([
            r"\begin{figure}[p]\centering",
            rf"\caption{{Country-by-country public activity: {name}}}",
            rf"\label{{fig:atlas_{code}}}",
            rf"\includegraphics[page={page},width=\textwidth,height=.81\textheight,keepaspectratio]{{fig_evidence_country_sectors.pdf}}",
            r"\fignote{Fixed historical-README cohort, confidence threshold 0.80. Thin grey: daily rates; coloured: trailing seven-day mean. Dashed means indicate fewer than 30 users; empty cells have no assigned users. Scales are common across countries on this page but may differ across domains. Grey shading: July 18--23. The outcome counts each assigned user's primary activity anywhere on GitHub, not only activity in the repository used for assignment.}",
            r"\end{figure}\clearpage",
        ])
    (TEX / "appendix_country_atlas.tex").write_text("\n\n".join(tex) + "\n")
    summary = dict(countries=len(countries), domains=len(NAMES), panels=len(countries)*len(NAMES),
                   dates=len(dates), zero_cells=int((ns == 0).sum().sum()),
                   small_nonzero_cells=int(((ns > 0) & (ns < 30)).sum().sum()),
                   max_synthetic_path_difference=max(errors), users=int(ns.sum().sum()))
    (OUT / "country_atlas_validation.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
