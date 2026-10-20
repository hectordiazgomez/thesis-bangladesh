#!/usr/bin/env python3
"""Auditoría: ¿los outcomes secundarios usan numerador de TODOS los usuarios y denominador de elegibles?

Solo lectura: no modifica ningún archivo del repositorio.
Uso (desde cualquier carpeta):  python 02_secondary_sample_check.py [ruta_al_repo]
Sin argumento usa la raíz del repositorio que contiene este script."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
el = pd.read_parquet(REPO/"results/synthetic_control/eligible_users_donors.parquet")
en = pd.read_parquet(REPO/"results/synthetic_control/country_day_outcomes_enriched.parquet").set_index(["country","date"])
cd = pd.read_parquet(REPO/"results/synthetic_control/country_day_donor_pool.parquet").set_index(["country","date"])
raw = pd.read_parquet(REPO/"data/processed/github_activity_international_enriched.parquet")
elig = raw.merge(el[["country","login"]], on=["country","login"])
def agg(d, mask=None, col=None):
    if col is None:
        return d[mask].groupby(["country","date"]).login.nunique().reindex(en.index, fill_value=0)
    return d.groupby(["country","date"])[col].sum().reindex(en.index, fill_value=0)
print("Comparación contra country_day_outcomes_enriched.parquet (celdas idénticas de 1905 / max|dif|)")
print(f"{'outcome':30s} {'solo elegibles':>22s} {'todos los usuarios':>22s}")
for tgt, src in [("productive_active_users","productive_output_active"),("shipping_active_users","shipping_active"),
                 ("collaboration_active_users","collaboration_active"),("broad_interaction_active_users","broad_interaction_active")]:
    a = agg(elig, elig[src]>0) - en[tgt]; b = agg(raw, raw[src]>0) - en[tgt]
    print(f"{tgt:30s} {int((a==0).sum()):>10d} / {int(a.abs().max()):<9d} {int((b==0).sum()):>10d} / {int(b.abs().max()):<9d}")
for tgt in ["collaboration_events","shipping_output","productive_output","issues_opened","issue_comments"]:
    a = agg(elig, col=tgt) - en[tgt]; b = agg(raw, col=tgt) - en[tgt]
    print(f"{'suma '+tgt:30s} {int((a==0).sum()):>10d} / {int(a.abs().max()):<9d} {int((b==0).sum()):>10d} / {int(b.abs().max()):<9d}")
# Tasas: ¿numerador de todos / denominador de elegibles?
n_el = el.groupby("country").size(); n_all = raw.groupby("country").login.nunique()
num_all = agg(raw, raw.productive_output_active>0)
rate_arch = en.productive_active_rate_pp
r1 = 100*num_all / n_el.reindex(num_all.index.get_level_values(0)).to_numpy()
r2 = 100*num_all / n_all.reindex(num_all.index.get_level_values(0)).to_numpy()
print("\nproductive_active_rate_pp archivada vs (todos/elegibles): max|dif|", float((r1-rate_arch).abs().max()),
      "| vs (todos/todos): max|dif|", float((r2-rate_arch).abs().max()))
bd = pd.DataFrame({"primario_active_rate_pp (elegibles)": cd.active_rate_pp.xs("Bangladesh"),
                   "productive_active_rate_pp (archivado)": rate_arch.xs("Bangladesh"),
                   "num_productive_todos": num_all.xs("Bangladesh"), "num_productive_elegibles": agg(elig, elig.productive_output_active>0).xs("Bangladesh"),
                   "n_users": en.n_users.xs("Bangladesh")})
print(bd.loc["2024-07-14":"2024-07-25"].round(3).to_string())
print("\nusuarios por país: user-day completo vs elegibles, y razón")
print(pd.DataFrame({"todos": n_all, "elegibles": n_el, "ratio": (n_all/n_el).round(2)}).T.to_string())
pre = (en.index.get_level_values("date") < "2024-07-18")
print("\nMedia pre-período: tasa productiva archivada vs tasa primaria (pp)")
print(pd.DataFrame({"productive_rate_arch": en.productive_active_rate_pp[pre].groupby("country").mean(),
                    "primary_rate": cd.active_rate_pp[pre].groupby("country").mean()}).round(2).T.to_string())
