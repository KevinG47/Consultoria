# Metodología estadística del análisis longitudinal

**Auditoría estadística del sistema de reconocimiento de investigadores de MinCiencias**  
EDA previo, justificación del muestreo, post-estratificación y estimador GREG. Documento generado por `documentacion_auditoria/src/generar_metodologia_muestreo.py` a partir de `data/memoria/eda_resultados.json` y `data/memoria/estimadores_resultados.json`. Fecha: 2026-10-14.

**Alcance.** Este documento es un **ejercicio metodológico**: documenta *cómo* se estimaría y qué se gana con cada estimador. Las cifras oficiales del análisis longitudinal son las del **censo** (la base completa está disponible), que se reportan en `analisis_longitudinal.md`; aquí se usan además como patrón de contraste, lo que permite verificar de verdad cada estimador en lugar de confiar en la teoría.

**Datos.** 77 237 registros, 30 086 personas únicas, 6 convocatorias (2013-2021). Muestra vigente: 2 224 personas, MAS con semilla 2026.

## 1. Marco teórico

### 1.1 Por qué un EDA antes de decidir el muestreo

El análisis exploratorio no es un trámite previo: es lo que permite elegir el diseño. Como resume la literatura de muestreo, *«el análisis exploratorio de datos, incluidas la producción de resúmenes simples, tabulaciones y gráficos, es normalmente la primera etapa de cualquier análisis de este tipo»* y se debe *«llevar a cabo trabajo exploratorio sobre subconjuntos o muestras para clarificar qué enfoque será a la vez práctico y eficaz»* (StatsRef.com, sobre Cochran, 1977). En este proyecto el EDA cumple tres funciones concretas:

1. **Detectar si hay estratos naturales**, es decir, grupos con comportamiento muy distinto. Si no los hay, la estratificación no aporta y complica el diseño.
2. **Detectar grupos pequeños** que necesitarían representación garantizada y no la tienen con un MAS.
3. **Cuantificar la varianza intra e inter-grupo**, que es exactamente lo que determina cuánta precisión se gana al estratificar.

### 1.2 Los tres estimadores y su relación

| Estimador | Idea | Fundamento |
|---|---|---|
| **MAS (expansión simple)** | Cada persona entra con el mismo peso `N/n` | Cochran (1977); Lohr (2010). Insesgado por diseño |
| **Post-estratificado** | Se reponderan los pesos para que la muestra reproduzca la composición conocida de la población en categorías | Cochran (1977, §5A); Lohr (2010, §7.6). Su distribución asintótica coincide con la de un muestreo estratificado con asignación proporcional |
| **GREG (model-assisted)** | Se usa un modelo de regresión como auxiliar, pero la validez de la estimación **no** depende de que el modelo sea correcto | Särndal, Swensson & Wretman (1992, §6.4-6.5); FCSM (2003); Kalton (2002) |

La idea central del GREG es la del **modelo asistido**: el modelo se usa para ganar eficiencia, no para sostener la inferencia. Como lo formulan Kalton (2002) y el FCSM (2003), *«los modelos se usan ampliamente dentro del modo de inferencia basado en el diseño, tanto en el diseño muestral como en la estimación, pero de manera asistida por el modelo, de forma que la validez de las estimaciones no depende de la validez de los supuestos del modelo»*. La propiedad que lo garantiza es la consistencia por diseño: si el modelo es malo, el estimador sigue siendo aproximadamente insesgado porque el término de corrección usa los residuos observados en la muestra.

Formalmente, con probabilidades de inclusión `π_i = n/N` (MAS sin reemplazo) el estimador de diferencia que se implementa aquí es

$$\hat{Y}_{GREG} = \frac{1}{N}\sum_{i\in U}\hat{y}_i + \frac{1}{n}\sum_{i\in s}\left(y_i - \hat{y}_i\right)$$

y con un modelo **lineal** adopta la forma clásica `Y_GREG = ȳ_s + (X̄_U − x̄_s)′β̂_s`, donde las medias de las auxiliares se conocen para **toda** la población. Un detalle importante para interpretar los resultados: **la post-estratificación es un caso particular de GREG** con un modelo saturado en los post-estratos. En la sección 6 se comprueba numéricamente.

## 2. EDA: qué se exploró y qué se encontró

### 2.1 Univariado

**Categóricas** (perfil de cada persona en su última convocatoria observada, n = 30 086):

| Variable | Categorías | Distribución |
|---|---:|---|
| Categoría | 4 | Investigador Junior 68,7 % · Investigador Asociado 19,2 % · Investigador Sénior 10,9 % · Investigador Emérito 1,1 % |
| Género | 4 | Masculino 60,6 % · Femenino 39,4 % · Intersexual 0,0 % · No disponible 0,0 % |
| Gran área | 7 | Ciencias Sociales 30,7 % · Ciencias Naturales 20,9 % · Ingeniería y Tecnología 18,7 % · Ciencias Médicas y de la Salud 15,2 % · Humanidades 8,0 % · … (7 en total) |
| Nivel de formación | 10 | Doctorado 49,4 % · Maestría/Magister 36,0 % · Postdoctorado 7,6 % · Especialidad Médica 2,5 % · Pregrado/Universitario 2,2 % · … (10 en total) |
| Departamento | 35 | Bogotá D. C. 32,6 % · Antioquia 16,6 % · Valle del Cauca 8,3 % · Atlántico 6,2 % · Santander 5,2 % · … |

**Edad.** Media 45,52 años, desviación 13,91, mediana 43,8, rango intercuartílico 15,6 (Q1 = 37,2; Q3 = 52,8). El criterio del bigote 1,5·IQR marca **106 valores atípicos**, y 11 personas declaran **más de 100 años** (máximo registrado: 956,25). Sin esos casos la media baja a 45,39 años: es un problema de **calidad de captura**, no de la población, y por eso se reporta explícitamente.

**Presencia.** Cada persona aparece en promedio en 2,567 convocatorias. El 36,1 % aparece en una sola y nunca vuelve, y solo el 9,1 % está en las seis. Esto ya anticipa que la serie temporal tendrá mucha entrada y salida, y que la unidad de análisis correcta es la persona, no el registro.

**Faltantes.** De 30 columnas, 4 tienen valores vacíos:

| Columna | Vacíos | % | Convocatorias afectadas |
|---|---:|---:|---|
| `INST_FILIA` | 9 326 | 12,1 % | 2013: 2 016, 2014: 1 415, 2015: 1 622, 2017: 1 634, 2019: 321, 2021: 2 318 |
| `COD_DANE_NAC_PR` | 4 591 | 5,9 % | 2013: 624, 2014: 519, 2015: 694, 2017: 790, 2019: 940, 2021: 1 024 |
| `COD_DANE_RES_PR` | 2 448 | 3,2 % | 2013: 347, 2014: 242, 2015: 329, 2017: 291, 2019: 488, 2021: 751 |
| `EDAD_ANOS_PR` | 1 | 0,0 % | 2021: 1 |

Las tres columnas más afectadas son institucionales o geográficas (`COD_DANE_*`), **ninguna es una variable del análisis longitudinal**, y el único vacío en edad es un registro. Conclusión operativa: los faltantes no obligan a un tratamiento especial (imputación o excluir dominios), lo que refuerza la viabilidad del MAS.

### 2.2 Bivariado: ¿la retención depende del grupo?

Para cada par de convocatorias consecutivas se calculó la retención por estrato candidato. La pregunta que importa para el diseño es **cuánta varianza de la retención explica cada variable**, porque con asignación proporcional la reducción teórica de varianza al estratificar es exactamente esa proporción. Se calcula sobre el **censo** (par de referencia 2019→2021, retención global 79,5 %):

| Estrato candidato | Estratos | Varianza **entre** grupos | Varianza **dentro** | χ² | p |
|---|---:|---:|---:|---:|---:|
| `CLASIFICACION` | 4 | **7,1 %** | 92,9 % | 1 189,0 | < 10⁻²⁰⁰ |
| `GENERO` | 2 | **0,1 %** | 99,9 % | 18,9 | 1,35e-05 |
| `GRAN_AREA` | 7 | **1,4 %** | 98,6 % | 232,3 | 2,44e-47 |
| `DEPARTAMENTO_RES` | 32 | **1,0 %** | 99,0 % | 166,8 | 1,59e-20 |
| `NIV_FORM` | 8 | **0,3 %** | 99,7 % | 50,7 | 1,06e-08 |

Los contrastes χ² dan significativos todos los candidatos, pero eso es casi inevitable con N = 30 086: la significación estadística no mide relevancia. Lo informativo es la **magnitud**: la categoría de reconocimiento explica el 7,1 % de la varianza de la retención, mientras que género, gran área, departamento y nivel de formación no llegan al 1,4 % cada uno. Es decir: **la población es homogénea en su comportamiento de permanencia salvo por la categoría**.

### 2.3 ¿Hay estratos naturales?

| Candidato | Estratos | Reducción teórica de varianza | Estrato más pequeño (censo) |
|---|---:|---:|---:|
| `CLASIFICACION × GRAN_AREA` | 27 | 8,4 % | 2 |
| `CLASIFICACION × GENERO` | 8 | 7,1 % | 16 |
| `CLASIFICACION` | 4 | 7,1 % | 53 |
| `GRAN_AREA` | 7 | 1,4 % | 105 |
| `DEPARTAMENTO_RES` | 32 | 1,0 % | 1 |
| `NIV_FORM` | 8 | 0,3 % | 1 |
| `GENERO` | 2 | 0,1 % | 6 411 |

Lectura del EDA, que es la que sostiene las decisiones posteriores:

1. **Sí hay un estrato natural, pero uno solo: la categoría.** Con 4 estratos explica alrededor del 7 % de la varianza de la retención. Ese 7 % es el techo de lo que se puede ganar por esta vía, y es modesto.
2. **Combinar variables casi no añade y sí complica.** Añadir género a la categoría sube la varianza explicada de 7,08 % a 7,12 % (ocho estratos en lugar de cuatro), y cruzar categoría con gran área llega a 8,39 % pero genera 27 estratos con celdas de 2 personas en el censo: inaplicable.
3. **Cuatro estratos es además lo que recomienda la teoría.** Cochran (1977, pp. 132-134) aconseja entre cuatro y seis estratos cuando el tamaño por estrato es razonable: el número de estratos se elige por el tamaño de muestra disponible, no por el tamaño de la población.
4. **No hay grupos pequeños que exijan representación garantizada** en el diseño: el grupo minoritario del censo (Emérito, 334 personas = 1,1 %) queda cubierto por el MAS en proporción, y su tratamiento se resuelve en la etapa de estimación (sección 4), no en la de diseño.

Las gráficas del EDA están en `data/memoria/eda/`.

## 3. Decisión de muestreo: MAS, y por qué

Se mantiene el **muestreo aleatorio simple de personas** ya ejecutado (n = 2 224, semilla 2026). La decisión se sostiene en cuatro razones, y la tercera responde directamente a la pregunta de por qué no se combina con regresión:

1. **El marco es una lista completa de unidades finales.** Las 30 086 personas tienen identificador único y no hay duplicados persona × convocatoria, así que no existe la situación que justifica un diseño por conglomerados o polietápico (Cochran, 1977, §9-§10): no hay que muestrear unidades compuestas para llegar a las finales.
2. **El EDA no muestra estructura fuerte que obligue a estratificar.** Con un techo de ~7 % de varianza explicada, y con un MAS cuyo error de diseño efectivo es de ±2,0 pp, la ganancia potencial de un diseño estratificado no compensa la pérdida de simplicidad: estratificar exigiría definir cuotas y ponderar cada estimación posterior.
3. **«MAS o regresión» es un falso dilema: se combinan, y aquí se hace.** La regresión no sustituye al diseño; entra como **información auxiliar** en la etapa de estimación. Eso es exactamente el estimador GREG de la sección 5: el diseño aporta la validez (insesgadez aproximada por diseño) y el modelo aporta eficiencia (menos varianza). Kalton (2002) y el FCSM (2003) formulan esta posición como el uso *asistido por el modelo* de la inferencia basada en el diseño. Dicho de otro modo: no se elige entre muestrear y modelar, se elige no hacer depender la validez del modelo.
4. **La igualdad de probabilidades simplifica el análisis longitudinal.** Al ser autoponderado, la retención de un par es directamente una proporción muestral y las matrices de transición son proporciones de celdas, sin ponderadores intermedios. Eso reduce las oportunidades de error en una cadena de cálculo que ya es larga.

Además, el MAS conserva la propiedad que hace posible este documento: se puede **verificar** contra el censo, porque la base completa está disponible. La sección 6 explota esa posibilidad.

## 4. Post-estratificación

### 4.1 Fundamento y pesos

La post-estratificación repondera las observaciones para que la muestra reproduzca una composición de la población **conocida de antemano**. Con `N_h` el total poblacional del estrato `h` y `n_h` el de la muestra, el peso de cada persona del estrato es

$$w_i = \frac{N_h/N}{n_h/n}$$

y el estimador es `Σ_h W_h p̂_h` con `W_h = N_h/N`, con varianza estimada

$$v = \sum_h W_h^2\,(1 - n_h/N_h)\,\frac{s_h^2}{n_h}$$

La propiedad que justifica usarla es que su distribución asintótica es la misma que la de un muestreo estratificado con asignación proporcional (Cochran, 1977, §5A; Lohr, 2010, §7.6). Su atractivo aquí es que es **barata**: la composición por categoría de toda la población se conoce, así que no hay coste de diseño.

### 4.2 Condición de tamaño mínimo: no se cumple en tres pares

Cochran (1977, pp. 132-134) recomienda que **cada estrato tenga un tamaño razonable, del orden de 20**, porque `p̂_h` se estima solo con las observaciones de ese estrato. El resultado de comprobarlo es incómodo y hay que decirlo:

| Par | n_h por estrato (Junior / Asociado / Sénior / Emérito) | ¿Cumple n_h > 20? |
|---|---|---|
| 2013→2014 | 440 / 128 / 50 / 0 | sí |
| 2014→2015 | 400 / 169 / 71 / 0 | sí |
| 2015→2017 | 444 / 227 / 81 / 1 | **no** (Emérito n_h = 1) |
| 2017→2019 | 580 / 271 / 125 / 7 | **no** (Emérito n_h = 7) |
| 2019→2021 | 757 / 322 / 176 / 3 | **no** (Emérito n_h = 3) |
| 2013→2021 | 440 / 128 / 50 / 0 | sí |

Un 0 en esa columna no significa un estrato pequeño sino **inexistente**: el reconocimiento Emérito no aparece en el padrón hasta 2015, así que en las convocatorias de 2013 y 2014 ese estrato no existe ni en la población ni en la muestra, y no hay nada que reponderar.

**Consecuencias, y qué se hizo al respecto.** En los pares donde Emérito tiene 1, 7 o 3 observaciones, la post-estratificación de 4 estratos hace depender el resultado de una celda diminuta: `s_h²` es inestable y el peso de esas personas se dispara (hasta 5,5 en el estrato «Investigador Emérito», estimado con 1 observación(es)). Un peso así significa que una sola persona representa a decenas en la población, que es exactamente lo que la condición de Cochran busca evitar.
Las dos salidas estándar son **colapsar estratos** o **usar un modelo** que preste fuerza a la celda pequeña. Aquí se implementaron **las dos** y se reportan ambas: una post-estratificación colapsada (Sénior + Emérito, con lo que el estrato pequeño pasa a tener un tamaño suficiente en todos los pares) y el estimador GREG de la sección 5, que no depende de que cada celda tenga 20 casos porque estima un efecto común con todas las observaciones.

### 4.3 Resultados sobre la retención

| Par | Censo | MAS | Post-estratificado (4) | Post-estratificado colapsado |
|---|---:|---:|---:|---:|
| 2013→2014 | 60,09 % | 61,17 % | 62,19 % | 62,19 % |
| 2014→2015 | 82,81 % | 82,66 % | 82,66 % | 82,66 % |
| 2015→2017 | 81,23 % | 80,74 % | 80,09 % | 80,66 % |
| 2017→2019 | 76,87 % | 76,50 % | 76,44 % | 76,64 % |
| 2019→2021 | 79,51 % | 80,21 % | 80,35 % | 80,41 % |
| 2013→2021 | 56,18 % | 56,63 % | 57,31 % | 57,31 % |

| Par | Error MAS | Error PS | Error PS colapsado | Ganancia de varianza (PS) | Ganancia teórica que predijo el EDA |
|---|---:|---:|---:|---:|---:|
| 2013→2014 | +1,073 pp | +2,099 pp | +2,099 pp | 16,6 % | 12,0 % |
| 2014→2015 | -0,158 pp | -0,155 pp | -0,155 pp | 0,6 % | 1,2 % |
| 2015→2017 | -0,490 pp | -1,139 pp | -0,575 pp | 4,8 % | 6,4 % |
| 2017→2019 | -0,371 pp | -0,427 pp | -0,232 pp | 8,1 % | 8,7 % |
| 2019→2021 | +0,694 pp | +0,834 pp | +0,895 pp | 7,1 % | 7,1 % |
| 2013→2021 | +0,459 pp | +1,133 pp | +1,133 pp | 6,4 % | 4,9 % |

La última columna es la comprobación de que el EDA sirvió: la ganancia de varianza que la post-estratificación logra en la muestra sigue de cerca a la que el EDA había predicho con el censo (por ejemplo, 7,1 % previsto frente a 7,1 % logrado en 2019→2021). Es decir: **la decisión de estratificar por categoría se tomó con evidencia previa y el resultado la confirmó**.

### 4.4 ¿La post-estratificación acerca las estimaciones al censo?

**No de forma sistemática.** El MAS es el más cercano al censo en 4 de los 6 pares. La post-estratificación reduce la varianza entre 0,6 % y 16,6 %, pero no reduce el error frente al valor poblacional; en los pares 2013→2014, 2015→2017 y 2013→2021 incluso lo aumenta.

La explicación es la que ya anticipaba el EDA: **la muestra del MAS ya estaba equilibrada**. La categoría explica solo ~7 % de la varianza de la retención, de modo que el desbalance que la post-estratificación podría corregir es pequeño, y lo que queda es ruido de muestreo. Dicho con precisión: la post-estratificación **no corrige un sesgo, compra precisión**.

## 5. Estimador GREG (model-assisted)

### 5.1 Modelos ajustados

Para cada variable de interés se ajustó un modelo con variables auxiliares **conocidas en toda la población**:

| Variable de interés | Modelo | Auxiliares |
|---|---|---|
| Retención (sí/no) | Logístico | categoría, género, gran área, departamento de residencia |
| Edad | Lineal | género, gran área, región de residencia |
| Ascenso de categoría | Ordinal (odds proporcionales, 3 niveles) y logístico (binario) | categoría en t₁, género, gran área |

El modelo ordinal se ajustó por máxima verosimilitud implementada directamente (con penalización L2 para estabilizar), porque el entorno no dispone de `statsmodels`. Del modelo ordinal se deriva `P(asciende)` por persona y se usa como modelo de trabajo del GREG, igual que con el logístico.

### 5.2 Resultados

| Par | Censo | MAS | GREG lineal | GREG logístico |
|---|---:|---:|---:|---:|
| 2013→2014 | 60,09 % | 61,17 % | 61,65 % | 61,80 % |
| 2014→2015 | 82,81 % | 82,66 % | 82,72 % | 82,76 % |
| 2015→2017 | 81,23 % | 80,74 % | 79,97 % | 80,53 % |
| 2017→2019 | 76,87 % | 76,50 % | 76,78 % | 76,59 % |
| 2019→2021 | 79,51 % | 80,21 % | 80,42 % | 80,35 % |
| 2013→2021 | 56,18 % | 56,63 % | 56,95 % | 57,14 % |

| Par | Ganancia var. GREG-lineal | Ganancia var. GREG-logit | R² en la muestra (lineal) |
|---|---:|---:|---:|
| 2013→2014 | 20,6 % | 20,1 % | 0,2056 |
| 2014→2015 | 7,6 % | 5,9 % | 0,0762 |
| 2015→2017 | 10,6 % | 9,3 % | 0,1063 |
| 2017→2019 | 10,0 % | 9,1 % | 0,1002 |
| 2019→2021 | 8,9 % | 8,5 % | 0,0885 |
| 2013→2021 | 18,5 % | 17,5 % | 0,1850 |

**Edad** (población: personas en su última convocatoria; censo = 45,5190 años):

| Estimador | Valor | Error estándar | IC 95 % | Ganancia de varianza |
|---|---:|---:|---|---:|
| MAS | 45,1435 | 0,2096 | [44,733; 45,554] | 0,0 % |
| Post-estratificado | 45,2399 | 0,2043 | [44,839; 45,640] | 5,0 % |
| GREG lineal | 45,1528 | 0,2059 | [44,749; 45,556] | 3,5 % |

El modelo lineal de la edad explica poco (R² = 0,0351), coherente con el EDA: género, área y región apenas distinguen la edad. La ganancia de precisión es por tanto pequeña (3,5 %). Con las 46 edades mayores de 100 excluidas, el censo pasa a 45,3931 años y el MAS a 45,1435.

**Ascenso de categoría 2019→2021** (población: 13 355 personas presentes en ambas convocatorias; en el censo ascendieron 2 336, permanecieron 9 657 y descendieron 1 362):

| Estimador | Valor | Error estándar | Ganancia de varianza | Error vs censo |
|---|---:|---:|---:|---:|
| MAS | 18,73 % | 1,18 % | 0,0 % | +1,240 pp |
| Post-estratificado | 18,34 % | 1,12 % | 9,4 % | +0,847 pp |
| GREG lineal | 18,26 % | 1,14 % | 7,3 % | +0,769 pp |
| GREG logístico | 18,37 % | 1,14 % | 7,3 % | +0,881 pp |
| GREG con modelo ordinal | 18,41 % | 1,15 % | 5,0 % | +0,920 pp |

Aquí sí ocurre lo que la teoría predice: **los tres estimadores asistidos por modelo reducen el error** frente al MAS (de +1,240 pp a +0,881 pp con el logístico), y además reducen la varianza. El motivo es que en este caso sí había desbalance: el MAS sobrerrepresentó a quienes ascendieron, y tanto la reponderación como el modelo lo corrigen.

## 6. Comparación de los tres estimadores

### 6.1 Comprobación interna: la post-estratificación es un caso particular de GREG

Si el modelo auxiliar del GREG se satura en los post-estratos, los dos estimadores deben **coincidir exactamente**. Se verificó con los datos reales (retención 2019→2021, post-estratos = categoría):

| Estimador | Valor |
|---|---:|
| GREG con modelo saturado en categoría | 80,347473 % |
| Post-estratificado por categoría | 80,347473 % |
| Diferencia absoluta | **1.11e-16** pp (ruido de coma flotante) |

No es un detalle decorativo: confirma que las dos implementaciones son coherentes entre sí y con la teoría (Särndal et al., 1992), y que cualquier diferencia entre ellas proviene del modelo, no de un error de cálculo.

### 6.2 Tabla comparativa completa

| Parámetro | Censo | MAS [IC 95 %] | Post-estratificado [IC] | GREG [IC] | Estimador más cercano al censo |
|---|---:|---|---|---|---|
| Retención 2013→2014 | 60,09 % | 61,17 % [57,47; 64,86] | 62,19 % [58,82; 65,56] | 61,80 % [58,50; 65,10] | MAS |
| Retención 2014→2015 | 82,81 % | 82,66 % [79,84; 85,48] | 82,66 % [79,85; 85,47] | 82,76 % [80,02; 85,49] | GREG |
| Retención 2015→2017 | 81,23 % | 80,74 % [78,03; 83,45] | 80,09 % [77,45; 82,74] | 80,53 % [77,95; 83,11] | MAS |
| Retención 2017→2019 | 76,87 % | 76,50 % [73,95; 79,05] | 76,44 % [74,00; 78,89] | 76,59 % [74,16; 79,02] | GREG |
| Retención 2019→2021 | 79,51 % | 80,21 % [78,09; 82,33] | 80,35 % [78,31; 82,39] | 80,35 % [78,32; 82,38] | MAS |
| Retención 2013→2021 | 56,18 % | 56,63 % [52,88; 60,39] | 57,31 % [53,67; 60,94] | 57,14 % [53,72; 60,55] | MAS |
| Edad media | 45,519 | 45,144 [44,73; 45,55] | 45,240 [44,84; 45,64] | 45,153 [44,75; 45,56] | Post-estrat. |
| Ascenso 2019→2021 | 17,49 % | 18,73 % [16,42; 21,05] | 18,34 % [16,13; 20,54] | 18,37 % [16,14; 20,60] | Post-estrat. |

### 6.3 Ganancia de precisión

| Parámetro | Reducción de varianza con post-estratificación | Con GREG |
|---|---:|---:|
| Retención 2013→2014 | 16,6 % | 20,1 % |
| Retención 2014→2015 | 0,6 % | 5,9 % |
| Retención 2015→2017 | 4,8 % | 9,3 % |
| Retención 2017→2019 | 8,1 % | 9,1 % |
| Retención 2019→2021 | 7,1 % | 8,5 % |
| Retención 2013→2021 | 6,4 % | 17,5 % |
| Edad media | 5,0 % | 3,5 % |
| Ascenso 2019→2021 | 9,4 % | 7,3 % |

### 6.4 Una advertencia metodológica importante

La columna «estimador más cercano al censo» se calcula comparando cada estimación con el valor poblacional verdadero. Es una comprobación valiosa **porque aquí el censo se conoce**, y sirve para verificar que las implementaciones no están sesgadas. Pero **no** es un criterio válido para elegir estimador: el error realizado es **una sola realización** de la muestra. Si se hubiera sorteado otra semilla, el orden podría cambiar. El criterio correcto para elegir es la **varianza** (la ganancia de precisión de la sección 6.3), que sí es una propiedad del estimador y no del sorteo concreto. Por eso el documento reporta las dos cosas por separado y no elige por el error observado.

## 7. Conclusión: qué se reporta y por qué

1. **Las cifras oficiales del análisis longitudinal son las del censo.** La base completa está disponible, así que no hay razón para reportar una estimación cuando se puede reportar el parámetro. Toda la maquinaria de muestreo de este documento tiene un valor **metodológico y de verificación**, no de sustitución.
2. **Si hubiera que estimar a partir de la muestra, el MAS simple ya sería suficiente y es el que menos supuestos exige.** Es insesgado por diseño y en esta aplicación resultó el más cercano al censo en 4 de los 6 pares, precisamente porque la muestra quedó equilibrada.
3. **La post-estratificación por categoría no corrige sesgo: compra precisión.** Reduce la varianza entre 0,6 % y 16,6 % según el par, sin mejorar de forma sistemática el error frente al censo. Se justifica cuando el objetivo es estrechar intervalos, no cuando se sospecha un desbalance.
4. **El GREG es el estimador recomendado si hay que estimar**, porque domina en varianza (hasta 20,1 % de reducción) y porque su validez no depende de que el modelo esté bien especificado: es la propiedad *model-assisted* de Kalton (2002) y del FCSM (2003). Además resuelve el problema del estrato pequeño, que es el punto débil de la post-estratificación en este corpus.
5. **El estrato pequeño se declara, no se esconde.** Con Emérito en 1, 7 y 3 observaciones según el par, la post-estratificación de 4 estratos incumple la condición de tamaño mínimo de Cochran (1977). La versión colapsada (Sénior + Emérito) la cumple y se reporta junto a la otra, y el GREG ofrece una tercera vía que no depende de que cada celda sea grande.

**Recomendación operativa.** Reportar el censo; documentar el MAS como el diseño de referencia y su validación (Anexo A de `analisis_longitudinal.md`); y usar GREG —no la post-estratificación de 4 estratos— si en algún momento hubiera que producir una estimación muestral con intervalos más estrechos.

## Referencias bibliográficas

- Cochran, W. G. (1977). *Sampling Techniques* (3rd ed.). John Wiley & Sons. — Formulación y ajuste del tamaño de muestra; post-estratificación (§5A); recomendación de 4 a 6 estratos con ~20 observaciones por estrato (pp. 132-134).
- Lohr, S. L. (2010). *Sampling: Design and Analysis* (2nd ed.). Brooks/Cole. — Muestreo aleatorio simple, estimación de proporciones y post-estratificación (§7.6).
- Särndal, C.-E., Swensson, B., & Wretman, J. (1992). *Model Assisted Survey Sampling*. Springer-Verlag. — Estimador GREG y su forma de diferencia (§6.4-6.5); la post-estratificación como caso particular con modelo saturado.
- Kalton, G. (2002). Models in the practice of survey sampling. *International Statistical Review*, 70(2), 175-192. — Uso de modelos en modo asistido, de forma que la validez de las estimaciones no dependa de los supuestos del modelo.
- FCSM (2003). *Glossary of Terms*. Federal Committee on Statistical Methodology. — Definición y motivación del estimador GREG como *model-assisted*.
- StatsRef.com (s. f.). *Exploratory data analysis*. En *Statistics Reference Online*. — «EDA ... is typically the first stage of any such analysis»; síntesis de la posición de Cochran (1977) sobre el trabajo exploratorio previo.
- OhioLINK ETD Center. *Post-stratification variance*. — La distribución asintótica del estimador post-estratificado coincide con la del estimador de un muestreo estratificado con asignación proporcional (Cochran, 1977; Lohr, 1999).
- Canadian Journal of Forest Research (2019). *Efficiency of post-stratification for a large-scale forest inventory*. — Recomendación de Cochran (1977, pp. 132-134) sobre el número de estratos y el tamaño mínimo por estrato.

## Anexo: artefactos y reproducibilidad

| Artefacto | Contenido |
|---|---|
| `src/eda_longitudinal.py` | EDA completo (Parte 1) |
| `data/memoria/eda_resultados.json` | Cifras del EDA |
| `data/memoria/eda/` | 6 gráficas del EDA |
| `src/estimadores_longitudinal.py` | Post-estratificación y GREG (Partes 2-3) |
| `data/memoria/estimadores_resultados.json` | Cifras de los estimadores |
| `src/generar_metodologia_muestreo.py` | Genera este documento |

```bash
python src/eda_longitudinal.py
python src/estimadores_longitudinal.py
python src/generar_metodologia_muestreo.py
```

El muestreo **no se rehizo**: se reutilizan los identificadores de `data/memoria/muestra_ids.csv` (semilla 2026).

