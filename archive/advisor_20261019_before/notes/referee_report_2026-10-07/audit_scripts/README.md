# Scripts de auditoría

Respaldan las cifras de `../referee_report.pdf`. Solo leen el repositorio: no modifican datos,
resultados ni el manuscrito.

## Cómo ejecutarlos

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python 01_rebuild_country_day.py        # y así con 02 … 08
```

Sin argumentos, cada script usa la raíz del repositorio que lo contiene. Para apuntar a otra copia:
`python 01_rebuild_country_day.py /ruta/al/repo`.

`09_compare_figures.py` necesita dos carpetas: las figuras versionadas y las regeneradas en una copia
del repo con `analysis/figures/make_all_figures.py`.

Las salidas de la auditoría del 7 de octubre de 2026 (commit `7346f22`) están en `output/`.

## Qué verifica cada uno

| Script | Verifica | Informe |
|---|---|---|
| `01_rebuild_country_day.py` | Reconstruye el panel país-día del outcome principal y la regla de elegibilidad | Tabla de estado, R2 |
| `02_secondary_sample_check.py` | Los outcomes secundarios usan numerador de todos los usuarios | R1 |
| `03_secondary_sc_reproduce.py` | Reproduce las tablas secundarias archivadas y calcula la versión corregida | R1 |
| `04_mechanism_reproduce.py` | Reproduce las tablas del mecanismo; cohortes por fecha y hora de autoría; niveles | M1 |
| `05_definitions_rdit.py` | Contenido de `productive_events`; muestra y sensibilidad del RDiT | R2, M6 |
| `06_text_claims.py` | Cruza cifras del texto con los archivos de resultados | Sección 2.4 |
| `07_referee_diagnostics.py` | Ventana de ajuste, composición diaria del ATT, cohorte de julio, día de la semana | M2, M4, M5 |
| `08_context_checks.py` | Feriados, fases del análisis previo, calibración del test de rango | R5, M4 |
| `09_compare_figures.py` | Compara figuras versionadas y regeneradas | Tabla de estado |

Los cálculos marcados como diagnóstico en el informe (sensibilidad del control sintético y del RDiT,
cohorte de julio) son verificaciones de arbitraje. No son especificaciones nuevas del paper.
