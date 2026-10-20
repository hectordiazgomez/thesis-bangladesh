"""Data identities and numerical checks independent of manuscript generation."""
from pathlib import Path
import json,sqlite3,zlib
import numpy as np,pandas as pd
from scipy.optimize import minimize
from sector_classify import ROOT,DATA,TYPES
from supporting_analysis import scmod
OUT=ROOT/'results/advisor_20261019'
checks=[]
def check(name,value):
 checks.append({'check':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def main(report_path=None):
 e=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet')
 check('Original eligible sample 59158',len(e)==59158)
 check('No duplicate cross-country logins',not e.login.str.lower().duplicated().any())
 x=pd.read_parquet(DATA/'international_repo_event_day.parquet');x.date=pd.to_datetime(x.date)
 check('15 countries extracted',x.country.nunique()==15)
 check('Dates restricted to authorized window',x.date.min()==pd.Timestamp('2024-05-01') and x.date.max()==pd.Timestamp('2024-07-23'))
 p=x[x.date.lt('2024-07-18')&x.event_type.isin(TYPES)]
 dom=p.groupby(['country','login','repo_name']).agg(active_days=('date','nunique'),events=('event_count','sum')).reset_index().sort_values(['country','login','active_days','events','repo_name'],ascending=[True,True,False,False,True]).drop_duplicates(['country','login'])
 saved=pd.read_parquet(DATA/'user_dominant_pre_repo.parquet')
 j=dom.merge(saved,on=['country','login'],suffixes=('_new','_saved'),validate='one_to_one')
 check('Dominant repositories reproduce SQL extraction',len(j)==len(saved) and j.repo_name_new.eq(j.repo_name_saved).all() and j.active_days_new.eq(j.active_days_saved).all())
 audit=json.loads((OUT/'primary_mapping_validation.json').read_text());check('Recovered primary counts match exactly',audit['count_mismatches']==0 and audit['rows_compared']==799417)
 sc=scmod();panel=sc.load_panel();donors=list(panel.columns.drop('Bangladesh'));pre=panel.loc[:'2024-07-17'];w=sc.fit_sc(pre.Bangladesh.to_numpy(),pre[donors].to_numpy());post=panel.loc['2024-07-18':'2024-07-23'];att=(post.Bangladesh-post[donors]@w).mean()
 check('Original national ATT unchanged',abs(att-(-13.255939))<1e-6)
 X=pre[donors].to_numpy();y=pre.Bangladesh.to_numpy();r=minimize(lambda v:np.mean((y-X@v)**2),w,method='SLSQP',bounds=[(0,1)]*len(w),constraints={'type':'eq','fun':lambda v:v.sum()-1},options={'ftol':1e-12,'maxiter':3000})
 check('Independent constrained optimizer agrees',r.success and abs(r.fun-np.mean((y-X@w)**2))<1e-7)
 es=pd.read_csv(OUT/'sector_sc_estimates.csv',dtype={'code':str});ws=pd.read_csv(OUT/'sector_sc_weights.csv',dtype={'code':str});paths=pd.read_csv(OUT/'sector_sc_paths.csv',dtype={'code':str},parse_dates=['date'])
 check('All sector weights nonnegative',ws.weight.ge(-1e-10).all())
 check('All sector weights sum to one',np.allclose(ws.groupby(['variant','code']).weight.sum(),1,atol=1e-8))
 actual=paths[paths.date.between('2024-07-18','2024-07-23')].groupby(['variant','code']).gap.mean();a=es.set_index(['variant','code']).ATT
 check('Every sector ATT equals mean daily gap',np.allclose(actual.sort_index(),a.sort_index(),atol=1e-8))
 check('All reported groups meet support rule',es.BD_users.ge(30).all() and es.donors.ge(5).all())
 check('Rank probabilities respect donor resolution',(es.rank_p_ATT+1e-10>=1/(es.donors+1)).all() and (es.rank_p_ratio+1e-10>=1/(es.donors+1)).all())
 part=json.loads((OUT/'sector_partition_checks.json').read_text());check('Observed national activity exactly partitions into groups',all(v['max_numerator_difference']==0 and v['users_partitioned']==59158 for v in part))
 for variant in es.variant.unique():
  m=pd.read_parquet(OUT/f'sector_membership_{variant}.parquet')
  check(variant+' preserves all eligible users',len(m)==59158 and not m.duplicated(['country','login']).any())
  if variant.startswith('historical_readme'):
   assigned=m[m.group.ne('Unclassified')];check(variant+' assigns only historical READMEs',assigned.status.eq('ok').all())
 c=sqlite3.connect(f'file:{DATA}/international_sector.sqlite?mode=ro',uri=True)
 check('All selected repositories classified',c.execute('SELECT count(*) FROM repos WHERE code IS NULL').fetchone()[0]==0)
 check('All model revisions pinned',c.execute('SELECT count(*) FROM repos WHERE revision IS NULL OR revision != ?',('e40747e90bbc547e56b7145d2b97494bff69b42d',)).fetchone()[0]==0)
 check('No pending retrieval or query errors',c.execute("SELECT count(*) FROM repos WHERE status IS NULL OR status LIKE '%error%'").fetchone()[0]==0)
 check('Every successful historical README contains source text',all(blob and zlib.decompress(blob).decode('utf-8').strip() for (blob,) in c.execute("SELECT readme FROM repos WHERE status='ok'")))
 check('Legacy cache records all refreshed',c.execute("SELECT count(*) FROM repos WHERE source='existing_historical_cache'").fetchone()[0]==0)
 f=pd.read_parquet(OUT/'residual_user_characteristics.parquet');check('Residual core cohort 40',f.core_public_active.sum()==40);check('Onset-author cohort 250',f.onset_author.sum()==250);check('Delayed onset-author cohort 191',f.delayed_onset_author.sum()==191)
 target=Path(report_path) if report_path else OUT/'verification.json'
 target.write_text(json.dumps({'checks':checks,'count':len(checks),'all_passed':all(c['passed'] for c in checks)},indent=2));print('PASSED',len(checks),'checks')
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser()
 parser.add_argument('--report',help='Write verification to a new file, preserving prior results')
 main(parser.parse_args().report)
