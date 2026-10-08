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
