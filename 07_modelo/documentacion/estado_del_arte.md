# Estado del arte: predicción de movilidad académica y su aplicación al modelo de categorías Minciencias

**Proyecto:** Consultoría estadística USTA 2026-II — Observatorio Minciencias
**Componente:** Fase 3 · modelo predictivo de movilidad de categoría
**Fecha de cierre de la búsqueda:** 26 de octubre de 2026
**Uso previsto:** guía fundamentada para la siguiente iteración del modelo

> **Regla de este documento.** No se inventan citas, páginas ni autores. Cada
> referencia se verificó el 26-10-2026 contra Crossref, OpenAlex, arXiv, Europe
> PMC o el propio documento; cuando solo se pudo confirmar título y DOI, se dice
> expresamente. Cuando una cifra circula sin fuente localizable, se advierte y no
> se le atribuye autoría.

## Nota metodológica de la búsqueda

- **Búsquedas realizadas:** Minciencias + movilidad + categorías; promoción
  académica + machine learning; regresión ordinal + boosting; desbalanceo +
  umbral + F1; validación temporal; panel + lags; redes de coautoría + predicción.
- **Bases y APIs:** OpenAlex, Crossref, arXiv, Europe PMC, PubMed, Zenodo.
- **Criterio de inclusión:** estudios con datos de Colombia o de sistemas
  nacionales de categorización, y estudios metodológicos con resultado
  cuantificado y replicable.
- **Criterio de exclusión:** repositorios sin metadatos verificables, blogs y
  documentos sin autoría identificable.

---

## §1 · Introducción

Este proyecto no parte de cero. Existe literatura reciente, y en parte producida
sobre **los mismos datos abiertos de Minciencias**, que aborda tres preguntas
directamente relevantes para nosotros: cómo se organiza el censo de
investigadores reconocidos, qué determina que una persona cambie de categoría y
cómo se evalúa un modelo que predice ese cambio.

La convergencia es notable: el estudio más cercano a nuestro problema
[Godoy et al., 2026] trabaja con **40 485 observaciones de seis convocatorias
entre 2013 y 2021** y las clasifica en los rangos **Junior, Asociado y Sénior**;
nuestro dataset tiene **43 187 transiciones contiguas de 18 116 personas en las
mismas seis convocatorias** [`model_card.md`, §2]. Dos construcciones
independientes del mismo universo llegan a un tamaño casi idéntico, lo que es una
validación externa de nuestra ingesta.

El estado del arte se usa aquí para tres cosas concretas:

1. **Confirmar o corregir decisiones ya tomadas** (máscaras estructurales,
   modelo ordinal, umbral distinto de 0,5, validación temporal).
2. **Priorizar la siguiente iteración** con evidencia, no con intuición: qué
   variables, qué métricas y qué arquitecturas tienen respaldo y cuáles no.
3. **Documentar los límites** que son del dato y no del método, para que la
   Memoria no los presente como fallas del modelado.

---

## §2 · Estudios sobre datos de Minciencias (el más importante)

### 2.1 El estudio

**Godoy, J. M., Abramo, G., D'Angelo, C. A. & Cortés, J. D. (2026).** *Should I
stay or should I go? The role of national geographic mobility, gender, age,
institutional research profiles, and labor market on the career performance of
the scientific workforce in Colombia.* **Scientometrics, 131(9), 5803-5824.**
DOI: [10.1007/s11192-026-05716-9](https://doi.org/10.1007/s11192-026-05716-9).

Versión previa: *Juglares — The Role of Geographic Mobility, Gender, Age,
Institutional Research Profiles, and Local Labor Market on the Career Performance
of the Scientific Workforce in Colombia* (preprint, Zenodo, 26-12-2025,
DOI [10.5281/zenodo.18062681](https://doi.org/10.5281/zenodo.18062681)).
También existe una ponencia en ISSI 2025, *National Mobility and Career
Performance of the Scientific Workforce in Colombia*, DOI
[10.51408/issi2025_145](https://doi.org/10.51408/issi2025_145).

**Datos.** Datos administrativos abiertos de Minciencias; **40 485
observaciones** persona–convocatoria en **seis convocatorias (2013-2021)**; rangos
ordenados Junior, Asociado, Sénior.

**Modelo.** Regresión logística ordinal con variable latente («research
recognition») y puntos de corte. Estiman primero el modelo con **supuesto de odds
proporcionales** y lo contrastan: el test de líneas paralelas lo rechaza
(p < 0,001). En consecuencia, estiman un modelo ordinal **no restringido** que
relaja el supuesto de odds proporcionales conservando el orden de las categorías;
la comparación por razón de verosimilitud entre la versión restringida y la no
restringida da **LR = 911, gl = 13, p < 0,001**, y AIC/BIC favorecen la no
restringida.

**Qué encuentra.** Cuatro resultados con implicación directa:

- **La movilidad geográfica no acelera la promoción.** Los coeficientes de
  movilidad son positivos pero solo significativos en el umbral Junior→Asociado,
  y la movilidad se asocia a **consolidar la posición inicial**: un Junior que se
  muda tiene mayor probabilidad de **seguir siendo Junior**, y un Asociado que se
  muda enfrenta mayor riesgo de **reclasificación hacia abajo**.
- **El contexto institucional pesa más que la movilidad.** El índice de
  **concentración de capital académico en la institución** (HHI de la
  distribución de rangos dentro de la institución) tiene coeficientes grandes y
  significativos, sobre todo en el umbral de Asociado: una mayor densidad de
  investigadores sénior en la institución aumenta la probabilidad de ocupar un
  rango superior.
- **El mercado laboral local importa, sobre todo al inicio.** La **tasa de
  desempleo de la ciudad** (rezagada) se asocia con cambios en las probabilidades
  de rango, y el efecto es más fuerte en Junior (mayor desempleo se asocia a mayor
  movilidad ascendente, compatible con un esfuerzo por consolidar el vínculo
  académico) que en los rangos altos.
- **El efecto de la categoría previa es no lineal** (términos lineal y
  cuadrático): el sistema genera inercia hacia los extremos y penaliza las
  mejoras incrementales que no superan umbrales críticos.

### 2.2 Qué valida de nuestro enfoque

| Nuestra decisión | Lo que muestra Godoy et al. | Lectura |
|---|---|---|
| **Máscaras estructurales** (Junior no puede bajar; Emérito excluido) | El umbral Junior→Asociado responde a un proceso distinto del Asociado→Sénior; la movilidad consolida a los Junior en su categoría | Modelar **transiciones heterogéneas por categoría** no es un capricho: es lo que muestran los datos |
| **Modelo ordinal** (bayesiano acumulativo, capa de incertidumbre) | Regresión ordinal con cortes; el supuesto de odds proporcionales **se rechaza** | El ordinal es la familia correcta; el supuesto fuerte hay que relajarlo o tratarlo con cautela |
| **No usar un único modelo de tres clases sin estructura** | La versión no restringida (efectos distintos por umbral) es la que gana | Refuerza el enfoque por categoría de origen sobre el multiclase plano |
| **Excluir a Emérito** | La escala analizada es Junior/Asociado/Sénior; Emérito no entra en la transición | Coincide con nuestro hallazgo de que Emérito no tiene transiciones en el dato |

**Matiz importante.** El estudio **no usa máscaras** ni un modelo bayesiano: usa
regresión ordinal no restringida. Lo que valida es el **diagnóstico** (las
transiciones no son homogéneas y el supuesto de odds proporcionales falla), no
literalmente nuestra arquitectura. Nuestra combinación —máscaras + ordinal
bayesiano como capa— sigue siendo una decisión de ingeniería propia.

### 2.3 Variables que usan y nosotros no tenemos

| Variable en Godoy et al. | Definición en el estudio | ¿Está en nuestro censo? |
|---|---|---|
| **Concentración de capital académico en la institución** | HHI de la distribución de rangos (share de investigadores sénior) en la institución del investigador | **No** como variable del modelo: tenemos `INST_FILIA` (filiación) y `n_grupos_distintos`, pero no la distribución de rangos por institución |
| **Tasa de desempleo local** | Tasa de desempleo de la ciudad, rezagada un período | **No**: el censo no trae variables de mercado laboral |
| **Movilidad geográfica** | Cambio de ciudad entre dos convocatorias consecutivas | **No** con esa definición: no tenemos ciudad de residencia por convocatoria en el dataset del modelo |
| **Área de conocimiento (OECD FOS)** | Seis grandes áreas, 219 disciplinas | **Sí**, pero **sin usar**: el censo fuente trae `NME_GRAN_AREA_PR` y el dataset del modelo no la incorpora |
| **Número de afiliaciones** | Proxy de densidad de red institucional | Parcial: `n_grupos_distintos` |
| **Edad** | Años desde la mayoría de edad | **Sí**: `EDAD_ANOS_PR` → `edad`; probada en el bloque demográfico (**−0,02 pp**) y descartada |

### 2.4 Implicación operativa para nosotros

El hallazgo más accionable no es la movilidad (que no tenemos) sino la
**concentración de capital académico institucional**, que el estudio señala como
el correlato más fuerte del resultado. Es construible con nuestros datos: el
censo tiene institución y categoría por persona y convocatoria, de modo que se
puede calcular, para cada investigador, **la proporción de investigadores de
categoría igual o superior en su institución** y su variación respecto de la
convocatoria anterior. Requiere un procesamiento nuevo, pero no datos nuevos.

Ojo con la interpretación: los autores advierten que el resultado es **correlacional**
y que el proceso mismo de clasificación de Minciencias podría reforzar jerarquías
institucionales preexistentes. Esa advertencia nos obliga a no venderlo como
«efecto causal» en la Memoria.

---

## §3 · Predicción de promoción académica con machine learning

### 3.1 Qué hay

**Yeo, M. M., Lim, S. H., Kumar, A. & Thompson, A. W. (2024).** *Calculator for
predicting the probability of faculty promotion in an academic medical centre.*
**BMJ Leader, 8(3), 203-207.** DOI:
[10.1136/leader-2023-000861](https://doi.org/10.1136/leader-2023-000861).

Centro médico académico con más de 2 200 profesores y ~300 nombramientos y
promociones al año. Variables: publicaciones, índice H, contribuciones
educativas y liderazgo/servicio dentro y fuera de la institución. Comparan cinco
métodos y seleccionan **Random Forest** mediante validación cruzada
leave-one-out. El resultado se despliega como **calculadora** para aspirantes y
comités. Es un caso de **clasificación binaria** (promoción aprobada o no).

**Gayatri, N. A. G., Prabowo, H., Heryadi, Y. & Kuncoro, E. A. (2025).**
*Predicting Academic Rank Improvement of Higher Education Lecturers Using Machine
Learning Model.* **ICoICT 2025.** DOI:
[10.1109/icoict66265.2025.11193099](https://doi.org/10.1109/icoict66265.2025.11193099).

**1 229 docentes**; variables de desempeño (evaluaciones docentes, productividad
investigativa, contribuciones profesionales); comparan **Random Forest, SVM,
regresión logística y k-vecinos**; aplican **SMOTE** por desbalance; Random
Forest + SMOTE obtiene F1 **0,989** y exactitud 98,9 %; análisis SHAP identifica
índice H, publicaciones, evaluaciones, citas y años de experiencia como las
variables más importantes. También es **binario** (mejora de rango sí/no).

**Jafor, M. A., Wadud, M. A. H., Nur, K. & Rahman, M. M. (2023).** *Employee
Promotion Prediction Using Improved AdaBoost Machine Learning Approach.* **AIUB
Journal of Science and Engineering, 22(3), 258-266.** DOI:
[10.53799/ajse.v22i3.781](https://doi.org/10.53799/ajse.v22i3.781).

AdaBoost mejorado aplicado a **promoción de empleados** (dominio de recursos
humanos, no académico). Se cita como evidencia de que los *boosting* se usan en
predicción de promoción, pero **no se puede extrapolar** a categorización
científica sin advertirlo.

### 3.2 Lo que no se encontró

**No se localizó un estudio que use XGBoost específicamente para predecir
promoción académica o categorización de investigadores.** Los trabajos
localizados usan Random Forest (BMJ Leader 2024), Random Forest/SVM/regresión
logística/k-NN (ICoICT 2025) y AdaBoost en promoción de empleados (AJSE 2023).
Esto no invalida nuestra elección —XGBoost es un *gradient boosting* con
regularización, y los *boosting* son los métodos que mejor rinden en datos
tabulares [Grinsztajn et al., 2022; Shwartz-Ziv & Armon, 2022]— pero conviene
**no atribuir a la literatura una comparación que no existe**.

### 3.3 La limitación común: todos son binarios

Los tres estudios predicen **promoción sí/no**. Nuestro problema es **ordinal de
tres resultados** (baja, se mantiene, sube), lo que es más fino y más difícil:

- Un binario «promoción» **no distingue** entre mantenerse y bajar; nuestro
  objetivo sí, y la clase de interés (baja) es la minoritaria.
- Un binario permite métricas limpias (AUC, F1 binario); un ordinal obliga a
  decidir cómo se penaliza el error entre categorías no adyacentes (§4).
- Los F1 de 0,99 reportados en ICoICT 2025 deben leerse con cautela: SMOTE sobre
  un conjunto pequeño y partición no temporal suele inflar el desempeño; nuestro
  F1 «baja» de 0,4234 en test temporal no es comparable con esa cifra.

---

## §4 · Modelos ordinales frente a multiclase

### 4.1 Cumulative Link Models (CLM)

El modelo de enlaces acumulativos es la extensión natural de la regresión
logística a categorías ordenadas [McCullagh, 1980]: se modela

```
logit[P(Y ≤ j | x)] = θ_j − x'β ,   j = 1, …, J−1
```

con un intercepto (corte) por categoría y **pendientes β comunes**. Es la
especificación que Godoy et al. prueban primero y **rechazan** para su caso: el
supuesto de odds proporcionales no se sostiene.

**Alternativas cuando el supuesto falla:**

| Especificación | Qué relaja | Costo |
|---|---|---|
| Odds proporcionales (CLM estándar) | Nada; β común a todos los cortes | Menos parámetros, más sesgo si el supuesto falla |
| **Odds proporcionales parciales / no restringido** | Permite β distintos por corte (o por subconjunto de covariables) | Más parámetros; es lo que usa Godoy et al. |
| Probit ordenado / log-log complementario | Cambia la función de enlace, no el supuesto de β común | Cambio de interpretación |
| **Ordinal bayesiano jerárquico** (nuestro caso) | β y cortes con distribuciones previas; permite heterogeneidad por grupo sin colapsar | Costo computacional; requiere diagnóstico de convergencia |

Nuestro modelo bayesiano mínimo usa un **ordinal acumulativo con 12 predictores**
y efectos por categoría, con 2×1 000 + 1 000 iteraciones; reporta AUC «baja»
**0,82** y Brier **0,4370**, mejor calibrado que el XGBoost, pero con peor
clasificación automática (F1 «baja» 0,003 sin umbral; 0,286 con umbral ajustado).
Eso es exactamente el patrón que la literatura predice para modelos ordinales
paramétricos: **buena calibración, poca discriminación** cuando la relación no es
monótona.

### 4.2 Weighted Kappa: la métrica que falta

El kappa ponderado [Cohen, 1968] generaliza el acuerdo entre dos jueces
ordinales penalizando el desacuerdo según la distancia entre categorías:

```
κ_w = 1 − (Σ w_ij · O_ij) / (Σ w_ij · E_ij)
```

con `w_ij` pesos lineales (`|i−j|/(K−1)`) o cuadráticos (`(i−j)²/(K−1)²`). En un
problema de tres clases ordenadas, confundir «baja» con «se mantiene» es un error
menos grave que confundir «baja» con «sube»; **el F1 macro y la exactitud tratan
ambos errores igual**, el kappa ponderado no.

**Aplicación a nuestro caso:** el kappa ponderado se calcula con la misma matriz
de confusión del test, sin reentrenar. Es la métrica que permitiría reportar
honestamente si el modelo, además de detectar descensos, **ordena bien** las tres
categorías. No se ha calculado aún; es una de las palancas de bajo costo (§
«Implicación para la siguiente iteración»).

### 4.3 Boosting con pérdida ordinal (OGBoost / «O-LGBM»)

La idea de un *gradient boosting* con pérdida específicamente ordinal existe y
está implementada en abierto:

**Sharabiani, M. T. A., Bottle, A. & Mahani, A. S. (2026).** *OGBoost: A Python
Package for Ordinal Regression Gradient Boosting.* **Journal of Statistical
Software, 117(5).** DOI:
[10.18637/jss.v117.i05](https://doi.org/10.18637/jss.v117.i05). Preprint:
arXiv:[2502.13456](https://arxiv.org/abs/2502.13456).

OGBoost es compatible con scikit-learn y optimiza **conjuntamente** una función
latente continua (por descenso de gradiente funcional) y un **vector de umbrales**
que convierte el valor latente en probabilidades de clase (por descenso de
gradiente clásico). Es la versión práctica de la familia que en la literatura
aparece como «ordinal gradient boosting» o «O-LGBM».

**Nota técnica honesta:** LightGBM y XGBoost **no traen una pérdida ordinal
nativa**; se implementa con objetivos personalizados o con paquetes externos como
OGBoost. Decir «O-LGBM» como si fuera una opción de configuración de LightGBM no
es exacto.

### 4.4 Decisión para nuestro caso

| Opción | Ventaja | Desventaja | Decisión |
|---|---|---|---|
| **XGBoost multiclase con máscaras** (actual) | Mejor F1 «baja» (0,4234 en test); respeta la estructura (Junior no baja, Emérito fuera) | Probabilidades mal calibradas (Brier 0,4692); no usa el orden entre clases | **Se mantiene como modelo operativo** |
| **Bayesiano ordinal** (actual) | Calibración (Brier 0,4370) e incertidumbre; coherente con la estructura ordinal | Discriminación baja; no operativo | **Se mantiene como capa de incertidumbre** |
| **OGBoost / ordinal boosting** | Usa el orden en la pérdida; podría mejorar la calibración sin perder discriminación | No probado con nuestras máscaras; requiere validación completa | **Candidato para probar** (§9) |
| **CLM no restringido** | Es lo que usa Godoy et al. y funciona en este dominio | Muchos parámetros con 172 features; riesgo de sobreajuste | Descartado como modelo principal; útil como contraste |

---

## §5 · Manejo del desbalanceo y optimización del umbral

### 5.1 El umbral 0,5 no es sagrado

El resultado teórico relevante es de **Lipton, Z. C., Elkan, C. &
Narayanaswamy, B. (2014).** *Thresholding Classifiers to Maximize F1 Score.*
arXiv:[1402.1892](https://arxiv.org/abs/1402.1892). Derivan la relación entre el
mejor F1 alcanzable y el umbral que lo logra y demuestran que, **si las
probabilidades están bien calibradas, el umbral óptimo para F1 es la mitad del F1
óptimo**, no 0,5. Es decir: con clases desbalanceadas y F1 como métrica, el umbral
0,5 es sistemáticamente demasiado alto.

Esto respalda nuestra elección de **0,15** (fijado en validación, no en test), y
además da una comprobación de orden de magnitud: nuestro F1 «baja» es 0,4234, y
la mitad es ≈ 0,21; el umbral elegido (0,15) está en ese orden, no en 0,5.

**Sobre las cifras 52,78 % → 91,67 %.** Circulan en notas internas como ejemplo
de que «bajar el umbral de 0,5 a 0,1 sube el recall». **No se localizó una fuente
verificable para ese par de valores**; por eso no se citan como si tuvieran autor.
La afirmación cualitativa —bajar el umbral sube recall y baja precisión— sí tiene
respaldo (Lipton et al. 2014; práctica estándar de *threshold moving*).

### 5.2 PR-AUC frente a ROC-AUC

Con desbalanceo fuerte, la curva precisión-recall es más informativa que la ROC:
**Saito, T. & Rehmsmeier, M. (2015).** *The Precision-Recall Plot Is More
Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced
Datasets.* **PLOS ONE, 10(3), e0118432.** DOI:
[10.1371/journal.pone.0118432](https://doi.org/10.1371/journal.pone.0118432); y
la base formal en **Davis, J. & Goadrich, M. (2006).** *The relationship between
Precision-Recall and ROC curves.* **ICML '06.** DOI:
[10.1145/1143844.1143874](https://doi.org/10.1145/1143844.1143874).

**Contrapunto que conviene citar:** **Richardson, E., Trevizani, R., Greenbaum,
J. A., Carter, H., Nielsen, M. & Peters, B. (2024).** *The receiver operating
characteristic curve accurately assesses imbalanced datasets.* **Patterns,
5(6), 100994.** DOI:
[10.1016/j.patter.2024.100994](https://doi.org/10.1016/j.patter.2024.100994).
Argumentan que la ROC-AUC no es intrínsecamente engañosa con desbalanceo y que su
supuesta inferioridad se debe a comparaciones mal planteadas. La lectura
equilibrada: **ROC-AUC puede reportarse, pero no debe ser la métrica de decisión
cuando la clase minoritaria es la de interés**.

**Nuestro caso concreto.** Prevalencia de «baja» en test: 10,2 %. Reportamos AUC
«baja» 0,8631, pero ese valor está **inflado por la máscara de Junior** (al no
poder bajar, se separan trivialmente); la AUC dentro de categoría es 0,672
(Asociado) y 0,634 (Sénior). Es un ejemplo de libro de por qué la AUC global no
debe usarse como argumento de venta del modelo.

### 5.3 SMOTE: mejor no

**van den Goorbergh, R., van Smeden, M., Timmerman, D. & Van Calster, B. (2022).**
*The harm of class imbalance corrections for risk prediction models: illustration
and simulation using logistic regression, random forest, and RUSBoost.*
**JAMIA, 29(9), 1525-1534.** DOI:
[10.1093/jamia/ocac093](https://doi.org/10.1093/jamia/ocac093).

Muestra que las correcciones de desbalanceo (SMOTE, *undersampling*) **no mejoran
la discriminación** y **degradan la calibración** de las probabilidades. Nuestra
decisión —pesos de clase balanceados en el entrenamiento + umbral ajustado en
validación, sin remuestreo sintético— está alineada con esa evidencia. Además, el
test real mantiene la prevalencia natural, que es lo que un sistema de alertas
necesita.

### 5.4 Resumen numérico de nuestro enfoque

| Elemento | Valor | Fuente |
|---|---|---|
| Prevalencia de «baja» (test) | 10,2 % | [`model_card.md`, §5] |
| Umbral operativo | 0,15 (mediana de los umbrales de los folds) | [`model_card.md`, §3] |
| Alertas emitidas | 25,7 % de las filas | [`model_card.md`, §4] |
| F1 «baja» / recall / precisión | 0,4234 / 0,7878 / 0,2895 | [`expE_test`, `model_card.md`] |
| Brier multiclase | 0,4692 (constante: 0,4419) | [`model_card.md`, §4] |

---

## §6 · Validación temporal

### 6.1 La regla

Para datos con estructura temporal, **la partición aleatoria no es válida**:
mezcla pasado y futuro y produce estimaciones optimistas. La práctica
recomendada es **origen móvil** (*rolling origin*): entrenar con todo lo
disponible hasta T y evaluar en el período siguiente, desplazando T.

Referencias verificadas:

- **Tashman, L. J. (2000).** *Out-of-sample tests of forecasting accuracy: an
  analysis and review.* **International Journal of Forecasting, 16(4),
  437-456.** DOI:
  [10.1016/S0169-2070(00)00065-0](https://doi.org/10.1016/S0169-2070(00)00065-0).
- **Bergmeir, C. & Benítez, J. M. (2010).** *A survey of cross-validation
  procedures for model selection.* **Statistics Surveys, 4, 40-79.** DOI:
  [10.1214/09-SS054](https://doi.org/10.1214/09-SS054).
- **Hyndman, R. J. & Athanasopoulos, G.** *Forecasting: Principles and Practice*
  (3.ª ed.), secciones «Time series cross-validation» y «Lagged predictors»,
  [otexts.com/fpp3](https://otexts.com/fpp3/).

### 6.2 Nuestro esquema

| Elemento | Nuestro diseño |
|---|---|
| Folds | 3 temporales: entrenar con cohortes anteriores y validar en la siguiente |
| Test | Cohorte 2021 (13 355 filas), **evaluada una sola vez** |
| Umbral | Fijado con la mediana de los folds, **nunca en test** |
| Selección de modelo | Solo con validación temporal (4 rondas) |

Esto coincide con la práctica recomendada. La debilidad no es el esquema sino el
**tamaño de la historia**: cinco cohortes útiles (2014, 2015, 2017, 2019, 2021) no
permiten separar tendencia de ruido, y por eso el test de 2021 cambia de régimen
(prevalencia 5,2 % → 10,2 %).

---

## §7 · Estructura de datos de panel: lags y momentum

### 7.1 Lo que dice la literatura

Con datos de panel (persona × convocatoria), las covariables deben entrar
**rezagadas**: la producción de t−1 y t−2 explica el cambio observado en t. La
inclusión de rezagos y de transformaciones de cambio es práctica estándar en
predicción con series temporales y paneles [Hyndman & Athanasopoulos, *op. cit.*,
«Lagged predictors»]. El propio Godoy et al. construyen sus variables
individuales e institucionales con el sufijo `_l1` (valor en la convocatoria
inmediatamente anterior) como estrategia de rezago para mitigar endogeneidad.

### 7.2 Lo que hicimos y lo que falta

| Elemento | Estado en nuestro modelo |
|---|---|
| Variables de producción en t−1 | **Sí** (las 172 features se construyen con la producción acumulada/ventana previa) |
| Cambio de producción (momentum) | **Sí**: `momentum_produccion`, evaluado en la Ronda 3 con **+0,78 pp** de F1 «baja» fuera de muestra; por debajo del umbral de adopción (+2 pp) |
| **Lags de dos períodos** (t−2) | **No** probados |
| Tiempo en categoría e historial | **Sí**: `tiempo_en_categoria`, `historial_bajas`, `historial_subidas`, `gap` |

**Implicación:** hay margen real para probar `t−2` y diferencias de segundo orden.
Dos advertencias: (i) con cohortes de 2 a 5 años, un lag de dos períodos puede
**reducir mucho la muestra**; (ii) los lags están correlacionados entre sí, y el
modelo puede repartir la importancia de forma inestable entre ellos.

---

## §8 · Red de coautorías

### 8.1 La evidencia

**Dies, S., Liu, D. & Eliassi-Rad, T. (2025).** *Forecasting Faculty Placement
from Patterns in Co-authorship Networks.* arXiv:[2507.14696](https://arxiv.org/abs/2507.14696).

Formulan la colocación institucional de doctores como un problema de predicción
individual con redes temporales de coautoría. Resultado central, con la
formulación exacta del artículo: la red **mejora la precisión predictiva «hasta
un 10 %» sobre los indicadores tradicionales solos**, y **«un 8,48 % (p = 0,005)
sobre el rango de la institución doctoral sola»**; las ganancias mayores se
observan en los casos de menor información previa. También reportan que la
estructura de red aporta información **complementaria** a la productividad.

### 8.2 Nuestra limitación, con nombre y apellido

El archivo de producción que usamos tiene **1,02 autores por producto en promedio
(máximo 6)** y no incluye la lista de coautores; en todo el censo hay solo
**72 226 pares de coautoría**, lo que hace degenerada la red
[`validacion_honesta.md`, Ronda 4]. Probamos una aproximación por **compañeros de
grupo** (6 features de red) y el efecto fue **0,00 pp**.

**Esto es limitación del dato, no del método**, y la literatura lo respalda: la
ganancia de 8,48 % se obtiene con redes de coautoría reales, que nuestro archivo
no contiene. La consecuencia práctica es que **no se puede prometer esa mejora**
sin acceso al detalle de autores por producto (que sí existe en CvLAC/GrupLAC,
pero no en el CSV entregado).

---

## §9 · Brechas y oportunidades para nuestro modelo

### 9.1 Lo que la literatura sugiere probar

| # | Palanca | Respaldo | Costo | Riesgo |
|---|---|---|---|---|
| 1 | **Weighted Kappa** como métrica de evaluación | Cohen (1968); uso estándar en predicción ordinal | Muy bajo (se calcula con la matriz de confusión) | Ninguno; agrega información |
| 2 | **Variables de contexto institucional** (densidad de sénior en la institución, HHI de rangos) | Godoy et al. (2026): el correlato más fuerte del estudio | Medio (requiere reconstruir la distribución por institución) | Correlación con la categoría propia; riesgo de fuga si se calcula con el mismo período |
| 3 | **Lags de dos períodos** y diferencias de segundo orden | Práctica estándar en paneles y series (FPP3; Godoy et al. usan `_l1`) | Bajo-medio | Pérdida de muestra; inestabilidad entre lags correlacionados |
| 4 | **Ordinal boosting (OGBoost)** | Sharabiani et al. (2026); el orden de las clases entra en la pérdida | Medio | No probado con máscaras; puede empeorar la discriminación |

### 9.2 Lo que la literatura NO sugiere

| Tentación | Por qué no | Respaldo |
|---|---|---|
| **Deep learning tabular** | Los modelos basados en árboles siguen siendo *state of the art* en datos tabulares de tamaño medio (~10 000 filas), incluso sin contar su velocidad | Grinsztajn, Oyallon & Varoquaux (2022), arXiv:2207.08815; Shwartz-Ziv & Armon (2022), DOI [10.1016/j.inffus.2021.11.011](https://doi.org/10.1016/j.inffus.2021.11.011) |
| **SMOTE / remuestreo sintético** | No mejora la discriminación y daña la calibración; los pesos de clase + umbral son preferibles | van den Goorbergh et al. (2022), DOI [10.1093/jamia/ocac093](https://doi.org/10.1093/jamia/ocac093) |
| **Modelo de dos etapas** (clasificar «baja» y luego «sube») | No se localizó respaldo específico; nuestros datos no muestran que el problema sea de dos decisiones independientes | Búsqueda sin resultado; se reporta como ausencia de evidencia |
| **Corrección de *prior shift*** | Nuestro ensayo empeoró el Brier (0,4917 y 0,4851 frente a 0,4692) | [`model_card.md`, §4] |

---

## §10 · Referencias con DOI/URL

**Sobre datos de Minciencias**

1. Godoy, J. M., Abramo, G., D'Angelo, C. A. & Cortés, J. D. (2026). *Should I
   stay or should I go? The role of national geographic mobility, gender, age,
   institutional research profiles, and labor market on the career performance of
   the scientific workforce in Colombia.* Scientometrics, 131(9), 5803-5824.
   https://doi.org/10.1007/s11192-026-05716-9
2. Godoy, J. M., Abramo, G., D'Angelo, C. A. & Cortés, J. D. (2025). *Juglares —
   The Role of Geographic Mobility, Gender, Age, Institutional Research Profiles,
   and Local Labor Market on the Career Performance of the Scientific Workforce in
   Colombia* [preprint]. Zenodo. https://doi.org/10.5281/zenodo.18062681
3. Godoy, J. M., Abramo, G., D'Angelo, C. A. & Cortés, J. D. (2025). *National
   Mobility and Career Performance of the Scientific Workforce in Colombia*
   [ponencia ISSI 2025]. https://doi.org/10.51408/issi2025_145

**Predicción de promoción académica**

4. Yeo, M. M., Lim, S. H., Kumar, A. & Thompson, A. W. (2024). *Calculator for
   predicting the probability of faculty promotion in an academic medical centre.*
   BMJ Leader, 8(3), 203-207. https://doi.org/10.1136/leader-2023-000861
5. Gayatri, N. A. G., Prabowo, H., Heryadi, Y. & Kuncoro, E. A. (2025).
   *Predicting Academic Rank Improvement of Higher Education Lecturers Using
   Machine Learning Model.* ICoICT 2025.
   https://doi.org/10.1109/icoict66265.2025.11193099
6. Jafor, M. A., Wadud, M. A. H., Nur, K. & Rahman, M. M. (2023). *Employee
   Promotion Prediction Using Improved AdaBoost Machine Learning Approach.* AIUB
   Journal of Science and Engineering, 22(3), 258-266.
   https://doi.org/10.53799/ajse.v22i3.781

**Modelos ordinales y métricas**

7. McCullagh, P. (1980). *Regression Models for Ordinal Data.* Journal of the
   Royal Statistical Society, Series B, 42(2), 109-142.
   https://doi.org/10.1111/j.2517-6161.1980.tb01109.x
8. Cohen, J. (1968). *Weighted kappa: nominal scale agreement provision for
   scaled disagreement or partial credit.* Psychological Bulletin, 70(4),
   213-220. https://doi.org/10.1037/h0026256
9. Sharabiani, M. T. A., Bottle, A. & Mahani, A. S. (2026). *OGBoost: A Python
   Package for Ordinal Regression Gradient Boosting.* Journal of Statistical
   Software, 117(5). https://doi.org/10.18637/jss.v117.i05 · preprint
   https://arxiv.org/abs/2502.13456

**Umbral, desbalanceo y métricas de clasificación**

10. Lipton, Z. C., Elkan, C. & Narayanaswamy, B. (2014). *Thresholding
    Classifiers to Maximize F1 Score.* https://arxiv.org/abs/1402.1892
11. Saito, T. & Rehmsmeier, M. (2015). *The Precision-Recall Plot Is More
    Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced
    Datasets.* PLOS ONE, 10(3), e0118432.
    https://doi.org/10.1371/journal.pone.0118432
12. Davis, J. & Goadrich, M. (2006). *The relationship between Precision-Recall
    and ROC curves.* ICML '06. https://doi.org/10.1145/1143844.1143874
13. Richardson, E., Trevizani, R., Greenbaum, J. A., Carter, H., Nielsen, M. &
    Peters, B. (2024). *The receiver operating characteristic curve accurately
    assesses imbalanced datasets.* Patterns, 5(6), 100994.
    https://doi.org/10.1016/j.patter.2024.100994
14. van den Goorbergh, R., van Smeden, M., Timmerman, D. & Van Calster, B.
    (2022). *The harm of class imbalance corrections for risk prediction models.*
    JAMIA, 29(9), 1525-1534. https://doi.org/10.1093/jamia/ocac093

**Validación temporal y paneles**

15. Tashman, L. J. (2000). *Out-of-sample tests of forecasting accuracy: an
    analysis and review.* International Journal of Forecasting, 16(4), 437-456.
    https://doi.org/10.1016/S0169-2070(00)00065-0
16. Bergmeir, C. & Benítez, J. M. (2010). *A survey of cross-validation
    procedures for model selection.* Statistics Surveys, 4, 40-79.
    https://doi.org/10.1214/09-SS054
17. Hyndman, R. J. & Athanasopoulos, G. *Forecasting: Principles and
    Practice* (3.ª ed.). https://otexts.com/fpp3/

**Redes y aprendizaje automático tabular**

18. Dies, S., Liu, D. & Eliassi-Rad, T. (2025). *Forecasting Faculty Placement
    from Patterns in Co-authorship Networks.*
    https://arxiv.org/abs/2507.14696
19. Grinsztajn, L., Oyallon, E. & Varoquaux, G. (2022). *Why do tree-based
    models still outperform deep learning on typical tabular data?* NeurIPS 2022.
    https://arxiv.org/abs/2207.08815
20. Shwartz-Ziv, R. & Armon, A. (2022). *Tabular data: Deep learning is not all
    you need.* Information Fusion, 81, 84-90.
    https://doi.org/10.1016/j.inffus.2021.11.011

**Referencias internas del proyecto**

21. `07_modelo/modelado/model_card.md`
22. `07_modelo/modelado/validacion_honesta.md`
23. `07_modelo/modelado/resultados/expE_test_20261026_024016.json`
24. `07_modelo/documentacion/criterios_minciencias.md`

**Nota de verificación.** Las referencias 1-20 se contrastaron contra Crossref,
OpenAlex, arXiv o Europe PMC el 26-10-2026 (título, autores, revista, volumen,
páginas y DOI). No se pudo acceder al texto completo de la versión publicada en
Scientometrics (muro de pago); los detalles metodológicos de §2 provienen del
**preprint de acceso abierto** (Research Square/Zenodo), que declara los mismos
datos y modelo. La referencia 3 se verificó por título y DOI en Crossref.

---

## Implicación para la siguiente iteración del modelo

La literatura permite priorizar con criterio. El orden propuesto combina tres
factores: **respaldo en la evidencia**, **costo de implementación** y **riesgo de
romper lo ya validado**. La regla de decisión se mantiene: una palanca se adopta
solo si mejora el F1 «baja» fuera de muestra en **≥ 2 pp** sin degradar el Brier
de forma sustancial.

### Palanca 1 · Nivel de formación (prioridad máxima, aunque no venga de la literatura)

No es una palanca «de estado del arte», es **de los criterios de Minciencias** y ya
está documentada en [`criterios_minciencias.md`]: el censo fuente trae
`NME_NIV_FORM_PR` (nivel de formación), es criterio explícito de las cuatro
categorías y **nunca entró al modelo**.

- **Por qué primero:** es la única variable disponible que ataca directamente un
  requisito oficial y no ha sido probada. Costo casi nulo.
- **Cómo probarla:** añadir `tiene_doctorado` (y dummies por nivel) al bloque de
  features y correr la misma validación temporal de 3 folds; comparar contra la
  referencia 0,3054 de F1 «baja» OOS.
- **Riesgo:** puede ser casi constante en la población reconocida (la mayoría de
  Sénior y Asociado tiene doctorado), en cuyo caso el efecto será nulo. Se sabrá
  en una corrida.

### Palanca 2 · Variables de contexto institucional (la de mayor respaldo externo)

Godoy et al. (2026) encuentran que la **concentración de capital académico en la
institución** es el correlato más fuerte del resultado, por encima de la movilidad
y del mercado laboral. Es construible con nuestros datos.

- **Features candidatas:** proporción de investigadores de categoría ≥ la propia
  en la institución; HHI de rangos por institución y convocatoria; variación de
  esa concentración respecto de la convocatoria anterior.
- **Cómo probarla:** join por (institución, convocatoria); validar con los mismos
  3 folds; vigilar fuga de información (el HHI debe calcularse **solo con la
  convocatoria anterior**, como hacen ellos con `_l1`).
- **Riesgo:** alta correlación con la categoría propia y con el tamaño
  institucional; puede inflar el ajuste en entrenamiento y no generalizar.

### Palanca 3 · Weighted Kappa como métrica de evaluación

No cambia el modelo; cambia lo que reportamos.

- **Qué hace:** penaliza los errores según la distancia ordinal (baja↔sube pesa
  más que baja↔mantiene), algo que F1 macro y exactitud no distinguen.
- **Costo:** se calcula con la matriz de confusión del test que ya se genera; no
  requiere reentrenar.
- **Uso:** reportarla junto con F1 «baja» y Brier, y **no** como métrica de
  selección (para no optimizar sobre el test).
- **Riesgo:** ninguno técnico; el único riesgo es de comunicación: un kappa
  ponderado bajo (esperable, ~0,3-0,4 con nuestro nivel de acierto) puede leerse
  como «mal modelo» si no se explica que el problema es difícil por diseño.

### Palanca 4 · Lags de dos períodos

Práctica estándar en paneles; nosotros solo probamos el cambio de un período
(momentum, +0,78 pp).

- **Features candidatas:** producción en t−2, diferencia (t−1) − (t−2), y ratio
  de crecimiento de dos períodos.
- **Cómo probarla:** solo si la muestra lo permite; reportar el tamaño efectivo
  antes y después del lag, porque con cinco cohortes se pierden filas.
- **Riesgo:** colinealidad con `momentum_produccion` y con las features de
  producción acumulada; el modelo puede repartir importancia de forma inestable
  entre folds.

### Lo que no se hará (y por qué)

- **Deep learning tabular:** Grinsztajn et al. (2022) y Shwartz-Ziv & Armon (2022)
  muestran que los árboles siguen siendo competitivos en tablas de ~10 000 filas.
  Cambiar de familia no está justificado por la evidencia.
- **SMOTE:** van den Goorbergh et al. (2022) documentan el daño a la calibración.
  Nuestro enfoque (pesos de clase + umbral validado) es el recomendado.
- **Modelo de dos etapas:** no se localizó respaldo específico y nuestros datos no
  muestran independencia entre las decisiones.
- **Corrección de *prior shift*:** ya se probó y empeoró el Brier (0,4917/0,4851
  frente a 0,4692).

### Orden de ejecución propuesto

| Turno | Acción | Criterio de éxito |
|---|---|---|
| 1 | Palanca 1 (`tiene_doctorado` + dummies de nivel) | ≥ +2 pp de F1 «baja» OOS |
| 2 | Palanca 3 (weighted kappa en el reporte del test) | Se incorpora al `model_card` sin cambiar el modelo |
| 3 | Palanca 2 (contexto institucional) | ≥ +2 pp sin degradar Brier |
| 4 | Palanca 4 (lags t−2) | ≥ +2 pp con muestra suficiente |

Si las cuatro palancas fallan el criterio, la conclusión no cambia: **el techo es
del dato**, y el estado del arte lo respalda, porque las variables que sí mueven
la aguja en la literatura (financiación, coautoría real, mercado laboral,
movilidad) no están en el censo que tenemos.

---

## Actualización 27-10-2026: las cuatro palancas ya se ejecutaron

El plan de esta sección se cerró. Resultados, todos **solo con folds** y con el
mismo criterio de +2 pp (media OOS ≥ 0,3185 sobre 0,2985):

| Palanca | Resultado | Veredicto |
|---|---|---|
| 1. Nivel de formación (`NME_NIV_FORM_PR`) | 0,2987 (+0,02 pp con one-hot; −0,71 pp con ordinal) | Descartada: casi constante en la población reconocida |
| 2. Contexto institucional (HHI + movilidad) | 0,3032 (+0,47 pp) | No alcanza |
| 3. Weighted kappa | No ejecutada como palanca de modelo; sigue pendiente como **métrica de reporte** | — |
| 4. Lags de dos períodos | 0,3049 (+0,64 pp; t−2 no lo usa el modelo) | No alcanza |

Además se probaron TabICLv2 (−17,16 pp) y Laya zero-shot (ρ = 0,075, p = 0,458),
documentados en `laya_y_open_weights.md`. **El modelo se cerró con la Ronda 2**;
el detalle está en `07_modelo/modelado/validacion_honesta.md` § «Cierre
definitivo».

