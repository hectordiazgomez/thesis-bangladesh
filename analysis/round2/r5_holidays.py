"""R5: source-based holiday-label alternative; never overwrite processed data."""
from pathlib import Path
import importlib.util
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/diagnostics/round2'
def main():
    spec = importlib.util.spec_from_file_location('did', ROOT/'analysis/did/01_aggregate_did_eventstudy.py')
    did = importlib.util.module_from_spec(spec); spec.loader.exec_module(did)
    d = pd.read_parquet(did.SRC); d['date'] = pd.to_datetime(d.date)
    select = d.country.eq('Bangladesh') & d.date.between('2024-08-04','2024-08-07')
    alt = d.copy(); changed = alt.country.eq('Bangladesh') & alt.date.between('2024-08-06','2024-08-07')
    alt.loc[changed, 'is_holiday'] = 0
    audit = d.loc[select, ['country','date','active_rate_pp','is_holiday','holiday_name']].copy()
    audit['alternative_is_holiday'] = alt.loc[select,'is_holiday']
    clean = pd.read_parquet(ROOT/'data/processed/panel_clean.parquet', columns=['country','date','hol_bd','f4_second'])
    clean['date'] = pd.to_datetime(clean.date)
    clean = clean[clean.country.eq('Bangladesh') & clean.date.between('2024-08-04','2024-08-07')]
    assert clean.groupby('date')[['hol_bd','f4_second']].nunique().eq(1).all().all()
    flags = clean.groupby('date')[['hol_bd','f4_second']].first().rename(columns={'hol_bd':'panel_clean_hol_bd','f4_second':'panel_clean_second_shutdown'})
    audit = audit.merge(flags, on='date', validate='one_to_one')
    rows=[]
    for label, data in [('archived',d),('Aug6_reopening_alternative',alt)]:
        w=data.pivot(index='date',columns='country',values='active_rate_pp')
        h=data.pivot(index='date',columns='country',values='is_holiday').astype(bool)
        for exclude in [False,True]:
            panel=w.mask(h) if exclude else w
            rows.append({'labels':label,'remove_holidays':exclude,'ATT_pp':did.did_by_unit(panel,w.index.to_series().between('2024-07-18','2024-07-23'))['Bangladesh']})
    OUT.mkdir(parents=True,exist_ok=True)
    audit.to_csv(OUT/'r5_holiday_label_conflict.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'r5_holiday_did_comparison.csv',index=False)
    print(audit.to_string(index=False));print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__': main()
