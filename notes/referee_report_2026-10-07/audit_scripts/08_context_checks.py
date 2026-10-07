#!/usr/bin/env python3
"""Auditoría: (A) feriados codificados para Bangladesh, (B) fases codificadas en el análisis previo del
autor (panel_clean.parquet), (C) trayectoria diaria de Bangladesh y su sintético alrededor del 5 de
agosto, (D) calibración del test de rango del event study, (E) archivos procesados que requieren
db-dtypes.

Solo lectura: no modifica ningún archivo del repositorio.
Uso (desde cualquier carpeta):  python 08_context_checks.py [ruta_al_repo]
Sin argumento usa la raíz del repositorio que contiene este script."""
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60); pd.set_option("display.max_rows", 200)
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
SC = REPO / "results" / "synthetic_control"

h = pd.read_parquet(SC / "country_day_donor_pool_with_holidays.parquet")
print("A. Feriados codificados para Bangladesh")
print(h[(h.country == "Bangladesh") & (h.is_holiday == 1)][["date", "holiday_name", "active_rate_pp"]].round(2).to_string(index=False))
print("\n   Feriados de cualquier país entre el 12 y el 24 de julio:")
print(h[(h.is_holiday == 1) & (h.date >= "2024-07-12") & (h.date <= "2024-07-24")][["country", "date", "holiday_name"]].to_string(index=False))

print("\nB. Fases codificadas en data/processed/panel_clean.parquet (análisis previo del autor)")
flags = ["f0_jul17", "f1_total", "f2_broadband", "f3_socialblock", "f4_second", "f5_post"]
pc = pd.read_parquet(REPO / "data" / "processed" / "panel_clean.parquet", columns=["date"] + flags)
for f in flags:
    dd = pc.loc[pc[f] == 1, "date"]
    print(f"   {f:15s} {dd.min().date()} -> {dd.max().date()}  ({dd.nunique()} días)")

print("\nC. Bangladesh y su sintético, 24 de julio - 12 de agosto (pp)")
syn = pd.read_csv(SC / "reproduced" / "sc_daily_path_full.csv", parse_dates=["date"]).set_index("date")
print(syn.loc["2024-07-24":"2024-08-12"].round(2).T.to_string())
print("\n   Bangladesh y su sintético, 26 de junio - 17 de julio (pp)")
print(syn.loc["2024-06-26":"2024-07-17"].round(2).T.to_string())

print("\nD. Event study: semanas en las que Bangladesh es la unidad más extrema de las 15 (rank p = 1/15)")
es = pd.read_csv(REPO / "results" / "did" / "did_eventstudy_weekly.csv")
es["mas_extrema"] = es.rank_p < 0.07
print(es[["event_week", "start", "end", "theta_pp", "placebo_min_pp", "placebo_max_pp", "rank_p"]].round(3).to_string(index=False))
pre = es[es.event_week < 0]
post = es[es.event_week > 0]
print(f"   semanas previas con rango 1/15: {int(pre.mas_extrema.sum())} de {len(pre)} -> {list(pre[pre.mas_extrema].event_week)}")
print(f"   semanas posteriores con rango 1/15: {int(post.mas_extrema.sum())} de {len(post)} -> {list(post[post.mas_extrema].event_week)}")

print("\nE. Parquet de data/processed cuya columna de fecha exige la extensión db-dtypes de pandas")
for f in sorted((REPO / "data" / "processed").glob("*.parquet")):
    md = pq.read_schema(f).pandas_metadata or {}
    ext = [c["numpy_type"] for c in md.get("columns", []) if c["name"] == "date"]
    if ext and ext[0] not in ("datetime64[ns]", "object"):
        print(f"   {f.name}: tipo de fecha '{ext[0]}'")
