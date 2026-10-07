#!/usr/bin/env python3
"""Auditoría: (A) contenido del outcome primario (productive_events), (B) muestra del RDiT frente a la
muestra del control sintético, (C) sensibilidad del RDiT al corte y al ancho de banda.

La parte C es un diagnóstico del auditor: NO es una especificación del paper ni una propuesta de
nuevo resultado principal. La especificación archivada es corte 17 de julio, ancho de banda 7.

Solo lectura: no modifica ningún archivo del repositorio.
Uso (desde cualquier carpeta):  python 05_definitions_rdit.py [ruta_al_repo]
Sin argumento usa la raíz del repositorio que contiene este script."""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
PROC = REPO / "data" / "processed"

raw = pd.read_parquet(PROC / "github_activity_international_enriched.parquet")
el = pd.read_parquet(REPO / "results" / "synthetic_control" / "eligible_users_donors.parquet")
d = raw.merge(el[["country", "login"]], on=["country", "login"])

# ---------------------------------------------------------------- A. outcome primario
print("A. ¿Qué contiene productive_events? (el outcome primario es productive_events > 0)")
comp = ["pushes", "commits", "pr_opened", "pr_closed", "pr_merged", "issues_closed", "releases", "pr_reviews"]
hits = [cs for r in range(1, len(comp) + 1) for cs in itertools.combinations(comp, r)
        if (raw[list(cs)].sum(axis=1) == raw.productive_events).all()]
print("  sumas de componentes que reproducen productive_events exactamente:", hits or "ninguna")
listed = ["pushes", "pr_opened", "pr_closed", "pr_merged", "issues_closed", "releases", "pr_reviews",
          "issues_opened", "issue_comments", "pr_review_comments", "commit_comments"]
prod = d.productive_events > 0
none_listed = d[listed].sum(axis=1) == 0
print(f"  usuario-día elegibles con productive_events > 0: {int(prod.sum()):,}")
print(f"    sin ningún componente enumerado en los datos: {int((prod & none_listed).sum()):,} "
      f"= {100 * (prod & none_listed).sum() / prod.sum():.1f}%")
print(f"    sin ningún push: {int((prod & (d.pushes == 0)).sum()):,} = {100 * (prod & (d.pushes == 0)).sum() / prod.sum():.1f}%")
n = el.groupby("country").size()
print("  tasa de Bangladesh según la definición usada (media de porcentajes diarios):")
for lab, m in [("primario archivado: productive_events > 0", prod),
               ("Tabla 2 'productive': commits | issues_closed | pr_closed | releases", d.productive_output_active > 0),
               ("cualquier evento enumerado", ~none_listed)]:
    r = 100 * d[m].groupby(["country", "date"]).login.nunique().unstack(0, fill_value=0) / n
    b = r["Bangladesh"]
    print(f"    {lab:70s} pre {b.loc[:'2024-07-17'].mean():5.2f} | Jul 18-23 {b.loc['2024-07-18':'2024-07-23'].mean():4.2f} "
          f"| Jul 19-22 {b.loc['2024-07-19':'2024-07-22'].mean():5.3f}")

# ---------------------------------------------------------------- B. muestras
print("\nB. Muestra del RDiT frente a la muestra del control sintético")
bd = pd.read_parquet(PROC / "panel_user_day_bangladesh.parquet")
ph = pd.read_parquet(PROC / "panel_user_day_philippines.parquet")
for c, p in [("Bangladesh", bd), ("Philippines", ph)]:
    s_sc, s_rd = set(el[el.country == c].login.str.lower()), set(p.login.str.lower().unique())
    print(f"  {c}: RDiT {len(s_rd):,} | SC {len(s_sc):,} | en ambas {len(s_rd & s_sc):,} | solo RDiT {len(s_rd - s_sc):,} | solo SC {len(s_sc - s_rd):,}")
cd = pd.read_parquet(REPO / "results" / "synthetic_control" / "country_day_donor_pool.parquet")
y_r = 100 * (bd.productive_events > 0).groupby(bd.date).mean()
y_s = cd[cd.country == "Bangladesh"].set_index("date").active_rate_pp
print("  serie diaria de Bangladesh (%), panel RDiT frente a panel SC:")
print(pd.DataFrame({"RDiT": y_r, "SC": y_s}).loc["2024-07-14":"2024-07-26"].round(2).T.to_string())

# ---------------------------------------------------------------- C. sensibilidad
def rd(y: pd.Series, cut: pd.Timestamp, bw: int, lags: int = 2) -> tuple[float, float]:
    """Mismo estimador que analysis/rdit/01_reproduce_rdit.py (lineal local, HAC Newey-West)."""
    idx = pd.date_range(cut - pd.Timedelta(days=bw), cut + pd.Timedelta(days=bw))
    t = (idx - cut).days.to_numpy(float)
    dd = (t >= 0).astype(float)
    X = np.column_stack([np.ones_like(t), dd, t, dd * t])
    yy = y.loc[idx].to_numpy(float)
    b = np.linalg.lstsq(X, yy, rcond=None)[0]
    e = yy - X @ b
    nn, k = X.shape
    S = (X * e[:, None]).T @ (X * e[:, None])
    for L in range(1, lags + 1):
        G = (X[L:] * e[L:, None]).T @ (X[:-L] * e[:-L, None])
        S += (1 - L / (lags + 1)) * (G + G.T)
    B = np.linalg.inv(X.T @ X)
    return b[1], float(np.sqrt((B @ S @ B)[1, 1] * nn / (nn - k)))


print("\nC. Sensibilidad del RDiT en Bangladesh (pp; error estándar HAC entre paréntesis)")
print("   el día de corte queda del lado posterior, como en la especificación archivada")
for cut in ["2024-07-17", "2024-07-18", "2024-07-19"]:
    cells = []
    for bw in (4, 5, 7, 10, 14):
        b, se = rd(y_r, pd.Timestamp(cut), bw)
        cells.append(f"h={bw}: {b:6.2f} ({se:4.2f})")
    print(f"  corte {cut} | " + " | ".join(cells))
leg = pd.read_csv(PROC / "table3_rdit_sensitivity.csv")
print(f"\n  grilla anterior guardada en data/processed/table3_rdit_sensitivity.csv: {len(leg)} especificaciones, "
      f"tau entre {100 * leg.tau.min():.1f} y {100 * leg.tau.max():.1f} pp (no reportada en el manuscrito)")
