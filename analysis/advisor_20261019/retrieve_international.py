"""Retrieve GH Archive events for the unchanged eligible sample; never replace inputs."""
from pathlib import Path
import json
from google.cloud import bigquery

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/advisor_20261019'
OUT.mkdir(parents=True, exist_ok=True)
target = OUT / 'international_repo_event_day.parquet'
if target.exists():
    print('Already downloaded:', target)
else:
    client = bigquery.Client(project='olah-aac6b')
    query = (Path(__file__).parent / 'international_events.sql').read_text()
    job = client.query(query, job_config=bigquery.QueryJobConfig(maximum_bytes_billed=30_000_000_000))
    (OUT/'international_query_job.json').write_text(json.dumps({'job_id':job.job_id,'project':job.project,'location':job.location},indent=2))
    df = job.result().to_dataframe(create_bqstorage_client=False)
    df.to_parquet(target, index=False)
    print(json.dumps({'rows':len(df),'countries':df.country.nunique(),'repositories':df.repo_name.nunique(),'bytes_processed':job.total_bytes_processed}))
