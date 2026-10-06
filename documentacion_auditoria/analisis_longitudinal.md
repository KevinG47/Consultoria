# Análisis longitudinal de la dinámica del reconocimiento de investigadores

**Auditoría estadística del sistema de reconocimiento de MinCiencias — objetivo específico 2**  
Documento generado por `documentacion_auditoria/src/generar_analisis_longitudinal.py` a partir de `data/memoria/longitudinal_resultados.json` (cifras verificadas de forma independiente). Fecha de generación: 2026-10-06.

**Fuente de datos.** `Datos/Investigadores_Reconocidos_por_convocatoria_20261006.csv` (datos.gov.co, dataset `bqtm-4y2h`): 77 237 registros, 30 086 personas únicas, 6 convocatorias entre 2013 y 2021. El archivo de entrada no se modificó.

**Diseño.** Muestreo aleatorio simple de **personas** (no de registros), n = 2 224, semilla 2026. Para cada persona seleccionada se recuperaron **todos** sus registros en **todas** las convocatorias (5 806 registros en total), de modo que cada trayectoria individual queda completa.

## 1. Metodología del muestreo

### 1.1 Unidad de muestreo y marco muestral

La unidad de muestreo es **el investigador**, no el registro. El marco muestral son las **30 086 personas únicas** del padrón. La elección es determinante: una muestra de registros repartiría las observaciones de una misma persona entre convocatorias distintas y ninguna trayectoria quedaría completa, con lo que la retención y las transiciones de categoría no serían estimables.

Antes de muestrear se comprobó que la clave `(ID_PERSONA_PR, ID_CONVOCATORIA)` es única: **0 duplicados** en los 77 237 registros. Por tanto el panel persona × convocatoria es una matriz sin repeticiones y cada persona tiene como máximo una observación por convocatoria.

### 1.2 Tamaño de muestra: fórmula de Cochran con corrección por población finita

Se usó la fórmula de Cochran (1977) para estimar una proporción con varianza máxima, corregida por población finita:

$$n_0 = \frac{Z^2\,p\,(1-p)}{e^2}, \qquad n = \frac{n_0}{1 + \dfrac{n_0-1}{N}}$$

| Parámetro | Valor | Justificación |
|---|---|---|
| Población `N` | 30 086 | personas únicas del padrón |
| Confianza `Z` | 1,96 | 95 % de confianza |
| Proporción `p` | 0,50 | varianza máxima `p(1-p) = 0,25`: tamaño más conservador (Cochran, 1977, §4.2) |
| Margen `e` | 0,02 | ±2 puntos porcentuales |
| `n₀` (sin corregir) | 2 401 | 1,96² × 0,25 / 0,02² |
| `n` corregido (exacto) | 2223,62 | `n₀ / (1 + (n₀−1)/N)` |
| **`n` final usado** | **2 224** | redondeo hacia arriba |
| Fracción de muestreo | 7,39 % | `n/N` |
| Error efectivo (con corrección) | 2,00 pp | `Z·√(p(1−p)/n)·√((N−n)/(N−1))` |

El margen de ±2 pp rige para **proporciones sobre el total de la muestra**. Para los subgrupos y para cada par de convocatorias la precisión es menor, porque el denominador es el número de personas presentes en esa convocatoria (entre 618 y 1 554), y así se reporta: cada tasa se acompaña de su propio intervalo.

### 1.3 Selección, semilla y reproducibilidad

El marco se ordenó de forma ascendente por `ID_PERSONA_PR` y se extrajeron 2 224 posiciones **sin reemplazo** con `numpy.random.default_rng(2026).choice(N, n, replace=False)`. La semilla 2026 fija la selección de manera determinista: repetir el procedimiento reproduce exactamente los mismos 2 224 identificadores y, por tanto, todas las cifras de este documento.

El identificador se trató siempre como texto (`dtype=str`), porque `ID_PERSONA_PR` tiene ceros a la izquierda y una conversión numérica los perdería. `EDAD_ANOS_PR` se leyó con `decimal=","` y `ANO_CONVO` como fecha `dd/mm/aaaa`, nunca como año.

### 1.4 Panel resultante

| Convocatoria | Fecha (`ANO_CONVO`) | Personas (universo) | Personas (muestra) | Registros en la muestra |
|---|---|---|---|---|
| 2013 | 2013-10-31 | 8 016 | 618 | 618 |
| 2014 | 2014-10-15 | 8 280 | 640 | 640 |
| 2015 | 2015-10-15 | 10 050 | 753 | 753 |
| 2017 | 2017-05-12 | 13 001 | 983 | 983 |
| 2019 | 2019-12-06 | 16 796 | 1 258 | 1 258 |
| 2021 | 2021-02-25 | 21 094 | 1 554 | 1 554 |
| **Total** | — | 77 237 | **2 224** | **5 806** |

La media de registros por persona en la muestra es 2,611 (en el universo, 2,567). Las cifras de personas por convocatoria coinciden exactamente con las del universo para cada uno de los seis cortes, porque cada persona aporta como máximo un registro por convocatoria.

### 1.5 Verificación de representatividad

Para comparar persona contra persona se fijó una regla explícita: el perfil de cada persona se toma de su **última convocatoria observada**. La regla es necesaria porque los atributos no son constantes dentro de una persona: 42 personas cambian de género; 1 203 personas cambian de departamento de residencia; 1 389 personas cambian de gran área de conocimiento; 3 844 personas cambian de nivel de formación; 8 755 personas cambian de categoría.

| Eje | χ² | gl | p | Diferencia absoluta máxima | Categoría con mayor diferencia |
|---|---|---|---|---|---|
| Género | 3,128 | 3 | 0,372 | 1,64 pp | Masculino (1,64 pp) |
| Categoría | 9,473 | 3 | 0,024 | 1,89 pp | Investigador Asociado (1,89 pp) |
| Gran área | 5,145 | 6 | 0,525 | 0,95 pp | Ingeniería y Tecnología (0,95 pp) |
| Departamento | 43,473 | 34 | 0,128 | 1,23 pp | Bogotá, D. C. (-1,23 pp) |
| Nivel de formación | 10,473 | 9 | 0,314 | 0,99 pp | Postdoctorado (0,99 pp) |

**Lectura.** Cuatro de los cinco ejes tienen p > 0,05. El único que baja de ese umbral es la categoría (p = 0,024), y hay que ser explícito sobre qué significa: se hicieron cinco contrastes simultáneos, de modo que el umbral de Bonferroni es 0,05/5 = 0,01 y ese p-valor **no** lo alcanza. Además, la mayor discrepancia observada en categoría es de 1,89 pp (Asociado: 19,24 % en el universo frente a 21,13 % en la muestra), dentro del margen de diseño de ±2 pp. En ninguna de las cinco variables la diferencia máxima supera 2 pp.

Conviene decirlo con precisión estadística: en un muestreo aleatorio simple la representatividad **está garantizada por el diseño** en esperanza, no es una hipótesis que haya que contrastar. Estos χ² no son evidencia de representatividad; son una **comprobación de la implementación** (que el marco estuviera bien construido y que el filtro por identificador no sesgara la extracción). Lo que sí es una limitación real es que dos categorías de género del universo —Intersexual (5 personas) y No disponible (4)— no quedan representadas en la muestra, algo esperable con esas frecuencias y que impide cualquier desagregación por ellas.

### 1.6 Validación contra el universo completo

La base completa está disponible, así que las estimaciones muéstrales pueden contrastarse con el valor censal. Esto no sustituye al muestreo —el ejercicio se diseñó como muestra— pero permite auditar el estimador:

| Par | Estimación muestral | Valor censal | Diferencia | ¿Censal dentro del IC 95 %? |
|---|---|---|---|---|
| Retención 2013→2014 | 61,17 % | 60,09 % | +1,07 pp | sí |
| Retención 2014→2015 | 82,66 % | 82,81 % | -0,16 pp | sí |
| Retención 2015→2017 | 80,74 % | 81,23 % | -0,49 pp | sí |
| Retención 2017→2019 | 76,50 % | 76,87 % | -0,37 pp | sí |
| Retención 2019→2021 | 80,21 % | 79,51 % | +0,69 pp | sí |
| Retención global 2013→2021 | 56,63 % | 56,18 % | +0,46 pp | sí |

Las seis estimaciones quedan dentro de ±1,07 pp del valor censal y el valor censal cae dentro del intervalo de confianza en los seis casos, de modo que el estimador reproduce el valor del universo dentro del margen de diseño.

## 2. Hallazgos

### 2.1 Retención, entradas y salidas por par de convocatorias

Definiciones: **retenidos** = presentes en ambas convocatorias; **salidas** = presentes en la primera y no en la segunda; **entradas** = presentes en la segunda y no en la primera. Las tasas de retención y salida se calculan sobre las personas presentes en la primera convocatoria, y la de entrada sobre las presentes en la segunda.

| Par | Años reales | n en t₁ | Retenidos | Tasa de retención | IC 95 % | Tasa de salida | Entradas | Tasa de entrada | Crecimiento neto |
|---|---|---|---|---|---|---|---|---|---|
| 2013→2014 | 0,96 | 618 | 378 | **61,2 %** | [57,32; 65,01] | 38,8 % | 262 | 40,9 % | +22 |
| 2014→2015 | 1,00 | 640 | 529 | **82,7 %** | [79,72; 85,59] | 17,3 % | 224 | 29,7 % | +113 |
| 2015→2017 | 1,57 | 753 | 608 | **80,7 %** | [77,93; 83,56] | 19,3 % | 375 | 38,1 % | +230 |
| 2017→2019 | 2,57 | 983 | 752 | **76,5 %** | [73,85; 79,15] | 23,5 % | 506 | 40,2 % | +275 |
| 2019→2021 | 1,22 | 1 258 | 1 009 | **80,2 %** | [78,00; 82,41] | 19,8 % | 545 | 35,1 % | +296 |

La identidad del panel se cumple en los cinco pares: retenidos + entradas reconstruye exactamente el tamaño de la segunda convocatoria (todos los pares). Los intervalos se calcularon con la fórmula binomial `p̂ ± 1,96·√(p̂(1−p̂)/n)`; se verificaron además el intervalo de Wilson y la versión con corrección por población finita: la discrepancia máxima entre los tres métodos, en cualquier par y en cualquier extremo, es de 0,20 pp. Los extremos se recortan al rango [0 %, 100 %], de modo que en grupos muy pequeños el límite superior puede aparecer pegado a 100 %.

### 2.2 Los intervalos de tiempo reales cambian la comparación

Los años **nominales** de las convocatorias sugieren intervalos de 1, 1, 2, 2 y 2 años. Pero `ANO_CONVO` contiene fechas, y al medirlas los intervalos reales son otros:

| Par | Intervalo nominal | Intervalo real (`ANO_CONVO`) | Retención observada | Anualizada (nominal) | Anualizada (real) |
|---|---|---|---|---|---|
| 2013→2014 | 1 año | 0,956 años | 61,2 % | 61,2 % | **62,8 %** |
| 2014→2015 | 1 año | 0,999 años | 82,7 % | 82,7 % | **82,7 %** |
| 2015→2017 | 2 años | 1,574 años | 80,7 % | 56,1 % | **64,9 %** |
| 2017→2019 | 2 años | 2,568 años | 76,5 % | 51,5 % | **43,1 %** |
| 2019→2021 | 2 años | 1,224 años | 80,2 % | 55,5 % | **73,4 %** |

La causa principal es un dato ya documentado en el repositorio auditado: la convocatoria rotulada **«833 de 2018» está fechada el 06/12/2019**. Por eso el hueco 2017→2019 dura 2,57 años, no 2, mientras que 2019→2021 dura solo 1,22 años.

La consecuencia no es cosmética: **invierte el orden de los pares**. Con años nominales, 2017→2019 (51,5 %) y 2019→2021 (55,5 %) parecen igual de malos; con los intervalos reales, 2017→2019 es con diferencia el par de peor retención anualizada (43,1 %) y 2019→2021 resulta ser el segundo mejor (73,4 %), por detrás de 2014→2015. Reportar solo la tasa observada, o anualizarla con años nominales, llevaría a la conclusión contraria.

La tasa anualizada supone riesgo constante dentro del intervalo (`1−(1−r)^{1/años}`): es una aproximación geométrica, no un modelo de supervivencia, y con solo seis puntos de observación no puede distinguir un riesgo constante de uno decreciente.

### 2.3 Retención global 2013→2021

De las 618 personas de la muestra reconocidas en 2013, 350 seguían reconocidas en 2021: **56,6 %** (IC 95 % [52,73; 60,54]). El valor censal es 56,2 %. En otras palabras, algo más de la mitad de quienes entraron en 2013 permanecía ocho años después, con tres convocatorias perdidas por el camino (2016, 2018 y 2020 no existieron).

La estructura de permanencia de las personas a lo largo de todo el período es muy desigual:

| N.º de convocatorias en que aparece | Personas | Porcentaje |
|---|---|---|
| 1 | 10 871 | 36,13 % |
| 2 | 7 139 | 23,73 % |
| 3 | 4 157 | 13,82 % |
| 4 | 2 720 | 9,04 % |
| 5 | 2 457 | 8,17 % |
| 6 | 2 742 | 9,11 % |

El **36,13 %** de las personas aparece en una sola convocatoria y nunca vuelve; en el extremo opuesto, 2 742 personas (9,11 %) están reconocidas en las seis. El padrón es, en buena parte, una población de paso.

### 2.4 Transiciones de categoría

Cada matriz tiene en las filas la categoría en la primera convocatoria del par y en las columnas la categoría en la segunda; cada celda muestra el número de personas y el porcentaje sobre el total de la fila (la categoría de origen). El orden jerárquico es Junior (12) < Asociado (13) < Sénior (14) < Emérito (15), según `ORDEN_CLAS_PR`.

**2013→2014** — 378 personas con categoría en ambas convocatorias; permanecen 277 (73,3 %), ascienden 69, descienden 32.

| Categoría en t₁ ↓ / t₂ → | Junior | Asociado | Sénior | Emérito | Total |
|---|---|---|---|---|---|
| Junior | 161 (73,5 %) | 47 (21,5 %) | 11 (5,0 %) | 0 (0,0 %) | 219 |
| Asociado | 30 (26,3 %) | 73 (64,0 %) | 11 (9,6 %) | 0 (0,0 %) | 114 |
| Sénior | 1 (2,2 %) | 1 (2,2 %) | 43 (95,6 %) | 0 (0,0 %) | 45 |
| Emérito | 0 | 0 | 0 | 0 | 0 |
| **Total** | 192 | 121 | 65 | 0 | 378 |

Movimientos más frecuentes: Junior→Asociado (47); Asociado→Junior (30); Asociado→Sénior (11); Junior→Sénior (11).

**2014→2015** — 529 personas con categoría en ambas convocatorias; permanecen 441 (83,4 %), ascienden 72, descienden 16.

| Categoría en t₁ ↓ / t₂ → | Junior | Asociado | Sénior | Emérito | Total |
|---|---|---|---|---|---|
| Junior | 266 (83,6 %) | 51 (16,0 %) | 1 (0,3 %) | 0 (0,0 %) | 318 |
| Asociado | 10 (6,7 %) | 119 (79,9 %) | 20 (13,4 %) | 0 (0,0 %) | 149 |
| Sénior | 2 (3,2 %) | 4 (6,5 %) | 56 (90,3 %) | 0 (0,0 %) | 62 |
| Emérito | 0 | 0 | 0 | 0 | 0 |
| **Total** | 278 | 174 | 77 | 0 | 529 |

Movimientos más frecuentes: Junior→Asociado (51); Asociado→Sénior (20); Asociado→Junior (10); Sénior→Asociado (4).

**2015→2017** — 608 personas con categoría en ambas convocatorias; permanecen 477 (78,5 %), ascienden 100, descienden 31.

| Categoría en t₁ ↓ / t₂ → | Junior | Asociado | Sénior | Emérito | Total |
|---|---|---|---|---|---|
| Junior | 263 (79,9 %) | 53 (16,1 %) | 13 (4,0 %) | 0 (0,0 %) | 329 |
| Asociado | 25 (12,4 %) | 143 (71,1 %) | 31 (15,4 %) | 2 (1,0 %) | 201 |
| Sénior | 2 (2,6 %) | 4 (5,1 %) | 71 (91,0 %) | 1 (1,3 %) | 78 |
| Emérito | 0 | 0 | 0 | 0 | 0 |
| **Total** | 290 | 200 | 115 | 3 | 608 |

Movimientos más frecuentes: Junior→Asociado (53); Asociado→Sénior (31); Asociado→Junior (25); Junior→Sénior (13).

**2017→2019** — 752 personas con categoría en ambas convocatorias; permanecen 554 (73,7 %), ascienden 147, descienden 51.

| Categoría en t₁ ↓ / t₂ → | Junior | Asociado | Sénior | Emérito | Total |
|---|---|---|---|---|---|
| Junior | 305 (75,1 %) | 87 (21,4 %) | 14 (3,4 %) | 0 (0,0 %) | 406 |
| Asociado | 41 (18,0 %) | 142 (62,3 %) | 45 (19,7 %) | 0 (0,0 %) | 228 |
| Sénior | 4 (3,4 %) | 6 (5,1 %) | 107 (90,7 %) | 1 (0,8 %) | 118 |
| Emérito | 0 | 0 | 0 | 0 | 0 |
| **Total** | 350 | 235 | 166 | 1 | 752 |

Movimientos más frecuentes: Junior→Asociado (87); Asociado→Sénior (45); Asociado→Junior (41); Junior→Sénior (14).

**2019→2021** — 1 009 personas con categoría en ambas convocatorias; permanecen 730 (72,3 %), ascienden 189, descienden 90.

| Categoría en t₁ ↓ / t₂ → | Junior | Asociado | Sénior | Emérito | Total |
|---|---|---|---|---|---|
| Junior | 415 (74,0 %) | 116 (20,7 %) | 30 (5,3 %) | 0 (0,0 %) | 561 |
| Asociado | 63 (22,6 %) | 173 (62,0 %) | 41 (14,7 %) | 2 (0,7 %) | 279 |
| Sénior | 8 (4,7 %) | 19 (11,2 %) | 142 (84,0 %) | 0 (0,0 %) | 169 |
| Emérito | 0 | 0 | 0 | 0 | 0 |
| **Total** | 486 | 308 | 213 | 2 | 1009 |

Movimientos más frecuentes: Junior→Asociado (116); Asociado→Junior (63); Asociado→Sénior (41); Junior→Sénior (30).

Las transiciones dominantes son de ascenso: Junior→Asociado es el flujo más numeroso en todos los pares, con 116 personas en 2019→2021 (20,7 % de los Junior de 2019). En el mismo par, 41 Asociados pasaron a Sénior. Los descensos existen y no son marginales: 90 personas bajaron de categoría en 2019→2021, de las cuales 63 son Asociado→Junior y 19 son Sénior→Asociado. Es decir, la categoría no es un derecho adquirido: 8,9 % de las trayectorias observadas retrocedió.

### 2.5 «Emérito» es un estado absorbente

De las 251 personas clasificadas como Investigador Emérito en las convocatorias de 2015, 2017 y 2019, **ninguna** vuelve a aparecer en una convocatoria posterior: 0 retornos sobre 251 oportunidades. La categoría no existe en 2013 ni en 2014 y aparece por primera vez en 2015 (74 personas).

Esto tiene dos consecuencias. En lo descriptivo, la fila «Emérito» de toda matriz de transición es estructuralmente cero: nadie sale de Emérito porque nadie vuelve a ser observado. En lo analítico, cualquier cadena de Markov que se ajuste a estas transiciones tendrá en Emérito un **estado absorbente**, y la retención de los Eméritos no es un caso particular de baja retención sino una regla del sistema. Lo que el dato **no** permite determinar es la causa: podría ser que el reconocimiento de Emérito no se renueve, que se otorgue una sola vez, o que quienes lo reciben dejen de postularse. El registro no contiene esa información.

### 2.6 Entradas y salidas en sentido estricto

La definición del enunciado clasifica como «entrada» a quien está en la segunda convocatoria y no en la primera, pero eso mezcla dos poblaciones muy distintas: quien nunca había sido reconocido y quien ya lo fue antes, faltó a la convocatoria intermedia y volvió. Separarlas cambia la lectura del crecimiento:

| Par | Entradas (definición del enunciado) | Entradas nuevas reales | Reingresos | Reingresos / entradas | Salidas | Salidas temporales | Salidas definitivas |
|---|---|---|---|---|---|---|---|
| 2013→2014 | 262 | 262 | 0 | 0,0 % | 240 | 115 | 125 |
| 2014→2015 | 224 | 183 | 41 | 18,3 % | 111 | 71 | 40 |
| 2015→2017 | 375 | 292 | 83 | 22,1 % | 145 | 58 | 87 |
| 2017→2019 | 506 | 419 | 87 | 17,2 % | 231 | 62 | 169 |
| 2019→2021 | 545 | 450 | 95 | 17,4 % | 249 | 0 | 249 |

Entre el 14 % y el 22 % de las «entradas» son en realidad **reingresos** de personas ya reconocidas antes. Y en el otro sentido, buena parte de las «salidas» no son definitivas: en 2013→2014, 115 de las 240 salidas (47,9 %) corresponden a personas que reaparecen después. Tratar cada ausencia como una baja definitiva infla la rotación aparente del padrón.

La última fila requiere una advertencia: en 2019→2021 no hay convocatorias posteriores, de modo que las 249 salidas están **censuradas a la derecha** y la columna de salidas definitivas no es comparable con la de los pares anteriores.

### 2.7 Desagregaciones

**Retención por género en todos los pares** (tasa de retención por par; el contraste contrasta la hipótesis de igual retención entre géneros):

| Género | 2013→2014 | 2014→2015 | 2015→2017 | 2017→2019 | 2019→2021 | n en 2019 (último par) |
|---|---|---|---|---|---|---|
| Masculino | 63,3 % | 83,6 % | 81,4 % | 78,9 % | 81,4 % | 803 |
| Femenino | 56,9 % | 80,8 % | 79,5 % | 72,3 % | 78,0 % | 455 |
| *p* (χ² homogeneidad) | 0,123 | 0,377 | 0,546 | 0,020 | 0,143 | — |

La retención femenina es **inferior a la masculina en los cinco pares**, con una brecha que va de 1,84 puntos porcentuales en 2015→2017 a 6,54 en 2017→2019. La dirección es consistente, pero solo en 2017→2019 la diferencia es estadísticamente significativa al 5 % (p = 0,020); en los otros cuatro pares el intervalo no permite descartar el azar. Un patrón sistemático en la dirección con significación intermitente es compatible tanto con una desventaja real y moderada como con fluctuación muestral: con esta muestra no puede resolverse, y haría falta un contraste conjunto o una muestra mayor para decidirlo.

**Retención por gran área de conocimiento**:

| Gran área | 2013→2014 | 2014→2015 | 2015→2017 | 2017→2019 | 2019→2021 |
|---|---|---|---|---|---|
| Ciencias Sociales | 53,0 % | 81,5 % | 76,2 % | 73,7 % | 76,2 % |
| Ciencias Naturales | 66,4 % | 82,2 % | 79,9 % | 77,5 % | 80,3 % |
| Ingeniería y Tecnología | 72,8 % | 89,6 % | 85,5 % | 82,5 % | 86,2 % |
| Ciencias Médicas y de la Salud | 71,0 % | 81,4 % | 83,3 % | 74,3 % | 83,3 % |
| Humanidades | 40,0 % | 80,0 % | 79,1 % | 72,7 % | 76,7 % |
| Ciencias Agrícolas | 67,6 % | 78,4 % | 82,2 % | 75,8 % | 80,0 % |
| No registra | 54,9 % | 55,6 % | — | — | 50,0 % |
| *p* (χ² homogeneidad) | < 0,001 | 0,137 | 0,339 | 0,278 | 0,021 |

**Retención por departamento de residencia** (cinco mayores del padrón) y **por nivel de formación** en el último par:

| Grupo | n | Retenidos | Tasa | IC 95 % |
|---|---|---|---|---|
| Departamento: Bogotá, D. C. | 392 | 297 | 75,8 % | [71,52; 80,01] |
| Departamento: Antioquia | 211 | 170 | 80,6 % | [75,23; 85,91] |
| Departamento: Valle del Cauca | 96 | 78 | 81,2 % | [73,44; 89,06] |
| Departamento: Atlántico | 87 | 78 | 89,7 % | [83,26; 96,05] |
| Departamento: Santander | 80 | 72 | 90,0 % | [83,43; 96,57] |
| Nivel: Doctorado | 620 | 490 | 79,0 % | [75,83; 82,24] |
| Nivel: Maestría/Magister | 478 | 391 | 81,8 % | [78,34; 85,26] |
| Nivel: Postdoctorado | 95 | 74 | 77,9 % | [69,55; 86,24] |
| Nivel: Pregrado/Universitario | 24 | 19 | 79,2 % | [62,92; 95,41] |
| Nivel: Especialización | 21 | 17 | 81,0 % | [64,16; 97,75] |
| Nivel: Especialidad Médica | 20 | 18 | 90,0 % | [76,85; 100,00] |

Resultados de los contrastes de homogeneidad para el par 2019→2021:

| Eje | χ² | gl | p | Frecuencia esperada mínima | ¿Supuesto de χ² satisfecho? |
|---|---|---|---|---|---|
| Género | 2,143 | 1 | 0,143 | 90,06 | sí |
| Departamento | 14,705 | 4 | 0,005 | 15,80 | sí |
| Gran área | 14,964 | 6 | 0,021 | 1,19 | **no** |
| Nivel de formación | 2,854 | 5 | 0,722 | 3,96 | **no** |

Solo el **departamento** supera el contraste sin reservas (p = 0,005; frecuencia esperada mínima 15,80, suficiente): Atlántico (89,7 %) y Santander (90,0 %) retienen bastante más que Bogotá (75,8 %) y Valle del Cauca (81,2 %). En gran área el p-valor es 0,021, pero con una frecuencia esperada mínima de 1,19 las celdas pequeñas invalidan la aproximación χ², así que no debe interpretarse. En nivel de formación no hay diferencia apreciable (p = 0,722).

**Transiciones desagregadas (2019→2021)**: composición de las trayectorias por grupo.

| Grupo | n | Permanece | Asciende | Desciende |
|---|---|---|---|---|
| Género: Femenino | 355 | 271 (76,3 %) | 55 (15,5 %) | 29 (8,2 %) |
| Género: Masculino | 654 | 459 (70,2 %) | 134 (20,5 %) | 61 (9,3 %) |
| Gran área: Ciencias Agrícolas | 52 | 41 (78,8 %) | 9 (17,3 %) | 2 (3,8 %) |
| Gran área: Ciencias Médicas y de la Salud | 145 | 103 (71,0 %) | 31 (21,4 %) | 11 (7,6 %) |
| Gran área: Ciencias Naturales | 216 | 163 (75,5 %) | 43 (19,9 %) | 10 (4,6 %) |
| Gran área: Ciencias Sociales | 305 | 216 (70,8 %) | 47 (15,4 %) | 42 (13,8 %) |
| Gran área: Humanidades | 69 | 43 (62,3 %) | 15 (21,7 %) | 11 (15,9 %) |
| Gran área: Ingeniería y Tecnología | 219 | 162 (74,0 %) | 44 (20,1 %) | 13 (5,9 %) |
| Gran área: No registra | 3 | 2 (66,7 %) | 0 (0,0 %) | 1 (33,3 %) |
| Departamento: Antioquia | 170 | 122 (71,8 %) | 38 (22,4 %) | 10 (5,9 %) |
| Departamento: Atlántico | 78 | 51 (65,4 %) | 13 (16,7 %) | 14 (17,9 %) |
| Departamento: Bogotá, D. C. | 297 | 214 (72,1 %) | 51 (17,2 %) | 32 (10,8 %) |
| Departamento: Santander | 72 | 58 (80,6 %) | 10 (13,9 %) | 4 (5,6 %) |
| Departamento: Valle del Cauca | 78 | 53 (67,9 %) | 18 (23,1 %) | 7 (9,0 %) |

Los hombres ascienden más que las mujeres (20,49 % frente a 15,49 %) y las mujeres permanecen más (76,34 % frente a 70,18 %), pero el contraste global no alcanza significación (p = 0,099). El patrón es coherente con la brecha de retención: ellas se quedan más y suben menos. En Ciencias Sociales y Humanidades el porcentaje de descensos es el más alto (13,77 % y 15,94 %), aunque el contraste por gran área tiene celdas esperadas por debajo de 1 y su p-valor (0,006) no es fiable.

### 2.8 Calidad del registro que revela el panel

El seguimiento de las mismas personas entre convocatorias expone inconsistencias que un análisis transversal no puede ver:

- **Género contradictorio.** 42 personas (0,14 % del padrón) figuran con más de un género a lo largo del tiempo: Masculino→Femenino (30), Femenino→Masculino (7), Femenino→Intersexual (2), Masculino→Intersexual (2), Masculino→No disponible (1). El género no es un atributo estable en este registro.
- **Atributos que cambian dentro de la misma persona**: departamento de residencia en 1 203 personas, gran área en 1 389, nivel de formación en 3 844 y categoría en 8 755. Los tres primeros son en parte esperables (migración, nuevos títulos), pero obligan a declarar qué observación se usa en cada análisis.
- **Sin duplicados**: 0 repeticiones de la clave persona × convocatoria, lo que permite tratar el panel como una matriz limpia.
- **Tamaño del sistema**: 30 086 personas y 77 237 reconocimientos a lo largo de seis convocatorias en nueve años del calendario.

## 3. Conclusiones

1. **La retención es alta en cada intervalo, pero acumulada pierde casi la mitad del padrón.** Entre convocatorias consecutivas se retiene entre 61,2 % y 82,7 %, pero de quienes entraron en 2013 solo 56,6 % seguía en 2021. La caída no ocurre de golpe en un par concreto: se acumula en cinco transiciones.
2. **Anualizar con las fechas reales invierte el diagnóstico.** El hueco 2017→2019 dura 2,57 años y el 2019→2021 solo 1,22. Con años nominales ambos parecen equivalentes; con las fechas reales, 2017→2019 es el peor par (43,1 % anualizado) y 2019→2021 el segundo mejor (73,4 %). Cualquier comparación entre convocatorias que ignore las fechas reales llega a la conclusión opuesta.
3. **La movilidad es ascendente y masiva, y el descenso también existe.** En 2019→2021, de 1 009 trayectorias observadas 189 ascendieron y 90 descendieron (8,9 %). La categoría de investigador es revisable a la baja, no un escalafón de una sola dirección.
4. **«Emérito» funciona como estado terminal: 0 de 251 retornos.** Ninguna persona clasificada como Emérito vuelve a aparecer en una convocatoria posterior. Es la regularidad más nítida de todo el análisis y debe incorporarse como supuesto explícito en cualquier modelo de transición.
5. **La rotación aparente está inflada.** Entre el 14 % y el 22 % de las «entradas» son reingresos de personas ya reconocidas, y hasta 47,9 % de las salidas de 2013→2014 corresponden a personas que reaparecen después. Contar cada ausencia como una baja permanente sobreestima el recambio del padrón.

## 4. Limitaciones

1. **Es una muestra, no el universo.** Las cifras son estimaciones con intervalos al 95 %; el error efectivo de diseño es de ±2,00 pp para proporciones sobre el total de la muestra y mayor en subgrupos. En este ejercicio el valor censal estaba disponible y todas las estimaciones quedaron a menos de 1,1 pp, pero esa comprobación es un privilegio de contar con la base completa: en un uso real del muestreo solo se dispondría del intervalo.
2. **Las convocatorias no son anuales.** Faltan 2016, 2018 y 2020, y los intervalos reales van de 0,96 a 2,57 años. Las tasas anualizadas suponen riesgo constante dentro de cada intervalo y con seis puntos de observación no puede contrastarse ese supuesto. El análisis es descriptivo: no se ajustó ningún modelo de supervivencia ni de hazard, pese a que el anteproyecto mencionaba esos métodos.
3. **Qué significa `ANO_CONVO` no está documentado.** Se midió el intervalo con esas fechas, que son el único dato temporal del archivo, pero la discrepancia entre el rótulo «833 de 2018» y la fecha 06/12/2019 no se resuelve con la información disponible. Si `ANO_CONVO` fuera una fecha de publicación de resultados y no de apertura, los intervalos reales cambiarían y con ellos las tasas anualizadas.
4. **Observación solo en las fechas de convocatoria.** Una persona ausente en una convocatoria y presente en la siguiente es indistinguible de alguien que nunca fue reconocido, salvo por el historial previo. Por eso se separaron reingresos y salidas temporales; aun así, no se observa lo que ocurre entre convocatorias.
5. **Censura a la derecha en el último par.** En 2019→2021 no hay convocatorias posteriores: las 249 salidas no pueden clasificarse en temporales y definitivas, y la retención de 2021 es la última observable. El mismo problema afecta a la categoría Emérito, cuya condición terminal se comprueba solo hasta 2021.
6. **Subgrupos pequeños.** Categorías como Emérito o «No registra» en gran área tienen frecuencias que no sostienen contrastes: en varios ejes la frecuencia esperada mínima baja de 5 y el χ² deja de ser válido. Se marcó explícitamente en cada caso en lugar de reportar el p-valor como si fuera interpretable.
7. **Atributos no constantes.** El perfil de cada persona se tomó de su última convocatoria observada, y el género cambia en 42 personas. Las desagregaciones por género o área usan el atributo en la convocatoria de origen de cada par, lo que es coherente para medir retención, pero no debe leerse como una característica fija de la persona.

## 5. Referencias

- Cochran, W. G. (1977). *Sampling Techniques* (3.ª ed.). John Wiley & Sons. (Fórmula de tamaño de muestra para una proporción y corrección por población finita.)
- Lohr, S. L. (2010). *Sampling: Design and Analysis* (2.ª ed.). Brooks/Cole. (Muestreo aleatorio simple, estimación de proporciones y efectos del diseño.)
- Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association*, 22(158), 209–212. (Intervalo de confianza de score, usado como comprobación del intervalo de Wald.)
- Agresti, A. y Coull, B. A. (1998). Approximate is better than “exact” for interval estimation of binomial proportions. *The American Statistician*, 52(2), 119–126.
- Departamento Administrativo de Ciencia, Tecnología e Innovación (MinCiencias). *Investigadores reconocidos por convocatoria* [conjunto de datos, `bqtm-4y2h`]. datos.gov.co. Consulta: 2026-10-06.

## Anexo: archivos y reproducibilidad

| Archivo | Contenido |
|---|---|
| `documentacion_auditoria/src/analisis_longitudinal.py` | Cálculo completo: muestreo, representatividad, retención, transiciones, desagregaciones y gráficas |
| `documentacion_auditoria/src/generar_analisis_longitudinal.py` | Genera este documento a partir del JSON verificado |
| `data/memoria/muestra_ids.csv` | 2 224 identificadores muestreados (entregable) |
| `data/memoria/muestra_registros.csv` | Los 5 806 registros de esas personas en las seis convocatorias |
| `data/memoria/longitudinal_resultados.json` | Todas las cifras citadas en este documento |
| `data/memoria/graficas_longitudinal/` | Las cinco gráficas (entregable) |

Reproducción:

```bash
python documentacion_auditoria/src/analisis_longitudinal.py
python documentacion_auditoria/src/generar_analisis_longitudinal.py
```

Con la semilla 2026 el procedimiento es determinista: la misma corrida produce los mismos 2 224 identificadores y las mismas cifras. La verificación independiente de retención y transiciones (recalculadas con operaciones de conjuntos y tablas cruzadas, sin reutilizar el código del análisis) coincide exactamente con los resultados reportados.

