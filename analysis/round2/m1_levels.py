"""Author-date levels and onset cohorts, with original push-day sampling weights."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/diagnostics/round2';M=ROOT/'results/mechanism'
def strict_sample():
 u=pd.read_parquet(M/'clean_repo_sha_first_push.parquet');m=pd.read_parquet(M/'commit_sha_author_push_master.parquet')
 u['pdate']=pd.to_datetime(u.push_time,utc=True).dt.floor('D')
 for col in ['push_time','authored_time','committed_time']:m[col]=pd.to_datetime(m[col],utc=True)
 m['pdate']=m.push_time.dt.floor('D'); rate=(m.groupby('pdate').size()/u.groupby('pdate').size()).rename('request_rate')
 m=m.join(rate,on='pdate');m['weight']=1/m.request_rate
 return m[m.found & m.authored_time.notna() & m.author_equals_pusher.fillna(False).astype(bool) & m.author_to_push_hours.ge(0)].copy(),m,u

def main():
 s,m,u=strict_sample();s['adate']=s.authored_time.dt.floor('D');end=pd.Timestamp('2024-07-24',tz='UTC');onset=pd.Timestamp('2024-07-18 15:00',tz='UTC')
 s['backlog']=s.push_time.ge(end)
 daily=s.groupby('adate').agg(observed_commits=('sha','size'),weighted_commits=('weight','sum'),users=('pusher_login','nunique'))
 daily=daily.reindex(pd.date_range('2024-07-01','2024-08-10',tz='UTC',name='adate'),fill_value=0);daily.to_csv(OUT/'m1_author_date_daily.csv')
 rows=[]
 for name,start,stop in [('calendar',pd.Timestamp('2024-07-18',tz='UTC'),end),('before_total',pd.Timestamp('2024-07-18',tz='UTC'),onset),('total_onset',onset,end)]:
  g=s[s.authored_time.ge(start)&s.authored_time.lt(stop)];rows.append(dict(cohort=name,commits=len(g),users=g.pusher_login.nunique(),backlog=int(g.backlog.sum()),backlog_pct=100*g.backlog.mean(),pushed_before_jul24=int((~g.backlog).sum()),days=(stop-start).total_seconds()/86400))
 cohorts=pd.DataFrame(rows);cohorts.to_csv(OUT/'m1_cohort_definitions.csv',index=False)
 windows=[]
 for day in range(1,7):
  start=pd.Timestamp(f'2024-07-{day:02}',tz='UTC');stop=start+pd.Timedelta(days=6)
  g=s[s.authored_time.ge(start)&s.authored_time.lt(stop)]
  same=s[s.authored_time.ge(start+pd.Timedelta(hours=15))&s.authored_time.lt(stop)]
  windows.append(dict(start=start,stop_exclusive=stop,weighted_6day=g.weight.sum(),weighted_duration_matched=same.weight.sum()))
 w=pd.DataFrame(windows);w.to_csv(OUT/'m1_level_baselines.csv',index=False)
 g=s[s.authored_time.ge(onset)&s.authored_time.lt(end)&s.push_time.lt(end)]
 early=g.groupby(g.push_time.dt.floor('D')).agg(commits=('sha','size'),users=('pusher_login','nunique'));early.to_csv(OUT/'m1_early_release.csv')
 ref=w.weighted_6day.mean();matched=w.weighted_duration_matched.mean()
 c=cohorts.set_index('cohort');total_n=int(c.loc['total_onset','commits']);calendar_n=int(c.loc['calendar','commits']);total_backlog=int(c.loc['total_onset','backlog']);calendar_backlog=int(c.loc['calendar','backlog'])
 stats=dict(strict_commits=len(s),pre_requested=int(m.pdate.lt('2024-07-18').sum()),pre_universe=int(u.pdate.lt('2024-07-18').sum()),mean_6day_baseline=ref,mean_matched_baseline=matched,total_decline_raw_6day_pct=100*(total_n/ref-1),total_decline_matched_pct=100*(total_n/matched-1),total_decline_duration_scaled_pct=100*((total_n/c.loc['total_onset','days'])/(ref/c.loc['calendar','days'])-1),calendar_decline_pct=100*(calendar_n/ref-1),calendar_backlog_pct_normal=100*calendar_backlog/ref,total_backlog_pct_normal_matched=100*total_backlog/matched,early_commits=len(g),early_users=g.pusher_login.nunique(),calendar_backlog_aug5_10=int((s.authored_time.ge('2024-07-18')&s.authored_time.lt(end)&s.push_time.ge('2024-08-05')).sum()))
 assert cohorts.set_index('cohort').loc['calendar','commits']==2932 and len(g)==345
 (OUT/'m1_summary.json').write_text(json.dumps(stats,indent=2));print(cohorts.to_string(index=False));print(json.dumps(stats,indent=2));print(early.to_string())
if __name__=='__main__':main()
