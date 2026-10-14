# Análisis longitudinal de la dinámica del reconocimiento de investigadores

**Auditoría estadística del sistema de reconocimiento de MinCiencias — objetivo específico 2**  
Documento generado por `documentacion_auditoria/src/generar_analisis_longitudinal.py`. Fecha: 2026-10-14.

> **Estas cifras son del universo, no de una muestra.** La base completa está disponible (77 237 registros, 30 086 personas), así que el análisis longitudinal se hace sobre el **censo**: no hay razón para reportar una estimación cuando se puede reportar el parámetro. El ejercicio de muestreo con el que se trabajó antes se conserva, pero pasa a ser lo que corresponde: una **validación metodológica** (Anexo A) y una comparación de estimadores (Anexo B). La metodología completa está en `metodologia_muestreo.md`.

## 1. Datos y alcance

| Convocatoria | Fecha (`ANO_CONVO`) | Personas | Registros |
|---|---|---:|---:|
| 2013 | 2013-10-31 | 8 016 | 8 016 |
| 2014 | 2014-10-15 | 8 280 | 8 280 |
| 2015 | 2015-10-15 | 10 050 | 10 050 |
| 2017 | 2017-05-12 | 13 001 | 13 001 |
| 2019 | 2019-12-06 | 16 796 | 16 796 |
| 2021 | 2021-02-25 | 21 094 | 21 094 |
| **Total** | — | **30 086** | **77 237** |

La clave `(ID_PERSONA_PR, ID_CONVOCATORIA)` es única: 0 duplicados en los 77 237 registros. Por tanto cada persona aparece **como máximo una vez por convocatoria** y el panel persona × convocatoria es una matriz sin repeticiones. Las convocatorias **no son anuales** (faltan 2016, 2018 y 2020), lo que condiciona cualquier lectura temporal y obliga a medir los intervalos reales en lugar de suponerlos.

## 2. Cifras del universo (censo)

### 2.1 Retención, entradas y salidas

**Retenidos** = presentes en ambas convocatorias · **salidas** = presentes en la primera y no en la segunda · **entradas** = presentes en la segunda y no en la primera. Las tasas de retención y salida se calculan sobre las personas presentes en la primera convocatoria, y la de entrada sobre las de la segunda.

| Par | Años reales | Personas en t₁ | Retenidos | Retención | Salidas | Entradas | Crecimiento neto |
|---|---|---:|---:|---:|---:|---:|---:|
| 2013→2014 | 0,96 | 8 016 | 4 817 | **60,09 %** | 39,91 % | 3 463 | +264 |
| 2014→2015 | 1,00 | 8 280 | 6 857 | **82,81 %** | 17,19 % | 3 193 | +1 770 |
| 2015→2017 | 1,57 | 10 050 | 8 164 | **81,23 %** | 18,77 % | 4 837 | +2 951 |
| 2017→2019 | 2,57 | 13 001 | 9 994 | **76,87 %** | 23,13 % | 6 802 | +3 795 |
| 2019→2021 | 1,22 | 16 796 | 13 355 | **79,51 %** | 20,49 % | 7 739 | +4 298 |

La identidad del panel se cumple en los cinco pares: retenidos + entradas reconstruye exactamente el tamaño de la segunda convocatoria.

### 2.2 Los intervalos de tiempo reales cambian la comparación

Los años nominales sugieren intervalos de 1, 1, 2, 2 y 2 años, pero `ANO_CONVO` contiene fechas y al medirlas los intervalos son otros:

| Par | Intervalo nominal | Intervalo real | Retención observada | Anualizada (nominal) | Anualizada (real) |
|---|---|---|---|---|---|
| 2013→2014 | 1 años | 0,956 años | 60,09 % | 60,09 % | **61,76 %** |
| 2014→2015 | 1 años | 0,999 años | 82,81 % | 82,81 % | **82,83 %** |
| 2015→2017 | 2 años | 1,574 años | 81,23 % | 56,68 % | **65,45 %** |
| 2017→2019 | 2 años | 2,568 años | 76,87 % | 51,91 % | **43,45 %** |
| 2019→2021 | 2 años | 1,224 años | 79,51 % | 54,74 % | **72,62 %** |

La causa principal es un dato ya documentado en el repositorio auditado: la convocatoria rotulada **«833 de 2018» está fechada el 06/12/2019**. Por eso el hueco 2017→2019 dura 2,57 años y 2019→2021 solo 1,22. La consecuencia no es cosmética: **invierte el orden de los pares**. Con años nominales, 2017→2019 (51,91 %) y 2019→2021 (54,74 %) parecen igual de malos; con los intervalos reales, 2017→2019 es el peor (43,45 %) y 2019→2021 el segundo mejor (72,62 %).

### 2.3 Retención global 2013→2021

De las 8 016 personas reconocidas en 2013, 4 503.0 seguían reconocidas en 2021: **56,18 %**. La estructura de permanencia a lo largo de todo el período es muy desigual:

| N.º de convocatorias en que aparece | Personas | Porcentaje |
|---|---:|---:|
| 1 | 10 871 | 36,1 % |
| 2 | 7 139 | 23,7 % |
| 3 | 4 157 | 13,8 % |
| 4 | 2 720 | 9,0 % |
| 5 | 2 457 | 8,2 % |
| 6 | 2 742 | 9,1 % |

El **36,1 %** de las personas aparece en una sola convocatoria y nunca vuelve; en el extremo opuesto, 2 742 personas (9,1 %) están reconocidas en las seis.

### 2.4 Transiciones de categoría

Filas: categoría en la primera convocatoria del par. Columnas: categoría en la segunda. Cada celda muestra el número de personas y el porcentaje sobre el total de la fila. El orden jerárquico es Junior (12) < Asociado (13) < Sénior (14) < Emérito (15), según `ORDEN_CLAS_PR`.

**2013→2014** — 4 817 personas con categoría en ambas convocatorias; permanecen 3 485 (72,35 %), ascienden 953, descienden 379.

| Categoría en t₁ ↓ / t₂ → | Junior | Asociado | Sénior | Emérito | Total |
|---|---|---|---|---|---|
| Junior | 1967 (73,5 %) | 557 (20,8 %) | 152 (5,7 %) | 0 (0,0 %) | 2 676 |
| Asociado | 349 (23,0 %) | 927 (61,0 %) | 244 (16,1 %) | 0 (0,0 %) | 1 520 |
| Sénior | 10 (1,6 %) | 20 (3,2 %) | 591 (95,2 %) | 0 (0,0 %) | 621 |
| Emérito | 0 | 0 | 0 | 0 | 0 |
| **Total** | 2 326 | 1 504 | 987 | 0 | 4 817 |

**2014→2015** — 6 857 personas con categoría en ambas convocatorias; permanecen 5 620 (81,96 %), ascienden 945, descienden 292.

| Categoría en t₁ ↓ / t₂ → | Junior | Asociado | Sénior | Emérito | Total |
|---|---|---|---|---|---|
| Junior | 3420 (83,2 %) | 598 (14,5 %) | 87 (2,1 %) | 7 (0,2 %) | 4 112 |
| Asociado | 191 (10,7 %) | 1392 (77,9 %) | 199 (11,1 %) | 6 (0,3 %) | 1 788 |
| Sénior | 20 (2,1 %) | 81 (8,5 %) | 808 (84,4 %) | 48 (5,0 %) | 957 |
| Emérito | 0 | 0 | 0 | 0 | 0 |
| **Total** | 3 631 | 2 071 | 1 094 | 61 | 6 857 |

**2015→2017** — 8 164 personas con categoría en ambas convocatorias; permanecen 6 366 (77,98 %), ascienden 1 447, descienden 351.

| Categoría en t₁ ↓ / t₂ → | Junior | Asociado | Sénior | Emérito | Total |
|---|---|---|---|---|---|
| Junior | 3600 (77,8 %) | 885 (19,1 %) | 129 (2,8 %) | 12 (0,3 %) | 4 626 |
| Asociado | 301 (12,4 %) | 1737 (71,6 %) | 367 (15,1 %) | 22 (0,9 %) | 2 427 |
| Sénior | 12 (1,1 %) | 38 (3,4 %) | 1029 (92,6 %) | 32 (2,9 %) | 1 111 |
| Emérito | 0 | 0 | 0 | 0 | 0 |
| **Total** | 3 913 | 2 660 | 1 525 | 66 | 8 164 |

**2017→2019** — 9 994 personas con categoría en ambas convocatorias; permanecen 7 018 (70,22 %), ascienden 2 246, descienden 730.

| Categoría en t₁ ↓ / t₂ → | Junior | Asociado | Sénior | Emérito | Total |
|---|---|---|---|---|---|
| Junior | 3797 (72,0 %) | 1283 (24,3 %) | 192 (3,6 %) | 3 (0,1 %) | 5 275 |
| Asociado | 558 (18,1 %) | 1793 (58,0 %) | 726 (23,5 %) | 13 (0,4 %) | 3 090 |
| Sénior | 81 (5,0 %) | 91 (5,6 %) | 1428 (87,7 %) | 29 (1,8 %) | 1 629 |
| Emérito | 0 | 0 | 0 | 0 | 0 |
| **Total** | 4 436 | 3 167 | 2 346 | 45 | 9 994 |

**2019→2021** — 13 355 personas con categoría en ambas convocatorias; permanecen 9 657 (72,31 %), ascienden 2 336, descienden 1 362.

| Categoría en t₁ ↓ / t₂ → | Junior | Asociado | Sénior | Emérito | Total |
|---|---|---|---|---|---|
| Junior | 5558 (77,9 %) | 1276 (17,9 %) | 291 (4,1 %) | 7 (0,1 %) | 7 132 |
| Asociado | 960 (24,9 %) | 2171 (56,4 %) | 701 (18,2 %) | 16 (0,4 %) | 3 848 |
| Sénior | 88 (3,7 %) | 314 (13,2 %) | 1928 (81,2 %) | 45 (1,9 %) | 2 375 |
| Emérito | 0 | 0 | 0 | 0 | 0 |
| **Total** | 6 606 | 3 761 | 2 920 | 68 | 13 355 |

Las transiciones dominantes son de ascenso: Junior→Asociado es el flujo más numeroso en todos los pares. Pero el descenso existe y no es marginal: en 2019→2021 bajaron de categoría 1 362 personas, el 10,20 % de las trayectorias observadas. La categoría no es un derecho adquirido.

### 2.5 «Emérito» es un estado absorbente

De las 251 personas clasificadas como Investigador Emérito en 2015, 2017 o 2019, **ninguna** vuelve a aparecer en una convocatoria posterior: 0 retornos sobre 251 oportunidades. La categoría no existe en 2013 ni en 2014 y aparece por primera vez en 2015.

Dos consecuencias. En lo descriptivo, la fila «Emérito» de toda matriz de transición es estructuralmente cero. En lo analítico, cualquier cadena de Markov ajustada a estas transiciones tendrá en Emérito un **estado absorbente**, y la retención de los Eméritos no es un caso de baja retención sino una regla del sistema. Lo que el dato **no** permite determinar es la causa: podría ser que el reconocimiento no se renueve, que se otorgue una sola vez, o que quienes lo reciben dejen de postularse.

### 2.6 Entradas y salidas en sentido estricto

La definición habitual de «entrada» mezcla dos poblaciones distintas: quien nunca había sido reconocido y quien ya lo fue, faltó a la convocatoria intermedia y volvió. Separarlas cambia la lectura del crecimiento:

| Par | Entradas | Entradas nuevas reales | Reingresos | Reingresos/entradas | Salidas | Salidas temporales | Salidas definitivas |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2013→2014 | 3 463 | 3 463 | 0 | 0,0 % | 3 199 | 1 508 | 1 691 |
| 2014→2015 | 3 193 | 2 574 | 619 | 19,4 % | 1 423 | 838 | 585 |
| 2015→2017 | 4 837 | 3 893 | 944 | 19,5 % | 1 886 | 738 | 1 148 |
| 2017→2019 | 6 802 | 5 850 | 952 | 14,0 % | 3 007 | 880 | 2 127 |
| 2019→2021 | 7 739 | 6 290 | 1 449 | 18,7 % | 3 441 | 0 | 3 441 |

Entre el 0 % y el 20 % de las entradas son **reingresos**. Y en el otro sentido, buena parte de las salidas no son definitivas: en 2013→2014, 1 508 de las 3 199 salidas (47,14 %) corresponden a personas que reaparecen después. Tratar cada ausencia como una baja definitiva infla la rotación aparente del padrón. La última fila está **censurada a la derecha**: en 2019→2021 no hay convocatorias posteriores.

### 2.7 Desagregaciones (censo)

Tasas de retención por par. Se calculan sobre el universo, no sobre la muestra.

**Categoría**

| Grupo | 2013→2014 | 2014→2015 | 2015→2017 | 2017→2019 | 2019→2021 |
|---|---|---|---|---|---|
| Investigador Asociado | 83,42 % | 86,63 % | 87,97 % | 85,95 % | 88,48 % |
| Investigador Junior | 48,66 % | 79,71 % | 76,45 % | 69,64 % | 71,89 % |
| Investigador Sénior | 89,35 % | 90,54 % | 95,28 % | 95,43 % | 96,04 % |

**Gran área de conocimiento**

| Grupo | 2013→2014 | 2014→2015 | 2015→2017 | 2017→2019 | 2019→2021 |
|---|---|---|---|---|---|
| Ciencias Agrícolas | 61,50 % | 84,15 % | 82,49 % | 74,84 % | 77,09 % |
| Ciencias Médicas y de la Salud | 74,22 % | 84,66 % | 84,10 % | 77,64 % | 83,64 % |
| Ciencias Naturales | 67,88 % | 86,34 % | 81,63 % | 78,51 % | 82,34 % |
| Ciencias Sociales | 50,54 % | 78,45 % | 77,27 % | 74,82 % | 75,17 % |
| Humanidades | 41,57 % | 74,33 % | 76,47 % | 72,01 % | 70,19 % |
| Ingeniería y Tecnología | 71,58 % | 85,51 % | 84,95 % | 79,59 % | 84,42 % |
| No registra | 45,61 % | 60,68 % | — | — | 67,62 % |

**Género**

| Grupo | 2013→2014 | 2014→2015 | 2015→2017 | 2017→2019 | 2019→2021 |
|---|---|---|---|---|---|
| Femenino | 58,17 % | 81,25 % | 80,00 % | 75,22 % | 77,79 % |
| Masculino | 61,08 % | 83,67 % | 81,91 % | 77,86 % | 80,58 % |

Las tres tablas cuentan la misma historia que el EDA: la **categoría** separa comportamientos (los Junior retienen bastante menos que los Sénior), la **gran área** separa algo (Ingeniería y Ciencias Médicas por encima de Sociales y Humanidades) y el **género** apenas separa.

### 2.8 Calidad del registro que revela el panel

- **Sin duplicados**: 0 repeticiones de la clave persona × convocatoria.
- **Género contradictorio**: 42 personas (0,14 % del padrón) figuran con más de un género a lo largo del tiempo —Masculino→Femenino (30), Femenino→Masculino (7), Femenino→Intersexual (2), Masculino→Intersexual (2), Masculino→No disponible (1). El género no es un atributo estable en este registro.
- **Atributos que cambian dentro de la misma persona**: 42 en genero, 1 203 en departamento_res, 1 389 en gran_area, 3 844 en niv_form, 8 755 en clasificacion. Obliga a declarar qué observación se usa en cada análisis.
- **Edades imposibles**: 11 personas declaran más de 100 años (máximo 956,25). Es un problema de captura, no de la población.
- **Faltantes**: 4 de 30 columnas tienen vacíos, concentrados en `INST_FILIA` y los códigos DANE; ninguna es variable del análisis longitudinal.

## 3. Conclusiones

1. **La retención es alta en cada intervalo, pero acumulada pierde casi la mitad del padrón.** Entre convocatorias consecutivas se retiene entre 60,09 % y 82,81 %, pero de quienes entraron en 2013 solo el 56,18 % seguía en 2021.
2. **Anualizar con las fechas reales invierte el diagnóstico.** El hueco 2017→2019 dura 2,57 años y el 2019→2021 solo 1,22; con años nominales ambos parecen equivalentes, con las fechas reales 2017→2019 es el peor par y 2019→2021 el segundo mejor.
3. **La movilidad es ascendente y masiva, y el descenso también existe.** En 2019→2021, de 13 355 trayectorias 2 336 ascendieron y 1 362 descendieron.
4. **«Emérito» funciona como estado terminal: 0 retornos de 251.** Debe incorporarse como supuesto explícito en cualquier modelo de transición.
5. **La rotación aparente está inflada.** Entre el 14 % y el 20 % de las entradas son reingresos, y hasta el 47,14 % de las salidas de 2013→2014 corresponden a personas que reaparecen.

## 4. Limitaciones

1. **Las convocatorias no son anuales**: faltan 2016, 2018 y 2020, y los intervalos reales van de 1,0 a 2,6 años. Las tasas anualizadas suponen riesgo constante dentro del intervalo y con seis puntos de observación ese supuesto no puede contrastarse. El análisis es descriptivo: no se ajustó ningún modelo de supervivencia.
2. **Qué significa `ANO_CONVO` no está documentado.** Se midió el intervalo con esas fechas, el único dato temporal del archivo, pero la discrepancia entre el rótulo «833 de 2018» y la fecha 06/12/2019 no se resuelve con lo disponible.
3. **Observación solo en las fechas de convocatoria.** Una persona ausente en una convocatoria y presente en la siguiente es indistinguible de alguien que nunca fue reconocido, salvo por el historial previo; por eso se separan reingresos y salidas temporales, pero no se observa lo que ocurre entre convocatorias.
4. **Censura a la derecha en el último par.** En 2019→2021 las 3 441 salidas no pueden clasificarse en temporales y definitivas. Lo mismo afecta a la condición terminal de Emérito.
5. **Atributos no constantes.** El perfil de cada persona se toma de su última convocatoria observada, y el género cambia en 42 personas.
6. **Datos atípicos de edad** sin corregir: se reportan 11 casos por encima de 100 años; el análisis de edad describe el registro tal como está.

## 5. Referencias

- Cochran, W. G. (1977). *Sampling Techniques* (3rd ed.). John Wiley & Sons.
- Lohr, S. L. (2010). *Sampling: Design and Analysis* (2nd ed.). Brooks/Cole.
- Särndal, C.-E., Swensson, B., & Wretman, J. (1992). *Model Assisted Survey Sampling*. Springer-Verlag.
- Kalton, G. (2002). Models in the practice of survey sampling. *International Statistical Review*, 70(2), 175-192.
- Departamento Administrativo de Ciencia, Tecnología e Innovación (MinCiencias). *Investigadores reconocidos por convocatoria* [conjunto de datos, `bqtm-4y2h`]. datos.gov.co. Consulta: 2026-10-06.

---

## Anexo A — Validación del muestreo (MAS)

Este anexo documenta el ejercicio de muestreo. **No es la fuente de las cifras de este documento**: sirve para (i) mostrar que el diseño elegido es defendible, y (ii) verificar los estimadores contra el censo, que es una oportunidad poco habitual y aquí se aprovecha.

### A.1 Diseño y tamaño de muestra

Muestreo aleatorio simple **de personas** (no de registros), sin reemplazo, con semilla 2026. Marco: 30 086 personas. Fórmula de Cochran (1977) con corrección por población finita:

| Parámetro | Valor |
|---|---:|
| Confianza `Z` | 2,0 |
| Proporción `p` (varianza máxima) | 0,5 |
| Margen `e` | 0,0 |
| `n₀` sin corregir | 2 401 |
| `n` ajustado (exacto) | 2223,62 |
| **`n` final** | **2 224** |
| Fracción de muestreo | 7,4 % |
| Error efectivo (con corrección) | 2,0 pp |

El panel muestral recupera **todos** los registros de esas personas en todas las convocatorias: 5 806 registros. La justificación de elegir MAS y no un diseño estratificado, y de por qué «MAS o regresión» es un falso dilema, está desarrollada en `metodologia_muestreo.md` §3, a la luz del EDA.

### A.2 Verificación de representatividad

Perfil de cada persona en su última convocatoria observada. Contraste de bondad de ajuste de la muestra contra las proporciones del universo:

| Eje | χ² | gl | p | Diferencia absoluta máxima |
|---|---:|---:|---:|---:|
| Género | 3,128 | 3 | 0,372 | 1,6 pp |
| Categoría | 9,473 | 3 | 0,024 | 1,9 pp |
| Gran área | 5,145 | 6 | 0,525 | 1,0 pp |
| Departamento | 43,473 | 34 | 0,128 | 1,2 pp |
| Nivel de formación | 10,473 | 9 | 0,314 | 1,0 pp |

Cuatro de los cinco ejes tienen p > 0,05. El único que baja de ese umbral es la categoría; con cinco contrastes simultáneos el umbral de Bonferroni es 0,01 y ese p-valor no lo alcanza, y la mayor discrepancia observada en categoría queda dentro del margen de diseño de ±2 pp. Conviene decirlo con precisión: en un MAS la representatividad **está garantizada por el diseño** en esperanza; estos χ² son una comprobación de la implementación, no evidencia de representatividad. La limitación real es que dos categorías de género del universo (Intersexual, 5 personas, y No disponible, 4) no quedan representadas en la muestra.

### A.3 Contraste muestra vs censo

| Par | Estimación muestral | IC 95 % | Valor censal | Diferencia | ¿Censal dentro del IC? |
|---|---|---|---|---|:--:|
| Retención 2013→2014 | 61,17 % | [57,32; 65,01] | 60,09 % | 1,07 pp | sí |
| Retención 2014→2015 | 82,66 % | [79,72; 85,59] | 82,81 % | -0,16 pp | sí |
| Retención 2015→2017 | 80,74 % | [77,93; 83,56] | 81,23 % | -0,49 pp | sí |
| Retención 2017→2019 | 76,50 % | [73,85; 79,15] | 76,87 % | -0,37 pp | sí |
| Retención 2019→2021 | 80,21 % | [78,00; 82,41] | 79,51 % | 0,69 pp | sí |
| Retención global 2013→2021 | 56,63 % | [52,73; 60,54] | 56,18 % | 0,46 pp | sí |

Las seis estimaciones quedan dentro de ±1,1 pp del valor censal y el valor censal cae dentro del intervalo en los seis casos. **El diseño funciona**: el estimador reproduce el parámetro. Esto no es un argumento para usar la muestra —el censo es mejor— sino la comprobación de que si alguna vez hubiera que estimar, el método sería fiable.

### A.4 Retención muestral con intervalos de confianza

| Par | n en t₁ | Retenidos | Retención | IC 95 % (Wald) | IC 95 % (Wilson) | IC 95 % (con fpc) |
|---|---:|---:|---|---|---|---|
| 2013→2014 | 618 | 378 | 61,17 % | [57,32; 65,01] | [57,26; 64,93] | [57,36; 64,97] |
| 2014→2015 | 640 | 529 | 82,66 % | [79,72; 85,59] | [79,53; 85,39] | [79,75; 85,56] |
| 2015→2017 | 753 | 608 | 80,74 % | [77,93; 83,56] | [77,77; 83,40] | [77,96; 83,52] |
| 2017→2019 | 983 | 752 | 76,50 % | [73,85; 79,15] | [73,75; 79,04] | [73,89; 79,11] |
| 2019→2021 | 1 258 | 1 009 | 80,21 % | [78,00; 82,41] | [77,91; 82,32] | [78,05; 82,36] |

Se reportan los tres intervalos porque el intervalo de Wald es el habitual pero se degrada cerca de 0 y 1: la discrepancia máxima entre los tres, en cualquier par y cualquier extremo, es inferior a 0,2 pp, de modo que la elección no altera ninguna conclusión.

### A.5 Transiciones en la muestra

Las matrices del censo están en §2.4. Las de la muestra (necesarias para las desagregaciones por subgrupo, donde no siempre hay masa crítica en el censo) coinciden en las tasas de permanencia:

| Par | Permanencia (muestra) | Permanencia (censo) | Diferencia |
|---|---|---:|---:|
| 2013→2014 | 73,28 % | 72,35 % | 0,93 pp |
| 2014→2015 | 83,36 % | 81,96 % | 1,40 pp |
| 2015→2017 | 78,45 % | 77,98 % | 0,48 pp |
| 2017→2019 | 73,67 % | 70,22 % | 3,45 pp |
| 2019→2021 | 72,35 % | 72,31 % | 0,04 pp |

### A.6 Desagregaciones por subgrupo

Cuando el subgrupo es pequeño, el censo no siempre ofrece celdas con masa suficiente para un contraste; la muestra de 2 224 personas tampoco. Se reportan las del censo (§2.7) y, para los contrastes de homogeneidad, los del par 2019→2021:

| Eje | χ² | gl | p | Frecuencia esperada mínima | ¿Supuesto satisfecho? |
|---|---:|---:|---:|---:|:--:|
| Género | 2,143 | 1 | 0,1432 | 90,06 | sí |
| Departamento | 14,705 | 4 | 0,0054 | 15,80 | sí |
| Gran área | 14,964 | 6 | 0,0205 | 1,19 | **no** |
| Nivel de formación | 2,854 | 5 | 0,7225 | 3,96 | **no** |

Estos contrastes se calculan sobre la muestra, así que sus p-valores son orientativos; el EDA ya estableció con el censo la magnitud de las diferencias (Anexo §2.2 de `metodologia_muestreo.md`), que es de alrededor del 7 % de la varianza para la categoría y menos del 1,4 % para el resto.

---

## Anexo B — Post-estratificación y GREG

Comparación de los tres estimadores frente al valor censal. El desarrollo conceptual, los modelos y las referencias están en `metodologia_muestreo.md` (§4-§8), incluidos los diagnósticos de supuestos (normalidad, heterocedasticidad y g-weights); aquí se resume el resultado.

| Parámetro | Censo | MAS | Post-estratificado | GREG |
|---|---:|---:|---:|---:|
| Retención 2013→2014 | 60,09 % | 61,17 % | 62,19 % | 61,80 % |
| Retención 2014→2015 | 82,81 % | 82,66 % | 82,66 % | 82,76 % |
| Retención 2015→2017 | 81,23 % | 80,74 % | 80,09 % | 80,53 % |
| Retención 2017→2019 | 76,87 % | 76,50 % | 76,44 % | 76,59 % |
| Retención 2019→2021 | 79,51 % | 80,21 % | 80,35 % | 80,35 % |
| Retención 2013→2021 | 56,18 % | 56,63 % | 57,31 % | 57,14 % |
| Edad media | 45,519 | 45,144 | 45,240 | 45,153 |
| Ascenso 2019→2021 | 17,49 % | 18,73 % | 18,34 % | 18,37 % |

**Ganancia de precisión** (reducción de varianza respecto al MAS):

| Parámetro | Post-estratificado | GREG |
|---|---:|---:|
| Retención 2013→2014 | 16,6 % | 20,1 % |
| Retención 2014→2015 | 0,6 % | 5,9 % |
| Retención 2015→2017 | 4,8 % | 9,3 % |
| Retención 2017→2019 | 8,1 % | 9,1 % |
| Retención 2019→2021 | 7,1 % | 8,5 % |
| Retención 2013→2021 | 6,4 % | 17,5 % |
| Edad media | 5,0 % | 3,5 % |
| Ascenso 2019→2021 | 9,4 % | 7,3 % |

**Lectura.** El MAS es el más cercano al censo en 5 de los 6 pares, es decir que la muestra ya estaba equilibrada y la post-estratificación no corrige sesgo: **compra precisión** (hasta 16,6 % menos varianza). El GREG domina en varianza (hasta 20,1 %) y además su validez no depende de que el modelo esté bien especificado, que es la propiedad *model-assisted*. Se comprobó además que la post-estratificación es un caso particular de GREG: con un modelo saturado en los post-estratos ambos coinciden exactamente (diferencia 1.1e-16 pp).

**Conclusión del anexo:** si hubiera que estimar en lugar de censar, el orden de preferencia es GREG > post-estratificado > MAS en términos de varianza, y el MAS es el que menos supuestos exige. La post-estratificación de 4 estratos incumple la condición de tamaño mínimo de Cochran (1977) en los pares donde Emérito tiene menos de 20 casos, por lo que se reporta también la versión colapsada (Sénior + Emérito).

---

## Anexo C — Archivos y reproducibilidad

| Archivo | Contenido |
|---|---|
| `src/analisis_longitudinal.py` | Muestreo, panel y análisis longitudinal (censo y muestra) |
| `src/eda_longitudinal.py` | EDA previo (Parte 1 de la metodología) |
| `src/estimadores_longitudinal.py` | Post-estratificación y GREG |
| `src/generar_analisis_longitudinal.py` | Genera este documento |
| `metodologia_muestreo.md` | Documento metodológico completo |
| `data/memoria/longitudinal_resultados.json` | Cifras del análisis |
| `data/memoria/eda_resultados.json` | Cifras del EDA |
| `data/memoria/eda/` | 6 gráficas del EDA |
| `data/memoria/estimadores_resultados.json` | Cifras de los estimadores |
| `data/memoria/muestra_ids.csv` | 2 224 identificadores (semilla 2026) |

```bash
python src/analisis_longitudinal.py
python src/eda_longitudinal.py
python src/estimadores_longitudinal.py
python src/generar_analisis_longitudinal.py
python src/generar_metodologia_muestreo.py
```

