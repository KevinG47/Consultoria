# Informe de Consultoría Estadística — Observatorio MinCiencias (Investigadores Reconocidos)

**Documento:** Primera versión — Documentación técnica y propuesta metodológica
**Proyecto auditado:** [`Observatorio_Ministerio_de_Ciencias_Grupo8`](https://github.com/ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8)
**Contexto:** Consultoría universitaria — Ustadistica · Universidad Santo Tomás · 2026-I
**Rol:** Consultor Estadístico Senior · Auditoría de Proyectos de Datos
**Fecha de auditoría:** Revisión integral del repositorio (236 archivos; clonado y analizado en su totalidad)

---

## 1. Diagnóstico Descriptivo y Exploratorio del Repositorio

### 1.1 Identificación del proyecto y tema central

El repositorio materializa un **observatorio crítico del sistema de reconocimiento de investigadores del Ministerio de Ciencia, Tecnología e Innovación de Colombia (MinCiencias)**. El tema central detectado es la **evaluación estadística de la calidad, comparabilidad y equidad de un registro administrativo oficial de capital humano científico** (el padrón de investigadores reconocidos por convocatoria), complementado con el cruce de **productividad científica declarada** (producción de grupos de investigación).

Sus preguntas de investigación (documentadas en el README) orbitan en torno a seis ejes analíticos:

- **Fiabilidad de la fuente** — ¿la información publicada por MinCiencias es comparable entre convocatorias?
- **Dinámica longitudinal** — ¿el sistema retiene investigadores entre convocatorias (sube/baja/desaparece)?
- **Concentración territorial** — ¿la capacidad investigativa está distribuida de manera equitativa?
- **Brecha de género** — paridad por gran área OCDE y su evolución en una década.
- **Redes institucionales** — conexión de instituciones vía doble afiliación (universidades-puente).
- **Diversidad e inclusión** — representación étnica, discapacidad y víctimas del conflicto frente al censo poblacional.
- **Productividad cruzada** — quién firma realmente la producción que el sistema mide y cómo se distribuye por categoría, género y territorio.

### 1.2 Inventario de la estructura de carpetas

| Ruta | Contenido | Observación de auditoría |
|---|---|---|
| `src/ingesta/` | Descarga desde API Socrata (`sodapy`): `minciencias.py` (padrón) y `produccion.py` (~1.2 GB paginado) | Correcto; separa fuentes |
| `src/Transformacion.py` | Pipeline de limpieza: normalización de texto, parseo de años, estandarización de género, imputación de mediana | Centraliza transformaciones |
| `src/analisis/` | 7 módulos reutilizables: `longitudinal`, `territorial`, `genero`, `redes`, `diversidad`, `produccion`, `calidad` | Buena modularización funcional |
| `src/modelo/dimensional.py` | Esquema estrella en DuckDB: 7 dimensiones + `fact_clasificacion` + tabla puente N:N de instituciones | Kimball aplicado |
| `scripts/` | 17 orquestadores por *sprint* (sprint2–sprint6) | Patrón de ejecución reproducible |
| `notebooks/` | `01_eda.ipynb` (EDA activo, 16 celdas) + carpetas legacy `tarea_*` (código R/Python histórico) | Zona legacy sin limpiar |
| `datos/` | `catalogo.yaml` (metadatos + diccionario), `tarea_join/` (consolidado CSV+XLSX versionado), `raw/` y `processed/` (gitignored) | Catálogo excelente; versionado de datos incompleto |
| `evidencias/` | 79 CSVs de resultados exportados por sprint | Evidencia trazable |
| `artifacts/` | 56 PNG + HTML por sprint (figuras, Sankeys, mapas) | Trazable |
| `hallazgos/` | 2 HTML interactivos de grafos Pyvis | Entregable parcial |
| `docs/` | Informe LaTeX (~30 pág.), presentación Reveal.js (18 slides), `manual.ipynb` (49 celdas) | Documentación sólida |
| `app/` + `streamlit_app.py` (raíz) | Dashboard duplicado: el de la raíz es el real (7 tabs); `app/streamlit_app.py` es un *placeholder* "en construcción" | **Inconsistencia detectada** (ver §1.6) |
| `.github/workflows/` | `etl_update.yml` — ingesta mensual automatizada | **CI referenciando módulos inexistentes** (ver §1.6) |
| `tests/` | 1 test trivial (existencia del catálogo) | Cobertura insuficiente |
| `models/` | Vacío (solo `.gitkeep`) | Componente ML pendiente |

### 1.3 Inventario de código fuente y datos

**Lenguajes y cómputo analítico**

| Tipo | Cantidad | Detalle |
|---|---|---|
| Python (`.py`) | 40 | 26 de producción (src/scripts), 14 auxiliares/tests |
| R (`.R`) | 6 | Legacy en `notebooks/tarea_*` (EDA, MCA, clustering k-prototypes) |
| Notebooks (`.ipynb`) | 5 | 1 activo (EDA) + 4 legacy |
| SQL (embebido) | — | Consultas DuckDB dentro de `dimensional.py` y scripts |

**Datos (79 CSV + 1 XLSX + catálogo YAML)**

| Dataset | Registros | Llave | Rol |
|---|---|---|---|
| Padrón de investigadores reconocidos (`bqtm-4y2h`, 6 convocatorias 2013–2021) | 77.237 filas · 30.086 investigadores únicos · 30 variables | `id_persona_pr` | Fuente primaria |
| Producción de grupos (`33dq-ab5a`) | 3.166.629 filas producto-autor · 77.401 autores únicos | `id_persona_pd ↔ id_persona_pr` (+ `id_convocatoria`) | Cruce de productividad |
| 79 CSV de evidencias | Resultados agregados (matrices de transición, HHI, brechas, cobertura, tabla maestra IES, etc.) | — | Salidas de los análisis |
| `investigadores_consolidado.xlsx/.csv` | 77.237 × 30 | versionado en git (12 MB) | Base analítica canónica |

**Hallazgo de calidad detectado durante la auditoría:** el CSV versionado presenta **problemas de codificación (mojibake)** — p. ej. `FÃ­sica` (debería ser *Física*), `SÃ©nior`, `BogotÃ¡` — indicativo de un desajuste UTF-8/Latin-1 en la cadena de descarga Socrata→CSV. El XLSX no se ve afectado, lo que sugiere que el defecto se introdujo en la exportación a texto. Este punto debe documentarse y corregirse en el pipeline (ver §4).

### 1.4 Arquitectura de datos y pipeline de procesamiento

El flujo implementado sigue un esquema **medallón ligero** (raw → processed → analítico) bajo el ciclo CRISP-DM:

```
[Socrata datos.gov.co]
   │  sodapy (paginado)
   ▼
datos/raw/  (gitignored; ~1.2 GB producción)        ── INGESTA
   │
   ▼
src/Transformacion.py  (limpiar_texto → parsear_ano →
   │                    estandarizar_genero → tratar_faltantes)  ── TRANSFORMACIÓN
   ▼
datos/tarea_join/investigadores_consolidado.{csv,xlsx}  (canónico, versionado)
   │
   ├─► src/modelo/dimensional.py → datos/processed/observatorio.duckdb
   │        (dim_convocatoria, dim_investigador, dim_categoria, dim_area,
   │         dim_territorio, dim_formacion, dim_institucion,
   │         fact_clasificacion, bridge_hecho_institucion)
   │
   └─► scripts/sprint{2..6}_*.py  ──► artifacts/*.png|html  +  evidencias/*.csv
   │
   ▼
streamlit_app.py  (dashboard 7 tabs)  ·  docs/informe/informe_final.tex  ·  docs/manual.ipynb
```

**Decisiones metodológicas documentadas en el código** (correctas en términos de auditoría):
- **Atípicos de edad:** 22 casos con `edad > 100` (máx. 956); se adoptó *eliminación* frente a *imputación por mediana del grupo* (gran área, categoría, género), con justificación explícita y reproducible (`src/analisis/calidad.py`).
- **Categorías:** normalización a 4 niveles ordinales (Junior=1 … Emérito=4) para permitir matrices de transición.
- **Faltantes:** imputación por mediana en numéricas; etiqueta explícita `NO REPORTADO` en categóricas (trazable).
- **Modelo dimensional:** esquema estrella (Kimball) con tabla puente para la relación N:N investigador↔institución (`inst_filia` separado por `|`).

### 1.5 Librerías principales

| Capa | Python | R (legacy) |
|---|---|---|
| Ingesta | sodapy, pandas, requests | readxl |
| Almacén | duckdb (modelo estrella) | — |
| Análisis | pandas, numpy, scikit-learn, statsmodels | FactoMineR, clustMixType, klaR, mice |
| Visualización | matplotlib, seaborn, plotly, folium | ggplot2, factoextra, ggrepel |
| Redes | networkx, pyvis | — |
| Dashboard | streamlit | — |
| Reproducibilidad | poetry, docker, GitHub Actions | — |
| Testing | pytest, ruff, pandera (declaradas en dev) | — |

**Observación:** `pandera` figura en dependencias dev pero no se utiliza en el código auditado; el testeo efectivo se limita a 1 caso. El clustering (k-prototypes) vive en scripts R legacy con rutas *hardcodeadas* (`Downloads/...`), por lo que **no es reproducible** desde el repositorio.

### 1.6 Estado del proyecto y hallazgos preliminares de la auditoría

**Estado general: maduro pero con deuda técnica localizada.** El cronograma CRISP-DM reporta Sprints 2–6 completados, 14 hallazgos críticos documentados (concentración territorial 51% Bogotá+Antioquia; brechas de género 24% mujeres en Ingeniería vs 48% en ciencias médicas; co-filiación solo capturada en 2019; 0% cobertura de etnia/discapacidad/conflicto antes de 2021; subrepresentación afro 3×, indígena 7.9×, discapacidad 8× vs DANE; 36.9% de autores en producción reconocidos en el padrón; productividad media por categoría Junior 30 / Asociado 65 / Senior 121; eméritos vitalicios), dashboard funcional e informe LaTeX consolidado.

**Fortalezas verificadas**

- Documentación de nivel profesional: README exhaustivo, catálogo YAML con diccionario de datos y llaves de cruce, decisiones metodológicas documentadas *en el propio código*.
- Reproducibilidad declarada: `poetry.lock`, Dockerfile, semillas (`set.seed(123)`), scripts de orquestación por sprint.
- Separación clara ingesta/transformación/análisis/modelado con lógica reutilizable en `src/`.
- Evidencias numerosas y trazables (79 CSVs) con convención de nombres consistente.

**Brechas y riesgos de la auditoría (evidencia directa en el repositorio)**

1. **CI/CD rota:** `.github/workflows/etl_update.yml` ejecuta `python -m src.ingesta.main` y `python -m src.transformacion.main`, módulos que **no existen** (los reales son `src.ingesta.minciencias`/`src.ingesta.produccion` y `src/Transformacion.py`). El job de actualización mensual fallaría en el primer paso.
2. **Deploy desalineado:** el Dockerfile ejecuta `app/streamlit_app.py`, que es un *placeholder* ("Dashboard en construcción"); el dashboard real es `streamlit_app.py` de la raíz. El contenedor desplegaría una app vacía.
3. **Versionado de datos incompleto:** `datos/raw` y `datos/processed` están gitignored y la nota del `.gitignore` sugiere DVC, pero no hay configuración DVC ni artefactos de datos en el repositorio; la reproducibilidad de la ingesta depende de la disponibilidad de la API.
4. **Calidad de codificación:** mojibake en el CSV canónico versionado (§1.3).
5. **Testing insuficiente:** 1 test funcional; `pandera` declarado y no usado; sin tests de contrato de datos ni de las funciones de análisis.
6. **Legacy no reproducible:** notebooks R con rutas absolutas de usuario (`Downloads/...`); entradas (Excel de gran tabla) no versionadas ni enlazadas.
7. **Duplicidad de artefactos:** múltiples variantes de matrices de transición (`matriz_*`, `matriz_*_ext`, `matriz_*_obs`) sin documentación de diferencias.
8. **Componente ML vacío:** `models/` sin contenido pese a declararse scikit-learn; la segmentación se ejecutó en R legacy, no en el pipeline principal.
9. **Inconsistencia documental menor:** el número de atípicos de edad aparece como 10 en el docstring de `calidad.py` y como 22 en el README/hallazgo 7 (el conteo real reportado en evidencias es 22).
10. **Desactualización de referencias internas:** README menciona el repo `Victor-Diaz-Usta/Min_ciencias`, rama `main_VictorD` y el nombre "Grupo7" en varias secciones, mientras el repositorio actual es Grupo8 — nomenclatura por unificar.

---

## 2. Estado del Arte y Marco Metodológico

El tema central del repositorio — **evaluación cuantitativa crítica de un sistema nacional de reconocimiento científico** — se inserta hoy en el paradigma de la **Ciencia de la Ciencia (Science of Science, SciSci)**, que estudia el sistema científico como objeto empírico mediante datos masivos y métodos cuantitativos. A continuación se sintetiza el estado del arte por eje metodológico, con las técnicas y métricas estándar recomendadas por la literatura.

### 2.1 Ciencia de la Ciencia (SciSci) como marco paradigmático

La revisión fundacional de [Fortunato et al. (2018), *Science*](https://www.sciencemagazinedigital.org/sciencemagazine/02_march_2018?pg=58) consolidó la SciSci como disciplina: combina **datos administrativos y bibliométricos a gran escala** con **física estadística, ciencia de redes y ML** para caracterizar la producción, la colaboración, la movilidad y la desigualdad del conocimiento. El enfoque del repositorio (observatorio sobre registro administrativo oficial) es un caso de aplicación directa de este paradigma, alineado también con la síntesis de Zeng et al. (2021, *Physics Reports*) sobre el análisis del sistema científico desde los sistemas complejos, y con la perspectiva de predicción basada en datos de Clauset, Larremore y Sinatra (2017, *Science*).

**Implicación metodológica:** el proyecto debe adoptar formalmente este marco: cada hallazgo debe asociarse a una *pregunta de sistema* (estructura, dinámica, desigualdad), no solo a un cruce descriptivo de variables.

### 2.2 Bibliometría y evaluación responsable

- **Métricas de impacto y productividad:** el índice h ([Hirsch, 2005, PNAS](https://www.pnas.org/doi/10.1073/pnas.0507655102)) y sus variantes normalizadas (h por carrera, por área, por autor) siguen siendo el estándar descriptivo; en el repositorio, la productividad se mide como *conteo de productos por investigador* — equivalente a un indicador de output bruto que la literatura recomienda normalizar por disciplina y ventana.
- **Leyes bibliométricas clásicas:** la ley de Lotka (1926) —concentración de la producción en una minoría de autores— y las leyes de Bradford/Zipf son los marcos nulos estándar para testar si la concentración observada (p. ej., productividad Senior vs Junior) difiere de la esperada por azar.
- **Evaluación responsable:** los **Principios de Leiden** ([Hicks et al., 2015, *Nature*](https://www.nature.com/articles/520429a)) y la **Declaración DORA** recomiendan: (i) indicadores cuantitativos *de apoyo*, nunca sustitutivos del juicio; (ii) medición robusta al contexto de campo; (iii) transparencia de definiciones y límites. El repositorio ya incorpora este espíritu crítico (patrón *Pregunta → Hallazgo → Caveat*), lo cual debe formalizarse como principio rector de la consultoría.

### 2.3 Métodos longitudinales y de transición de estado

El análisis de trayectorias de carrera es una línea activa (["Researchers' career transitions over the life cycle", *Scientometrics* 2016](https://rd.springer.com/article/10.1007/s11192-016-2131-y)):

- **Matrices de transición de Markov** (Kemeny & Snell, 1976): modelan la probabilidad de pasar de una categoría a otra entre convocatorias; el repositorio ya las implementa (5 pares de periodos) y constituye el núcleo longitudinal.
- **Modelos de supervivencia** (Kaplan–Meier, riesgos proporcionales de Cox): recomendados para cuantificar *tiempo hasta salida* del sistema (abandono) y su asociación con covariables (área, género, región, categoría) — complemento natural y no explotado aún del panel existente.
- **Modelos de crecimiento (mixed-effects / GEE):** para trayectorias individuales de productividad/categoría con datos panel desbalanceados.
- **Advertencias de la literatura:** los paneles administrativos sufren **censura, atrición selectiva y cohortes de entrada heterogéneas**; la propiedad markoviana (la transición depende solo del estado actual) rara vez se cumple en carreras científicas, por lo que se recomienda testearla y reportar matrices *condicionadas a historia* o modelos de orden superior.

### 2.4 Medición de concentración y desigualdad

Para el eje territorial el estándar es la familia de índices de desigualdad/concentración:

- **HHI (Herfindahl–Hirschman)** — ya implementado por el repositorio para departamentos y regiones; la literatura de economía regional recomienda acompañarlo de intervalos de confianza por bootstrap.
- **Gini y Lorenz** — miden desigualdad de la distribución completa (no solo cola); el paquete R [REAT](https://search.r-project.org/CRAN/refmans/REAT/html/REAT-package.html) los implementa junto con HHI y es la referencia para replicar y ampliar el análisis territorial.
- **Theil (1967) y entropía de Shannon** — descomponibles por grupos (entre-regiones vs intra-regiones), ideales para atribuir la concentración a componentes estructurales.
- **Per cápita** (vs población DANE 2018) — ya presente; la literatura de sistemas de innovación regional recomienda controles por tamaño poblacional y PIB regional.

### 2.5 Género y diversidad en la ciencia

- **Brechas globales:** el estudio canónico de [Larivière et al. (2013), *Nature*](https://www.nature.com/articles/504211a) documentó la subrepresentación femenina persistente y su variación por disciplina — la métrica estándar es la **proporción de participación por disciplina** y la **brecha relativa (odds ratio)** entre áreas.
- **Contexto regional:** [“Women in Latin American science: gender parity in the twenty-first century and prospects for a post-war Colombia” (2019)](https://www.tandfonline.com/doi/pdf/10.1080/25729861.2019.1621538) aporta evidencia específica de paridad de género en ciencia latinoamericana y colombiana, directamente relevante para interpretar los hallazgos del repositorio (24% mujeres en Ingeniería vs 48% en ciencias médicas).
- **Interseccionalidad** (Crenshaw, 1989): la literatura recomienda cruces género × etnia × territorio (el repositorio ya produce `diversidad_interseccional_genero_etnia.csv`), y el uso de **índices de representación relativa** (razón observado/esperado frente al censo) para cuantificar sub/sobrerrepresentación (afro 3×, indígena 7.9×, discapacidad 8×, raizales 3–6×).
- **Caveat metodológico:** estas variables son **auto-declaradas** y solo se capturan desde 2021 en el dataset; cualquier inferencia temporal debe limitarse a cortes transversales y reportarse como limitación.

### 2.6 Análisis de redes de colaboración y co-afiliación

- **Fundamentos:** redes de coautoría ([Newman, 2001](https://arxiv.org/abs/cond-mat/0106144)) y de co-filiación; métricas estándar de centralidad — grado, intermediación ([Freeman, 1977](https://www.jstor.org/stable/3033543)) y PageRank — para identificar instituciones-puente y jerarquías.
- **Desigualdad estructural:** [Clauset, Arbesman y Larremore (2015), *Science Advances*](https://www.science.org/doi/10.1126/sciadv.1400005) demostraron con redes de contratación de profesores que las jerarquías institucionales persisten décadas tras controlar por productividad — marco teórico directo para el hallazgo de Bogotá que "retiene 92% y absorbe 1.000+ investigadores".
- **Inferencia en redes:** la literatura recomienda contrastar las métricas observadas contra **modelos nulos** (grafos aleatorios con la misma distribución de grados, p. ej. configuración) para evitar atribuir significancia a ruido; también reportar métricas por convocatoria (ya implementado en `redes_metricas_por_convocatoria.csv`) y **declarar explícitamente los artefactos de captura** — en este proyecto, la co-filiación solo se capturó en 2019 (569 casos), por lo que la red es un corte transversal, no una serie.

### 2.7 Aprendizaje no supervisado con datos mixtos

Los datos del padrón mezclan variables categóricas (área OCDE, género, región, formación) y numéricas (edad, órdenes), lo que define el problema como **clustering de datos mixtos**:

- **Análisis factorial de datos mixtos (FAMD)** ([Husson, Lê & Pagès, 2017](https://www.crcpress.com/Exploratory-Multivariate-Analysis-by-Example-Using-R/Husson-Le-Pages/p/book/9781138196346)) y **MCA** ([Greenacre, 2017](https://www.crcpress.com/Correspondence-Analysis-in-Practice-Third-Edition/Greenacre/p/book/9781138700681)) son el estándar de reducción de dimensión previa; el repositorio ya usa CA/MCA en R legacy.
- **k-prototypes** ([Huang, 1998](https://link.springer.com/article/10.1023/A:1009769707641)) — el método implementado — y su validación: la literatura de *benchmarking* de particionamiento para datos mixtos ([arXiv:2203.16287](https://ar5iv.labs.arxiv.org/html/2203.16287)) recomienda reportar **silhouette, Calinski–Harabasz y Davies–Bouldin**, y comparar al menos dos algoritmos (p. ej., k-prototypes vs k-means sobre codificación one-hot/Gower).
- **Imputación múltiple** (paquete `mice`, ya importado en R) antes del clustering cuando el análisis de casos completos descarta >8% de la muestra (en el script legacy se pierde 8.4%).
- **Futuro del repositorio:** la transición de este bloque a scikit-learn (declarado en `pyproject.toml` pero no utilizado) con pipeline en `src/` cerraría la brecha de reproducibilidad (§1.6).

### 2.8 Calidad de datos y gobernanza

El núcleo de la consultoría es, en realidad, una **auditoría de calidad de datos**:

- **Dimensiones de calidad:** el marco canónico de [Wang & Strong (1996)](https://www.researchgate.net/publication/220591451_Beyond_Accuracy_What_Data_Quality_Means_to_Data_Consumers) — exactitud, completitud, consistencia, oportunidad, unicidad, validez — y su operacionalización en estándares (ISO/IEC 25012; DAMA-DMBOK, 2017). El repositorio ya cubre completitud (heatmaps de cobertura), unicidad (verificación de IDs por coherencia de edad) y validez (atípicos); faltan formalizar exactitud (cruce con fuentes oficiales) y consistencia (encodings, etiquetas).
- **FAIR:** los [principios FAIR](https://www.nature.com/articles/sdata201618) (Wilkinson et al., 2016) son el estándar para datos de investigación: *Findable, Accessible, Interoperable, Reusable*. El catálogo YAML y el diccionario de datos del repositorio son un buen punto de partida; la trazabilidad de transformaciones (data lineage) debe documentarse por escrito (los scripts ya la materializan).
- **Validación automatizada:** herramientas de perfilado y contrato de datos (pandera, great_expectations) — declarada `pandera` pero no usada — son la práctica recomendada para garantizar contratos de esquema entre ingesta y análisis.

### 2.9 Arquitectura analítica de referencia

- **Modelado dimensional (Kimball & Ross, 2013):** el esquema estrella implementado en DuckDB es la arquitectura estándar para observatorios (dimensiones + hechos + tablas puente N:N) y es correcta para el caso.
- **Reproducibilidad:** Poetry + Docker + CI/CD (práctica consolidada); la automatización mensual de ingesta (GitHub Actions) es exactamente lo que la gobernanza de datos recomienda, *si se corrige* la referencia a módulos inexistentes.
- **Escalabilidad:** DuckDB + pandas cubren el volumen actual (77k–3.2M filas); si el observatorio creciera a series más largas o datos a nivel de producto con análisis de texto (títulos, tipologías), la literatura sugeriría mover cómputos a PySpark/ray o Dask — no necesario hoy, pero debe declararse en el plan de evolución.

### 2.10 Síntesis: matriz de técnicas recomendadas

| Pregunta de investigación | Técnica estándar | Estado en el repo | Acción recomendada |
|---|---|---|---|
| ¿Los datos son fiables/comparables? | Perfilado DQ + dimensiones Wang & Strong + FAIR | Parcial (completitud/validez) | Formalizar auditoría DQ integral |
| ¿El sistema retiene investigadores? | Matrices de transición + supervivencia (KM/Cox) | Matrices ✅ | Añadir KM/Cox y test de markovianidad |
| ¿Hay concentración territorial? | HHI + Gini/Lorenz + Theil + bootstrap | HHI ✅ | Ampliar familia de índices + IC |
| ¿Brecha de género/diversidad? | Proporciones, odds ratios, representación relativa vs DANE | ✅ | Formalizar inferencia (IC) y caveats |
| ¿Cómo se conectan las instituciones? | Redes + centralidad + modelos nulos | Parcial (grafo) | Modelos nulos de significancia |
| ¿Quién produce? | Ley de Lotka, productividad normalizada | Parcial | Testar concentración vs ley nula |
| ¿Perfiles homogéneos? | FAMD/MCA + k-prototypes + validación | R legacy | Migrar a pipeline Python validado |
| Gobernanza general | Contratos de datos, CI/CD, lineage | Débil | Corregir CI, tests, versionado |

---

## 3. Definición del Proyecto de Consultoría

### 3.1 Objetivo general

> **Diseñar e implementar una auditoría estadística integral y reproducible del sistema de reconocimiento de investigadores de MinCiencias (convocatorias 2013–2021), que evalúe con métodos de la Ciencia de la Ciencia la fiabilidad, comparabilidad y equidad del padrón oficial — incluyendo su cruce con la productividad declarada de grupos — y que entregue un sistema de indicadores críticos, un dashboard de auditoría y documentación metodológica formal, listos para integrarse al informe institucional del observatorio.**

El objetivo se enmarca explícitamente en la evaluación responsable (Principios de Leiden/DORA): los indicadores se entregan como *evidencia de apoyo al juicio*, con definiciones operativas, supuestos y limitaciones declaradas.

### 3.2 Objetivos específicos secuenciales

**OE1 — Exploración, auditoría de calidad y consolidación de datos (Fase I: fundamentos).**
- Realizar un perfilado completo del padrón (30 variables × 6 convocatorias) y de la producción (3.2M filas) según las dimensiones de calidad de Wang & Strong (exactitud, completitud, consistencia, unicidad, validez, oportunidad).
- Corregir y documentar los problemas detectados en la auditoría: mojibake de codificación, inconsistencia de atípicos de edad (10 vs 22), duplicidad de evidencias, y estandarización de `inst_filia` mediante la tabla maestra IES (211 IES, 91% de cobertura).
- Entregables: (i) informe de auditoría de calidad con métricas por convocatoria; (ii) dataset consolidado v2 con codificación UTF-8 normalizada y diccionario de datos actualizado; (iii) contrato de esquema automatizado (pandera) para ingesta y análisis.

**OE2 — Modelado estadístico e inferencia analítica (Fase II: análisis).**
- Ampliar el modelo longitudinal: matrices de transición de Markov (ya existentes) complementadas con **modelos de supervivencia** (Kaplan–Meier y Cox) para retención/abandono, y test de la propiedad markoviana.
- Robustecer la medición de desigualdad: familia HHI–Gini–Theil con intervalos de confianza bootstrap, y test de concentración de productividad contra la ley de Lotka.
- Formalizar la inferencia de brechas (género, etnia, discapacidad) con modelos logísticos ajustados por área OCDE y cohorte, e indicadores de representación relativa con IC.
- Validar la significancia de las métricas de red (centralidad, puentes) contra modelos nulos, y migrar la segmentación (FAMD + k-prototypes) al pipeline Python con validación interna de clusters.
- Entregables: (i) paquete de indicadores reproducible (`src/analisis/` ampliado) con salidas en `evidencias/`; (ii) figuras y tablas de inferencia para el informe; (iii) documento metodológico de supuestos y validaciones.

**OE3 — Implementación, despliegue y documentación de resultados (Fase III: entrega).**
- Consolidar el dashboard de auditoría Streamlit (7 tabs tipo capítulo) con las nuevas métricas e indicadores de incertidumbre.
- Reparar la cadena de reproducibilidad: corregir GitHub Actions (módulos reales), alinear el Dockerfile con la app real, completar tests unitarios de las funciones analíticas y versionar datos críticos.
- Publicar el informe técnico final (LaTeX) y la documentación FAIR del dataset (catálogo actualizado, lineage de transformaciones, guía de reproducción end-to-end).
- Entregables: (i) dashboard desplegable; (ii) repositorio con CI verde y tests; (iii) informe final de consultoría listo para revisión del director y para incorporación a la entrega universitaria.

### 3.3 Fases, cronograma indicativo y productos

| Fase | Objetivo | Semanas | Productos clave |
|---|---|---|---|
| I. Fundamentos y calidad | OE1 | 1–3 | Auditoría DQ, dataset v2, contrato de datos |
| II. Modelado e inferencia | OE2 | 4–8 | Indicadores ampliados, supervivencia, índices con IC, redes validadas, clusters migrados |
| III. Implementación y entrega | OE3 | 9–12 | Dashboard, CI verde, informe final, documentación FAIR |

---

## 4. Alcance y Limitaciones

### 4.1 Alcance del análisis técnico

**Incluye (lo que se entregará):**
- Auditoría de calidad de datos del padrón de investigadores (2013–2021) y del dataset de producción, con las 6 dimensiones de calidad y su reporte por convocatoria.
- Sistema de indicadores críticos: longitudinales (retención, transición, supervivencia), territoriales (HHI/Gini/Theil per cápita), de género/diversidad (representación relativa con IC) y de productividad cruzada (cobertura, brechas, concentración vs Ley de Lotka).
- Red de co-filiación institucional con métricas de centralidad validadas contra modelos nulos.
- Segmentación de perfiles de investigación (FAMD/k-prototypes) reproducible en Python.
- Dashboard interactivo de auditoría (7 tabs) y documentación metodológica completa (informe LaTeX, catálogo FAIR, guía de reproducción).
- Recomendaciones de política científica basadas exclusivamente en los hallazgos estadísticos documentados.

**Excluye (límite explícito del análisis técnico):**
- **No** se realiza recolección primaria de datos ni validación contra registros internos de MinCiencias (solo se auditan los datasets públicos Socrata).
- **No** se construyen modelos predictivos de alto riesgo ni modelos causales (no hay diseño experimental ni cuasi-experimental); las asociaciones se reportan como tales.
- **No** se cubren convocatorias posteriores a 2021 (p. ej., 2023) salvo que se integren como extensión acordada.
- **No** se realiza análisis cualitativo ni entrevistas; el alcance es estrictamente cuantitativo.
- **No** se entrega infraestructura big data distribuida (PySpark/Dask) — el volumen actual no lo requiere.

### 4.2 Limitaciones y riesgos técnicos

| # | Limitación / riesgo | Evidencia / origen | Mitigación propuesta |
|---|---|---|---|
| L1 | **Calidad de codificación (mojibake)** en el CSV canónico versionado | `FÃ­sica`, `SÃ©nior`, `BogotÃ¡` en `investigadores_consolidado.csv` | Normalizar a UTF-8 en el pipeline; regenerar artefactos; test de contrato de encoding |
| L2 | **Atípicos e inconsistencia de registros**: 22 edades >100 (máx. 956); conteo documentado como 10 en un módulo y 22 en otro | `src/analisis/calidad.py` vs README/hallazgo 7 | Unificar documentación; mantener eliminación documentada; análisis de sensibilidad con imputación por mediana |
| L3 | **Faltantes estructurales**: departamento "NO DISPONIBLE" 5.2%; género "NO REPORTADO" 2.7% | Evidencias de cobertura | Tratamiento como categoría aparte (ya adoptado); reportar análisis con/sin exclusión |
| L4 | **Cobertura selectiva temporal**: co-filiación solo capturada en 2019 (569 casos); variables de etnia/discapacidad/conflicto solo desde 2021 | README hallazgos 3–4 | Restringir inferencia a cortes disponibles; declarar artefactos de captura; no extrapolar series |
| L5 | **Sesgos de medición**: auto-declaración de género/etnia/discapacidad; el padrón mide *reconocimiento*, no productividad real; cambio de reglas de captura entre convocatorias | Naturaleza administrativa de la fuente | Triangulación con producción; interpretación cautelosa; caveats explícitos en cada indicador |
| L6 | **Sesgo de cohorte y truncamiento por diseño**: eméritos vitalicios no reaparecen (100% de "desaparición" parcial es diseño del sistema) | README hallazgo 14 | Modelar estados absorbentes en las matrices; separar abandono real de diseño |
| L7 | **Tamaño muestral de subgrupos**: raizales, palenqueros, Rrom y discapacidad tienen conteos pequeños → estimaciones inestables | Evidencias de diversidad (3–6× representación) | IC bootstrap; reportar n y coeficientes de variación; evitar desagregaciones sin respaldo muestral |
| L8 | **Supuestos estadísticos potencialmente violados**: propiedad markoviana (dependencia del historial), homogeneidad temporal de transiciones, independencia de observaciones en paneles/redes, celdas esperadas <5 en chi-cuadrado | Naturaleza de los datos | Test de markovianidad; matrices de orden superior; modelos mixtos; correcciones de independencia; pruebas exactas (Fisher) en tablas dispersas |
| L9 | **Complejidad computacional**: producción con 3.2M filas y joins por `id_persona`; red global; riesgo de memoria en análisis ad-hoc | Tamaño declarado del dataset | Cómputos en DuckDB (push-down), particionamiento por convocatoria, caché de resultados en `evidencias/` |
| L10 | **Reproducibilidad comprometida**: CI/CD rota (módulos inexistentes), Dockerfile con app placeholder, tests mínimos, datos crudos no versionados, R legacy con rutas `Downloads/` | Evidencia directa del repositorio (§1.6) | Corregir workflows y Dockerfile; ampliar tests; versionar datos críticos (DVC o Git LFS); migrar R legacy al pipeline Python |
| L11 | **Riesgo ético y normativo**: datos personales (ID, edad, género, etnia, condición de víctima) sujetos a la Ley 1581 de 2012 (protección de datos personales en Colombia) | Presencia de variables sensibles | Mantener la "gran tabla sin ID" como estándar; minimización y anonimización; no publicar microdatos identificables; documentar tratamiento en el informe |
| L12 | **Generalización limitada**: los hallazgos describen el *sistema de reconocimiento*, no el sistema científico colombiano en su totalidad | Naturaleza del registro | Enmarcar conclusiones con este alcance explícito |

### 4.3 Condiciones de éxito y criterios de aceptación

- **Reproducibilidad:** ejecución end-to-end desde la ingesta hasta el informe con un único comando (Poetry) en un entorno limpio, con CI verde.
- **Trazabilidad:** cada indicador del informe mapea a un script y a un CSV de evidencias versionado.
- **Robustez estadística:** todo hallazgo principal reporta tamaño de efecto, intervalo de confianza y el supuesto metodológico que lo sustenta.
- **Alineación ética:** ningún entregable contiene microdatos identificables; todas las visualizaciones agregan a nivel de grupo.

---

## Referencias

### Fuentes del repositorio auditado
- `README.md` — descripción, preguntas de investigación, hallazgos y estructura del proyecto.
- `datos/catalogo.yaml` — metadatos, diccionario de datos y llaves de cruce de ambas fuentes Socrata.
- `src/` — `Transformacion.py`, `ingesta/{minciencias,produccion}.py`, `analisis/*.py`, `modelo/dimensional.py`.
- `scripts/sprint{2..6}_*.py` — orquestación de los análisis por sprint.
- `informe_final.md`, `MARCO_TEORICO.md`, `docs/informe/informe_final.tex`.
- `.github/workflows/etl_update.yml`, `Dockerfile`, `pyproject.toml`, `.gitignore`.

### Literatura metodológica citada
- Fortunato, S., et al. (2018). *Science of science*. Science, 359(6379), eaao0185. [Enlace](https://www.sciencemagazinedigital.org/sciencemagazine/02_march_2018?pg=58)
- Zeng, A., Shen, Z., Zhou, J., et al. (2021). *The science of science: From the perspective of complex systems*. Physics Reports.
- Clauset, A., Larremore, D. B., & Sinatra, R. (2017). *Data-driven predictions in the science of science*. Science, 355(6324), 477–480.
- Hirsch, J. E. (2005). *An index to quantify an individual's scientific research output*. PNAS, 102(46), 16569–16572.
- Hicks, D., Wouters, P., Waltman, L., de Rijcke, S., & Rafols, I. (2015). *The Leiden Manifesto for research metrics*. Nature, 520, 429–431. [Enlace](https://www.nature.com/articles/520429a)
- Kemeny, J. G., & Snell, J. L. (1976). *Finite Markov Chains*. Springer.
- Larivière, V., Ni, C., Gingras, Y., Cronin, B., & Sugimoto, C. R. (2013). *Global gender disparities in science*. Nature, 504, 211–213. [Enlace](https://www.nature.com/articles/504211a)
- Autores invitados (2019). *Women in Latin American science: gender parity in the twenty-first century and prospects for a post-war Colombia*. Journal of Science Communication / Taylor & Francis. [Enlace](https://www.tandfonline.com/doi/pdf/10.1080/25729861.2019.1621538)
- Newman, M. E. J. (2001). *The structure of scientific collaboration networks*. PNAS, 98(2), 404–409. [Enlace](https://arxiv.org/abs/cond-mat/0106144)
- Freeman, L. C. (1977). *A set of measures of centrality based on betweenness*. Sociometry, 40(1), 35–41.
- Clauset, A., Arbesman, S., & Larremore, D. B. (2015). *Systematic inequality and hierarchy in faculty hiring networks*. Science Advances, 1(1), e1400005. [Enlace](https://www.science.org/doi/10.1126/sciadv.1400005)
- Wasserman, S., & Faust, K. (1994). *Social Network Analysis: Methods and Applications*. Cambridge University Press.
- Greenacre, M. (2017). *Correspondence Analysis in Practice* (3rd ed.). Chapman & Hall/CRC.
- Husson, F., Lê, S., & Pagès, J. (2017). *Exploratory Multivariate Analysis by Example Using R* (2nd ed.). Chapman & Hall/CRC.
- Huang, Z. (1998). *Extensions to the k-means algorithm for clustering large data sets with categorical variables*. Data Mining and Knowledge Discovery, 2(3), 283–304.
- Benchmarking distance-based partitioning methods for mixed-type data (2022). [arXiv:2203.16287](https://ar5iv.labs.arxiv.org/html/2203.16287)
- Wang, R. Y., & Strong, D. M. (1996). *Beyond accuracy: What data quality means to data consumers*. Journal of Management Information Systems, 12(4), 5–33.
- Wilkinson, M. D., et al. (2016). *The FAIR Guiding Principles for scientific data management and stewardship*. Scientific Data, 3, 160018. [Enlace](https://www.nature.com/articles/sdata201618)
- Kimball, R., & Ross, M. (2013). *The Data Warehouse Toolkit* (3rd ed.). Wiley.
- DAMA International (2017). *DAMA-DMBOK: Data Management Body of Knowledge* (2nd ed.).
- Wirth, R., & Hipp, J. (2000). *CRISP-DM: Towards a standard process model for data mining*. Proceedings of the 4th International Conference on the Practical Applications of Knowledge Discovery and Data Mining.
- Herfindahl, O. C. (1950). *Concentration in the Steel Industry*. Tesis doctoral, Columbia University. / Hirschman, A. O. (1945). *National Power and the Structure of Foreign Trade*.
- Lotka, A. J. (1926). *The frequency distribution of scientific productivity*. Journal of the Washington Academy of Sciences, 16(12), 317–323.
- Crenshaw, K. (1989). *Demarginalizing the intersection of race and sex*. University of Chicago Legal Forum, 139–167.
