import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import matplotlib.pyplot as plt

# =============================
# Utility functions
# =============================

def load_commits_data(file_path: str) -> Dict:
    """Load commits data from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def get_week_start_date(date_str: str, reference_start: str = '2024-05-01') -> str:
    """Map a YYYY-MM-DD date to the start-date of its 7-day bin using May 1, 2024 as anchor."""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    ref = datetime.strptime(reference_start, '%Y-%m-%d')
    days_diff = (date - ref).days
    week_number = days_diff // 7
    week_start = ref + timedelta(days=week_number * 7)
    return week_start.strftime('%Y-%m-%d')


def complete_weeks_may_to_sept() -> List[str]:
    """Return sorted list of complete 7-day bins from May 1 to Sep 4, 2024 (inclusive)."""
    start = datetime(2024, 5, 1)
    end = datetime(2024, 9, 4)
    weeks = []
    cur = start
    while cur <= end:
        weeks.append(cur.strftime('%Y-%m-%d'))
        cur += timedelta(days=7)
    return weeks


def consistent_users(commits_data: Dict, pre_treatment_weeks: List[str]) -> List[str]:
    """Users with >=1 commit in *every* pre-treatment week."""
    keep = []
    for username, user_data in commits_data.items():
        weekly = defaultdict(int)
        for d, c in user_data.get('daily_commits', {}).items():
            if c > 0:
                w = get_week_start_date(d)
                if w in pre_treatment_weeks:
                    weekly[w] += c
        if len(weekly) == len(pre_treatment_weeks) and all(v > 0 for v in weekly.values()):
            keep.append(username)
    return keep


def build_balanced_user_week(commits_data: Dict, users: List[str], weeks: List[str]) -> List[Dict]:
    """Return a *balanced* panel of user-week observations for the given users × weeks.
    Missing user-week cells are filled with 0 commits.
    """
    panel = []
    for u in users:
        daily = commits_data[u].get('daily_commits', {})
        agg = defaultdict(int)
        for d, c in daily.items():
            if c > 0:
                w = get_week_start_date(d)
                if w in weeks:
                    agg[w] += c
        for w in weeks:
            panel.append({'user': u, 'week': w, 'commits': int(agg.get(w, 0))})
    return panel


def remove_top_percent_outliers(user_week_data: List[Dict], percentile: float = 95.0) -> Tuple[List[Dict], float]:
    """Remove observations strictly above the given percentile threshold on commits."""
    commits = [obs['commits'] for obs in user_week_data]
    if not commits:
        return user_week_data, 0.0
    thr = float(np.percentile(commits, percentile))
    clean = [obs for obs in user_week_data if obs['commits'] <= thr]
    return clean, thr


def weekly_totals(user_week_data: List[Dict]) -> Dict[str, int]:
    by_week = defaultdict(int)
    for obs in user_week_data:
        by_week[obs['week']] += int(obs['commits'])
    return dict(by_week)


def weekly_avg_per_user(user_week_data: List[Dict], n_users: int) -> Dict[str, float]:
    by_week = defaultdict(int)
    for obs in user_week_data:
        by_week[obs['week']] += int(obs['commits'])
    return {w: by_week[w] / n_users if n_users else 0.0 for w in by_week}


def period_slices(weeks: List[str], treatment_week: str = '2024-07-17') -> Dict[str, List[str]]:
    t = datetime.strptime(treatment_week, '%Y-%m-%d')
    pre, during, post = [], [], []
    for w in weeks:
        wd = datetime.strptime(w, '%Y-%m-%d')
        if wd < t:
            pre.append(w)
        elif wd == t:
            during.append(w)
        else:
            post.append(w)
    return {'pre': pre, 'during': during, 'post': post}


def period_mean(user_week_data: List[Dict], weeks_subset: List[str], n_users: int) -> float:
    if not weeks_subset or n_users == 0:
        return 0.0
    total = 0
    count = 0
    subset = set(weeks_subset)
    for obs in user_week_data:
        if obs['week'] in subset:
            total += obs['commits']
            count += 1
    # average commits per user-week within subset
    return (total / count) if count else 0.0


@dataclass
class DIDResult:
    pre: float
    during: float
    post: float
    change_pre_to_during: float
    change_pre_to_post: float
    did_pre_to_during: float
    did_pre_to_post: float


def did_from_panels(treated_panel: List[Dict], control_panel: List[Dict], weeks: List[str], n_treated: int, n_control: int,
                    treatment_week: str = '2024-07-17') -> DIDResult:
    """Compute difference-in-differences on *average commits per user-week*."""
    slices = period_slices(weeks, treatment_week)

    def avg(panel, subset_weeks, n_users):
        # average per user-week (balanced by construction)
        return period_mean(panel, subset_weeks, n_users)

    tr_pre = avg(treated_panel, slices['pre'], n_treated)
    tr_dur = avg(treated_panel, slices['during'], n_treated)
    tr_post = avg(treated_panel, slices['post'], n_treated)

    co_pre = avg(control_panel, slices['pre'], n_control)
    co_dur = avg(control_panel, slices['during'], n_control)
    co_post = avg(control_panel, slices['post'], n_control)

    change_tr_pre_dur = tr_dur - tr_pre
    change_tr_pre_post = tr_post - tr_pre
    change_co_pre_dur = co_dur - co_pre
    change_co_pre_post = co_post - co_pre

    did_during = change_tr_pre_dur - change_co_pre_dur
    did_post = change_tr_pre_post - change_co_pre_post

    return DIDResult(
        pre=tr_pre - co_pre,
        during=tr_dur - co_dur,
        post=tr_post - co_post,
        change_pre_to_during=change_tr_pre_dur,
        change_pre_to_post=change_tr_pre_post,
        did_pre_to_during=did_during,
        did_pre_to_post=did_post,
    )


# =============================
# Plotting helpers
# =============================

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def plot_time_series(avg_treated: Dict[str, float], avg_control: Dict[str, float], treatment_week: str, outdir: str):
    ensure_dir(outdir)
    weeks_sorted = sorted(avg_treated.keys())
    x = [datetime.strptime(w, '%Y-%m-%d') for w in weeks_sorted]
    y_tr = [avg_treated[w] for w in weeks_sorted]
    y_co = [avg_control[w] for w in weeks_sorted]

    plt.figure(figsize=(12, 7))
    plt.plot(x, y_tr, label='Bangladesh (treated)', linewidth=2)
    plt.plot(x, y_co, label='Philippines (control)', linewidth=2)

    t = datetime.strptime(treatment_week, '%Y-%m-%d')
    plt.axvspan(t, t + timedelta(days=7), color='gray', alpha=0.25, label='Blackout week')

    plt.title('Average commits per user-week (balanced panel, P95+ outliers removed)')
    plt.xlabel('Week (start date)')
    plt.ylabel('Commits per user-week')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, 'ts_avg_commits_user_week.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(outdir, 'ts_avg_commits_user_week.pdf'), bbox_inches='tight')
    plt.close()


def plot_did_bars(did: DIDResult, outdir: str):
    ensure_dir(outdir)
    labels = ['Δ Pre→During', 'Δ Pre→Post']
    values = [did.did_pre_to_during, did.did_pre_to_post]

    plt.figure(figsize=(8, 6))
    bars = plt.bar(labels, values)
    for b in bars:
        h = b.get_height()
        plt.text(b.get_x() + b.get_width()/2, h, f"{h:.2f}", ha='center', va='bottom')
    plt.title('Difference-in-Differences (Bangladesh − Philippines)')
    plt.ylabel('Commits per user-week')
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, 'did_bars.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(outdir, 'did_bars.pdf'), bbox_inches='tight')
    plt.close()


# =============================
# Main analysis pipeline
# =============================

def analyze(bd_path: str = 'main/bangladesh/commits.json',
            ph_path: str = 'philippines/commits.json',
            outdir: str = 'analysis',
            treatment_week: str = '2024-07-17',
            outlier_percentile: float = 95.0):
    ensure_dir(outdir)

    print('Loading data...')
    bd = load_commits_data(bd_path)
    ph = load_commits_data(ph_path)

    # Define weeks and slices
    weeks = complete_weeks_may_to_sept()
    slices = period_slices(weeks, treatment_week)
    print(f"Weeks in analysis window: {len(weeks)} (May 1 – Sep 4, 2024)")
    print(f"Pre: {len(slices['pre'])} weeks | During: {len(slices['during'])} | Post: {len(slices['post'])}")

    # Consistent users (pre-treatment completeness)
    bd_consistent = consistent_users(bd, slices['pre'])
    ph_consistent = consistent_users(ph, slices['pre'])
    print(f"Consistent users — Bangladesh: {len(bd_consistent)} | Philippines: {len(ph_consistent)}")

    # Build balanced user-week panels
    bd_panel = build_balanced_user_week(bd, bd_consistent, weeks)
    ph_panel = build_balanced_user_week(ph, ph_consistent, weeks)
    print(f"Balanced panels built: BD {len(bd_panel)} rows ({len(bd_consistent)}×{len(weeks)}), PH {len(ph_panel)} rows ({len(ph_consistent)}×{len(weeks)})")

    # Remove top-percent outliers per country
    bd_clean, bd_thr = remove_top_percent_outliers(bd_panel, outlier_percentile)
    ph_clean, ph_thr = remove_top_percent_outliers(ph_panel, outlier_percentile)
    print(f"Outlier thresholds (P{int(outlier_percentile)}): BD {bd_thr:.1f}, PH {ph_thr:.1f}")
    print(f"Rows removed — BD: {len(bd_panel) - len(bd_clean)} | PH: {len(ph_panel) - len(ph_clean)}")

    # Weekly averages per user (for plotting)
    bd_weekly_avg = weekly_avg_per_user(bd_clean, len(bd_consistent))
    ph_weekly_avg = weekly_avg_per_user(ph_clean, len(ph_consistent))

    # DID on per-user-week averages
    did_res = did_from_panels(bd_clean, ph_clean, weeks, len(bd_consistent), len(ph_consistent), treatment_week)

    # Placebo check: pick week 2024-06-12 as fake blackout
    placebo_week = '2024-06-12'
    placebo_did = did_from_panels(bd_clean, ph_clean, weeks, len(bd_consistent), len(ph_consistent), placebo_week)

    # Save figures
    plot_time_series(bd_weekly_avg, ph_weekly_avg, treatment_week, outdir)
    plot_did_bars(did_res, outdir)

    # Summaries
    summary = {
        'analysis_window_weeks': weeks,
        'n_weeks': len(weeks),
        'treatment_week': treatment_week,
        'consistent_users': {
            'bangladesh': len(bd_consistent),
            'philippines': len(ph_consistent)
        },
        'outlier_thresholds_commits': {
            'bangladesh_p95': round(bd_thr, 2),
            'philippines_p95': round(ph_thr, 2)
        },
        'did_results_commits_per_user_week': {
            'pre_diff_BD_minus_PH': round(did_res.pre, 4),
            'during_diff_BD_minus_PH': round(did_res.during, 4),
            'post_diff_BD_minus_PH': round(did_res.post, 4),
            'treated_change_pre_to_during': round(did_res.change_pre_to_during, 4),
            'treated_change_pre_to_post': round(did_res.change_pre_to_post, 4),
            'DID_pre_to_during': round(did_res.did_pre_to_during, 4),
            'DID_pre_to_post': round(did_res.did_pre_to_post, 4)
        },
        'placebo_check_Jun12': {
            'DID_pre_to_during': round(placebo_did.did_pre_to_during, 4),
            'DID_pre_to_post': round(placebo_did.did_pre_to_post, 4)
        }
    }

    with open(os.path.join(outdir, '8_analysis_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {os.path.join(outdir, '8_analysis_summary.json')}")

    # Console snapshot
    print('\n==== Difference-in-Differences (Commits per user-week) ====')
    print(f"Pre (BD−PH): {did_res.pre:.3f}")
    print(f"During (BD−PH): {did_res.during:.3f}")
    print(f"Post (BD−PH): {did_res.post:.3f}")
    print(f"Δ Treated Pre→During: {did_res.change_pre_to_during:.3f}")
    print(f"Δ Treated Pre→Post:   {did_res.change_pre_to_post:.3f}")
    print(f"DID Pre→During: {did_res.did_pre_to_during:.3f}")
    print(f"DID Pre→Post:   {did_res.did_pre_to_post:.3f}")


if __name__ == '__main__':
    analyze()