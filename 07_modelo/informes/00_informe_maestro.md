# Informe maestro · Predicción de movilidad de categoría en el SNCTI

**Proyecto:** Consultoría estadística USTA 2026-II — Observatorio Minciencias
**Componente:** Fase 3 · modelo predictivo de movilidad de categoría
**Documento:** informe maestro consolidado (defensa académica y entrega al docente)
**Fecha:** 27 de octubre de 2026
**Versión:** 1.0
**Autor:** Consultoría estadística USTA 2026-II

> **Regla editorial.** Todas las cifras de este informe provienen de artefactos
> verificables del repositorio (manifiestos, JSON de resultados, *model card* y
> los cinco informes modulares). Cuando una cifra tiene una salvedad de
> procedencia, se declara en el texto o en nota al pie. No se reportan cifras
> estimadas como si fueran medidas, ni se atribuyen a la literatura resultados que
> no se verificaron.

---

## 1. Portada y resumen ejecutivo

### 1.1 Ficha del documento

| Elemento | Contenido |
|---|---|
| Pregunta de consultoría | ¿Se puede anticipar, con datos abiertos del censo de Minciencias, qué investigadores descenderán de categoría en la siguiente convocatoria? |
| Universo | 43 187 transiciones contiguas de 18 116 investigadores, seis convocatorias (2013–2021) |
| Fuentes | Socrata `bqtm-4y2h` (padrón, 77 237 registros) y `33dq-ab5a` (producción, 3 166 629 filas) |
| Modelo de cierre | XGBoost con máscaras estructurales, 172 features, umbral 0,15 |
| Métrica principal | F1 de la clase «baja» en la cohorte 2021 (test), evaluada una vez |
| Resultado | **F1 0,4234 · recall 0,7878 · precisión 0,2895 · F1 macro 0,5109** |
| Conclusión | **Techo del dato**: nueve palancas probadas, ninguna supera +2 pp; el modelo sirve para priorizar revisión humana, no para automatizar decisiones |
| Documentos de detalle | [Informe 01](01_ingesta_y_datos.md) · [Informe 02](02_eda_y_auditoria.md) · [Informe 03](03_modelado_xgboost.md) · [Informe 04](04_modelo_bayesiano.md) · [Informe 05](05_pruebas_alternativas.md) |

### 1.2 Resumen ejecutivo

Minciencias reevalúa la categoría de cada investigador en **cada convocatoria**.
No existe ascenso automático ni permanencia distinta de la de Emérito: la
categoría se verifica de nuevo contra requisitos que dependen de una **ventana
móvil** de producción (diez años para Sénior, diez y cinco para Asociado). Un
investigador puede descender sin haber dejado de producir, simplemente porque un
producto salió de la ventana o porque la evidencia de formación de recurso humano
ya no cubre el periodo exigido. Esa mecánica —descrita en los documentos oficiales
del modelo de medición (Minciencias, 2021a, 2024)— convierte el descenso en un
evento **estructuralmente previsible en parte y estructuralmente incierto en
parte**: se puede anticipar el efecto de la ventana, pero no la pérdida de
elegibilidad por causas que el censo no publica.

La consultoría construyó, desde las fuentes abiertas, una base reproducible
—**1,35 GB** de producción descargados con hash y manifiesto, **3 166 629** filas
producto-autor, **77 237** registros del padrón— y derivó **43 187 transiciones**
contiguas de **18 116 personas**. Sobre esa base se entrenó un clasificador de tres
resultados (`baja`, `se mantiene`, `sube`) con **XGBoost y máscaras
estructurales**: Junior no puede bajar (se modela binario), Emérito se excluye (no
tiene transiciones) y Asociado y Sénior se modelan con tres clases. La validación
es **temporal por cohorte de destino** (entrenar con 2014–2017, validar con 2019,
evaluar con 2021), el umbral de decisión se fijó solo con validación (**0,15**) y
el test (2021) se reservó para la evaluación final, sin usarse para entrenar,
estandarizar ni fijar el umbral.

El resultado de cierre es **F1 «baja» 0,4234**, con **recall 0,7878** (detecta
cerca de cuatro de cada cinco descensos) y **precisión 0,2895** (una de cada 3,4
alertas es correcta). El **Brier multiclase es 0,4692**, peor que el de una
constante entrenada con las prevalencias de *train* (0,4419), porque la prevalencia
de «baja» pasó de **5,2 % a 10,2 %** entre los periodos. Esa combinación —buen
recall, precisión moderada, calibración degradada por cambio de régimen— define el
producto: un **sistema de alerta temprana para priorizar la revisión humana**, no
un oráculo ni un clasificador autónomo.

La conclusión central es que **el techo es del dato, no del método**. Se probaron
nueve palancas —regularización, selección de variables, demografía, trayectoria,
contexto institucional, dos familias alternativas (TabICLv2 y Laya), nivel de
formación y lags de dos periodos— y **ninguna superó el criterio de +2 pp**; la
mejor, trayectoria, aportó +0,78 pp. El modelo limpio (sin redundancias ni
features casi vacías) **empeoró** el F1 entre 1,08 y 1,51 pp. El benchmark de
identidad mostró que la ventaja por reconocer personas es de **2,18 pp**, muy por
debajo del umbral de 5 pp que habría obligado a reentrenar. El límite no está en el
algoritmo: está en que el censo describe **qué produjo** cada investigador, no
**con qué financiación, con quién y bajo qué condiciones institucionales**.

### 1.3 Cifras clave

| Indicador | Valor | Fuente |
|---|---:|---|
| Producción descargada | 1,35 GB · 3 166 629 filas | Manifiesto `produccion_20261025_193218.json` |
| Transiciones modelables | 43 187 (18 116 personas) | `dataset_20261025_202401.json` |
| Train / val / test | 19 838 / 9 994 / 13 355 | `model_card.md` §2 |
| Features | 172 (111 con `gain > 0`) | `model_card.md` §3 |
| F1 «baja» / recall / precisión | **0,4234 / 0,7878 / 0,2895** | `expE_test_20261026_024016.json` |
| F1 macro / Brier | 0,5109 / 0,4692 | idem |
| Delta de identidad A−B | **+2,18 pp** | `benchmark_B_20261027_201425.json` |
| Modelo bayesiano (val) | Brier 0,4370 · AUC 0,817 · F1 «baja» 0,003 | `evaluacion_bayesiano_minimo` |

### 1.4 Contribuciones

Las contribuciones evaluables son cinco: (i) una **base reproducible** con
integridad criptográfica y validación anti-fuga; (ii) un **benchmark de identidad**
que separa identidad de volumen y mide la inflación en 2,18 pp; (iii) una
**arquitectura con máscaras estructurales** que respeta la escala real de
categorías; (iv) una **capa bayesiana** de calibración e incertidumbre, con su
límite declarado; y (v) un **diagnóstico de techo** con nueve palancas y dos
familias alternativas documentadas.

---

## 2. Contexto y marco teórico

### 2.1 El SNCTI y la categorización de investigadores

El Sistema Nacional de Ciencia, Tecnología e Innovación (SNCTI) es el conjunto de
actores e instrumentos que el Ministerio de Ciencia, Tecnología e Innovación
(Minciencias) coordina para fomentar la CTeI; su marco normativo invoca la Ley 1951
de 2019, el Decreto 2226 de 2019 y el Documento CONPES 3582 de 2009
(Minciencias, 2020, p. 1). En ese sistema, el **reconocimiento
no es un premio ni un trámite**: es la verificación oficial de que una persona o un
grupo cumple los criterios del modelo de medición. Para los investigadores, la
convocatoria vigente verifica los criterios con base en la información registrada
en el CvLAC y avalada por la institución (Minciencias, 2024).

La categoría **no se elige ni se solicita**: la asigna el sistema a partir de la
hoja de vida, con un orden de prioridad que va de Emérito a Junior
(Minciencias, 2024, p. 42). Solo las cuatro primeras categorías son
«investigadores» en sentido estricto:

| Categoría | Requisito de formación | Producción mínima | Formación de RRHH | Vigencia |
|---|---|---|---|---|
| **Emérito (IE)** | Doctorado **o** 15 productos tipo A en la trayectoria | Productos Top/A; 65 años o más; top 25 % de su gran área | Dirección de tesis de doctorado o maestría | **Vitalicia** |
| **Sénior (IS)** | Doctorado **o** 15 productos tipo A | **10** productos Top/A en los últimos **10 años** | 4 maestrías **o** 1 doctorado en 10 años | Hasta la siguiente convocatoria |
| **Asociado (I)** | Doctorado, maestría o especialidad clínica **o** 7 tipo A | **3** tipo A en 10 años **y 4** adicionales en 5 años | 1 doctorado, 2 maestrías u 8 pregrados en 5 años | Hasta la siguiente convocatoria |
| **Junior (IJ)** | Doctorado en ventana ≤3 años, **o** doctorado/maestría/pregrado con 7 productos | **1** tipo A en la trayectoria **y 4** productos en 5 años | No exige | Hasta la siguiente convocatoria |

Fuente: síntesis de la Tabla 1 del modelo de medición, versiones 2021 y 2024
(Minciencias, 2021a, pp. 49–52; Minciencias, 2024, pp. 44–47). Los umbrales son
idénticos en ambas versiones.

Tres consecuencias de esta arquitectura son decisivas para el modelado:

1. **No hay ascenso automático.** Cada convocatoria reevalúa; la categoría puede
   mantenerse, subir o no alcanzarse (Minciencias, 2024, p. 42).
2. **La ventana móvil produce descensos «sin culpa».** Un producto que sale de la
   ventana deja de contar, de modo que la categoría puede perderse sin que la
   persona haya dejado de producir (Minciencias, 2021a, pp. 50–51).
3. **La evidencia de formación también está ventaneada** (10 años en Sénior, 5 en
   Asociado), lo que añade un segundo mecanismo de rotación.

El modelo predictivo no inventa la estructura: la **hereda** del reglamento. Eso
explica por qué la clase «baja» no es puro ruido —parte es mecánica de ventana— y
por qué la precisión tiene un techo estructural: la otra parte depende de
condiciones de elegibilidad que el censo no publica.

### 2.2 Lo que el censo captura y lo que no

El censo tiene 30 campos por registro y el dataset de modelo se alimenta de la
producción vinculada más agregados por persona y convocatoria. El cruce con los
criterios oficiales deja una asimetría nítida:

| Criterio oficial | ¿Está en el dato? | Variable o motivo |
|---|---|---|
| Categoría vigente | **Sí** | `ORDEN_CLAS_PR` (origen y `target_class`) |
| Productos Top/A (artículos, libros, capítulos, patentes) | **Sí** | 105 features de calidad y 58 de tipología |
| Productos de formación (tesis) | **Sí** | `n_tipologia_TESIS_*`, `n_categoria_TESIS_*` |
| Proyectos de I+D con calidad A/B/C | **Sí** | `n_tipologia_PROYECTO_*` y `*_CON_CALIDAD_*` |
| Trayectoria y permanencia | **Sí** | `tiempo_en_categoria`, historiales, `gap`, `momentum` |
| Pertenencia a grupos | **Parcial** | `n_grupos_distintos` (proxy débil) |
| **Financiación de proyectos** | **No** | Solo se trae la calidad del proyecto, no el financiador ni el monto |
| **Coautorías y cooperación** | **No** | 1,02 autores por producto, sin lista de coautores |
| **Aval institucional y vinculación contractual** | **No** | Se certifica en InstituLAC; el censo trae filiación, no contrato |
| **Cuartil JCR/SJR en el año de publicación** | **No** | Se trae la categoría ya calculada |
| **Fecha de grado del doctorado** | **No** | Solo nivel de formación y número de orden |

Fuente: `criterios_minciencias.md` §5–§6 (síntesis de Minciencias, 2021a, 2024).

La lectura es directa: el censo captura **la producción y la categoría**, y no
captura **los procesos** (financiación, cooperación, aval, condiciones
diferenciales). Esa asimetría —producción sí, procesos no— es la que explica el
techo que se documenta en el §5.

### 2.3 Estado del arte

**El estudio más cercano al problema.** Godoy, Abramo, D'Angelo y Cortés (2026)
trabajan con **40 485 observaciones** de las mismas seis convocatorias y las
clasifican en los rangos Junior, Asociado y Sénior. Estiman una **regresión
ordinal** con variable latente y puntos de corte; su test de líneas paralelas
**rechaza** el supuesto de odds proporcionales (p < 0,001) y la versión no
restringida —con efectos distintos por umbral— es la que gana (LR = 911, gl = 13,
p < 0,001). Encuentran que la movilidad geográfica **no acelera** la promoción y
que el **contexto institucional** (concentración de capital académico, medida con
un HHI de rangos) es el correlato más fuerte del resultado, por encima del mercado
laboral local. Nuestro dataset —construido de forma independiente— tiene **43 187
transiciones**, un tamaño casi idéntico, lo que constituye una validación externa
de la ingesta.

El estudio valida el **diagnóstico** (las transiciones no son homogéneas y el
supuesto ordinal fuerte falla), no nuestra arquitectura: ellos no usan máscaras ni
un modelo bayesiano. Nuestra combinación de máscaras + ordinal bayesiano como capa
sigue siendo una decisión de ingeniería propia, y así se declara.

**Predicción de promoción con aprendizaje automático.** Los tres trabajos
localizados predicen **promoción sí/no**, no un ordinal de tres resultados:

- Yeo, Lim, Kumar y Thompson (2024) comparan cinco métodos en un centro médico
  académico con más de 2 200 profesores y seleccionan **Random Forest**; el
  producto es una calculadora para aspirantes y comités.
- Gayatri, Prabowo, Heryadi y Kuncoro (2025) usan **1 229 docentes**, aplican
  **SMOTE** y reportan Random Forest con F1 **0,989**. Esa cifra no es comparable
  con la nuestra: mezcla remuestreo sintético, partición no temporal y un problema
  binario más pequeño (véase §5.2).
- Jafor, Wadud, Nur y Rahman (2023) aplican AdaBoost a promoción de empleados, un
  dominio de recursos humanos que no se puede extrapolar sin advertirlo.

**No se localizó un estudio que use XGBoost para predecir promoción académica o
categorización de investigadores.** La elección de XGBoost se sostiene por la
evidencia general sobre datos tabulares, no por una comparación publicada en este
dominio; presentarla como «lo que dice la literatura del tema» sería inexacto.

**Por qué árboles y no redes neuronales.** Grinsztajn, Oyallon y Varoquaux (2022)
muestran que los modelos basados en árboles mantienen ventaja en tablas típicas de
tamaño medio, y Shwartz-Ziv y Armon (2022) encuentran que el *deep learning* no
supera a XGBoost en datos tabulares cuando la comparación es justa. Con 19 838 a
29 832 filas por fold, 172 columnas dispersas y 132 features con más de 90 % de
ceros, nuestro caso cae de lleno en ese régimen.

**Umbral, desbalanceo y métricas.** Lipton, Elkan y Narayanaswamy (2014)
demuestran que, con probabilidades bien calibradas, el umbral que maximiza F1 es
**la mitad del F1 óptimo**, no 0,5. van den Goorbergh, van Smeden, Timmerman y Van
Calster (2022) muestran que las correcciones de desbalanceo (SMOTE,
*undersampling*) no mejoran la discriminación y **degradan la calibración**. Saito
y Rehmsmeier (2015) y Davis y Goadrich (2006) fundamentan el uso de curvas
precisión-recall con clases desbalanceadas; Richardson et al. (2024) ofrecen el
contrapunto de que la ROC no es intrínsecamente engañosa, lo que obliga a reportar
ambas lecturas sin convertir la AUC en argumento de venta.

**Validación temporal y fuga.** Tashman (2000), Bergmeir y Benítez (2010) y
Hyndman y Athanasopoulos (2021) establecen la validación por origen móvil para
datos con estructura temporal. Kaufman, Rosset, Perlich y Stitelman (2012)
formulan la fuga en minería de datos y Cerqua, Letta y Pinto (2025) documentan que
descuidar la estructura transversal y longitudinal del panel produce fugas
difíciles de detectar y desempeño fuera de muestra inflado.

**Coautoría.** Dies, Liu y Eliassi-Rad (2025) muestran que una red temporal de
coautoría mejora la predicción de colocación institucional «hasta un 10 %» y
«8,48 % (p = 0,005)» sobre el rango de la institución doctoral sola. Nuestro
archivo de producción **no contiene la lista de coautores** (1,02 autores por
producto, 72 226 pares en todo el censo), de modo que esa mejora no es
reproducible con el dato disponible: es una limitación del dato, no del método.

### 2.4 Brecha y posicionamiento

La literatura converge en tres puntos que esta consultoría adopta (transiciones
heterogéneas por categoría, familia ordinal correcta, validación temporal) y deja
tres huecos que el proyecto aborda:

1. **No se localizó un trabajo que aplique *gradient boosting* con restricciones
   estructurales a un registro nacional de investigadores.** Los estudios del
   dominio son binarios y con modelos clásicos.
2. **No se localizó un trabajo del dominio que mida la fuga por identidad en un
   panel de categorización.** El benchmark A/B y el control de volumen son una
   contribución metodológica transferible.
3. **No se localizó un trabajo que declare el techo con un criterio de adopción
   explícito** (+2 pp) y nueve palancas ejecutadas. La declaración de techo es, en
   sí misma, un resultado de consultoría.

---

## 3. Metodología

### 3.1 Pipeline de datos

| Etapa | Artefacto | Cifra | Control de calidad |
|---|---|---|---|
| Descarga Socrata `33dq-ab5a` | `produccion_grupos.csv` (externo) | **1,35 GB** · 3 166 629 filas · 64 páginas | SHA-256 `99a66ae6…`, manifiesto, contrato de 18 comprobaciones con tolerancia 0 |
| Padrón Socrata `bqtm-4y2h` | `target.parquet` | 77 237 registros · 30 086 personas | SHA-256 `663c89ef…`, V05 |
| Transiciones contiguas (`gap == 1`) | `modelo_dataset_ventana_contiguo.parquet` | **43 187** filas · 18 116 personas | V01, V07, V09 |
| Features de producción | 172 variables | 4 volumen + 5 clase + 58 tipología + 105 calidad | V06 anti-fuga |
| Partición temporal | `train` 19 838 · `val` 9 994 · `test` 13 355 | Cohortes de destino 17–19 / 20 / 21 | V08 |

La descarga se hizo **paginada** (50 000 filas por página, orden por `:id`) con
escritura en streaming, *checkpoint* por `offset`, reintentos con retroceso
exponencial y hash calculado mientras se escribe (Socrata, s. f.). La justificación
frente a una descarga directa —reanudación, determinismo, detección de páginas
inválidas y comparabilidad con el repositorio auditado— está desarrollada en el
[Informe 01](01_ingesta_y_datos.md), §3.1.

El detalle de las validaciones V01–V09 y del contrato C01–C12/A01/E01–E05 consta
en el [Informe 01](01_ingesta_y_datos.md), §2.3–§2.5. La comprobación crítica es
**V06**: reconstruye la etiqueta y el `split` desde el censo original y exige
coincidencia exacta con el parquet, de modo que ninguna feature pueda haberse
calculado con la convocatoria equivocada.

### 3.2 Por qué validación temporal y no aleatoria

Una partición aleatoria en un panel mezcla pasado y futuro: el modelo vería la
transición 2019→2021 de una persona y se evaluaría en su transición 2017→2019.
Aprendería de «lo que pasó después» para predecir «lo que pasó antes», y la
estimación sería optimista. Kaufman et al. (2012) formulan el problema de la fuga;
Cerqua et al. (2025) documentan que descuidar la estructura del panel produce
fugas difíciles de detectar y desempeño inflado; Tashman (2000) y Bergmeir y
Benítez (2010) establecen la validación por origen móvil.

El diseño concreto es una versión discreta de esa regla, adaptada a que solo hay
seis cohortes:

| Fold | Entrena | Valida | Evalúa |
|---|---|---|---|
| F1 | cohorte 17 | 18 | 19 |
| F2 | 17–18 | 19 | 20 |
| F3 | 18 | 19 | 20 |
| Test final | 2014–2019 (29 832 filas) | — | **2021 (13 355)** |

La partición aleatoria se descartó además por una razón de **uso**: el sistema
predice el futuro de la población conocida, no la entrada de personas nuevas. Un
split aleatorio respondería a otra pregunta (¿reconozco a esta persona?) y
produciría métricas que no corresponden al despliegue previsto.

### 3.3 Por qué XGBoost y no otra familia

La elección se evaluó contra tres alternativas y se decidió con evidencia, no por
preferencia:

| Alternativa | Evidencia | Veredicto |
|---|---|---|
| **Deep learning tabular** | Grinsztajn et al. (2022): los árboles siguen siendo competitivos en tablas de ~10 000 filas; Shwartz-Ziv y Armon (2022): el DL no supera a XGBoost en tablas | **Descartado**: no hay ventaja documentada y sí costo de ajuste con 19,8k filas |
| **Bayesiano ordinal** | Brier 0,4370 y AUC 0,817 (mejor calibración), pero `argmax` degenerado: 98,95 % «se mantiene» y F1 «baja» 0,003 | **No operativo**; se conserva como capa de incertidumbre ([Informe 04](04_modelo_bayesiano.md)) |
| **Modelos de fundación** | TabICLv2 con contexto 500 en CPU: F1 0,1269 (−17,16 pp) (Qu et al., 2026); Laya zero-shot: ρ = 0,075, p = 0,458 (Convai Innovations, s. f.) | **Descartados** ([Informe 05](05_pruebas_alternativas.md)) |

XGBoost ofrece, en este régimen, tres ventajas concretas: maneja de forma natural
features dispersas y de cola (132 con más de 90 % de ceros), no requiere
representaciones densas ni *embeddings*, y su `gain` por variable permite auditar
qué usa el modelo, algo que un comité de revisión necesita. La configuración final
—`n_estimators=100`, `max_depth=7`, `learning_rate=0,05`, `subsample=0,8`,
`gamma=0,1`, pesos de clase balanceados, `random_state=42`— es el resultado de una
búsqueda de 54 configuraciones con validación temporal; el detalle está en el
[Informe 03](03_modelado_xgboost.md), §2.3.

**Sobre el modelo bayesiano.** El modelo ordinal se implementó con un logit
acumulativo (McCullagh, 1980) en PyMC 5, con efectos aleatorios por categoría y
periodo (PyMC, s. f.). La comparación no es «cuál es más moderno» sino «cuál sirve
para decidir». El bayesiano **calibra mejor** (Brier 0,4370 frente a 0,5479 del
XGBoost de la Ronda 1) y **ordena mejor** la clase «baja» (AUC 0,817 frente a
0,563), pero su regla automática de decisión (`argmax`) colapsa a la clase
mayoritaria y produce F1 «baja» 0,003. La división de trabajo es explícita: XGBoost
clasifica; el bayesiano aporta intervalos de credibilidad y una lectura honesta de
la incertidumbre. Presentarlos como alternativas intercambiables sería inexacto.

### 3.4 Por qué máscaras estructurales

El fenómeno no es homogéneo por categoría. Godoy et al. (2026) rechazan el
supuesto de odds proporcionales y encuentran que los umbrales responden a procesos
distintos; en nuestros datos, además, hay dos hechos duros:

- **Junior no puede bajar**: no existe categoría inferior. Modelar `p(baja)` para
  un Junior sería estimar un evento imposible.
- **Emérito no tiene transiciones** en el censo: no hay filas que modelar.

La arquitectura resultante es un modelo por categoría de origen: Junior binario
(`sube` vs `se mantiene`), Asociado y Sénior tricótomos, Emérito excluido. Las
máscaras **eliminan regiones del espacio de probabilidad que el fenómeno no
permite** y, con ello, mejoran la calibración de las clases que sí existen. La
comparación en validación contra el modelo multiclase plano de la Ronda 1 muestra
el efecto: F1 «baja» en `argmax` de 0,132 a 0,244, F1 macro de 0,394 a 0,498, y
F1 «baja» con umbral de 0,345.

### 3.5 Por qué el umbral 0,15

Con clases desbalanceadas y F1 como métrica, el umbral 0,5 es sistemáticamente
demasiado alto. Lipton et al. (2014) demuestran que, si las probabilidades están
bien calibradas, el umbral que maximiza F1 es **la mitad del F1 óptimo**. Nuestro
F1 «baja» es 0,4234; la mitad es ≈0,21, y el umbral elegido (0,15) está en ese
orden.

El umbral se fijó con la **mediana de los umbrales óptimos de los folds**
(0,12 / 0,27 / 0,15), nunca con el test. La sensibilidad es real: moverlo cambia el
recall entre 0,54 y 0,89, y por eso debe **recalcularse con cada cohorte nueva**.
Se usaron pesos de clase balanceados, sin SMOTE, siguiendo la evidencia de van den
Goorbergh et al. (2022) de que el remuestreo sintético daña la calibración.

### 3.6 Reproducibilidad

La reproducibilidad está anclada a tres hashes de entrada (dataset, features y
censo), un entorno fijado (Python 3.11.9, XGBoost 3.2.0, scikit-learn 1.9.1,
pandas 3.1.0, numpy 2.4.6), una semilla (42) y un comando único de reentrenamiento
documentado en `model_card.md` §7. Los artefactos de cada experimento —JSON de
métricas y *logs*— están versionados en `07_modelo/modelado/resultados/`, y los
manifiestos de ingesta permiten reconstruir la base desde cero. El repositorio
incluye además la validación del RAG (15 reglas PASA, 0 fallas, 2 advertencias
declaradas), que actúa como control de coherencia documental.

---

## 4. Experimentación y resultados

### 4.1 Las nueve palancas

El criterio de adopción quedó fijado antes de la iteración de cierre: una palanca
se adopta solo si mejora el F1 «baja» fuera de muestra en **≥ 2 pp** (media OOS ≥
0,3185 sobre 0,2985) sin degradar el Brier de forma sustancial. Ninguna lo logró.

| # | Palanca | Mejor F1 «baja» OOS | Δ vs 0,2985 | Veredicto |
|---|---|---:|---:|---|
| 1 | Regularización (54 configuraciones) | 0,2985 | 0,00 | Define la base de la Ronda 2 |
| 2 | Selección de features (top 50/80/120) | 0,2985 | 0,00 | Sin efecto |
| 3 | Demografía (género, edad, depto, institución) | 0,2983 | −0,02 pp | Descartada |
| 4 | Trayectoria (5 features) | **0,3063** | **+0,78 pp** | No alcanza |
| 5 | Contexto institucional (HHI + movilidad) | 0,3032 | +0,47 pp | No alcanza |
| 6 | TabICLv2 zero-shot | 0,1269 | **−17,16 pp** | No competitivo |
| 7 | Laya zero-shot | ρ = 0,075 (p = 0,458) | Sin señal | No aporta |
| 8 | Nivel de formación | 0,2987 | +0,02 pp | Sin efecto |
| 9 | Lags de dos periodos | 0,3049 | +0,64 pp | No alcanza |

Fuente: `validacion_honesta.md` § «Cierre definitivo». El detalle de cada
experimento —incluidos los folds y las desviaciones— está en el
[Informe 03](03_modelado_xgboost.md) §4.6 y en el
[Informe 05](05_pruebas_alternativas.md) §4.

Tres lecturas de la tabla:

1. **El orden de magnitud es pequeño y consistente** (entre −0,02 y +0,78 pp)
   cuando la palanca era razonable. No hay una mejora escondida: hay un techo.
2. **La única palanca con respaldo externo fuerte** (contexto institucional, de
   Godoy et al., 2026) aportó +0,47 pp, por debajo del umbral. El HHI institucional
   es un correlato del **nivel** de categoría, no del **cambio** entre
   convocatorias.
3. **Cambiar de familia o de representación empeora**, no mejora: TabICLv2 cae
   17 pp y Laya no muestra señal. El techo no es del algoritmo.

### 4.2 Métricas de cierre y matriz de confusión

| Métrica (test 2021, n = 13 355) | Valor |
|---|---:|
| **F1 «baja»** | **0,4234** |
| **Recall «baja»** | **0,7878** |
| Precisión «baja» | 0,2895 |
| F1 macro | 0,5109 |
| Brier multiclase | 0,4692 |
| Exactitud | 0,5921 |
| AUC «baja» (global, inflada por la máscara de Junior) | 0,8631 |

Matriz de confusión registrada (umbral 0,117; véase la nota de trazabilidad):

| Real \ Predicho | `baja` | `se mantiene` | `sube` | Total |
|---|---:|---:|---:|---:|
| `baja` | **1 013** | 265 | 84 | 1 362 |
| `se mantiene` | 2 090 | **5 685** | 1 882 | 9 657 |
| `sube` | 332 | 795 | **1 209** | 2 336 |
| **Total** | 3 435 | 6 745 | 3 175 | **13 355** |

De la matriz se derivan: recall 0,7437, precisión 0,2949, exactitud 0,5921 y
F1 «baja» 0,4223; las alertas ocupan el 25,7 % de las filas (3 435).

> **Nota de trazabilidad.** La matriz que se conserva con conteos corresponde a la
> corrida de test de la Ronda 2 con umbral **0,117** (`pasoE_test_final`), que
> reportó F1 0,4223 y Brier 0,4592. La corrida de cierre con umbral **0,15**
> (`expE_test`) reportó F1 0,4234, recall 0,7878, precisión 0,2895 y Brier 0,4692;
> sus conteos no se guardaron como matriz. Se incluye la matriz disponible por su
> valor descriptivo —cuántos descensos se detectan y cuántas falsas alarmas se
> emiten—, no como métrica de cierre. La diferencia entre ambas corridas es de
> 0,0011 en F1 y de 0,0100 en Brier.

**Lectura operativa.** El modelo detecta **cerca de cuatro de cada cinco
descensos** y emite alerta en alrededor de una de cada cuatro filas; **una de cada
3,4 alertas es correcta**. Es un modelo de priorización: sirve para ordenar la cola
de revisión de un comité, no para sustituirlo. La precisión de 0,29 es el precio de
sostener un recall de 0,79 con una prevalencia del 10,2 %: el modelo prefiere no
perder descensos y acepta falsas alarmas.

### 4.3 Benchmark de identidad (A vs B)

En un panel temporal es normal que la misma persona aparezca en *train* y en
*test*: **64,31 % de las personas de test** (8 589 de 13 355) fueron vistas en
alguna convocatoria anterior. No es fuga de etiqueta —ninguna fila de test entra en
el entrenamiento— pero puede inflar el desempeño si el modelo «reconoce» a la
persona. Para medirlo se construyó un benchmark **entidad-disjunto** (B): se
eliminan del train y de la validación las personas que aparecen en el conjunto de
evaluación, y se compara con el modelo operativo (A).

| Modelo | F1 «baja» | Recall | Precisión | F1 macro | Brier |
|---|---:|---:|---:|---:|---:|
| **A** (operativo) | **0,4234** | 0,7878 | 0,2895 | 0,5109 | **0,4692** |
| **B** (entidad disjunta) | 0,4016 | 0,6153 | 0,2981 | 0,4412 | 0,4969 |
| **Control** (5 005 filas, identidad permitida) | 0,4222 | 0,7416 | 0,2951 | 0,5022 | 0,4400 |

Descomposición del delta de 2,18 pp:

| Componente | Cálculo | Valor |
|---|---|---:|
| Efecto **identidad** (a volumen fijo) | 0,4222 − 0,4016 | **+2,06 pp** |
| Efecto **volumen** (con identidad) | 0,4234 − 0,4222 | **+0,12 pp** |
| **Delta total A − B** | 0,4234 − 0,4016 | **+2,18 pp** |

La lectura es doble. Primero, **la inflación por identidad es de ~2,1 pp, no de
decenas de puntos**: con una sexta parte de los datos y personas compartidas se
llega a 0,4222, casi el 0,4234 del modelo completo; el modelo aprende **patrones de
producción**, no «caras». Segundo, **el perfil operativo sí cambia**: sin historia
previa, B detecta menos descensos (recall 0,6153 frente a 0,7878) con precisión
estable. La regla acordada era Δ < 5 pp ⇒ modelo robusto, y se cumple con holgura;
**no se reentrena**. El detalle metodológico está en el
[Informe 02](02_eda_y_auditoria.md) §4.7.

### 4.4 Alternativas y modelo limpio

| Prueba | Resultado | Decisión |
|---|---|---|
| TabICLv2 (contexto 500, CPU) | F1 0,1269 (−17,16 pp) | No competitivo |
| Laya zero-shot (100 filas) | ρ = 0,075 (p = 0,458) | Sin señal |
| Modelo limpio (123 features) | F1 0,2877 (−1,08 pp) | No se toca test |
| Modelo limpio (56 features) | F1 0,2834 (−1,51 pp) | No se toca test |

Las dos alternativas se documentan en el [Informe 05](05_pruebas_alternativas.md);
el modelo limpio, en el [Informe 02](02_eda_y_auditoria.md) §4.8 y en el
[Informe 03](03_modelado_xgboost.md). Ninguna de las cuatro pruebas justificó
volver al test: ya estaba reservado para la evaluación de cierre y no se reutilizó
para elegir modelo ni umbral.

### 4.5 Estabilidad y sobreajuste

| Indicador | Valor | Lectura |
|---|---:|---|
| F1 «baja» OOS (3 folds) | 0,2985 ± 0,0184 | Estable entre folds |
| F1 «baja» con umbral propio | 0,3054 | Referencia de la rejilla |
| Brecha train/val (F1 macro) | 0,83 vs 0,50 | Sobreajuste estructural |
| Brier en folds | 0,4196 | Mejor que el test (0,4692) |
| Umbrales óptimos por fold | 0,12 / 0,27 / 0,15 | Sensibilidad al régimen |
| Recall al mover el umbral | 0,54–0,89 | El punto de operación importa |

La brecha de sobreajuste (+0,33 en F1 macro) es consecuencia de la relación
filas/columnas (19,8k–29,8k filas, 172 features) y de la clase minoritaria; la
búsqueda de 54 configuraciones la atenúa, no la elimina. El Brier de folds (0,4196)
es mejor que el de test (0,4692) precisamente porque el test cambia de régimen.

---

## 5. Discusión: el techo del dato

### 5.1 Anatomía del 0,4234

Un F1 de 0,4234 con recall 0,7878 implica, por la definición de F1, una precisión
de 0,2895. Esa relación no es un accidente: con `precisión = TP/(TP+FP)` y
`recall = TP/P`, fijados P = 1 362 y recall = 0,7878, la precisión queda
determinada por el número de falsos positivos. Para mejorarla sin bajar el recall
habría que **separar mejor** los descensos reales de los falsos, y esa separación
depende de información que el modelo no tiene. Los cinco factores que explican el
techo son:

1. **Variables que faltan y que la literatura usa.** Financiación de proyectos,
   coautoría real, aval institucional y vinculación contractual, movilidad y
   mercado laboral local. Godoy et al. (2026) encuentran que el contexto
   institucional es el correlato más fuerte; Dies et al. (2025) muestran que la red
   de coautoría aporta «hasta un 10 %». Nuestro censo no publica ninguna de las
   dos con el detalle necesario.
2. **Solo cinco cohortes históricas.** 2013, 2014, 2015, 2017 y 2019 no alcanzan
   para separar tendencia de ruido ni para validar la estabilidad del umbral y del
   Brier entre regímenes.
3. **Cambio de régimen 2019→2021.** La prevalencia de «baja» pasa de 5,2 % a
   10,2 % y quiénes bajan cambia de composición (χ² = 469,53; V = 0,0737). Ninguna
   corrección de *prior shift* lo resuelve: las dos variantes probadas empeoran el
   Brier (0,4917 y 0,4851 frente a 0,4692).
4. **Drift de features.** Tres variables con PSI > 0,25 (proyecto de I+D con
   calidad, artículos y artículos de generación de contenido) y 69 de 172 con KS
   p < 0,01. El modelo aprende un régimen de producción que cambió.
5. **Incertidumbre irreducible del propio reglamento.** Parte de los descensos
   depende de la ventana móvil (previsible) y parte de la pérdida de elegibilidad
   por aval, contrato o condiciones diferenciales (no observada). Esa segunda parte
   actúa como ruido de etiqueta y pone un piso al error alcanzable.

A esto se suma el **desbalanceo** (5,15 % de «baja» en train) y el **tamaño
muestral** (19 838 filas de entrenamiento): con 172 columnas, el modelo memoriza
antes de generalizar, y la brecha train/val de +0,33 así lo muestra.

### 5.2 Por qué el F1 es 0,4234 y no 0,90

La comparación con los F1 de 0,99 de la literatura es engañosa por cuatro razones
concretas, y conviene decirlas en la defensa antes de que las pregunte el jurado:

| Diferencia | Nuestro caso | Estudios con F1 ≈ 0,99 |
|---|---|---|
| Tarea | Ordinal de 3 clases, clase minoritaria 10,2 % | Binaria (promoción sí/no) |
| Partición | Temporal por cohorte, test 2021 intacto | No temporal |
| Desbalanceo | Pesos de clase, sin remuestreo | **SMOTE** sobre conjunto pequeño |
| Tamaño | 19,8k–29,8k filas de train, 172 features | 1 229 docentes, pocas variables |

Gayatri et al. (2025) reportan F1 0,989 con 1 229 docentes, SMOTE y un problema
binario; ese número **no es comparable** con un F1 ordinal en un test temporal con
prevalencia cambiante. Yeo et al. (2024) reportan una calculadora con Random
Forest, no un ordinal. Presentar 0,99 como «estado del arte alcanzable» sería un
error de lectura, y la consultoría no lo comete.

El 0,90 tampoco es alcanzable con el censo actual por una razón aritmética: para
subir la precisión de 0,29 a 0,60 manteniendo recall 0,79 habría que reducir los
falsos positivos en más de dos tercios, y muchos de esos falsos positivos
corresponden, probablemente, a **descensos que no ocurrieron por causas no
observadas** (aval, contrato, condiciones diferenciales) o a **descensos que el
modelo no puede distinguir** de un mantenimiento con producción similar. Más
capacidad del modelo no crea esa información.

### 5.3 La paradoja de la limpieza

La intuición dice que quitar 49 features redundantes y 86 casi vacías debería
mejorar o, al menos, no empeorar. Los datos dicen lo contrario:

| Variante | Features | F1 «baja» OOS | Δ | Brier |
|---|---:|---:|---:|---:|
| Base (Ronda 2) | 172 | **0,2985** | — | **0,4196** |
| Solo VIF | 123 | 0,2877 | −1,08 pp | 0,4223 |
| Limpio completo | 56 | 0,2834 | −1,51 pp | 0,4223 |

Tres explicaciones plausibles, en orden de probabilidad:

1. **Las features redundantes actúan como regularización implícita.** XGBoost con
   `subsample=0,8` reparte el `gain` entre columnas clonadas; al podarlas, el
   modelo queda más expuesto al sobreajuste (la desviación entre folds sube entre
   57 % y 77 %).
2. **Las 67 features casi vacías que se eliminaron no eran ruido puro:** son las
   categorías raras que el modelo usa para separar «sube» en perfiles atípicos. Al
   quitarlas, el F1 macro se mantiene pero la cola de «baja» pierde señal.
3. **La winsorización al p99 altera 288 filas de test** (los productores
   extremos), que son justamente los que casi nunca bajan; el efecto es pequeño
   pero va en la dirección equivocada.

La lección metodológica es que **la limpieza no es gratis y debe probarse, no
suponerse**. Si en el futuro se quiere podar, tendría que hacerse **por familia de
producto** (colapsar duplicados en una sola columna suma), no eliminando columnas
una a una, y probarse con `colsample_bytree < 1` para no perder la diversidad que
hoy compensa la redundancia.

### 5.4 Qué significa el delta de identidad

Un delta de 2,18 pp podría leerse como «el modelo hace trampa». No es así: el
control de volumen demuestra que **casi todo el desempeño se sostiene con una
sexta parte de los datos** y sin personas nuevas (0,4222 con 5 005 filas frente a
0,4234 con 29 832). La identidad aporta 2,06 pp; el volumen, 0,12 pp. El modelo
generaliza a personas nuevas con una pérdida modesta de F1 (0,4234 → 0,4016), pero
**con una pérdida operativa relevante de recall** (0,7878 → 0,6153): sin historia
previa, alerta menos. Esa es la lectura honesta para el despliegue: el sistema
funciona mejor con población conocida y pierde sensibilidad en *cold start*.

### 5.5 Alcance epistémico

El modelo es **correlacional**. No estima efectos causales de la producción sobre
la categoría, ni de la institución sobre la promoción, ni del género sobre el
descenso. Godoy et al. (2026) advierten que el propio proceso de clasificación
puede reforzar jerarquías institucionales preexistentes; esa advertencia se
extiende a cualquier lectura causal de nuestras features. El modelo **predice la
asignación observada**, no la regla escrita, y si la regla cambió entre cohortes
(como cambió entre 2021 y 2024) el modelo mezcla regímenes. Es una herramienta de
priorización y de medición, no un instrumento de política ni un dictamen de mérito.

---

## 6. Conclusiones y recomendaciones

### 6.1 Conclusiones

1. **El modelo es un sistema de alerta temprana, no un oráculo.** Con F1 0,4234,
   recall 0,7878 y precisión 0,2895, detecta cerca de cuatro de cada cinco
   descensos y acierta una de cada 3,4 alertas. Su valor está en **ordenar la cola
   de revisión** y en hacer explícito el riesgo, no en decidir.
2. **El techo es del dato.** Nueve palancas en cuatro rondas, dos familias
   alternativas y un modelo limpio: ninguna superó +2 pp; la mejor aportó +0,78 pp.
   Las variables que mueven la aguja en la literatura (financiación, coautoría
   real, mercado laboral, movilidad) no están en el censo.
3. **La validación temporal es la decisión metodológica más importante.** Sin ella,
   cualquier métrica sería optimista y no correspondería al despliegue. El precio
   es un test que cambia de régimen y un Brier peor que la constante.
4. **La identidad infla poco y el volumen casi nada.** Δ A−B = 2,18 pp (2,06 de
   identidad + 0,12 de volumen), por debajo del umbral de 5 pp. El modelo aprende
   patrones de producción, no personas.
5. **Las máscaras estructurales son correctas y medibles.** Respetan la escala real
   de categorías y mejoran el F1 «baja» de 0,132 a 0,244 en `argmax` y a 0,345 con
   umbral, frente al modelo plano de 173 features.
6. **El bayesiano no reemplaza al XGBoost, pero lo complementa.** Calibra mejor
   (Brier 0,4370, AUC 0,817) y entrega intervalos de credibilidad; su `argmax` es
   degenerado y no sirve para clasificar.
7. **La limpieza agresiva empeora.** −1,08 pp con 123 features y −1,51 pp con 56;
   la redundancia funciona como regularización implícita en este dataset.

### 6.2 Recomendaciones de uso

| Recomendación | Detalle | Riesgo si no se sigue |
|---|---|---|
| **Usar el ranking, no el valor puntual** | Ordenar por `p(baja)` y aplicar el umbral; no interpretar la probabilidad como probabilidad real | El Brier es peor que la constante; el valor puntual engaña |
| **Recalcular el umbral con cada cohorte** | El óptimo por fold va de 0,12 a 0,27; congelarlo degrada el punto de operación | Recall entre 0,54 y 0,89 según el umbral |
| **Mantener revisión humana** | El modelo prioriza; el comité decide | 7 de cada 10 alertas son falsas |
| **Vigilar las tres features con PSI > 0,25** | Proyecto I+D con calidad, artículos, artículos de generación de contenido | La calibración se degrada sin aviso |
| **Reentrenar con cada convocatoria nueva** | Añadir la cohorte y repetir la validación temporal | El régimen 2021→2023 puede cambiar otra vez |
| **No usar el modelo para decisiones automatizadas** | Es una herramienta de priorización, no de sanción | Uso indebido de una predicción correlacional |

### 6.3 Trabajo futuro

Superar el techo exige **datos nuevos**, no más *machine learning* sobre el mismo
censo. La tabla ordena las fuentes por valor esperado y costo:

| Dato faltante | Fuente potencial | Qué desbloquearía | Esfuerzo |
|---|---|---|---|
| **Lista de coautores por producto** | CvLAC / GrupLAC | Red de coautoría real; cooperación y cohesión (pesos 0,4 y 0,1 del Indicador de Grupo) | Alto (acceso y procesamiento) |
| **Financiación por proyecto** | Proyectos con financiador y monto | Capacidad de gestión y elegibilidad; el atributo que el modelo oficial sí mide | Alto (requiere acceso) |
| **Vinculación contractual y aval** | InstituLAC | Pérdida de elegibilidad, causa probable de descensos no observados | Alto |
| **Fecha de grado del doctorado** | CvLAC | Vía (i) de Junior y ventana de 3 años | Bajo–medio |
| **Gran área OCDE y percentil por área** | Censo (`NME_GRAN_AREA_PR`) | Percentil por área, lógica de cuartiles oficial | Bajo |
| **Mercado laboral y movilidad** | DANE / ciudad de residencia | Los correlatos de Godoy et al. (2026) | Medio |
| **Más cohortes históricas** | Minciencias | Más folds y estabilidad del umbral | Alto |

En el plano metodológico quedan tres frentes de bajo costo y alto valor:

- **Weighted kappa** como métrica ordinal de reporte (Cohen, 1968): se calcula con
  la matriz de confusión y penaliza los errores según la distancia entre
  categorías.
- **Ordinal boosting (OGBoost)** (Sharabiani et al., 2026): usa el orden en la
  pérdida; no se probó con máscaras y es el candidato natural para mejorar la
  calibración sin perder discriminación.
- **Auditoría de equidad** por género, región e institución, y **monitoreo de
  drift** con PSI en cada cohorte nueva.

### 6.4 Cierre

El proyecto entrega algo más valioso que un F1: entrega un **marco de medición
honesto**. La base es reproducible, la validación respeta el tiempo, las
restricciones estructurales son explícitas, la fuga de identidad está medida, las
nueve palancas están documentadas y el techo está diagnosticado con evidencia. El
mensaje para el Observatorio es claro: **con el censo actual se puede priorizar la
revisión de descensos con una sensibilidad cercana al 80 %, pero no se puede
predecir con precisión suficiente para automatizar**. Para superar el 0,4234 no hace
falta un modelo más complejo; hace falta el dato que el censo no publica: con
quién se produce, con qué se financia y bajo qué condiciones institucionales se
permanece en el sistema.

---

## 7. Referencias bibliográficas

Bergmeir, C., & Benítez, J. M. (2010). A survey of cross-validation procedures for
model selection. *Statistics Surveys, 4*, 40–79.
https://doi.org/10.1214/09-SS054

Cerqua, A., Letta, M., & Pinto, G. (2025). On the (mis)use of machine learning
with panel data. *Oxford Bulletin of Economics and Statistics, 88*(3), 506–518.
https://doi.org/10.1111/obes.70019

Cohen, J. (1968). Weighted kappa: Nominal scale agreement provision for scaled
disagreement or partial credit. *Psychological Bulletin, 70*(4), 213–220.
https://doi.org/10.1037/h0026256

Convai Innovations. (s. f.). *Laya* [Model card]. Hugging Face.
https://huggingface.co/convaiinnovations/laya

Davis, J., & Goadrich, M. (2006). The relationship between precision-recall and
ROC curves. En *Proceedings of the 23rd International Conference on Machine
Learning*. ACM. https://doi.org/10.1145/1143844.1143874

Dies, S., Liu, D., & Eliassi-Rad, T. (2025). *Forecasting faculty placement from
patterns in co-authorship networks*. arXiv. https://arxiv.org/abs/2507.14696

Gayatri, N. A. G., Prabowo, H., Heryadi, Y., & Kuncoro, E. A. (2025). Predicting
academic rank improvement of higher education lecturers using machine learning
model. En *2025 International Conference on Information and Communication
Technology (ICoICT)*. https://doi.org/10.1109/icoict66265.2025.11193099

Godoy, J. M., Abramo, G., D'Angelo, C. A., & Cortés, J. D. (2026). Should I stay
or should I go? The role of national geographic mobility, gender, age,
institutional research profiles, and labor market on the career performance of the
scientific workforce in Colombia. *Scientometrics, 131*(9), 5803–5824.
https://doi.org/10.1007/s11192-026-05716-9

Grinsztajn, L., Oyallon, E., & Varoquaux, G. (2022). Why do tree-based models
still outperform deep learning on typical tabular data? En *Advances in Neural
Information Processing Systems 35* (NeurIPS 2022).
https://arxiv.org/abs/2207.08815

Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and
practice* (3.ª ed.). OTexts. https://otexts.com/fpp3/

Jafor, M. A., Wadud, M. A. H., Nur, K., & Rahman, M. M. (2023). Employee promotion
prediction using improved AdaBoost machine learning approach. *AIUB Journal of
Science and Engineering, 22*(3), 258–266. https://doi.org/10.53799/ajse.v22i3.781

Kaufman, S., Rosset, S., Perlich, C., & Stitelman, O. (2012). Leakage in data
mining: Formulation, detection, and avoidance. *ACM Transactions on Knowledge
Discovery from Data, 6*(4), 1–21. https://doi.org/10.1145/2382577.2382579

Lipton, Z. C., Elkan, C., & Narayanaswamy, B. (2014). *Thresholding classifiers to
maximize F1 score*. arXiv. https://arxiv.org/abs/1402.1892

McCullagh, P. (1980). Regression models for ordinal data. *Journal of the Royal
Statistical Society: Series B, 42*(2), 109–142.
https://doi.org/10.1111/j.2517-6161.1980.tb01109.x

Ministerio de Ciencia, Tecnología e Innovación. (2020). *Procedimiento de
clasificación de grupos de investigación y reconocimiento de investigadores del
SNCTeI* (M601PR04, Versión 00).
https://minciencias.gov.co/sites/default/files/m601pr04_clasificacion_grupos_y_reconocimiento_investigadores_v00.pdf

Ministerio de Ciencia, Tecnología e Innovación. (2021a). *Modelo de medición de
grupos de investigación, desarrollo tecnológico o de innovación y de reconocimiento
de investigadores del SNCTI* (Versión 00, M601PR04G01).
https://minciencias.gov.co/sites/default/files/m601pr04g01_modelo_medicion_grupos_investigacion_tecnologica_o_innovacion_y_reconocimiento_investigadores_sncti_v00.pdf

Ministerio de Ciencia, Tecnología e Innovación. (2021b). *Producción de grupos de
investigación* [Conjunto de datos]. datos.gov.co.
https://www.datos.gov.co/resource/33dq-ab5a.csv

Ministerio de Ciencia, Tecnología e Innovación. (2024). *Modelo de medición de
grupos de investigación, desarrollo tecnológico o de innovación y de reconocimiento
de investigadores del SNCTI* (Versión 02, M601PR04G01).
https://minciencias.gov.co/sites/default/files/upload/convocatoria/m601pr04g01_modelo_medicion_grupos_investigacion_tecnologica_o_innovacion_y_reconocimiento_investigadores_-_2024_1.pdf

PyMC. (s. f.). *PyMC documentation* (Versión 5). https://www.pymc.io/

Qu, J., Holzmüller, D., Varoquaux, G., & Le Morvan, M. (2026). *TabICLv2: A
better, faster, scalable, and open tabular foundation model*. En *International
Conference on Machine Learning (ICML 2026)*. https://arxiv.org/abs/2602.11139

Richardson, E., Trevizani, R., Greenbaum, J. A., Carter, H., Nielsen, M., &
Peters, B. (2024). The receiver operating characteristic curve accurately assesses
imbalanced datasets. *Patterns, 5*(6), 100994.
https://doi.org/10.1016/j.patter.2024.100994

Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative
than the ROC plot when evaluating binary classifiers on imbalanced datasets.
*PLOS ONE, 10*(3), e0118432. https://doi.org/10.1371/journal.pone.0118432

Sharabiani, M. T. A., Bottle, A., & Mahani, A. S. (2026). OGBoost: A Python
package for ordinal regression gradient boosting. *Journal of Statistical
Software, 117*(5). https://doi.org/10.18637/jss.v117.i05

Shwartz-Ziv, R., & Armon, A. (2022). Tabular data: Deep learning is not all you
need. *Information Fusion, 81*, 84–90.
https://doi.org/10.1016/j.inffus.2021.11.011

Socrata. (s. f.). *SODA API documentation*. https://dev.socrata.com/

Tashman, L. J. (2000). Out-of-sample tests of forecasting accuracy: An analysis
and review. *International Journal of Forecasting, 16*(4), 437–456.
https://doi.org/10.1016/S0169-2070(00)00065-0

van den Goorbergh, R., van Smeden, M., Timmerman, D., & Van Calster, B. (2022).
The harm of class imbalance corrections for risk prediction models: Illustration
and simulation using logistic regression, random forest, and RUSBoost. *Journal of
the American Medical Informatics Association, 29*(9), 1525–1534.
https://doi.org/10.1093/jamia/ocac093

Yeo, M. M., Lim, S. H., Kumar, A., & Thompson, A. W. (2024). Calculator for
predicting the probability of faculty promotion in an academic medical centre.
*BMJ Leader, 8*(3), 203–207. https://doi.org/10.1136/leader-2023-000861

---

### Documentos internos citados

- `07_modelo/informes/01_ingesta_y_datos.md` … `05_pruebas_alternativas.md`
  (suite modular).
- `07_modelo/modelado/model_card.md` — model card del clasificador.
- `07_modelo/modelado/validacion_honesta.md` — bitácora de rondas y cierre.
- `07_modelo/documentacion/auditoria_base_datos.md` — EDA, benchmark y modelo
  limpio.
- `07_modelo/documentacion/criterios_minciencias.md` — síntesis de los criterios
  oficiales.
- `07_modelo/documentacion/estado_del_arte.md` — revisión bibliográfica y
  referencias verificadas.
- `07_modelo/documentacion/laya_y_open_weights.md` — evaluación de Laya, TabICLv2
  y TabPFN-2.5.
- `07_modelo/modelado/diseno_bayesiano.md` — diseño del modelo bayesiano.
