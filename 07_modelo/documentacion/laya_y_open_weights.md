# Laya y modelos de fundación tabulares con pesos abiertos

**Proyecto:** Consultoría estadística USTA 2026-II — Observatorio Minciencias
**Componente:** Fase 3 · modelo predictivo de movilidad de categoría
**Fecha:** 26 de octubre de 2026
**Origen:** recomendación del docente (Laya + ingeniería de características + pesos abiertos)

> **Regla de este documento.** Todo dato técnico proviene de la model card oficial
> de Laya en Hugging Face, del repositorio de TabICLv2 y de la model card de
> TabPFN-2.5, consultados el 26-10-2026. Cuando una afirmación es expectativa y
> no hecho verificado, se marca como tal.

---

## §1 · Qué es Laya exactamente

**Laya** (`convaiinnovations/laya`) se define en su model card como un
**«modelo de decisión System 1, multilingüe y no autorregresivo»**: recibe un
**estado** (texto, correo, ticket o **JSON**) y un conjunto de **preguntas
tipadas**, y devuelve **respuestas tipadas con probabilidades calibradas en un
solo paso hacia adelante** (~33 ms en GPU), en más de 100 idiomas.

| Atributo | Valor (model card) |
|---|---|
| Parámetros | **421 M** en total |
| Backbone | **ModernBERT-large** (395 M, bidireccional, ajustado por completo) + cabeza de decisión de 2 capas de transformer, un *option-marker scorer* y una cabeza act/escalate |
| Contexto | 512 tokens en el checkpoint inglés; 1 024 (hasta 8 192) en los otros |
| Salida | **Nunca genera texto**: puntúa opciones y devuelve probabilidades tipadas. «No hay nada que parsear y nada que alucinar» |
| Entrenamiento | **RLCD** (Reinforcement Learning for Calibrated Decisions) contra reglas de puntuación estrictamente propias (*log*, *spherical* y *ranked probability score* para preguntas ordinales) |
| Licencia | **Apache 2.0** |
| Instalación | `pip install laya` (Python ≥ 3.10) |
| Latencia | 32,8 ms en GPU con routing; **193-464 ms por petición en CPU** con checkpoints precargados |

### 1.1 Cómo decide: marcadores de opción

Cada opción de una pregunta se puntúa **en su propio token `[MASK]`** y luego se
aplica *softmax* sobre las opciones de esa pregunta. El espacio de respuestas se
define **en tiempo de petición**, de modo que un esquema nuevo no requiere
reentrenamiento.

### 1.2 Los tres tipos de pregunta

| Tipo | Qué devuelve | Uso típico |
|---|---|---|
| **`choice`** | Distribución sobre `criteria` (opciones) | Clasificación |
| **`score`** | Valor continuo en `[0, n]` (p. ej. 1,84 de 2,0) | Escala ordinal |
| **`noul`** | Probabilidad de que la respuesta sea «sí» | Preguntas booleanas |

### 1.3 Los tres checkpoints

| Checkpoint | Backbone | Params | Contexto | Para qué |
|---|---|---|---|---|
| `convaiinnovations/laya` (raíz) | ModernBERT-large | 421 M | 512 | Inglés, guardrails, triage |
| `laya-multilingual` | mmBERT-base | 322 M | 1 024 (hasta 8 k) | 100+ idiomas |
| `laya-typed-decisions` | ModernBERT-large | 421 M | 1 024 | Los cuatro flujos tipados de su banco de pruebas (0,766 de exactitud) |

### 1.4 Límites que la propia model card declara (importantes para §3)

- **Los checkpoints base están cerca del azar en decisiones tipadas zero-shot:**
  0,362 de exactitud frente a 0,461 de la clase mayoritaria. El 0,766 pertenece
  al checkpoint **ajustado** sobre el banco de pruebas.
- **Las preguntas `score` ordinales son la primitiva más débil** (SST-5 0,372).
- **Sale sobre-confidente:** el ECE medio pasa de 0,466 a 0,081 solo después de
  ajustar una temperatura por (tipo de pregunta, número de opciones).
- `noul` puede seguir la etiqueta (`false:`/`true:`) en lugar del estado.
- El checkpoint raíz **solo funciona en inglés**.

---

## §2 · Cómo podría aplicarse a nuestro problema

### 2.1 La idea: features numéricas → JSON descriptivo → pregunta tipada

Nuestro dato es una tabla de 172 conteos de producción más categoría, cohorte e
institución. Laya no lee tablas: lee **estado en lenguaje natural o JSON**. El
puente es describir cada investigador en un JSON compacto:

```json
{
  "categoria_actual": "Asociado",
  "cohorte": 2017,
  "institucion": "UNIVERSIDAD NACIONAL DE COLOMBIA",
  "productos_totales": 12,
  "tesis_doctorado": 3,
  "tesis_maestria": 1,
  "articulos_a1": 2,
  "articulos_a2": 4,
  "articulos_b": 3,
  "libros": 0,
  "proyectos_id": 2,
  "tiempo_en_categoria_anios": 4,
  "grupos": 2
}
```

Y preguntar:

```json
{
  "subida": {
    "type": "score",
    "instructions": "¿Cuál es la probabilidad de que este investigador
                     suba de categoría en la siguiente convocatoria?",
    "criteria": ["muy improbable", "posible", "muy probable"]
  }
}
```

La respuesta sería un valor continuo en `[0, 2]` (p. ej. 1,3), o —con
`choice`— una distribución entre `baja` / `se mantiene` / `sube`.

### 2.2 Por qué `choice` sería mejor que `score` en este problema

Nuestra etiqueta es **ordinal de tres clases**, no una probabilidad escalar:

- `score` devuelve un número en una escala subjetiva y, según la model card, es
  **la primitiva más débil**. Además, un valor de 1,3 no es una probabilidad de
  subir, es una posición en una escala de tres anclas.
- `choice` con tres opciones devuelve directamente `P(baja), P(mantiene),
  P(sube)`, que es lo que necesitamos para calcular F1.

**Decisión del experimento:** se ejecuta `score` 0-2 como pidió la instrucción
(es la vía más barata de sondear señal) y se deriva `p_sube = score/2` para
correlacionar. La comparación con `choice` queda como prueba posterior si hay
señal.

### 2.3 Qué esperaríamos obtener

Tres escenarios posibles, todos informativos:

1. **Correlación ≈ 0** (lo más probable según §1.4): Laya no aporta en
   zero-shot; se documenta y se cierra la vía sin más costo.
2. **Correlación débil pero positiva (> 0,1):** hay señal semántica en la
   descripción; valdría la pena probar `choice`, fine-tuning ligero o destilar
   sus respuestas como *feature* para el XGBoost.
3. **Correlación sorprendentemente alta (> 0,3):** indicaría que el texto
   describe bien el problema; habría que auditar que no haya fuga en el JSON
   (p. ej., incluir la categoría destino).

---

## §3 · Limitaciones de Laya para datos tabulares

1. **No está entrenado con tablas numéricas.** Su preentrenamiento y su
   benchmark son decisiones sobre **texto** (triaje de correo, *routing*,
   *guardrails*). Nuestro problema es una tabla densa de conteos: la
   representación que Laya ve es una **serialización en texto**, no la matriz.
2. **El JSON pierde información.** 172 features no caben en 512 tokens sin
   perder detalle; hay que elegir un subconjunto, y esa elección es a la vez
   arbitraria y decisiva.
3. **Cuantización del orden.** Un conteo de 12 vs 13 productos es una diferencia
   numérica fina que el modelo solo ve como dos cadenas distintas.
4. **Zero-shot ruidoso y sobre-confidente.** La propia model card advierte que
   los checkpoints base están cerca del azar en decisiones tipadas y que las
   probabilidades requieren ajuste de temperatura.
5. **Costo de oportunidad bajo, pero no cero.** En CPU son ~200-460 ms por
   petición; 100 filas son minutos, no horas. La prueba es barata y por eso vale
   la pena hacerla.

**Conclusión de §3:** Laya es un motor de decisiones sobre **estado semántico**.
Nuestro estado es **numérico**. La expectativa razonable es señal nula o muy
débil; el experimento sirve para **descartar documentadamente** una vía
alternativa, no para reemplazar el modelo.

---

## §4 · Modelos de fundación tabulares con pesos abiertos

### 4.1 TabICLv2 — candidato prioritario

| Atributo | Valor |
|---|---|
| Referencia | **Qu, J., Holzmüller, D., Varoquaux, G. & Le Morvan, M. (2026).** *TabICLv2: A better, faster, scalable, and open tabular foundation model.* ICML 2026. arXiv:[2602.11139](https://arxiv.org/abs/2602.11139) |
| Licencia | **BSD 3-Clause** (permisiva, sin *gating*) |
| Instalación | `pip install tabicl` (2.2.0 al 26-10-2026) |
| API | Compatible con scikit-learn (`fit` / `predict_proba`) |
| Paradigma | *In-context learning*: un solo paso hacia adelante sobre el conjunto de entrenamiento; sin ajuste de hiperparámetros |
| Desempeño declarado | **Supera a XGBoost, CatBoost y LightGBM fuertemente ajustados en TabArena en ~80 % de los conjuntos** |
| Tamaños de preentrenamiento | **300 a 48 000 filas**, 2 a 100 columnas |
| Escalabilidad | Hasta ~500 000 filas con *offload* a CPU/disco, «aunque la exactitud puede degradarse» |
| Costo | \(O(n^2 + nm^2)\); en GPU H100, 50 000 × 100 en < 10 s |

**Por qué es el candidato prioritario:** licencia permisiva, sin registro,
API de sklearn y un rango de filas de preentrenamiento (300-48 000) que cubre
nuestros conjuntos de entrenamiento por fold (≈ 19 800-29 800 filas). Es el
único de los dos que se puede usar sin restricciones de uso.

**Advertencia técnica:** nuestro tablero tiene **172 features** y TabICLv2 se
preentrenó con **2-100 columnas**; la propia documentación advierte degradación
«mucho más allá de 100». Esto obliga a una decisión explícita en el experimento
(usar top-k features o aceptar la degradación) y a documentarla.

### 4.2 TabPFN-2.5 — potente pero con licencia restrictiva

| Atributo | Valor |
|---|---|
| Referencia | **Grinsztajn, L. et al. (2025).** *TabPFN-2.5: Advancing the State of the Art in Tabular Foundation Models.* arXiv:[2511.08667](https://arxiv.org/abs/2511.08667) |
| Licencia | **`tabpfn-2.5-license-v1.1`**: permite investigación, evaluación y benchmarking interno; **prohíbe uso comercial o en producción** (incluye entregables a clientes y decisiones comerciales internas) |
| Límites de uso | **≤ 50 000 muestras** y ≤ 2 000 features |
| Acceso | Repositorio con *gating* (formulario de aceptación) |

**Por qué no es el prioritario:** la licencia restringe el uso en producción y
en entregables. Para una consultoría académica el uso es defendible como
evaluación interna, pero **TabICLv2 no tiene ese problema** y su rango de filas
también nos cubre. Se deja documentado como alternativa de contraste.

### 4.3 Comparación rápida

| | TabICLv2 | TabPFN-2.5 | Laya |
|---|---|---|---|
| Tipo | Fundación tabular | Fundación tabular | Motor de decisión sobre texto/JSON |
| Lee nuestra tabla | **Sí** (matriz) | **Sí** (matriz) | No (JSON serializado) |
| Licencia | BSD-3 | Research-only | Apache 2.0 |
| Filas que cubre | 300-48 k (hasta 500 k con offload) | ≤ 50 k | n/a |
| Costo en CPU | Alto (O(n²)) | Alto | Bajo (~0,2-0,5 s/petición) |
| Prioridad | **1** | 2 | 3 (prueba de concepto) |

---

## §5 · Ingeniería de características: contexto institucional

Tres familias de features construidas con datos que **ya tenemos**, inspiradas en
Godoy et al. (2026):

### 5.1 HHI institucional (concentración de rangos)

Para cada **institución \(i\)** y **cohorte \(c\)**, con \(p_k\) = proporción de
investigadores en la categoría \(k \in \{Junior, Asociado, Sénior, Emérito\}\):

\[
HHI_{i,c} = \sum_{k} p_{k}^{2}
\]

- Rango: \(1/4 \le HHI \le 1\). Un valor alto indica que la institución concentra
  sus investigadores en pocas categorías (típicamente, muchas personas en la
  misma).
- Complemento interpretable: `share_senior = p_{Sénior} + p_{Emérito}`, que es la
  lectura que Godoy et al. dan al índice («mayor densidad de investigadores
  senior»).
- Control de tamaño: `log(1 + n_institucion)`, porque el HHI está
  mecánicamente correlacionado con el tamaño (instituciones de 1-2 personas
  tienen HHI ≈ 1).

**Rezago.** Para la fila (persona, cohorte \(c\)) que predice la transición
\(c \to c+1\), se usa el HHI de la institución **medido en \(c-1\)**. Es el
equivalente de la estrategia `_l1` de Godoy et al. y evita que la composición
contemporánea —que incluye la categoría de la propia persona— contamine la señal.

### 5.2 Movilidad institucional

\[
mov_{i,c} = \mathbb{1}[inst_{i,c} \neq inst_{i,c-1}]
\]

- Vale 1 si la persona cambió de institución entre la cohorte anterior y la
  actual; es la versión «institucional» de la movilidad geográfica que ellos
  miden como cambio de ciudad (nosotros no tenemos ciudad por convocatoria).
- Se acompaña de una bandera de faltante para los casos sin observación previa
  (primera cohorte o institución vacía).

### 5.3 Tamaño de grupo

- `n_grupos_distintos` ya existe en el dataset y actúa como proxy del tamaño de
  la red institucional (lo usó la Ronda 4 de red).
- Se puede complementar con `n_institucion` (§5.1) y con el número de
  integrantes del grupo, si se cruza GrupLAC.

### 5.4 Construcción concreta

| Paso | Detalle |
|---|---|
| Fuente | `01_datos/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv` |
| Columnas | `ID_PERSONA_PR`, `ID_CONVOCATORIA`, `ORDEN_CLAS_PR` (12-15), `INST_FILIA` |
| Normalización | `INST_FILIA` en mayúsculas y sin espacios; IDs con `zfill(10)`; deduplicar (persona, convocatoria) |
| Cobertura | 77 237 registros; **9 326 sin institución (12,1 %)**, que quedan como faltantes con bandera |
| Cruce | por (persona, cohorte) para institución actual y anterior; por (institución, cohorte-1) para el HHI rezagado |

**Riesgos declarados:** (i) el HHI puede correlacionar con la categoría propia
(las instituciones grandes tienen más Sénior y también más Junior); (ii) las
instituciones pequeñas producen HHI extremos; (iii) si la institución cambia de
nombre entre convocatorias, el cruce falla y el rezago se pierde.

---

## §6 · Plan de experimentos priorizado

| Orden | Experimento | Qué responde | Costo | Criterio de avance |
|---|---|---|---|---|
| **1** | **HHI + movilidad institucional** sobre el XGBoost con máscaras | ¿El contexto institucional agrega sobre las 172 features de producción? | Bajo (sin instalaciones) | F1 «baja» OOS medio ≥ 0,3185 (+2 pp) |
| **2** | **TabICLv2** zero-shot en los 3 folds | ¿Un modelo de fundación tabular supera al XGBoost sin ajuste? | Medio (instalar torch + tabicl, CPU lenta) | Superar 0,2985 con el mismo protocolo de umbral |
| **3** | **Laya** zero-shot, 100 filas de F1 | ¿Hay señal semántica en la descripción JSON? | Bajo-medio (instalar laya; ~1 min de inferencia) | Correlación con la etiqueta > 0,1 |
| **4** | **Lags de dos períodos** | ¿Aporta la historia de producción a \(t-2\)? | Bajo | +2 pp |

**Regla común:** nada toca el test (cohorte 21) hasta que un experimento supere
el +2 pp sobre 0,2985. El test se evalúa **una sola vez** y solo si se cumple el
criterio.

**Limitación de hardware:** el equipo tiene 4 núcleos de CPU, 11,8 GB de RAM y
**sin GPU**. TabICLv2 y Laya son viables pero lentos; TabPFN-2.5 y Laya
requieren descargar pesos (cientos de MB a ~1 GB), lo que condiciona el tamaño
de la prueba.

---

## §7 · Resultados de la ejecución (26-10-2026)

Los tres experimentos se corrieron el mismo día, **sin tocar la cohorte 21
(test)**. El criterio de adopción se mantuvo: **+2 pp** sobre 0,2985, es decir,
media OOS ≥ 0,3185.

### 7.1 Experimento 1 · HHI institucional + movilidad

Salida literal del script (`expI_hhi.py`):

```
base: 172 features | nuevas: 6 -> total 178
cobertura HHI lag1: 74.9% de las filas
movilidad institucional observada: 13.89%

variante         folds                       media   desv  F1macro   Brier  t
base_172         [0.2728, 0.3076, 0.315]    0.2985 0.0184   0.4870  0.4196  [0.12, 0.27, 0.15]
hhi              [0.2728, 0.3275, 0.3036]   0.3013 0.0224   0.4859  0.4146  [0.12, 0.19, 0.15]
movilidad        [0.2728, 0.3392, 0.2896]   0.3005 0.0282   0.4899  0.4203  [0.12, 0.18, 0.25]
hhi_movilidad    [0.2728, 0.335, 0.302]     0.3032 0.0254   0.4865  0.4144  [0.12, 0.14, 0.19]

MEJOR: hhi_movilidad -> media 0.3032 (base 0.2985, delta +0.47 pp)
criterio para tocar test: media >= 0.3185
NO cumple el +2 pp: test NO se toca.
```

**Lectura.** El bloque institucional aporta **+0,28 pp** (HHI), **+0,20 pp**
(movilidad) y **+0,47 pp** (ambos), siempre por debajo del umbral. Hay dos
detalles que importan:

- El fold F1 **no se mueve** (0,2728 en las cuatro variantes): en ese fold el
  modelo no usa las features nuevas, probablemente porque el HHI rezagado de la
  cohorte 2013 tiene poca variación y el árbol no encuentra cortes útiles.
- La **desviación entre folds sube** (0,0184 → 0,0254) y el umbral óptimo se
  mueve (F2 pasa de 0,27 a 0,14): la señal es inestable.
- El Brier mejora levemente con HHI (0,4196 → 0,4146), lo que sugiere que la
  variable aporta algo de calibración, no de discriminación.

**Conclusión:** la variable con más respaldo externo (Godoy et al. 2026) **no
supera el criterio** en nuestro dato. Es consistente con el diagnóstico de techo:
el HHI institucional es un correlato del *nivel* de categoría, no del *cambio*
de categoría entre dos convocatorias.

### 7.2 Experimento 2 · TabICLv2 zero-shot

Salida literal (tres corridas, contexto 500, top-100 features, 1 estimador):

```
=== F1 ===
features: top-100 por ganancia del XGBoost base
TabICLv2 | context=500 | estimators=1 | features=100 | device=cpu
  F1: F1 baja=0.1031 | macro=0.2224 | brier=0.3769 | t=0.03 | 58s

=== F2 ===
  F2: F1 baja=0.1415 | macro=0.2995 | brier=0.4741 | t=0.07 | 98s

=== F3 ===
  F3: F1 baja=0.1360 | macro=0.2867 | brier=0.4785 | t=0.04 | 93s
```

| | F1 | F2 | F3 | Media | Desv. | Δ vs XGBoost |
|---|---|---|---|---|---|---|
| **TabICLv2** (ctx 500, top-100) | 0,1031 | 0,1415 | 0,1360 | **0,1269** | 0,0170 | **−17,16 pp** |
| **XGBoost máscaras** (172) | 0,2728 | 0,3076 | 0,3150 | **0,2985** | 0,0184 | — |

**Control de robustez al contexto:** en F1 se corrió también con **1 500 filas**
de contexto (3×) y el resultado fue **0,1024**, prácticamente idéntico a 0,1031.
Es decir, **el tamaño del contexto no es el cuello de botella** en este rango: la
diferencia con el XGBoost no se explica por la truncación.

**Conclusión, con la advertencia honesta:** TabICLv2 queda **muy por debajo** del
XGBoost en nuestro problema. No es una prueba justa de su techo (contexto
truncado, 100 de 172 features, sin ajuste), pero sí responde la pregunta
práctica: **en este entorno (4 núcleos, sin GPU, 11,8 GB de RAM) no es una
alternativa usable**, y aun con más contexto no mostró señal de mejora.

### 7.3 Experimento 3 · Laya zero-shot

Salida literal (`expK_laya.py --n 100`):

```
fold F1 | filas de evaluación: 8164 | muestra: 100
distribución de la etiqueta en la muestra: {0: 4, 1: 71, 2: 25}
cargando Laya (convaiinnovations/laya) en CPU ...
modelo cargado en 21.6s
  20/100 ... (81s)
  40/100 ... (145s)
  60/100 ... (210s)
  80/100 ... (280s)
  100/100 ... (345s)

correlaciones: {"spearman_score_vs_y": 0.075, "pearson_score_vs_y": 0.1035,
"spearman_p": 0.4583900090514819, "spearman_score_vs_sube_bin": 0.0568,
"media_score_baja": 0.778, "media_score_mantiene": 0.802,
"media_score_sube": 0.855, "n_validas": 100, "n_errores": 0}
SEÑAL > 0.1: no; Laya no aporta en zero-shot
```

**Lectura.** La correlación de Spearman entre el `score` de Laya y la etiqueta
real es **0,075 (p = 0,458)**: no significativa y por debajo del umbral de 0,1.
Las medias por clase son 0,778 / 0,802 / 0,855 — un orden correcto pero con una
diferencia de 0,077 en una escala de 0 a 2, indistinguible del ruido. El modelo
además emitió una advertencia de calibración («invalid temperatures ... treat
confidence as uncalibrated»).

**Conclusión:** **Laya no aporta señal en zero-shot** para este problema, tal
como anticipaba §3: es un motor de decisión sobre estado semántico y nuestro
estado es numérico. No se justifica fine-tuning: si el zero-shot no captura
nada, el ajuste solo aprendería el mapeo de 100 ejemplos.

### 7.4 Decisión de la iteración

| Experimento | Mejor resultado | Δ vs 0,2985 | ¿Supera +2 pp? |
|---|---|---|---|
| 1. HHI + movilidad | 0,3032 | **+0,47 pp** | No |
| 2. TabICLv2 (ctx 500) | 0,1269 | −17,16 pp | No |
| 3. Laya zero-shot | ρ = 0,075 (p = 0,458) | n/a | No |

**Ninguna palanca supera el +2 pp. El test (cohorte 21) permanece intacto y no
hay plan de evaluación en test para esta iteración.** Queda pendiente la palanca
4 (lags de dos períodos), que se probará con el mismo protocolo.

### 7.5 Lecciones operativas (para reproducir)

- **Sandbox:** `huggingface_hub` intenta escribir en `%USERPROFILE%\.cache`, que
  está fuera del workspace; hay que fijar `HF_HOME` a `07_modelo/.cache/huggingface`
  (ya incorporado en los scripts).
- **RAM:** con 11,8 GB totales y ~2,7 GB libres, TabICL con contexto 1 500
  **crasheó** en F2 (proceso nativo, sin traza de Python); con 500 filas corre
  estable. Laya (1,7 GB de pesos) solo carga si no hay otro proceso pesado.
- **Tiempo:** HHI ≈ 9 min (4 variantes × 3 folds); TabICL ≈ 60-100 s por fold;
  Laya ≈ 3,5 s por fila en CPU (345 s para 100 filas).
- **Reproducibilidad:** `expI_hhi.py`, `expJ_tabicl.py`, `expK_laya.py` en
  `07_modelo/modelado/`; resultados en `resultados/expI_hhi_*.json`,
  `expJ_tabicl_*.json`, `expK_laya_*.json` y el consolidado
  `resultados/exp_iteracion_laya_resumen_20261026.json`.
