# Informe de revisión — segunda ronda

Fecha: 8 de octubre de 2026. Rama `referee-round2`, creada desde `referee-pending-items` en `d680ffb`. Hay commits identificados por comentario y un cierre de verificación. **No se hizo push.**

El resultado principal permanece exactamente en **−13,255939 pp (−86,769280%)**, con actividad observada de 2,021287%, contrafactual de 15,277226%, tratamiento julio 18–23, 10.241 cuentas de Bangladesh y los mismos 14 donantes. Los diagnósticos de la fase B no sustituyen ninguna cifra principal. No se modificaron los datos procesados ni los resultados archivados anteriores a esta ronda.

## 1. Estado por comentario

«Bloqueado» identifica información indispensable ausente; no significa que la parte verificable se haya omitido. «Preparado para asesor» mantiene todas las alternativas fuera de la especificación principal. Las cifras nuevas se añaden al lado de las originales, salvo las correcciones editoriales indicadas.

| ID | Estado | Trabajo y cifras anteriores → nuevas |
|---|---|---|
| R1, R3, R4 | Hecho previamente | Se conservaron las correcciones de la ronda anterior; sin nuevas sustituciones. |
| Bibliografía y 7 referencias | Hecho previamente | Se conservaron las correcciones; las cuatro referencias ligadas a M4 siguen sólo en el borrador pendiente. |
| R5 | Hecho | Fuentes del segundo corte, anuncio de festivos y reapertura; corregidas nota de Figura 1 y §6.5. Alternativa de festivos agosto 6–7: 1→0 sólo en archivos nuevos. DiD −13,087502→−13,087502; sin festivos −13,379098→−13,379098 pp. Conflicto adicional entre archivos documentado. |
| R2 | Bloqueado parcialmente | §4.1/4.2 y Tabla 2 distinguen 17,254550% primario de 15,379483% secundario, sin redefinirlos. Regla verificable: ≥4 días con cualquier evento, UTC. 60.729 candidatos frente a 59.158 retenidos; faltan reglas de 1.571 exclusiones y mapa exacto de tipos de productive_events. Tres métricas de bots reproducidas para los 59.158 retenidos. |
| R6 | Bloqueado parcialmente | Se incorporaron 25 scripts históricos distintos, con procedencia y SHA-256; 35 archivos encontrados quedaron inventariados, incluidas copias duplicadas. No se encontró el código original de varias etapas actuales; se enumeran abajo. Ninguna cifra sustituida. |
| R7 | Hecho para análisis con insumos almacenados | requirements.txt incluye db-dtypes y jinja2; README identifica LaTeX/PDF como versión actual; manifest.csv enumera todos los archivos versionados. Se empaquetaron copias de insumos sectoriales para reproducir análisis posteriores. La adquisición completa sigue bloqueada. |
| M5 | Hecho | Ventana principal conservada: −13,255939 pp, −86,769280%. Sensibilidad julio 19–22: observado 0,212382%, contrafactual 14,686946%, ATT −14,474564 pp, −98,553943%. Se discuten selección y reversión a la media. |
| M1 | Hecho con límites de observación | Calendario: 2.932 commits, 829 retrasados, 28,274216%. Desde 15:00 UTC julio 18: 1.097, 752 y 68,550593%. Frente a referencia de duración equivalente, creación observada −96,347991%; backlog 2,503474% de lo normal. Se reescribió el argumento en niveles y se explicó la censura al agosto 10. |
| M8 | Hecho | Se añadieron 8.145 días-usuario de déficit durante el cierre; 10.186 hasta primer cruce diario julio 27; 12.068 hasta cruce de media móvil agosto 13. Déficit neto al septiembre 4: 3.633. Se eliminan afirmaciones no sustentadas de política y de tres márgenes identificados. |
| M6 | Hecho; decisión preparada | Se mantiene −9,2836 pp. Grilla nueva de 45 ajustes, con rango Bangladesh −4,4457 a −19,5230; se muestran también las 16 filas archivadas (−12,4 a −23,7). Corte y discrepancias explícitos; no se eliminó el RDiT. |
| M2 | Preparado para asesor; datos parciales bloqueados | Tabla 3: original −13,2559; alternativas de ajuste −11,3174, −14,7037, −15,5732 pp. Cohorte tardía 891 (889 con inicio pretratamiento). Elegibilidad fijada en mayo: 5.140 cuentas y −16,0099 pp; misma muestra original con ajuste junio: −13,3205. Ninguna adoptada. |
| M4 | Preparado para asesor; ampliación bloqueada | Regla de donantes propuesta; ajuste por día de semana −14,023087 frente a −13,255939 pp. DiD como cuatro medias reproducido. Conformal: p nula cero 0,011905 y grilla aceptada [−19; −6,5], con fuertes reservas de estabilidad; p entre países sigue 0,0667. |
| M3 | Preparado para asesor; comparación completa bloqueada | Cronología y diagnóstico horario de pushes. Usuarios activos/hora, 12 h antes→después: corte 130→2,42; fija 1,25→8,67; móvil 67,92→139,50. Todos los anchos 6/12/24 h publicados. No son efectos causales ajustados. |
| M7 | Preparado para asesor | Opciones concretas: apéndice, heterogeneidad por rasgos previos o mantener descripción. No se reestructuró el bloque sectorial. |
| Menor 1 | Hecho | Corte de Pakistán julio 31 documentado como amenaza al contrafactual de recuperación; peso 47,6% conservado. |
| Menor 2 | Hecho | Tamaños explícitos: Ghana 1.373, Jordania 446; advertencia de ruido muestral. Sin cambio de donantes. |
| Menor 3 | Hecho | 86.065 objetivos de consulta =17.000 pre +69.065 post; universo pre 134.479, fracción 12,64%. No confundir objetivo y universo. |
| Menor 4 | Hecho | authoredDate/committedDate se describen como metadatos dependientes; no validación independiente del reloj. Sin cambio numérico. |
| Menor 5 | Hecho con discrepancia preservada | Desempate determinista; top-10 sigue 651/2.739=23,767798%. El 2.740/23,76% del informe no se reproduce bajo esa regla. |
| Menor 6 | Hecho | Se corrige el orden invertido: Finanzas 91,3; Información 94,5. Archivos de resultados intactos. |
| Menor 7 | Hecho | «Dentro del rango previo» se califica como criterio débil; se añaden criterios explícitos M8. |
| Menor 8 / Ashura | Hecho previamente | Se conserva la fuente de julio 17 ya incorporada. |
| Menor 9 | Hecho | DOCX/TXT retirados del uso actual y etiquetados como borradores históricos obsoletos; preservados para procedencia. |
| Informe §2.4 | Hecho | Inmobiliario +7=108,262108→108,3 se añade a semanas sobre 100. Máximo de Información 126,349848: redondeo 126,4→126,3. |

Los 0,212382% de actividad residual acotan el componente **activo observado** que podría estar mal localizado; no acotan toda la proporción de cuentas físicamente fuera del país. Las cuentas inactivas no permiten conocer ubicación.

En M1, comparar directamente el tramo de 5,375 días con seis días normales da −96,753237%; ajustar duración con ventanas equivalentes da −96,347991%. Se muestran ambas, sin favorecer la caída mayor. El calendario julio 18–23 incluye 1.835 commits anteriores al corte total y cae 91,322234% frente a seis días normales. El backlog calendario es 2,453570% del nivel normal, frente al 28,274216% condicional sobre los pocos commits del cierre. Los 345 commits del tramo posterior al inicio publicados antes de julio 24 corresponden a 64 usuarios; 246 se publicaron julio 23 y 99 antes. Los datos no distinguen acceso excepcional, ubicación distinta o problemas de reloj. Los pesos previos corrigen muestreo por fecha del primer push, no fallos de recuperación de metadatos. Hay 35 commits del backlog calendario publicados agosto 5–10; publicaciones posteriores y trabajo nunca público no son observables.

M8 conserva todos los criterios: primer cruce diario del contrafactual julio 27; primera media móvil de siete días no negativa agosto 13; primeros siete días consecutivos no negativos terminan agosto 16. Respecto a la media propia previa, los cruces son agosto 14 y agosto 22. Hasta septiembre 4, área negativa 13.526,274 y positiva 9.893,465 días-usuario, saldo −3.632,809; déficit máximo 13.236,567 agosto 9. La compensación aritmética es parcial, no evidencia identificada de recuperación causal ni medida de horas/productividad total.

## 2. Decisiones para el asesor

El detalle y las tablas están en `notes/advisor_decisions_round2.md`.

- **M2:** recuperar creación de cuentas e historial anterior a mayo; conservar toda la sensibilidad de ventanas mientras se decide una regla que separe selección y estimación. Los nombres compartidos assignment-1 (126 usuarios), web-dev-portfolio (112), my-first-github-repo (71) y g3-architects-website (67) sugieren ejercicios comunes, pero no identifican un bootcamp. Las 879 cuentas con pushes previos no comparten un repositorio completo o propietario entre cuentas en este extracto. Las noticias de huelga universitaria y protestas desde julio 1 no prueban la causa del aumento GitHub.
- **M3:** recuperar todos los tipos de eventos y controles horarios para investigar conectividad frente a conflicto. Mantener ahora el diagnóstico disponible como descriptivo. Rajasthan, septiembre 26 de 2021 (examen), y Venezuela tras julio 28 de 2024 (protestas sin corte nacional, con bloqueos de sitios) son candidatos documentados, no nuevos resultados o donantes.
- **M4:** decidir y registrar una regla de cobertura, tamaño y conectividad antes de obtener nuevos outcomes. Propuesta: ≥1.000 elegibles en ventana anterior a mayo, filtro de bots verificable, cobertura externa y exclusión por cortes nacionales ≥20% durante ≥1 h en el período pertinente. No hay datos locales para enumerar países añadidos. Resolver M2 antes de adoptar inferencia temporal: autocorrelación residual pre=0,674; gap mayo–junio 0,095 pp frente a julio 4,824 pp. El conjunto conformal corresponde a trayectorias constantes; no es un intervalo irrestricto del ATT ni reemplaza p=0,0667.
- **M6:** preferir reconstrucción horaria en el inicio efectivo si se recuperan outcome y controles; si eso no es viable, retirar su papel causal. El manuscrito conserva entretanto el RDiT y todas las sensibilidades, con limitaciones.
- **M7:** recomendar el apéndice descriptivo ahora; evaluar después heterogeneidad fijada por rasgos previos, con protocolo y pocos grupos establecidos antes de ver resultados. Ninguna de estas opciones se ejecutó en el manuscrito.

## 3. Conflictos y límites de procedencia registrados

1. **Agosto:** anuncio de festivos agosto 5–7 frente al anuncio BSS de reapertura agosto 6. Además, country-day is_holiday=1 agosto 5–7, mientras panel_clean.hol_bd=0 agosto 4–7 y f4_second=1 agosto 4–5. La descripción conjunta inicial no correspondía a los dos archivos. Una orden de reapertura tampoco demuestra que cada institución abriera.
2. **Definición del outcome:** tasas pre primarias 17,254550% y secundarias 15,379483% son distintas. 104.786 de 1.103.680 días-usuario activos carecen de los componentes documentados. El panel sectorial tiene ocho tipos seleccionados, pero no reconstruye el recuento primario: sobre 179.468 días comunes, rango de matriz 8 frente a 9 al agregar productive_events. No se declara una lista no verificada.
3. **Elegibilidad/bots:** 60.729 candidatos por actividad, 59.158 finales; 1.571 exclusiones sin explicación recuperable. Los flags de retenidos son falsos, pero no revelan reglas para excluidos. Se verifican máximo diario de commits, días con commits y esos días/78, no los umbrales.
4. **Mecanismo:** cohorte calendario y cohorte desde inicio total no son equivalentes; 1.835 commits son anteriores al inicio total. Los 345 pushes antes de julio 24 y la censura requieren cautela. La proporción retrasada no mide la fracción de producción normal preservada.
5. **RDiT:** archivo histórico h=7 lineal sin donut −14,0 pp frente a preferido reproducido −9,2836 pp. Faltan procedencia/corte/muestra de las 16 filas; se preservan ambas. RDiT contiene 174 cuentas fuera del SCM y pierde 86 de éste, no sólo 88 cuentas adicionales. Julio 17 no coincide con el corte nacional julio 18 a las 15:00 UTC.
6. **Cohorte tardía:** 891 con primera actividad desde junio 29, pero sólo 889 si también se exige que comience antes del cierre. Primera actividad observada no equivale a creación de cuenta. Salto diario julio 1→2: +652, de los que +320 son tardíos; la comparación del informe +440/+1.035 utiliza una ventana de contraste no especificada y no se declara reproducida.
7. **Concentración:** top-10 determinista 2.739 y 23,767798%, frente a 2.740 y 23,76% del informe; no se cambió un número para forzar coincidencia.
8. **Sector:** corregida inversión Finanzas/Información; añadido Inmobiliario +7>100; evitado doble redondeo de Información. Retornar al rango previo no implica nivel o compensación acumulada recuperados.
9. **Horario:** 182.808 filas PushEvent frente a 182.807 eventos únicos; una duplicación exacta se elimina únicamente en el archivo diagnóstico nuevo. Estos pushes no son la definición completa del outcome principal.
10. **Inferencia y donantes:** p conformal 0,011905 y p entre países 0,0667 responden a procedimientos y supuestos distintos. El quiebre de julio amenaza calibración temporal; el corte pakistaní julio 31 afecta interpretación de recuperación. No se elige la inferencia o el conjunto de donantes por significación.

## 4. Pendientes y qué se necesita

| Pendiente | Insumo o decisión necesaria |
|---|---|
| R2: lista exacta GH Archive y constructor completo de elegibles | SQL original, reglas de tipo/acción, patrones y umbrales de bots, auditoría de excluidos. Consulta reconstruida preparada: `analysis/pending/r2_event_types.sql`. Coincidencia nueva no sustituye procedencia histórica. |
| R6: upstream actual | Recuperar búsqueda/extracción original por país, agregación productive_events, festivos, filtros de bots, código original de grilla RDiT de 16 especificaciones, procedimiento/SE de SDID y extracción/muestreo/consulta de metadatos del mecanismo. Semilla del muestreo pre de metadatos ausente; semilla sectorial 20240718 sí recuperada. Buscar en otras ubicaciones o servicios requeriría autorización adicional. |
| M2: creación, organizaciones, selección anterior al ajuste original | Ejecutar GraphQL preparado `m2_accounts.graphql` con acceso adecuado y paginar organizaciones; membresía actual no prueba membresía en 2024. Obtener enero–abril para todos los países con `m2_before_may_eligibility.sql`; precisar ventana del contraste +440/+1.035. |
| M4: países que entrarían | Lista mundial congelada de cuentas/ubicaciones, consulta `m4_candidate_universe.sql`, filtro verificable y auditoría de conectividad. El conteo local es sólo una aproximación de tamaño en la ventana archivada. Aprobación antes de cambiar donantes/inferencia. |
| M3: diseño horario completo y episodios comparables | Ejecutar `m3_hourly_all_events.sql`, recuperar outcome primario y denominadores comparables, cuentas/geografía del episodio de Rajasthan y datos de Venezuela; diseño aprobado. |
| M6 y M7 | Aprobación explícita del asesor sobre papel/diseño RDiT y ubicación o reemplazo de la sección sectorial. |
| Reproducibilidad de adquisición completa | Dos entradas de descarga/clasificación sectorial sólo verificadas con --help. Para ejecutarlas de extremo a extremo hacen falta servicios externos GitHub, metadatos/README históricos, dependencias/modelo sectorial y los insumos/query originales. Los análisis con insumos almacenados sí se prueban en clon limpio. |
| Observabilidad del mecanismo | Para estudiar censura más allá de agosto 10 harían falta pushes posteriores. No puede recuperarse de GitHub público el código nunca publicado ni la localización física o el momento real de escritura. No se imputaron esos resultados. |

No se ejecutaron nuevas consultas GH Archive/BigQuery ni se inventaron resultados pendientes. El intento de abrir el informe OHCHR recibió 403; la cronología se apoya en fuentes alternativas efectivamente abiertas.

## 5. Verificación

- Tras cada fase se ejecutaron `analysis/tables/make_all_tables.py` y `analysis/figures/make_all_figures.py`.
- `latexmk -xelatex main.tex`, ejecutado dentro de paper/latex, produce thesis.pdf de 50 páginas. Sin errores, citas/referencias indefinidas ni cajas desbordadas. Se revisaron visualmente las páginas y las tablas/figuras añadidas.
- Fase A: 22 análisis con insumos almacenados aprobaron en clon limpio; dos entradas externas sólo --help.
- Fase B: entorno Python 3.14 nuevo instalado únicamente desde requirements.txt; 25 análisis con insumos almacenados aprobaron en clon limpio; dos entradas externas sólo --help. Los JSON de auditoría registran invocaciones y commit probado. No se afirma reproducción completa del upstream.
- Los SHA-256 de los 141 archivos de datos/resultados versionados preexistentes coinciden con la instantánea anterior a esta ronda. El manifiesto cubre los 326 archivos versionados y git diff --check pasa. La bitácora registra todas las cifras añadidas o corregidas.

## Sources — URLs efectivamente abiertas

Fuentes de esta ronda; las fuentes bibliográficas y de Ashura de la ronda anterior permanecen en `notes/referee_pending_items_audit.md`.

1. [Cloudflare: interrupciones del tercer trimestre de 2024](https://blog.cloudflare.com/q3-2024-internet-disruption-summary/).
2. [BSS: anuncio de reapertura agosto 6](https://www.bssnews.net/news/top-news/202726).
3. [Bangladesh News: anuncio de tres días de festivo](https://bangladeshnews.live/national/news/general-holiday-for-three-consecutive-days-from-tomorrow).
4. [Cloudflare / Belson: interrupciones de julio de 2024](https://blog.cloudflare.com/a-recent-spate-of-internet-disruptions-july-2024/).
5. [UNB: huelga de docentes universitarios desde julio 1](https://unb.com.bd/category/Bangladesh/university-teachers-begin-indefinite-work-abstention-protesting-discriminatory-pension-scheme/138446).
6. [The Daily Star: protesta por pensiones y cierre universitario](https://www.thedailystar.net/news/bangladesh/news/pension-protest-brings-public-univs-halt-3646701).
7. [Chernozhukov, Wüthrich y Zhu: inferencia conformal](https://arxiv.org/pdf/1712.09089).
8. [Gunsilius y Van Dijcke: episodio de Rajasthan](https://arxiv.org/pdf/2309.14630).
9. [Amnistía Internacional: carta del 30 de julio](https://www.amnesty.org/ru/wp-content/uploads/2024/07/ASA1383722024ENGLISH.pdf).
10. [Internet Society Pulse: corte en Bangladesh julio 18](https://pulse.internetsociety.org/en/shutdowns/internet-suspended-in-bangladesh-18-july-2024/).
11. [GH Archive: archivo horario y acceso a datos](https://www.gharchive.org/).
12. [Amnistía Internacional: evidencia publicada julio 17](https://www.amnesty.org/en/latest/news/2024/07/bangladesh-witness-testimony-video-and-photographic-analysis-confirm-police-used-unlawful-force-against-protesters/).

Documentación técnica abierta para la compilación: [TinyTeX](https://yihui.org/tinytex/) y [script oficial de instalación, leído](https://tinytex.yihui.org/install-bin-unix.sh). Se descargó el [runtime oficial Darwin](https://github.com/rstudio/tinytex-releases/releases/download/daily/TinyTeX-1-darwin.tar.xz) y se instaló sólo dentro del directorio de trabajo de esta tarea.
