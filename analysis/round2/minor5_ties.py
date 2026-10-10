"""Deterministic backlog ranking: descending backlog, ascending lowercase login."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/diagnostics/round2'
def main():
 u=pd.read_csv(ROOT/'results/final/mechanism_user_level.csv');u['login_key']=u.pusher_login.str.lower()
 u=u.sort_values(['backlog_commits','login_key'],ascending=[False,True],kind='stable');rows=[]
 for k in [1,3,5,10,20]:
  rest=u.iloc[k:];n=int(rest.blackout_commits.sum());b=int(rest.backlog_commits.sum())
  rows.append(dict(drop_top_users=k,N=n,backlog_N=b,backlog_pct=100*b/n))
 d=pd.DataFrame(rows);old=pd.read_csv(ROOT/'results/final/table_mechanism_drop_users.csv');c=old.merge(d,on='drop_top_users',suffixes=('_archived','_deterministic'))
 c.to_csv(OUT/'minor5_tie_comparison.csv',index=False);u.head(20).to_csv(OUT/'minor5_ranked_users.csv',index=False);print(c.to_string(index=False))
if __name__=='__main__':main()
