"""Package the verified local revision without deleting or publishing files."""
from pathlib import Path
import csv,hashlib,json,shutil,zipfile
from sector_classify import ROOT

OUT=Path('/Users/hectoralbertodiazgomez/Documents/Codex/2026-10-19/go/outputs')
RESULT=ROOT/'results/advisor_20261019'
def main():
 verification=json.loads((RESULT/'verification.json').read_text())
 if not verification['all_passed']:raise RuntimeError('Analysis verification has not passed')
 OUT.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/'paper/latex/thesis.pdf',OUT/'thesis-bangladesh-revised.pdf')
 summary=json.loads((RESULT/'sector_report_summary.json').read_text())
 status=(
  'Bangladesh thesis revision - 19 October 2026\n\n'
  'All eight current advisor comments were addressed in the manuscript and/or new analyses.\n'
  'The original manuscript and notes are preserved under archive/advisor_20261019_before/.\n'
  'Original national results, raw/processed inputs and the prior sector database were preserved.\n\n'
  '1. Donor sample: all countries, sample sizes, pre-period rates and weights are shown;\n'
  '   the paper distinguishes data availability from positive fitted weights.\n'
  '2. Literature: expanded comparisons of designs, findings, mechanisms and limitations.\n'
  '3. Outcomes: plain-language GitHub definitions and explicit denominators; original SQL\n'
  '   recovered and all 799,417 overlapping primary user-day counts reproduced exactly.\n'
  '4. Methodology: constrained minimization, predictor matrix, weights and assumptions.\n'
  '5. Predictors: original daily-lag-only fit retained; five lag specifications and\n'
  '   pre-treatment holdout diagnostics reported. No unmeasured covariates are claimed.\n'
  '6. RDiT: detailed methods, figure and estimates moved to the appendix.\n'
  '7. International domain SCM: all 15 countries processed; 58,122 dominant pre-treatment\n'
  '   repositories classified with the pinned multilingual model. The main rule uses\n'
  '   nonempty historical README text and score >=0.80; empty/missing text is explicit.\n'
  f"   {summary['supported_named_domains']} named groups pass support rules. They cover "
  f"{summary['BD_supported_named_pct']:.1f}% of eligible Bangladesh users. All supported\n"
  '   estimates, donor weights, placebos, omitted-donor results and threshold sensitivities\n'
  '   are retained. Unclassified users are estimated separately, not discarded.\n'
  '8. Residual users: distinguish 40 core-window public users, 250 strict onset authors,\n'
  '   and 191 delayed onset authors; compare pre-activity, collaboration, pushes, account\n'
  '   age, concentration, repository ownership and domain composition.\n\n'
  'National headline remains -13.255939 percentage points.\n\n'
  'Limits still stated explicitly: repository domains are not verified employment\n'
  'industries; small donor pools limit inference; concurrent unrest limits attribution;\n'
  'author timestamps do not verify physical work time or location; unpublished/later\n'
  'code is censored; the original 1,571 account-exclusion rules remain unavailable.\n\n'
  f"Validation: {verification['count']} data/numerical checks passed. See verification.json\n"
  'and the analysis README in the package. The package excludes credentials, model weights,\n'
  'and obsolete manuscript builds. The pinned model can be downloaded from Hugging Face.\n'
 )
 (OUT/'revision-summary.txt').write_text(status)
 # Include current manuscript sources/assets, new code/results/data and original inputs
 # consumed by the new scripts. These copies do not change the working repository.
 files=[]
 for directory in ['analysis/advisor_20261019','results/advisor_20261019']:
  files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='revision_package_manifest.json')
 for p in (ROOT/'paper/latex').rglob('*'):
  if p.is_file() and p.suffix in ['.tex','.bib','.pdf','.sty','.cls'] and p.name!='main.pdf':files.append(p)
 for name in ['international_repo_event_day.parquet','user_dominant_pre_repo.parquet','international_repo_predictions.parquet','international_sector.sqlite','bd_account_creation.jsonl','international_query_job.json','cache_seed_audit.parquet']:
  files.append(ROOT/'data/advisor_20261019'/name)
 for name in ['data/processed/github_activity_international_enriched.parquet','results/synthetic_control/eligible_users_donors.parquet','results/synthetic_control/country_day_donor_pool.parquet','results/mechanism/commit_sha_author_push_master.parquet','analysis/synthetic_control/01_reproduce_sc.py','notes/advisor_plan_20261019.md','notes/literature_evidence_20261019.md','notes/revision_log.md','paper/latex/.latexmkrc']:
  if (ROOT/name).exists():files.append(ROOT/name)
 files=sorted(set(files))
 manifest=[]
 for p in files:manifest.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 (RESULT/'revision_package_manifest.json').write_text(json.dumps(manifest,indent=2))
 archive=OUT/'thesis-revision-analysis.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
  for p in files:z.write(p,str(p.relative_to(ROOT)))
  z.write(RESULT/'revision_package_manifest.json','revision_package_manifest.json')
  z.write(OUT/'revision-summary.txt','REVISION_SUMMARY.txt')
 with zipfile.ZipFile(archive) as z:
  corrupt=z.testzip()
  if corrupt:raise RuntimeError('Corrupt ZIP entry: '+corrupt)
 print('DELIVERED',archive.stat().st_size,'bytes;',len(files),'package files')
if __name__=='__main__':main()
