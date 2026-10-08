"""Exhaustive declared grid: cutoff Jul17/18/19 x h4/5/7/10/14, all three series."""
from pathlib import Path
import importlib.util
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/diagnostics/round2'
def main():
 spec=importlib.util.spec_from_file_location('rd',ROOT/'analysis/rdit/01_reproduce_rdit.py');rd=importlib.util.module_from_spec(spec);spec.loader.exec_module(rd)
 bd=rd.daily_rate('panel_user_day_bangladesh.parquet');ph=rd.daily_rate('panel_user_day_philippines.parquet');rows=[]
 for cutoff in ['2024-07-17','2024-07-18','2024-07-19']:
  for bw in [4,5,7,10,14]:
   rd.CUT=pd.Timestamp(cutoff);rd.BW=bw
   for name,y in [('Bangladesh',bd),('BD_minus_PH',bd-ph),('Philippines',ph)]:
    rows.append(dict(cutoff=cutoff,bandwidth=bw,series=name,**rd.rd(y)))
 d=pd.DataFrame(rows);d.to_csv(OUT/'m6_cutoff_bandwidth_grid.csv',index=False)
 a=pd.read_csv(ROOT/'data/processed/table3_rdit_sensitivity.csv');a['provenance']='archived; cutoff/outcome/sample/SE provenance unresolved';a.to_csv(OUT/'m6_archived_16_grid.csv',index=False)
 e=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet');p=pd.read_parquet(ROOT/'data/processed/panel_user_day_bangladesh.parquet',columns=['login']);old=set(p.login.str.lower());main=set(e.loc[e.country.eq('Bangladesh'),'login'].str.lower())
 pd.DataFrame([{'rdit_users':len(old),'scm_users':len(main),'rdit_not_scm':len(old-main),'scm_not_rdit':len(main-old)}]).to_csv(OUT/'m6_sample_overlap.csv',index=False)
 print(d[d.series.eq('Bangladesh')][['cutoff','bandwidth','effect','se_hac']].to_string(index=False));print('Sample differences',len(old-main),len(main-old))
if __name__=='__main__':main()
