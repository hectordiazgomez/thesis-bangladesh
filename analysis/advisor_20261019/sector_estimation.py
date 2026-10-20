"""International SCM by fixed, pre-treatment repository-domain cohort.

This estimates heterogeneity in public activity among users associated with a
repository application domain, not firm industry output. Support rules are
fixed before viewing treatment estimates: >=30 users per country/domain and
>=5 donor countries. All supported domains are reported, including poor fits.
"""
from pathlib import Path
import importlib.util,json,sqlite3
import numpy as np,pandas as pd
import db_dtypes
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'data/advisor_20261019';OUT=ROOT/'results/advisor_20261019';OUT.mkdir(parents=True,exist_ok=True)
NAMES={'11':'Agriculture','21':'Mining','22':'Utilities','23':'Construction','31-33':'Manufacturing','42':'Wholesale','44-45':'Retail','48-49':'Transport','51':'Information','52':'Finance','53':'Real estate','54':'Professional services','56':'Administrative support','61':'Education','62':'Health','71':'Arts and recreation','72':'Accommodation and food','81':'Other services','92':'Public administration','Unclassified':'Unclassified'}
def main():
 spec=importlib.util.spec_from_file_location('sc',ROOT/'analysis/synthetic_control/01_reproduce_sc.py');sc=importlib.util.module_from_spec(spec);spec.loader.exec_module(sc)
 c=sqlite3.connect(f'file:{DATA}/international_sector.sqlite?mode=ro',uri=True)
 pred=pd.read_sql_query('SELECT repo,status,code,score,revision,source FROM repos',c)
 if pred.code.isna().any():raise RuntimeError(f'Classification incomplete: {pred.code.isna().sum()} repositories')
 eligible=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet')[['country','login']]
 dominant=pd.read_parquet(DATA/'user_dominant_pre_repo.parquet')
 members=eligible.merge(dominant,on=['country','login'],how='left',validate='one_to_one').merge(pred,left_on='repo_name',right_on='repo',how='left',validate='many_to_one')
 d=pd.read_parquet(ROOT/'data/processed/github_activity_international_enriched.parquet');d.date=pd.to_datetime(d.date);d=d.merge(eligible,on=['country','login'],validate='many_to_one');d['active']=d.productive_events.gt(0)
 dates=pd.date_range('2024-05-01','2024-09-04');countries=sorted(eligible.country.unique())
 variants=[('historical_readme_080',.8,True),('historical_readme_070',.7,True),('historical_readme_090',.9,True),('name_fallback_080',.8,False)]
 results=[];allweights=[];placebos=[];paths=[];supports=[];loo=[];coverage=[];identity=[]
 for variant,threshold,readme in variants:
  m=members.copy();ok=m.score.ge(threshold)&m.code.notna()
  if readme:ok &= m.status.eq('ok')
  m['group']=m.code.where(ok,'Unclassified')
  m.to_parquet(OUT/f'sector_membership_{variant}.parquet',index=False)
  for country,z in m.groupby('country'):
   coverage.append(dict(variant=variant,country=country,eligible=len(z),dominant_repository=z.repo_name.notna().sum(),historical_readme=z.status.eq('ok').sum(),assigned=(z.group!='Unclassified').sum(),assigned_pct=100*(z.group!='Unclassified').mean()))
  ns=m.groupby(['group','country']).size().unstack(fill_value=0).reindex(index=list(NAMES),columns=countries,fill_value=0)
  z=d.merge(m[['country','login','group']],on=['country','login'],validate='many_to_one')
  nums=z.groupby(['group','date','country']).active.sum()
  # Exact accounting identity across mutually exclusive groups, including unclassified.
  national=z.groupby(['date','country']).active.sum();parts=nums.groupby(['date','country']).sum()
  identity.append(dict(variant=variant,max_numerator_difference=float((national-parts).abs().max()),users_partitioned=len(m)))
  for group,n in ns.iterrows():
   pool=[x for x in countries if x!='Bangladesh' and n[x]>=30]
   supported=n['Bangladesh']>=30 and len(pool)>=5
   supports.append(dict(variant=variant,code=group,sector=NAMES.get(group,group),BD_users=int(n['Bangladesh']),donors=len(pool),supported=supported,reason='supported' if supported else 'fewer than 30 Bangladesh users or five donor countries with 30 users'))
   if not supported:continue
   counts=nums.loc[group].unstack('country',fill_value=0).reindex(index=dates,columns=countries,fill_value=0).fillna(0)
   rates=100*counts.div(n.replace(0,np.nan),axis=1)
   res=sc.sc_stats(rates,'Bangladesh',pool,'2024-05-01','2024-07-17','2024-07-18','2024-07-23');weights=res.pop('weights');premean=rates.loc[:'2024-07-17','Bangladesh'].mean()
   actual=res['ATT'];ratio=res['RMSPE_ratio'];rankatt=1;rankratio=1
   for treated in pool:
    pr=sc.sc_stats(rates,treated,[x for x in pool if x!=treated],'2024-05-01','2024-07-17','2024-07-18','2024-07-23');pr.pop('weights');placebos.append(dict(variant=variant,code=group,treated=treated,**pr))
    rankatt+=abs(pr['ATT'])>=abs(actual)-1e-10;rankratio+=pr['RMSPE_ratio']>=ratio-1e-10
   # Validation uses earlier fit only, with the original eligible/domain cohort held fixed.
   vr=sc.sc_stats(rates,'Bangladesh',pool,'2024-05-01','2024-06-30','2024-07-01','2024-07-17');validation=vr['post_RMSPE']
   res.update(dict(variant=variant,code=group,sector=NAMES.get(group,group),BD_users=int(n['Bangladesh']),donors=len(pool),pre_mean_pct=premean,normalized_pre_RMSPE=res['pre_RMSPE']/premean if premean else np.nan,pre_holdout_RMSPE=validation,rank_p_ATT=rankatt/(len(pool)+1),rank_p_ratio=rankratio/(len(pool)+1),BD_sample_share=n['Bangladesh']/10241))
   results.append(res)
   allweights.extend(dict(variant=variant,code=group,country=x,weight=float(v),country_group_users=int(n[x])) for x,v in weights.items())
   syn=rates[pool]@weights
   for date in dates:paths.append(dict(variant=variant,code=group,date=str(date.date()),actual=float(rates.loc[date,'Bangladesh']),synthetic=float(syn.loc[date]),gap=float(rates.loc[date,'Bangladesh']-syn.loc[date])))
   if variant=='historical_readme_080':
    for excluded in pool:
     lr=sc.sc_stats(rates,'Bangladesh',[x for x in pool if x!=excluded],'2024-05-01','2024-07-17','2024-07-18','2024-07-23');lr.pop('weights');loo.append(dict(code=group,excluded=excluded,**lr))
  print('ESTIMATED',variant,flush=True)
 pd.DataFrame(results).to_csv(OUT/'sector_sc_estimates.csv',index=False);pd.DataFrame(allweights).to_csv(OUT/'sector_sc_weights.csv',index=False);pd.DataFrame(placebos).to_csv(OUT/'sector_sc_placebos.csv',index=False);pd.DataFrame(paths).to_csv(OUT/'sector_sc_paths.csv',index=False);pd.DataFrame(supports).to_csv(OUT/'sector_support.csv',index=False);pd.DataFrame(loo).to_csv(OUT/'sector_leave_one_out.csv',index=False);pd.DataFrame(coverage).to_csv(OUT/'sector_classification_coverage.csv',index=False)
 (OUT/'sector_partition_checks.json').write_text(json.dumps(identity,indent=2))
 print(pd.DataFrame(results).query("variant=='historical_readme_080'")[['sector','BD_users','donors','ATT','relative_effect_pct','pre_RMSPE','rank_p_ATT','rank_p_ratio']].round(3).to_string(index=False))
if __name__=='__main__':main()
