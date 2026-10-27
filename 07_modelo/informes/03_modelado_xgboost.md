# Informe 3 · Modelado con XGBoost y máscaras estructurales

**Proyecto:** Consultoría estadística USTA 2026-II — Observatorio Minciencias
**Componente:** Fase 3 · modelo predictivo de movilidad de categoría
**Entregable:** modelo operativo de alerta temprana de descenso de categoría
**Fecha:** 27 de octubre de 2026
**Autor:** Consultoría estadística USTA 2026-II

---

## 1. Objetivo de la etapa

Construir el **modelo operativo** que, para cada investigador reconocido y cada
convocatoria, estime la probabilidad de que en la convocatoria siguiente su
categoría **baje**. El uso previsto no es automatizar la clasificación sino
**priorizar la revisión humana**: ordenar la cola de casos que un comité debería
mirar primero.

El objetivo impone tres requisitos que condicionan el diseño:

1. **Respetar la estructura del fenómeno.** Un Junior no puede descender (no hay
   categoría inferior) y un Emérito no puede ascender (es la cima). Un modelo que
   ignore esas restricciones produce probabilidades imposibles.
2. **Detectar la clase minoritaria sin destruir la calibración.** «Baja» es el
   5,15 % del train y el 10,20 % del test; la métrica de decisión es el F1 de esa
   clase, no la exactitud.
3. **Evaluarse una sola vez en el futuro.** El test (cohorte 2021) se consume al
   final, con el modelo y el umbral ya decididos en validación temporal.

---

## 2. Metodología y herramientas usadas

### 2.1 Arquitectura: un modelo por categoría de origen con máscaras

| Categoría de origen | Modelo | Restricción estructural |
|---|---|---|
| **Junior (IJ)** | Binario: `sube` vs `se_mantiene` | **No puede bajar**: `p(baja) = 0` |
| **Asociado (I)** | Tricótomo: `baja` / `se_mantiene` / `sube` | Sin restricción |
| **Sénior (IS)** | Tricótomo: `baja` / `se_mantiene` / `sube` | Sin restricción |
| **Emérito (IE)** | **Excluido** | Sin transiciones en los datos |

La máscara se aplica en la salida: para Junior, la probabilidad de `baja` se fija
en cero y las dos restantes se renormalizan; para Emérito no hay filas que
modelar. El resultado es un conjunto de probabilidades **siempre compatible con la
escala real** de categorías.

### 2.2 Features

| Familia | N.º | Contenido |
|---|---:|---|
| Volumen | 4 | `n_filas`, `n_productos`, `n_grupos_distintos`, `dias_desde_ultimo` |
| Clase de producto | 5 | Nuevo conocimiento, desarrollo tecnológico, formación, apropiación, no categorizado |
| Tipología | 58 | Artículos, tesis, libros, eventos, patentes, etc. |
| Categoría / calidad | 105 | Categorías editoriales y calidades (A1, A2, B, A, etc.) |
| **Total** | **172** | Sin `ano` |

Las features se construyen con la **ventana de observación previa** a la
convocatoria de destino (véase informe 1). En el modelo final, **111 de las 172
tienen `gain > 0`**; las otras 61 no se usan. En el fold más pequeño (entrenado
solo con la cohorte 17) se activan 43.

### 2.3 Hiperparámetros

| Parámetro | Valor |
|---|---|
| `n_estimators` | 100 |
| `max_depth` | 7 |
| `learning_rate` | 0,05 |
| `subsample` | 0,8 |
| `gamma` | 0,1 |
| `min_child_weight` | 1 |
| `tree_method` | `hist` |
| Pesos de clase | Balanceados |
| `random_state` | 42 |

Estos valores son el resultado de una búsqueda de 54 configuraciones con
validación temporal (palanca 1 del cierre), no una elección arbitraria.

### 2.4 Validación, umbral y test

| Elemento | Diseño |
|---|---|
| Folds | 3 temporales: F1 entrena con 17 y valida en 18; F2 entrena con 17–18 y valida en 19; F3 entrena con 18 y valida en 19 |
| Test | Cohorte 2021 (13 355 filas), evaluado **una sola vez** |
| Umbral | **0,15**, mediana de los umbrales óptimos de los folds (0,12 / 0,27 / 0,15) |
| Métricas | F1 «baja», recall, precisión, F1 macro, Brier multiclase, exactitud y AUC por clase |
| Criterio de adopción de mejoras | +2 pp de F1 «baja» fuera de muestra (media OOS ≥ 0,3185 sobre 0,2985) |

### 2.5 Herramientas

Python 3.11.9 · **XGBoost 3.2.0** · scikit-learn 1.9.1 · pandas 3.1.0 · numpy
2.4.6 · venv `07_modelo/.venv-bayes` · semilla 42. La reproducibilidad está anclada
a los hashes de las entradas (parquet de dataset, features y censo) que constan en
`model_card.md` §7.

---

## 3. Justificación técnica

### 3.1 Por qué XGBoost y no aprendizaje profundo

La evidencia sobre datos tabulares de tamaño medio es consistente: los modelos
basados en árboles siguen siendo el estado del arte y superan a las redes
neuronales en este régimen. Grinsztajn, Oyallon y Varoquaux (2022) muestran que
los árboles mantienen ventaja en tablas típicas —incluidas las de ~10 000 filas—
porque capturan interacciones y umbrales sin necesidad de representaciones
densas, y Shwartz-Ziv y Armon (2022) encuentran que los modelos de *deep learning*
no superan a XGBoost en datos tabulares y que la comparación justa suele favorecer
al *boosting*.

Nuestro caso tiene, además, tres condiciones que refuerzan la elección:

- **Tamaño**: 19 838 a 29 832 filas por fold y 172 columnas; el régimen donde los
  árboles son competitivos.
- **Features dispersas y de cola**: 132 features con >90 % de ceros; los árboles
  manejan naturalmente la dispersión y los cortes, sin embeddings.
- **Interpretabilidad operativa**: `gain` por feature permite auditar qué usa el
  modelo, algo que un comité de revisión necesita.

**Advertencia honesta:** no se localizó un estudio que use XGBoost específicamente
para predecir promoción académica o categorización de investigadores. Los trabajos
del dominio usan Random Forest, SVM, regresión logística o AdaBoost. La elección de
XGBoost se sostiene por la evidencia general sobre datos tabulares, no por una
comparación publicada en este dominio; presentarla como «lo que dice la literatura
del tema» sería inexacto.

### 3.2 Por qué máscaras estructurales

Las transiciones **no son homogéneas por categoría**. El estudio más cercano a
nuestro problema —Godoy, Abramo, D'Angelo y Cortés (2026), con 40 485 observaciones
de las mismas seis convocatorias— estima una regresión ordinal y **rechaza el
supuesto de odds proporcionales** (test de líneas paralelas, p < 0,001); la versión
no restringida, con efectos distintos por umbral, es la que gana (LR = 911, gl =
13, p < 0,001). Es decir: el proceso Junior→Asociado responde a un mecanismo
distinto del Asociado→Sénior.

Ese diagnóstico se traduce en dos hechos del dato:

- **Junior no puede bajar**, porque no existe categoría inferior. Modelar la
  probabilidad de descenso de un Junior sería estimar un evento imposible.
- **Emérito no tiene transiciones** en el censo: no hay filas que modelar y su
  inclusión solo añadiría ruido.

Las máscaras no son una restricción cosmética: **eliminan regiones del espacio de
probabilidad que el fenómeno no permite**. La comparación que fijó la arquitectura
se hizo en validación contra el modelo multiclase plano de la Ronda 1 (173
features, con `ano`): en `argmax`, el F1 «baja» pasó de **0,132 a 0,244** y el F1
macro de **0,394 a 0,498**; con umbral, el F1 «baja» llegó a **0,345**. La
arquitectura final conserva 172 features, sin `ano` [`paso3_xgb_mascaras`].

### 3.3 Por qué el umbral 0,15 y no 0,5

Con clases desbalanceadas y F1 como métrica, el umbral 0,5 es sistemáticamente
demasiado alto. Lipton, Elkan y Narayanaswamy (2014) demuestran que, si las
probabilidades están bien calibradas, el umbral que maximiza F1 es **la mitad del
F1 óptimo**, no 0,5. Nuestro F1 «baja» es 0,4234; la mitad es ≈0,21, y el umbral
elegido (0,15) está en ese orden.

El umbral se fijó con la **mediana de los umbrales óptimos de los folds** (0,12,
0,27 y 0,15), nunca con el test. Es una decisión de punto de operación: bajarlo
sube recall y baja precisión; subirlo hace lo contrario.

### 3.4 Por qué pesos de clase y no SMOTE

Se usaron **pesos de clase balanceados** en el entrenamiento, sin remuestreo
sintético. van den Goorbergh y colaboradores (2022) muestran que las correcciones
de desbalanceo (SMOTE, *undersampling*) **no mejoran la discriminación y degradan
la calibración** de las probabilidades. Nuestro enfoque —pesos + umbral validado—
es el recomendado por esa evidencia, y conserva la prevalencia natural del test,
que es lo que un sistema de alertas necesita.

### 3.5 Por qué la AUC global no es el argumento de venta

La AUC «baja» en test es 0,8631, pero está **inflada por la máscara de Junior**: al
no poder bajar, los Junior se separan trivialmente. En validación, dentro de
categoría, la AUC es 0,672 (Asociado) y 0,634 (Sénior) [`paso3_xgb_mascaras`]. Es
un ejemplo de libro de por qué la AUC global no debe usarse como argumento de
venta; por eso la métrica de decisión es el F1 de «baja» y el Brier se reporta con
su comparación contra la constante.

---

## 4. Resultados y métricas

### 4.1 Validación temporal (3 folds)

| Fold | Entrena | Valida | Evalúa | F1 «baja» (umbral 0,15) |
|---|---|---|---:|---:|
| F1 | 17 | 18 | 19 | 0,2728 |
| F2 | 17–18 | 19 | 20 | 0,3076 |
| F3 | 18 | 19 | 20 | 0,3150 |
| **Media OOS** | | | | **0,2985** (desv. 0,0184) |

Con el umbral propio de cada fold, la media es 0,3054; con el umbral fijo de
operación (0,15) es **0,2985**, que es la referencia contra la que se midieron las
nueve palancas de mejora. Ninguna superó el umbral de +2 pp (media ≥ 0,3185).

### 4.2 Test (cohorte 2019→2021, n = 13 355)

| Métrica | Valor |
|---|---:|
| **F1 «baja»** | **0,4234** |
| **Recall «baja»** | **0,7878** |
| Precisión «baja» | 0,2895 |
| F1 macro | 0,5109 |
| Brier multiclase | 0,4692 |
| F1 «se mantiene» | 0,6932 |
| F1 «sube» | 0,4388 |
| Exactitud | 0,5921 |
| AUC «baja» (global, inflada por la máscara de Junior) | 0,8631 |
| Alertas emitidas | 25,7 % de las filas |

**Lectura operativa.** El modelo detecta **~79 % de los descensos** (recall 0,7878)
emitiendo alerta en una de cada cuatro filas; la precisión de 0,2895 implica que
**1 de cada 3,4 alertas es correcta**. Es un modelo de priorización, no de
decisión: sirve para ordenar la cola de revisión, no para sustituir al comité.

### 4.3 Comparación con referencias

| Referencia | F1 «baja» | Brier |
|---|---:|---:|
| Constante con prevalencias de train | 0,1851 | **0,4419** |
| **XGBoost Ronda 2 (test)** | **0,4234** | 0,4692 |
| XGBoost con corrección de *prior shift* | — | 0,4917 / 0,4851 (peor) |

El modelo supera a la constante en F1 «baja» en **+0,238**, pero **no** en Brier
(0,4692 frente a 0,4419). La causa es el cambio de prevalencia 5,2 % → 10,2 %:
las probabilidades están calibradas para el régimen de train. Se probó una
corrección de *prior shift* con la prevalencia estimada sin etiquetas (0,4917) y con
la prevalencia observada como oráculo (0,4851); ambas empeoran. **El Brier honesto
es 0,4692** y así se reporta.

### 4.4 Curva de operación

| Umbral | Recall | Precisión | Uso sugerido |
|---|---:|---:|---|
| 0,06–0,08 | 0,84–0,80 | 0,21–0,22 | Si no detectar un descenso es caro |
| **0,15** | **0,7878** | **0,2895** | Punto de operación por defecto |
| 0,20 | 0,54 | 0,25 | Si las falsas alarmas cuestan |

El umbral debe **recalcularse con cada cohorte nueva**; congelarlo entre regímenes
degrada el punto de operación.

### 4.5 Diagnóstico de sobreajuste

El F1 macro es **0,83 en train frente a 0,50 en val**: una brecha de +0,33. Con 100
árboles, `gamma=0,1` y `subsample=0,8` la brecha se atenúa, no desaparece. Es
consecuencia de la relación filas/columnas (19,8k–29,8k filas, 172 features) y se
declara como limitación, no se corrige con más regularización (la búsqueda de 54
configuraciones no mejoró el F1 fuera de muestra).

### 4.6 Cierre

| Decisión | Resultado |
|---|---|
| ¿Se adoptó alguna de las 9 palancas? | **No**: la mejor fue trayectoria (+0,78 pp) |
| ¿Se toca el test con otro modelo? | **No**: se consumió una vez con la Ronda 2 |
| Estado | **Cerrado** (techo del dato) |

Las mejoras futuras tendrían que venir de **datos nuevos** (financiación de
proyectos, coautoría real, vinculación contractual), no de más features sobre el
mismo censo. El detalle de las nueve palancas está en `validacion_honesta.md` §
«Cierre definitivo» y en el informe 5.

---

## 5. Referencias

1. **Grinsztajn, L., Oyallon, E. & Varoquaux, G. (2022).** *Why do tree-based
   models still outperform deep learning on typical tabular data?* **NeurIPS
   2022.** https://arxiv.org/abs/2207.08815
2. **Shwartz-Ziv, R. & Armon, A. (2022).** *Tabular data: Deep learning is not all
   you need.* **Information Fusion, 81, 84-90.** DOI:
   [10.1016/j.inffus.2021.11.011](https://doi.org/10.1016/j.inffus.2021.11.011).
3. **Lipton, Z. C., Elkan, C. & Narayanaswamy, B. (2014).** *Thresholding
   Classifiers to Maximize F1 Score.* https://arxiv.org/abs/1402.1892
4. **van den Goorbergh, R., van Smeden, M., Timmerman, D. & Van Calster, B.
   (2022).** *The harm of class imbalance corrections for risk prediction models.*
   **JAMIA, 29(9), 1525-1534.** DOI:
   [10.1093/jamia/ocac093](https://doi.org/10.1093/jamia/ocac093).
5. **Godoy, J. M., Abramo, G., D'Angelo, C. A. & Cortés, J. D. (2026).** *Should I
   stay or should I go? The role of national geographic mobility, gender, age,
   institutional research profiles, and labor market on the career performance of
   the scientific workforce in Colombia.* **Scientometrics, 131(9), 5803-5824.**
   DOI: [10.1007/s11192-026-05716-9](https://doi.org/10.1007/s11192-026-05716-9).
6. **Saito, T. & Rehmsmeier, M. (2015).** *The Precision-Recall Plot Is More
   Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced
   Datasets.* **PLOS ONE, 10(3), e0118432.** DOI:
   [10.1371/journal.pone.0118432](https://doi.org/10.1371/journal.pone.0118432).

**Evidencia interna**

7. `07_modelo/modelado/model_card.md` — model card del clasificador.
8. `07_modelo/modelado/validacion_honesta.md` — bitácora de rondas y cierre de las
   nueve palancas.
9. `07_modelo/modelado/resultados/expE_test_20261026_024016.json` — métricas de
   test.
10. `07_modelo/modelado/resultados/expD_umbral_mediana_20261026_023950.json` —
    umbrales de los folds y umbral mediana.
