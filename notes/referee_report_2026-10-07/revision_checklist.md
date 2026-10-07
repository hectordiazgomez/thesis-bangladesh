# Lista de revisiones — informe de arbitraje del 7 de octubre de 2026

Versión de trabajo del informe `referee_report.pdf` (misma carpeta). La evidencia y las tablas están en
el PDF; aquí solo está lo que hay que hacer. Manuscrito auditado: commit `7346f22`,
`paper/latex/main.tex`.

Reglas para todas las tareas:

- No adoptar ningún cambio porque produzca resultados más fuertes. Si una especificación cambia,
  reportar la original junto a la nueva.
- M2 y M4 son cambios metodológicos mayores: acordarlos con el asesor antes de implementarlos.
- Toda afirmación sobre hechos políticos o de conectividad necesita fuente; si no la hay, escribir
  `[CITATION NEEDED]`.
- Al terminar cada tarea, registrar en `notes/revision_log.md`.

Cada cifra de esta lista sale de `audit_scripts/` (salidas en `audit_scripts/output/`).

## Prioridad 1 — antes de cualquier otra cosa

### R1. Outcomes secundarios: numerador y denominador de muestras distintas
- **Problema:** en `results/synthetic_control/country_day_outcomes_enriched.parquet` el numerador
  cuenta a los 150,017 usuarios del archivo usuario-día y el denominador a los 59,158 elegibles.
- **Hacer:** reconstruir el panel solo con elegibles; regenerar `results/final/table_secondary_*.csv`
  y `results/final/table_DiD_all_outcomes.csv`; regenerar `tab_secondary_outcomes`,
  `tab_did_secondary`, `tab_donor_weights_specific`; actualizar la sección 6.4 y la frase de la
  introducción con −86.2, −92.2 y −92.1; reportar los rangos placebo de los dos outcomes de conteo;
  subir el código.
- **Análisis nuevo:** recalcular, misma especificación.
- **Referencia:** mi reconstrucción da −11.665 pp (−86.6%) para actividad productiva con pesos fijos,
  frente a −15.179 pp (−86.5%) en el manuscrito. Ver `03_secondary_sc_reproduce.py`.
- **Aceptación:** `02_secondary_sample_check.py` muestra coincidencia con "solo elegibles".

### R2. Definir el outcome primario, la elegibilidad y los bots
- **Problema:** `productive_events` incluye tipos de evento no enumerados (9.5% de los usuario-día
  activos no tiene ningún componente listado); "four active days" cuenta cualquier evento; la regla
  de bots (1,571 exclusiones) no es reconstruible.
- **Hacer:** listar en la sección 4.2 los tipos de evento de GH Archive del outcome primario;
  escribir las reglas de elegibilidad y de bots con sus umbrales; declarar que los días son UTC;
  subir el código que genera `eligible_users_donors.parquet`.
- **Análisis nuevo:** no.

### R3. Tablas y figuras deben correr en un clon limpio
- **Hacer:** versionar `results/sector_recovery/sectorwide/sectorwide_support.csv`,
  `results/sector_recovery/pre8/sector_recovery_summary_pre8.csv` y los
  `sectorwide_user_eventstudy.csv` de los umbrales 0.70 y 0.90 (o eliminar la dependencia); llamar
  a `fig_sc_intime_placebos` desde `main()` en `analysis/figures/make_all_figures.py`.
- **Aceptación:** `make_all_tables.py`, `make_all_figures.py` y
  `10_make_sector_results_final.py` terminan sin error en un clon nuevo.

### R5. El 4 al 7 de agosto
- **Problema:** la nota de la Figura 1 atribuye la caída del 5 de agosto a un feriado;
  `data/processed/panel_clean.parquet` codifica el 4–5 de agosto como `f4_second` y el 28 de julio
  al 3 de agosto como `f3_socialblock`. El manuscrito no menciona un segundo corte.
- **Hacer:** documentar con fuentes qué ocurrió esos días `[CITATION NEEDED]`; corregir la nota de
  la Figura 1 y el párrafo de la sección 6.5 sobre la caída de la semana +2.
- **Análisis nuevo:** no.

### M1. Mecanismo: cohorte, niveles y redacción
- **Problema:** 1,835 de los 2,932 commits "del apagón" se crearon el 18 de julio antes de las
  15:00 UTC, antes del corte total (rezago 4.2%). Los 1,097 creados sin conexión tienen rezago de
  68.6% y son el 3.2% del volumen normal de seis días (33,787 commits ponderados).
- **Hacer:**
  1. Definir la cohorte desde el inicio del corte total y reportar ambas definiciones.
  2. Presentar la serie diaria de commits por fecha de autoría como outcome propio.
  3. Reescribir resumen, introducción, sección 7, discusión y conclusión con el nivel además de la
     participación.
  4. Discutir la censura al 10 de agosto.
  5. Explicar los 345 commits creados durante el corte total y publicados antes del 24.
- **Análisis nuevo:** sí.
- **Referencia:** `04_mechanism_reproduce.py`.

### M2. Quiebre del 2 de julio y regla de elegibilidad — acordar antes de implementar
- **Problema:** la tasa de Bangladesh salta de 19.1% a 25.5% el 2 de julio; brecha media de +4.8 pp
  frente al sintético del 1 al 17 de julio. 891 usuarios tratados (8.7%) tienen su primera
  actividad desde el 29 de junio, frente a 2.1–4.5% en los donantes. Según la ventana de ajuste, el
  ATT va de −11.32 a −15.57 pp.
- **Hacer:**
  1. Definir la elegibilidad en una ventana anterior al período de estimación.
  2. Averiguar y documentar con fuentes qué ocurrió a inicios de julio; verificar con la fecha de
     creación de las cuentas si la cohorte es de cuentas nuevas.
  3. Reportar la tabla de sensibilidad a la ventana de ajuste en el texto principal.
  4. Matizar las frases sobre recuperación rápida (secciones 6.2, 9 y 10).
- **Análisis nuevo:** sí.
- **Referencia:** `07_referee_diagnostics.py`.

## Prioridad 2 — necesario para enviar

### M4. Inferencia — acordar antes de implementar
- **Hacer:** ampliar el grupo de donantes con una regla fijada de antemano; añadir inferencia que
  use las 78 observaciones previas (Chernozhukov, Wüthrich y Zhu 2021) y discutir el ajuste
  imperfecto (Ferman y Pinto 2021); agregar a frecuencia semanal o quitar el efecto de día de la
  semana; presentar el DiD como diferencia de medias, no como confirmación independiente; decir en
  el texto que el test de rango da 1/15 en 4 de 11 semanas previas.
- **Análisis nuevo:** sí.

### M3. Apagón frente a disturbios
- **Hacer:** cronología con fuentes de todo lo que cambió esos días; análisis horario alrededor
  del corte (18 de julio, ~15:00 UTC), la vuelta de banda ancha (23, ~13:00 UTC) y la del móvil
  (28, ~09:00 UTC); usar el período del 1 al 17 de julio; buscar episodios comparables.
- **Análisis nuevo:** sí (horario).

### M5. Medición
- **Hacer:** reportar el efecto del 19 al 22 de julio (−14.47 pp, −98.6%) junto al de la ventana
  completa; reportar la actividad residual (0.2%) como cota del error de ubicación; discutir la
  reversión a la media.
- **Análisis nuevo:** ya calculado en `07_referee_diagnostics.py`.

### M8. Pregunta económica y encuadre
- **Hacer:** calcular la pérdida acumulada en días-usuario activos, si hubo recuperación por encima
  del contrafactual, y la persistencia; quitar o respaldar el párrafo de política de la sección 9;
  reordenar las contribuciones.
- **Análisis nuevo:** cálculo simple.

### R4. Cifras sectoriales no verificables
- **Hacer:** guardar en `results/sector_recovery/` los conteos de la sección 4.4 (23,866; 168,875;
  92,979; 32,491), el 82.5% de la sección 8.3 y el resumen `pre8`.

### R6. Código aguas arriba
- **Hacer:** subir las consultas a GH Archive, la construcción de `data/processed/`, la agregación
  a país-día, la estimación por outcome, el SDID, la grilla del RDiT, la extracción y el muestreo
  del mecanismo (con semilla), y la selección de la muestra de 20,000 (con semilla).

## Prioridad 3 — limpieza

### M6. RDiT
- **Hacer:** eliminarlo, o rehacerlo con datos horarios y corte en el inicio del apagón. Si se
  queda, reportar la grilla completa y justificar el corte. No elegir la especificación por su
  resultado.

### M7. Recuperación sectorial
- **Hacer:** moverla al apéndice como descripción, o reemplazarla por heterogeneidad según rasgos
  del usuario fijados antes del apagón.

### Bibliografía
- `cloudflare2024`: autor David Belson; añadir URL.
- `isoc2024`: usar la URL específica de la entrada.
- `githubevents`: citar una versión fechada de la documentación.
- `schachenhofer2023`: volumen 98, artículo 104101.
- `aceto2018`: apellido Pescapé; citarla o quitarla junto con `schachenhofer2023`.
- Corregir "independently records", "residential", la fila del 16–17 de julio de la Tabla 1, la
  frase sobre Kreitmeir y Raschky, y la de Hausman y Rapson.
- Añadir: Chernozhukov, Wüthrich y Zhu (2021); Abadie, Diamond y Hainmueller (2015); Ferman y Pinto
  (2021); Ben-Michael, Feller y Rothstein (2021); Conley y Taber (2011); Zhang y Zhu (2011);
  McDermott y Hansen (2021). Los DOI están en el PDF.

### R7. Empaquetado
- `requirements.txt` para el análisis principal (incluir `pyarrow` y `db-dtypes`).
- Unificar en `README.md` y `main.tex` cuál es el manuscrito vigente; retirar `paper/thesis.txt` y
  `paper/thesis.docx` si ya no lo son.
- Completar `manifest.csv` (faltan 33 archivos).

### Comentarios menores
Los nueve puntos de la sección 3.4 del PDF.
