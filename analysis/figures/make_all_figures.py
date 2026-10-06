"""Regenerate every manuscript figure from stored repository outputs.

Usage (from the repository root):

    python analysis/figures/make_all_figures.py [--png-dir DIR]

Figures are written as vector PDFs to paper/latex/figures/. The optional
--png-dir flag additionally writes PNG previews to DIR.

This script only reads existing result files; it does not re-estimate any
specification. Each figure checks the numbers it plots against
results/final/ (or the documented source file) and stops if they disagree.

Requirements: pandas, matplotlib, pyarrow (for Figure 3).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
OUT = REPO / "paper" / "latex" / "figures"

# Treatment window (CLAUDE.md): July 18-23, 2024 inclusive.
SHUT_START = pd.Timestamp("2024-07-18")
SHUT_END = pd.Timestamp("2024-07-23")
HALF_DAY = pd.Timedelta(hours=12)

# Consistent style: one accent colour for Bangladesh, greys for comparisons.
BD = "#1F4E79"
COMP = "#6E6E6E"
SHADE = "#E6E6E6"
FULL_W = 6.5  # inches, equals \textwidth with 1in margins on US letter

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "lines.linewidth": 1.4,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    }
)


def check(label: str, got: float, expected: float, tol: float = 1e-3) -> None:
    if not np.isclose(got, expected, atol=tol):
        raise AssertionError(f"{label}: plotted value {got} != verified value {expected}")


def shade_shutdown(ax, label: bool = True) -> None:
    """Grey band covering the daily observations July 18-23 and an onset marker."""
    ax.axvspan(SHUT_START - HALF_DAY, SHUT_END + HALF_DAY, color=SHADE, zorder=0, lw=0,
               label="Shutdown window (Jul 18–23)" if label else None)
    ax.axvline(SHUT_START - HALF_DAY, color="black", lw=0.8, ls=":", zorder=1)


def date_axis(ax, interval: int = 7) -> None:
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))


def save(fig, name: str, png_dir: Path | None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    if png_dir is not None:
        png_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_dir / f"{name}.png", dpi=200)
    plt.close(fig)
    print(f"wrote {OUT.relative_to(REPO) / (name + '.pdf')}")


# ---------------------------------------------------------------------------
# Figure 1: actual vs synthetic Bangladesh
# ---------------------------------------------------------------------------
def fig_sc_actual_vs_synthetic(png_dir):
    d = pd.read_csv(RES / "synthetic_control" / "actual_vs_synthetic_daily.csv",
                    parse_dates=["date"])
    shut = d[(d.date >= SHUT_START) & (d.date <= SHUT_END)]
    pre = d[d.date < SHUT_START]
    # Verified against results/final/FINAL_COPY_READY_RESULTS.txt and
    # results/final/table_primary_SC_leave_one_out.csv (zero-weight donor rows).
    check("SC actual", shut.Bangladesh.mean(), 2.021)
    check("SC counterfactual", shut.Synthetic_Control.mean(), 15.277)
    loo = pd.read_csv(RES / "final" / "table_primary_SC_leave_one_out.csv")
    base = loo.loc[loo.removed == "Indonesia"].iloc[0]  # zero weight => baseline
    check("SC ATT", (shut.Bangladesh - shut.Synthetic_Control).mean(), base.ATT)
    check("SC pre RMSPE",
          np.sqrt(((pre.Bangladesh - pre.Synthetic_Control) ** 2).mean()), base.pre_RMSPE)

    # Descriptive extension through September 4 with the archived weights, from
    # analysis/synthetic_control/01_reproduce_sc.py; must match the archived
    # daily series wherever both exist (May 1 - July 23).
    full = pd.read_csv(RES / "synthetic_control" / "reproduced" / "sc_daily_path_full.csv",
                       parse_dates=["date"])
    both = full.merge(d, on="date", suffixes=("", "_arch"))
    check("extended path vs archived (max abs diff)",
          (both.Synthetic_Control - both.Synthetic_Control_arch).abs().max(), 0.0, 1e-3)
    check("extended actual vs archived (max abs diff)",
          (both.Bangladesh - both.Bangladesh_arch).abs().max(), 0.0, 1e-9)

    restore_start = SHUT_END + pd.Timedelta(days=1)
    fig, ax = plt.subplots(figsize=(FULL_W, 3.0))
    shade_shutdown(ax)
    ax.axvspan(restore_start - HALF_DAY, full.date.max() + HALF_DAY, color="#E8EFF6", zorder=0,
               lw=0, label="Post-restoration (descriptive)")
    ax.plot(full.date, full.Bangladesh, color=BD, label="Bangladesh (actual)")
    ax.plot(full.date, full.Synthetic_Control, color=COMP, ls="--",
            label="Synthetic Bangladesh")
    ax.set_ylabel("Eligible users with productive\nGitHub activity (%)")
    ax.set_ylim(0, max(full.Bangladesh.max(), full.Synthetic_Control.max()) * 1.08)
    ax.set_xlim(full.date.min() - HALF_DAY, full.date.max() + HALF_DAY)
    date_axis(ax, interval=14)
    ax.grid(axis="y", color="#DDDDDD", lw=0.5)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    save(fig, "fig1_sc_actual_vs_synthetic", png_dir)


# ---------------------------------------------------------------------------
# Figure 2: in-space placebo inference (post/pre RMSPE ratio)
# ---------------------------------------------------------------------------
def fig_sc_placebos(png_dir):
    p = pd.read_csv(RES / "synthetic_control" / "sc_inspace_placebos.csv")
    final = pd.read_csv(RES / "final" / "table_primary_SC_placebos.csv")
    merged = p.merge(final, on="country", suffixes=("", "_final"))
    if len(merged) != 14:
        raise AssertionError("expected 14 donor placebos")
    for _, r in merged.iterrows():
        check(f"placebo ratio {r.country}", r.RMSPE_ratio, r.RMSPE_ratio_final, 1e-5)
        check(f"placebo ATT {r.country}", r.ATT, r.ATT_final, 1e-5)
    bd = p.loc[p.country == "Bangladesh"].iloc[0]
    check("BD RMSPE ratio", bd.RMSPE_ratio, 4.192)
    n_units = len(p)
    rank_ratio = (p.RMSPE_ratio >= bd.RMSPE_ratio).sum() / n_units
    rank_att = (p.ATT.abs() >= abs(bd.ATT)).sum() / n_units
    check("ratio rank p", rank_ratio, 1 / 15, 1e-9)
    check("ATT rank p", rank_att, 1 / 15, 1e-9)

    p = p.sort_values("RMSPE_ratio")
    y = np.arange(len(p))
    is_bd = (p.country == "Bangladesh").to_numpy()
    colors = np.where(is_bd, BD, COMP)

    fig, ax = plt.subplots(figsize=(FULL_W, 3.3))
    ax.hlines(y, 0, p.RMSPE_ratio, color=colors, lw=1.4)
    ax.scatter(p.RMSPE_ratio, y, color=colors, s=22, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(p.country)
    for lab, b in zip(ax.get_yticklabels(), is_bd):
        if b:
            lab.set_fontweight("bold")
            lab.set_color(BD)
    ax.annotate(f"{bd.RMSPE_ratio:.2f}", (bd.RMSPE_ratio, y[is_bd][0]),
                xytext=(5, -3), textcoords="offset points", fontsize=8, color=BD)
    ax.set_xlim(0, p.RMSPE_ratio.max() * 1.12)
    ax.set_ylim(-0.7, len(p) - 0.3)
    ax.set_xlabel("Post/pre-treatment RMSPE ratio")
    ax.grid(axis="x", color="#DDDDDD", lw=0.5)
    save(fig, "fig2_sc_placebo_rmspe_ratio", png_dir)


# ---------------------------------------------------------------------------
# Figure 3: release timing of blackout-authored commits
# ---------------------------------------------------------------------------
def fig_mechanism_release(png_dir):
    m = pd.read_parquet(
        RES / "mechanism" / "commit_sha_author_push_master.parquet",
        columns=["found", "authored_time", "author_equals_pusher", "author_to_push_hours",
                 "authored_during_blackout", "offline_author_backlog", "push_time"],
    )
    strict = m[m.found & m.authored_time.notna()
               & m.author_equals_pusher.fillna(False).astype(bool)
               & (m.author_to_push_hours >= 0)]
    c = strict[strict.authored_during_blackout].copy()
    main = pd.read_csv(RES / "final" / "table_mechanism_main.csv").set_index("timestamp")
    check("strict sample N", len(strict), 59920, 0)
    check("blackout N", len(c), main.loc["authoredDate", "N_blackout"], 0)
    check("backlog N", c.offline_author_backlog.sum(), main.loc["authoredDate", "backlog_N"], 0)

    c["push_day"] = pd.to_datetime(c.push_time.dt.tz_convert("UTC").dt.date)
    daily = c.groupby(["push_day", "offline_author_backlog"]).size().unstack(fill_value=0)
    daily = daily.reindex(pd.date_range(daily.index.min(), daily.index.max()), fill_value=0)
    rel = pd.read_csv(RES / "mechanism" / "backlog_release_dates.csv", parse_dates=["push_date"])
    stored = rel.set_index("push_date").blackout_authored_commits_pushed
    if not daily[True][daily[True] > 0].equals(stored.rename(True).astype(daily[True].dtype)):
        raise AssertionError("backlog release dates differ from backlog_release_dates.csv")

    n = len(c)
    cum = daily.sum(axis=1).cumsum() / n * 100
    share_after = daily[True].sum() / n * 100
    check("backlog share", share_after, main.loc["authoredDate", "backlog_pct"])

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(FULL_W, 2.7), sharex=True)
    for ax in (a1, a2):
        shade_shutdown(ax, label=False)
        date_axis(ax)
    a1.bar(daily.index, daily[False], width=0.8, color=COMP,
           label="First pushed Jul 18–23")
    a1.bar(daily.index, daily[True], width=0.8, color=BD,
           label="First pushed on/after Jul 24")
    a1.set_ylabel("Commits (first public push)")
    a1.set_ylim(0, None)
    a1.set_title("(a) Date of first public push", loc="left")
    a1.legend(loc="upper right")

    a2.step(cum.index, cum.values, where="post", color=BD)
    a2.axhline(100 - share_after, color=COMP, lw=0.6, ls="--")
    xb = pd.Timestamp("2024-08-06")
    a2.annotate("", xy=(xb, 100), xytext=(xb, 100 - share_after),
                arrowprops=dict(arrowstyle="<->", color="#333333", lw=0.7))
    a2.text(xb - pd.Timedelta(days=0.6), 100 - share_after / 2,
            f"{share_after:.2f}% first\npushed on or\nafter Jul 24",
            ha="right", va="center", fontsize=8)
    a2.text(pd.Timestamp("2024-07-24"), 100 - share_after - 3,
            f"{100 - share_after:.2f}% pushed by Jul 23", ha="left", va="top",
            fontsize=8, color=COMP)
    a2.set_ylim(0, 102)
    a2.set_ylabel("Cumulative share pushed (%)")
    a2.set_title("(b) Cumulative release", loc="left")
    a2.set_xlim(daily.index.min() - HALF_DAY, daily.index.max() + HALF_DAY)
    fig.tight_layout(w_pad=2)
    save(fig, "fig4_mechanism_release", png_dir)


# ---------------------------------------------------------------------------
# SC in-time (backdated) placebos
# ---------------------------------------------------------------------------
def fig_sc_intime_placebos(png_dir):
    p = pd.read_csv(RES / "synthetic_control" / "reproduced" / "sc_intime_placebos.csv",
                    parse_dates=["start", "end"]).sort_values("start")
    real = p[p.type == "real"].iloc[0]
    plc = pd.read_csv(RES / "synthetic_control" / "sc_inspace_placebos.csv").set_index("country")
    check("in-time real ATT = archived", real.ATT, plc.loc["Bangladesh", "ATT"], 1e-4)
    labels = [f"{s:%b %-d}–{e:%b %-d}" for s, e in zip(p.start, p.end)]
    is_real = (p.type == "real").to_numpy()
    colors = np.where(is_real, BD, COMP)
    y = np.arange(len(p))

    fig, ax = plt.subplots(figsize=(FULL_W, 2.9))
    ax.axvline(0, color="black", lw=0.6)
    ax.hlines(y, 0, p.ATT, color=colors, lw=1.4)
    ax.scatter(p.ATT, y, color=colors, s=22, zorder=3)
    for yi, (att, hol) in enumerate(zip(p.ATT, p.bd_holidays_in_window.fillna(""))):
        txt = f"{att:.2f}".replace("-", "−") + (" (holiday)" if hol else "")
        ax.annotate(txt, (att, yi), xytext=(5 if att >= 0 else -5, -3), textcoords="offset points",
                    ha="left" if att >= 0 else "right", fontsize=7.5,
                    color=BD if is_real[yi] else "#333333")
    ax.set_yticks(y)
    ax.set_yticklabels([("Actual shutdown, " if r else "") + l for l, r in zip(labels, is_real)])
    for lab, r in zip(ax.get_yticklabels(), is_real):
        if r:
            lab.set_color(BD)
            lab.set_fontweight("bold")
    ax.set_xlim(p.ATT.min() - 3.5, p.ATT.max() + 3.5)
    ax.set_xlabel("Synthetic-control ATT over the six-day window (pp)")
    ax.grid(axis="x", color="#DDDDDD", lw=0.5)
    save(fig, "figA1_sc_intime_placebos", png_dir)


# ---------------------------------------------------------------------------
# International DiD event study (weekly, in-space placebo intervals)
# ---------------------------------------------------------------------------
def fig_did_eventstudy(png_dir):
    es = pd.read_csv(RES / "did" / "did_eventstudy_weekly.csv")
    did = pd.read_csv(RES / "final" / "table_DiD_all_outcomes.csv")
    att = did[(did.outcome == "active_rate_pp") & ~did.remove_holidays].ATT.iloc[0]
    check("event week 0 = archived DiD ATT", es.loc[es.event_week == 0, "theta_pp"].iloc[0], att, 1e-9)
    pre = es[es.event_week < 0]

    fig, ax = plt.subplots(figsize=(FULL_W, 3.0))
    ax.axvspan(-0.5, 0.5, color=SHADE, lw=0, zorder=0, label="Shutdown (Jul 18–23)")
    ax.axhline(0, color="black", lw=0.6)
    for i, v in enumerate([pre.theta_pp.min(), pre.theta_pp.max()]):
        ax.axhline(v, color=COMP, lw=0.7, ls=":",
                   label="Range of pre-shutdown weekly estimates" if i == 0 else None)
    ax.vlines(es.event_week, es.ci_low_pp, es.ci_high_pp, color=BD, lw=1.0,
              label="Donor-placebo reference interval")
    ax.plot(es.event_week, es.theta_pp, "o", color=BD, ms=4, label="Bangladesh − donor mean")
    ax.annotate(f"{att:.2f}".replace("-", "−"), (0, att), xytext=(6, -2), textcoords="offset points",
                fontsize=8, color=BD)
    ax.set_xticks(es.event_week)
    ax.set_xlabel("Event week (0 = July 18–23; +1 = July 24–30)")
    ax.set_ylabel("Change relative to pre-period,\nBangladesh minus donors (pp)")
    ax.grid(axis="y", color="#DDDDDD", lw=0.5)
    ax.legend(loc="lower left", ncol=1)
    save(fig, "fig3_did_eventstudy", png_dir)


# ---------------------------------------------------------------------------
# RDiT: daily series around the July 17 cutoff (archived preferred design)
# ---------------------------------------------------------------------------
RD_CUT = pd.Timestamp("2024-07-17")
RD_BW = 7


def fig_rdit(png_dir):
    # Series and design recovered by analysis/rdit/01_reproduce_rdit.py, which
    # reproduces results/rdit/main_rdit_summary.csv exactly.
    s = pd.read_csv(RES / "rdit" / "rdit_daily_series.csv", parse_dates=["date"]).set_index("date")
    arch = pd.read_csv(RES / "rdit" / "main_rdit_summary.csv").set_index("specification")
    win_lo, win_hi = RD_CUT - pd.Timedelta(days=RD_BW), RD_CUT + pd.Timedelta(days=RD_BW)

    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.9), sharey=True)
    for ax, col, spec, title in [
            (axes[0], "bangladesh_pct", "Main local linear", "(a) Bangladesh"),
            (axes[1], "philippines_pct", "Geographic placebo", "(b) Philippines (geographic placebo)")]:
        y = s[col]
        inwin = (y.index >= win_lo) & (y.index <= win_hi)
        ax.axvspan(SHUT_START - HALF_DAY, SHUT_END + HALF_DAY, color=SHADE, zorder=0, lw=0,
                   label="Shutdown (Jul 18–23)")
        ax.plot(y.index[~inwin], y[~inwin], "o", mfc="white", mec=COMP, ms=3.5, mew=0.8)
        ax.plot(y.index[inwin], y[inwin], "o", color=BD, ms=3.5)
        # Local linear fits of the archived design: July 17 (t = 0) is on the post side.
        icpt = {}
        for side, sel in [("pre", inwin & (y.index < RD_CUT)), ("post", inwin & (y.index >= RD_CUT))]:
            t = (y.index[sel] - RD_CUT).days.to_numpy(float)
            b = np.polyfit(t, y[sel].to_numpy(), 1)
            icpt[side] = b[1]
            tt = np.array([0.0, t.max()]) if side == "post" else np.array([t.min(), 0.0])
            ax.plot(RD_CUT + pd.to_timedelta(tt, unit="D"), np.polyval(b, tt), color=BD, lw=1.2)
        check(f"RDiT {spec}", icpt["post"] - icpt["pre"], 100 * arch.loc[spec, "effect"], 1e-4)
        ax.axvline(RD_CUT - HALF_DAY, color="black", lw=0.8, ls="--", label="RDiT cutoff")
        ax.axvline(SHUT_START - HALF_DAY, color="black", lw=0.8, ls=":", label="Shutdown onset")
        ax.set_title(title, loc="left")
        date_axis(ax)
        ax.set_xlim(y.index.min() - HALF_DAY, y.index.max() + HALF_DAY)
        ax.grid(axis="y", color="#DDDDDD", lw=0.5)
    axes[0].set_ylabel("Users with productive\nGitHub activity (%)")
    axes[0].set_ylim(0, None)
    axes[1].legend(loc="lower right")
    fig.tight_layout(w_pad=1.5)
    save(fig, "fig7_rdit_cutoff", png_dir)


# ---------------------------------------------------------------------------
# Figures 5-6: within-Bangladesh sectoral recovery (classifier score >= 0.80)
# ---------------------------------------------------------------------------
SECTOR_DIR = RES / "sector_recovery"
# Main-figure sectors, ordered from fastest to slowest recovery. Professional/
# Scientific and Administrative Support are excluded because their support
# collapses at the 0.90 classifier threshold (see the appendix robustness table).
SECTORS = [
    ("Finance and Insurance", "Finance"),
    ("Information", "Information"),
    ("Educational Services", "Education"),
    ("Health Care and Social Assistance", "Health"),
    ("Retail Trade", "Retail"),
    ("Real Estate and Rental", "Real Estate"),
    ("Accommodation and Food Services", "Accommodation/Food"),
]
FAINT = "#D0D0D0"


def sector_eventstudy() -> pd.DataFrame:
    e = pd.read_csv(SECTOR_DIR / "sectorwide" / "sectorwide_user_eventstudy.csv")
    final = pd.read_csv(SECTOR_DIR / "final" / "table_sector_recovery_main.csv").set_index("sector")
    for sector, _ in SECTORS:
        g = e[e.sector == sector].set_index("event_time")
        r = final.loc[sector]
        for k, col in [(0, "shutdown"), (1, "week1"), (2, "week2"), (4, "week4"), (8, "week8")]:
            check(f"{sector} {col}", round(g.loc[k, "recovery_index"], 1),
                  r[f"{col}_recovery_index"], 1e-9)
    return e


def sector_panels(nrows: int, height: float, sharey: bool):
    fig, axes = plt.subplots(nrows, 4, figsize=(FULL_W, height), sharex=True, sharey=sharey)
    axes = axes.ravel()
    axes[-1].axis("off")
    return fig, axes


def fig_sector_recovery_index(png_dir):
    e = sector_eventstudy()
    e = e[e.event_time.between(-8, 17)]  # full observed window
    top = 200
    fig, axes = sector_panels(2, 3.6, sharey=True)
    for ax, (sector, short) in zip(axes, SECTORS):
        ax.axvspan(-0.5, 0.5, color=SHADE, lw=0, zorder=0)
        ax.axhline(100, color="black", lw=0.6)
        ax.axhline(80, color=COMP, lw=0.6, ls=":")
        for other, _ in SECTORS:
            if other != sector:
                g = e[e.sector == other].sort_values("event_time")
                ax.plot(g.event_time, g.recovery_index, color=FAINT, lw=0.8, zorder=1)
        g = e[e.sector == sector].sort_values("event_time")
        ax.plot(g.event_time, g.recovery_index, color=BD, marker="o", ms=2.5, zorder=3)
        # Label values outside the common axis instead of silently clipping them.
        for r in g[g.recovery_index > top].itertuples():
            ax.annotate(f"{r.recovery_index:.0f}", (r.event_time, top), xytext=(4, -8),
                        textcoords="offset points", fontsize=7, color=BD)
        ax.set_title(short, loc="left")
        ax.set_xticks([-8, 0, 8, 16])
        ax.set_ylim(0, top)
    for ax in axes[4:7]:
        ax.set_xlabel("Event week")
    for ax in axes[[0, 4]]:
        ax.set_ylabel("Recovery index\n(pre-period mean = 100)")
    fig.tight_layout(h_pad=1.2, w_pad=0.8)
    save(fig, "fig5_sector_recovery_index", png_dir)


def fig_sector_eventstudy(png_dir):
    e = sector_eventstudy()
    # Separate y-scales: pre-period activity levels differ roughly sevenfold.
    fig, axes = sector_panels(2, 3.8, sharey=False)
    for ax, (sector, short) in zip(axes, SECTORS):
        g = e[e.sector == sector].sort_values("event_time")
        ax.axvspan(-0.5, 0.5, color=SHADE, lw=0, zorder=0)
        ax.axhline(0, color="black", lw=0.6)
        ax.vlines(g.event_time, g.ci_low_pp, g.ci_high_pp, color=BD, lw=0.8)
        ax.plot(g.event_time, g.beta_vs_pre8_pp, "o", color=BD, ms=2.5)
        ax.set_title(short, loc="left")
        ax.set_xticks([-8, 0, 8, 16])
    for ax in axes[4:7]:
        ax.set_xlabel("Event week")
    for ax in axes[[0, 4]]:
        ax.set_ylabel("Change from pre-period\nmean (pp)")
    fig.tight_layout(h_pad=1.2, w_pad=0.8)
    save(fig, "fig6_sector_eventstudy", png_dir)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--png-dir", type=Path, default=None)
    args = ap.parse_args()
    fig_sc_actual_vs_synthetic(args.png_dir)
    fig_sc_placebos(args.png_dir)
    fig_mechanism_release(args.png_dir)
    fig_did_eventstudy(args.png_dir)
    fig_rdit(args.png_dir)
    fig_sector_recovery_index(args.png_dir)
    fig_sector_eventstudy(args.png_dir)


if __name__ == "__main__":
    main()
