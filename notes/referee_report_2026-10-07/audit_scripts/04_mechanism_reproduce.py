#!/usr/bin/env python3
"""Auditoría: reproducir las tablas del mecanismo desde commit_sha_author_push_master.parquet (no hay código en el repo)
y diagnósticos adicionales de referee.

Solo lectura: no modifica ningún archivo del repositorio.
Uso (desde cualquier carpeta):  python 04_mechanism_reproduce.py [ruta_al_repo]
Sin argumento usa la raíz del repositorio que contiene este script."""
import sys, itertools
from pathlib import Path
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]; MECH = REPO/"results/mechanism"; FINAL = REPO/"results/final"
m = pd.read_parquet(MECH/"commit_sha_author_push_master.parquet")
print("master: filas", len(m), "| found", int(m.found.sum()), f"({100*m.found.mean():.2f}%)", "| metadata_requested", int(m.metadata_requested.sum()))
print("push_time rango:", m.push_time.min(), "->", m.push_time.max())
strict = m[m.found & m.authored_time.notna() & m.author_equals_pusher.fillna(False).astype(bool) & (m.author_to_push_hours >= 0)].copy()
print("muestra estricta:", len(strict), "(paper: 59,920)")
B0, B1 = pd.Timestamp("2024-07-18", tz="UTC"), pd.Timestamp("2024-07-24", tz="UTC")
c = strict[(strict.authored_time >= B0) & (strict.authored_time < B1)].copy()
print("autorados Jul 18-23 UTC:", len(c), "| flag authored_during_blackout:", int(strict.authored_during_blackout.sum()))
back = c.push_time >= B1
print(f"backlog (push >= Jul 24 UTC): {int(back.sum())} = {100*back.mean():.4f}% | flag offline_author_backlog: {int(c.offline_author_backlog.sum())}")
for h in (24, 48, 72, 120): print(f"  delay > {h}h: {100*(c.author_to_push_hours>h).mean():.4f}%")
print(f"  mean delay h: {c.author_to_push_hours.mean():.4f}")
# committedDate
s2 = m[m.found & m.committed_time.notna() & m.committer_equals_pusher.fillna(False).astype(bool) & (m.commit_to_push_hours >= 0)]
c2a = s2[(s2.committed_time >= B0) & (s2.committed_time < B1)]
s3 = m[m.found & m.committed_time.notna() & m.author_equals_pusher.fillna(False).astype(bool) & (m.commit_to_push_hours >= 0)]
c2b = s3[(s3.committed_time >= B0) & (s3.committed_time < B1)]
print(f"committedDate (committer=pusher): N {len(c2a)}, backlog {int((c2a.push_time>=B1).sum())} = {100*(c2a.push_time>=B1).mean():.3f}%")
print(f"committedDate (author=pusher):    N {len(c2b)}, backlog {int((c2b.push_time>=B1).sum())} = {100*(c2b.push_time>=B1).mean():.3f}%   (paper: 790 de 2,909 = 27.16%)")
# concentración
u = c.groupby("pusher_login").agg(n=("sha","size"), b=("offline_author_backlog","sum")).sort_values("b", ascending=False)
r = c.groupby("repo").agg(n=("sha","size"), b=("offline_author_backlog","sum"))
tot = u.b.sum()
print(f"usuarios {len(u)} | con backlog {int((u.b>0).sum())} ({100*(u.b>0).mean():.2f}%) | repos {len(r)} | con backlog {int((r.b>0).sum())} ({100*(r.b>0).mean():.2f}%)")
print(f"top1 {100*u.b.iloc[0]/tot:.2f}% | top5 {100*u.b.iloc[:5].sum()/tot:.2f}% | top10 {100*u.b.iloc[:10].sum()/tot:.2f}%")
for k in (1,3,5,10,20):
    keep = c[~c.pusher_login.isin(u.index[:k])]
    print(f"  sin top{k}: N {len(keep)}, backlog {100*keep.offline_author_backlog.mean():.2f}%")
for lab, mask in [("all", c.push_size>0), ("<=10", c.push_size<=10), ("<=5", c.push_size<=5), ("<=2", c.push_size<=2), ("==1", c.push_size==1)]:
    g = c[mask]; print(f"  push_size {lab:5s} N {len(g):5d} backlog {int(g.offline_author_backlog.sum()):4d} = {100*g.offline_author_backlog.mean():.2f}%")
# fechas de liberación
b = c[c.offline_author_backlog]; d = b.push_time.dt.date.value_counts().sort_index(); cum = 100*d.cumsum()/len(b)
print("liberación backlog:", {str(k): (int(v), round(cum[k],1)) for k, v in d.items() if str(k) <= "2024-07-31"})
# cobertura de metadata por período de push
per = np.where(m.push_time < B0, "PRE", np.where(m.push_time < B1, "BLACKOUT", "POST"))
cov = m.groupby(per).agg(N=("sha","size"), found_pct=("found", lambda x: 100*x.mean()),
        author_login_pct=("author_login", lambda x: 100*x.notna().mean()),
        aep=("author_equals_pusher", lambda x: 100*x.fillna(False).astype(bool).mean()))
print("\ncobertura por período de push:\n", cov.round(2).to_string())
print("\n================ DIAGNÓSTICOS ADICIONALES (cálculos propios del auditor) ================")
c["aday"] = c.authored_time.dt.date.astype(str); c["pday"] = c.push_time.dt.date.astype(str)
t = c.groupby("aday").agg(N=("sha","size"), backlog=("offline_author_backlog","sum"), users=("pusher_login","nunique"),
                          same_day=("sha", lambda s: 0))
t["same_day"] = (c.aday == c.pday).groupby(c.aday).sum()
t["pushed_in_blackout_window"] = (c.push_time < B1).groupby(c.aday).sum()
t["backlog_pct"] = 100*t.backlog/t.N
print("Commits autorados durante Jul 18-23 por día de autoría (UTC):\n", t.round(1).to_string())
# Jul 18 antes/después de las 15:00 UTC (~21:00 hora local, cuando el tráfico nacional cae a ~0 según el paper)
cut = pd.Timestamp("2024-07-18 15:00", tz="UTC")
for lab, g in [("autorados Jul 18 antes de 15:00 UTC (antes del apagón total)", c[c.authored_time < cut]),
               ("autorados desde Jul 18 15:00 UTC hasta Jul 23 (apagón total)", c[c.authored_time >= cut])]:
    print(f"{lab}: N {len(g)}, backlog {int(g.offline_author_backlog.sum())} = {100*g.offline_author_backlog.mean():.1f}%, "
          f"empujados dentro de la ventana Jul 18-23: {int((g.push_time < B1).sum())}, usuarios {g.pusher_login.nunique()}")
g = c[(c.authored_time >= cut)]
ins = g[g.push_time < B1]
print("  -> de los autorados en apagón total y empujados antes de Jul 24: por día de push", ins.pday.value_counts().sort_index().to_dict(), "| usuarios", ins.pusher_login.nunique())
# volumen relativo a ventanas placebo (weighted_N = población estimada de commits estrictos autorados por ventana de 6 días)
pl = pd.read_csv(FINAL/"table_mechanism_placebos.csv"); wN = pl[pl.window.str.startswith("PLACEBO")].weighted_N.mean()
print(f"\nVolumen: commits estrictos autorados por ventana placebo de 6 días (ponderado): {wN:,.0f}; durante el apagón: {len(c):,} "
      f"= {100*len(c)/wN:.1f}% de lo normal; backlog 829 = {100*829/wN:.2f}% del volumen normal; "
      f"autorados en apagón total (>=15:00 UTC Jul 18): {len(g):,} = {100*len(g)/wN:.1f}%")
# censura a la derecha: ventana de observación de pushes termina Aug 10
print("último push observado:", m.push_time.max(), "| commits del backlog empujados en Aug 5-10:", int((b.push_time >= pd.Timestamp('2024-08-05', tz='UTC')).sum()))
# zona horaria: ¿la ventana usa UTC? distribución horaria de autoría en la ventana
print("autorados por hora UTC el 18 de julio:", c[c.aday=='2024-07-18'].authored_time.dt.hour.value_counts().sort_index().to_dict())
# tamaño de push entre backlog y no backlog
print("push_size mediana backlog vs no backlog:", b.push_size.median(), c[~c.offline_author_backlog].push_size.median(),
      "| commits de backlog en pushes >10:", int((b.push_size>10).sum()))
# ¿los pushers del análisis de mecanismo pertenecen a la muestra elegible del control sintético?
el = pd.read_parquet(REPO/"results/synthetic_control/eligible_users_donors.parquet")
e = set(el[el.country=="Bangladesh"].login.str.lower())
pe = set(pd.read_parquet(MECH/"bd_push_events_20240701_20240810.parquet", columns=["pusher_login"]).pusher_login.str.lower())
print(f"\npushers en bd_push_events: {len(pe):,} | dentro de los 10,241 elegibles de Bangladesh: {len(pe & e):,}")
uni = pd.read_parquet(MECH/"clean_repo_sha_first_push.parquet", columns=["push_time"]); dd = uni.push_time.dt.date.astype(str)
npre = int((dd < "2024-07-18").sum()); req_pre = int((m.push_time < B0).sum())
print(f"universo de pares repo-SHA: {len(uni):,} | empujados antes del 18 de julio: {npre:,} | con metadata solicitada: {req_pre:,} ({100*req_pre/npre:.1f}%)")
