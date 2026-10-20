#!/usr/bin/env python3
"""Diagnósticos de referee (cálculos del auditor, NO especificaciones del paper): anomalía de julio en Bangladesh,
sensibilidad del SC a la ventana de ajuste, y composición diaria del ATT.

Solo lectura: no modifica ningún archivo del repositorio.
Uso (desde cualquier carpeta):  python 07_referee_diagnostics.py [ruta_al_repo]
Sin argumento usa la raíz del repositorio que contiene este script."""
import sys, importlib.util
from pathlib import Path
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("sc", REPO/"analysis/synthetic_control/01_reproduce_sc.py")
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
w = sc.load_panel(); donors = [c for c in w.columns if c != "Bangladesh"]
T = pd.Timestamp
print("A. Sensibilidad del SC a la ventana de ajuste (mismo estimador, mismos donantes, misma ventana de tratamiento Jul 18-23)")
for lab, a, b in [("May 1 - Jul 17 (paper)", "2024-05-01", "2024-07-17"), ("May 1 - Jun 30 (excluye julio)", "2024-05-01", "2024-06-30"),
                  ("Jul 1 - Jul 17 (solo julio)", "2024-07-01", "2024-07-17"), ("Jun 20 - Jul 17 (últimas 4 semanas)", "2024-06-20", "2024-07-17")]:
    s = sc.sc_stats(w, "Bangladesh", donors, T(a), T(b), sc.SHUT_START, sc.SHUT_END)
    wt = s["weights"]; synth = w[donors] @ wt; gap = w["Bangladesh"] - synth
    top = "; ".join(f"{c} {v:.2f}" for c, v in wt.sort_values(ascending=False).items() if v > 0.02)
    print(f"  ajuste {lab:36s} ATT {s['ATT']:7.2f} pp | contrafactual {s['counterfactual']:5.2f}% | rel {s['relative_effect_pct']:6.1f}% | RMSPE ajuste {s['pre_RMSPE']:.2f} | "
          f"brecha media Jul 1-17 {gap.loc['2024-07-01':'2024-07-17'].mean():5.2f} | brecha Aug 14-27 {gap.loc['2024-08-14':'2024-08-27'].mean():5.2f} | {top}")
print("\nB. Composición diaria del ATT principal (pesos del paper)")
wt = pd.read_csv(REPO/"results/final/table_primary_SC_weights.csv").set_index("country").weight
synth = w[wt.index] @ wt; d = pd.DataFrame({"BD": w["Bangladesh"], "sint": synth, "gap": w["Bangladesh"]-synth}).loc["2024-07-17":"2024-07-24"]
print(d.round(2).T.to_string())
print(f"  ATT Jul 18-23: {d.gap.loc['2024-07-18':'2024-07-23'].mean():.2f} | ATT Jul 19-23: {d.gap.loc['2024-07-19':'2024-07-23'].mean():.2f} | ATT Jul 19-22: {d.gap.loc['2024-07-19':'2024-07-22'].mean():.2f} "
      f"({100*d.gap.loc['2024-07-19':'2024-07-22'].mean()/d.sint.loc['2024-07-19':'2024-07-22'].mean():.1f}%)")
print("\nC. ¿Qué explica el salto de Bangladesh desde el 2 de julio? (usuarios elegibles)")
el = pd.read_parquet(REPO/"results/synthetic_control/eligible_users_donors.parquet")
raw = pd.read_parquet(REPO/"data/processed/github_activity_international_enriched.parquet", columns=["country","login","date","productive_events","pushes","commits","repos_active"])
d = raw.merge(el[["country","login"]], on=["country","login"]); d = d[d.productive_events > 0]
first = d.groupby(["country","login"]).date.min().rename("first").reset_index()
d = d.merge(first, on=["country","login"])
for c in ["Bangladesh","Pakistan","Indonesia","Nigeria"]:
    g = d[d.country==c]; n = (el.country==c).sum()
    f = first[first.country==c]["first"]
    a = g[g.date.between("2024-06-17","2024-06-30")].groupby("date").login.nunique().mean(); b = g[g.date.between("2024-07-02","2024-07-10")].groupby("date").login.nunique().mean()
    newb = g[g.date.between("2024-07-02","2024-07-10") & (g["first"] >= "2024-06-29")].groupby("date").login.nunique().mean()
    print(f"  {c:11s} elegibles {n:6d} | 1.ª actividad productiva en/después de Jun 29: {int((f>='2024-06-29').sum()):5d} ({100*(f>='2024-06-29').mean():4.1f}%) "
          f"| activos/día Jun 17-30: {a:7.0f} -> Jul 2-10: {b:7.0f} (Δ {b-a:+6.0f}); de ellos, usuarios nuevos (1.ª act. ≥ Jun 29): {newb:6.0f}")
bd = d[d.country=="Bangladesh"]
cohort = set(first[(first.country=="Bangladesh") & (first["first"] >= "2024-06-29")].login)
n_bd = (el.country=="Bangladesh").sum()
s_all = bd.groupby("date").login.nunique(); s_old = bd[~bd.login.isin(cohort)].groupby("date").login.nunique()
print(f"  cohorte BD con 1.ª actividad ≥ Jun 29: {len(cohort)} usuarios ({100*len(cohort)/n_bd:.1f}% de la muestra tratada)")
print("  tasa BD (%) con todos vs excluyendo esa cohorte (denominador ajustado):")
t = pd.DataFrame({"todos": 100*s_all/n_bd, "sin_cohorte": 100*s_old/(n_bd-len(cohort))}).loc["2024-06-27":"2024-07-18"]
print(t.round(1).T.to_string())
# días activos pre de la cohorte y actividad post
pa = el[el.country=="Bangladesh"].set_index("login").pre_active_days
print(f"  días activos pre (mediana): cohorte {pa[pa.index.isin(cohort)].median():.0f} vs resto {pa[~pa.index.isin(cohort)].median():.0f}")
post = bd[bd.date.between("2024-08-14","2024-09-03")]
print(f"  activos/día Aug 14-Sep 3: cohorte {post[post.login.isin(cohort)].groupby('date').login.nunique().mean():.0f} de {len(cohort)} "
      f"({100*post[post.login.isin(cohort)].groupby('date').login.nunique().mean()/len(cohort):.1f}%) | resto {100*post[~post.login.isin(cohort)].groupby('date').login.nunique().mean()/(n_bd-len(cohort)):.1f}%")
# mismo cálculo de 'usuarios nuevos' para la semana previa en todos los países
x = first.assign(new=first["first"] >= "2024-06-29").groupby("country").new.mean().mul(100).round(1)
print("  % de elegibles cuya 1.ª actividad productiva es ≥ Jun 29, por país:", x.to_dict())

print("\nD. Estacionalidad semanal: Bangladesh vs sintético por día de la semana (May 1 - Jun 30; fechas UTC; pesos del paper)")
g = pd.DataFrame({"BD": w["Bangladesh"], "sint": synth}).loc["2024-05-01":"2024-06-30"]
g = g[~g.index.isin(pd.to_datetime(["2024-06-17","2024-06-18","2024-06-19","2024-05-01"]))]
g["gap"] = g.BD - g.sint; g["dow"] = g.index.day_name()
print(g.groupby("dow")[["BD","sint","gap"]].mean().reindex(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]).round(2).T.to_string())
resid = g.gap - g.groupby("dow").gap.transform("mean")
print(f"  RMSPE May-Jun (sin feriados BD): {np.sqrt((g.gap**2).mean()):.2f} | tras quitar la media por día de semana: {np.sqrt((resid**2).mean()):.2f}")
wk = pd.DataFrame({"BD": w["Bangladesh"], "sint": synth}).loc["2024-05-02":"2024-07-17"]
wk["week"] = ((wk.index - pd.Timestamp("2024-05-02")).days // 7)
ww = wk.groupby("week").mean(); print(f"  RMSPE con datos semanales (11 semanas May 2 - Jul 17): {np.sqrt(((ww.BD-ww.sint)**2).mean()):.2f} pp vs diario 3.26")
print("\nE. Peor ajuste pre-tratamiento entre las 15 unidades:")
p = pd.read_csv(REPO/"results/synthetic_control/sc_inspace_placebos.csv").sort_values("pre_RMSPE", ascending=False)
print(p[["country","pre_RMSPE","post_RMSPE","RMSPE_ratio","ATT"]].head(4).round(3).to_string(index=False))
