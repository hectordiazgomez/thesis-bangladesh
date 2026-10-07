#!/usr/bin/env python3
"""Auditoría: ¿se puede reconstruir el panel país-día (insumo del SC/DiD) desde data/processed/?
Solo lectura sobre el repo.

Solo lectura: no modifica ningún archivo del repositorio.
Uso (desde cualquier carpeta):  python 01_rebuild_country_day.py [ruta_al_repo]
Sin argumento usa la raíz del repositorio que contiene este script."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
el = pd.read_parquet(REPO/"results/synthetic_control/eligible_users_donors.parquet")
cd = pd.read_parquet(REPO/"results/synthetic_control/country_day_donor_pool.parquet")
en = pd.read_parquet(REPO/"results/synthetic_control/country_day_outcomes_enriched.parquet")
raw = pd.read_parquet(REPO/"data/processed/github_activity_international_enriched.parquet")
print("user-day enriched: rows", len(raw), "| countries", raw.country.nunique(), "| users", raw.login.nunique(),
      "| dates", raw.date.min().date(), "->", raw.date.max().date())
print("users por país en user-day vs elegibles:")
u = raw.groupby("country").login.nunique().rename("users_userday").to_frame().join(el.groupby("country").size().rename("eligible"))
print(u.T.to_string())
key = el[["country","login"]]
d = raw.merge(key, on=["country","login"], how="inner")
print("filas tras restringir a elegibles:", len(d), "de", len(raw))
n = el.groupby("country").size()
cands = {
 "productive_events>0": d.productive_events > 0,
 "interactive_events>0": d.interactive_events > 0,
 "any row": pd.Series(True, index=d.index),
 "pushes>0": d.pushes > 0,
 "productive_output_active": d.productive_output_active > 0,
 "broad_interaction_active": d.broad_interaction_active > 0,
 "prod|interactive": (d.productive_events > 0) | (d.interactive_events > 0),
}
tgt = cd.set_index(["country","date"]).active_users
print("\n¿Qué definición reproduce active_users del panel archivado?")
for lab, m in cands.items():
    got = d[m].groupby(["country","date"]).login.nunique().reindex(tgt.index, fill_value=0)
    diff = (got - tgt)
    print(f"  {lab:28s} celdas idénticas {int((diff==0).sum()):5d}/{len(tgt)} | max|dif| {int(diff.abs().max())} | corr {np.corrcoef(got, tgt)[0,1]:.6f}")
best = d[d.productive_events > 0].groupby(["country","date"]).login.nunique().reindex(tgt.index, fill_value=0)
rate = (100*best/ n.reindex(best.index.get_level_values(0)).to_numpy())
arch = cd.set_index(["country","date"]).active_rate_pp
print("\nactive_rate_pp reconstruido vs archivado: max|dif| =", float((rate-arch).abs().max()))
# conteos agregados
for c in ["pushes","commits","pr_merged","releases","pr_reviews","issues_closed","pr_closed","pr_opened","interactive_events"]:
    got = d.groupby(["country","date"])[c].sum().reindex(tgt.index, fill_value=0)
    a = cd.set_index(["country","date"])[c]
    print(f"  suma {c:20s} max|dif| {int((got-a).abs().max())}")
# outcomes secundarios
e = en.set_index(["country","date"])
for col, src in [("productive_active_users","productive_output_active"),("shipping_active_users","shipping_active"),
                 ("collaboration_active_users","collaboration_active")]:
    got = d[d[src] > 0].groupby(["country","date"]).login.nunique().reindex(e.index, fill_value=0)
    print(f"  {col:28s} max|dif| {int((got-e[col]).abs().max())}")
for col in ["collaboration_events","shipping_output","productive_output"]:
    got = d.groupby(["country","date"])[col].sum().reindex(e.index, fill_value=0)
    print(f"  suma {col:23s} max|dif| {int((got-e[col]).abs().max())}")
# elegibilidad: >=4 días activos pre-tratamiento
pre = raw[(raw.date < "2024-07-18")]
for lab, m in [("productive_events>0", pre.productive_events>0), ("any row", pd.Series(True,index=pre.index)),
               ("interactive_events>0", pre.interactive_events>0)]:
    days = pre[m].groupby(["country","login"]).date.nunique().rename("days").reset_index()
    j = el.merge(days, on=["country","login"], how="left").fillna({"days":0})
    print(f"elegibilidad con '{lab}': pre_active_days coincide en {int((j.days==j.pre_active_days).sum())}/{len(j)}")
days = pre[pre.productive_events>0].groupby(["country","login"]).date.nunique()
print("usuarios en user-day con >=4 días productivos pre:", int((days>=4).sum()), "| elegibles archivados:", len(el),
      "| excluidos pese a >=4:", int((days>=4).sum()) - len(el))
print("bots en archivo elegible: name_bot", int(el.name_bot.sum()), "behavior_bot", int(el.behavior_bot.sum()),
      "| max_daily_commits máx:", int(el.max_daily_commits.max()), "| commit_day_share máx:", float(el.commit_day_share.max()))
# regla de elegibilidad: días previos al 18 de julio con CUALQUIER evento registrado
anyd = pre.groupby(["country","login"]).date.nunique()
print(f"usuarios con >=4 días pre con cualquier evento: {int((anyd>=4).sum()):,} | elegibles archivados: {len(el):,} | "
      f"diferencia (excluidos por la regla de bots, no reproducible desde el repo): {int((anyd>=4).sum()) - len(el):,}")
print("todos los elegibles cumplen >=4 días con cualquier evento:", bool((el.set_index(['country','login']).index.isin(anyd[anyd>=4].index)).all()))
