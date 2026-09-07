# Validación independiente: referencias y mapeo al repositorio del "Estado del Arte"

**Validador:** agente independiente y crítico (lectura + verificación empírica + búsqueda web; sin modificación de fuentes)
**Alcance:** `documentacion_auditoria/latex/estado_del_arte` (secciones 02–12, `refs.bib`) vs. repositorio `Observatorio_Ministerio_de_Ciencias_Grupo8` y datos de auditoría `documentacion_auditoria/data/`
**Método:** (1) cotejo de cada entrada de `refs.bib` contra conocimiento bibliométrico y verificación web puntual; (2) verificación de los 16 recursos de la sección 12.2 por búsqueda web; (3) contraste de las afirmaciones de mapeo de las secciones 03–10 contra el código real del repo (`src/`, `.github/workflows/`, `.gitignore`), `README.md`, `datos/catalogo.yaml`, `data/ejecucion_resumen.csv` y el informe fáctico previo `data/validacion/validacion_factica.md`; (4) coherencia interna (matriz de la sección 11, claves de cita, `main.bbl`/`main.blg`).

---

## 1. Referencias canónicas (`refs.bib`) — tabla de veredictos

Veredictos: **OK** = obra real con autores, año y medio correctos · **DUDOSA** = no pude confirmar o hay ambigüedad material · **ERROR** = error verificable de autoría/año/medio.

| # | Clave | Entrada declarada | Veredicto | Nota del validador |
|---|-------|-------------------|-----------|--------------------|
| 1 | `fortunato2018science` | Fortunato et al., *Science of science*, Science 359(6379):eaao0185, 2018 | **OK** | Obra real; autoría, revista, volumen, número y artículo (eaao0185) correctos. |
| 2 | `zeng2021science` | Zeng et al., *The science of science: From the perspective of complex systems*, Physics Reports 935:1–60, 2021 | **OK** | Correcto (A. Zeng, Z. Shen, J. Zhou, J. Fan, Z. Di, Y. Wang, H. E. Stanley, S. Havlin). |
| 3 | `wang2021sciencebook` | Wang & Barabási, *The Science of Science*, Cambridge University Press, 2021 | **OK** | Sí, es Cambridge UP (2021). Respuesta a la duda explícita del encargo: **correcta**. |
| 4 | `clauset2017data` | Clauset, Larremore, Sinatra, *Data-driven predictions in the science of science*, Science 355(6324):477–480, 2017 | **OK** | Correcto (Science, no otra revista). |
| 5 | `hicks2015leiden` | Hicks, Wouters, Waltman, de Rijcke, Rafols, *The Leiden Manifesto for research metrics*, Nature 520(7548):429–431, 2015 | **OK** | Correcto (Nature 520; respuesta a la duda del encargo: **sí**). |
| 6 | `wilsdon2015metric` | Wilsdon et al., *The Metric Tide*, HEFCE, 2015 | **OK** (observación) | Obra real (HEFCE 2015). Observaciones: (i) el tipo `@report` **no está definido en plainnat** → BibTeX emite warning (main.blg:6-7) y la entrada se trata como misc; (ii) `Wilsdon, James and others` se renderiza "James Wilsdon et al." perdiendo a los ~15 coautores reales. No es error de fondo. |
| 7 | `dora2012` | San Francisco Declaration on Research Assessment (DORA), 2012 | **OK** | Declaración real (iniciada 2012, publicada 2012/2013); autor corporativo correcto. |
| 8 | `coara2022` | Agreement on Reforming Research Assessment, CoARA, 2022 | **OK** | Correcto (firmado 2022). |
| 9 | `lariviere2013global` | Larivière, Ni, Gingras, Cronin, Sugimoto, *Global gender disparities in science*, Nature 504(7479):211–213, 2013 | **OK** | Correcto (Nature 504; respuesta a la duda del encargo: **sí**). |
| 10 | `newman2001structure` | Newman, *The structure of scientific collaboration networks*, PNAS 98(2):404–409, 2001 | **OK** | Correcto. |
| 11 | `freeman1977set` | Freeman, *A set of measures of centrality based on betweenness*, Sociometry 40(1):35–41, 1977 | **OK** | Correcto. |
| 12 | `clauset2015systematic` | Clauset, Arbesman, Larremore, *Systematic inequality and hierarchy in faculty hiring networks*, Science Advances 1(1):e1400005, 2015 | **OK** | Correcto (Science Advances 1(1); respuesta a la duda del encargo: **sí, es Science Advances**). |
| 13 | `sugimoto2017scientists` | Sugimoto et al., *Scientists have most impact when they're free to move*, Nature 550(7674):29–31, 2017 | **OK** | Correcto (comment en Nature 550). |
| 14 | `hirsch2005index` | Hirsch, *An index to quantify an individual's scientific research output*, PNAS 102(46):16569–16572, 2005 | **OK** | Correcto. |
| 15 | `wang1996beyond` | Wang & Strong, *Beyond accuracy: What data quality means to data consumers*, JMIS 12(4):5–33, 1996 | **OK** | Correcto. |
| 16 | `wilkinson2016fair` | Wilkinson et al., *The FAIR Guiding Principles…*, Scientific Data 3:160018, 2016 | **OK** | Correcto. |
| 17 | `dama2017dmbok` | DAMA International, *DAMA-DMBOK*, 2.ª ed., Technics, 2017 | **OK** | Correcto. |
| 18 | `kimball2013data` | Kimball & Ross, *The Data Warehouse Toolkit*, 3.ª ed., Wiley, 2013 | **OK** (obra) / **ERROR de integración** | Obra real y metadatos correctos, **pero nunca se cita con `\cite`** en el texto: aparece solo como mención textual "Kimball 2013" en 02_introduccion.tex:27. Consecuencia verificada en `main.bbl`: solo se listan 26 de las 27 entradas; **Kimball & Ross queda fuera de la bibliografía compilada (12.1)** y el lector no puede localizar la obra. |
| 19 | `kemeny1976finite` | Kemeny & Snell, *Finite Markov Chains*, Springer-Verlag, 1976 | **OK** (con nota) | Obra real. Matiz de historiografía: original Van Nostrand 1960; la edición Springer-Verlag 1976 es una reedición clásica ampliamente citada. Aceptable; convendría anotar "reedición". |
| 20 | `lotka1926frequency` | Lotka, *The frequency distribution of scientific productivity*, J. Washington Acad. Sci. 16(12):317–323, 1926 | **OK** | Correcto. |
| 21 | `huang1998extensions` | Huang, *Extensions to the k-means algorithm for clustering large data sets with categorical variables*, DMKD 2(3):283–304, 1998 | **OK** | Correcto (artículo canónico de k-prototypes). |
| 22 | `greenacre2017correspondence` | Greenacre, *Correspondence Analysis in Practice*, 3.ª ed., Chapman & Hall/CRC, 2017 | **OK** | Correcto (3.ª ed. 2017). |
| 23 | `husson2017exploratory` | Husson, Lê, Pagès, *Exploratory Multivariate Analysis by Example Using R*, 2.ª ed., Chapman & Hall/CRC, 2017 | **OK** | Correcto (2.ª ed. 2017; cubre FAMD). |
| 24 | `crenshaw1989demarginalizing` | Crenshaw, *Demarginalizing the intersection of race and sex…*, Univ. of Chicago Legal Forum 1989:139–167 | **OK** | Correcto (Vol. 1989, Art. 8, pp. 139–167). |
| 25 | `wasserman1994social` | Wasserman & Faust, *Social Network Analysis*, Cambridge UP, 1994 | **OK** | Correcto. |
| 26 | `theil1967economics` | Theil, *Economics and Information Theory*, "journal = North-Holland", 1967 | **ERROR de medio** (obra real) | La obra existe y es el origen del índice de Theil (North-Holland, Amsterdam, 1967; autor y año correctos). **Pero está tipificada como `@article` con `journal={North-Holland}`**: North-Holland es la **editorial**, no una revista; debería ser `@book` con `publisher={North-Holland}`. En la bibliografía compilada se mostrará como un "artículo" sin revista real. Respuesta a la duda del encargo: la obra es real, el medio está mal clasificado. |
| 27 | `souza2023observability` | Souza, Skluzacek, Wilkinson, Ziatdinov, da Silva, *Towards Lightweight Data Integration using Multi-workflow Provenance and Data Observability*, IEEE eScience 2023 (preprint) | **OK** | Verificado por web: preprint del artículo **aceptado en el 19.º IEEE eScience 2023** (Limassol); autoría y URL ar5iv (2308.09004) correctas. `howpublished` honesto. Respuesta a la duda del encargo: **sí, es IEEE eScience 2023**. |

**Resumen:** 26/27 entradas con obra real y metadatos correctos; 1 ERROR de medio (`theil1967economics`); 1 error de integración bibliográfica (`kimball2013data` ausente de la bibliografía compilada); 2 observaciones menores (`@report` no definido en plainnat; `others` en Wilsdon). **Ninguna referencia fabricada ni con autor/año/medio sustancialmente falso.**

---

## 2. Recursos en línea (sección 12.2) — evaluación

**Veredicto global: enfoque correcto y prudente; 3 observaciones de coherencia y 1 de prudencia interpretativa.**

Verificación de existencia (búsqueda web, todos los URLs resuelven a recursos reales):

| Ítem 12.2 | Recurso | Existencia | Nota |
|---|---|---|---|
| 1 | Revista CTS, vol. 5, n.º 13 — "Dos países latinoamericanos…: Brasil y Colombia (Lattes vs. ScienTI)" | **REAL** | El PDF de revistacts.net reproduce exactamente ese título. |
| 2 | Universidad y Sociedad (scielo.sld.cu) — categorización de grupos e investigadores SNCTI Colombia | **REAL** | Coincide con el registro S2218-36202023000500133. |
| 3 | Revista Científica (UDistrital) — ciencia abierta, métricas de nueva generación, Publindex/SCIENTI | **REAL** | Existe (espejo scielo.org.co, S0124-2253…093); la descripción trunca el subtítulo, sin fabricar nada. |
| 4 | Journal of Informetrics 17(1) 2023 — "Geography of science: Competitiveness and inequality" | **REAL** | Confirmado (p. ej. handle Tor Vergata 2108/309876). |
| 5 | FEBS Letters 2024 — "Leaving science — attrition of biologists in 38 OECD countries" | **REAL** | DOI 10.1002/1873-3468.70028 confirmado. |
| 6 | "Patterns of Scientific Attrition… OECD Countries" (xbjk.ecnu.edu.cn, id=11215) | **REAL** | Confirmado; la atribución "(Kwiek y Szymula)" que sí incluye el ítem es **correcta**. |
| 7 | PMC10450398 — "Ranking mobility and impact inequality in early academic careers" (2023) | **REAL** | Confirmado (IRIS Pavia). |
| 8 | BVS — "Quantifying hierarchy and dynamics in US faculty hiring and retention" | **REAL** | Corresponde a Nature 610 (2022), PMID 36131023. |
| 9 | Blog UCLA Career 2024 — "Hierarchy in Hiring…" | **REAL** | URL confirmada. |
| 10 | UCACUE Pure — "Gender disparities in scientific output in the Andean Community (2020–2024)" | **REAL** | URL confirmada. |
| 11 | UCR — "Gender Gaps and Female Participation in STEM: A Bibliometric Analysis…" | **REAL** | PDF en portal.so.ucr.ac.cr confirmado. |
| 12 | CLACSO — medidas que desestimulan la producción de libros / CSH | **REAL** | El título real ("…producción de libros académicos y desconocen la producción colectiva de conocimiento…") respalda la descripción. |
| 13 | Souza et al. 2023, IEEE eScience (preprint) | **REAL** | Idéntico a la entrada canónica (ver §1, #27). |
| 14 | Benchmark-Mixed-Clustering (GitHub, ClementCornet) | **REAL** | Repositorio abierto confirmado; la descripción coincide con su tagline. |
| 15 | Research in Higher Education 64 (2023) — "The Role of Early-Career University Prestige Stratification…" | **REAL** | Confirmado (ERIC EJ1363118). |
| 16 | Catálogo Stanford — estudios de academic inbreeding (Grochocki) | **REAL** | Es una **búsqueda de catálogo** (URL de consulta), no un documento; la descripción lo declara honestamente. |

**Juicio sobre el enfoque "sin atribuir autoría no verificada": correcto.** Las descripciones se mantienen a nivel de título/medio/vena y no inventan autores; la política declarada en 02 y 12.2 es la decisión bibliográfica correcta para material gris.

**Observaciones:**
1. **Inconsistencia interna de la propia política**: el preámbulo de 12.2 afirma que los recursos se citan "sin atribuir autoría no verificada", pero el ítem 6 atribuye "(Kwiek y Szymula)" y el ítem 13 da la cita completa con autores (Souza et al.). En ambos casos la autoría es *correcta* (verificada), pero el enunciado de política no se cumple uniformemente.
2. **Duplicación**: el ítem 13 (Souza et al. 2023) es la misma obra de la entrada canónica `souza2023observability` (refs.bib, §12.1). La obra figura dos veces en el documento con dos tratamientos distintos.
3. **Prudencia interpretativa (ítem 1 usado en la sección 04)**: la descripción del ítem 1 reproduce el título del artículo (prudente), pero la sección 04 eleva el recurso a afirmación fáctica *actual* —"solo dos países latinoamericanos cuentan con sistemas de información curricular consolidados" ("actualmente")— anclada en un artículo de ~2010 (vol. 5, n.º 13 de CTS). Esa afirmación es discutible hoy (p. ej., México/CVU-SNI, actualizaciones de CVLAC) y el SotA la presenta sin fecha ni matiz. No es un error de referencia (el recurso es real y dice eso), pero el uso que se hace en 04 merece cautela.
4. **Estabilidad del ítem 16**: un URL de búsqueda de catálogo es frágil (cambia con el catálogo); como "recurso" es débil aunque la descripción sea honesta.

---

## 3. Mapeo al repositorio — afirmaciones verificadas (secciones 03–10 vs. repo y auditoría)

Fuentes de contraste: `README.md`, `datos/catalogo.yaml`, código real (`src/analisis/redes.py`, `src/analisis/diversidad.py`, `src/analisis/longitudinal.py`, workflows, `.gitignore`), `data/ejecucion_resumen.csv`, fichas `data/analisis_codigo/*.json` y `data/validacion/validacion_factica.md`.

| # | Afirmación del SotA (sección) | Verificación | Veredicto |
|---|---|---|---|
| a | "6 convocatorias 2013–2021, 77 237 registros declarados, 30 086 investigadores únicos" (02:13-14; también 04) | README:25 y catálogo: `n_total=77237`, `n_unicos=30086`, 6 convocatorias (640/2013…894/2021); evidencias versionadas `calidad_resumen.json` con 77.237. El SotA dice prudentemente "declarados" y distingue del XLSX del clon. | **CORRECTO** |
| b | "3 de 6 convocatorias en el consolidado versionado" (04:28-29); "consolidado completo de 6 convocatorias, hoy ausente del clon" (05:45) | `validacion_factica.md` §2: XLSX `investigadores_consolidado.xlsx` = 50.891×30 con solo conv. 19/20/21 (2017/2019/2021). **El SotA lo dice (3 de 6), aunque no cuantifica 50.891** — omisión de precisión, no error. | **CORRECTO** (no cuantifica 50.891) |
| c | "HHI por departamento y región (hallazgo: Bogotá y Antioquia concentran 51 %)" (07:25-26) | README hallazgo 1 ("Bogotá + Antioquia = 51% del país"); `sprint2_territorial.py` calcula HHI. Sin intervalos de confianza ni Gini/Theil en `src/` (grep: 0 coincidencias). | **CORRECTO** |
| d | "24 % en Ingeniería vs. 48 % en ciencias médicas" (08:21-22) | README hallazgo 2, idéntico. | **CORRECTO** |
| e | "afro 3×, indígena 7.9×, discapacidad 8× subrepresentados" vs DANE (08:24-26) | README hallazgo 5, idéntico. | **CORRECTO** |
| f | "matrices de transición de Markov… con las 6 convocatorias" y "no hay modelos de supervivencia" (06:25-26, 30-31) | Evidencias versionadas: matrices de 5 periodos entre las 6 convocatorias (2013_2014…2019_2021; obs/ext). Sin código de supervivencia/Kaplan/Cox en `src/` ni `scripts/` (grep: 0). | **CORRECTO** |
| g | "bug de `split(n=1)` en `redes.py` pierde pares de 3+ afiliaciones y crea nodos con cadenas literales ('B\|C')" (09:28-30) | `redes.py:62-64`: `str.split("|", n=1, expand=True)` verificado; bug reproducido empíricamente por `validacion_factica.md` §4c (efecto real peor de lo descrito). | **CORRECTO** |
| h | "segmentación… en scripts R legacy (`kproto` con k=3 fijo, sin validación)" y "pérdida del 8.4 %… por casos incompletos" (10:22-23, 27-28) | Ficha `analisis_de_clusters.R.json`: `kproto(GT_NA, k=3)` sin validación; `cc()` retiene 91.6 % (pierde 8.4 %); rutas hardcodeadas `Downloads/`. CA/MCA/FAMD en R también con rutas `Downloads/` (`analisis_multivariado_base_gran_table.R.json`). Gran tabla sin ID con `dtype='object'` (`codigo_creacion_gran_tabla…py.json`). | **CORRECTO** |
| i | "bug metodológico del denominador `comparar_dane()`" (08:29-30) | `diversidad.py:78-79`: comentario promete excluir "NINGUN GRUPO ETNICO" del denominador; el filtro solo excluye "NO DISPONIBLE" → denominador inflado, razones de subrepresentación diluidas. Bug real (reproducido en `validacion_factica.md` §4b). **Matiz de redacción**: el paréntesis "(corrige la exclusión de 'NINGUN GRUPO ETNICO')" es ambiguo — el código *no aplica* esa exclusión; el texto parece afirmar lo contrario. La identificación del bug es correcta, la frase no. | **CORRECTO (con redacción ambigua)** |
| j | "CI/CD rota (módulos inexistentes en el workflow)"; "datos crudos y procesados sin versionar (ausencia de DVC pese a la nota del `.gitignore`)" (05:27, 26) | Workflow `etl_update.yml` invoca `python -m src.ingesta.main` y `python -m src.transformacion.main`; **no existen** esos módulos en `src/` (no hay `ingesta/main.py` ni paquete `transformacion`) → el job falla. Sin archivos `.dvc`/`dvc.yaml` en el repo (glob: 0); `.gitignore:15` comenta "usar DVC para versionar". | **CORRECTO** |
| — | Otras afirmaciones de mapeo muestreadas: co-filiación solo 2019 (569 casos), 2.762 cadenas→~800 IES, tabla maestra 211 IES/91 %, productividad Junior 30/Asociado 65/Senior 121, retención Bogotá 92 % y absorción 1 000+, eméritos vitalicios, conv. 833 mal etiquetada, 22 atípicos de edad, 5 de 6 áreas con brecha de productividad, duplicidad de artefactos de matrices, cobertura 0 % de diversidad antes de 2021, patrón Pregunta→Hallazgo→Caveat (03:35-37; 04:27-29; 06:27, 32; 07:26-27, 31-32; 08:23-24, 27-28; 09:23-27) | Todas coinciden con README (hallazgos 1–14, Sprint 6), catálogo y fichas de auditoría. | **CORRECTO** |

**Conclusión del mapeo:** las secciones 03–10 describen fielmente el estado actual del repositorio; no se detectó exageración de capacidades ni atribución de resultados inexistentes. Las afirmaciones de "carencia" (sin supervivencia, sin Gini/Theil/IC, sin DVC, CI/CD rota, k sin validar, bug de pares, bug del denominador) son todas verificables en el código real. El SotA hereda correctamente los hallazgos de la auditoría (que a su vez fue validada como "APROBADO CON OBSERVACIONES" por `validacion_factica.md`). Única zona de redacción ambigua: la frase sobre `comparar_dane()` (§i). Mención menor: en 06:33-34 el SotA lista las ventanas como "(2013, 2014, 2015, 2017, 2019, 2021)"; coincide con los periodos reales de las matrices (2017_2019, 2019_2021, según `ANO_CONVO` real = fecha de publicación), mientras README/catálogo etiquetan la conv. 833 como "2018" (nominal) — el propio repo documenta la anomalía; ninguna de las dos convenciones es un error del SotA.

---

## 4. Coherencia interna

**4.1 Matriz de la sección 11 vs. recomendaciones 03–10.**
Las 8 filas de la matriz (Evaluación responsable, Calidad de datos, Longitudinal, Desigualdad, Género y diversidad, Redes, Datos mixtos, Sistema nacional) se corresponden con las secciones 03/05/06/07/08/09/10/04 y recogen la *mejora prioritaria* de cada una con sus referencias principales (todas existentes en `refs.bib`). **Cobertura mayoritaria pero no exhaustiva**: recomendaciones secundarias que no aparecen en ninguna fila de la matriz:
- 03, rec. 3 — modelos predictivos de carreras (estilo Clauset 2017 / Wang & Barabási 2021): ausente.
- 06, rec. 4 — modelar movilidad geográfica entre departamentos: ausente.
- 07, rec. 3 / 09, rec. 3 — análisis de jerarquía institucional tipo `clauset2015systematic` y endogamia en Colombia: ausente (la fila "Redes" solo cubre modelos nulos + extracción de pares + corte 2019).
- 08, rec. 3 — robustecer el cruce interseccional (celdas mínimas, `reindex`): ausente.
- 04, recs. 1 y 3 — marco comparativo Brasil–Colombia y alineación con ciencia abierta/CONPES: solo parcial (fila "Sistema nacional" = posicionar en el debate de política).
Como la matriz se autodefine de "mejora prioritaria" (no exhaustiva), esto es una omisión de condensación, no una contradicción; pero un lector que use solo la matriz perdería esas 5 líneas de recomendación.

**4.2 Citas indefinidas.** Ninguna: todas las claves `\cite/\citet/\citep` usadas en 03–11 (28 usos sobre 24 claves) existen en `refs.bib` (verificado clave a clave; sin warnings de undefined en `main.blg`; `main.aux`/`main.bbl` compilan con 26 entradas usadas). Las referencias cruzadas "(sección 12.2)" apuntan a ítems existentes y pertinentes (atrición OCDE→ítems 5-6; movilidad temprana→7; geografía→4; jerarquía/endogamia→8-9, 16; Comunidad Andina→10; STEM→11; benchmark→14; SNCTI/Lattes→1-3). Mención textual "ISO/IEC 25012" (05) no requiere entrada bibliográfica.

**4.3 Problemas de integración detectados (verificados en `main.bbl`/`main.blg`):**
1. `kimball2013data` nunca se cita → **no aparece en la bibliografía compilada** pese a nombrarse como clásico canónico en la introducción ("Kimball 2013", 02:27). (26/27 entradas en el .bbl.)
2. `theil1967economics` se imprime como si fuera un artículo "North-Holland 1967" (tipo/medio erróneos; §1, #26).
3. Warning de BibTeX por `@report` indefinido en plainnat (`wilsdon2015metric`); cosmético.
4. Duplicación Souza 2023 en 12.1 y 12.2 (§2, obs. 2) e inconsistencia de la política de "no atribución" (§2, obs. 1).

---

## 5. Veredicto final

# **APROBADO CON OBSERVACIONES**

**Fundamento:**
1. **Referencias canónicas**: 26/27 entradas corresponden a obras reales con autoría, año y medio correctos (incluidas las cinco dudas explícitas del encargo: Clauset 2015 = Science Advances; Larivière 2013 = Nature 504; Hicks 2015 = Nature 520; Wang & Barabási 2021 = Cambridge UP; Souza et al. 2023 = IEEE eScience). No hay referencias fabricadas.
2. **Recursos en línea (12.2)**: los 16 URLs son reales y las descripciones son prudentes; el enfoque de no inventar autoría es correcto.
3. **Mapeo al repositorio**: las afirmaciones de estado actual (a–j) se verifican contra el código, README, catálogo y datos de auditoría; no hay exageraciones ni omisiones de hallazgos clave.
4. **No hay errores de fondo** que invaliden contenido, números o recomendaciones.

**Observaciones no bloqueantes (errores concretos):**
1. `refs.bib:229-234` — `theil1967economics` tipificada como `@article` con `journal={North-Holland}`: obra real pero medio mal clasificado; debe ser `@book` (publisher North-Holland).
2. `refs.bib:162-168` / `02_introduccion.tex:27` — `kimball2013data` nunca citada con `\cite`: ausente de la bibliografía compilada (26/27 en `main.bbl`).
3. `08_genero_diversidad.tex:29-30` — frase "(corrige la exclusión de 'NINGUN GRUPO ETNICO')" ambigua: el código de `comparar_dane()` **no** excluye "NINGUN GRUPO ETNICO" del denominador (diversidad.py:78-79); debería decir "el código no aplica la exclusión prometida por el comentario".
4. `12_referencias.tex` — duplicación de Souza 2023 (ítem 13 = entrada canónica `souza2023observability`) e incoherencia de la política de no atribución (ítems 6 y 13 sí atribuyen autoría, correcta pero no declarada).
5. `04_sistemas_nacionales.tex:6-12` — el uso del artículo CTS (~2010) como base de una afirmación *actual* ("solo dos países… actualmente") merece fecharse y matizarse.

**Tres hallazgos más importantes:**
1. **Las referencias son casi impecables en exactitud**: no se encontró ninguna obra inventada ni ningún error de autor/año/revista en las 27 entradas canónicas; el único defecto bibliográfico real es la clasificación errónea de Theil 1967 como artículo (es libro), más el caso editorial de Kimball 2013 ausente de la bibliografía compilada.
2. **El mapeo al repositorio es fiel y verificable**: las 10 afirmaciones de estado (a–j), incluidos los bugs `split(n=1)` en `redes.py:62-64` y el denominador de `comparar_dane()` (diversidad.py:78-79), se confirman en el código real; el SotA no exagera capacidades ni atribuye resultados inexistentes.
3. **La sección 11 es una condensación fiel pero incompleta**: la matriz omite 5 recomendaciones secundarias sustantivas (modelos predictivos de carrera, movilidad geográfica, jerarquía institucional/endogamia, robustez interseccional, marco Brasil–Colombia y ciencia abierta), y las secciones 04–08 contienen dos zonas de redacción que conviene corregir (el paréntesis de `comparar_dane()` y la afirmación "actual" basada en el artículo CTS de ~2010).
