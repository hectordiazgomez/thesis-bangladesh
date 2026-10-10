"""M2 diagnostics only: original fit windows and eligibility fixed before fitting."""
from pathlib import Path
import importlib.util,json
import db_dtypes
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/diagnostics/round2'
def main():
 spec=importlib.util.spec_from_file_location('sc',ROOT/'analysis/synthetic_control/01_reproduce_sc.py');sc=importlib.util.module_from_spec(spec);spec.loader.exec_module(sc)
 w=sc.load_panel();donors=list(w.columns.drop('Bangladesh'));fits=[('2024-05-01','2024-07-17'),('2024-05-01','2024-06-30'),('2024-06-20','2024-07-17'),('2024-07-01','2024-07-17')];rows=[];weights=[]
 for a,b in fits:
  r=sc.sc_stats(w,'Bangladesh',donors,a,b,'2024-07-18','2024-07-23');wt=r.pop('weights');gap=w.Bangladesh-w[donors]@wt
  rows.append(dict(fit_start=a,fit_end=b,**r,gap_jul1_17=gap.loc['2024-07-01':'2024-07-17'].mean(),gap_aug14_27=gap.loc['2024-08-14':'2024-08-27'].mean()))
  weights.extend(dict(fit_start=a,fit_end=b,country=c,weight=v) for c,v in wt.items())
 pd.DataFrame(rows).to_csv(OUT/'m2_referee_table3.csv',index=False);pd.DataFrame(weights).to_csv(OUT/'m2_fit_weights.csv',index=False)
 d=pd.read_parquet(ROOT/'data/processed/github_activity_international_enriched.parquet');d.date=pd.to_datetime(d.date)
 e=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet');d=d.merge(e[['country','login']],on=['country','login'],validate='many_to_one');d['active']=d.productive_events.gt(0)
 first=d[d.active].groupby(['country','login']).date.min().rename('first_productive_date').reset_index();first['late']=first.first_productive_date.ge('2024-06-29')
 cohorts=e[['country','login']].merge(first,on=['country','login'],how='left');cohorts['late']=cohorts.late.fillna(False);cohorts.to_csv(OUT/'m2_first_productive_dates.csv',index=False)
 counts=cohorts.groupby('country').agg(eligible=('login','size'),late=('late','sum'));counts['late_pct']=100*counts.late/counts.eligible;counts.to_csv(OUT/'m2_late_cohort_counts.csv')
 bd=cohorts[cohorts.country.eq('Bangladesh')];z=d[d.country.eq('Bangladesh')].merge(bd[['login','late']],on='login');z['period']=np.select([z.date.between('2024-06-20','2024-06-28'),z.date.between('2024-07-02','2024-07-17'),z.date.between('2024-08-14','2024-09-03')],['Jun20_28','Jul2_17','Aug14_Sep3'],default='other')
 daily=z.groupby(['date','late']).active.sum().unstack(fill_value=0).reindex(w.index,fill_value=0);daily.columns=['earlier_active_users','late_active_users'];daily.to_csv(OUT/'m2_cohort_daily.csv')
 late_n=int(bd.late.sum());early_n=len(bd)-late_n
 summary=dict(late_accounts=late_n,first_productive_after_jul17=int((bd.late & bd.first_productive_date.gt('2024-07-17')).sum()),jul1_total_active=int(daily.loc['2024-07-01'].sum()),jul2_total_active=int(daily.loc['2024-07-02'].sum()),jul1_to_jul2_late_increment=int(daily.loc['2024-07-02','late_active_users']-daily.loc['2024-07-01','late_active_users']),late_aug14_sep3_pct=100*daily.loc['2024-08-14':'2024-09-03','late_active_users'].mean()/late_n,earlier_aug14_sep3_pct=100*daily.loc['2024-08-14':'2024-09-03','earlier_active_users'].mean()/early_n)
 (OUT/'m2_cohort_summary.json').write_text(json.dumps(summary,indent=2))

 # Four active days in May, then fit only June 1–July 17. Retain archived bot exclusions.
 eligible=d[d.date.between('2024-05-01','2024-05-31')].groupby(['country','login']).date.nunique();fixed=eligible[eligible.ge(4)].reset_index()[['country','login']];n=fixed.groupby('country').size()
 q=d.merge(fixed,on=['country','login']);num=q.groupby(['date','country']).active.sum().unstack(fill_value=0).reindex(w.index,fill_value=0);wf=100*num.div(n,axis=1)
 rows2=[]
 for name,panel,start in [('original_full',w,'2024-05-01'),('original_June_fit',w,'2024-06-01'),('May_fixed_eligibility_June_fit',wf,'2024-06-01')]:
  r=sc.sc_stats(panel,'Bangladesh',donors,start,'2024-07-17','2024-07-18','2024-07-23');r.pop('weights');rows2.append(dict(sample=name,BD_users=int(n['Bangladesh']) if name.startswith('May_') else len(bd),**r))
 pd.DataFrame(rows2).to_csv(OUT/'m2_fixed_eligibility.csv',index=False);n.rename('May_eligible_users').to_csv(OUT/'m2_fixed_sample_counts.csv')
 # Local July push data contain repository names, not organization membership.
 push=pd.read_parquet(ROOT/'results/mechanism/bd_push_events_20240701_20240810.parquet');push['login']=push.pusher_login.str.lower();push.push_time=pd.to_datetime(push.push_time,utc=True);push=push[push.push_time.lt('2024-07-18')];late=set(bd.loc[bd.late,'login']);p=push[push.login.isin(late)].copy();p['owner']=p.repo.str.split('/').str[0].str.lower();p['basename']=p.repo.str.split('/').str[-1].str.lower()
 for col in ['repo','basename','owner']:
  p.groupby(col).agg(users=('login','nunique'),pushes=('login','size')).sort_values(['users','pushes'],ascending=False).to_csv(OUT/f'm2_shared_{col}.csv')
 (OUT/'m2_metadata_limits.json').write_text(json.dumps(dict(late_BD=len(late),late_with_pre_pushes=p.login.nunique(),account_created_at_available=False,organization_membership_available=False,repo_owner_is_not_verified_organization=True),indent=2))
 pending=ROOT/'analysis/pending/m2_accounts.graphql';lines=['# PENDING: not executed. Current public memberships are not historical 2024 membership.','query LateCohort {']
 for i,login in enumerate(sorted(late)):
  lines.append(f'  u{i}: user(login: {json.dumps(login)}) {{ login createdAt organizations(first: 100) {{ nodes {{ login }} pageInfo {{ hasNextPage endCursor }} }} }}')
 lines.append('}');pending.write_text('\n'.join(lines)+'\n')
 print(pd.DataFrame(rows).round(4).to_string(index=False));print(pd.DataFrame(rows2).round(4).to_string(index=False));print(counts.to_string());print('Late push coverage',p.login.nunique())
if __name__=='__main__':main()
