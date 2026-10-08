# Decisiones para el asesor — ronda 2

Fecha: 2026-10-08. Ninguna opción de este documento autoriza cambiar la especificación principal, la muestra, los donantes o la ventana. Los diagnósticos están separados en results/diagnostics/round2. El resultado principal sigue siendo -13.255939 pp (-86.769280%), julio 18–23, 14 donantes y 10.241 cuentas de Bangladesh. La selección de opciones debe basarse en diseño y medición, nunca en resultados más fuertes.

## M6 — RDiT

Se conservaron el resultado original (-9.2836 pp, SE HAC 5.0344, corte julio 17, h=7), las 45 combinaciones de corte julio 17/18/19 × h=4/5/7/10/14 × Bangladesh/gap con Filipinas/placebo filipino y la grilla histórica de 16 filas. La grilla comparable de Bangladesh va de -4.4457 a -19.5230 pp. La fila histórica lineal h=7 sin donut es -14.0 pp; su muestra/corte/outcome/cálculo de SE no están documentados y no se equipara al resultado reproducido. Hay 174 cuentas del RDiT fuera del SCM y 86 del SCM fuera del RDiT.

Opciones: (1) conservar como diagnóstico descriptivo diario con todas las limitaciones; (2) sustituir, tras aprobación y disponibilidad de datos, por un análisis horario en torno a las 15:00 UTC del 18 de julio; (3) retirar el RDiT como evidencia causal. Recomiendo (2) si se recuperan eventos por hora y una definición verificable del outcome; en caso contrario, (3). Por ahora no se eliminó ni seleccionó ninguna especificación. El 17 se conserva por trazabilidad histórica: no coincide con el inicio del corte nacional, aunque ya existían cortes móviles por proveedor la noche anterior UTC.

## M2 — quiebre de julio y cohorte tardía

La Tabla 3 del informe se reproduce con el mismo outcome, donantes y tratamiento:

| Ajuste | ATT pp | Contrafactual % | Cambio relativo % | Gap julio 1–17 pp | Gap agosto 14–27 pp |
|---|---:|---:|---:|---:|---:|
| Mayo 1–julio 17 (original) | -13.2559 | 15.2772 | -86.7693 | 4.8241 | 4.4566 |
| Mayo 1–junio 30 | -11.3174 | 13.3387 | -84.8465 | 6.8382 | 6.1331 |
| Junio 20–julio 17 | -14.7037 | 16.7249 | -87.9145 | 3.1068 | 4.0790 |
| Julio 1–17 | -15.5732 | 17.5945 | -88.5118 | 2.4678 | 3.5270 |

La definición del informe (primera actividad productiva observada desde junio 29, sin límite superior) identifica 891 cuentas, 8.70% del grupo. Dos tienen primera actividad productiva después de julio 17; restringir el inicio al preperíodo da 889. No son necesariamente cuentas recién creadas: createdAt no está en los JSON locales, que sólo contienen logins, ni en los paneles. Se preparó `analysis/pending/m2_accounts.graphql` para consultar creación y organizaciones públicas; no se ejecutó. Las membresías actuales no probarían membresía en 2024.

Hay PushEvents pre-julio-18 para 879 cuentas de esa cohorte. Los nombres base compartidos incluyen assignment-1 (126 cuentas), web-dev-portfolio (112), my-first-github-repo (71), g3-architects-website (67). Ningún repositorio completo ni propietario de repositorio es compartido por más de una de estas cuentas en este extracto. Esto es compatible con ejercicios comunes, pero no identifica un curso, organización ni bootcamp. El salto julio 1→2 es 1.958→2.610 cuentas activas (+652), del que la cohorte tardía aporta +320; no se equipara a la comparación media +440/+1.035 del informe, cuya ventana de contraste no está especificada. Agosto 14–septiembre 3: tasa tardía 28.1546%, anterior 15.1337%.

Diagnóstico de elegibilidad independiente del ajuste: exigir cuatro días con cualquier evento en mayo y ajustar junio 1–julio 17 (conservar las exclusiones archivadas de bots). Bangladesh pasa de 10.241 a 5.140 cuentas. ATT original completo -13.2559 pp; misma muestra con ajuste desde junio -13.3205; muestra fijada en mayo con ajuste desde junio -16.0099 (-89.4717%). Se muestran los tres, sin adoptar el más negativo. Fijar elegibilidad antes de mayo manteniendo el ajuste original requiere datos enero–abril para todos los donantes; la consulta exacta queda en `analysis/pending/m2_before_may_eligibility.sql`.

Fuentes abiertas documentan huelga universitaria desde julio 1 y movilización por cuotas en esa fecha. No demuestran que causaran el aumento de GitHub:
- https://unb.com.bd/category/Bangladesh/university-teachers-begin-indefinite-work-abstention-protesting-discriminatory-pension-scheme/138446
- https://www.thedailystar.net/news/bangladesh/news/pension-protest-brings-public-univs-halt-3646701

Recomiendo recuperar createdAt, membresías históricas si existen y datos de elegibilidad anteriores a mayo; mantener entretanto la tabla completa de sensibilidad. La elección de ventana debe justificarse por estabilidad y separación entre selección y estimación, no por magnitud o significación. No adopto ningún cambio de muestra ni de ajuste.

## M4 — donantes, calendario e inferencia

**Regla propuesta antes de ver nuevos outcomes:** enumerar todos los países de una lista global congelada de ubicaciones GitHub; requerir ≥1.000 cuentas elegibles con ≥4 días de cualquier evento antes de mayo, aplicar un filtro de bots documentado y exigir cobertura suficiente de fuentes externas de conectividad. Excluir cortes documentados con descenso nacional ≥20% durante ≥1 hora en mayo 1–septiembre 4 si se quiere interpretar también recuperación. No seleccionar por correlación post, signo, significación o peso estimado. Registrar también países sin cobertura como no evaluados. Esta regla deliberadamente podría quitar Pakistán por julio 31; no se adopta en el paper.

El prototipo con la elegibilidad archivada (que NO es la ventana pre-mayo propuesta) deja fuera a Jordania, 446, por tamaño; Ghana, 1.373, supera el umbral. Los otros 13 donantes actuales superan el umbral de tamaño, pero falta su revisión completa de conectividad. No hay cuentas ni conteos de países adicionales en los datos locales: no se puede afirmar qué países se añadirían. La consulta exacta `analysis/pending/m4_candidate_universe.sql` devuelve los países que pasarían el primer filtro, una vez aportada la lista global congelada. Este subpedido está bloqueado por datos externos, no resuelto inventando candidatos aptos.

El ajuste de efectos de día de semana específicos de país, estimados sólo en los 78 días pre, produce ATT -14.023087 pp frente al original -13.255939. Bangladesh tiene fin de semana viernes–sábado; se modelan los siete días, sin imponer sábado–domingo a todos los países. `m4_referee_weekdays.csv` reproduce la comparación mayo–junio sin feriados de Bangladesh. No se cambia la serie principal.

DiD como diferencia de medias en exactamente los mismos datos:

| Variante | BD pre | BD cierre | Media donantes pre | Media donantes cierre | DiD pp |
|---|---:|---:|---:|---:|---:|
| Todos los días | 17.254550 | 2.021287 | 15.919824 | 13.774063 | -13.087502 |
| Sin feriados | 17.583364 | 2.021287 | 16.050254 | 13.867275 | -13.379098 |

**Prototipo conformal CWZ:** 78 días pre + 6 de tratamiento. Para cada trayectoria nula constante tau, imputar Y−tau en tratamiento, reestimar pesos sobre los 84 días bajo esa nula, obtener residuos y calcular S1 con las 84 rotaciones circulares, incluida identidad. La grilla tau=-25…5 pp, paso 0,25, acepta -19 a -6,5 al 5%; para la nula cero p=1/84=0,011905. Es un conjunto para trayectorias constantes, no un intervalo general para el ATT. El código no reutiliza residuos ajustados sólo en pre como si eso fuera conformal exacto. Fuente metodológica abierta: https://arxiv.org/pdf/1712.09089.

**Advertencia de diseño, no resultado adoptado:** la validez temporal depende de estabilidad y dependencia de los residuos; autocorrelación pre de orden 1=0,674; gap medio mayo–junio=0,095 pp frente a julio=4,824 pp. El quiebre de julio cuestiona la calibración. El p=0,0119 NO reemplaza el rango entre países 1/15=0,0667 ni justifica una nueva afirmación de significación. Recomiendo resolver M2 y ampliar donantes con regla documentada antes de adoptar inferencia temporal; mostrar ajuste de calendario y diferencia de medias como diagnósticos. Las cuatro referencias M4 siguen en notes/pending_literature_M4.md, sin introducir una metodología no aprobada en el manuscrito.

## M3 — cronología y análisis horario

Cronología con fuentes y episodios comparables: notes/round2_M3_chronology.md. El corte total alrededor de 15:00 UTC julio 18 precede al toque de queda nacional de la noche julio 19–20 local; las protestas y cortes parciales ya habían comenzado. Restauración fija desde 13:00 UTC julio 23; móvil desde 09:00 UTC julio 28. Esa secuencia ayuda a describir mecanismos, pero no elimina simultaneidad ni selección de quién recupera conexión primero.

Diagnóstico horario disponible: PushEvents de Bangladesh, no el outcome principal sin definición recuperada. Se conservan las 10.241 cuentas como denominador, con 7.750 actores observados; 182.808 filas contienen 182.807 eventos únicos (una duplicación exacta eliminada sólo del diagnóstico). Se reportan todos los anchos de 6/12/24 horas y un gráfico, con referencia al mismo día/hora de la semana de julio 1–17.

| Cambio | Usuarios activos por hora, 12 h antes | 12 h después |
|---|---:|---:|
| Corte total julio 18, 15:00 UTC | 130.00 | 2.42 |
| Restauración fija julio 23, 13:00 UTC | 1.25 | 8.67 |
| Restauración móvil julio 28, 09:00 UTC | 67.92 | 139.50 |

Estas medias no son efectos causales ajustados: cambian también la hora del día y la población con acceso. Opciones: mantener el estimando de episodio con esta limitación, o reconstruir outcome y controles horarios y diseñar una comparación entre episodios. Recomiendo la segunda para separar conectividad y conflicto; no sustituir ahora la estimación principal con la serie de pushes. Pendiente `analysis/pending/m3_hourly_all_events.sql`, con eventos de donantes y países comparables ausentes localmente.

Candidatos con fuentes abiertas: Rajasthan septiembre 26, 2021 (cierre por examen en Gunsilius–Van Dijcke, no protesta como motivo); Venezuela tras julio 28, 2024 (protestas sin corte nacional según Cloudflare, aunque con bloqueo de sitios). No se les atribuyen efectos GitHub inexistentes ni se los añade a los donantes. Hacen falta cohortes geográficas verificables y eventos horarios comparables, y aprobación para incorporar otro diseño.

## M7 — lugar del análisis sectorial

**Opción A (recomendada ahora):** trasladar a un apéndice descriptivo la sección sectorial y sus tablas, dejando una síntesis breve que no prometa recuperación causal por industria. Justificación: clasificación de repositorios, no empleadores; falta control externo; reasignación a proyectos nuevos; selección en actividad previa; sectores con pocos usuarios y concentración. El diagnóstico nacional M8 y los niveles M1 dan una contribución más directamente vinculada a las observaciones.

**Opción B:** sustituir el bloque principal por heterogeneidad fijada antes del cierre. Protocolo propuesto, sin estimar ni seleccionar cortes por resultados: grupos de días activos pre (4–9, 10–29, ≥30), experiencia en GitHub por createdAt si se recupera, actividad colaborativa previa, y uso previo de varios repositorios. Definir grupos sobre un período anterior al ajuste, usar las mismas reglas por país y conservar tasas con denominador fijo e intervalos que reconozcan el nivel de asignación. Priorizar pocas interacciones predefinidas; reportar todas, sin elegir subgrupos por caídas mayores. Edad de cuenta e historial previo a mayo están pendientes según M2; no usar sectores inferidos después del cierre como rasgos previos.

**Opción C:** conservar la sección principal, pero reducir su papel a descripción de repositorios. Es viable editorialmente, pero deja una contribución central más débil y no resuelve la comparabilidad de cohortes.

No se movieron secciones, no se reemplazó la muestra y no se calcularon nuevos resultados sectoriales para adoptar una opción. La decisión A/B/C queda para el asesor. Los resultados originales, incluidas las sensibilidades existentes de umbral y repositorios fijos, permanecen intactos.
