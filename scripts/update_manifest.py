"""List every tracked/staged file; preserve known original export provenance."""
from pathlib import Path
import csv
import subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 path=ROOT/'manifest.csv'
 with path.open() as f:old={r['export_path']:r for r in csv.DictReader(f)}
 files=sorted(set(subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()))
 fields=['original_path','export_path','filename','extension','size_bytes','size_mb']
 for _ in range(8):
  prior=path.read_bytes();rows=[]
  for name in files:
   p=ROOT/name;size=p.stat().st_size
   rows.append(dict(original_path=old.get(name,{}).get('original_path',''),export_path=name,filename=p.name,extension=p.suffix,size_bytes='' if name=='manifest.csv' else size,size_mb='' if name=='manifest.csv' else size/(1024**2)))
  with path.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
  if path.read_bytes()==prior:break
 else:raise RuntimeError('manifest self-size did not converge')
 print(f'{len(rows)} versioned files; blank original_path = no known export provenance')
if __name__=='__main__':main()
