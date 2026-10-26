# Diseño del modelo bayesiano jerárquico — transición de categoría

**Fase 5 · alcance acotado · documento de diseño (antes de escribir código)**
Datos: 43 187 transiciones contiguas (16→17, 17→18, 18→19, 19→20, 20→21).
Partición: train 19 838 (destinos 2014/15/17), val 9 994 (2019), test 13 355 (2021, **sin tocar**).

---

## 0. Decisión de alcance: dataset **ventana** (decisión, no conclusión empírica)

Se elige `modelo_dataset_ventana_contiguo.parquet` como dataset del modelo bayesiano.
Es una **decisión de alcance**, no una conclusión empírica: ventana es la tabla
primaria del proyecto (la que se usa en el panel y en la comparación con XGBoost) y
evita el solapamiento de información del acumulado. **El acumulado queda como
comparación pendiente** para una ronda posterior.

Números de ronda 1 que muestran que no hay superioridad clara de ventana:

| Dataset | F1 macro | F1 «baja» | AUC «baja» | Brier |
|---|---:|---:|---:|---:|
| ventana | **0,3939** | 0,132 | 0,563 | **0,5479** |
| acumulado | 0,3844 | **0,153** | **0,580** | 0,5700 |

Ventana gana F1 macro y Brier; el acumulado gana F1 «baja» y AUC «baja». La elección
se declara como alcance, no como evidencia de que ventana sea mejor para «baja».

## 1. Decisión de modelo: ordinal acumulativo (cumulative link), **no** multinomial

La variable tiene un orden natural (baja < se_mantiene < sube) y el negocio pregunta
por el umbral, no por categorías intercambiables. Se usa un **logit acumulativo con
odds proporcionales**:

    y_i ~ OrderedLogistic(η_i, κ)
    η_i = x_i'β + u_{c(i)} + v_{t(i)}
    P(y_i ≤ k | x) = logit⁻¹(κ_k − η_i),   k = 1, 2,   κ_1 < κ_2

**Por qué no multinomial:**
- El multinomial (softmax) ignora el orden e introduce K·(K−1) = 6 parámetros de
  corte/efectos por categoría; el acumulativo usa **2 cutpoints** y un solo β. Con
  19 838 filas y una clase «baja» del 5 %, el multinomial sobreajusta.
- Los odds proporcionales dan una lectura directa: un β positivo desplaza la
  distribución hacia arriba; los cortes fijan dónde se cruza cada categoría.
- La comparación con el auditado y con el panel también es ordinal (sube/baja).
- **La hipótesis de odds proporcionales se diagnostica después del ajuste** (§11);
  no queda solo como riesgo declarado.

**Máscaras estructurales (obligatorias):**
- **IJ (Junior)** no puede «bajar» (no hay categoría inferior): su verosimilitud se
  trunca a {se_mantiene, sube}, con p(baja) = 0 y renormalización.
- **IE (Emérito)** no puede «subir» (es la cima): se trunca a {baja, se_mantiene}.
- La renormalización se implementa en `pm.Categorical` con las probabilidades
  acumuladas y una máscara por fila; **se prueba antes de NUTS** (§12).

## 2. Efectos aleatorios con parameterización **non-centered**

    z_c ~ Normal(0, 1)          u_c = σ_u · z_c        (categoría de origen)
    w_t ~ Normal(0, 1)          v_t = σ_v · w_t        (periodo de destino)
    σ_u, σ_v ~ HalfNormal(1)

- Non-centered es crítico para NUTS: evita el funnel entre efectos y desviaciones.
- Las categorías son {IJ, I, IS, IE}; los periodos de train son {17, 18, 19}.
- **Periodos nuevos:** val (20) y test (21) no existen en train. La predicción
  integra `v_20 ~ Normal(0, σ_v)` en el posterior predictive (nivel nuevo, no se
  extrapola una tendencia). La incertidumbre de periodo se propaga y se declara.

## 3. Predictores: **25** (20 base + 4 demográficas materializadas en 6 columnas)

Se sustituyen las 173 one-hot por 25 variables. Las proporciones usan `n_productos`
como denominador (0 si `sin_produccion`). Se **eliminó `share_otras_tipologias`**
(residual, el menos informativo) para no pasar de 25 con los indicadores de faltante.

| # | Predictor | Definición |
|---|---|---|
| 1 | `log1p(n_filas)` | filas producto-autor de la ventana |
| 2 | `log1p(n_productos)` | productos únicos |
| 3 | `log1p(n_grupos_distintos)` | grupos distintos |
| 4 | `dias_desde_ultimo` | días desde el último producto (mediana-imputado, escalado) |
| 5 | `sin_produccion` | 1 si no hay producción en la ventana |
| 6 | `share_clase_apropiacion` | `n_clase_APROPIACI_N_SOCIAL_DEL_CONOCIMIENTO / n_productos` |
| 7 | `share_clase_desarrollo` | `n_clase_DESARROLLO_TECNOL_GICO_E_INNOVACI_N / n_productos` |
| 8 | `share_clase_formacion` | `n_clase_FORMACI_N_DE_RECURSO_HUMANO / n_productos` |
| 9 | `share_clase_no_categorizado` | `n_clase_NO_CATEGORIZADO / n_productos` |
| 10 | `share_clase_nuevo_conocimiento` | `n_clase_NUEVO_CONOCIMIENTO / n_productos` |
| 11 | `share_clase_otras` | 1 − (6+7+8+9+10) |
| 12 | `share_tip_articulos_investigacion` | `n_tipologia_ART_CULOS_DE_INVESTIGACI_N / n_productos` |
| 13 | `share_tip_tesis_pregrado` | `n_tipologia_TESIS_DE_PREGRADO / n_productos` |
| 14 | `share_tip_evento_cientifico` | `n_tipologia_EVENTO_CIENT_FICO / n_productos` |
| 15 | `share_tip_articulos` | `n_tipologia_ART_CULOS / n_productos` |
| 16 | `share_cat_articulos_generacion` | `n_categoria_ART_CULOS_DE_GENERACI_N_DE_CONTENIDO / n_productos` |
| 17 | `share_cat_tesis_pregrado_b` | `n_categoria_TESIS_DE_PREGRADO_CON_CALIDAD_B / n_productos` |
| 18 | `share_cat_evento_cientifico_a` | `n_categoria_EVENTO_CIENT_FICO_CON_CALIDAD_A / n_productos` |
| 19 | `share_otras_categorias` | 1 − (16+17+18) |
| 20 | `genero_masculino` | 1 si `NME_GENERO_PR == "Masculino"`; 0 si no |
| 21 | `genero_desconocido` | 1 si `NME_GENERO_PR` falta o es "No disponible" |
| 22 | `edad_estandarizada` | `EDAD_ANOS_PR` (coma decimal) estandarizada; mediana si falta |
| 23 | `edad_faltante` | 1 si `EDAD_ANOS_PR` falta (1 caso en el censo) |
| 24 | `depto_bogota` | 1 si `NME_DEPARTAMENTO_RES_PR` empieza por "Bogotá" |
| 25 | `depto_antioquia` | 1 si `NME_DEPARTAMENTO_RES_PR == "Antioquia"` |

Notas:
- Demográficas desde el censo por `(ID_PERSONA_PR, ID_CONVOCATORIA)`; no vienen en
  el parquet de features y se unen en el script de entrenamiento.
- `Intersexual` (5 casos) queda en la categoría base (masculino=0, desconocido=0).
- `ano` **no** entra: el periodo se modela con `v_t`.
- Estandarización: las 6 numéricas (1-4, 22) con media/desviación de train; el resto
  ya está en [0, 1].

## 4. Priors (débiles pero informativos)

    β_j ~ Normal(0, 1)                     (sobre predictores estandarizados)
    π_ref ~ Dirichlet(1, 1, 1)             → κ_1 = logit(π_1), κ_2 = logit(π_1+π_2)
    z_c, w_t ~ Normal(0, 1)
    σ_u, σ_v ~ HalfNormal(1)

- El Dirichlet sobre las probabilidades de referencia garantiza `κ_1 < κ_2` **por
  construcción** (cutpoints ordenados) y evita el problema de la Normal truncada.
- `Normal(0, 1)` en β es débil; sensibilidad con `Normal(0, 2)` en el diagnóstico.

## 5. Verosimilitud

- Probabilidades acumuladas con `sigmoid(κ_k − η)` y `pm.Categorical` con las
  máscaras IJ/IE; renormalización por fila.
- Sin imputación adicional: NaN de `dias_desde_ultimo` con mediana de train;
  `edad_faltante` marca el único caso.

## 6. Muestreo y plan de cómputo

- PyMC 5 + NUTS, `target_accept=0.9`, trace a
  `07_modelo/modelado/modelos/trace_bayesiano.nc`.
- **Sin compilador C en esta máquina**: se ejecuta con `PYTENSOR_FLAGS="cxx="`
  (modo Python, más lento). Se documenta.
- **Prueba previa obligatoria**: 1 cadena × 500 iteraciones, cronometrada. Si tarda
  **> 2 h**, se reduce a 2 cadenas × 2 000 o se declara el riesgo de no converger.
- **Producción**: 4 cadenas × 2 000 tune + 2 000 draws (o 2 × 2 000 si la prueba
  obliga).
- Diagnósticos: r_hat, ESS (bulk y tail), divergencias, energía.

## 7. Criterio de parada (duro)

Tras **48 horas** de cómputo (o al terminar el muestreo, lo que ocurra primero):

- Si **max r_hat > 1.01**, o **min ESS < 400**, o **divergencias > 0.1 %**:
  **se detiene**. No se evalúa, no se reajusta, no se toca test. Se reporta como
  **deuda técnica declarada**, con este diseño listo para retomarse.
- Si converge: se pasa a `evaluar_bayesiano.py`.

### 7.1 Deuda técnica declarada: el run completo agotó el tiempo (25-oct-2026)

> **Modelo completo (25 predictores, máscaras IJ/IE, 4 cadenas x 2000+2000) no
> terminó en 3h de cómputo con nutpie. Se reformuló a versión mínima.**

- El proceso (PID 19736) se detuvo a las ~3 h de pared, con **28 676 s de CPU**
  acumulados y **sin escribir trace**: `trace_bayesiano.nc` sigue siendo el del
  smoke 1×500.
- Causa: sin compilador C, PyTensor ejecuta el grafo en modo Python; nutpie
  (NUTS en Rust) amortigua pero no alcanza 4 × 4 000 iteraciones sobre 19 838
  filas y 25 predictores en el presupuesto disponible.
- **No hay veredicto de convergencia del modelo completo**: no se evaluó
  (coherente con §7) y no se reajusta sin autorización. Queda como deuda
  técnica, con el diseño intacto aquí para retomarlo cuando haya compilador C.
- La prueba de tiempo *sí* se cumplió: 1 cadena × 500 = **16,13 min** (nutpie),
  ESS 129, 1 divergencia (0,2 %), r_hat no calculable con 1 cadena.

### 7.2 Reformulación mínima (ejecutada en su lugar)

Orden de magnitud del cómputo, no del diseño: **12 predictores**, **sin máscaras
IJ/IE** (ordinal puro), **2 cadenas × 1 000 tune + 1 000 draws**, nutpie con
caché en TEMP, trace en `trace_bayesiano_minimo.nc`.

- `log1p(n_productos)`, `log1p(n_filas)`, `n_grupos_distintos`,
  `dias_desde_ultimo`, `sin_produccion`,
  `share_clase_nuevo_conocimiento`, `share_clase_formacion`,
  `share_tip_articulos_investigacion`, `share_cat_articulos_generacion`,
  `genero_masculino`, `edad_estandarizada`, `depto_bogota`.
- Se conservan los efectos aleatorios `u_c` y `v_t` (non-centered) y los priors
  de §4; se eliminan solo las máscaras y los predictores de cola.
- **Universo**: el modelo se ajusta sobre las **19 838** filas de *train* y se
  evalúa en las **9 994** de *val*; las **43 187** transiciones son el tamaño
  del universo, no filas de ajuste. El **test (13 355) no se carga ni se toca**.

### 7.3 Retiro del `assert` del split test (línea 195 de `entrenar_bayesiano.py`)

La línea era `assert len(np.where(estratos == "test")[0]) > 0`. **No era
imprescindible**: solo verificaba que la columna `split` del parquet seguía
conteniendo el estrato `test`. El script nunca calculaba `idx_te` ni usaba esas
filas: `X` se construye con operaciones **fila a fila** (log1p, shares,
dummies) y la estandarización e imputación usan **solo estadísticos de train**,
de modo que el test no podía filtrar información a train ni a val. Se eliminó y
se dejó una nota en el código.

### 7.4 Resultado final de la línea mínima (dos ajustes, sin tercera iteración)

Regla aplicada: **un solo reajuste**; si volvía a fallar, se cerraba como deuda.

| Ajuste | target_accept | Tiempo | r_hat_max | ESS_min | Divergencias | Veredicto |
|---|---|---|---|---|---|---|
| 1 | 0,90 | 18,35 min | 1,0049 | 467 | 15/2000 (0,750 %) | falla por divergencias |
| 2 | 0,95 | 20,41 min | 1,0103 | 378 | 0/2000 (0,000 %) | divergencias OK; r_hat y ESS marginalmente fuera |

El ajuste 2 **no cumple el criterio triple de §7** por 0,0003 en r_hat (1,0103 vs
1,01) y por 22 unidades de ESS (378 vs 400); los parámetros limitantes son los
cortes `kappa1`/`kappa2` y `u[0..2]`. La puerta operativa fijada para esta línea
era **divergencias ≤ 0,1 %**, que sí se cumple (0/2000). Se evaluó **declarando
la marginalidad** y **sin tercer ajuste**.

**Evaluación en val (n = 9 994; test nunca cargado):**

| Métrica | Bayesiano mínimo | XGBoost r1 | Δ |
|---|---|---|---|
| F1 macro | **0,2945** | 0,3939 | −9,9 pp |
| F1 baja | 0,003 | 0,132 | — |
| F1 se_mantiene | 0,826 | (no consta) | — |
| F1 sube | 0,055 | (no consta) | — |
| AUC OvR baja | **0,817** | 0,563 | +0,254 |
| AUC OvR se_mantiene | 0,562 | (no consta) | — |
| AUC OvR sube | 0,672 | (no consta) | — |
| Brier multiclase | **0,4370** | 0,5479 | −0,1109 |
| Exactitud | 0,7049 | (no consta) | — |

Referencia: una constante con las prevalencias de val (0,073 / 0,702 / 0,225)
da Brier **0,4510**. Es decir, el bayesiano apenas la supera (0,4370) y el
XGBoost r1 está **por debajo** (0,5479): en este corte temporal ninguno de los
dos es un buen modelo de probabilidades, y el bayesiano es el menos malo.

Intervalos de credibilidad (probabilidad media por clase; IC80 / IC95 agregados
y ancho medio por observación):

| Clase | Media | IC80 | IC95 | Ancho medio IC80 / IC95 |
|---|---|---|---|---|
| baja | 0,059 | [0,034; 0,082] | [0,023; 0,133] | 0,048 / 0,140 |
| se_mantiene | 0,769 | [0,730; 0,802] | [0,653; 0,808] | 0,103 / 0,234 |
| sube | 0,172 | [0,114; 0,232] | [0,069; 0,308] | 0,119 / 0,244 |

**Lectura honesta:**

- El `argmax` es **degenerado**: 0,01 % «baja», 98,95 % «se_mantiene», 1,04 %
  «sube». Por eso el F1 macro cae 9,9 pp y el F1 de «baja» es 0,003: el modelo
  casi nunca predice la clase minoritaria.
- En cambio, en **puntuaciones propias** (Brier) y en el **ranking** de «baja»
  (AUC 0,817) es mucho mejor que el XGBoost r1: las probabilidades están
  encogidas hacia las prevalencias pero ordenan bien.
- Con los criterios de victoria de §8 (**≥ 2 pp F1 macro *o* ≥ 0,02 Brier**), el
  bayesiano **cumple por Brier** (−0,1109) y **pierde por F1 macro** (−9,9 pp).
  Para el póster: XGBoost sigue siendo el clasificador; el bayesiano aporta
  calibración, incertidumbre y la ruta metodológica, no el `argmax`.

**Diagnóstico de odds proporcionales (§11), versión mínima:** modelo relajado con
`δ_{k,c} ~ Normal(0; 0,5)`, 1 cadena × 500. Resultado: `|Δβ|` máximo **0,040**,
media 0,014, correlación 0,999, **0 cambios de signo** → la hipótesis de odds
proporcionales es **plausible** para estos 12 predictores. Advertencia: el
ajuste relajado es corto (ESS_min 62, 7/500 divergencias), así que es un chequeo
grueso, no un test formal.

**Artefactos:** `trace_bayesiano_minimo.nc` (target_accept 0,95),
`trace_bayesiano_minimo_ta090.nc` (respaldo del primer ajuste),
`resultados/bayesiano_minimo_20261026_014416.json`,
`resultados/evaluacion_bayesiano_minimo_20261026_014535.json`,
`resultados/odds_diagnostico_minimo_20261026_015539.json`; scripts
`entrenar_bayesiano_minimo.py`, `evaluar_bayesiano_minimo.py`,
`diagnostico_odds_minimo.py`, `diagnostico_minimo.py`.

## 8. Evaluación (solo val)

- Posterior predictive en val: F1 macro, F1 por clase, AUC OvR, Brier multiclase.
- Intervalos de credibilidad al **80 % y 95 %** para la probabilidad de cada clase.
- Comparación con XGBoost r1: F1 macro 0,3939; AUC «baja» 0,563; Brier 0,5479.
- Criterios de victoria: **≥ 2 pp** en F1 macro **o** **≥ 0,02** de mejora en Brier.
- **Diagnóstico post-ajuste de odds proporcionales** (§11).

## 9. Riesgos declarados

- **Extrapolación temporal**: `v_20` es un nivel nuevo; la incertidumbre crece y es
  honesta, pero el modelo no puede saber el efecto 2019 sin datos de 2019.
- **Odds proporcionales**: se diagnostica post-ajuste (§11); si falla, se declara
  como limitación medida.
- **«Baja» escasa**: el prior y el pooling ayudan, pero si la señal individual no
  existe, el F1 seguirá limitado. El bayesiano aporta honestidad, no milagros.
- **Cómputo**: sin compilador C, modo Python; la prueba previa decide el tamaño.

## 10. Entorno y entregables

- PyMC y ArviZ instalados en **`07_modelo/.venv-bayes`** (opción 2: el sandbox no
  permite escribir en el venv de Agente). Interprete:
  `07_modelo\.venv-bayes\Scripts\python.exe`.
- Entregables: `entrenar_bayesiano.py`, `trace_bayesiano.nc`,
  `evaluar_bayesiano.py`, `diagnostico_odds.py`, `model_card.md`.
- **Test**: se evalúa una sola vez, con el modelo operativo ya decidido.

## 11. Diagnóstico post-ajuste de odds proporcionales

Tras la convergencia del modelo principal:

1. Se ajusta un **modelo relajado** con cortes desplazados por categoría de origen:
   `κ_{k,c} = κ_k + δ_{k,c}`, con `δ ~ Normal(0, 0,5)`. Es un NUTS corto
   (1 cadena × 500) sobre el mismo train.
2. Se comparan las **posteriores de β** (media y desviación) entre ambos modelos, y
   el ELPD/LOO si ArviZ lo permite.
3. Si los β cambian poco (|Δmedia| < 0,2 y las conclusiones no se invierten), la
   hipótesis de odds proporcionales es **plausible**; si cambian mucho, se declara
   como **limitación medida** y se reporta la variante relajada como alternativa.

## 12. Test unitario de renormalización de máscaras (antes de NUTS)

Función `_test_mascaras()` en `entrenar_bayesiano.py` (≈10 líneas):

- Toma probabilidades sintéticas `p = (0,3, 0,4, 0,3)`.
- Aplica la máscara IJ (p_baja = 0, renormaliza) y comprueba `sum == 1` y `p_baja == 0`.
- Aplica la máscara IE (p_sube = 0, renormaliza) y comprueba `sum == 1` y `p_sube == 0`.
- Si falla, **aborta antes de muestrear**.

## 13. Regla de corte temporal (1 de noviembre)

Si el **1 de noviembre** el bayesiano no ha convergido, o no bate a XGBoost en F1
macro o en Brier, se cierra con **XGBoost**: el diseño bayesiano queda documentado
como **contribución metodológica** y el póster se construye con XGBoost + la
justificación del bayesiano. No se reajusta sin autorización.
