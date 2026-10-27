# Informe 2 · Análisis exploratorio y auditoría de la base

**Proyecto:** Consultoría estadística USTA 2026-II — Observatorio Minciencias
**Componente:** Fase 3 · modelo predictivo de movilidad de categoría
**Entregable:** diagnóstico del dato (desbalanceo, drift, atípicos, redundancia y
fuga por identidad)
**Fecha:** 27 de octubre de 2026
**Autor:** Consultoría estadística USTA 2026-II

---

## 1. Objetivo de la etapa

Caracterizar la base construida en el informe 1 antes de modelarla, y responder
tres preguntas que condicionan cualquier resultado posterior:

1. **¿Cómo se distribuye el fenómeno?** Tamaño del universo, prevalencia de cada
   clase y evolución entre cohortes.
2. **¿El dato cambia entre el pasado y el futuro?** Deriva (*drift*) de las
   features y de la prevalencia, medida con PSI, KS y χ².
3. **¿Hay fuga por identidad?** Cuantificar cuánto del desempeño depende de que el
   modelo reconozca personas vistas y no de que generalice a personas nuevas.

El objetivo no es «hacer EDA» como trámite: es **decidir si el modelo operativo se
sostiene o hay que reentrenarlo**, y dejar documentada la deuda de robustez que no
se resuelve con el modelo actual. El resultado de la etapa es una decisión
explícita, no un conjunto de gráficos.

---

## 2. Metodología y herramientas usadas

### 2.1 Universo y partición

| Elemento | Valor |
|---|---|
| Transiciones contiguas | **43 187** |
| Personas únicas | **18 116** |
| Cohorte de origen → destino | 16→17, 17→18, 18→19, 19→20, 20→21 |
| `train` (destinos 17, 18, 19) | 19 838 filas |
| `val` (destino 20) | 9 994 filas |
| `test` (destino 21) | 13 355 filas, evaluado una sola vez |
| Features | 172 de producción |

La partición es **temporal por cohorte de destino**, no aleatoria: el modelo
entrena con transiciones que terminan en 2014, 2015 y 2017, valida con 2019 y se
evalúa con 2021. Ninguna fila de test entra en entrenamiento, estandarización ni
selección de umbral.

### 2.2 Los siete análisis

El diagnóstico se ejecutó con tres scripts sobre el parquet, sin reentrenar el
modelo operativo:

| # | Análisis | Script | Salida |
|---|---|---|---|
| a | χ² de homogeneidad de la clase entre splits | `auditoria_eda.py` | `auditoria_eda_*.json` |
| b | PSI y KS por feature (train vs test) | `auditoria_eda.py` | idem |
| c | Atípicos de `n_productos` y winsorización al p99 | `auditoria_eda.py` | idem |
| d | VIF iterativo sobre las 172 features | `auditoria_eda.py` | idem |
| e | Features muertas (ceros y `gain = 0`) | `auditoria_eda.py` | idem |
| f | Fechas posteriores a la convocatoria | `auditoria_eda.py` | idem |
| g | Benchmark B (entidad disjunta) y control de volumen | `benchmark_B.py`, `control_volumen.py` | `benchmark_B_*.json`, `control_volumen_*.json` |

### 2.3 Métricas de deriva y de fuga

- **χ² de homogeneidad** con V de Cramér para medir si la distribución de clases
  cambia entre splits, separando significancia de tamaño de efecto.
- **PSI** (*population stability index*) por feature entre train y test, con los
  umbrales convencionales: <0,10 estable, 0,10–0,25 cambio moderado, >0,25 cambio
  severo.
- **KS** de dos muestras como contraste no paramétrico, leído con cautela por el
  tamaño muestral.
- **VIF** iterativo (eliminar la feature de mayor VIF hasta que todas queden por
  debajo de 10) para cuantificar redundancia.
- **Benchmark B**: mismo diseño temporal, pero se eliminan del train y de la
  validación las personas que aparecen en el conjunto de evaluación. La diferencia
  `A − B` mide la **inflación por identidad**. Para separar identidad de volumen se
  añade un **control** con la misma cantidad de filas que B pero sin excluir
  personas.

### 2.4 Herramientas

Python 3.11.9, pandas 3.1.0, numpy 2.4.6, scikit-learn 1.9.1 y XGBoost 3.2.0
(configuración de la Ronda 2 congelada). Los cálculos de PSI, KS, VIF y χ² se
implementaron con pandas/numpy y `scipy.stats`; el benchmark B reutiliza el
pipeline de `opt_comun.py` para que el diseño sea idéntico al del modelo
operativo.

---

## 3. Justificación técnica

### 3.1 Por qué la división temporal y no una aleatoria

La elección no es estilística. Con datos de panel (persona × convocatoria), una
partición aleatoria mezcla pasado y futuro en el mismo conjunto: el modelo puede
ver la transición 2019→2021 de una persona y evaluarse en su transición
2017→2019, de modo que aprende de «lo que pasó después» para predecir «lo que pasó
antes». El resultado es una estimación optimista que no se sostiene en producción.

La literatura es explícita en los dos frentes:

- **Fuga de información.** Kaufman, Rosset, Perlich y Stitelman (2012) formulan el
  problema de la fuga en minería de datos, distinguen sus tipos y proponen
  estrategias de detección; una partición que ignore la estructura temporal es uno
  de los casos que esa formulación cubre.
- **Datos de panel.** Cerqua, Letta y Pinto (2025) documentan que descuidar la
  estructura transversal y longitudinal del panel produce **fugas difíciles de
  detectar** y desempeño fuera de muestra inflado; es, según el resumen del editor,
  la primera evaluación sistemática del problema en aprendizaje automático con
  datos de panel.
- **Validación temporal.** La práctica recomendada para datos con estructura
  temporal es el origen móvil (*rolling origin*): entrenar con lo disponible hasta
  T y evaluar en el periodo siguiente, desplazando T (Tashman, 2000; Bergmeir y
  Benítez, 2010; Hyndman y Athanasopoulos, *FPP3*).

Nuestro esquema —tres folds temporales, test de 2021 evaluado una vez, umbral
fijado solo con validación— es una versión discreta de esa regla, adaptada a que
solo hay seis cohortes.

La partición aleatoria se descartó además por una razón de **uso**: el sistema
predice el futuro de la población conocida, no la entrada de personas nuevas. Un
split aleatorio respondería a una pregunta distinta (¿reconozco a esta persona?) y
produciría métricas que no corresponden al despliegue previsto.

### 3.2 Por qué PSI y no solo el p-valor del KS

Con 19 838 filas de train y 13 355 de test, el KS rechaza casi cualquier
diferencia, por trivial que sea: el p-valor mide significancia, no magnitud. El PSI
incorpora la magnitud del cambio en la distribución y tiene umbrales de lectura
operativa. Por eso la decisión sobre drift se toma con PSI y el KS se reporta como
contraste.

### 3.3 Por qué se audita la identidad y no solo la etiqueta

En un panel temporal es normal que la misma persona aparezca en train y en test: es
lo que permite pronosticar su futuro. Eso **no es fuga de etiqueta** —ninguna fila
de test entra en el entrenamiento— pero sí puede inflar el desempeño si el modelo
«reconoce» a la persona. La auditoría separa los dos conceptos y mide el segundo
con un diseño entidad-disjunto (B) y un control de volumen. La regla de decisión se
fijó antes de mirar el resultado: **Δ A−B < 5 pp ⇒ modelo robusto, se cierra**;
>10 pp ⇒ separar benchmarks; >15 pp ⇒ reentrenar con aprobación.

---

## 4. Resultados y métricas

### 4.1 Desbalanceo y cambio de régimen

| Split | `baja` | `se_mantiene` | `sube` | Total | Prevalencia de `baja` |
|---|---:|---:|---:|---:|---:|
| train (17–19) | 1 022 | 15 471 | 3 345 | 19 838 | **5,15 %** |
| val (20) | 730 | 7 018 | 2 246 | 9 994 | **7,30 %** |
| test (21) | 1 362 | 9 657 | 2 336 | 13 355 | **10,20 %** |

El desbalanceo es fuerte y **creciente**: en train hay una «baja» por cada 15
«se mantiene»; en test, una por cada 7. Ese cambio de régimen (5,2 % → 10,2 %) es
el hecho más importante del EDA: explica por qué el Brier del modelo es peor que
el de una constante entrenada con las prevalencias de train (0,4692 frente a
0,4419) y por qué el umbral no puede congelarse entre cohortes.

**χ² de homogeneidad:** χ² = **469,53**, gl = 4, p = **2,6 × 10⁻¹⁰⁰**, V de Cramér
= **0,0737** (esperado mínimo 720,62). Los tres pares dan V < 0,10 (train vs val
0,0853; train vs test 0,0980; val vs test 0,0744). Lectura: la distribución **no
es homogénea** (p ínfimo) pero el **tamaño del efecto es pequeño**; el desajuste
lo explica la prevalencia, no un cambio de forma.

### 4.2 Deriva de las features (PSI y KS)

| Umbral | N.º de features |
|---|---:|
| PSI > 0,25 (drift severo) | **3** |
| PSI > 0,20 | **4** |
| PSI > 0,10 | **12** |
| KS con p < 0,01 | **69 de 172** |

Top-10 por PSI (train vs test):

| Feature | PSI | KS |
|---|---:|---:|
| `n_categoria_PROYECTO_DE_INVESTIGACION_Y_DESARROLLO_CON_CALIDAD` | **0,384** | 0,285 |
| `n_tipologia_ART_CULOS` | **0,316** | 0,240 |
| `n_categoria_ART_CULOS_DE_GENERACI_N_DE_CONTENIDO` | **0,316** | 0,240 |
| `n_categoria_EVENTO_CIENT_FICO_CON_CALIDAD_A` | 0,203 | 0,210 |
| `n_tipologia_CAP_TULOS_DE_LIBRO_DE_INVESTIGACI_N` | 0,169 | 0,165 |
| `n_tipologia_PROYECTO_DE_INVESTIGACION_Y_DESARROLLO` | 0,161 | 0,194 |
| `n_categoria_CAP_TULOS_DE_LIBRO_DE_INVESTIGACI_N_CON_CALIDAD_A` | 0,160 | 0,159 |
| `n_tipologia_EVENTO_CIENT_FICO` | 0,144 | 0,173 |
| `n_productos` | 0,113 | 0,146 |
| `n_clase_APROPIACI_N_SOCIAL_DEL_CONOCIMIENTO` | 0,111 | 0,130 |

Las tres features con drift severo son las de **proyectos de I+D** y las **dos de
artículos** (la de tipología y la de categoría de generación de contenido),
justamente las que crecieron entre 2019 y 2021; el evento científico con calidad A
queda en 0,203. El resto se mueve poco. Consecuencia práctica: la pérdida de
calibración del modelo en 2021 no es un fallo del método sino un cambio de
composición de la producción, y el monitoreo del próximo año debe vigilar esas tres
variables.

### 4.3 Atípicos de producción

| Métrica | Valor |
|---|---:|
| Q1 / Q3 | 8 / 33 |
| IQR | 25 |
| Cerco superior de Tukey | 70,5 |
| Máximo | **613** |
| p99 de train | **105** |
| Filas sobre el cerco IQR | 2 039 (4,72 %) |
| Filas sobre p99(train) | **628 (1,45 %)** — train 194 · val 146 · test 288 |
| Media antes → después de winsorizar | 24,59 → 23,83 |
| Desviación antes → después | 26,43 → **21,84 (−17,4 %)** |

La media apenas cambia (−3,1 %) pero la desviación cae 17,4 %: la cola domina la
dispersión. La winsorización al p99 se probó **solo en los folds** (nunca en test)
y se descartó como mejora porque empeoraba el F1 (véase §4.8).

### 4.4 Redundancia (VIF)

| Métrica | Valor |
|---|---:|
| Features iniciales | 172 |
| Features finales | **123** |
| Eliminadas | **49** |
| — duplicados exactos (r = 1,00000) | 34 |
| — eliminadas por VIF > 10 | 15 |
| VIF máximo final | **4,95** |

La mayor parte de la «redundancia» es literal: **34 de las 49** eliminadas son la
misma variable con otro nombre (por ejemplo, `n_tipologia_ART_CULOS` ≡
`n_categoria_ART_CULOS_DE_GENERACI_N_DE_CONTENIDO`). El modelo con 172 features
está sobreparametrizado por construcción; con 123 se conserva la información. Aun
así, la poda **no mejora** el desempeño (§4.8).

### 4.5 Features muertas

| Métrica | Valor |
|---|---:|
| Features con > 90 % ceros | **132** |
| Features con > 99 % ceros | **86** |
| Features completamente cero | 0 |
| `gain = 0` en el modelo base (173 features) | 66 |
| `gain = 0` en el modelo final de la Ronda 2 (172) | **61** |

Por familia (>99 % ceros): clase 1, tipología 23, categoría 62. Son categorías
legítimas pero rarísimas (patentes, variedades, regulaciones); su valor está en la
cola, no en el promedio, y por eso la poda debe probarse antes de adoptarla.

### 4.6 Fechas posteriores a la convocatoria

| Conv. | Año | Filas | Filas tardías | % | Pares persona-conv afectados |
|---|---|---:|---:|---:|---:|
| 16 | 2013 | 238 407 | 10 | 0,0042 | 9 |
| 17 | 2014 | 342 160 | 103 | 0,0301 | 96 |
| 18 | 2015 | 376 653 | 14 | 0,0037 | 14 |
| 19 | 2017 | 536 648 | 1 | 0,0002 | 1 |
| 20 | 2019 | 762 719 | 0 | 0 | 0 |
| 21 | 2021 | 910 042 | 0 | 0 | 0 |
| **Total** | | **3 166 629** | **128** | **0,004 %** | **120** |

El artefacto existe pero es marginal: **128 filas** (0,004 %), concentradas en
2013–2014, con un share medio de 9,32 % de la producción de los 120 pares
afectados y solo 3 pares con el 100 % tardío. Desaparece en 2019 y 2021, de modo
que **no compromete el test**. Se recomienda excluirlas en una futura
reconstrucción, no ahora.

### 4.7 Fuga por identidad

| Métrica | Valor |
|---|---:|
| Investigadores únicos en train | 10 074 |
| Investigadores únicos en val | 9 994 |
| Investigadores únicos en test | 13 355 |
| Test ∩ train | **6 117 (45,80 % de test)** |
| Test ∩ val | **8 271 (61,93 %)** |
| **Test ∩ (train ∪ val)** | **8 589 (64,31 %)** |
| Test ∩ train ∩ val | 5 799 |
| Test sin aparición previa | **4 766 (35,69 %)** |
| Val ∩ train | 6 718 (67,22 %) |
| Universo total | 18 116 |

El solapamiento es alto, y es **consecuencia del diseño temporal**: la misma
persona aparece en varias cohortes. No es fuga de etiqueta, pero hay que medir
cuánto aporta.

**Benchmark B (entidad disjunta).** Se eliminan del train y de la validación las
personas del conjunto de evaluación:

| Fold | Train | Val | Eval | F1 «baja» |
|---|---:|---:|---:|---:|
| F1 | 713 | 1 197 | 8 164 | 0,2604 |
| F2 | 2 254 | 1 693 | 9 994 | 0,2647 |
| F3 | 1 197 | 1 693 | 9 994 | 0,2873 |
| **Media** | | | | **0,2708** (desv. 0,0118) |

Frente a la referencia de A (0,2985), el delta en folds es **+2,77 pp**. En test:

| Modelo | F1 «baja» | Recall | Precisión | F1 macro | Brier |
|---|---:|---:|---:|---:|---:|
| **A** (operativo) | **0,4234** | **0,7878** | 0,2895 | 0,5109 | **0,4692** |
| **B** (entidad disjunta) | 0,4016 | 0,6153 | 0,2981 | 0,4412 | 0,4969 |
| **Control** (5 005 filas, identidad permitida) | 0,4222 | 0,7416 | 0,2951 | 0,5022 | 0,4400 |

**Descomposición del delta de 2,18 pp:**

| Componente | Cálculo | Valor |
|---|---|---:|
| Efecto identidad (a volumen fijo) | 0,4222 − 0,4016 | **+2,06 pp** |
| Efecto volumen (con identidad) | 0,4234 − 0,4222 | **+0,12 pp** |
| **Delta total A − B** | 0,4234 − 0,4016 | **+2,18 pp** |

Dos hallazgos: (i) la inflación por identidad es de **~2,1 pp, no de decenas de
puntos**: con una sexta parte de los datos y personas compartidas se llega a
0,4222, casi el 0,4234 del modelo completo; (ii) el **perfil operativo sí cambia**:
B detecta menos descensos (recall 0,6153 frente a 0,7878), con precisión estable
(~0,29).

**Decisión.** Δ A−B = 2,18 pp en test y 2,77 pp en folds, ambos por debajo de
5 pp: **el modelo es robusto y se cierra con la Ronda 2**, sin reentrenar y sin
volver a tocar test. El benchmark B queda como medida de generalización a personas
nuevas, no como reemplazo del modelo operativo.

### 4.8 Modelo limpio: ¿la limpieza mejora el F1?

Se construyó un dataset sin las 49 features redundantes, sin las 86 con >99 % de
ceros y con `n_productos` winsorizada en el p99 de train. Se evaluó **solo en
folds**, con test intacto:

| Variante | Features | F1 «baja» OOS | Desv. | Brier |
|---|---:|---:|---:|---:|
| Base (Ronda 2) | 172 | **0,2985** | 0,0184 | **0,4196** |
| Solo VIF | 123 | 0,2877 (**−1,08 pp**) | 0,0326 | 0,4223 |
| Limpio completo | 56 | 0,2834 (**−1,51 pp**) | 0,0288 | 0,4223 |

La limpieza **empeora**: cae el F1 entre 1,08 y 1,51 pp, sube la desviación entre
folds y el Brier sube 0,27 %. Tres explicaciones plausibles: las features
redundantes actúan como regularización implícita; las 67 features casi vacías
eliminadas no eran ruido puro (separan «sube» en perfiles atípicos); y la
winsorización altera 288 filas de test que son productores extremos que casi nunca
bajan. **Decisión: el modelo se cierra con la Ronda 2**; el dataset limpio queda
como evidencia, no como modelo operativo.

### 4.9 Síntesis de la etapa

| Pregunta | Respuesta |
|---|---|
| ¿Hay desbalanceo? | Sí, fuerte y creciente (5,15 % → 10,20 % de «baja») |
| ¿Hay drift? | Sí, severo en 3 features y moderado en 4; el KS marca 69/172 |
| ¿Hay fuga de identidad? | Solapamiento del 64,31 % en test, con inflación de **2,18 pp** |
| ¿Se reentrena? | **No**: 2,18 pp < 5 pp y la limpieza empeora el F1 |
| ¿Qué queda como deuda? | Drift de las 3 features de PSI > 0,25 para el próximo año; poda por familia, no por columna |

---

## 5. Referencias

1. **Cerqua, A., Letta, M. & Pinto, G. (2025).** *On the (Mis)Use of Machine
   Learning With Panel Data.* **Oxford Bulletin of Economics and Statistics,
   88(3), 506-518.** DOI: [10.1111/obes.70019](https://doi.org/10.1111/obes.70019).
2. **Kaufman, S., Rosset, S., Perlich, C. & Stitelman, O. (2012).** *Leakage in
   data mining: formulation, detection, and avoidance.* **ACM Transactions on
   Knowledge Discovery from Data, 6(4), 1-21.** DOI:
   [10.1145/2382577.2382579](https://doi.org/10.1145/2382577.2382579).
3. **Tashman, L. J. (2000).** *Out-of-sample tests of forecasting accuracy: an
   analysis and review.* **International Journal of Forecasting, 16(4),
   437-456.** DOI:
   [10.1016/S0169-2070(00)00065-0](https://doi.org/10.1016/S0169-2070(00)00065-0).
4. **Bergmeir, C. & Benítez, J. M. (2010).** *A survey of cross-validation
   procedures for model selection.* **Statistics Surveys, 4, 40-79.** DOI:
   [10.1214/09-SS054](https://doi.org/10.1214/09-SS054).
5. **Hyndman, R. J. & Athanasopoulos, G.** *Forecasting: Principles and Practice*
   (3.ª ed.), secciones «Time series cross-validation» y «Lagged predictors».
   https://otexts.com/fpp3/
6. **Godoy, J. M., Abramo, G., D'Angelo, C. A. & Cortés, J. D. (2026).** *Should I
   stay or should I go? …* **Scientometrics, 131(9), 5803-5824.** DOI:
   [10.1007/s11192-026-05716-9](https://doi.org/10.1007/s11192-026-05716-9).

**Evidencia interna**

7. `07_modelo/documentacion/auditoria_base_datos.md` §2 y §6–§7 — cálculo y
   salidas literales del EDA, del benchmark B y del modelo limpio.
8. `07_modelo/modelado/auditoria_eda.py`,
   `07_modelo/modelado/benchmark_B.py`, `07_modelo/modelado/control_volumen.py`.
9. `07_modelo/modelado/resultados/auditoria_eda_20261027_201914.json`,
   `benchmark_B_20261027_201425.json`,
   `control_volumen_20261027_202210.json`.
10. `07_modelo/modelado/model_card.md` §5 — limitaciones del modelo.
