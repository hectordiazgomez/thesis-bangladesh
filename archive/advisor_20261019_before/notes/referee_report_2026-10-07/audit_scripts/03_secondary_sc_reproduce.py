#!/usr/bin/env python3
"""Auditoría: (1) reproducir tablas archivadas de outcomes secundarios (no hay código en el repo);
(2) cuantificar el efecto de construir los numeradores solo con usuarios elegibles (como describe el paper).

Solo lectura: no modifica ningún archivo del repositorio.
Uso (desde cualquier carpeta):  python 03_secondary_sc_reproduce.py [ruta_al_repo]
Sin argumento usa la raíz del repositorio que contiene este script."""
import sys, importlib.util
from pathlib import Path
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("sc", REPO/"analysis/synthetic_control/01_reproduce_sc.py")
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
FINAL = REPO/"results/final"
el = pd.read_parquet(REPO/"results/synthetic_control/eligible_users_donors.parquet")
en = pd.read_parquet(REPO/"results/synthetic_control/country_day_outcomes_enriched.parquet")
raw = pd.read_parquet(REPO/"data/processed/github_activity_international_enriched.parquet")
elig = raw.merge(el[["country","login"]], on=["country","login"])
n = el.groupby("country").size()
idx = pd.MultiIndex.from_frame(en[["country","date"]])
def rate(mask): 
    s = elig[mask].groupby(["country","date"]).login.nunique().reindex(idx, fill_value=0)
    return 100*s/n.reindex(s.index.get_level_values(0)).to_numpy()
def per1000(col):
    s = elig.groupby(["country","date"])[col].sum().reindex(idx, fill_value=0)
    return 1000*s/n.reindex(s.index.get_level_values(0)).to_numpy()
fixed = pd.DataFrame({
  "productive_active_rate_pp": rate(elig.productive_output_active>0),
  "shipping_active_rate_pp": rate(elig.shipping_active>0),
  "collaboration_active_rate_pp": rate(elig.collaboration_active>0),
  "collaboration_events_per_1000": per1000("collaboration_events"),
  "shipping_output_per_1000": per1000("shipping_output")}).reset_index()
wprim = pd.read_csv(FINAL/"table_primary_SC_weights.csv").set_index("country").weight
arch_fx = pd.read_csv(FINAL/"table_secondary_fixed_SC.csv").set_index("outcome")
arch_sp = pd.read_csv(FINAL/"table_secondary_specific_SC.csv").set_index("outcome")
arch_pl = pd.read_csv(FINAL/"table_secondary_placebo_summary.csv").set_index("outcome")
W = (sc.PRE_START, sc.PRE_END, sc.SHUT_START, sc.SHUT_END)
def fixed_w(panel, col):
    w = panel.pivot(index="date", columns="country", values=col).sort_index()
    synth = w[wprim.index] @ wprim
    post = slice(sc.SHUT_START, sc.SHUT_END)
    a, c = w.loc[post,"Bangladesh"].mean(), synth.loc[post].mean()
    return a, c, a-c, 100*(a-c)/c
def specific(panel, col):
    w = panel.pivot(index="date", columns="country", values=col).sort_index()
    donors = [c for c in w.columns if c!="Bangladesh"]
    s = sc.sc_stats(w, "Bangladesh", donors, *W)
    rows = [s] + [sc.sc_stats(w, c, [d for d in donors if d!=c], *W) for c in donors]
    att = np.array([r["ATT"] for r in rows]); rr = np.array([r["RMSPE_ratio"] for r in rows])
    return s, (np.abs(att)>=abs(att[0])).mean(), (rr>=rr[0]).mean()
print("A. PESOS PRIMARIOS FIJOS  (archivado = lo que está en el paper | reproducido con panel archivado | corregido = numerador solo elegibles)")
print(f"{'outcome':30s} {'ATT arch':>9s} {'ATT repr':>9s} | {'rel arch':>8s} {'rel repr':>8s} || {'actual corr':>11s} {'cf corr':>8s} {'ATT corr':>9s} {'rel corr':>8s}")
for o in arch_fx.index:
    a = fixed_w(en, o); c = fixed_w(fixed, o)
    print(f"{o:30s} {arch_fx.loc[o,'ATT']:9.3f} {a[2]:9.3f} | {arch_fx.loc[o,'relative_effect_pct']:8.2f} {a[3]:8.2f} || {c[0]:11.3f} {c[1]:8.3f} {c[2]:9.3f} {c[3]:8.2f}")
print("\nB. PESOS ESPECÍFICOS POR OUTCOME")
print(f"{'outcome':30s} {'ATT arch':>9s} {'ATT repr':>9s} | {'rel arch':>8s} {'rel repr':>8s} | p_ATT p_RMSPE (arch) | p_ATT p_RMSPE (repr) || {'ATT corr':>9s} {'rel corr':>8s} p_ATT p_RMSPE (corr)")
for o in arch_sp.index:
    s, pa, pr = specific(en, o); s2, pa2, pr2 = specific(fixed, o)
    ap = f"{arch_pl.loc[o,'ATT_rank_p']:.4f} {arch_pl.loc[o,'RMSPE_rank_p']:.4f}" if o in arch_pl.index else "   --     --  "
    print(f"{o:30s} {arch_sp.loc[o,'ATT']:9.3f} {s['ATT']:9.3f} | {arch_sp.loc[o,'relative_effect_pct']:8.2f} {s['relative_effect_pct']:8.2f} | {ap} | {pa:.4f} {pr:.4f} || {s2['ATT']:9.3f} {s2['relative_effect_pct']:8.2f} {pa2:.4f} {pr2:.4f}")
print("\nC. DiD todos los outcomes: archivado vs reproducido con panel archivado vs corregido")
did = pd.read_csv(FINAL/"table_DiD_all_outcomes.csv")
hol = en.pivot(index="date", columns="country", values="is_holiday").astype(bool)
def did_att(panel, col, drop_hol):
    w = panel.pivot(index="date", columns="country", values=col).sort_index()
    if drop_hol: w = w.mask(hol.reindex(w.index))
    pre = w.loc[sc.PRE_START:sc.PRE_END].mean(); post = w.loc[sc.SHUT_START:sc.SHUT_END].mean(); chg = post-pre
    return chg["Bangladesh"] - chg.drop("Bangladesh").mean()
for r in did[did.outcome!="active_rate_pp"].itertuples():
    print(f"{r.outcome:30s} hol_removed={str(r.remove_holidays):5s} arch {r.ATT:9.3f} | repr {did_att(en, r.outcome, r.remove_holidays):9.3f} | corregido {did_att(fixed, r.outcome, r.remove_holidays):9.3f}")
