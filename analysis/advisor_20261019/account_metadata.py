"""Read only immutable account-creation dates; omit contact/profile text."""
from pathlib import Path
import concurrent.futures,datetime,json
import pandas as pd
from sector_classify import gql,token,ROOT,DATA

out=DATA/'bd_account_creation.jsonl'
known={json.loads(l)['requested_login'].lower() for l in out.read_text().splitlines()} if out.exists() else set()
e=pd.read_parquet(ROOT/'results/synthetic_control/eligible_users_donors.parquet')
names=sorted(set(e.loc[e.country.eq('Bangladesh'),'login'].str.lower())-known);t=token()
def fetch(batch):
 q='query{'+''.join(f'u{i}:user(login:{json.dumps(u)}){{login createdAt}}' for i,u in enumerate(batch))+'}'
 r=gql(q,t);date=datetime.datetime.now(datetime.timezone.utc).isoformat()
 return [dict(requested_login=u,queried_at=date,**(r['data'].get(f'u{i}') or {'login':None,'createdAt':None})) for i,u in enumerate(batch)]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool, out.open('a') as f:
 jobs=[pool.submit(fetch,names[i:i+50]) for i in range(0,len(names),50)]
 for k,j in enumerate(concurrent.futures.as_completed(jobs)):
  for r in j.result():f.write(json.dumps(r)+'\n')
  f.flush()
  if k%20==0:print('ACCOUNT_BATCHES',k+1,'/',len(jobs),flush=True)
print('ACCOUNT_METADATA_DONE',flush=True)
