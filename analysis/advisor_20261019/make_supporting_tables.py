from pathlib import Path
import json
import pandas as pd
R=Path(__file__).resolve().parents[2];D=R/'results/advisor_20261019';T=R/'paper/latex/tables'
def table(name,caption,label,headers,rows,notes,widths=None):
 cols=widths or ('l'+'r'*(len(headers)-1))
 fixed={'tab_advisor_donors.tex','tab_sector_coverage.tex','tab_sector_support.tex','tab_sector_fit.tex','tab_sector_sc_sensitivity.tex','tab_residual_domains.tex'}
 placement='H' if name in fixed else 'htbp'
 text='\\begin{table}['+placement+']\n\\centering\n\\small\n\\caption{'+caption+'}\n\\label{'+label+'}\n\\begin{threeparttable}\n\\begin{tabular}{@{}'+cols+'@{}}\n\\toprule\n'
 text+=' & '.join(headers)+r' \\'+'\n\\midrule\n'
 text+='\n'.join(' & '.join(str(x) for x in row)+r' \\' for row in rows)
 text+='\n\\bottomrule\n\\end{tabular}\n\\begin{tablenotes}[flushleft]\n\\footnotesize\n\\item '+notes+'\n\\end{tablenotes}\n\\end{threeparttable}\n\\end{table}\n'
 (T/name).write_text(text)
def main():
 d=pd.read_csv(D/'donor_audit.csv').rename(columns={'Unnamed: 0':'country'})
 rows=[[r.country,f'{r.eligible_users:,.0f}',f'{r.pre_mean_pct:.2f}',f'{r.pre_sd_pp:.2f}',('--' if r.country=='Bangladesh' else f'{100*r.SC_weight:.2f}')] for r in d.itertuples()]
 table('tab_advisor_donors.tex','The full country sample and fitted national donor weights','tab:advisor_donors',['Country','Users','Pre mean (\\%)','Pre SD (pp)','Weight (\\%)'],rows,'The sample is unchanged. Pre-period: May 1--July 17. Every comparison country enters the fit; zero weight is an optimization result, not an exclusion. Bangladesh is the treated unit. Source: stored eligible-user and country-day panels; regenerated donor audit.')
 d=pd.read_csv(D/'sc_predictor_sensitivity.csv')
 rows=[[r.specification,str(r.predictors),f'{r.ATT_pp:.2f}',f'{r.pre_RMSPE_pp:.2f}',f'{r.validation_RMSPE_pp:.2f}'] for r in d.itertuples()]
 table('tab_advisor_lags.tex','Sensitivity to pre-treatment outcome predictors','tab:advisor_lags',['Predictors','$K$','ATT (pp)','Pre RMSPE','Holdout RMSPE'],rows,'Same users, donor pool and July 18--23 estimand in every row. Weekly means use the final 77 fitting days, grouped into 11 complete weeks. Holdout errors use a separate fit through June 30 and score July 1--17, applying each predictor rule to the shorter training sample; they are not treatment-period tuning statistics. All errors are in percentage points.')
 d=pd.read_csv(D/'residual_group_summary.csv')
 short={'All eligible':'All eligible','Core-window publishers':'Core publishers','No core-window publication':'Other eligible users','Onset-timestamp authors':'Onset authors','Delayed onset authors':'Delayed onset authors','Pre-restoration onset publishers':'Early onset publishers'}
 rows=[[short[r.group],f'{r.users:,}',f'{r.pre_activity_pct_mean:.2f}',f'{r.pre_pushes_median:.1f}',f'{r.pre_collaboration_pct_mean:.2f}'] for r in d.itertuples()]
 table('tab_advisor_residual.tex','Pre-shutdown characteristics of residual-activity cohorts','tab:advisor_residual',['Cohort','Users','Active days (\\%)','Pushes (median)','Collab. days (\\%)'],rows,'Characteristics are measured May 1--July 17. Core publishers record at least one primary public event on July 19--22. Onset authors have strict author-equals-pusher commits timestamped July 18 at 15:00 UTC through July 23, observed in pushes by August 10. Delayed authors push at least one such commit from July 24 onward; early publishers push before July 23. Cohorts overlap. These are descriptions of selected observed users, not causal effects or verified residence. Pushes is a pre-period count; activity and collaboration are shares of 78 days.','p{0.28\\textwidth}rrrr')
if __name__=='__main__':main()
