# Evaluación de cumplimiento de los objetivos del repositorio auditado

**Fase 1 — Diagnóstico de cumplimiento · Semana 1**
Consultoría Estadística USTA · 2026-II

Este documento responde a una pregunta distinta de las que ya responden los seis
criterios de auditoría. Los criterios evalúan **cómo está hecho** el repositorio
(entendimiento, datos, código, estadística, lógica, historia). Aquí se evalúa
**si cumplió lo que se propuso**: para cada objetivo declarado y cada pregunta de
investigación, qué producto demostraría que se cumplió y si ese producto existe
hoy, es correcto y es reproducible.

---

## 1. Alcance, fuentes y método

### Fuentes de los objetivos (todas del repositorio auditado, commit `1528939`)

| Fuente | Qué aporta |
|---|---|
| `datos_originales/repo_auditado/informe_final.md:28` | **Objetivo general** |
| `datos_originales/repo_auditado/informe_final.md:32-40` | **5 objetivos específicos** |
| `datos_originales/repo_auditado/README.md:47-53` | **7 preguntas de investigación** |
| `datos_originales/repo_auditado/README.md:55-72` | 14 hallazgos críticos (lo que el repositorio dice haber encontrado) |
| `datos_originales/repo_auditado/docs/informe/informe_final.tex:192-199` | **6 preguntas** (Q1–Q6) — lista distinta de la del README |

> **Primera inconsistencia documentada.** El README declara **7 preguntas** y el
> informe LaTeX deja **6**. No es lo mismo con otro número: el informe **omite la
> pregunta de redes de co-filiación** (README preg. 5) aunque dedica una sección
> completa al tema (`informe_final.tex:568-579`, «Redes y poder institucional») y
> fusiona en su Q4 la brecha de género con su réplica en productividad. Adoptamos
> como referencia la lista de 7 del README, que es la más completa, y anotamos cada
> diferencia. Es del mismo tipo que las demás erratas del proyecto auditado
> (`datos_originales/ERRATA.md`).

### Método

Para cada objetivo se define primero el **criterio de cumplimiento**: el producto
concreto —archivo, tabla, figura o resultado— que demostraría que se cumplió.
Después se distingue **dos niveles de cobertura**, porque confundirlos sería el
error más fácil de cometer en este documento:

| Nivel | Significado | Dónde vive la evidencia |
|---|---|---|
| **A · Auditoría** | Revisamos y evaluamos el producto del auditado: existe, es correcto, tiene límites | `documentacion_auditoria/latex/objetivo_*/secciones/03_*.tex`, fichas de `data/analisis_codigo/` |
| **B · Análisis propio** | Volvimos a calcular o extendimos el análisis con métodos nuestros | `analisis_longitudinal.md`, `metodologia_muestreo.md`, `data/memoria/dashboard_eda.html`, JSON de `data/memoria/` |

Un objetivo puede estar **auditado y no reanalizado**: entonces la cobertura es
**Parcial**, porque sabemos qué hay y qué vale, pero no lo hemos reproducido.

### Verificación

Ninguna cifra de este documento se copió de otro documento. Se comprobó contra los
archivos: el esquema del modelo estrella se leyó de la base DuckDB
(`_archivo/scripts_oneoff/inspeccionar_estrella.py`), los recuentos de evidencia
de los CSV del auditado, y la ejecución real de los scripts está en
`datos_originales/reporte_ejecucion_51_poetry.csv`. **No se modificó el
repositorio auditado**; `datos_originales/verificar_hashes.py` confirma 236/236
hashes intactos.

---

## 2. Los objetivos declarados

### Objetivo general

> «Consolidar, validar y analizar los datos de investigadores reconocidos de las
> convocatorias 2017, 2019 y 2021 del Minciencias, y producir un modelo
> dimensional y un conjunto de análisis descriptivos y multivariados para
> facilitar su uso en el observatorio institucional.»
> — `informe_final.md:28`

### Objetivos específicos (`informe_final.md:32-40`)

| # | Enunciado literal (resumido) |
|---|---|
| **OE1** | Análisis descriptivo **por cada base** (2017, 2019, 2021) de variables clave: edad, género, área, afiliación, región |
| **OE2** | **Unir las tres bases** en una única tabla maestra con todas las convocatorias |
| **OE3** | **Verificar la unicidad de identificadores** de investigador mediante reglas (comparación de edades y atributos) |
| **OE4** | Diseñar y crear un **modelo dimensional (esquema estrella)** con nueve dimensiones y una tabla de hechos |
| **OE5** | Construir la **«gran tabla»** (sin IDs) y ejecutar análisis **univariado, bivariado, multivariado y clustering** para segmentar perfiles |

### Las 7 preguntas de investigación (`README.md:47-53`)

| # | Pregunta (resumida) | Equivalente en el informe LaTeX |
|---|---|---|
| **Q1** | ¿Qué tan confiable es la información de MinCiencias? ¿Permite comparar convocatorias? | Q1 |
| **Q2** | ¿El sistema retiene a sus investigadores? ¿Qué % sube, baja o desaparece? | Q2 |
| **Q3** | ¿La capacidad investigativa está concentrada o distribuida? **Comparación per cápita con población DANE 2018** | Q3 (añade «¿en qué departamentos trabajan?») |
| **Q4** | ¿Hay paridad de género por gran área OCDE? ¿Se cerró la brecha en STEM? | Q4 (añade «¿se replica en productividad?») |
| **Q5** | ¿Cómo se conectan las instituciones por doble afiliación? **¿Hay universidades-puente?** | **sin equivalente** |
| **Q6** | ¿La composición refleja la diversidad del país (etnia, discapacidad, víctimas)? | Q5 (solo composición étnica) |
| **Q7** | ¿Quién firma la producción que MinCiencias mide? ¿Sénior > Junior? ¿Brecha de género en outputs? | Q6 (fusionada con Q4) |

---

## 3. Tabla de cumplimiento

### 3.1 Objetivos

| Objetivo | Criterio de cumplimiento (qué producto lo demostraría) | ¿Cubierto por nuestro trabajo? | Evidencia (ruta) | Comentarios |
|---|---|---|---|---|
| **General** | (a) un consolidado único y validado; (b) un modelo dimensional poblado; (c) análisis descriptivos **y multivariados** publicados con evidencia | **Parcial** | `datos_originales/repo_auditado/informe_final.md:28` · `documentacion_auditoria/latex/objetivo_5/secciones/03_logica.tex` · `datos_originales/repo_mejorado/CHANGELOG.md` · `documentacion_auditoria/analisis_longitudinal.md` | Los tres componentes existen, pero (a) el consolidado cubre **3 de 6** convocatorias (ERRATA E2), (b) el modelo poblado que inspeccionamos tiene **50 891 hechos de 3 convocatorias** mientras su evidencia versionada documenta **77 237 de 6** (§4.1), y (c) la parte **multivariada** vive en R legacy que ya no corre (§4.3) |
| **OE1** Descriptivos por base | Panel de estadísticas descriptivas **por convocatoria** (2017/2019/2021) de edad, género, área, afiliación y región | **Parcial** | `documentacion_auditoria/latex/objetivo_4/secciones/03_estadistica.tex` · `documentacion_auditoria/data/memoria/dashboard_eda.html` (pestaña 1) · `data/memoria/eda_resultados.json` · `repo_auditado/evidencias/panel_longitudinal_*.csv` | El auditado **sí produjo** descriptivos por convocatoria. Nuestro EDA es de **diseño distinto**: una fila por persona en su **última convocatoria observada** (30 086 personas), no un corte por base. Cubre el mismo terreno por otro camino; falta el panel por convocatoria |
| **OE2** Unir las tres bases | Archivo único con las tres convocatorias (**2017, 2019, 2021**), con su conteo verificable | **Sí** | `datos_originales/repo_auditado/datos/tarea_join/investigadores_consolidado.xlsx` · `documentacion_auditoria/latex/objetivo_2/secciones/03_datos.tex` · `datos_originales/ERRATA.md` (E2) | **Cumplido en los términos del objetivo**: el objetivo pide *las tres* bases y el consolidado es exactamente **50 891 filas × 30 columnas con las 3 convocatorias** (verificado). El problema de «3 de 6» no es un incumplimiento del OE2: es una **ampliación posterior de alcance** del README que el dato versionado no acompaña |
| **OE3** Unicidad de IDs | Regla de deduplicación **documentada y cuantificada**: duplicados detectados, criterio aplicado y falsos positivos | **Parcial** | `documentacion_auditoria/latex/objetivo_4/secciones/03_estadistica.tex` · `documentacion_auditoria/latex/objetivo_3/secciones/03_codigo.tex` · `data/analisis_codigo/*.json` (51 fichas) | La verificación **existe y funciona** (coherencia de edad ±4 años y de género), y nuestro criterio 4 la califica de «heurística razonable». Pero **no está formalizada**: no hay informe de duplicados, ni tasa de falsos positivos, ni umbral justificado. No la formalizamos nosotros tampoco |
| **OE4** Modelo estrella | Base de datos con las dimensiones y la tabla de hechos, **poblada** y con integridad referencial verificada | **Parcial** | `repo_auditado/src/modelo/dimensional.py` · `repo_auditado/scripts/sprint2_duckdb.py` · `repo_auditado/evidencias/duckdb_resumen_modelo.txt` · `datos_originales/reporte_ejecucion_51_poetry.csv` | El **diseño está completo y el script corre** (`sprint2_duckdb.py` → exit 0 en nuestra prueba con las versiones del lock). Dos matices verificados en §4.1: son **7 dimensiones + 1 hecho + 1 puente = 9 tablas** (no «9 dimensiones»), y el modelo poblado hoy tiene **3 convocatorias**, no las 6 de su evidencia |
| **OE5** Gran tabla + univariado, bivariado, multivariado y clustering | La gran tabla **versionada** (sin IDs) + resultados de los cuatro tipos de análisis **con su validación** (k elegido, silhouette) | **Parcial** | `repo_auditado/notebooks/tarea_gran_tabla/` · `documentacion_auditoria/latex/objetivo_4/secciones/03_estadistica.tex` · `documentacion_auditoria/data/memoria/dashboard_eda.html` (pestañas 1-2) | **Univariado y bivariado: cubiertos** por nuestro dashboard (17 gráficos). **Multivariado y clustering: no reproducibles** — el clustering es k-prototypes con k=3 fijo y sin validación, pierde el 8,4 % de la muestra, y los scripts son R legacy con rutas `Downloads/`. La gran tabla **no está versionada como dato** (§4.3) |

### 3.2 Preguntas de investigación

| Pregunta | Criterio de cumplimiento | ¿Cubierto? | Evidencia (ruta) | Comentarios |
|---|---|---|---|---|
| **Q1** Fiabilidad y comparabilidad | Informe de calidad con las anomalías **cuantificadas** y su efecto sobre la comparabilidad entre convocatorias | **Sí** | `datos_originales/ERRATA.md` (E1–E6) · `latex/objetivo_2/secciones/03_datos.tex` · `latex/objetivo_4/secciones/03_estadistica.tex` · `metodologia_muestreo.md` §2 · `analisis_longitudinal.md` §2.8 | Cobertura más completa de las siete. Nuestras erratas **corrigen** dos cifras del propio repositorio (22 vs 19 vs 10 atípicos; mojibake) y añaden un defecto que nadie había visto: el `poetry.lock` no correspondía a su `pyproject.toml` (E6) |
| **Q2** Retención y transiciones | Tasas de retención por par + matriz de transición + proporción que sube/baja/desaparece | **Sí** | `documentacion_auditoria/analisis_longitudinal.md` (§2.1-2.7) · `data/memoria/dashboard_eda.html` (pestaña 2) · `data/memoria/herramienta_trayectorias.html` · `data/memoria/longitudinal_resultados.json` · `latex/objetivo_4/secciones/03_estadistica.tex` | Es la pregunta que **mejor cubrimos**, y donde **colmanos la debilidad que nuestra propia auditoría señaló** (criterio 4: «matrices correctas pero sin inferencia»): añadimos intervalos de confianza, post-estratificación y GREG. Retención global 2013→2021 = **56,2 % censal** (56,6 % estimación MAS, n=618) |
| **Q3** Concentración territorial | Índice de concentración por convocatoria **+ comparación per cápita con población DANE 2018** por departamento | **Parcial** | `latex/objetivo_4/secciones/03_estadistica.tex` · `dashboard_eda.html` (pestaña 1 deptos., pestaña 2 retención por depto.) · `repo_auditado/evidencias/territorial_hhi_por_convocatoria.csv` · `evidencias/territorial_cuotas_departamento.csv` | La concentración **sí** está medida (HHI por convocatoria y cuotas por departamento) y la auditamos (correcta en concepto; sin IC bootstrap ni Gini/Theil). **La comparación per cápita con DANE 2018 no existe**: el HHI usa *cuotas de investigadores*, no investigadores por habitante. No hay ningún artefacto per cápita en el auditado ni en nuestro trabajo (§4.2) |
| **Q4** Paridad de género | % femenino por gran área OCDE y su evolución + brecha de género **en productividad** | **Parcial** | `metodologia_muestreo.md` §7.4 y §2 · `dashboard_eda.html` (u2, r3, v2) · `data/memoria/eda_resultados.json` (`genero_colapso`) · `repo_auditado/evidencias/genero_*.csv` · `evidencias/produccion_brecha_genero.csv` | Representación y retención por género: **cubiertas**, incluido el colapso de las categorías no representadas (9 personas en el censo, 0 en la muestra) y que el género explica solo el **0,11 %** de la varianza de la retención. **La réplica en productividad no está cubierta** (bloqueada por el dataset de producción, §4.4) y la «década» queda limitada a 3 convocatorias en el dato versionado |
| **Q5** Redes de co-filiación | Red con métricas (nodos, aristas, grado) + identificación de **instituciones-puente**, con su limitación de captura | **Parcial** | `latex/objetivo_4/secciones/03_estadistica.tex` · `latex/objetivo_3/secciones/03_codigo.tex` · `repo_mejorado` (los 2 scripts corren: `sprint3_redes.py` y `sprint3_grafo_interactivo.py` → exit 0) · `repo_auditado/hallazgos/sprint3_grafo_*.html` (498 y 146 nodos) | **Reproducimos y verificamos**, pero **no analizamos**: no hay modelos nulos, la red es un **corte transversal de 2019** (co-filiación capturada en 569 casos, según `README.md:61`) y no existe un criterio formal de «universidad-puente». Nuestro dashboard **no tiene sección de redes**. La pregunta queda respondida solo descriptivamente |
| **Q6** Diversidad poblacional | Comparación de la composición (etnia, discapacidad, víctimas) contra DANE/RUV con **razón de subrepresentación** | **Parcial** | `latex/objetivo_4/secciones/03_estadistica.tex` · `repo_mejorado/CHANGELOG.md` (sección E: comentario vs código) · `_archivo/scripts_oneoff/verificar_comparar_dane.py` · `repo_auditado/evidencias/diversidad_*.csv` | **Verificamos** que la evidencia del auditado es reproducible (afro **3,0×**, indígena **7,9×**, discapacidad **8,0×**, víctimas **8,6×**) y corregimos el comentario del código que inducía a un error grave. **No reanalizamos** con intervalos de confianza, y la cobertura de las tres variables es **0 % antes de 2021** (ocho años de diversidad invisible) |
| **Q7** Productividad y autoría | Cruce producción↔investigadores: productividad por categoría, autoría no reconocida, brecha de género en outputs | **No** | `latex/objetivo_3/secciones/03_codigo.tex` (fichas de `produccion.py` y `sprint5_*`) · `repo_mejorado/CHANGELOG.md` (sección C) · `datos_originales/reporte_ejecucion_51_poetry.csv` | **No es reproducible por nosotros**: `datos/raw/produccion_grupos.csv` (~1,2 GB) **no está versionado en ninguna parte** y no se puede descargar sin red. Los 3 scripts de producción salen con **código 3** por diseño, con aviso accionable. La evidencia del auditado existe (`evidencias/produccion_*.{csv,json}`: **8 archivos**) pero **no podemos recalcularla**. Es el hueco más grande del proyecto |

### 3.3 Recuento

| | Sí | Parcial | No |
|---|---:|---:|---:|
| Objetivos (general + 5 específicos) | **1** | **5** | 0 |
| Preguntas de investigación (7) | **2** | **4** | **1** |
| **Total (12 ítems)** | **3** | **9** | **1** |

Lectura del recuento: **el repositorio auditado cumplió razonablemente lo que se
propuso**. Nueve ítems parciales no son nueve incumplimientos: en la mayoría
nuestro trabajo **auditó bien un producto que existe**, y lo que falta es
**reproducibilidad** (datos no versionados) o **formalización estadística**
(inferencia), no el producto en sí. El único «No» es de acceso a datos, no de
trabajo no hecho.

---

## 4. Hallazgos verificados que cualifican el cumplimiento

### 4.1 El modelo estrella: dos precisiones que la documentación no hace

Inspeccionado el esquema real de `observatorio.duckdb` (2,90 MB) con DuckDB
(`_archivo/scripts_oneoff/inspeccionar_estrella.py`):

**a) No son «nueve dimensiones y una tabla de hechos». Son 9 tablas.**

| Tablas | Detalle |
|---|---|
| **7 dimensiones** | `dim_area` (215), `dim_categoria` (4), `dim_convocatoria` (**3**), `dim_formacion` (11), `dim_institucion` (2 619), `dim_investigador` (26 662), `dim_territorio` (227) |
| **1 tabla de hechos** | `fact_clasificacion` (**50 891** filas, 11 columnas) |
| **1 tabla puente** | `bridge_hecho_institucion` (47 187 filas, relación N:N) |

El propio docstring de `sprint2_duckdb.py` lista esas 9 tablas, así que **el
«nueve» del objetivo cuenta tablas, no dimensiones**. El diseño es correcto y la
integridad referencial la verifica el script; lo que conviene es **corregir el
enunciado** para que no prometa nueve dimensiones.

**b) El modelo poblado cubre 3 convocatorias, no 6.**

`dim_convocatoria` tiene **3 filas** y `fact_clasificacion` **50 891** hechos,
mientras la evidencia versionada del propio auditado
(`evidencias/duckdb_resumen_modelo.txt`) documenta **6 convocatorias y 77 237
registros** (8 016 + 8 280 + 10 050 + 13 001 + 16 796 + 21 094). La causa está
localizada: `sprint2_duckdb.py:28` construye el modelo con `cargar_consolidado()`,
que prefiere `datos/raw/investigadores_consolidado.csv` —**vacío, está
gitignored**— y cae al XLSX de `datos/tarea_join/`, que es el de 3 convocatorias.
Es el patrón de la ERRATA E2 aplicado al modelo dimensional: **la evidencia
versionada y el producto reproducible no coinciden**.

### 4.2 La comparación per cápita con DANE 2018 no existe en ningún artefacto

Q3 pide explícitamente «comparación per cápita con población DANE 2018». Lo que
hay es:

- `territorial_cuotas_departamento.csv`: **cuotas** de investigadores por
  departamento (Bogotá 0,312 en 2021, Antioquia 0,167…).
- `territorial_hhi_por_convocatoria.csv`: HHI de esas cuotas (0,190 en 2013 →
  0,153 en 2019).
- `diversidad_comparacion_dane.csv`: comparación con DANE 2018, pero de **grupos
  étnicos**, no de territorios.

Un HHI sobre cuotas de investigadores mide concentración **entre investigadores**,
no **respecto a la población**. Nadie ha dividido investigadores por habitantes
departamentales. Conclusión: la segunda mitad de Q3 quedó sin producir.

### 4.3 La «gran tabla» no está versionada y su generador no compila

`notebooks/tarea_gran_tabla/` contiene el generador
(`codigo_creacion_gran_tabla_a_partir_del_modelo_estrella.py`) y tres informes en
markdown (`informe_clusters.md`, `informe_multivariado.md`,
`analisis_Univariado.md`), pero **ningún artefacto de datos**: no hay
`gran_tabla.csv` ni equivalente versionado. Además, verificamos al ejecutar los 51
artefactos del inventario que ese script **no compila** (`SyntaxError` en la línea
157) y que el análisis multivariado y el clustering están en **R legacy** con
rutas `Downloads/`. Es decir: de OE5, la parte «multivariado y clustering» **no es
reproducible hoy por nadie**, ni por el propio repositorio.

### 4.4 El bloqueo de Q7 y de la mitad de Q4 es el mismo

Los tres scripts de producción salen con **código 3** porque falta
`datos/raw/produccion_grupos.csv` (~1,2 GB, 3,2 M de filas, Socrata `33dq-ab5a`).
Ese único archivo bloquea:

- **Q7** completa (quién firma, Sénior vs Junior, brecha de género en outputs);
- la parte de **Q4** sobre si la brecha de representación «se replica en
  productividad»;
- **OE4** en su parte de producción (`sprint5_duckdb.py`: `fact_produccion`).

Es el desbloqueante de mayor rendimiento de la Fase 2.

### 4.5 Otras inconsistencias internas del auditado (contexto, no obstáculo)

- **7 preguntas en el README frente a 6 en el informe** (§1), con la pregunta de
  redes omitida en el informe pese a tener sección propia.
- **«Doce hallazgos»** dice el informe (`informe_final.tex:188`), la tabla del
  README lista **14**, y el README describe `docs/manual.ipynb` como «notebook
  ejecutable con los **15** hallazgos» (`README.md:122`).
- Estas inconsistencias no afectan al cumplimiento de los objetivos, pero sí a la
  **auditabilidad** de la entrega, que es justo lo que pide Q1.

---

## 5. Lo que NO está cubierto y deberíamos completar en la Fase 2

Ordenado por rendimiento sobre el cumplimiento, no por dificultad.

### Bloqueantes (sin esto no se puede cerrar el objetivo)

| # | Qué falta | Qué completaría el cumplimiento | Por qué primero |
|---|---|---|---|
| **F2-1** | **Q7 completa** y la mitad de Q4: productividad, autoría y brecha de género en outputs | Obtener `produccion_grupos.csv` (Socrata `33dq-ab5a`, 3,2 M filas) **o** acordar y documentar una alternativa: validar la evidencia versionada del auditado contra una muestra del dataset, o declarar Q7 fuera de alcance con su motivo | Un solo archivo desbloquea 1 pregunta entera, media pregunta más y la tabla de hechos de producción |
| **F2-2** | **Q3 per cápita**: comparación con población DANE 2018 por departamento | Descargar población DANE 2018 por departamento (censo) y calcular **investigadores por 100 000 habitantes**, con **IC bootstrap** y **Gini/Theil** además del HHI | Nunca se produjo; es el criterio literal de la pregunta. Añadir IC y Gini/Theil cubre de paso la debilidad que señaló nuestro criterio 4(b) |
| **F2-3** | **Modelo estrella reproducible**: hoy se reconstruye con 3 convocatorias y su evidencia dice 6 | Versionar el insumo que permite reconstruirlo con las 6 convocatorias (o un script que lo descargue y valide), y **corregir el enunciado** de «nueve dimensiones» a «7 dimensiones + 1 hecho + 1 puente» | Sin esto, `sprint2_duckdb.py` corre pero produce un modelo que **no coincide con su propia evidencia** |

### Análisis que faltan (método ya disponible en el proyecto)

| # | Qué falta | Qué completaría el cumplimiento |
|---|---|---|
| **F2-4** | **Q5 redes**: no hay análisis propio ni criterio de «universidad-puente» | Modelo nulo / bootstrap sobre la red de 2019, grado y centralidad con su incertidumbre, y un criterio explícito de puente. Declarar la limitación de captura (co-filiación solo en 2019: 569 pares) y decidir si se añade una pestaña al dashboard |
| **F2-5** | **Q6 diversidad**: verificación sin reanálisis | Recalcular las razones de subrepresentación con **IC**, corregir el denominador documentado, y mostrar la **cobertura por convocatoria** (0 % antes de 2021). Añadir las tres variables al dashboard, que hoy no las muestra |
| **F2-6** | **OE5 multivariado y clustering** | Formalizar el k-prototypes: elegir **k** con silhouette / Calinski-Harabasz, reportar la pérdida del 8,4 % y validar la estabilidad. O declarar el clustering fuera de alcance con su justificación, en vez de dejarlo en R legacy |
| **F2-7** | **OE3 unicidad de IDs** | Formalizar la heurística (±4 años, género) en un informe: duplicados detectados, umbral justificado y **tasa de falsos positivos**. Hoy es «razonable sin formalizar» |
| **F2-8** | **OE1 descriptivos por convocatoria** | Añadir una pestaña de descriptivos **por convocatoria** al dashboard. Nuestro EDA es por persona en su última convocatoria: mismo terreno, otro diseño |
| **F2-9** | **Inferencia en las demás preguntas** | Nuestra inferencia (MAS + post-estratificación + GREG) cubre hoy **retención y edad**. Extenderla a territorial, género y diversidad es exactamente la debilidad que nuestro criterio 4 identificó como principal en el auditado |
| **F2-10** | **Supervivencia** | Kaplan-Meier / Cox para el tiempo hasta la salida del padrón, señalado por nuestro criterio 4(a) y no cubierto por las matrices de Markov |

### Recomendación de secuencia

1. **F2-1** (desbloqueante de datos) — es el que más cumplimiento mueve.
2. **F2-2** y **F2-3** — cierran dos criterios literales de objetivos/preguntas.
3. **F2-4, F2-5, F2-9** — reutilizan la maquinaria de inferencia que ya tenemos.
4. **F2-6 a F2-8, F2-10** — formalización y alcance, ya sin bloqueos.

---

## 6. Conclusión

De los **12 ítems** evaluados (objetivo general + 5 específicos + 7 preguntas),
**3 están cubiertos, 9 parcialmente y 1 no está cubierto**.

El diagnóstico no es que el repositorio auditado incumpliera: **cumplió lo que se
propuso**, y lo que falta es mayoritariamente **reproducibilidad** (datos pesados
no versionados, evidencia que no coincide con el producto reconstruible) y
**formalización estadística** (inferencia, validación de clustering, criterios de
unicidad de IDs y de red). El único «No» —productividad— es un problema de acceso
a un archivo de 1,2 GB, no de trabajo no realizado.

La Fase 2 tiene por delante 10 frentes, de los cuales **tres son desbloqueantes** y
el resto reutiliza métodos que el proyecto ya tiene construidos y verificados.

---

### Archivos citados en este documento

| Ruta | Qué es |
|---|---|
| `datos_originales/repo_auditado/` | Los 236 archivos del commit `1528939` (evidencia, inmutable) |
| `datos_originales/ERRATA.md` | Las 6 contradicciones conocidas del auditado (E1–E6) |
| `datos_originales/repo_mejorado/CHANGELOG.md` | Los 30 arreglos aplicados, con su verificación |
| `documentacion_auditoria/analisis_longitudinal.md` | Panel, retención, transiciones y validación del muestreo |
| `documentacion_auditoria/metodologia_muestreo.md` | EDA, MAS, post-estratificación, GREG y diagnósticos |
| `documentacion_auditoria/data/memoria/dashboard_eda.html` | Los 17 gráficos del EDA en 4 pestañas |
| `documentacion_auditoria/data/memoria/herramienta_trayectorias.html` | Visor interactivo del panel |
| `documentacion_auditoria/latex/objetivo_*/secciones/03_*.tex` | Los 6 criterios de auditoría |
| `datos_originales/reporte_ejecucion_51_poetry.csv` | Ejecución real de los 51 artefactos con las versiones del lock |
| `_archivo/scripts_oneoff/inspeccionar_estrella.py` | Inspección del esquema del modelo estrella (§4.1) |
