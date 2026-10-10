"""Descriptive cumulative gaps using unchanged primary weights and cohort."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/diagnostics/round2'
def main():
 d=pd.read_csv(ROOT/'results/synthetic_control/reproduced/sc_daily_path_full.csv',parse_dates=['date']).set_index('date')
 n=10241;pre=d.loc['2024-05-01':'2024-07-17','Bangladesh'].mean();p=d.loc['2024-07-18':].copy()
 p['gap_userdays']=p.gap*n/100;p['cumulative_gap_userdays']=p.gap_userdays.cumsum();p['gap_7day_mean_pp']=p.gap.rolling(7).mean();p['own_pre_gap_pp']=p.Bangladesh-pre
 def first(mask):
  ix=p.index[mask & (p.index>=pd.Timestamp('2024-07-24'))];return ix[0] if len(ix) else None
 criteria={'first_daily_at_counterfactual':first(p.gap.ge(0)),'first_trailing_7day_mean_at_counterfactual':first(p.gap_7day_mean_pp.ge(0)),'first_7_consecutive_days_at_counterfactual_end':first(p.gap.ge(0).rolling(7).sum().eq(7)),'first_daily_at_own_pre_mean':first(p.own_pre_gap_pp.ge(0)),'first_trailing_7day_mean_at_own_pre_mean':first(p.Bangladesh.rolling(7).mean().ge(pre))}
 rows=[]
 for label,end in criteria.items():
  rows.append(dict(criterion=label,date=None if end is None else str(end.date()),cumulative_gap_userdays=None if end is None else p.loc[:end].gap_userdays.sum(),days_since_jul18=None if end is None else (end-p.index[0]).days))
 pd.DataFrame(rows).to_csv(OUT/'m8_return_criteria.csv',index=False)
 p.to_csv(OUT/'m8_cumulative_daily.csv')
 post=p.loc['2024-07-24':];s=dict(pre_mean_pct=pre,shutdown_net_loss_userdays=-p.loc[:'2024-07-23'].gap_userdays.sum(),total_negative_area_userdays=-p.gap_userdays.clip(upper=0).sum(),total_positive_area_userdays=p.gap_userdays.clip(lower=0).sum(),net_loss_through_sep4_userdays=-p.gap_userdays.sum(),lowest_cumulative_gap_userdays=p.cumulative_gap_userdays.min(),lowest_cumulative_date=str(p.cumulative_gap_userdays.idxmin().date()),post_days=len(post),post_days_below_counterfactual=int(post.gap.lt(0).sum()),post_negative_area_userdays=-post.gap_userdays.clip(upper=0).sum(),post_positive_area_userdays=post.gap_userdays.clip(lower=0).sum(),cumulative_loss_repaid=bool(p.cumulative_gap_userdays.ge(0).any()))
 (OUT/'m8_summary.json').write_text(json.dumps(s,indent=2));print(pd.DataFrame(rows).to_string(index=False));print(json.dumps(s,indent=2))
if __name__=='__main__':main()
