"""Reproduce the recovered primary-map audit and account-age summaries."""
from pathlib import Path
import json
import pandas as pd
import db_dtypes
from sector_classify import ROOT,DATA,TYPES
OUT=ROOT/'results/advisor_20261019'
def main():
 e=pd.read_parquet(DATA/'international_repo_event_day.parquet');e.date=pd.to_datetime(e.date)
 p=e[e.event_type.isin(TYPES)].groupby(['country','login','date']).event_count.sum().rename('recovered')
 d=pd.read_parquet(ROOT/'data/processed/github_activity_international_enriched.parquet');d.date=pd.to_datetime(d.date)
 u=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet')
 z=d[d.date.le('2024-07-23')].merge(u[['country','login']],on=['country','login'],validate='many_to_one')
 a=z.set_index(['country','login','date'])[['productive_events']].join(p,how='outer').fillna(0);a['delta']=a.recovered-a.productive_events
 bad=a[a.delta.ne(0)];bad.reset_index().to_csv(OUT/'primary_mapping_discrepancies.csv',index=False)
 stats={'rows_compared':len(a),'exact_count_matches':int(a.delta.eq(0).sum()),'count_mismatches':len(bad),'binary_mismatches':int((a.recovered.gt(0)!=a.productive_events.gt(0)).sum()),'event_types':TYPES}
 (OUT/'primary_mapping_validation.json').write_text(json.dumps(stats,indent=2))
 assert not len(bad),'Recovered event map does not reproduce archived counts'
 e.groupby(['country','event_type']).event_count.sum().to_csv(OUT/'international_event_type_counts.csv')
 a=pd.DataFrame(json.loads(l) for l in (DATA/'bd_account_creation.jsonl').read_text().splitlines());a['login']=a.requested_login.str.lower();a['created_at']=pd.to_datetime(a.createdAt,utc=True)
 f=pd.read_parquet(OUT/'residual_user_characteristics.parquet').reset_index().merge(a[['login','created_at']],on='login',how='left',validate='one_to_one')
 first=d[d.country.eq('Bangladesh')].groupby('login').date.min();first=pd.to_datetime(first,utc=True)
 f=f.join(first.rename('first_observed'),on='login')
 # Daily events do not retain within-day times: permit creation anywhere on first UTC day.
 f['date_consistent']=f.created_at.notna()&f.created_at.lt(f.first_observed+pd.Timedelta(days=1))
 f['account_age_years']=((pd.Timestamp('2024-07-18',tz='UTC')-f.created_at).dt.total_seconds()/(365.25*86400)).where(f.date_consistent)
 rows=[]
 for name,mask in [('All eligible',pd.Series(True,index=f.index)),('Core publishers',f.core_public_active),('Other eligible',~f.core_public_active),('Onset authors',f.onset_author),('Delayed onset authors',f.delayed_onset_author)]:
  z=f[mask];rows.append(dict(group=name,users=len(z),resolved_created_at=int(z.created_at.notna().sum()),consistent_age_n=int(z.date_consistent.sum()),median_age_years=z.account_age_years.median(),mean_age_years=z.account_age_years.mean(),created_in_2024_pct=100*z.loc[z.date_consistent,'created_at'].ge('2024-01-01').mean()))
 pd.DataFrame(rows).to_csv(OUT/'residual_account_age.csv',index=False);f.to_parquet(OUT/'residual_user_characteristics_with_age.parquet',index=False)
 # Descriptive frequency of residual publication across pre-activity quartiles.
 f['pre_activity_quartile']=pd.qcut(f.pre_productive_days.rank(method='average'),4,labels=['Q1','Q2','Q3','Q4'])
 f.groupby('pre_activity_quartile',observed=True).agg(users=('login','size'),core_publishers=('core_public_active','sum'),onset_authors=('onset_author','sum'),mean_pre_active_days=('pre_productive_days','mean')).assign(core_publication_pct=lambda x:100*x.core_publishers/x.users,onset_authorship_pct=lambda x:100*x.onset_authors/x.users).to_csv(OUT/'residual_pre_activity_quartiles.csv')
 z=e[e.country.eq('Bangladesh')&e.date.lt('2024-07-18')&e.event_type.eq('PushEvent')].copy()
 z['own_account_repo']=z.repo_name.str.split('/').str[0].str.lower().eq(z.login)
 totals=z.groupby('login').event_count.sum();own=z[z.own_account_repo].groupby('login').event_count.sum()
 f=f.set_index('login');f['own_repo_share']=100*own.reindex(f.index,fill_value=0)/totals.reindex(f.index).replace(0,float('nan'))
 ownrows=[]
 for cohort,mask in [('All eligible',pd.Series(True,index=f.index)),('Core publishers',f.core_public_active),('Other eligible',~f.core_public_active),('Onset authors',f.onset_author),('Delayed onset authors',f.delayed_onset_author)]:
  x=f[mask].own_repo_share;ownrows.append(dict(cohort=cohort,users_with_pre_pushes=int(x.notna().sum()),mean_own_account_repo_push_share_pct=x.mean(),median_own_account_repo_push_share_pct=x.median()))
 pd.DataFrame(ownrows).to_csv(OUT/'residual_own_repository_activity.csv',index=False)
 print('PRIMARY_MAP_VALIDATED',stats,flush=True);print(pd.DataFrame(rows).round(3).to_string(index=False))
if __name__=='__main__':main()
