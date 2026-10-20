from pathlib import Path
import json,math
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from make_supporting_tables import table
from sector_estimation import ROOT,OUT,NAMES
def main():
 estimates=pd.read_csv(OUT/'sector_sc_estimates.csv',dtype={'code':str})
 main=estimates[estimates.variant.eq('historical_readme_080')].copy().sort_values('code')
 named=main[main.code.ne('Unclassified')]
 cv=pd.read_csv(OUT/'sector_classification_coverage.csv');cv=cv[cv.variant.eq('historical_readme_080')]
 bd=cv[cv.country.eq('Bangladesh')].iloc[0]
 support=pd.read_csv(OUT/'sector_support.csv',dtype={'code':str});support=support[support.variant.eq('historical_readme_080')]
 rows=[[r.sector,f'{r.BD_users:,}',str(r.donors),f'{r.ATT:.2f}',f'{r.relative_effect_pct:.1f}',f'{r.pre_RMSPE:.2f}',f'{r.rank_p_ATT:.3f}'] for r in main.itertuples()]
 table('tab_sector_sc.tex','International synthetic controls by pre-treatment repository domain','tab:sector_sc',['Domain','$N_{BD,s}$','$J_s$','ATT (pp)','Rel. (\\%)','Pre RMSPE','Rank'],rows,'Main assignment: historical README and score at least 0.80. All supported domains and the unclassified group are shown. Outcome: primary public activity anywhere on GitHub among users assigned before treatment. ATT averages July 18--23. Rank compares absolute ATT with country placebos; its minimum depends on donor count. These are conditional comparative estimates, not effects on total industrial output or evidence that domain effects differ statistically.','p{0.23\\textwidth}rrrrrr')
 table('tab_sector_coverage.tex','International historical-text classification coverage','tab:sector_coverage',['Country','Eligible','README','Assigned','Assigned (\\%)'],[[r.country,f'{r.eligible:,}',f'{r.historical_readme:,}',f'{r.assigned:,}',f'{r.assigned_pct:.1f}'] for r in cv.itertuples()],'Counts refer to users and their dominant pre-treatment repository. Assigned requires an available July 17 README and classifier score at least 0.80. Other eligible users remain unclassified; they are not removed from national estimates. Retrieval takes place in October 2026 and cannot recover every repository available in 2024.')
 table('tab_sector_support.tex','Pre-specified support screen for every domain','tab:sector_support',['Domain','Bangladesh users','Eligible donors','Estimated'],[[r.sector,str(r.BD_users),str(r.donors),'Yes' if r.supported else 'No'] for r in support.itertuples()],'At least 30 Bangladesh users and five donor countries with at least 30 users each are required. The rule uses sample support, not treatment-period effect size. Unreported estimates in the main table correspond to this screen, not a zero estimated effect.','p{0.38\\textwidth}rrr')
 piv=estimates.pivot(index='sector',columns='variant',values='ATT')
 variants=['historical_readme_070','historical_readme_080','historical_readme_090','name_fallback_080']
 rows=[[r]+[f'{piv.loc[r,v]:.2f}' if pd.notna(piv.loc[r,v]) else '--' for v in variants] for r in sorted(piv.index)]
 table('tab_sector_sc_sensitivity.tex','Sector-cohort ATT sensitivity to classification rules','tab:sector_sc_sensitivity',['Domain','0.70','0.80','0.90','Name fallback'],rows,'Effects in percentage points. The first three columns require a historical README. The final column admits classifications from names alone at score 0.80. Each rule changes the fixed cohort and may change donor support. A dash means insufficient support, not a zero effect; columns are therefore not estimates for an identical population.','p{0.38\\textwidth}rrrr')
 rows=[[r.sector,f'{r.normalized_pre_RMSPE:.2f}',f'{r.pre_holdout_RMSPE:.2f}',f'{r.RMSPE_ratio:.2f}',f'{r.rank_p_ratio:.3f}'] for r in main.itertuples()]
 table('tab_sector_fit.tex','Sector-cohort fit and scale-adjusted placebo diagnostics','tab:sector_fit',['Domain','Pre RMSPE / mean','Holdout (pp)','Post/pre RMSPE','Ratio rank'],rows,'The normalized fit divides pre-period RMSPE by mean pre-period activity. Holdout weights are fitted through June 30 and evaluated July 1--17, conditional on July 17 cohort definitions. Large errors limit counterfactual credibility. Ratio rank compares the shutdown/pre-period RMSPE ratio with sector-specific donor placebos.','p{0.27\\textwidth}rrrr')
 loo=pd.read_csv(OUT/'sector_leave_one_out.csv',dtype={'code':str});bounds=loo.groupby('code').ATT.agg(['min','max'])
 fig,ax=plt.subplots(figsize=(8.4,max(3.5,len(main)*.45+1.0)))
 y=np.arange(len(main));ax.axvline(0,color='#777777',lw=.8)
 for i,r in enumerate(main.itertuples()):
  b=bounds.loc[r.code];ax.plot([b['min'],b['max']],[i,i],color='#8397aa',lw=3);ax.plot(r.ATT,i,'o',color='#154c79',ms=6)
 ax.set_yticks(y,main.sector);ax.invert_yaxis();ax.set_xlabel('Change in active-user rate (percentage points)');ax.grid(axis='x',alpha=.15)
 ax.spines[['top','right','left']].set_visible(False);fig.tight_layout();fig.savefig(ROOT/'paper/latex/figures/fig_advisor_sector_sc.pdf');plt.close(fig)
 paths=pd.read_csv(OUT/'sector_sc_paths.csv',dtype={'code':str},parse_dates=['date']);paths=paths[paths.variant.eq('historical_readme_080')]
 ncols=3;nrows=math.ceil(len(main)/ncols);fig,axes=plt.subplots(nrows,ncols,figsize=(10.5,2.4*nrows),squeeze=False)
 for ax,r in zip(axes.flat,main.itertuples()):
  z=paths[paths.code.eq(r.code)];ax.plot(z.date,z.actual,color='#154c79',lw=1,label='Bangladesh');ax.plot(z.date,z.synthetic,color='#bc6c25',lw=1,label='Synthetic');ax.axvspan(pd.Timestamp('2024-07-18'),pd.Timestamp('2024-07-24'),alpha=.15,color='grey');ax.set_title(r.sector,fontsize=9);ax.xaxis.set_major_locator(mdates.MonthLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'));ax.tick_params(labelsize=8);ax.spines[['top','right']].set_visible(False)
 for ax in list(axes.flat)[len(main):]:ax.set_visible(False)
 axes.flat[0].legend(fontsize=7,frameon=False);fig.supylabel('Daily active users (%)',fontsize=9);fig.tight_layout();fig.savefig(ROOT/'paper/latex/figures/fig_advisor_sector_paths.pdf');plt.close(fig)
 pct=float(named.BD_users.sum()/10241*100);weighted=float((named.ATT*named.BD_sample_share).sum())
 summary={'supported_named_domains':len(named),'BD_assigned_users':int(bd.assigned),'BD_assigned_pct':float(bd.assigned_pct),'BD_supported_named_users':int(named.BD_users.sum()),'BD_supported_named_pct':pct,'named_ATT_min':float(named.ATT.min()),'named_ATT_max':float(named.ATT.max()),'weighted_contribution_supported_named_pp':weighted,'national_headline_unchanged':True}
 (OUT/'sector_report_summary.json').write_text(json.dumps(summary,indent=2))
 # Cross-tabulate the residual groups without inferring employer or occupation.
 members=pd.read_parquet(OUT/'sector_membership_historical_readme_080.parquet')
 residual=pd.read_parquet(OUT/'residual_user_characteristics.parquet').reset_index()
 residual=residual.merge(members[members.country.eq('Bangladesh')][['login','group']],on='login',validate='one_to_one')
 cohort_rows=[]
 for cohort,mask in [('All eligible',pd.Series(True,index=residual.index)),('Core publishers',residual.core_public_active),('Onset authors',residual.onset_author),('Delayed onset authors',residual.delayed_onset_author)]:
  z=residual[mask]
  for group,n in z.groupby('group').size().items():cohort_rows.append(dict(cohort=cohort,code=group,domain=NAMES.get(group,group),users=int(n),cohort_users=len(z),cohort_pct=100*n/len(z)))
 cohorts=pd.DataFrame(cohort_rows);cohorts.to_csv(OUT/'residual_domain_composition.csv',index=False)
 cp=cohorts.pivot(index='domain',columns='cohort',values='users').fillna(0)
 table('tab_residual_domains.tex','Repository-domain composition of residual-activity cohorts','tab:residual_domains',['Pre-treatment domain',r'\shortstack{All\\eligible}',r'\shortstack{Core\\publishers}',r'\shortstack{Onset\\authors}',r'\shortstack{Delayed\\authors}'],[[domain]+[f'{int(cp.loc[domain,col]):,}' for col in ['All eligible','Core publishers','Onset authors','Delayed onset authors']] for domain in sorted(cp.index)],'Counts, not effects. Historical README classification at score 0.80; all unclassified accounts remain visible. Cohorts overlap and have the definitions in the mechanism section. Small cells and substantial unclassified coverage do not establish occupational specialization.','p{0.34\\textwidth}rrrr')
 text=r'''\subsection{International comparisons by repository domain}
\label{sec:sector_sc_results}

The international extension complements the before--after sector comparison with a separate comparison-country counterfactual for each fixed pre-treatment repository-domain cohort. '''+f'The main historical-text rule assigns {int(bd.assigned):,} of the 10,241 Bangladesh accounts ({bd.assigned_pct:.1f} percent) to a domain. Of these, {int(named.BD_users.sum()):,} accounts belong to {len(named)} named domains that pass the support rule; the remaining eligible accounts are either in unsupported named groups or the separately reported unclassified group. '+r'''Coverage by country and the full support screen are reported in \cref{tab:sector_coverage,tab:sector_support}. The complete country-by-country appendix (\cref{app:country_atlas}) displays all 20 groups, including unclassified accounts, across all 15 countries: 300 panels, of which 45 have no assigned users and 144 contain fewer than 30. These cells remain visible even when they cannot support estimation. A country-domain denominator of zero is not a zero activity rate, and small cells can produce large daily percentage movements.

\input{tables/tab_sector_sc}

'''+f'Across the {len(named)} supported named domains, estimated July 18--23 changes range from {named.ATT.min():.2f} to {named.ATT.max():.2f} percentage points. '+r'''\Cref{fig:advisor_sector_sc} shows every supported estimate and the range obtained when one donor is omitted. These ranges are sensitivity summaries, not confidence intervals. \Cref{tab:sector_fit} reports pre-fit and scale-adjusted placebo ranks, and \cref{tab:sector_sc_sensitivity} retains all classification-threshold comparisons. Smaller domain samples and fewer eligible donors make the reference distributions coarser than in the national analysis. No domain ranking is treated as a statistically established ranking of causal exposure.

\begin{figure}[htbp]
\centering
\caption{Synthetic-control gaps across pre-treatment repository domains}
\label{fig:advisor_sector_sc}
\includegraphics[width=\textwidth]{fig_advisor_sector_sc.pdf}
\fignote{Points show the July 18--23 ATT for all supported groups. Horizontal segments span the estimates from omitting each donor country in turn; they are not sampling confidence intervals. Assignment uses pre-shutdown activity and historical README classification at score 0.80. The outcome follows assigned users' public activity across repositories.}
\end{figure}

'''+f'The supported named groups comprise {pct:.1f} percent of eligible Bangladesh accounts. Weighting their estimates by their shares of the national eligible sample gives a contribution of {weighted:.2f} percentage points. '+r'''This is a partial decomposition for the covered groups, not a national treatment effect: unsupported groups have no assigned zero effect, and the unclassified group is substantial. Moreover, domain-specific weights differ from the national weights. The national headline therefore remains the original $-$13.26 percentage points.

These comparisons strengthen the design relative to the older within-Bangladesh recovery indices because they introduce untreated-country counterfactuals and freeze group membership before the shock. They still depend on country-domain comparability, imperfect text classification and the absence of coincident group-specific shocks. They concern public activity among users associated with a repository domain; they do not establish effects on firms, employment sectors or industrial output. The separate recovery indices and their broader Bangladesh sample are preserved in the appendix (\cref{sec:sector_results}).
'''
 indexed=main.set_index('code')
 if {'44-45','51','61','62'}.issubset(indexed.index):
  retail,info,edu,health=(indexed.loc[k] for k in ['44-45','51','61','62'])
  interpretation=(f"Retail- and Information-associated cohorts provide relatively closer pre-period fits: their RMSPEs are {retail.pre_RMSPE:.2f} and {info.pre_RMSPE:.2f} percentage points, compared with estimated shutdown gaps of {retail.ATT:.2f} and {info.ATT:.2f}. "
   f"Health has a larger point estimate ({health.ATT:.2f}) but also a pre-period RMSPE of {health.pre_RMSPE:.2f}; Education's earlier-fit holdout error is {edu.pre_holdout_RMSPE:.2f} points. "
   "These diagnostics weaken a comparison of the largest point estimates. Every leave-one-donor-out estimate remains negative, but this robustness does not resolve imperfect fit, classifier error or common exposure to unrest.\n\n")
  text=text.replace(r'\begin{figure}[htbp]',interpretation+r'\begin{figure}[htbp]',1)
 (ROOT/'paper/latex/sections/06_sector_results.tex').write_text(text)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
