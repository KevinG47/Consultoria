# Auditoría de la base de datos del modelo

**Proyecto:** Consultoría estadística USTA 2026-II — Observatorio Minciencias
**Objeto:** verificar si el dataset de la Fase 3 se construyó de forma idónea, con
énfasis en **fuga por identidad** (*identity leakage*) y en la calidad del
análisis exploratorio (EDA).
**Fecha:** 27 de octubre de 2026
**Alcance:** auditoría y planificación. **No se reentrenó ningún modelo ni se
volvió a tocar el test** (cohorte 2021).

> **Resumen ejecutivo.**
> 1. **No hay fuga de etiqueta ni de construcción**: las nueve comprobaciones del
>    manifiesto (V01–V09) pasan, y el `split` se asigna por cohorte de destino,
>    no al azar [`validar_dataset.py`, L255-259].
> 2. **Sí hay solapamiento de identidad**: **64,31 % de los investigadores de
>    test** (8 589 de 13 355) aparecen también en train o val. Es estructural al
>    diseño de panel con split temporal, no un error de construcción.
> 3. Ese solapamiento **no invalida** las métricas si el objetivo es pronosticar
>    a la población ya conocida por el sistema, pero **impide afirmar
>    generalización a investigadores nuevos** (arranque en frío).
> 4. El **EDA fue parcial**: se documentaron la distribución del objetivo y el
>    desbalanceo, pero no se trataron los valores atípicos de producción, no se
>    evaluó la multicolinealidad de las 172 features (hay 39 pares con
>    |r| > 0,99) y no se analizó el drift entre splits.
> 5. **Recomendación:** no reentrenar todavía. Primero completar el EDA y añadir
>    un benchmark de entidad disjunta; el plan está en §4.

---

## §1 · Método y fuentes auditadas

| Fuente | Qué se usó |
|---|---|
| `07_modelo/datos/derivados/modelo_dataset_ventana_contiguo.parquet` | 43 187 transiciones, 18 116 personas, columnas `ID_PERSONA_PR`, `split`, `target_class`, 172 features |
| `07_modelo/modelado/validar_dataset.py` | comprobaciones V01–V09 y tabla de `target_class` por split |
| `07_modelo/ingesta/manifiestos/validacion_dataset_20261025_202417.json` | resultado de las comprobaciones (todas OK) |
| `07_modelo/modelado/diagnostico_person_leakage.py` + `diagnostico_leakage_20261025_204708.json` | diagnóstico previo de *person leakage* |
| `07_modelo/modelado/diagnostico_supuestos.py` + `diagnostico_supuestos_20261025_204753.json` | VIF, Box-Tidwell y autocorrelación por persona |
| `07_modelo/modelado/preparar_dataset.py`, `07_modelo/ingesta/agregar_por_persona.py` | definición del split, recorte de `dias_desde_ultimo`, ventana de producción |
| `07_modelo/modelado/model_card.md`, `validacion_honesta.md` | métricas y decisiones ya documentadas |

**Reproducción de la auditoría:** los cálculos de §2 se hicieron con pandas sobre
el parquet; el código es de ~20 líneas y está transcrito en el Anexo A.

---

## §2 · Tarea 1 — Fuga por identidad

### 2.1 Dos cosas distintas que conviene no confundir

| Tipo de fuga | Qué es | ¿Aplica aquí? |
|---|---|---|
| **Fuga de etiqueta / de construcción** | Que una feature contenga información del resultado (p. ej., la categoría de destino) o que el `split` se haya hecho al azar mezclando futuro y pasado | **No.** V06 verifica que `target_class` y `split` del dataset coincidan con `target.parquet`; V08 verifica que el split se asigne por cohorte de destino [`validar_dataset.py`, L207-259] |
| **Fuga por identidad** (*identity leakage*) | Que la misma entidad (aquí, el investigador) aparezca en train y en test, de modo que el modelo pueda «reconocerla» en lugar de generalizar | **Sí, por diseño.** Un split temporal de datos de panel comparte personas entre periodos; es lo que permite pronosticar el futuro de la población conocida |

El problema que describe la literatura reciente [Cerqua, Letta & Pinto, 2025] es
que **descuidar la estructura transversal y longitudinal del panel** produce
fugas difíciles de detectar y desempeño fuera de muestra inflado. La defensa
mínima es un split que respete el tiempo; la defensa adicional —cuando se quiere
medir generalización a entidades nuevas— es un split agrupado por entidad.

### 2.2 Resultados del cálculo de solapamiento

Salida literal (extracto de la corrida; se omiten dos líneas descriptivas):

```
personas unicas por split: {'train': 10074, 'val': 9994, 'test': 13355}
transiciones por split: {'test': 13355, 'train': 19838, 'val': 9994}
test ^ train: 6117
test ^ val: 8271
test ^ (train|val): 8589
val ^ train: 6718
union total: 18116
transiciones test: 13355 | de personas vistas: 8589 (64.31%)
pct personas de test vistas en train o val: 64.31%
pct personas de test vistas SOLO en val: 18.51%
```

| Métrica | Valor |
|---|---|
| Investigadores únicos en **train** | **10 074** (en 19 838 filas: 3 823 con 1 fila, 2 738 con 2, 3 513 con 3) |
| Investigadores únicos en **val** | **9 994** (1 fila por persona) |
| Investigadores únicos en **test** | **13 355** (1 fila por persona) |
| Test ∩ train | **6 117** (45,80 % de test) |
| Test ∩ val | **8 271** (61,93 % de test) |
| **Test ∩ (train ∪ val)** | **8 589 (64,31 % de test)** |
| Test ∩ train ∩ val | 5 799 |
| Test sin ninguna aparición previa | **4 766 (35,69 %)** |
| Val ∩ train | 6 718 (67,22 % de val) |
| **Transiciones de test cuyo autor fue visto en entrenamiento (train)** | **6 117 de 13 355 (45,80 %)** |
| **Transiciones de test cuyo autor fue visto en train o val** | **8 589 de 13 355 (64,31 %)** |
| Universo total | 18 116 personas |

**Nota de lectura:** en val y test cada persona contribuye con **una sola fila**
(la cohorte de destino es 2019 y 2021, respectivamente), por lo que el porcentaje
de personas y el de transiciones coincide. En train sí hay repetición porque la
ventana cubre tres convocatorias.

### 2.3 Diagnóstico

**Hay solapamiento, y es > 0 %. Ahora bien, no es «fuga» en el sentido que
invalidaría el modelo; es una consecuencia del diseño y hay que declararla.**

Tres razones:

1. **El split es temporal, no aleatorio.** Train = cohortes de destino 2014,
   2015 y 2017; val = 2019; test = 2021 [`preparar_dataset.py`, L27-31]. El
   modelo nunca ve el futuro, y ninguna fila de test entra en el entrenamiento.
2. **La tarea es pronosticar a la población conocida.** El uso operativo del
   observatorio es asignar una probabilidad a cada investigador **que ya está en
   ScienTI** en la convocatoria siguiente. Que la persona haya sido observada en
   2017 no es una ventaja indebida: es la información histórica que el sistema
   tendría disponible en producción.
3. **La fuga sería real si el split fuese aleatorio por fila**, que es el error
   que documenta la literatura: ahí la misma persona cae en train y test y el
   modelo memoriza su patrón. Aquí no ocurre.

**Lo que el solapamiento sí impide afirmar:** que el modelo generalice a
**investigadores nuevos** (recién reconocidos, o que no estaban en las cohortes
de entrenamiento). Las métricas de test (F1 «baja» 0,4234) describen a la
población con historia previa, que es el 64,31 %. Para el 35,69 % restante no
tenemos estimación.

### 2.4 El diagnóstico previo y por qué no cierra el tema

`diagnostico_person_leakage.py` (25-10-2026) comparó el split temporal con un
80/20 **por persona** y concluyó «sin person leakage» porque el F1 macro **subió**
+5,84 pp en el split por persona (0,4523 vs 0,3939)
[`diagnostico_leakage_20261025_204708.json`].

Esa comparación está **confundida**: el split por persona evalúa sobre una
muestra que mezcla cohortes (2014, 2015, 2017, 2019), y las cohortes tempranas son
más fáciles que 2019. Un F1 mayor ahí no demuestra ausencia de fuga; demuestra
que el conjunto de evaluación es distinto. **El diagnóstico previo no responde la
pregunta de esta auditoría** y no debe citarse como evidencia de ausencia de
solapamiento.

### 2.5 Qué se puede y qué no se puede afirmar con las métricas actuales

| Afirmación | ¿Soportada? |
|---|---|
| «El modelo detecta el 79 % de los descensos en la cohorte 2021» | **Sí**, para la población con historia previa (8 589 personas) |
| «El modelo generaliza a investigadores nuevos» | **No.** No hay benchmark de entidad disjunta |
| «El F1 0,4234 es comparable con literatura que usa splits aleatorios» | **No.** Nuestro split es más exigente en el tiempo, pero menos exigente en identidad; no son comparables sin declararlo |
| «No hay fuga de etiqueta» | **Sí**, verificado por V06/V08 |

### 2.6 Severidad

| Hallazgo | Severidad | Por qué |
|---|---|---|
| Fuga de etiqueta o de construcción | **Nula** | Comprobaciones V01–V09 en verde |
| Solapamiento de identidad (64,31 %) | **Media** | No invalida el modelo operativo; limita el alcance de la conclusión |
| Riesgo residual de fuga temporal en features | **Baja** | Fechas de producto posteriores a la convocatoria (104 filas) recortadas a 0, pero el producto sigue contando [§3.2] |

---

## §3 · Tarea 2 — Auditoría del EDA

### 3.1 Checklist con evidencia

| Aspecto | ¿Se hizo? | Evidencia | Veredicto |
|---|---|---|---|
| **Distribución de `target_class` por split** | **Sí** | `validar_dataset.py` L270-281 imprime la tabla para los cuatro datasets; `model_card.md` §2 y §5 documentan la prevalencia 5,2 % → 10,2 %; `pasoB_baseline_prevalencia.py` construye el baseline de prevalencia | **Suficiente** para modelar, **sin gráfico** ni contraste formal |
| **Desbalanceo de clases y su impacto** | **Sí** | Pesos de clase `N/(3·n_clase)` en `entrenar_modelos.py` L186 y `opt_comun.py` L152-168; umbral ajustado en validación; baseline con F1 «baja» 0,185 y Brier 0,4419 (`model_card.md` §4) | **Suficiente** |
| **Valores atípicos** | **Parcial** | `preparar_dataset.py` L32 y L181-185 recortan `dias_desde_ultimo` a ≥ 0 y crean la bandera `dias_desde_ultimo_negativo` (104 filas); **no** se trató `n_productos` (máx. 613, p99 122, p99,9 259) ni `n_filas` | **Insuficiente** |
| **Multicolinealidad** | **Parcial** | `diagnostico_supuestos.py` calcula VIF pero **solo sobre 5 agregados** (`ano`, `n_filas`, `n_productos`, `n_grupos_distintos`, `dias_desde_ultimo`); el JSON reporta VIF **38,2** (`n_filas`) y **37,2** (`n_productos`) como altos, sin acción | **Insuficiente**: 39 pares con \|r\| > 0,99 entre las 172 features |
| **Drift train/val/test** | **No** | No hay análisis de distribución de features por split. Medición de esta auditoría: `n_productos` medio **21,3** en train vs **28,9** en test (+35,7 %) | **Faltó** |
| **Nulos, constantes y redundancia** | **No** | `gap` es constante (=1) en las 43 187 filas; **132** de las 172 features tienen > 90 % ceros y **86** tienen > 99 %; 61 tienen `gain = 0` en el modelo final (`model_card.md` §5.4) | **Faltó** |
| **Fuga temporal en features** | **Parcial, documentada** | `agregar_por_persona.py` L32-34: hay productos con `fcreacion` posterior a la convocatoria; `dias_desde_ultimo` se recorta a 0 pero el producto **sí** cuenta en `n_productos` | **Riesgo residual**, no cuantificado |
| **Fuga por identidad** | **Parcial** | `diagnostico_person_leakage.py`, con la limitación de §2.4 | **No concluyente** antes de esta auditoría |

### 3.2 Detalle de los hallazgos

**a) Distribución del objetivo por split.** Es la tabla que se usó para decidir el
umbral y el baseline:

| Split | baja | se mantiene | sube | n |
|---|---|---|---|---|
| train | 1 022 (5,15 %) | 15 471 (77,99 %) | 3 345 (16,86 %) | 19 838 |
| val | 730 (7,30 %) | 7 018 (70,22 %) | 2 246 (22,47 %) | 9 994 |
| test | 1 362 (10,20 %) | 9 657 (72,31 %) | 2 336 (17,49 %) | 13 355 |

El salto de prevalencia de «baja» (5,15 % → 10,20 %) está documentado en el
`model_card` y explica el Brier peor que la constante. **Lo que no se hizo** fue
un contraste formal de homogeneidad (χ²) ni intervalos de confianza por split,
ni un gráfico en el dashboard del modelo.

**b) Valores atípicos.** El único tratamiento explícito es el de
`dias_desde_ultimo` (recorte a 0 + bandera). Los conteos de producción tienen
cola pesada: el percentil 99 es 122 productos y el máximo 613 (50× la mediana,
18). Un valor de 613 productos en una convocatoria puede ser un investigador muy
productivo o un problema de vinculación de productos; **no se auditó cuál**. Con
XGBoost el efecto es acotado (los árboles son robustos a la escala), pero
distorsiona la importancia de features y el análisis de sensibilidad.

**c) Multicolinealidad.** El VIF se calculó solo sobre cinco agregados, no sobre
las 172 features. La auditoría encontró **39 pares con |r| > 0,99** y **53 pares
con |r| > 0,9** (correlación de Pearson en una muestra de 5 000 filas). La causa
es estructural: la tipología incluye categorías padre e hijo (`n_tipologia_LIBROS`
y `n_tipologia_LIBROS_DE_INVESTIGACI_N`, `n_clase_*` y las `n_tipologia_*` que la
componen, `n_filas` y `n_productos`). El modelo funciona, pero **la importancia
de features no es interpretable** y el `gain` se reparte entre columnas
duplicadas.

**d) Desbalanceo.** Bien cubierto: pesos de clase, umbral elegido en validación,
baseline de prevalencia y análisis del cambio de régimen 2019→2021.

**e) Drift.** No analizado. Además de `n_productos` (+35,7 % en media), el
cambio de régimen ya documentado (prevalencia y composición) sugiere que varias
features cambian de distribución entre train y test. Sin ese análisis, el Brier
0,4692 se atribuye a «cambio de régimen» sin cuantificar qué features derivan.

### 3.3 Conclusión sobre el EDA

**El EDA fue parcial y no fue suficiente para guiar el modelado con el rigor que
la base merece.** Se hicieron bien las dos cosas que más afectan la decisión
inmediata (distribución del objetivo y desbalanceo) y se documentó la validación
temporal; pero se pasó al modelo **sin** resolver la redundancia de features, sin
tratar los atípicos de producción, sin medir drift y sin cuantificar el
solapamiento de identidad. El costo se ve en dos lugares: 61 features con
`gain = 0` y un Brier peor que la constante que se explica cualitativamente pero
no se descompone.

---

## §4 · Plan de corrección

### 4.1 Tres benchmarks, no uno

El error a evitar es **reemplazar** el split temporal por un split aleatorio
agrupado: eso resolvería la identidad y rompería el tiempo (el error que critica
[Cerqua, Letta & Pinto, 2025]). La solución es **declarar tres benchmarks** y
reportar los tres:

| Benchmark | Definición | Qué mide | Costo |
|---|---|---|---|
| **A. Operativo** (actual) | Split temporal por cohorte de destino (train 2014/15/17, val 2019, test 2021), personas pueden repetirse | Pronóstico de la población conocida | Ya existe |
| **B. Entidad disjunta** (*cold start*) | Igual que A, pero **se eliminan del train todas las personas que aparecen en el fold de evaluación** | Generalización a investigadores nuevos | Alto: ver §4.3 |
| **C. Agrupado por persona dentro del periodo** | `GroupShuffleSplit` por `ID_PERSONA_PR` sobre el mismo periodo temporal: sirve para estabilidad de hiperparámetros, **no** para métricas de producción | Sensibilidad a la composición de personas | Bajo |

**Regla de reporte:** el número de producción sigue siendo **A**, siempre
acompañado de **B** y de la diferencia entre ambos. La diferencia
`F1(A) − F1(B)` es la **inflación atribuible a la continuidad de identidad** y es
el dato que el docente pide.

### 4.2 Cómo se implementa (código de referencia)

**B. Entidad disjunta (temporal + sin personas compartidas):**

```python
m_tr = np.isin(per, tr_cohortes)
m_ev = per == ev_cohorte
ids_eval = set(df.loc[m_ev, "ID_PERSONA_PR"])
m_tr_cold = m_tr & ~df["ID_PERSONA_PR"].isin(ids_eval)   # <- única línea nueva
# se reentrena con m_tr_cold y se evalúa con m_ev; el umbral se elige en val
```

**C. `GroupShuffleSplit` por persona (para estabilidad, dentro del mismo periodo):**

```python
from sklearn.model_selection import GroupShuffleSplit
gss = GroupShuffleSplit(n_splits=5, test_size=0.2, random_state=42)
for tr_idx, ev_idx in gss.split(X, y, groups=df["ID_PERSONA_PR"]):
    ...  # mismos grupos nunca en train y eval a la vez
```

La garantía es exactamente la que pide la literatura: **todos los registros de un
investigador en un solo split**. Scikit-learn lo implementa en
`GroupShuffleSplit` [scikit-learn, s. f.].

### 4.3 Costo real de B (medido, sin reentrenar)

| Fold | Train actual | Train entidad-disjunta | Pérdida | Eval |
|---|---|---|---|---|
| F1 (eval 2017) | 4 817 | **1 304** | −72,9 % | 8 164 |
| F2 (eval 2019) | 11 674 | **3 752** | −67,9 % | 9 994 |
| F3 (eval 2019) | 6 857 | **2 213** | −67,7 % | 9 994 |
| **Test (eval 2021)** | 29 832 | **8 476** | **−71,6 %** | 13 355 |

Con 1 300–3 700 filas de entrenamiento, el modelo pierde capacidad y B **no será
comparable en condiciones de igualdad**. Por eso B debe reportarse como
**benchmark de generalización**, no como reemplazo de A, y conviene acompañarlo de
un modelo más simple (regresión logística o XGBoost con menos profundidad) para
distinguir «cae por cold start» de «cae por falta de datos».

### 4.4 EDA faltante: qué hacer y cómo

| # | Análisis | Cómo | Salida |
|---|---|---|---|
| 1 | Homogeneidad del objetivo entre splits | χ² de independencia (3×3) + intervalos de Wilson por clase; gráfico de barras por split | Tabla + figura; si χ² es significativo, documentar el cambio de régimen con magnitud |
| 2 | Drift de features | PSI (*Population Stability Index*) y KS por feature, train vs test; top-20 por PSI | Tabla de PSI; PSI > 0,25 exige justificación o transformación |
| 3 | Atípicos de producción | Cuantiles, regla IQR y curva de Lorenz de `n_productos`; prueba de sensibilidad con winsorización al p99 en **un fold** | Decisión documentada (winsorizar o no) |
| 4 | Multicolinealidad | Matriz de correlación de Spearman de las 172; VIF iterativo eliminando la de mayor VIF; regla de pares \|r\| > 0,99 | Lista de 39 pares, propuesta de colapso por familia y efecto en folds |
| 5 | Redundancia y features muertas | Columnas con > 99 % ceros (86) y con `gain = 0` (61) | Propuesta de poda y su efecto en F1 OOS |
| 6 | Fuga temporal de `dias_desde_ultimo` | Aislar las 104 filas con fecha posterior a la convocatoria; reentrenar sin ellas en un fold | Verificar que el F1 no dependa de ese artefacto |
| 7 | Solapamiento de identidad | Este documento (§2) + benchmark B (§4.1) | Tabla de solapamiento y delta A−B |

Todo debe quedar en un script reproducible `07_modelo/modelado/auditoria_eda.py`
con salida JSON en `resultados/`, para que la Memoria pueda citar cifras y no
impresiones.

### 4.5 Criterios de aceptación

1. Ningún par con |r| > 0,99 puede quedar sin decisión documentada (colapsar,
   eliminar o justificar).
2. Cada fold reporta F1 de A y de B, y la diferencia.
3. El PSI de las 20 features más importantes debe estar reportado; si alguna
   supera 0,25, se documenta su efecto.
4. La decisión sobre atípicos (winsorizar o no) se toma **en validación**, nunca
   en test.
5. El test se vuelve a evaluar **una sola vez** y solo si un cambio supera el +2
   pp ya establecido.

### 4.6 Qué no hacer

- **No reemplazar el split temporal por uno aleatorio agrupado.** Sería el error
  inverso al que se quiere corregir: rompe la causalidad temporal.
- **No reentrenar el test** para «ver si cambia». El test ya se consumió una vez.
- **No cambiar el modelo operativo** solo porque B dé distinto: A y B responden
  preguntas distintas y ambas deben reportarse.
- **No interpretar la importancia de features** mientras existan los 39 pares
  colineales sin resolver.

---

## §5 · Referencias

1. **Cerqua, A., Letta, M. & Pinto, G. (2025).** *On the (Mis)Use of Machine
   Learning With Panel Data.* **Oxford Bulletin of Economics and Statistics,
   88(3), 506-518.** DOI:
   [10.1111/obes.70019](https://doi.org/10.1111/obes.70019). Acceso abierto
   (CC BY 4.0). El resumen del editor describe «la primera evaluación sistemática
   de los problemas de fuga de datos en el uso de aprendizaje automático con datos
   de panel», y advierte que descuidar la estructura transversal y longitudinal
   «conduce a fugas difíciles de detectar», a desempeño fuera de muestra inflado
   y a sobreestimar la utilidad real de los modelos.
2. **Paz, H. R. (2025).** *A Leakage-Aware Data Layer For Student Analytics: The
   Capire Framework For Multilevel Trajectory Modeling.* arXiv:
   [2511.11866](https://arxiv.org/abs/2511.11866). Propone una capa de datos
   consciente de la fuga que separa **ventana de observación** y **horizonte de
   resultado** (parámetro VOT) para prevenir la fuga por construcción, y organiza
   los predictores en cuatro niveles (N1–N4).
3. **Kaufman, S., Rosset, S., Perlich, C. & Stitelman, O. (2012).** *Leakage in
   data mining: formulation, detection, and avoidance.* **ACM Transactions on
   Knowledge Discovery from Data, 6(4), 1-21.** DOI:
   [10.1145/2382577.2382579](https://doi.org/10.1145/2382577.2382579). Formulación
   clásica del problema y de las estrategias de detección.
4. **scikit-learn developers (s. f.).** *`GroupShuffleSplit`.*
   https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html
   Documentación de la utilidad que garantiza que un grupo (aquí,
   `ID_PERSONA_PR`) no se reparta entre train y test.

**Referencias internas**

5. `07_modelo/modelado/validar_dataset.py` y
   `07_modelo/ingesta/manifiestos/validacion_dataset_20261025_202417.json`
6. `07_modelo/modelado/diagnostico_person_leakage.py` y
   `resultados/diagnostico_leakage_20261025_204708.json`
7. `07_modelo/modelado/diagnostico_supuestos.py` y
   `resultados/diagnostico_supuestos_20261025_204753.json`
8. `07_modelo/modelado/preparar_dataset.py`, `07_modelo/ingesta/agregar_por_persona.py`
9. `07_modelo/modelado/model_card.md`, `07_modelo/modelado/validacion_honesta.md`

---

## Anexo A · Código del cálculo de solapamiento

```python
import pandas as pd

df = pd.read_parquet(
    "07_modelo/datos/derivados/modelo_dataset_ventana_contiguo.parquet",
    columns=["ID_PERSONA_PR", "ID_CONVOCATORIA", "split", "target_class"])
df["ID_PERSONA_PR"] = df["ID_PERSONA_PR"].astype(str)

sp = {k: set(df.loc[df["split"] == k, "ID_PERSONA_PR"]) for k in ("train", "val", "test")}
print("personas unicas por split:", {k: len(v) for k, v in sp.items()})
print("test ^ train:", len(sp["test"] & sp["train"]))
print("test ^ val:", len(sp["test"] & sp["val"]))
print("test ^ (train|val):", len(sp["test"] & (sp["train"] | sp["val"])))
print("val ^ train:", len(sp["val"] & sp["train"]))

m = df["split"] == "test"
vistos = sp["train"] | sp["val"]
m2 = m & df["ID_PERSONA_PR"].isin(vistos)
print(f"transiciones test: {int(m.sum())} | de personas vistas: {int(m2.sum())} "
      f"({100 * m2.sum() / m.sum():.2f}%)")
```
