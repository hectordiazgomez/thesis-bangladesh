#!/usr/bin/env python3
"""Auditoría: cruce de cifras escritas a mano en el texto contra archivos de resultados (las que no se verificaron en scripts previos).

Solo lectura: no modifica ningún archivo del repositorio.
Uso (desde cualquier carpeta):  python 06_text_claims.py [ruta_al_repo]
Sin argumento usa la raíz del repositorio que contiene este script."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]; R = REPO/"results"
v = pd.read_csv(R/"did/did_pre_period_volatility.csv").set_index("country").pre_weekly_sd_pp
print(f"[06] SD semanal pre: BD {v['Bangladesh']:.2f} (texto 3.04) | donantes {v.drop('Bangladesh').min():.2f}–{v.drop('Bangladesh').max():.2f} (texto 0.70–2.18)")
es = pd.read_csv(R/"did/did_eventstudy_weekly.csv").set_index("event_week").theta_pp
print(f"[06] ES: sem+1 {es[1]:.3f}, +2 {es[2]:.3f} (texto −2.66, −2.76) | +4..+6 {es[4]:.2f} {es[5]:.2f} {es[6]:.2f} (texto 2.53 a 4.84) | pre min {es[es.index<0].min():.2f} max {es[es.index<0].max():.2f}")
e = pd.read_csv(R/"sector_recovery/sectorwide/sectorwide_user_eventstudy.csv")
print("columnas eventstudy sectorial:", list(e.columns), "| event_time", e.event_time.min(), e.event_time.max())
def ri(sec, ks): g = e[e.sector==sec].set_index("event_time").recovery_index; return [round(float(g[k]),1) for k in ks]
print("[06] Finance sem −1:", ri("Finance and Insurance", [-1]), "(texto 193.6) | Finance post <80 en semanas:", [int(k) for k in e[(e.sector=="Finance and Insurance")&(e.event_time>3)&(e.recovery_index<80)].event_time])
print("[06] Accom/Food base −8..−1:", ri("Accommodation and Food Services", range(-8,0)), "(texto: 254.1 y 127.3; resto 40.8–95.5)")
print("[06] Real Estate +1..+8:", ri("Real Estate and Rental", range(1,9)), "| +12..+17:", ri("Real Estate and Rental", range(12,18)), "(texto: 25.1–44.4 hasta +4; 115.1, 157.3; 85.5; +12→ 31.9–46.7)")
print("[06] Retail +1..+9:", ri("Retail Trade", range(1,10)), "(texto ~52, 153.7 en +4, 76.5 en +5, corrida desde +9)")
print("[06] Information +10..+17:", ri("Information", range(10,18)), "(texto 111.5–126.4 en +10..+15; 144.3 en +17)")
print("[06] IC95 excluye 0 en apagón, todos los sectores:", bool((e[e.event_time==0].ci_high_pp < 0).all()), "| fechas semana +17:", e[e.event_time==17][[c for c in e.columns if 'start' in c or 'end' in c]].drop_duplicates().to_dict('records')[:1])
ps = pd.read_csv(R/"mechanism/robust_push_size_period.csv"); print("[08] completitud de push:\n", ps.to_string(index=False))
th = pd.read_csv(R/"sector_recovery/final/sector_threshold_robustness_full.csv")
t = th[th.sector.isin(["Accommodation and Food Services","Real Estate and Rental","Retail Trade","Educational Services","Health Care and Social Assistance","Finance and Insurance","Information","Professional, Scientific, Technical Services","Administrative and Support Services"])]
print("[08] robustez umbral:\n", t[["sector","threshold","pre_users","week1_recovery_index","week4_recovery_index","week8_recovery_index","first_sustained2_ge_80"]].round(1).sort_values(["sector","threshold"]).to_string(index=False))
