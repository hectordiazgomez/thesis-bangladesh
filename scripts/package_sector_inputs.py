"""One-time export of immutable local inputs to new portable replication files."""
from pathlib import Path
import hashlib,json,shutil,sqlite3
ROOT=Path(__file__).resolve().parents[1]
def main():
 src=ROOT/'data/sector_recovery';out=ROOT/'data/replication/sector';out.mkdir(parents=True,exist_ok=True);records=[]
 for name in ['bangladesh_full_preactivity_stats.parquet','bangladesh_preactive_sample_20000.parquet','bd_preactive20000_repo_event_day_metadata.parquet']:
  dest=out/name
  if dest.exists():raise FileExistsError(dest)
  shutil.copyfile(src/name,dest);records.append({'source':str((src/name).relative_to(ROOT)),'copy':str(dest.relative_to(ROOT)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
 columns='repo_name, first_activity, last_activity, target_date, total_events, pre_events, shutdown_events, recovery_events, readme_status, prediction_status, naics_code, sector, score, second_code, second_score, score_margin, high_confidence, model_name, model_revision'
 dest=out/'repo_sector.sqlite'
 if dest.exists():raise FileExistsError(dest)
 con=sqlite3.connect((src/'repo_sector.sqlite').as_uri()+'?mode=ro',uri=True);cur=con.execute('SELECT '+columns+' FROM repos ORDER BY repo_name');names=[x[0] for x in cur.description];rows=cur.fetchall();con.close()
 db=sqlite3.connect(dest);db.execute('CREATE TABLE repos ('+', '.join(names)+')');db.executemany('INSERT INTO repos VALUES ('+','.join(['?']*len(names))+')',rows);db.commit();db.close()
 records.append({'source':'data/sector_recovery/repo_sector.sqlite','copy':str(dest.relative_to(ROOT)),'columns':names,'rows':len(rows),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
 (out/'provenance.json').write_text(json.dumps(records,indent=2))
if __name__=='__main__':main()
