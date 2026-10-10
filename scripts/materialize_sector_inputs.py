"""Populate absent legacy input paths from versioned replication snapshots.
Existing files are NEVER replaced; run inside a clean clone before analyses.
"""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'data/sector_recovery';out.mkdir(parents=True,exist_ok=True)
 for p in (ROOT/'data/replication/sector').iterdir():
  if p.suffix not in ['.parquet','.sqlite']:continue
  dest=out/p.name
  if dest.exists():print('kept existing',dest.relative_to(ROOT));continue
  shutil.copyfile(p,dest);print('materialized',dest.relative_to(ROOT))
if __name__=='__main__':main()
