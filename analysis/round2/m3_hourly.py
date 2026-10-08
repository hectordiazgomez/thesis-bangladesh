"""Descriptive hourly PushEvents; not the unresolved primary productive outcome."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/diagnostics/round2'
def main():
 d=pd.read_parquet(ROOT/'results/mechanism/bd_push_events_20240701_20240810.parquet');d.push_time=pd.to_datetime(d.push_time,utc=True)
 e=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet');users=set(e[e.country.eq('Bangladesh')].login);assert set(d.pusher_login.str.lower()).issubset(users)
 original=len(d);dup=d[d.event_id.duplicated(False)]
 # Exact duplicate event records only; other conflicts would stop execution.
 if len(dup) and len(dup.drop_duplicates())!=dup.event_id.nunique():raise ValueError('Conflicting duplicate event IDs')
 d=d.drop_duplicates('event_id');d['hour']=d.push_time.dt.floor('h');d['login']=d.pusher_login.str.lower()
 ix=pd.date_range('2024-07-01','2024-08-11',freq='h',inclusive='left',tz='UTC',name='hour')
 h=d.groupby('hour').agg(push_events=('event_id','size'),active_push_users=('login','nunique')).reindex(ix,fill_value=0);h['active_push_rate_pct']=100*h.active_push_users/len(users)
 h['hour_of_week']=h.index.dayofweek*24+h.index.hour;pre=h.loc[:'2024-07-17 23:00:00+00:00'];base=pre.groupby('hour_of_week').active_push_rate_pct.mean();h['pre_hour_of_week_mean_pct']=h.hour_of_week.map(base);h.to_csv(OUT/'m3_hourly_push_series.csv')
 cuts=[('total_onset','2024-07-18 15:00'),('broadband_start','2024-07-23 13:00'),('mobile_start','2024-07-28 09:00')];rows=[]
 fig,axes=plt.subplots(3,1,figsize=(8,8),layout='constrained')
 for ax,(name,date) in zip(axes,cuts):
  cut=pd.Timestamp(date,tz='UTC')
  for bw in [6,12,24]:
   for side,a,b in [('before',cut-pd.Timedelta(hours=bw),cut),('after',cut,cut+pd.Timedelta(hours=bw))]:
    g=h[(h.index>=a)&(h.index<b)];rows.append(dict(event=name,cutoff_UTC=str(cut),hours=bw,side=side,mean_active_users=g.active_push_users.mean(),mean_rate_pct=g.active_push_rate_pct.mean(),baseline_rate_pct=g.pre_hour_of_week_mean_pct.mean(),events=g.push_events.sum()))
  g=h.loc[cut-pd.Timedelta(hours=24):cut+pd.Timedelta(hours=24)];t=(g.index-cut).total_seconds()/3600
  ax.plot(t,g.active_push_rate_pct,label='Observed PushEvent activity');ax.plot(t,g.pre_hour_of_week_mean_pct,'--',label='July 1–17 same hour-of-week mean');ax.axvline(0,color='black',lw=.8);ax.set_title(f'{name}: {cut}');ax.set_ylabel('% of 10,241 accounts');ax.set_xlabel('Hours relative to connectivity change')
 axes[0].legend(fontsize=8);fig.savefig(OUT/'m3_hourly_diagnostics.pdf');plt.close(fig)
 pd.DataFrame(rows).to_csv(OUT/'m3_connectivity_windows.csv',index=False)
 pd.DataFrame([dict(raw_events=original,unique_events=len(d),duplicate_records_removed=original-len(d),actors=d.login.nunique(),denominator=len(users))]).to_csv(OUT/'m3_coverage.csv',index=False)
 print(pd.DataFrame(rows)[lambda x:x.hours.eq(12)].to_string(index=False))
if __name__=='__main__':main()
