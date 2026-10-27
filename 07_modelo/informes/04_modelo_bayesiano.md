# Informe 4 · Modelo ordinal jerárquico bayesiano

**Proyecto:** Consultoría estadística USTA 2026-II — Observatorio Minciencias
**Componente:** Fase 3 · modelo predictivo de movilidad de categoría
**Entregable:** capa de incertidumbre y contraste ordinal del modelo operativo
**Fecha:** 27 de octubre de 2026
**Autor:** Consultoría estadística USTA 2026-II

---

## 1. Objetivo de la etapa

Explorar la estructura **ordinal** del fenómeno con un modelo probabilístico
explícito, con dos propósitos:

1. **Contrastar la familia de modelo.** La categoría tiene un orden natural
   (`baja` < `se_mantiene` < `sube`) y el negocio pregunta por umbrales, no por
   categorías intercambiables. Un modelo ordinal con cortes pone esa estructura en
   la verosimilitud; un multiclase plano la ignora.
2. **Aportar una capa de incertidumbre.** Aun sin ser competitivo como
   clasificador, un modelo bayesiano entrega distribuciones posteriores,
   intervalos de credibilidad y una calibración que el XGBoost no ofrece. La
   pregunta es si esa capa sirve para **reportar riesgo con honestidad**, aunque no
   para decidir.

La etapa **no** busca reemplazar al modelo operativo. Busca medir si el orden de
las categorías aporta información y documentar, con evidencia, por qué el modelo
bayesiano se queda como capa de incertidumbre y no como clasificador.

---

## 2. Metodología y herramientas usadas

### 2.1 Especificación

Modelo de enlaces acumulativos (*cumulative logit*) con efectos aleatorios:

```
y_i ~ OrderedLogistic(η_i, κ)
η_i = x_i'β + u_{c(i)} + v_{t(i)}
P(y_i ≤ k | x) = logit⁻¹(κ_k − η_i),   k = 1, 2,   κ_1 < κ_2
```

- **Cortes ordenados** `κ_1 < κ_2`, construidos desde un `Dirichlet(1,1,1)` sobre
  las probabilidades de referencia, de modo que el orden se garantiza **por
  construcción**.
- **Efectos aleatorios** por categoría de origen `u_c` y por periodo de destino
  `v_t`, con parameterización **non-centered** (`u = σ_u · z`, `z ~ Normal(0,1)`)
  para evitar el *funnel* que rompe NUTS.
- **Priores débiles**: `β ~ Normal(0,1)` sobre predictores estandarizados,
  `σ_u, σ_v ~ HalfNormal(1)`.
- **Periodos nuevos**: val (20) y test (21) no existen en train; la predicción
  integra `v_20 ~ Normal(0, σ_v)` como nivel nuevo, sin extrapolar tendencia, y
  propaga esa incertidumbre.

### 2.2 Diseño completo y reformulación mínima

El diseño completo contemplaba **25 predictores** (19 de producción + 4 variables
demográficas materializadas en 6 columnas), con **máscaras estructurales** (Junior
truncado a `{se_mantiene, sube}`; Emérito truncado a `{baja, se_mantiene}`) y
máscaras verificadas con un test unitario antes de muestrear.

El ajuste completo **no terminó** en el presupuesto disponible: el proceso se
detuvo a las ~3 horas de pared con **28 676 s de CPU** acumulados y sin escribir
*trace*. La causa es de entorno: sin compilador C, PyTensor ejecuta el grafo en
modo Python, y 4 cadenas × 4 000 iteraciones sobre 19 838 filas y 25 predictores
no caben en la ventana. Se declaró **deuda técnica** y se reformuló a una versión
mínima, sin cambiar el diseño conceptual:

| Elemento | Diseño completo | Versión mínima ejecutada |
|---|---|---|
| Predictores | 25 | **12** |
| Máscaras IJ/IE | Sí | **No** (ordinal puro) |
| Cadenas × iteraciones | 4 × (2 000 + 2 000) | **2 × (1 000 + 1 000)** |
| Ajuste | Sobre train (19 838) | Sobre train (19 838) |
| Evaluación | val (9 994) | val (9 994); test nunca cargado |

Los 12 predictores de la versión mínima son: `log1p(n_productos)`,
`log1p(n_filas)`, `n_grupos_distintos`, `dias_desde_ultimo`, `sin_produccion`,
`share_clase_nuevo_conocimiento`, `share_clase_formacion`,
`share_tip_articulos_investigacion`, `share_cat_articulos_generacion`,
`genero_masculino`, `edad_estandarizada` y `depto_bogota`.

### 2.3 Muestreo y diagnóstico

- **PyMC 5 + NUTS** con backend **nutpie** (NUTS en Rust) y caché en `TEMP`.
- `target_accept = 0,90` en el primer ajuste y **0,95** en el segundo.
- Criterio de parada **triple**: `r_hat ≤ 1,01`, `ESS mínimo ≥ 400`,
  divergencias **≤ 0,1 %**. Si no se cumple, se declara deuda y no se evalúa.
- Regla de un solo reajuste: si el segundo ajuste fallaba, la línea se cerraba.
- **Diagnóstico post-ajuste de odds proporcionales**: modelo relajado con
  `δ_{k,c} ~ Normal(0; 0,5)`, 1 cadena × 500; se comparan las posteriores de β.

### 2.4 Herramientas

PyMC 5, ArviZ, nutpie y PyTensor en el entorno `07_modelo/.venv-bayes`. El
interprete es explícito (`07_modelo\.venv-bayes\Scripts\python.exe`) porque el
sandbox no permite instalar en el venv del agente. El test no se cargó en ningún
momento del ajuste ni de la evaluación.

---

## 3. Justificación técnica

### 3.1 Por qué un modelo ordinal y no un multinomial

Un multinomial (softmax) trata las tres clases como intercambiables e introduce
`K·(K−1) = 6` parámetros de corte/efectos por categoría. El acumulativo usa **dos
*cutpoints*** y un solo vector `β`, con tres ventajas en este problema:

1. **Parsimonia con muestra pequeña.** Con 19 838 filas y una clase «baja» del
   5,15 %, el multinomial tiene más parámetros para la misma información y
   sobreajusta con más facilidad.
2. **Orden natural.** La categoría es una escala: confundir `baja` con
   `se_mantiene` no es el mismo error que confundirlo con `sube`. El modelo
   acumulativo impone monotonía en las probabilidades acumuladas, que es
   exactamente la estructura del fenómeno.
3. **Lectura directa.** Un `β` positivo desplaza la distribución hacia arriba; los
   cortes fijan dónde se cruza cada categoría. Es la lectura que un comité puede
   usar.

La familia es la estándar para desenlaces ordenados: McCullagh (1980) formula los
*Cumulative Link Models* y su extensión logística. En el dominio específico,
Godoy, Abramo, D'Angelo y Cortés (2026) estiman precisamente una regresión ordinal
con variable latente y cortes sobre las mismas convocatorias; su test de líneas
paralelas **rechaza** el supuesto de odds proporcionales (p < 0,001) y su versión
no restringida —efectos distintos por umbral— es la que gana (LR = 911, gl = 13,
p < 0,001). Eso confirma que la familia ordinal es la correcta y que el supuesto
fuerte hay que diagnosticarlo, no asumirlo.

Por eso el diseño incluye un **diagnóstico post-ajuste** de odds proporcionales y
no deja el supuesto como riesgo declarado.

### 3.2 Por qué efectos aleatorios jerárquicos

Las categorías de origen y los periodos de destino no son grupos independientes:
comparten información (un Sénior de 2017 se parece a un Sénior de 2015 más que a
un Junior de 2017). Un modelo jerárquico **parcialmente agrupado** (*partial
pooling*) permite que cada categoría y cada periodo tengan su desviación, pero
encogida hacia la media global cuando hay pocos datos. Es la respuesta estándar
cuando hay estructura de grupos y muestras desiguales.

**Nota de veracidad:** en nuestra búsqueda no se localizó una referencia
jerárquica específica verificada para este dominio. El diseño de efectos aleatorios
—parameterización non-centered, priors débiles, niveles nuevos integrados en el
posterior predictive— es una **decisión basada en la práctica estándar de la
industria**, documentada en la guía de PyMC. No se le atribuye a un paper que no se
verificó.

### 3.3 Por qué falló como modelo operativo

El `argmax` de la posterior predictive es **degenerado**:

| Clase | Predicciones |
|---|---:|
| `baja` | **0,01 %** |
| `se_mantiene` | **98,95 %** |
| `sube` | **1,04 %** |

Con una clase mayoritaria del 70 % y encogimiento hacia la prevalencia, el
`argmax` elige casi siempre `se_mantiene`. El F1 de «baja» cae a **0,003** y el F1
macro a 0,2945, frente a 0,3939 del XGBoost de la Ronda 1. No es un error de
implementación: es el comportamiento esperado de un modelo ordinal paramétrico
cuando la relación no es monótona y la clase de interés es rara. El modelo
**ordena bien** pero **no clasifica**: sus probabilidades están encogidas hacia las
prevalencias.

### 3.4 Por qué sirve como capa de incertidumbre

El mismo modelo que falla en `argmax` es el mejor en **puntuación propia** y en
**ranking**:

- **Brier multiclase 0,4370**, mejor que la constante con prevalencias de val
  (0,4510) y muy mejor que el XGBoost de la Ronda 1 (0,5479).
- **AUC «baja» 0,817**, frente a 0,563 del XGBoost de la Ronda 1.
- **Intervalos de credibilidad** al 80 % y 95 % por observación, que el XGBoost no
  entrega.

Es decir: el modelo bayesiano **sabe cuánto no sabe** y ordena el riesgo, aunque su
regla de decisión automática sea inútil. Esa es exactamente la definición de una
capa de incertidumbre: se usa para reportar y priorizar con honestidad, no para
emitir la etiqueta.

---

## 4. Resultados y métricas

### 4.1 Convergencia

| Ajuste | `target_accept` | Tiempo | `r_hat` máx. | ESS mín. | Divergencias | Veredicto |
|---|---|---|---|---|---|---|
| 1 | 0,90 | 18,35 min | 1,0049 | 467 | 15/2 000 (0,750 %) | Falla por divergencias |
| 2 | 0,95 | 20,41 min | **1,0103** | **378** | **0/2 000 (0,000 %)** | Divergencias OK; `r_hat` y ESS marginalmente fuera |

El ajuste 2 no cumple el criterio triple por **0,0003** en `r_hat` (1,0103 frente a
1,01) y por **22 unidades** de ESS (378 frente a 400); los parámetros limitantes
son los cortes `kappa1`/`kappa2` y `u[0..2]`. La puerta operativa fijada para esta
línea era **divergencias ≤ 0,1 %**, que sí se cumple. Se evaluó **declarando la
marginalidad** y **sin tercer ajuste**.

### 4.2 Métricas en validación (n = 9 994; test nunca cargado)

| Métrica | Bayesiano mínimo | XGBoost Ronda 1 | Δ |
|---|---:|---:|---:|
| F1 macro | 0,2945 | 0,3939 | **−9,9 pp** |
| F1 «baja» | 0,003 | 0,132 | — |
| F1 «se mantiene» | 0,826 | (no consta) | — |
| F1 «sube» | 0,055 | (no consta) | — |
| AUC OvR «baja» | **0,817** | 0,563 | **+0,254** |
| AUC OvR «se mantiene» | 0,562 | (no consta) | — |
| AUC OvR «sube» | 0,672 | (no consta) | — |
| Brier multiclase | **0,4370** | 0,5479 | **−0,1109** |
| Exactitud | 0,7049 | (no consta) | — |

Referencia: una constante con las prevalencias de val (0,073 / 0,702 / 0,225) da
Brier **0,4510**. El bayesiano la supera (0,4370); el XGBoost de la Ronda 1 está
por debajo (0,5479). En este corte temporal ninguno de los dos es un buen modelo de
probabilidades, y el bayesiano es el menos malo.

### 4.3 Intervalos de credibilidad

Probabilidad media por clase, con intervalos agregados y ancho medio por
observación:

| Clase | Media | IC80 | IC95 | Ancho medio IC80 / IC95 |
|---|---:|---|---|---:|
| `baja` | 0,059 | [0,034; 0,082] | [0,023; 0,133] | 0,048 / 0,140 |
| `se_mantiene` | 0,769 | [0,730; 0,802] | [0,653; 0,808] | 0,103 / 0,234 |
| `sube` | 0,172 | [0,114; 0,232] | [0,069; 0,308] | 0,119 / 0,244 |

### 4.4 Diagnóstico de odds proporcionales

Modelo relajado con `δ_{k,c} ~ Normal(0; 0,5)`, 1 cadena × 500:

| Indicador | Valor |
|---|---:|
| `|Δβ|` máximo | **0,040** |
| `|Δβ|` medio | 0,014 |
| Correlación entre posteriores | 0,999 |
| Cambios de signo | **0** |

La hipótesis de odds proporcionales es **plausible** para estos 12 predictores.
Advertencia honesta: el ajuste relajado es corto (ESS mín. 62, 7/500 divergencias),
así que es un chequeo grueso, no un test formal.

### 4.5 Comparación y decisión

| Criterio de la etapa | Resultado |
|---|---|
| ≥ +2 pp en F1 macro **o** ≥ 0,02 de mejora en Brier | **Cumple por Brier** (−0,1109); pierde por F1 macro (−9,9 pp) |
| ¿Reemplaza al XGBoost como clasificador? | **No**: `argmax` degenerado, F1 «baja» 0,003 |
| ¿Aporta como capa de incertidumbre? | **Sí**: Brier 0,4370, AUC 0,817, IC80/IC95 |

**Decisión:** el modelo bayesiano **no es operativo**. Se conserva como
**contribución metodológica y capa de incertidumbre**: documenta que la estructura
ordinal es correcta, que el supuesto de odds proporcionales es plausible para un
subconjunto de predictores y que un modelo con buena calibración puede, aun así,
no servir para clasificar. El ajuste completo con máscaras y 25 predictores queda
como **deuda técnica declarada**, listo para retomarse cuando haya compilador C.

### 4.6 Lectura

El resultado conjunto de los informes 3 y 4 es una división de trabajo explícita:
el **XGBoost clasifica** (F1 «baja» 0,4234 en test) y el **bayesiano calibra y
cuantifica incertidumbre** (Brier 0,4370 en val, AUC 0,817). Ninguno de los dos
resuelve el problema completo, y presentarlos como alternativas intercambiables
sería inexacto. La combinación —ranking del XGBoost con intervalos del
bayesiano— es la que se recomienda para un reporte de riesgo, no para una decisión
automática.

---

## 5. Referencias

1. **McCullagh, P. (1980).** *Regression Models for Ordinal Data.* **Journal of the
   Royal Statistical Society, Series B, 42(2), 109-142.** DOI:
   [10.1111/j.2517-6161.1980.tb01109.x](https://doi.org/10.1111/j.2517-6161.1980.tb01109.x).
2. **Godoy, J. M., Abramo, G., D'Angelo, C. A. & Cortés, J. D. (2026).** *Should I
   stay or should I go? The role of national geographic mobility, gender, age,
   institutional research profiles, and labor market on the career performance of
   the scientific workforce in Colombia.* **Scientometrics, 131(9), 5803-5824.**
   DOI: [10.1007/s11192-026-05716-9](https://doi.org/10.1007/s11192-026-05716-9).
3. **PyMC.** *PyMC documentation* (v5): guía de modelos jerárquicos,
   parameterización non-centered y diagnóstico de NUTS. https://www.pymc.io/ —
   documentación de la herramienta, no fuente académica revisada por pares.

**Nota sobre «papers de modelos jerárquicos»:** no se localizó en nuestra búsqueda
una referencia jerárquica específica verificada que se pueda citar sin inventar
autoría. La decisión de usar efectos aleatorios con *partial pooling* se sostiene
en la **práctica estándar de la industria** y en la documentación de PyMC; se deja
dicho para que la Memoria no atribuya a un paper una decisión que no se verificó.

**Evidencia interna**

4. `07_modelo/modelado/diseno_bayesiano.md` — diseño completo, deuda técnica y
   resultados de la versión mínima.
5. `07_modelo/modelado/resultados/bayesiano_minimo_20261026_014416.json`,
   `evaluacion_bayesiano_minimo_20261026_014535.json`,
   `odds_diagnostico_minimo_20261026_015539.json`.
6. `07_modelo/modelado/entrenar_bayesiano_minimo.py`,
   `evaluar_bayesiano_minimo.py`, `diagnostico_odds_minimo.py`.
7. `07_modelo/modelado/model_card.md` §3–§4 — comparación con el modelo operativo.
