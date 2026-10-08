"""Audit only: do not guess the missing event-type map or bot thresholds."""
from pathlib import Path
import json
import db_dtypes  # registers historical BigQuery date extension
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'results/diagnostics/round2'
def main():
 d=pd.read_parquet(ROOT/'data/processed/github_activity_international_enriched.parquet');d.date=pd.to_datetime(d.date)
 e=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet')
 pre=d[d.date.between('2024-05-01','2024-07-17')]
 counts=pre.groupby(['country','login']).date.nunique().rename('reconstructed_any_event_days').reset_index()
 compare=e.merge(counts,on=['country','login'],how='left')
 assert (compare.pre_active_days==compare.reconstructed_any_event_days).all()
 metrics=pre.assign(commit_day=pre.commits.gt(0)).groupby(['country','login']).agg(max_daily_commits=('commits','max'),commit_days=('commit_day','sum'))
 metrics['commit_day_share']=metrics.commit_days/78
 metric_check=e.set_index(['country','login'])[['max_daily_commits','commit_days','commit_day_share']].join(metrics,rsuffix='_reconstructed')
 metric_matches={c:int(np.isclose(metric_check[c],metric_check[c+'_reconstructed'],rtol=0,atol=1e-12).sum()) for c in metrics.columns}
 assert all(n==len(e) for n in metric_matches.values())
 candidates=counts[counts.reconstructed_any_event_days>=4].merge(e[['country','login']],on=['country','login'],how='left',indicator=True)
 candidates['in_archived_eligible']=candidates['_merge'].eq('both'); candidates.drop(columns='_merge').to_csv(OUT/'r2_eligibility_candidates.csv',index=False)
 z=d.merge(e[['country','login']],on=['country','login'],validate='many_to_one')
 components=['pushes','pr_opened','pr_closed','issues_opened','issues_closed','releases','pr_reviews','issue_comments','pr_review_comments','commit_comments']
 active=z.productive_events.gt(0); zero=z[components].sum(axis=1).eq(0)
 assert np.array_equal(z.productive_output_active.astype(bool),(z.commits+z.issues_closed+z.pr_closed+z.releases)>0)
 bd=z[z.country.eq('Bangladesh') & z.date.between('2024-05-01','2024-07-17')]; denom=int(e.country.eq('Bangladesh').sum())*78
 stats={'eligible_users':len(e),'any_event_candidates_ge4':len(candidates),'excluded_rule_unknown':int((~candidates.in_archived_eligible).sum()),'eligible_primary_active_userdays':int(active.sum()),'active_without_documented_components':int((active&zero).sum()),'primary_pre_BD_pct':100*bd.productive_events.gt(0).sum()/denom,'secondary_pre_BD_pct':100*bd.productive_output_active.sum()/denom,'name_bot_retained':int(e.name_bot.sum()),'behavior_bot_retained':int(e.behavior_bot.sum()),'exact_event_type_mapping':'not identifiable from aggregated files; upstream SQL missing'}
 stats['retained_behavior_metric_exact_matches']=metric_matches
 # Independent selected-event panel provides only eight event types. Test
 # whether even unrestricted linear coefficients can reproduce the primary
 # counts on common Bangladesh user-days; if not, no subset is an exact map.
 sector=pd.read_parquet(ROOT/'data/replication/sector/bd_preactive20000_repo_event_day_metadata.parquet')
 sector['date']=pd.to_datetime(sector.event_date)
 sector=sector[sector.date.between('2024-05-01','2024-09-04')]
 types=sector.groupby(['login_lower','date','event_type']).event_count.sum().unstack(fill_value=0)
 types.index=types.index.set_names(['login','date'])
 common=types.join(d[d.country.eq('Bangladesh')].set_index(['login','date'])[['productive_events']],how='inner')
 X=common[types.columns].to_numpy(float);y=common.productive_events.to_numpy(float)
 stats['independent_panel_types']=list(types.columns)
 stats['independent_common_userdays']=len(common)
 stats['event_matrix_rank']=int(np.linalg.matrix_rank(X))
 stats['augmented_rank_with_primary']=int(np.linalg.matrix_rank(np.column_stack([X,y])))
 (OUT/'r2_definitions.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
