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
 candidates=counts[counts.reconstructed_any_event_days>=4].merge(e[['country','login']],on=['country','login'],how='left',indicator=True)
 candidates['in_archived_eligible']=candidates['_merge'].eq('both'); candidates.drop(columns='_merge').to_csv(OUT/'r2_eligibility_candidates.csv',index=False)
 z=d.merge(e[['country','login']],on=['country','login'],validate='many_to_one')
 components=['pushes','pr_opened','pr_closed','issues_opened','issues_closed','releases','pr_reviews','issue_comments','pr_review_comments','commit_comments']
 active=z.productive_events.gt(0); zero=z[components].sum(axis=1).eq(0)
 assert np.array_equal(z.productive_output_active.astype(bool),(z.commits+z.issues_closed+z.pr_closed+z.releases)>0)
 bd=z[z.country.eq('Bangladesh') & z.date.between('2024-05-01','2024-07-17')]; denom=int(e.country.eq('Bangladesh').sum())*78
 stats={'eligible_users':len(e),'any_event_candidates_ge4':len(candidates),'excluded_rule_unknown':int((~candidates.in_archived_eligible).sum()),'eligible_primary_active_userdays':int(active.sum()),'active_without_documented_components':int((active&zero).sum()),'primary_pre_BD_pct':100*bd.productive_events.gt(0).sum()/denom,'secondary_pre_BD_pct':100*bd.productive_output_active.sum()/denom,'name_bot_retained':int(e.name_bot.sum()),'behavior_bot_retained':int(e.behavior_bot.sum()),'exact_event_type_mapping':'not identifiable from aggregated files; upstream SQL missing'}
 (OUT/'r2_definitions.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
