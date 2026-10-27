# Model card — Clasificador de transición de categoría (Minciencias)

**Versión:** Ronda 2 · **Estado:** cerrado (techo del dato) · **Fecha:** 26-oct-2026
**Autor:** consultoría estadística USTA 2026-II · **Uso:** revisión priorizada, no automatización

## 1. Qué predice

Para cada **investigador del Observatorio** y cada **convocatoria t**, la
probabilidad de que en la convocatoria siguiente su categoría:

- **suba**,
- **se mantenga**,
- **baje**.

Salida operativa: `p(baja)` + umbral de decisión (0,15). Unidad de predicción:
la **transición** de un individuo entre dos convocatorias consecutivas.

## 2. Datos

| Fuente | Tamaño |
|---|---|
| Censo de investigadores reconocidos | **77 237 registros** (persona × convocatoria) |
| Producción (`produccion_grupos.csv`) | **3 166 629 filas**, 16 columnas |
| Convocatorias cubiertas | **6** (2013, 2014, 2015, 2017, 2019, 2021) |
| Transiciones contiguas modelables | **43 187** (18 116 personas) |

- **Train**: cohortes 2014, 2015, 2017 (19 838 filas).
- **Val**: cohorte 2019 (9 994).
- **Test**: cohorte 2021 (13 355), evaluado **una sola vez**.
- Nunca se usa el test para entrenar, estandarizar ni elegir umbral.

## 3. Modelo

**XGBoost con máscaras estructurales** (un modelo por categoría de origen):

| Categoría origen | Modelo | Restricción |
|---|---|---|
| Junior (IJ) | binario sube / se mantiene | **no puede bajar** (p(baja) = 0) |
| Asociado (I) | tricótomo | — |
| Senior (IS) | tricótomo | — |
| Emérito (IE) | **excluido** | sin transiciones en los datos |

- **172 features** de producción: volumen (4), clase de producto (5),
  tipología (58) y categoría/calidad (105). Sin `ano`. **111 tienen gain > 0 en el
  modelo final (43 en el fold más pequeño, entrenado solo con la cohorte 17)**; las
  otras 61 no se usan.
- Configuración: `n_estimators=100`, `max_depth=7`, `learning_rate=0.05`,
  `subsample=0.8`, `gamma=0.1`, `min_child_weight=1`, `tree_method=hist`,
  pesos de clase balanceados, `random_state=42`.
- Umbral de «baja»: **0,15** (mediana de los umbrales de los folds temporales).

## 4. Métricas en test (cohorte 2019→2021, n = 13 355)

| Métrica | Valor |
|---|---|
| **F1 «baja»** | **0,4234** |
| **Recall «baja»** | **0,7878** |
| **Precisión «baja»** | 0,2895 |
| **F1 macro** | 0,5109 |
| **Brier multiclase** | **0,4692** |
| F1 «se mantiene» / «sube» | 0,6932 / 0,4388 |
| Exactitud | 0,5921 |
| AUC «baja» | 0,8631 |
| Alertas emitidas | 25,7 % de las filas |

Referencias: constante con prevalencias de train → Brier 0,4419 y F1 «baja»
0,1851; el modelo supera el F1 en **+0,238**. Validación temporal (3 folds):
F1 «baja» OOS medio 0,3054 (desv. 0,0295).

**Corrección de prior shift: descartada.** Se estimó la prevalencia de test sin
sus etiquetas (tendencia de cohortes 17–20: 5,4 %–12,0 % para «baja») y se
reproyectaron las probabilidades: el Brier **empeora** en todos los escenarios
(0,4917–0,6054) e incluso con la prevalencia observada (0,4851). El modelo ya
predice 11,6 % de «baja» de media en test; el desajuste es de composición, no de
nivel. **El Brier honesto es 0,4692.**

> **Nota de transparencia (prior shift).** Se probó una corrección de prior
> shift que usó la prevalencia observada de test (10,2 %) para recalibrar
> probabilidades. Se descartó porque empeoraba el Brier (0,4917 vs 0,4692). El
> modelo operativo (Ronda 2) **NO** usa esa corrección; sus métricas se
> calcularon antes del experimento. Precisión adicional: el 0,4917 corresponde al
> escenario con la prevalencia **estimada** sin etiquetas (logit, todas las
> cohortes: 5,4 %); el escenario con la prevalencia **observada** de 10,2 %
> (oráculo) dio 0,4851. Ambos empeoran el 0,4692.


## 5. Limitaciones

1. **Brier peor que la constante** (0,4692 vs 0,4419) por el cambio de
   prevalencia de «baja» **5,2 % → 10,2 %** entre train y test, y por cambio de
   composición. No se corrige sin etiquetas de test.
2. **Umbral sensible a la cohorte**: el óptimo por fold va de **0,08 a 0,29**.
   Se fija 0,15 por mediana; moverlo cambia el recall entre 0,54 y 0,89.
3. **Sobreajuste train-val**: F1 macro **0,83 en train vs 0,50 en val**
   (brecha +0,33). Con 100 árboles y `gamma=0,1` se atenúa, no desaparece.
4. **61 de 172 features con gain 0 en el modelo final** (111 activas; en el fold
   más pequeño, entrenado solo con la cohorte 17, se activan 43).
5. **No hay coautorías en el dato**: `produccion_grupos.csv` registra **1,02
   autores por producto** (máx. 6) porque `id_producto_pd` es personal; solo
   existen 72 226 pares de coautoría en todo el censo. La red de grupos tampoco
   aporta (+0,00 pp).
6. **Solo 5 cohortes históricas**: no alcanza para validar estabilidad del
   umbral ni del Brier entre regímenes.
7. **Nueve palancas probadas y ninguna supera el +2 pp**: regularización,
   selección de features, demografía, trayectoria (+0,78 pp, la mejor), HHI
   institucional + movilidad (+0,47 pp), TabICLv2 (−17,16 pp), Laya zero-shot
   (sin señal), nivel de formación (+0,02 pp) y lags de dos períodos (+0,64 pp).
   El cierre está documentado en `validacion_honesta.md` § «Cierre definitivo».

## 6. Uso recomendado

- **Priorizar revisión humana. NO automatizar decisiones.** El modelo detecta
  ~79 % de los descensos, pero **1 de cada 3,4 alertas es correcta** (precisión
  0,29): sirve para ordenar la cola de revisión, no para decidir solo.
- **Las probabilidades no son confiables** (Brier peor que la constante): usar
  el **ranking** de `p(baja)` y el umbral, no el valor puntual.
- Punto de operación según costo: umbral **0,06–0,08** → recall 0,84–0,80,
  precisión 0,21–0,22 (si no detectar un descenso es caro); umbral **0,20** →
  recall 0,54, precisión 0,25 (si las falsas alarmas cuestan).
- **Recalcular el umbral con cada cohorte nueva**; no congelarlo.

## 7. Reproducibilidad

**Comando exacto (reentrena con 17–20 y evalúa test una vez):**

```powershell
07_modelo\.venv-bayes\Scripts\python.exe 07_modelo/modelado/expE_test.py
```

Requiere `07_modelo/modelado/resultados/spec_final.json` (generado por
`expD_umbral_mediana.py`).

**Hashes SHA-256 de las entradas:**

| Archivo | SHA-256 |
|---|---|
| `07_modelo/datos/derivados/modelo_dataset_ventana_contiguo.parquet` | `97289128AFD5D87E6C60DAA85AE85F8A48FEF30CB539A98622C31F45025D3376` |
| `07_modelo/datos/derivados/features_ventana_t.parquet` | `CBDBC82303962FC3A85A6D7044FCE29D0F25A3D2D477B4358C464CE375F802AC` |
| `01_datos/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv` | `9A55DD87F5F571B1B82A834372F2F037C521AE4F02536F164D427D1C16CA9565` |

**Entorno:** Python 3.11.9 · xgboost **3.2.0** · scikit-learn 1.9.1 ·
pandas 3.1.0 · numpy 2.4.6 · venv `07_modelo/.venv-bayes` · semilla 42.

**Piezas:** `opt_comun.py` (features y folds), `expE_test.py` (entrenamiento y
evaluación final), `pasoA_cv_temporal.py`/`expA_grid.py`–`expD_umbral_mediana.py`
(validación y umbral), `expH_prior_shift.py` (prior shift, descartado) y
`expI_hhi.py`–`expM_lags2.py` (palancas 5 a 9 de la iteración de cierre).
Resultados en `07_modelo/modelado/resultados/*.json`. Bitácora:
`07_modelo/modelado/validacion_honesta.md`.
