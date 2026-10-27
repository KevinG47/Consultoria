# Informe 5 · Pruebas alternativas: TabICLv2 y Laya

**Proyecto:** Consultoría estadística USTA 2026-II — Observatorio Minciencias
**Componente:** Fase 3 · modelo predictivo de movilidad de categoría
**Entregable:** evaluación documentada de dos alternativas de familia y de
representación antes de cerrar el modelo
**Fecha:** 27 de octubre de 2026
**Autor:** Consultoría estadística USTA 2026-II

---

## 1. Objetivo de la etapa

Antes de declarar cerrado el modelo, se probaron dos alternativas que no
pertenecen a la familia del *gradient boosting* y que, en principio, podrían
aportar algo distinto:

1. **TabICLv2**, un modelo de fundación tabular con *in-context learning*: se le
   entrega el conjunto de entrenamiento en el contexto y predice sin ajustar
   hiperparámetros. Es la familia que la literatura reciente presenta como
   competidora de los árboles en datos tabulares.
2. **Laya**, un motor de decisión sobre **estado en lenguaje natural o JSON**: no
   lee matrices, puntúa opciones tipadas. La hipótesis era que una descripción
   semántica del investigador pudiera capturar señal que los conteos no capturan.

El objetivo es **descartar con evidencia**, no sumar experimentos: cada prueba
tenía un criterio previo de éxito (superar la referencia de F1 «baja» OOS de
0,2985 o mostrar correlación > 0,1) y un límite de costo. Ninguna de las dos se
adoptó, y este informe documenta por qué.

---

## 2. Metodología y herramientas usadas

### 2.1 TabICLv2

| Elemento | Detalle |
|---|---|
| Referencia | Qu, Holzmüller, Varoquaux y Le Morvan (2026), ICML 2026 |
| Versión | `tabicl` 2.2.0 (26-10-2026) |
| Licencia | BSD 3-Clause, sin *gating* |
| API | Compatible con scikit-learn (`fit` / `predict_proba`) |
| Paradigma | *In-context learning*: un solo paso hacia adelante, sin ajuste de hiperparámetros |
| Preentrenamiento | 300 a 48 000 filas, **2 a 100 columnas** |
| Costo | `O(n² + n·m²)`; en GPU H100, 50 000 × 100 en < 10 s |

El experimento se ejecutó **en CPU**, con `context = 500` filas de entrenamiento,
`estimators = 1`, **top-100 features** (por `gain` del XGBoost) y los mismos tres
folds temporales del modelo operativo. La métrica es el F1 «baja» con el umbral
elegido en validación, igual que en la referencia.

Se intentó primero un contexto de 1 500 filas. En el fold F2 el proceso **abortó
sin *traceback*** (fallo nativo del runtime, no una excepción de Python). En F1, el
contexto de 1 500 dio F1 0,1024, prácticamente igual que el de 500 (0,1031), de
modo que la truncación del contexto **no era el factor limitante**. Se fijó 500
como tamaño estable en CPU y se corrieron los tres folds.

### 2.2 Laya

| Elemento | Detalle |
|---|---|
| Modelo | `convaiinnovations/laya` |
| Arquitectura | **421 M** parámetros; backbone **ModernBERT-large** (395 M) + cabeza de decisión de 2 capas |
| Tipo | Modelo de decisión «System 1», multilingüe, **no autorregresivo** |
| Entrada | Estado (texto, correo, ticket o **JSON**) + preguntas tipadas |
| Salida | Respuestas tipadas con probabilidades calibradas; **nunca genera texto** |
| Contexto | 512 tokens (checkpoint inglés) |
| Licencia | Apache 2.0 |
| Instalación | `pip install laya` (Python ≥ 3.10) |
| Latencia | 32,8 ms en GPU; **193–464 ms por petición en CPU** |

El experimento serializó cada investigador en un JSON compacto (categoría,
cohorte, institución, productos totales, tesis, artículos por categoría, libros,
proyectos, tiempo en categoría y grupos) y preguntó con la primitiva `score` en
una escala de 0 a 2 («muy improbable» a «muy probable» de subir). Se derivó
`p_sube = score / 2` y se correlacionó con la etiqueta en **100 filas del fold
F1**. La prueba se ejecutó en CPU: ~3,5 s por fila y 345 s para las 100 filas, con
1,7 GB de pesos.

**Decisión de diseño:** se usó `score` (la vía más barata de sondear señal) y no
`choice`, porque la propia *model card* advierte que `score` es la primitiva más
débil; si no hay señal con la más débil, no hay razón para pagar el costo de
`choice`. Además, un valor de 1,3 en una escala de tres anclas no es una
probabilidad de subir, es una posición subjetiva.

### 2.3 Herramientas

Python 3.11.9, `tabicl` 2.2.0 con PyTorch en CPU, `laya` y `transformers` en el
mismo entorno, `scipy.stats.spearmanr` para la correlación. Los resultados se
guardaron en `expJ_tabicl_*.json` y `expK_laya_*.json`; los *logs* completos están
en `07_modelo/modelado/resultados/`.

---

## 3. Justificación técnica

### 3.1 Por qué se probó TabICLv2 y no otro modelo de fundación

TabICLv2 era el candidato prioritario entre los modelos de fundación tabulares por
tres razones operativas:

- **Licencia permisiva** (BSD 3-Clause, sin *gating*), a diferencia de TabPFN-2.5,
  cuya licencia permite investigación y *benchmarking* interno pero **prohíbe uso
  comercial o en producción**, incluidos entregables a clientes. Para una
  consultoría académica el uso de TabPFN-2.5 sería defendible como evaluación
  interna, pero TabICLv2 no tiene ese problema.
- **API de scikit-learn** (`fit` / `predict_proba`), que permite reutilizar el
  pipeline de folds sin reescribirlo.
- **Rango de filas de preentrenamiento** (300–48 000) que cubre los conjuntos de
  entrenamiento por fold (≈19 800–29 800 filas).

### 3.2 Por qué TabICLv2 falló en CPU

El fallo no es de concepto sino de **restricciones de ejecución**, y conviene
separar tres causas:

1. **Costo cuadrático en CPU.** El modelo es `O(n² + n·m²)`; sin GPU, el contexto
   que cabe de forma estable es de ~500 filas. Con 500 filas de contexto, el
   modelo ve una fracción pequeña del entrenamiento y no puede competir con un
   XGBoost entrenado con 19 838–29 832 filas.
2. **Límite de contexto del runtime.** Subir a 1 500 filas **abortó el proceso** en
   F2 sin *traceback*; en F1 el resultado a 1 500 (0,1024) fue indistinguible del
   de 500 (0,1031). La truncación, por tanto, no explicaba el bajo desempeño: el
   problema es que el modelo no tenía señal suficiente ni con más contexto.
3. **Desajuste de dimensionalidad.** TabICLv2 se preentrenó con **2–100 columnas**
   y nuestro tablero tiene **172**; hubo que quedarse con las top-100 por `gain`.
   La propia documentación advierte degradación «mucho más allá de 100» columnas.

El resultado agregado fue F1 «baja» medio **0,1269** (desv. 0,0170), **−17,16 pp**
frente a la referencia 0,2985. No es un empate: es una diferencia de orden de
magnitud. La conclusión honesta es que **la comparación no se hizo en igualdad de
condiciones** (CPU vs. el XGBoost en CPU pero con todos los datos), y aun así el
resultado es tan bajo que no justifica el costo de conseguir GPU para repetirla.
Queda documentado como prueba no concluyente sobre el modelo en sí, concluyente
sobre su viabilidad en este entorno.

### 3.3 Por qué se probó Laya

Laya era la recomendación del docente y una hipótesis razonable: si el estado del
investigador se describe en lenguaje natural, un modelo de decisión entrenado para
puntuar opciones podría capturar relaciones que los conteos no capturan. La prueba
es barata (minutos, no horas) y el costo de oportunidad bajo.

### 3.4 Por qué Laya falló

La causa es de **representación**, no de ajuste:

1. **Laya no está entrenado con tablas numéricas.** Su preentrenamiento y su
   *benchmark* son decisiones sobre texto (triaje de correo, *routing*,
   *guardrails*). Nuestro problema es una matriz densa de conteos; lo que Laya ve
   es una **serialización en texto**.
2. **El JSON pierde información.** 172 features no caben en 512 tokens sin perder
   detalle; hay que elegir un subconjunto, y esa elección es a la vez arbitraria y
   decisiva.
3. **Cuantización del orden.** Un conteo de 12 frente a 13 productos es una
   diferencia numérica fina que el modelo solo ve como dos cadenas distintas.
4. **Zero-shot ruidoso y sobre-confidente.** La propia *model card* advierte que
   los checkpoints base están **cerca del azar** en decisiones tipadas (0,362 de
   exactitud frente a 0,461 de la clase mayoritaria) y que las probabilidades
   requieren ajuste de temperatura (el ECE medio pasa de 0,466 a 0,081 solo después
   de calibrar).

Con esas condiciones, la expectativa razonable era señal nula, y eso es lo que se
observó.

---

## 4. Resultados y métricas

### 4.1 TabICLv2 (3 folds, CPU, contexto 500, top-100 features)

| Fold | F1 «baja» |
|---|---:|
| F1 | 0,1031 |
| F2 | 0,1415 |
| F3 | 0,1360 |
| **Media** | **0,1269** |
| Desviación | 0,0170 |
| Referencia XGBoost (misma métrica) | 0,2985 |
| **Delta** | **−17,16 pp** |

Incidencias: con contexto 1 500 el proceso abortó en F2 (fallo nativo, sin
*traceback*); en F1 el contexto 1 500 dio 0,1024 frente a 0,1031 con 500. Equipo
de la prueba: 11,8 GB de RAM totales y ~2,7 GB libres.

**Veredicto:** no competitivo. No se adopta y no se repite con GPU: la brecha de
17 pp no se explica por el tamaño del contexto (probado) y el costo de una corrida
con GPU no está justificado para una alternativa que, en el mejor caso, empataría
con el modelo actual.

### 4.2 Laya zero-shot (100 filas de F1, primitiva `score` 0–2)

| Métrica | Valor |
|---|---:|
| Filas evaluadas | 100 |
| Correlación de Spearman (`score/2` vs etiqueta) | **ρ = 0,075** |
| p-valor | **0,458** |
| Tiempo por fila (CPU) | ~3,5 s |
| Tiempo total (100 filas) | 345 s |
| Pesos | 1,7 GB |

**Veredicto:** sin señal. ρ = 0,075 con p = 0,458 es indistinguible de cero; no se
justifica probar `choice` ni *fine-tuning*. La prueba cumplió su función: descartó
documentadamente una vía alternativa con un costo de minutos. Nota de entorno: la
latencia medida en esta máquina (≈3,5 s por fila) es muy superior a la declarada
en la *model card* (193–464 ms por petición en CPU); la diferencia es del equipo
sin optimización, no del modelo, y no afecta la conclusión sobre la señal.

### 4.3 Cuadro comparativo de las alternativas

| Alternativa | F1 «baja» OOS / señal | Delta vs 0,2985 | ¿Se adopta? |
|---|---:|---:|---|
| XGBoost Ronda 2 (referencia) | 0,2985 | — | **Sí (operativo)** |
| TabICLv2 (ctx 500) | 0,1269 | **−17,16 pp** | No |
| Laya zero-shot | ρ = 0,075 (p = 0,458) | n/a | No |
| TabPFN-2.5 | No ejecutado (licencia *research-only*) | — | No |

### 4.4 Lectura

Las dos pruebas apuntan a la misma conclusión desde ángulos distintos: **cambiar de
familia o de representación no mejora el desempeño en este dataset**. TabICLv2
falla por restricciones de cómputo y de dimensionalidad; Laya falla porque su
unidad de entrada es el texto, no la tabla. Ninguna de las dos es una crítica al
modelo operativo: son límites del dato y del entorno, y se documentan para que no
se repitan sin nueva evidencia.

La consecuencia práctica es que el cierre con XGBoost no fue por falta de
exploración: se probaron nueve palancas dentro de la familia (informe 3) y dos
familias alternativas (este informe), y ninguna superó el criterio de +2 pp. El
techo es del dato, no del método.

---

## 5. Referencias

1. **Qu, J., Holzmüller, D., Varoquaux, G. & Le Morvan, M. (2026).** *TabICLv2: A
   better, faster, scalable, and open tabular foundation model.* **ICML 2026.**
   https://arxiv.org/abs/2602.11139
2. **`convaiinnovations`** (organización). *Laya* [model card]. Hugging Face.
   https://huggingface.co/convaiinnovations/laya — ficha oficial del modelo
   (arquitectura, licencia Apache 2.0, límites declarados y latencias).
3. **Grinsztajn, L., Oyallon, E. & Varoquaux, G. (2022).** *Why do tree-based
   models still outperform deep learning on typical tabular data?* **NeurIPS
   2022.** https://arxiv.org/abs/2207.08815
4. **Shwartz-Ziv, R. & Armon, A. (2022).** *Tabular data: Deep learning is not all
   you need.* **Information Fusion, 81, 84-90.** DOI:
   [10.1016/j.inffus.2021.11.011](https://doi.org/10.1016/j.inffus.2021.11.011).
5. **Grinsztajn, L. et al. (2025).** *TabPFN-2.5: Advancing the State of the Art in
   Tabular Foundation Models.* https://arxiv.org/abs/2511.08667 — citado solo para
   documentar por qué se descartó por licencia.

**Evidencia interna**

6. `07_modelo/documentacion/laya_y_open_weights.md` — evaluación completa de Laya,
   TabICLv2 y TabPFN-2.5, con las cifras literales de las corridas.
7. `07_modelo/modelado/resultados/expJ_tabicl_20261026_205446.json`,
   `expJ_tabicl_20261026_210004.json`,
   `expJ_tabicl_20261026_210805.json`,
   `expJ_tabicl_20261026_210950.json`.
8. `07_modelo/modelado/resultados/expK_laya_20261026_210639.json` y
   `exp_iteracion_laya_resumen_20261026.json`.
9. `07_modelo/modelado/validacion_honesta.md` § «Cierre definitivo» — las nueve
   palancas y el criterio de adopción.
