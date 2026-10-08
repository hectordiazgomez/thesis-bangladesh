"""Advisor-only donor-size, weekday, difference-in-means and conformal prototypes.
CWZ sharp constant-effect null: refit on 78+6 null-imputed days, then all 84
circular residual shifts, S1 = sum(abs(post residual))/sqrt(6). This is not an
exact country-randomization p-value or an unrestricted-average-effect interval.
"""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/diagnostics/round2'
def main():
 spec=importlib.util.spec_from_file_location('sc',ROOT/'analysis/synthetic_control/01_reproduce_sc.py');sc=importlib.util.module_from_spec(spec);spec.loader.exec_module(sc)
 w=sc.load_panel();donors=list(w.columns.drop('Bangladesh'));pre=w.loc[:'2024-07-17'];block=w.loc[:'2024-07-23'];assert len(pre)==78 and len(block)==84
 r=sc.sc_stats(w,'Bangladesh',donors,'2024-05-01','2024-07-17','2024-07-18','2024-07-23');wt=r.pop('weights')
 # Pre-period country-specific day-of-week deviations, with mean retained.
 dow=pre.groupby(pre.index.dayofweek).mean()-pre.mean();adjusted=w.copy()
 for i in range(7):adjusted.loc[adjusted.index.dayofweek==i]=w.loc[w.index.dayofweek==i]-dow.loc[i]
 alt=sc.sc_stats(adjusted,'Bangladesh',donors,'2024-05-01','2024-07-17','2024-07-18','2024-07-23');alt.pop('weights')
 pd.DataFrame([dict(specification='original',**r),dict(specification='pre_fitted_country_weekday_adjusted',**alt)]).to_csv(OUT/'m4_weekday_sensitivity.csv',index=False)
 hol=pd.read_parquet(ROOT/'results/synthetic_control/country_day_donor_pool_with_holidays.parquet');hol.date=pd.to_datetime(hol.date);h=hol[hol.country.eq('Bangladesh')].set_index('date').is_holiday.astype(bool)
 dd=pd.DataFrame({'Bangladesh':w.Bangladesh,'Synthetic':w[donors]@wt});dd=dd.loc['2024-05-01':'2024-06-30'];dd=dd.loc[~h.reindex(dd.index)];dw=dd.groupby(dd.index.dayofweek).mean();dw['gap']=dw.Bangladesh-dw.Synthetic;dw.index=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];dw.to_csv(OUT/'m4_referee_weekdays.csv')
 stats=[]
 for flag,data in [(False,w),(True,w.mask(hol.pivot(index='date',columns='country',values='is_holiday').astype(bool)))]:
  a=data.loc[:'2024-07-17'].mean();b=data.loc['2024-07-18':'2024-07-23'].mean();stats.append(dict(remove_holidays=flag,BD_pre=a.Bangladesh,BD_post=b.Bangladesh,donor_pre=a[donors].mean(),donor_post=b[donors].mean(),difference_in_means=(b.Bangladesh-a.Bangladesh)-(b[donors].mean()-a[donors].mean())))
 pd.DataFrame(stats).to_csv(OUT/'m4_did_difference_in_means.csv',index=False)
 e=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet');n=e.groupby('country').size().rename('archived_eligible_users').reset_index();n['passes_1000_size_only']=n.archived_eligible_users.ge(1000);n['external_screen']='not yet established';n.loc[n.country.eq('Pakistan'),'external_screen']='July31 disruption documented; exclusion under whole-period rule';n.to_csv(OUT/'m4_local_donor_size_screen.csv',index=False)
 rows=[];X=block[donors].to_numpy();y=block.Bangladesh.to_numpy();grid=np.arange(-25,5.00001,.25)
 for tau in grid:
  null=y.copy();null[-6:]-=tau;beta=sc.fit_sc(null,X);resid=null-X@beta
  vals=np.array([np.abs(np.roll(resid,k)[-6:]).sum()/np.sqrt(6) for k in range(84)]);p=float(np.mean(vals>=vals[0]-1e-10))
  rows.append(dict(sharp_constant_effect_pp=tau,p_circular=p,observed_S1=vals[0],n_pre=78,n_post=6,n_shifts=84))
 q=pd.DataFrame(rows);q.to_csv(OUT/'m4_conformal_constant_path_grid.csv',index=False);accepted=q[q.p_circular.gt(.05)]
 # Stability diagnostics for the original pre-fit residual; not a proof of stationarity.
 resid=pre.Bangladesh-pre[donors]@wt
 summary=dict(p_sharp_zero=float(q.loc[q.sharp_constant_effect_pp.eq(0),'p_circular'].iloc[0]),accepted_grid_min=float(accepted.sharp_constant_effect_pp.min()),accepted_grid_max=float(accepted.sharp_constant_effect_pp.max()),accepted_grid_count=len(accepted),pre_residual_lag1_autocorrelation=resid.autocorr(1),pre_gap_MayJun=resid.loc[:'2024-06-30'].mean(),pre_gap_July=resid.loc['2024-07-01':].mean(),weekday_adjusted_ATT_pp=alt['ATT'])
 (OUT/'m4_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(pd.DataFrame(stats).to_string(index=False))
if __name__=='__main__':main()
