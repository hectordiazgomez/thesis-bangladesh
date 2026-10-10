"""Audit every current analysis script in a disposable clean clone.

Network/classifier entry points receive --help only and are BLOCKED as full
analyses, never claimed as replicated. Original checkout is never executed.
"""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import tempfile

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 repo=Path(__file__).resolve().parents[1];tmp=Path(tempfile.mkdtemp(prefix='thesis-round2-'));clone=tmp/'repo'
 subprocess.run(['git','clone','--quiet','--no-hardlinks',str(repo),str(clone)],check=True)
 env=os.environ.copy();env['MPLCONFIGDIR']=str(tmp/'mpl');env['PYTHONDONTWRITEBYTECODE']='1'
 subprocess.run([sys.executable,'scripts/materialize_sector_inputs.py'],cwd=clone,check=True,capture_output=True)
 network={'repo_sector_pipeline.py','repo_sector_stream.py'};rows=[]
 for p in sorted((clone/'analysis').rglob('*.py')):
  rel=str(p.relative_to(clone));help_only=p.name in network
  extra=[]
  if p.name.startswith(('06_', '07_', '08_', '09_')) and 'sector_recovery' in rel:
   extra=['--events','data/sector_recovery/bd_preactive20000_repo_event_day_metadata.parquet','--db','data/sector_recovery/repo_sector.sqlite','--outdir',str(tmp/p.stem)]
   if p.name.startswith('09_'):extra+=['--sample','data/sector_recovery/bangladesh_preactive_sample_20000.parquet']
  cmd=[sys.executable,rel]+(['--help'] if help_only else extra)
  try:
   r=subprocess.run(cmd,cwd=clone,env=env,capture_output=True,text=True,timeout=180)
   output=r.stdout+r.stderr;code=r.returncode
  except subprocess.TimeoutExpired as exc:output=str(exc);code=124
  status='blocked_external_pipeline' if help_only else ('passed' if code==0 else 'blocked_or_failed')
  log=tmp/(rel.replace('/','_')+'.log');log.write_text(output)
  rows.append(dict(script=rel,status=status,exit_code=code,invocation=' '.join(cmd),output_tail=output[-1800:]))
  print(status,rel,flush=True)
 report=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone,text=True).strip(),clone=str(clone),python=sys.version,results=rows)
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2))
 print('Detailed logs:',tmp)
if __name__=='__main__':main()
