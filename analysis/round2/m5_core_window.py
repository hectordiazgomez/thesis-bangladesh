"""Fixed original SCM weights; core-window sensitivity, not a new primary window."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/diagnostics/round2'
def main():
 d=pd.read_csv(ROOT/'results/synthetic_control/reproduced/sc_daily_path_full.csv',parse_dates=['date'])
 rows=[]
 for name,start,end in [('primary','2024-07-18','2024-07-23'),('core','2024-07-19','2024-07-22')]:
  g=d[d.date.between(start,end)];a=g.Bangladesh.mean();c=g.Synthetic_Control.mean()
  rows.append(dict(window=name,start=start,end=end,actual_pct=a,counterfactual_pct=c,ATT_pp=a-c,relative_pct=100*(a-c)/c,average_active_users=a*10241/100))
 pd.DataFrame(rows).to_csv(OUT/'m5_core_window.csv',index=False)
 p=pd.read_parquet(ROOT/'results/synthetic_control/country_day_donor_pool.parquet');p.date=pd.to_datetime(p.date)
 pre=p[p.date.between('2024-05-01','2024-07-17')].groupby('country').active_rate_pp.mean();post=p[p.date.between('2024-07-18','2024-07-23')].groupby('country').active_rate_pp.mean()
 (post-pre).rename('post_minus_pre_pp').to_csv(OUT/'m5_donor_changes.csv')
 print(pd.DataFrame(rows).to_string(index=False));print('Donor mean change', (post-pre).drop('Bangladesh').mean())
if __name__=='__main__':main()
