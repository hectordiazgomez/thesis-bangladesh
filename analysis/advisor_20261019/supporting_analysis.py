"""Donor/predictor diagnostics and residual-activity characterization.
All outputs are additive. Cohorts are descriptive and can overlap.
"""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
import db_dtypes
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/advisor_20261019';OUT.mkdir(parents=True,exist_ok=True)
def scmod():
 s=importlib.util.spec_from_file_location('sc',ROOT/'analysis/synthetic_control/01_reproduce_sc.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def national():
 sc=scmod();w=sc.load_panel();donors=list(w.columns.drop('Bangladesh'));pre=w.loc['2024-05-01':'2024-07-17'];post=w.loc['2024-07-18':'2024-07-23']
 specs={
  'All 78 daily lags':lambda x:x,
  'Complete weekly means':lambda x:x.iloc[-(len(x)//7)*7:].groupby(np.arange((len(x)//7)*7)//7).mean(),
  'Last 28 daily lags':lambda x:x.iloc[-28:],
  'Last 14 daily lags':lambda x:x.iloc[-14:],
  'Weekday means':lambda x:x.groupby(x.index.dayofweek).mean(),
 }
 rows=[];weights=[]
 for name,fn in specs.items():
  x=fn(pre);wt=sc.fit_sc(x.Bangladesh.to_numpy(),x[donors].to_numpy());fitgap=pre.Bangladesh-pre[donors]@wt;cf=post[donors]@wt;att=float((post.Bangladesh-cf).mean())
  # Honest pre-treatment check: refit through June 30, score July 1-17.
  train=fn(pre.loc[:'2024-06-30']);tw=sc.fit_sc(train.Bangladesh.to_numpy(),train[donors].to_numpy());valid=pre.loc['2024-07-01':]
  rows.append(dict(specification=name,predictors=len(x),ATT_pp=att,counterfactual_pct=cf.mean(),relative_pct=100*att/cf.mean(),pre_RMSPE_pp=np.sqrt((fitgap**2).mean()),validation_RMSPE_pp=np.sqrt(((valid.Bangladesh-valid[donors]@tw)**2).mean())))
  weights.extend(dict(specification=name,country=c,weight=float(v)) for c,v in zip(donors,wt))
 pd.DataFrame(rows).to_csv(OUT/'sc_predictor_sensitivity.csv',index=False);pd.DataFrame(weights).to_csv(OUT/'sc_predictor_weights.csv',index=False)
 e=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet');n=e.groupby('country').size();original=pd.Series(sc.fit_sc(pre.Bangladesh.to_numpy(),pre[donors].to_numpy()),index=donors)
 table=pd.DataFrame({'eligible_users':n,'pre_mean_pct':pre.mean(),'pre_sd_pp':pre.std(),'SC_weight':original}).fillna({'SC_weight':0});table.to_csv(OUT/'donor_audit.csv')
 print(pd.DataFrame(rows).round(4).to_string(index=False),flush=True)
def residual():
 d=pd.read_parquet(ROOT/'data/processed/github_activity_international_enriched.parquet');d.date=pd.to_datetime(d.date)
 e=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet');e=e[e.country.eq('Bangladesh')].copy();e.login=e.login.str.lower();d=d[d.country.eq('Bangladesh')].copy();d.login=d.login.str.lower();d=d.merge(e[['login']],on='login',validate='many_to_one')
 pre=d[d.date.lt('2024-07-18')].copy();pre['productive_day']=pre.productive_events.gt(0);pre['push_day']=pre.pushes.gt(0);pre['collaboration_day']=pre.collaboration_events.gt(0);pre['shipping_day']=pre.shipping_active.gt(0)
 pre['weekend_productive']=pre.productive_day&pre.date.dt.dayofweek.ge(5)
 f=pre.groupby('login').agg(pre_productive_days=('productive_day','sum'),pre_push_days=('push_day','sum'),pre_pushes=('pushes','sum'),pre_commits=('commits','sum'),pre_collaboration_days=('collaboration_day','sum'),pre_shipping_days=('shipping_day','sum'),pre_weekend_days=('weekend_productive','sum'),pre_repo_days=('repos_active','sum'))
 f=e[['login']].set_index('login').join(f).fillna(0)
 f['pre_activity_pct']=100*f.pre_productive_days/78
 f['pre_collaboration_pct']=100*f.pre_collaboration_days/78
 f['pre_shipping_pct']=100*f.pre_shipping_days/78
 f['weekend_share_pct']=100*f.pre_weekend_days/f.pre_productive_days.replace(0,np.nan)
 f['core_public_active']=f.index.isin(d.loc[d.date.between('2024-07-19','2024-07-22')&d.productive_events.gt(0),'login'])
 f['calendar_public_active']=f.index.isin(d.loc[d.date.between('2024-07-18','2024-07-23')&d.productive_events.gt(0),'login'])
 m=pd.read_parquet(ROOT/'results/mechanism/commit_sha_author_push_master.parquet');m.authored_time=pd.to_datetime(m.authored_time,utc=True);m.push_time=pd.to_datetime(m.push_time,utc=True)
 strict=m[m.author_equals_pusher.fillna(False)&m.authored_time.notna()&m.plausible_author_delay.fillna(False)].copy();strict.pusher_login=strict.pusher_login.str.lower()
 onset=strict[strict.authored_time.ge('2024-07-18T15:00:00Z')&strict.authored_time.lt('2024-07-24T00:00:00Z')].copy()
 f['onset_author']=f.index.isin(onset.pusher_login)
 f['delayed_onset_author']=f.index.isin(onset.loc[onset.push_time.ge('2024-07-24T00:00:00Z'),'pusher_login'])
 f['early_onset_publisher']=f.index.isin(onset.loc[onset.push_time.lt('2024-07-23T00:00:00Z'),'pusher_login'])
 f['restoration_day_publisher']=f.index.isin(onset.loc[onset.push_time.ge('2024-07-23T00:00:00Z')&onset.push_time.lt('2024-07-24T00:00:00Z'),'pusher_login'])
 f.to_parquet(OUT/'residual_user_characteristics.parquet')
 rows=[]
 groups={'All eligible':pd.Series(True,index=f.index),'Core-window publishers':f.core_public_active,'No core-window publication':~f.core_public_active,'Onset-timestamp authors':f.onset_author,'Delayed onset authors':f.delayed_onset_author,'Pre-restoration onset publishers':f.early_onset_publisher}
 for name,mask in groups.items():
  z=f[mask];row={'group':name,'users':len(z),'share_eligible_pct':100*len(z)/len(f)}
  for k in ['pre_activity_pct','pre_collaboration_pct','pre_shipping_pct','pre_pushes','pre_commits','weekend_share_pct']:
   row[k+'_mean']=z[k].mean();row[k+'_median']=z[k].median()
  rows.append(row)
 pd.DataFrame(rows).to_csv(OUT/'residual_group_summary.csv',index=False)
 core=d[d.date.between('2024-07-19','2024-07-22')];core.loc[core.productive_events.gt(0)].groupby('date').agg(active_users=('login','nunique'),productive_events=('productive_events','sum'),pushes=('pushes','sum')).to_csv(OUT/'residual_core_daily.csv')
 info={'eligible_users':len(f),'onset_commits':len(onset),'onset_users':onset.pusher_login.nunique(),'onset_users_in_eligible':int(f.onset_author.sum()),'calendar_public_users':int(f.calendar_public_active.sum()),'core_public_users':int(f.core_public_active.sum()),'delayed_onset_users':int(f.delayed_onset_author.sum()),'early_onset_publisher_users':int(f.early_onset_publisher.sum()),'restoration_day_publisher_users':int(f.restoration_day_publisher.sum()),'early_onset_commits':int(onset.push_time.lt('2024-07-23T00:00:00Z').sum()),'onset_author_core_public_overlap':int((f.onset_author&f.core_public_active).sum())}
 (OUT/'residual_cohort_counts.json').write_text(json.dumps(info,indent=2));print(json.dumps(info),flush=True)
 # User concentration in the directly observed residual primary event count.
 cnt=core.groupby('login').productive_events.sum().sort_values(ascending=False);cnt=cnt[cnt.gt(0)]
 concentration={'core_productive_events':int(cnt.sum()),'top1_event_share_pct':100*cnt.iloc[:1].sum()/cnt.sum(),'top10_event_share_pct':100*cnt.iloc[:10].sum()/cnt.sum()}
 (OUT/'residual_concentration.json').write_text(json.dumps(concentration,indent=2))
if __name__=='__main__':national();residual()
