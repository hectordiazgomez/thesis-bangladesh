# 9_rdd.py
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta
import os

import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

# ----------------------------
# Config
# ----------------------------
CUT_DATE = datetime(2024, 7, 17)         # blackout start
WINDOW_START = datetime(2024, 5, 1)
WINDOW_END   = datetime(2024, 9, 4)       # inclusive end used elsewhere
BANDWIDTH_WEEKS = 4                       # change to 3–5 to test sensitivity
OUT_DIR = "analysis"
PLOTS_DIR = "analysis/figs"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

# ----------------------------
# IO helpers
# ----------------------------
def load_commits_data(path):
    with open(path, "r") as f:
        return json.load(f)

def week_start(date_str, ref=datetime(2024,5,1)):
    # Group dates into 7-day bins starting at May 1, 2024
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    days = (dt - ref).days
    bucket = days // 7
    start = ref + timedelta(days=bucket*7)
    return start.strftime("%Y-%m-%d")

def all_complete_weeks():
    # enumerate week starts between WINDOW_START and WINDOW_END (inclusive by start)
    weeks = []
    d = WINDOW_START
    while d <= WINDOW_END:
        weeks.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=7)
    return weeks

def is_within_window(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return WINDOW_START <= dt <= WINDOW_END

# ----------------------------
# Panel building (balanced, consistent users)
# ----------------------------
def find_consistent_users(commits_data, pre_weeks):
    consistent = []
    for u, ud in commits_data.items():
        daily = ud.get("daily_commits", {})
        weekly = defaultdict(int)
        for ds, c in daily.items():
            if c > 0:
                w = week_start(ds)
                weekly[w] += c
        # consistent if has >0 each pre-treatment week
        if all(weekly.get(w, 0) > 0 for w in pre_weeks):
            consistent.append(u)
    return consistent

def build_balanced_panel(commits_data):
    weeks = all_complete_weeks()
    pre_weeks = [w for w in weeks if datetime.strptime(w, "%Y-%m-%d") < CUT_DATE]
    consistent = find_consistent_users(commits_data, pre_weeks)

    # user-week table (balanced: every consistent user x every week, fill zeros)
    rows = []
    for u in consistent:
        daily = commits_data[u].get("daily_commits", {})
        agg = defaultdict(int)
        for ds, c in daily.items():
            if c > 0:
                w = week_start(ds)
                if w in weeks:
                    agg[w] += c
        for w in weeks:
            rows.append({"user": u, "week": w, "commits": agg.get(w, 0)})

    return rows, weeks, consistent

def drop_top5_outliers(user_week_rows):
    if not user_week_rows:
        return user_week_rows, 0, 0.0
    vals = np.array([r["commits"] for r in user_week_rows])
    p95 = float(np.percentile(vals, 95))
    kept = [r for r in user_week_rows if r["commits"] <= p95]
    dropped = len(user_week_rows) - len(kept)
    return kept, dropped, p95

def weekly_mean_commits_per_user(user_week_rows, n_users, weeks):
    by_week = defaultdict(list)
    for r in user_week_rows:
        by_week[r["week"]].append(r["commits"])
    # balanced panel implies len(list)==n_users for each week after outlier removal may be < n_users;
    # we compute mean per user as (sum / n_users), counting dropped outliers as removed observations.
    # This mirrors your previous approach and keeps the denominator constant.
    series = {}
    for w in weeks:
        vals = by_week.get(w, [])
        total = sum(vals)
        series[w] = total / n_users if n_users > 0 else 0.0
    return series

# ----------------------------
# Local-linear RDD (WLS with triangular kernel)
# y_t = a0 + b0*r + a1*I[r>=0] + b1*r*I[r>=0] + e
# Discontinuity = a1 (jump at r=0)
# ----------------------------
def make_running_var(weeks):
    x = []
    for w in weeks:
        dt = datetime.strptime(w, "%Y-%m-%d")
        # running variable in weeks; 0 == cutoff week start
        delta = (dt - CUT_DATE).days / 7.0
        x.append(delta)
    return np.array(x)

def triangular_kernel(x, h):
    # weight = (1 - |x|/h)+  within |x|<=h, else 0
    w = np.clip(1 - np.abs(x)/h, 0, None)
    return w

def local_linear_rdd(y, x, h):
    # keep observations within bandwidth
    mask = np.abs(x) <= h
    y_loc = y[mask]
    x_loc = x[mask]
    if y_loc.size < 6:
        raise ValueError("Not enough observations within bandwidth for RDD.")

    T = (x_loc >= 0).astype(float)          # post side
    X = np.column_stack([
        np.ones_like(x_loc),                # a0
        x_loc,                              # b0
        T,                                  # a1 (the jump)
        x_loc * T                           # b1
    ])
    weights = triangular_kernel(x_loc, h)
    model = sm.WLS(y_loc, X, weights=weights)
    res = model.fit(cov_type="HC1")         # robust SE
    # discontinuity estimate = coefficient on T
    jump = res.params[2]
    se   = res.bse[2]
    return {"jump": float(jump), "se": float(se), "n": int(y_loc.size),
            "params": res.params.tolist(), "bse": res.bse.tolist()}

# ----------------------------
# Plot helper
# ----------------------------
def plot_rdd(bd_series, ph_series, weeks, h, outpath):
    x = make_running_var(weeks)
    bd_y = np.array([bd_series[w] for w in weeks], dtype=float)
    ph_y = np.array([ph_series[w] for w in weeks], dtype=float)

    # scatter + fitted lines (local means just for viz)
    fig, ax = plt.subplots(figsize=(12, 6))

    # points
    ax.scatter([datetime.strptime(w, "%Y-%m-%d") for w in weeks], bd_y,
               s=36, alpha=0.7, label="Bangladesh (avg commits/user-week)", marker="o")
    ax.scatter([datetime.strptime(w, "%Y-%m-%d") for w in weeks], ph_y,
               s=36, alpha=0.7, label="Philippines (avg commits/user-week)", marker="s")

    # vertical band = blackout week
    ax.axvspan(CUT_DATE, CUT_DATE + timedelta(days=7), color="gray", alpha=0.2, label="Blackout week (BD)")

    # cosmetics
    ax.set_title(f"Local RDD around {CUT_DATE.strftime('%Y-%m-%d')} (bandwidth {h} weeks)")
    ax.set_xlabel("Week start")
    ax.set_ylabel("Average commits per user-week")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close()

# ----------------------------
# Main
# ----------------------------
def main():
    print("Loading data...")
    bd = load_commits_data("main/bangladesh/commits.json")
    ph = load_commits_data("philippines/commits.json")

    weeks = all_complete_weeks()
    pre, during, post = (
        [w for w in weeks if datetime.strptime(w, "%Y-%m-%d") < CUT_DATE],
        [w for w in weeks if datetime.strptime(w, "%Y-%m-%d") == CUT_DATE],
        [w for w in weeks if datetime.strptime(w, "%Y-%m-%d") > CUT_DATE],
    )
    print(f"Weeks in analysis window: {len(weeks)} (May 1 – Sep 4, 2024)")
    print(f"Pre: {len(pre)} | During: {len(during)} | Post: {len(post)}")

    # Build balanced panels and remove P95 outliers
    bd_rows, weeks_b, bd_users = build_balanced_panel(bd)
    ph_rows, weeks_p, ph_users = build_balanced_panel(ph)
    assert weeks_b == weeks_p == weeks, "Week grids must match."

    bd_clean, bd_drop, bd_p95 = drop_top5_outliers(bd_rows)
    ph_clean, ph_drop, ph_p95 = drop_top5_outliers(ph_rows)

    print(f"Consistent users — Bangladesh: {len(bd_users)} | Philippines: {len(ph_users)}")
    print(f"Balanced panels: BD {len(bd_rows)} rows ({len(bd_users)}×{len(weeks)}), "
          f"PH {len(ph_rows)} rows ({len(ph_users)}×{len(weeks)})")
    print(f"Outlier thresholds (P95): BD {bd_p95:.1f}, PH {ph_p95:.1f}")
    print(f"Rows removed — BD: {bd_drop} | PH: {ph_drop}")

    # Weekly averages per user-week
    bd_avg = weekly_mean_commits_per_user(bd_clean, len(bd_users), weeks)
    ph_avg = weekly_mean_commits_per_user(ph_clean, len(ph_users), weeks)

    # Prepare inputs for RDD
    x = make_running_var(weeks)
    y_bd = np.array([bd_avg[w] for w in weeks], dtype=float)
    y_ph = np.array([ph_avg[w] for w in weeks], dtype=float)

    # Estimate local-linear RDD for each country
    h = BANDWIDTH_WEEKS
    bd_rdd = local_linear_rdd(y_bd, x, h)
    ph_rdd = local_linear_rdd(y_ph, x, h)

    # Difference-in-Discontinuities (simple): tau = tau_BD - tau_PH
    did_jump = bd_rdd["jump"] - ph_rdd["jump"]
    # Conservative SE assuming independence across country series
    did_se = math.sqrt(bd_rdd["se"]**2 + ph_rdd["se"]**2)
    did_t = did_jump / did_se if did_se > 0 else float("nan")

    # Save results
    out = {
        "config": {
            "cutoff": CUT_DATE.strftime("%Y-%m-%d"),
            "bandwidth_weeks": h,
            "window": {"start": WINDOW_START.strftime("%Y-%m-%d"),
                       "end": WINDOW_END.strftime("%Y-%m-%d")},
        },
        "panel": {
            "weeks": weeks,
            "n_weeks": len(weeks),
            "bd_users": len(bd_users),
            "ph_users": len(ph_users),
            "bd_rows": len(bd_rows),
            "ph_rows": len(ph_rows),
            "bd_p95": bd_p95,
            "ph_p95": ph_p95,
            "bd_rows_dropped": bd_drop,
            "ph_rows_dropped": ph_drop,
        },
        "rdd": {
            "bangladesh": bd_rdd,
            "philippines": ph_rdd,
            "difference_in_discontinuities": {
                "jump_diff": did_jump,
                "se": did_se,
                "t_stat": did_t
            }
        }
    }
    with open(os.path.join(OUT_DIR, "9_rdd_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved results to {os.path.join(OUT_DIR, '9_rdd_results.json')}")

    # Plot
    plot_rdd(bd_avg, ph_avg, weeks, h, os.path.join(PLOTS_DIR, "9_rdd_window.png"))
    print(f"Saved plot to {os.path.join(PLOTS_DIR, '9_rdd_window.png')}")

    # Console summary
    print("\n==== Local-linear RDD (bandwidth = {} weeks) ====".format(h))
    print("Bangladesh  jump: {:>8.3f}  (se {:>6.3f}, n={})".format(bd_rdd["jump"], bd_rdd["se"], bd_rdd["n"]))
    print("Philippines jump: {:>8.3f}  (se {:>6.3f}, n={})".format(ph_rdd["jump"], ph_rdd["se"], ph_rdd["n"]))
    print("DiDisc jump (BD−PH): {:>8.3f}  (se {:>6.3f}, t={:>6.2f})".format(did_jump, did_se, did_t))

if __name__ == "__main__":
    main()
