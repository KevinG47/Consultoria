# Validación honesta del XGBoost con máscaras (pasos A–E)

Fecha: 26-oct-2026 (02:24 UTC). Scripts: `pasoA_cv_temporal.py`,
`pasoB_baseline_prevalencia.py`, `pasoC_sobreajuste.py`,
`pasoD_importancia.py`, `pasoE_test_final.py`, entrenador común
`modelo_mascaras.py`. Resultados en `resultados/paso[ABCDE]_*.json`.

Modelo evaluado: **XGBoost con máscaras estructurales sin `ano`** (IJ binario,
Asociado y Senior tricótomos, Emérito excluido; 172 features).

## A. Validación cruzada temporal del umbral

Cohortes de destino: 17=13→14, 18=14→15, 19=15→17, 20=17→19, 21=19→21.

| Fold | train | val (umbral) | eval | t | F1 baja OOS | F1 macro | Brier |
|---|---|---|---|---|---|---|---|
| 1 | 17,18 | 19 | 20 | 0,14 | **0,3332** | 0,4916 | 0,4322 |
| 2 | 17,18,19 | 20 | 21 | 0,08 | **0,4334** | 0,5231 | 0,4397 |
| 3 | 17,18,19,20 | 21 | 21 (en muestra) | 0,13 | 0,4246 | 0,5214 | 0,4592 |
| 3-alt | 17…20 | — | 21 con t de fold 2 (0,08) | 0,08 | **0,4206** | 0,5083 | 0,4592 |

- Media OOS (folds 1 y 2): **0,3833** · desv. 0,0501.
- Media OOS (folds 1, 2 y 3-alt): **0,3957** · desv. **0,0445**.
- Criterio (media ≥ 0,25 y desv. ≤ 0,08): **CUMPLE** en ambas lecturas.

## B. Baseline de prevalencia

Prevalencias de train (17,18,19): baja 0,0515 / mantiene 0,7799 / sube 0,1686.
Test: baja 0,1020 / mantiene 0,7231 / sube 0,1749.

| Modelo | t | F1 baja test | precisión | recall | F1 macro | Brier |
|---|---|---|---|---|---|---|
| Constante (prevalencias de train) | 0,01 | 0,1851 | 0,1020 | 1,0000 | 0,0617 | 0,4419 |
| XGBoost con máscaras | 0,08 | **0,4334** | 0,3087 | 0,7269 | 0,5231 | 0,4397 |

El baseline predice «baja» para todo (umbral 0,01): su F1 de «baja» es
2p/(1+p) = 0,185 y su F1 macro se hunde a 0,062. El modelo lo supera en
**+0,2483** de F1 «baja».

## C. Sobreajuste

| n_estimators | F1 train | F1 val | Brier val |
|---|---|---|---|
| 100 | 0,7520 | **0,5141** | 0,4352 |
| 200 | 0,8275 | 0,4981 | **0,4260** |
| 400 | 0,8978 | 0,4711 | 0,4312 |
| 800 | 0,9535 | 0,4470 | 0,4507 |

- Regla (train > 0,70 y val < 0,55): **SOBREAJUSTE**. Brecha train−val en
  F1 macro: **+0,3294**.
- La curva muestra sobreajuste progresivo: a 800 árboles el train llega a 0,9535
  y el val cae a 0,4470. El mejor val en F1 macro es 100 árboles (0,5141); el
  mejor Brier val es 200 (0,4260).
- Consecuencia: el modelo se queda con 200 árboles por Brier, declarando el
  sobreajuste; no se ajusta más en esta ronda.

## D. Importancia (gain)

Top 5: `n_tipologia_TESIS_DE_MAESTRIA` (4,21 %), `n_tipologia_TESIS_DE_DOCTORADO`
(2,62 %), `n_clase_NUEVO_CONOCIMIENTO` (2,03 %),
`n_clase_FORMACI_N_DE_RECURSO_HUMANO` (1,93 %), `n_tipologia_SPIN_OFF` (1,77 %).

| Familia | gain | features |
|---|---|---|
| Tipología | **50,80 %** | 58 |
| Categoría / calidad | 36,96 % | 105 |
| Clase de producto | 7,35 % | 5 |
| Producción (filas, productos, grupos, días) | 4,89 % | 4 |
| Demografía | 0 % | 0 (no existen en este feature set) |

Domina **tipología** (producción de conocimiento), no el volumen de producción.

## E. Evaluación final en test (una sola vez)

Modelo entrenado con 17,18,19,20 (29 832 filas); umbral = media de los folds
(0,14 / 0,08 / 0,13) = **0,1167**; test = 13 355 filas.

| Métrica | Valor |
|---|---|
| **F1 «baja»** | **0,4223** |
| Recall «baja» | 0,7438 |
| Precisión «baja» | 0,2949 |
| F1 macro | 0,5181 |
| Brier | 0,4592 |
| Exactitud | 0,5921 |
| AUC «baja» | 0,8631 |
| Alertadas | 25,72 % |

Matriz de confusión (real × predicho): [[1013, 265, 84], [2090, 5685, 1882],
[332, 795, 1209]].

**Este es el número final: F1 «baja» = 0,4223 en test, con umbral fijado a
priori por la media de los folds.**

## Advertencias

- El Brier en test (0,4592) es **peor** que el de la constante con prevalencias
  de train (0,4419): con el desplazamiento de prevalencia (baja 5,2 % en train
  → 10,2 % en test) las probabilidades quedan descalibradas aunque el ranking y
  el F1 de «baja» sean mucho mejores. El F1 de «baja» es la métrica de decisión.
- El Fold 3 evalúa sobre su propio val (en muestra); por eso se reporta el
  Fold 3-alt con el umbral del Fold 2 y se calcula la media OOS sin él.
- Test se usó en los folds 2, 3 y en la evaluación final, como pedía el diseño
  A–E; no se vuelve a usar en esta ronda.

---

# Ronda 2 (optimización A–E) — solo validación temporal, test intacto hasta E

26-oct-2026 (02:40 UTC). Scripts: `expA_grid.py`, `expB_features.py`,
`expC_demografia.py`, `expD_umbral_mediana.py`, `expE_test.py`, utilidades
`opt_comun.py`. Folds **dentro de las cohortes pre-test** (17, 18, 19, 20):

| Fold | train | val | eval |
|---|---|---|---|
| F1 | 17 | 18 | 19 |
| F2 | 17, 18 | 19 | 20 |
| F3 | 18 | 19 | 20 |

Test (cohorte 21) **no se toca** en A–D.

## A. Grid de regularización (54 combinaciones × 3 folds)

Mejor: **n_estimators=100, min_child_weight=1, gamma=0,1, subsample=0,8**
→ F1 «baja» OOS media **0,2985** (desv. 0,0184), F1 macro 0,4870, Brier 0,4196.
Referencia (200, 1, 0, 0,8): media 0,2937 (desv. 0,0284). Tabla completa de 54
filas en `resultados/expA_grid_20261026_023713.json`.

## B. Reducción de features

| k | F1 baja OOS media | desv. |
|---|---|---|
| 172 | **0,2985** | 0,0184 |
| 120 | 0,2819 | 0,0167 |
| 80 | 0,2819 | 0,0167 |
| 50 | 0,2953 | 0,0239 |

Se queda **k = 172**. Dato relevante: en el fold más pequeño (solo cohorte 17) solo
**43 de las 172 features tienen gain > 0**; en el modelo final (17–20) son **111**
activas y **61 en cero**. En aquel fold, por eso, top-120 y top-80 daban predicciones
idénticas (máx. |Δp| = 0,0).

## C. Demografía (género, edad, departamento, institución; 27 columnas)

| Modelo | F1 baja OOS media | desv. | F1 macro | Brier |
|---|---|---|---|---|
| sin demografía | **0,2985** | 0,0184 | 0,4870 | 0,4196 |
| con demografía | 0,2983 | 0,0295 | 0,4873 | 0,4141 |

Δ = **−0,02 pp** → no cumple el criterio de +2 pp: **no se queda** (aunque el
Brier mejora 0,0055).

## D. Umbral estable (mediana de folds)

Umbrales por fold: 0,12 / 0,27 / 0,15 → **mediana t = 0,15**.
F1 «baja» OOS: 0,2655 (eval 19), 0,3357 (eval 20), 0,3150 (eval 20) →
**media 0,3054**, desv. 0,0295 (con umbral propio por fold: 0,2985 / 0,0184).

## E. Evaluación final en test (una sola vez)

Modelo: config A + 172 features, sin demografía; entrenado con 17–20
(29 832 filas); umbral 0,15; test 13 355 filas.

| Métrica | Nuevo | Anterior | Δ |
|---|---|---|---|
| F1 «baja» | **0,4234** | 0,4223 | +0,0011 |
| Recall «baja» | 0,7878 | 0,7438 | +0,0440 |
| Precisión «baja» | 0,2895 | 0,2949 | −0,0054 |
| F1 macro | 0,5109 | 0,5181 | −0,0072 |
| Brier | 0,4692 | 0,4592 | +0,0100 |

**Veredicto: mejora nominal de +0,0011 en F1 «baja», dentro del ruido.** No es
una mejora sustantiva: el cambio real es el umbral más alto (0,15 frente a
0,1167), que sube el recall a 0,788 y baja la precisión a 0,290, con F1 macro y
Brier algo peores. El modelo con máscaras sigue siendo el mismo; la ronda deja
una configuración más simple (100 árboles, gamma 0,1) y más estable.

---

# Ronda 3 (features de trayectoria) — techo del dato

26-oct-2026 (03:28 UTC). Scripts: `trayectoria.py`, `expF_trayectoria.py`.
Features nuevas por `(ID_PERSONA_PR, ID_CONVOCATORIA)`:

| Feature | Definición | Spearman con la clase |
|---|---|---|
| `tiempo_en_categoria` | convocatorias consecutivas en la categoría actual | +0,058 |
| `historial_bajas` | nº de bajadas hasta t (incluye la transición que termina en t) | +0,087 |
| `historial_subidas` | nº de subidas hasta t | −0,124 |
| `momentum_produccion` | `n_productos(t)/(n_productos(t−1)+1)`, 1,0 si no hay t−1 | +0,045 |
| `produccion_normalizada` | `n_productos(t)` / mediana de su categoría en t | **+0,182** |

Las **4 features conceptuales ocupan 5 columnas** (bajas y subidas van
separadas) → el modelo pasa de 172 a **177** features.

## Ablación (3 folds, config ronda 2)

| Variante | F1 «baja» OOS media | desv. | F1 macro | Brier |
|---|---|---|---|---|
| sin nuevas (172) | 0,2985 | 0,0184 | 0,4870 | 0,4196 |
| + tiempo_en_categoria | 0,2958 | 0,0166 | 0,4863 | 0,4198 |
| + historial (2) | 0,2972 | 0,0178 | 0,4861 | 0,4202 |
| + momentum | 0,3048 | 0,0271 | 0,4883 | 0,4172 |
| **+ producción normalizada** | **0,3063** | 0,0246 | 0,4876 | 0,4185 |
| + todas (5) | 0,3003 | 0,0249 | 0,4861 | 0,4166 |

Mejor: **producción normalizada, +0,78 pp** — muy por debajo del umbral de
**+2 pp (0,3185)** fijado para volver a tocar test. El fold 1 da idéntico en
todas las variantes porque entrena solo con la cohorte 17 (primeras
observaciones: las features de trayectoria son casi constantes).

## Decisión

**Test no se toca** (coherente con el criterio). Las features de trayectoria
**no aportan**: el mejor caso suma 0,78 pp y la variante «todas» incluso resta.
El modelo se cierra con la configuración de la **ronda 2** (100 árboles,
`gamma=0,1`, umbral 0,15: F1 «baja» 0,4234, recall 0,788) y se documenta como
**techo del dato, no del método**: 172 features de producción, 19,8k–29,8k
filas de entrenamiento y un cambio de régimen 2019→2021 que ya no se puede
capturar con más tuning ni con trayectoria.

---

# Ronda 4 (red de coautorías) — el CSV no tiene coautorías

26-oct-2026 (04:07 UTC). Scripts: `red_features.py`, `expG_red.py`.
Fuente: `produccion_grupos.csv` (1,26 GB, 3 166 629 filas, 16 columnas).

## Hallazgo previo: no hay lista de coautores

- 1 642 283 productos distintos; **1,02 autores por producto de media, máximo 6**.
- `id_producto_pd` es personal (p. ej. `ART-0000045012-144` contiene el id de la
  persona): **solo 72 226 pares (i<j) de coautoría en todo el censo**.
- Conclusión: la coautoría por producto compartido es **degenerada** y no puede
  alimentar un modelo. La única estructura social del archivo es
  `cod_grupo_gr` (grupo de investigación): 7 467 grupos, tamaño medio 9,9,
  máximo 137. La red se construyó sobre **co-membresía de grupo**, que es el
  análogo operativo disponible.

## Features construidas (246 694 pares persona-convocatoria, cobertura 94,4 %)

| Feature | Definición | Rango observado |
|---|---|---|
| `n_companeros_distintos` | personas distintas con las que comparte grupo en t | 0–252 (mediana 13) |
| `companeros_que_subieron` | compañeros con subida en la transición que termina en t−1 | 0–30 |
| `companeros_que_bajaron` | ídem para bajadas | 0–11 |
| `centralidad_grado` | grado normalizado por el máximo de la convocatoria | 0–1 |
| `n_grupos_distintos_red` | grupos distintos en t (**verificación**) | 1–13 |
| `companero_categoria_modal` | categoría ordinal modal de sus compañeros (proxy de «categoría del coautor más frecuente») | 0–15 |

**Verificación de (e):** `n_grupos_distintos` del dataset coincide **exactamente**
(correlación 1,0000, igualdad 100 %) con `n_grupos_distintos_red`: la feature
existente ya estaba calculada en la ventana correcta. Es un duplicado, como
sospechaba el encargo.

## Ablación (3 folds, config Ronda 2, 172 + 6 = 178 features)

| Variante | F1 «baja» OOS media | desv. | F1 macro | Brier |
|---|---|---|---|---|
| sin red (172) | 0,2985 | 0,0184 | 0,4870 | 0,4196 |
| + compañeros | 0,2932 | 0,0181 | 0,4898 | 0,4187 |
| + movilidad de pares | 0,2985 | 0,0184 | 0,4870 | 0,4196 |
| + centralidad | 0,2981 | 0,0214 | 0,4894 | 0,4192 |
| + n_grupos (duplicado) | 0,2985 | 0,0184 | 0,4870 | 0,4196 |
| + categoría modal del par | 0,2919 | 0,0251 | **0,4901** | 0,4189 |
| + todas (6) | 0,2944 | **0,0144** | 0,4896 | **0,4179** |

Mejor: **+0,00 pp** (movilidad de pares empata y no se usa en ningún split).
El umbral para tocar test era **0,3185**: no se alcanza.

## Decisión

**Test no se toca.** La red **no aporta** en este censo. Se cierra con la
**Ronda 2** (100 árboles, `gamma=0,1`, umbral 0,15): F1 «baja» **0,4234**,
recall **0,7878**, precisión 0,2895, F1 macro 0,5109, Brier 0,4692.

Cierre definitivo: **techo del dato, no del método**. Cuatro rondas
independientes (tuning, selección/ampliación de features, trayectoria, red) no
mueven el F1 «baja» de ~0,42. Lo que falta no es modelado: faltan cohortes
históricas (solo 5), faltan features que el censo no publica y hay un cambio de
régimen 2019→2021 (prevalencia de «baja» 5,2 % → 10,2 %) que ningún ajuste
sobre estas features puede anticipar.

---

# Ronda 5 (corrección de Brier por cambio de prevalencia) — no aplica

26-oct-2026 (04:20 UTC). Script: `expH_prior_shift.py`. La prevalencia de test
se **estima sin sus etiquetas** por tendencia de las cohortes 17–20; las
etiquetas de test se usan solo para medir el Brier.

Prevalencias con etiqueta disponible (baja): cohorte 17 = 0,0787; 18 = 0,0426;
19 = 0,0430; 20 = 0,0730. Train (17–20) = 0,0587.

Estimaciones de la cohorte 21 (sin etiquetas):

| Método | p(baja) estimada | Brier corregido |
|---|---|---|
| Lineal, todas las cohortes | 0,0552 | 0,4935 |
| Lineal, últimas 3 | 0,0833 | 0,5661 |
| Lineal, últimas 2 | 0,1031 | 0,5868 |
| Logit, todas | 0,0541 | **0,4917** (mejor) |
| Logit, últimas 3 | 0,0870 | 0,5830 |
| Logit, últimas 2 | 0,1199 | 0,6054 |
| *Oráculo (prevalencia observada)* | *0,1020* | *0,4851* |

**Ningún escenario baja del Brier original (0,4692) ni de la constante (0,4419)**
— y tampoco el oráculo. Motivo: el modelo ya predice de media **11,6 %** de
«baja» en test (porque usa las features, no solo el prior), así que reescalar
por la prevalencia **sobrecorrige**. El desajuste no es de **nivel** sino de
**composición**: quiénes bajan en 2021 no son los mismos que en 2019, y eso no
se arregla reweightando sin etiquetas.

**Conclusión:** la corrección de prior shift **se descarta**; el Brier honesto
del modelo es **0,4692** y así queda documentado en `model_card.md`.

---

# Cierre y techo del dato (decisión final, 26-oct-2026)

Decisión tomada con Kevin: **cerrar con la Ronda 2**. No se invierte en el
modelo de dos etapas: el prior shift no arregla el Brier y la evidencia de
cuatro rondas dice que el límite es del dato.

## Las cuatro palancas probadas

| Ronda | Palanca | Mejor resultado OOS | Δ vs 0,2985 |
|---|---|---|---|
| 2 | 54 configuraciones de regularización (A) | 0,2985 (100 árboles, mcw 1, gamma 0,1, sub 0,8) | **+0,50 pp** vs referencia 0,2937 |
| 2 | reducción de features a top 50/80/120 (B) | 0,2985 (top 172) | **+0,00 pp** |
| 2 | demografía: género, edad, depto, institución (C) | 0,2983 | **−0,02 pp** |
| 3 | 5 features de trayectoria (F) | 0,3063 (producción normalizada) | **+0,78 pp** |
| 4 | 6 features de red de grupos (G) | 0,2985 (empata) | **+0,00 pp** |
| 5 | corrección de prior shift | Brier 0,4917 (peor que 0,4692) | **no aplica** |

Umbral de decisión para volver a test: **0,3185** (+2 pp). **Nunca se alcanzó.**

## Por qué es techo del dato y no del método

1. **Cinco cohortes** históricas (2013, 2014, 2015, 2017, 2019): no hay
   suficiente historia para separar tendencia de ruido.
2. **El censo no publica las variables que la literatura usa** (financiación,
   movilidad internacional, productividad por proyecto). Las 172 features son
   todas de producción y **111 tienen gain > 0 en el modelo final** (43 en el fold
   más pequeño, entrenado solo con la cohorte 17).
3. **No existen coautorías** en el dato: 1,02 autores por producto.
4. **Cambio de régimen 2019→2021**: la prevalencia de «baja» pasa de 5,2 % a
   10,2 % y quiénes bajan cambia de composición. Ni el reweighting ni más
   features de producción lo anticipan (el oráculo de prevalencia tampoco mejora
   el Brier).
5. **Sobreajuste estructural**: con 19,8k–29,8k filas y 172 columnas, el modelo
   memoriza (0,83 train vs 0,50 val) antes de generalizar más.

## Modelo final

**Ronda 2** — XGBoost con máscaras, 100 árboles, `gamma=0,1`, `subsample=0,8`,
umbral 0,15. Test (13 355 filas): **F1 «baja» 0,4234 · recall 0,7878 ·
precisión 0,2895 · F1 macro 0,5109 · Brier 0,4692**. Documentado en
`model_card.md`.

# Cierre definitivo: nueve palancas y ninguna supera el umbral (27-oct-2026)

Con esta iteración se completan las nueve palancas que el plan contemplaba. El
criterio de adopción nunca cambió: una palanca se adopta solo si mejora el F1
«baja» fuera de muestra en **>= 2 pp**, es decir, media OOS **>= 0,3185** sobre
0,2985. **Ninguna lo logró.** El test (cohorte 21) sigue evaluado una sola vez
con el modelo de la Ronda 2.

## Las nueve palancas

| # | Palanca | Mejor F1 "baja" OOS | Desv. | Δ vs 0,2985 | Veredicto |
|---|---|---|---|---|---|
| 1 | Regularización (54 configuraciones) | 0,2985 | 0,0184 | 0,00 | define la base de la Ronda 2 |
| 2 | Selección de features (top 50/80/120) | 0,2985 | 0,0184 | 0,00 | sin efecto |
| 3 | Demografía (género, edad, depto, institución) | 0,2983 | 0,0295 | −0,02 pp | descartada |
| 4 | Trayectoria (5 features) | 0,3063 | 0,0246 | +0,78 pp | no alcanza |
| 5 | HHI institucional + movilidad (Godoy et al.) | 0,3032 | 0,0254 | +0,47 pp | no alcanza |
| 6 | TabICLv2 zero-shot (modelo de fundación) | 0,1269 | 0,0170 | −17,16 pp | no competitivo |
| 7 | Laya zero-shot (100 filas) | ρ = 0,075 (p = 0,458) | — | sin señal | no aporta |
| 8 | Nivel de formación (`NME_NIV_FORM_PR`) | 0,2987 | 0,0232 | +0,02 pp | sin efecto |
| 9 | Lags de dos períodos (t−1 y t−2) | 0,3049 | 0,0243 | +0,64 pp | no alcanza |

Fuera de la tabla quedan dos ensayos que no son palancas de F1: la **red de
grupos** (Ronda 4, +0,00 pp) y la **corrección de prior shift** (ataca el Brier,
no el F1, y lo empeoró: 0,4917/0,4851 frente a 0,4692).

## Salidas literales de las dos últimas palancas

**Palanca 8 — nivel de formación** (`expL_nivel_formacion.py`):

```
distribucion de nivel de formacion en el censo (persona x convocatoria):
Doctorado                   22534
Maestria/Magister           14846
Postdoctorado                3616
Especialidad Medica           995
Especializacion               600
Pregrado/Universitario        577
No disponible                  14
Cursos de corta duracion        2
Secundario                      2
Perfeccionamiento               1
faltantes (no disponible o sin registro): 0 (0.00% de las filas del dataset)
cobertura del cruce: 100.00% de las filas

variante         folds                       media   desv  F1macro   Brier  t
base_172         [0.2728, 0.3076, 0.315]    0.2985 0.0184   0.4870  0.4196  [0.12, 0.27, 0.15]
ordinal          [0.2627, 0.3292, 0.2823]   0.2914 0.0279   0.4873  0.4151  [0.09, 0.17, 0.23]
onehot           [0.2709, 0.3278, 0.2974]   0.2987 0.0232   0.4899  0.4130  [0.12, 0.17, 0.2]
ordinal_binario  [0.2627, 0.3292, 0.2823]   0.2914 0.0279   0.4873  0.4151  [0.09, 0.17, 0.23]

MEJOR: onehot -> media 0.2987 (base 0.2985, delta +0.02 pp)
NO cumple: test NO se toca.
```

**Palanca 9 — lags de dos períodos** (`expM_lags2.py`):

```
base: 172 features | lag1: 8 | lag2: 8
cobertura lag1: 56.7% | cobertura lag2: 31.8%

variante         folds                       media   desv  F1macro   Brier  t
base_172         [0.2728, 0.3076, 0.315]    0.2985 0.0184   0.4870  0.4196  [0.12, 0.27, 0.15]
lag1             [0.2728, 0.3314, 0.3106]   0.3049 0.0243   0.4902  0.4180  [0.12, 0.21, 0.19]
lag2             [0.2728, 0.3076, 0.315]    0.2985 0.0184   0.4870  0.4196  [0.12, 0.27, 0.15]
ambos_lags       [0.2728, 0.3314, 0.3106]   0.3049 0.0243   0.4902  0.4180  [0.12, 0.21, 0.19]

MEJOR: lag1 -> media 0.3049 (base 0.2985, delta +0.64 pp)
NO cumple: test NO se toca.
```

## Lectura

1. **El nivel de formación no aporta nada** (+0,02 pp con one-hot; con código
   ordinal incluso empeora −0,71 pp). La razón es estructural: el 52,2 % de las
   observaciones del dataset son doctorado y el 86,6 % son doctorado o maestría,
   de modo que la variable es casi constante en la población reconocida. Era la
   última variable del censo con anclaje directo en los criterios de Minciencias
   (`documentacion/criterios_minciencias.md`) y quedó descartada con evidencia.
2. **Los lags de dos períodos tampoco.** El lag de t−1 aporta +0,64 pp y el de
   t−2 **no lo usa el modelo**: la variante con ambos rezagos reproduce
   exactamente el resultado de lag1, y la de solo lag2 reproduce la base. Con
   68,2 % de valores imputados en t−2, la señal no existe.
3. **El orden de magnitud es el mismo en las nueve palancas**: entre −0,02 y
   +0,78 pp cuando la palanca era razonable, y negativo cuando se cambió de
   familia de modelo (TabICLv2) o de representación (Laya). El techo es del dato.

## Decisión final

**El modelo se cierra con la Ronda 2** (XGBoost con máscaras estructurales, 100
árboles, `gamma=0,1`, `subsample=0,8`, umbral 0,15). No hay plan de evaluación en
test para ninguna palanca nueva: el test ya se consumió una vez con la Ronda 2 y
no hay nada que justifique volver a él.

Métricas de cierre (Ronda 2, test cohorte 2021, n = 13 355): **F1 «baja»
0,4234 · recall 0,7878 · precisión 0,2895 · F1 macro 0,5109 · Brier 0,4692**.

Cualquier mejora futura tendría que venir de **datos nuevos** (financiación de
proyectos, coautoría real, vinculación contractual), no de más features sobre el
mismo censo.

## Prueba posterior: modelo limpio (27-oct-2026)

Salida del EDA de diagnóstico se probó un modelo sin las 49 features redundantes
(VIF y duplicados), sin las 86 con > 99 % de ceros y con `n_productos`
winsorizada en el p99 de train (105). Solo folds, test intacto:

| Variante | Features | F1 «baja» OOS | Desv. | Brier |
|---|---|---|---|---|
| Base (Ronda 2) | 172 | **0,2985** | 0,0184 | **0,4196** |
| Solo VIF | 123 | 0,2877 | 0,0326 | 0,4223 |
| Limpio completo | 56 | 0,2834 | 0,0288 | 0,4223 |

La limpieza **no mejora**: baja el F1 (1,1-1,5 pp), sube la desviación entre
folds y empeora el Brier (+0,27 %). El modelo se mantiene con la Ronda 2; el
detalle y las hipótesis están en `documentacion/auditoria_base_datos.md` §7.

