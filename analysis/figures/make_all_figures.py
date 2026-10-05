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

    fig, ax = plt.subplots(figsize=(FULL_W, 2.9))
    shade_shutdown(ax)
    ax.plot(d.date, d.Bangladesh, color=BD, label="Bangladesh (actual)")
    ax.plot(d.date, d.Synthetic_Control, color=COMP, ls="--",
            label="Synthetic Bangladesh")
    ax.set_ylabel("Eligible users with productive\nGitHub activity (%)")
    ax.set_ylim(0, max(d.Bangladesh.max(), d.Synthetic_Control.max()) * 1.08)
    ax.set_xlim(d.date.min() - HALF_DAY, d.date.max() + HALF_DAY)
    date_axis(ax)
    ax.grid(axis="y", color="#DDDDDD", lw=0.5)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--png-dir", type=Path, default=None)
    args = ap.parse_args()
    fig_sc_actual_vs_synthetic(args.png_dir)
    fig_sc_placebos(args.png_dir)
    fig_mechanism_release(args.png_dir)


if __name__ == "__main__":
    main()
