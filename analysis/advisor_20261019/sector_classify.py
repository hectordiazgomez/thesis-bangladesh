"""Frozen pre-treatment repository domains for all 15 countries.

Choose each eligible user's most frequently active pre-treatment repository,
using the recovered primary event map. Ties: events then lexical repository.
Fetch the README at the final default-branch commit by July 17, 2024. Missing
historical READMEs remain explicit; never substitute current metadata.
Existing Bangladesh README bytes can be reused, but all selected repositories
are classified with one pinned model and the same text formatter.
"""
from pathlib import Path
import argparse, concurrent.futures, datetime, hashlib, json, sqlite3, sys, time, zlib
import pandas as pd
import db_dtypes  # registers historical BigQuery date columns for local replication
import requests
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/advisor_20261019'; DATA.mkdir(parents=True,exist_ok=True)
MODEL='aquiro1994/naics-github-classifier-multilingual'
REV='e40747e90bbc547e56b7145d2b97494bff69b42d'
TYPES=['PushEvent','PullRequestEvent','PullRequestReviewEvent','PullRequestReviewCommentEvent','IssuesEvent','ReleaseEvent','CreateEvent']
def db():
 c=sqlite3.connect(DATA/'international_sector.sqlite',timeout=120)
 c.execute('PRAGMA journal_mode=WAL')
 c.execute('CREATE TABLE IF NOT EXISTS repos(repo TEXT PRIMARY KEY, status TEXT, sha TEXT, path TEXT, readme BLOB, source TEXT, code TEXT, score REAL, second_code TEXT, second_score REAL, revision TEXT, text_sha256 TEXT)')
 return c
def prepare():
 target=DATA/'user_dominant_pre_repo.parquet'
 if target.exists():g=pd.read_parquet(target)
 else:
  e=pd.read_parquet(DATA/'international_repo_event_day.parquet');e.date=pd.to_datetime(e.date)
  p=e[e.date.lt('2024-07-18')&e.event_type.isin(TYPES)]
  g=p.groupby(['country','login','repo_name']).agg(active_days=('date','nunique'),events=('event_count','sum')).reset_index()
  g=g.sort_values(['country','login','active_days','events','repo_name'],ascending=[True,True,False,False,True]).drop_duplicates(['country','login'])
  g.to_parquet(target,index=False)
 c=db();c.executemany('INSERT OR IGNORE INTO repos(repo) VALUES(?)',[(r,) for r in sorted(g.repo_name.unique())]);c.commit()
 old=sqlite3.connect(f'file:{ROOT}/data/sector_recovery/repo_sector.sqlite?mode=ro',uri=True)
 existing={r[0]:r[1:] for r in old.execute("SELECT repo_name,readme_status,readme_snapshot_sha,readme_path,readme_zlib FROM repos WHERE target_date='2024-07-17' AND readme_status='ok'")}
 reused=0
 for (r,) in c.execute('SELECT repo FROM repos WHERE status IS NULL').fetchall():
  if r in existing:
   status,sha,path,blob=existing[r]
   # Legacy replication databases may preserve status='ok' but only empty
   # placeholder bytes. A status flag is not evidence of cached source text.
   if not blob or not zlib.decompress(blob).decode().strip():continue
   c.execute('UPDATE repos SET status=?,sha=?,path=?,readme=?,source=? WHERE repo=?',(status,sha,path,blob,'existing_historical_cache',r));reused+=1
 c.commit();print('PREPARED',len(g),'users',g.repo_name.nunique(),'repos; reused',reused,flush=True)
def token():
 import os
 v=dotenv_values('/Users/hectoralbertodiazgomez/Documents/retrieve-info/.env')
 t=os.environ.get('GH_TOKEN') or v.get('GH_TOKEN') or v.get('GITHUB_TOKEN')
 if not t:raise RuntimeError('GitHub token unavailable')
 return t
def gql(q,t):
 for attempt in range(6):
  try:
   r=requests.post('https://api.github.com/graphql',headers={'Authorization':'Bearer '+t},json={'query':q},timeout=90)
   if r.status_code==200:
    p=r.json()
    if p.get('data') is not None:return p
   if r.status_code==401:raise RuntimeError('GitHub authentication failed')
  except (requests.Timeout,requests.ConnectionError):pass
  time.sleep(min(2**attempt,30))
 raise RuntimeError('GitHub query failed after retries')
def fetch_batch(repos,t):
 fields=[]
 for i,r in enumerate(repos):
  owner,name=r.split('/',1)
  fields.append(f'r{i}:repository(owner:{json.dumps(owner)},name:{json.dumps(name)}){{object(expression:"HEAD"){{... on Commit{{history(first:1,until:"2024-07-17T23:59:59Z"){{nodes{{oid tree{{entries{{name type oid}}}}}}}}}}}}}}')
 p=gql('query{'+''.join(fields)+'}',t);res=[];pending=[]
 for i,r in enumerate(repos):
  node=p['data'].get('r'+str(i))
  if not node:res.append((r,'unavailable',None,None,None,'github_graphql'));continue
  obj=node.get('object')
  hist=(obj or {}).get('history',{}).get('nodes',[])
  if not hist:res.append((r,'no_commit_at_target',None,None,None,'github_graphql'));continue
  h=hist[0];paths=[x for x in h['tree']['entries'] if x['type']=='blob' and (x['name'].lower()=='readme' or x['name'].lower().startswith('readme.'))]
  if not paths:res.append((r,'no_root_readme',h['oid'],None,None,'github_graphql'));continue
  x=sorted(paths,key=lambda x:(x['name'].lower()!='readme.md',x['name']))[0]
  pending.append((r,h['oid'],x['name'],x['oid']))
 if pending:
  fields=[]
  for i,(r,sha,path,oid) in enumerate(pending):
   owner,name=r.split('/',1)
   fields.append(f'r{i}:repository(owner:{json.dumps(owner)},name:{json.dumps(name)}){{object(oid:{json.dumps(oid)}){{... on Blob{{text isTruncated byteSize}}}}}}')
  q=gql('query{'+''.join(fields)+'}',t)
  for i,(r,sha,path,oid) in enumerate(pending):
   b=(q['data'].get('r'+str(i)) or {}).get('object') or {}
   txt=b.get('text');status=('ok' if txt.strip() else 'empty_readme') if isinstance(txt,str) and not b.get('isTruncated') else 'unreadable_blob'
   res.append((r,status,sha,path,zlib.compress(txt.encode()) if status in ('ok','empty_readme') else None,'github_graphql'))
 return res
def fetch():
 c=db();rs=[r[0] for r in c.execute("SELECT repo FROM repos WHERE status IS NULL OR status='query_error' ORDER BY repo")];t=token()
 print('FETCH_PENDING',len(rs),flush=True)
 batches=[rs[i:i+40] for i in range(0,len(rs),40)];done=0
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  futures={pool.submit(fetch_batch,b,t):b for b in batches}
  for f in concurrent.futures.as_completed(futures):
   try:result=f.result()
   except Exception as exc:
    print('BATCH_ERROR',type(exc).__name__,flush=True);result=[(r,'query_error',None,None,None,'github_graphql') for r in futures[f]]
   c.executemany('UPDATE repos SET status=?,sha=?,path=?,readme=?,source=? WHERE repo=?',[(s,sha,p,b,src,r) for r,s,sha,p,b,src in result]);c.commit();done+=len(result)
   if done%200==0 or done==len(rs):print('FETCHED',done,'/',len(rs),flush=True)
 print('FETCH_STATUS',c.execute('SELECT status,count(*) FROM repos GROUP BY status').fetchall(),flush=True)
def classify():
 import torch
 from transformers import AutoTokenizer,AutoModelForSequenceClassification
 from text_format_snapshot import format_model_input
 c=db();rows=c.execute("SELECT repo,readme FROM repos WHERE code IS NULL AND status IS NOT NULL AND status!='query_error' ORDER BY repo").fetchall()
 print('CLASSIFY_PENDING',len(rows),flush=True)
 if not rows:return
 torch.set_num_threads(4);device='mps' if torch.backends.mps.is_available() else 'cpu'
 tk=AutoTokenizer.from_pretrained(MODEL,revision=REV,local_files_only=True)
 m=AutoModelForSequenceClassification.from_pretrained(MODEL,revision=REV,local_files_only=True).eval().to(device)
 if device=='mps':m.half()
 print('MODEL_READY',device,flush=True)
 for start in range(0,len(rows),32):
  batch=rows[start:start+32]
  texts=[format_model_input(repo_name=r.split('/',1)[-1],readme=zlib.decompress(b).decode() if b else None) for r,b in batch]
  enc={k:v.to(device) for k,v in tk(texts,padding=True,truncation=True,max_length=512,return_tensors='pt').items()}
  with torch.inference_mode():pr=torch.softmax(m(**enc).logits.float(),dim=-1); vals,idx=torch.topk(pr,2,dim=-1)
  vals=vals.cpu().tolist();idx=idx.cpu().tolist()
  for (r,b),txt,v,i in zip(batch,texts,vals,idx):
   c.execute('UPDATE repos SET code=?,score=?,second_code=?,second_score=?,revision=?,text_sha256=? WHERE repo=?',(str(m.config.id2label[i[0]]),v[0],str(m.config.id2label[i[1]]),v[1],REV,hashlib.sha256(txt.encode()).hexdigest(),r))
  c.commit()
  if start%320==0:print('CLASSIFIED',min(start+32,len(rows)),'/',len(rows),flush=True)
 pd.read_sql_query('SELECT repo,status,sha,path,source,code,score,second_code,second_score,revision,text_sha256 FROM repos',c).to_parquet(DATA/'international_repo_predictions.parquet',index=False)
 print('CLASSIFICATION_DONE',flush=True)
def stream():
 """One resident model consumes fetched rows while network retrieval continues."""
 import torch
 from transformers import AutoTokenizer,AutoModelForSequenceClassification
 from text_format_snapshot import format_model_input
 torch.set_num_threads(4);device='mps' if torch.backends.mps.is_available() else 'cpu'
 tk=AutoTokenizer.from_pretrained(MODEL,revision=REV,local_files_only=True)
 m=AutoModelForSequenceClassification.from_pretrained(MODEL,revision=REV,local_files_only=True).eval().to(device)
 if device=='mps':m.half()
 c=db();done=0;starttime=time.time();print('STREAM_MODEL_READY',device,flush=True)
 while True:
  rows=c.execute("SELECT repo,readme FROM repos WHERE code IS NULL AND status IS NOT NULL AND status!='query_error' ORDER BY (readme IS NOT NULL),length(readme),repo LIMIT 640").fetchall()
  if not rows:
   if c.execute('SELECT count(*) FROM repos WHERE status IS NULL').fetchone()[0]==0:break
   time.sleep(5);continue
  for start in range(0,len(rows),32):
   batch=rows[start:start+32]
   texts=[format_model_input(repo_name=r.split('/',1)[-1],readme=zlib.decompress(b).decode() if b else None) for r,b in batch]
   enc={k:v.to(device) for k,v in tk(texts,padding=True,truncation=True,max_length=512,return_tensors='pt').items()}
   with torch.inference_mode():probs=torch.softmax(m(**enc).logits.float(),dim=-1)
   if not torch.isfinite(probs).all():raise RuntimeError('Nonfinite model probabilities')
   vals,idx=torch.topk(probs,2,dim=-1);vals=vals.cpu().tolist();idx=idx.cpu().tolist()
   for (r,b),txt,v,i in zip(batch,texts,vals,idx):
    c.execute('UPDATE repos SET code=?,score=?,second_code=?,second_score=?,revision=?,text_sha256=? WHERE repo=?',(str(m.config.id2label[i[0]]),v[0],str(m.config.id2label[i[1]]),v[1],REV,hashlib.sha256(txt.encode()).hexdigest(),r))
   c.commit();done+=len(batch)
  print('STREAM_CLASSIFIED',done,'seconds',round(time.time()-starttime),flush=True)
 pd.read_sql_query('SELECT repo,status,sha,path,source,code,score,second_code,second_score,revision,text_sha256 FROM repos',c).to_parquet(DATA/'international_repo_predictions.parquet',index=False)
 print('STREAM_DONE',flush=True)
def finish():
 """After retrieval, sort exact token lengths to reduce padding and Mac memory use."""
 import torch
 from transformers import AutoTokenizer,AutoModelForSequenceClassification
 from text_format_snapshot import format_model_input
 c=db()
 if c.execute('SELECT count(*) FROM repos WHERE status IS NULL').fetchone()[0]:raise RuntimeError('Retrieval is incomplete')
 rows=c.execute("SELECT repo,readme FROM repos WHERE code IS NULL AND status!='query_error'").fetchall()
 print('FINISH_PENDING',len(rows),flush=True)
 if rows:
  tk=AutoTokenizer.from_pretrained(MODEL,revision=REV,local_files_only=True)
  texts=[format_model_input(repo_name=r.split('/',1)[-1],readme=zlib.decompress(b).decode() if b else None) for r,b in rows]
  hashes=[hashlib.sha256(t.encode()).hexdigest() for t in texts]
  enc=tk(texts,padding=False,truncation=True,max_length=512)
  order=sorted(range(len(rows)),key=lambda i:len(enc['input_ids'][i]))
  print('TOKENS',sum(map(len,enc['input_ids'])),'mean',sum(map(len,enc['input_ids']))/len(rows),flush=True)
  torch.set_num_threads(4);device='mps' if torch.backends.mps.is_available() else 'cpu'
  m=AutoModelForSequenceClassification.from_pretrained(MODEL,revision=REV,local_files_only=True,dtype=torch.float16 if device=='mps' else torch.float32).eval().to(device)
  starttime=time.time()
  for start in range(0,len(order),16):
   ids=order[start:start+16]
   batch=tk.pad([{k:v[i] for k,v in enc.items()} for i in ids],padding=True,return_tensors='pt')
   batch={k:v.to(device) for k,v in batch.items()}
   with torch.inference_mode():probs=torch.softmax(m(**batch).logits.float(),dim=-1)
   if not torch.isfinite(probs).all():raise RuntimeError('Nonfinite model probabilities')
   vals,ix=torch.topk(probs,2,dim=-1);vals=vals.cpu().tolist();ix=ix.cpu().tolist()
   for rowidx,v,i in zip(ids,vals,ix):
    c.execute('UPDATE repos SET code=?,score=?,second_code=?,second_score=?,revision=?,text_sha256=? WHERE repo=?',(str(m.config.id2label[i[0]]),v[0],str(m.config.id2label[i[1]]),v[1],REV,hashes[rowidx],rows[rowidx][0]))
   c.commit()
   if start%320==0:print('FINISHED',min(start+16,len(rows)),'/',len(rows),'seconds',round(time.time()-starttime),flush=True)
 pd.read_sql_query('SELECT repo,status,sha,path,source,code,score,second_code,second_score,revision,text_sha256 FROM repos',c).to_parquet(DATA/'international_repo_predictions.parquet',index=False)
 print('FINISH_DONE',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('stage',choices=['prepare','fetch','classify','stream','finish','all']);x=a.parse_args()
 for s,fn in [('prepare',prepare),('fetch',fetch),('classify',classify),('stream',stream),('finish',finish)]:
  if x.stage==s or (x.stage=='all' and s in ('prepare','fetch','finish')):fn()
