# Validación independiente y crítica — Entrega 1 · Anteproyecto (Sustentación S1–S3, Formato y Citación)

**Validador:** agente independiente y crítico (no complaciente) — solo lectura de fuentes + extracción de la rúbrica; **no se modificó ningún material del equipo**. Este informe es el único archivo nuevo.
**Alcance:** (1) rúbrica oficial `Rúbrica — Entrega 1 · Anteproyecto.pdf` (15 págs., extraída íntegra con pymupdf); (2) `informe_consultoria_observatorio_minciencias.md` (informe base); (3) `documentacion_auditoria/pdf/` — `estado_del_arte.pdf` (20 págs.), `maestro_auditoria.pdf` (126 págs.), `objetivo_1..6` (+lite); (4) fuentes LaTeX `latex/estado_del_arte/` y `latex/maestro_auditoria/`; (5) `data/validacion/*.md` previos; (6) repo `Observatorio_Ministerio_de_Ciencias_Grupo8` (catálogo, README, evidencias, `verificacion_convocatoria_2023.md`).
**Método:** cotejo de cada dimensión de la rúbrica (S1/S2/S3, D1–D5, formato, citación) contra lo que los materiales ya contienen y lo que está ausente; búsqueda de la "Declaración de uso de IA y reparto" y de cualquier banco de preguntas/guion de sustentación (resultado: **no existen**).

---

## 0. Veredicto ejecutivo

**El equipo NO está listo para entregar hoy** (no existe el documento anteproyecto, no existe la declaración S3, no existe preparación individual verificable), **pero el sustrato de contenido es inusualmente fuerte**: los materiales responden, con cifras propias y verificadas, casi todas las preguntas de la matriz. Con un plan de cierre de 3–5 días (síntesis a 6–10 págs., declaración de IA con nombres, banco de preguntas practicado, guion de 10 min) el equipo puede llegar a un nivel **Competente–Ejemplar en D1–D5** y **Competente en S2/S3**. El riesgo mayor no es el contenido sino la **sustentación individual (S1, 28 %, con techo de autoría)**: los materiales fueron producidos en gran parte por agentes de IA y no hay evidencia de que cada integrante haya interiorizado el conjunto.

**Tres vacíos más críticos (en orden de gravedad):**
1. **S3 — No existe la "Declaración de uso de IA y reparto del trabajo" (½ pág.)** ni consta el reparto real con nombres. La rúbrica la exige como parte del documento; no declararla o declararla en falso deja S3 en *Insuficiente*. Dado que los propios materiales evidencian uso intensivo de IA (README, validadores "agente independiente", fichas generadas), una declaración honesta con casos concretos es la única vía segura (ver borrador en §4.2).
2. **No existe el anteproyecto como documento de 6–10 páginas.** Hay un informe base de auditoría fechado 2026-I (híbrido diagnóstico+propuesta, ~345 líneas) y 126+20 págs. de soporte, pero nada redactado en el formato exigido, ni recontextualizado al semestre 2026-II ni a la modalidad *datos abiertos* (criterio sin evidencia en la entrega = 0,0 → "No pertinente"). Además hay una **ambigüedad conceptual sin resolver**: el objeto del proyecto (¿el padrón/sistema MinCiencias? ¿el observatorio-código auditado?) debe fijarse en D1 para que D3 sea bloqueante-compatible (ver §5).
3. **Preparación individual para S1/S2 ausente.** No hay banco de preguntas respondido, ni guion de 10 minutos, ni diapositivas del anteproyecto, ni evidencia de lectura cruzada del conjunto por cada integrante. Con el techo `nota individual ≤ nota S1 + 1,0`, un S1 en *En desarrollo* (3,0) capa la nota en 4,0 aunque el documento sea 5,0. El §3 propone el banco y el mapa de decisiones; falta que el equipo lo practique **en voz alta y sin mirar los documentos**.

---

## 1. S1 · 28 % — Dominio del problema y defensa (individual)

### 1.1 Qué pide la rúbrica (niveles)
- **Ejemplar:** responde sobre cualquier sección (no solo la que redactó); explica el *porqué* de cada decisión y qué alternativa descartó; ante una objeción distingue lo defendible de lo revisable; sostiene con la literatura recordando de dónde viene cada argumento.
- **En desarrollo (piso 3,0):** domina su parte y responde "de oído" el resto; repite el documento sin poder ir más allá; ante objeción cede.
- La rúbrica es explícita: preguntan "a cada integrante por separado, no necesariamente sobre la parte que expuso"; "no repartan el anteproyecto en pedazos".

### 1.2 Evaluación de los materiales como sustrato
**Suficiente para preparar S1 = SÍ, con trabajo de interiorización. Los materiales cubren todas las secciones con contenido verificable:**

| Sección del anteproyecto | Material que la sostiene | Calidad del sustrato |
|---|---|---|
| Problema/contexto (D1) | Informe base §1 (14 hallazgos, cifras: 51 % Bogotá+Antioquia; 24 % vs 48 % mujeres por gran área; afro 3×, indígena 7,9×, discapacidad 8× vs DANE; 36,9 % de autores reconocidos en producción), maestro 02 y 03 | **Alta** — cifras *propias* (calculadas sobre el padrón), no de informes generales: cumple el requisito D1-Ejemplar de "al menos una cifra propia" |
| Estado del arte (D2) | SotA 20 págs., 39 referencias (bibliografía compilada: 38), matriz de mejora (§13), secciones por enfoque 03–10, ética §11 | **Alta** — organizado por enfoque y anclado al repo |
| Objetivos (D3) | Informe base §3.1–3.2 (1 general + 3 específicos OE1–OE3 con entregables) | **Media-alta** — ver §5: hay que verificar que el general responda *exactamente* al problema y que ningún específico sea una actividad |
| Datos (D4) | Maestro §04 (inventario, volumen, estado en clon), `datos/catalogo.yaml` (IDs Socrata `bqtm-4y2h` / `33dq-ab5a`, URLs directas, 30 variables, llaves de cruce), ejecución real 16 scripts (10 OK/6 ERROR), `verificacion_convocatoria_2023.md` | **Alta** — alguien del equipo (vía auditoría) **ya abrió los archivos** y puede citar filas |
| Alcance/riesgos/cronograma (D5) | Informe base §4 (incluye/excluye; L1–L12 con mitigación; fases 1–12 semanas) | **Alta**, pero fechas de 2026-I → rehacer para 2026-II |
| Ética (S3) | SotA §11 (Ley 1581/2012, reidentificación `rocher2019`, k-anonimato), informe base L11 | **Alta** |
| Decisiones + alternativas | Informe base §1.4, maestro §04/§06 (eliminación vs imputación de atípicos; `NO REPORTADO` vs eliminación; CSV vs XLSX; DuckDB vs pandas) | **Parcial** — existen decisiones documentadas, pero **no están redactadas como "alternativa considerada y descartada con razón"** en un solo lugar; hay que explicitarlas (es un requisito D4-Ejemplar y una pregunta típica S1) |

### 1.3 Brechas de S1 (lo que NO existe)
1. **No hay respuestas preparadas** para las preguntas típicas de la rúbrica (págs. 12–13 del PDF). Se proponen en §3 (banco de 10 con plantillas) — pero el banco hay que **practicarlo**, no leerlo.
2. **No hay evidencia de lectura del conjunto por cada integrante.** No constan nombres ni roles (§4.4). Si la producción fue delegada por secciones, el techo de autoría castigará.
3. **Riesgo específico de este equipo:** como la documentación fue generada con agentes de IA (fichas, validaciones, informes), el peligro de S1 no es "no saber la cifra" sino **no poder defender el porqué humano de las decisiones** ni "recordar de dónde viene cada argumento" (Ejemplar). La rúbrica pregunta por la conversación sobre decisiones, no por repetir datos.
4. Punto fuerte a explotar en la defensa: la capacidad de **distinguir lo defendible de lo revisable** está demostrada en los materiales (p. ej., el SotA dice 77.237 registros *declarados* y distingue del XLSX versionado con 50.891; la auditoría documenta sus propias inconsistencias: 10 vs 22 atípicos, conteos de autores). Usarlo en la sustentación ("esto lo defendemos, esto lo revisaríamos") es exactamente el comportamiento Ejemplar de S1.

### 1.4 Mapa de "decisiones y alternativas descartadas" (backbone para S1)
Cada integrante debería poder repetir estos 8 pares decisión/alternativa con una frase de razón:
1. **Problema:** auditar el *sistema de reconocimiento* (padrón+producción) y no evaluar desempeños individuales → el fin es de sistema/observatorio (evaluación responsable, Leiden/DORA).
2. **Fuentes:** solo datos abiertos Socrata (`bqtm-4y2h`, `33dq-ab5a`) en vez de solicitar registros internos a MinCiencias → acceso público, reproducibilidad, sin validación contra internos (exclusión declarada en §4.1 del informe base).
3. **Ventana:** 2013–2021 (6 convocatorias publicadas) en vez de incluir 2023 → verificación empírica: la conv. 2023 **no está publicada** en datos.gov.co (`verificacion_convocatoria_2023.md`).
4. **Panel:** no se reconstruye un panel balanceado (convocatorias irregulares: 2013, 2014, 2015, 2017, 2018/833→2019, 2021) → matrices de transición de 5 periodos + supervivencia.
5. **Atípicos de edad (22 > 100, máx. 956):** eliminación documentada en vez de imputación por mediana → se preserva la distribución; se propone análisis de sensibilidad.
6. **Faltantes:** categoría explícita `NO REPORTADO`/`NO DISPONIBLE` en vez de *listwise deletion* (el legacy R perdía 8,4 %) → trazable.
7. **Inferencia:** reforzar con IC bootstrap, supervivencia KM/Cox, modelos nulos de red, odds ratios ajustados; **causalidad descartada** (diseño observacional de registro administrativo, sin contrafactual) — límite declarado.
8. **Ética:** "gran tabla sin ID", agregación antes de publicar, no publicar microdatos (Ley 1581/2012); riesgo de reidentificación → k-anonimato/generalización de cuasi-identificadores.
9. **Reproducibilidad:** DuckDB + scripts por sprint + catálogo YAML; se corrigen CI/CD y Dockerfile (hoy rotos) y se migra el clustering R legacy a Python validado.
10. **Cobertura de diversidad:** las variables de etnia/discapacidad/víctimas solo existen desde 2021 → inferencia restringida a cortes transversales, sin extrapolar series.

---

## 2. S2 · 18 % — Claridad y estructura de la exposición (equipo)

### 2.1 Qué pide la rúbrica
En **10 minutos** alguien que no leyó el documento debe entender: problema → lo que ya se sabe → qué van a hacer → por qué cabe en el semestre. Hilo visible; diapositivas que apoyan y no se leen; ajuste al tiempo **sin comprimir el cierre**; reparto de la palabra.

### 2.2 Estado actual
No existe guion de 10 min ni deck del anteproyecto. El único deck disponible (`docs/presentacion/index.html`, Reveal.js, 18 slides) pertenece al **proyecto auditado**, no a la propuesta: sirve como banco de figuras ya renderizadas (15 PNG en `docs/presentacion/assets/` y 47+ PNG en `artifacts/`), no como plantilla narrativa.

### 2.3 Estructura óptima de 10 minutos (con tiempos y diapositivas)
Regla: 1 diapositiva ≈ 1 idea; el tiempo total de slides no debe superar ~9 min (dejar 1 min de colchón para no comprimir el cierre).

| # | Min | Bloque | Contenido (de materiales) | Diapositiva concreta (archivo existente) |
|---|---|---|---|---|
| 1 | 0:00–0:45 | Apertura | Quiénes son, objeto en 1 frase: "vamos a auditar estadísticamente el padrón de investigadores reconocidos de MinCiencias (2013–2021) y proponer mejoras al observatorio que lo publica" | Portada + fuentes Socrata con IDs y volúmenes (`bqtm-4y2h` 77.237 / `33dq-ab5a` 3.166.629) |
| 2 | 0:45–2:30 | Problema (D1) | Magnitud del sistema: 30.086 investigadores en 6 convocatorias. Cifras propias de inequidad/calidad: 51 % de la capacidad en Bogotá+Antioquia; 24 % vs 48 % de mujeres según gran área; afro 3×, indígena 7,9× y discapacidad 8× subrepresentados vs censo DANE; consolidado público con mojibake y solo 3 de 6 convocatorias versionadas. "A quién le importa": MinCiencias/ScienTI, política CTI (CONPES 3920/4069), OCDE, los propios investigadores. | `sprint2_territorial/fig01_top_departamentos.png`; `sprint2_genero_ocde/fig02_heatmap_pct_femenino.png`; `sprint4_diversidad/fig02_comparacion_dane.png`; `fig03_categorias_por_minoria.png` |
| 3 | 2:30–3:15 | Consecuencia de no actuar | Sin auditoría formal los errores de captura y las brechas no se documentan ni corrigen: malas señales para asignar recursos de ciencia; riesgo de reproducibilidad para quien use los datos; 2023 aún no publicada. Traducción a pregunta estadística respondible. | `sprint5_produccion/fig01_cobertura_reconocidos.png` (36,9 % de autores reconocidos) o `fig02_productividad_por_categoria.png` |
| 4 | 3:15–4:45 | Estado del arte (D2) | Qué se sabe: Ciencia de la Ciencia (Fortunato 2018); evaluación responsable (Leiden/DORA/CoARA) — indicadores de apoyo, no sustitutivos; sistemas nacionales de información curricular (Lattes vs ScienTI/CVLAC); métodos: Markov/supervivencia (carreras), HHI/Gini/Theil, representación relativa vs censo, modelos nulos de red; calidad de datos (Wang & Strong; FAIR); ética (Ley 1581/2012; riesgo de reidentificación). Contraste clave de 2 enfoques (pregunta típica): *medición de output bruto* (conteos de productividad) vs *evaluación responsable con métricas contextualizadas y caveats* → supuestos distintos sobre si un número puede juzgar sin contexto de área. Vacío declarado: no hay publicado un análisis de auditoría estadística del padrón 2013–2021 cruzado con producción que entregue indicadores de calidad/equidad con inferencia e IC; los análisis públicos previos del dataset son descripciones o casos institucionales. **Mundo vs Colombia** explícito. | Tabla sintética (3–4 filas) hecha a partir de la matriz §13 del SotA — diapositiva *nueva* |
| 5 | 4:45–6:00 | Objetivos (D3) | General (1) + 3 específicos OE1 (calidad y consolidado del dato), OE2 (modelado e inferencia con robustez), OE3 (indicadores, dashboard y recomendaciones al observatorio). Mostrar secuencia: OE1 habilita OE2 habilita OE3; con qué evidencia se declara cumplido cada uno (CSV de evidencias versionados, IC, CI verde). | Diagrama de flujo OE1→OE2→OE3 — diapositiva *nueva* (simple) |
| 6 | 6:00–7:15 | Datos y método (D4) | Procedencia (datos.gov.co/Socrata), periodo 2013–2021, unidad de observación (investigador-convocatoria; producto-autor), volúmenes, variables ligadas a objetivos; método: matrices de transición + supervivencia KM/Cox + familia HHI/Gini/Theil con IC bootstrap + odds ratios ajustados + modelos nulos + clustering validado; alternativas descartadas con razón (causalidad; imputación de atípicos). Plan si el dato no llega (producción ~1,2 GB gitignored → evidencias versionadas + catálogo; 2023 → límite explícito). | `sprint2_longitudinal/fig01_evolucion_total.png` + `sprint2_matrices_transicion` heatmap (`artifacts/sprint2_transiciones/fig01_heatmaps_ext.png`) |
| 7 | 7:15–8:15 | Alcance y por qué cabe en el semestre (D5) | Qué sí/no (sin recolección primaria, sin causalidad, sin >2021, sin big data distribuido); cronograma 12 semanas en 3 fases con hitos y entregables verificables + 2 semanas de holgura; horas reales por integrante. | Línea de tiempo de 12 semanas — diapositiva *nueva* |
| 8 | 8:15–9:00 | Ética e IA (S3) | Datos personales y categorías sensibles (etnia, discapacidad, víctimas) → Ley 1581/2012; auto-declaración y sesgo; riesgo de reidentificación; qué hará el equipo. IA declarada con caso descartado. | Diapositiva *nueva* (máx. 4 bullets) |
| 9 | 9:00–10:00 | Cierre | 2 frases: el problema y la promesa; una cifra memorable; agradecer y abrir preguntas. **No comprimir.** | Diapositiva de cierre |

Reglas de oro para S2: (a) no leer; (b) cada diapositiva nueva debe construirse desde el informe base/SotA (no copiar slides del repo auditado sin reencuadrarlas como propuesta); (c) practicar con cronómetro ≥2 veces repartiendo la palabra (criterio explícito "Reparto de la palabra entre integrantes"); (d) dejar el cierre intacto aunque sobre tiempo en el medio.

---

## 3. Banco de 10 preguntas de defensa con respuestas-plantilla (para practicar S1)

Origen: preguntas típicas de la rúbrica (PDF págs. 12–13) + preguntas de decisión. Cada plantilla cita el material de origen para que el equipo pueda verificar. **Practicar sin mirar el documento; adaptar a la voz de cada integrante.**

**P1 (D1). ¿Quién sufre este problema y desde cuándo?**
*Plantilla:* "El sistema de reconocimiento de investigadores de MinCiencias (ScienTI) ha clasificado a ~30.086 investigadores en 6 convocatorias desde 2013. El 'sufrimiento' es de doble vía: los investigadores, porque su categoría (Junior→Emérito) depende de un registro con errores de captura y sin indicadores de equidad auditados; y los formuladores de política CTI, porque toman decisiones de asignación sobre cifras que hoy no están validadas. La última convocatoria publicada es 2021; verificamos que la de 2023 aún no está en datos.gov.co." *(Fuentes: catálogo.yaml; informe base §1.1; verificacion_convocatoria_2023.md.)*

**P2 (D1). ¿Cómo se está resolviendo hoy, sin ustedes?**
*Plantilla:* "MinCiencias publica el padrón en datos abiertos y existe un observatorio (USTA) con dashboard de 7 capítulos y 14 hallazgos. Pero sin una auditoría formal: el CSV canónico tiene mojibake, el consolidado versionado solo trae 3 de las 6 convocatorias (50.891 de 77.237 filas), el dashboard tiene un bug que impide dibujar HHI y no hay intervalos de confianza. Hoy 'resolver' es publicar conteos; nosotros proponemos convertir el padrón en un objeto de auditoría estadística con indicadores y caveats." *(Fuentes: maestro 02/04; informe base §1.3, §1.6.)*

**P3 (D1). ¿Qué pasa si nadie hace nada?**
*Plantilla:* "Las brechas siguen sin documentarse formalmente —24 % de mujeres en Ingeniería vs 48 % en ciencias médicas; afro 3×, indígena 7,9× y discapacidad 8× subrepresentados frente al censo; 51 % de la capacidad concentrada en Bogotá y Antioquia— y cualquiera que use los datos públicos hoy no puede reproducir los resultados (faltan 3 convocatorias en el artefacto versionado). Eso perpetúa decisiones de política basadas en un registro no auditado y desalienta el uso del dato abierto." *(Fuentes: informe base §1.6; README hallazgos 1–5, 7.)*

**P4 (D2). ¿Cuál de las fuentes citadas los hizo cambiar de idea, y en qué?**
*Plantilla:* "Los Principios de Leiden (Hicks et al., 2015, Nature) y la revisión de Fortunato et al. (2018, Science) nos hicieron pasar de 'medir productividad con conteos' a enmarcar todo como evaluación responsable: indicadores de apoyo al juicio, normalizados por área y con límites declarados. Y el trabajo de Rocher et al. (2019) sobre reidentificación nos obligó a añadir una capa ética explícita (Ley 1581/2012) que no estaba en el diseño original del observatorio." *(Fuentes: SotA §03 y §11; refs.bib.)*

**P5 (D2). ¿Qué hicieron distinto los dos enfoques que contrastaron?**
*Plantilla:* "Contrastamos dos aproximaciones: (a) la bibliométrica clásica de output bruto (conteos tipo ley de Lotka, productividad por categoría) y (b) la evaluación responsable (Leiden/DORA/CoARA). Difieren en un supuesto: la primera trata el número como suficiente para comparar; la segunda exige contexto de área, ventana y caveats. Nuestro proyecto adopta la segunda como principio rector y usa la primera solo como marco nulo de concentración (test contra Lotka)." *(Fuentes: informe base §2.2, §2.10; SotA §03 y matriz §13.)*

**P6 (D2/D4). ¿Por qué su proyecto no es una repetición de lo ya publicado con esos mismos datos?**
*Plantilla:* "Por tres razones: (1) no conocemos —y no encontramos— una auditoría estadística publicada del padrón 2013–2021 **cruzado con la producción de grupos** (3,16 millones de filas) que entregue indicadores de calidad y equidad con inferencia e intervalos de confianza para Colombia; los trabajos públicos sobre ScienTI/CVLAC son descripciones o comparaciones de sistemas, no auditorías de este dataset (p. ej., el artículo CTS ~2010 y Universidad y Sociedad 2023). (2) El observatorio previo es descriptivo-exploratorio, sin supervivencia, sin IC, sin modelos nulos y con bugs documentados que corregimos. (3) Todo nuestro pipeline de hallazgos está validado de forma independiente." *(Fuentes: informe base §2; SotA §04, §13; validaciones.)*

**P7 (D3). Si cumplen los tres específicos, ¿ya resolvieron el general? Muéstrenlo.**
*Plantilla:* "Sí, y la secuencia es visible: OE1 entrega el dato auditado y consolidado (calidad por 6 dimensiones, UTF-8, contrato de esquema) → OE2 usa ese dato para modelar e inferir (transiciones + supervivencia, índices con IC, odds ratios ajustados, modelos nulos) → OE3 convierte eso en el sistema de indicadores, el dashboard y las recomendaciones al observatorio. Sin OE1, OE2 no tiene base reproducible; sin OE2, OE3 no tendría qué mostrar. Cada uno declara cumplido con evidencia versionada en `evidencias/`." *(Fuentes: informe base §3.2.)*

**P8 (D3/D4). ¿Qué variable responde a su primer objetivo específico? ¿Con qué evidencia declaran cumplido OE2?**
*Plantilla:* "Para las brechas de género y diversidad (parte de OE2): `NME_GENERO_PR` y `NME_GRAN_AREA_PR` del padrón, cruzadas con `ETNIA`, `DISCAPACIDAD` y condición de víctima (solo desde 2021) y con el censo DANE para representación relativa. Evidencia de cumplimiento de OE2: salidas con IC en `evidencias/` (p. ej., `diversidad_interseccional_genero_etnia.csv`, `territorial_hhi_por_convocatoria.csv`), más los scripts `sprint*.py` que las generan." *(Fuentes: catalogo.yaml variables; evidencias/.)*

**P9 (D4). ¿Alguien del equipo ya abrió el archivo? ¿Cuántas filas tiene?**
*Plantilla:* "Sí. El padrón completo declarado tiene 77.237 filas (6 convocatorias, 30.086 investigadores únicos, 30 variables) según catálogo y evidencias; el XLSX canónico versionado en el repo tiene 50.891 filas y solo 3 convocatorias (2017: 13.001, 2019: 16.796, 2021: 21.094) — esa discrepancia es un hallazgo de nuestra auditoría, no un descuido nuestro. La producción tiene 3.166.629 filas (77.401 autores) y no está versionada por tamaño (~1,2 GB). Verificamos con conteos reales y ejecutamos 16 scripts (10 OK, 6 error con causa documentada)." *(Fuentes: maestro §04; validacion_factica.md §2; ejecucion_resumen.csv.)*

**P10 (D4/D5/S1). ¿Qué alternativa consideraron y descartaron, y por qué? ¿Qué harían si el dato no llega?**
*Plantilla:* "Descartamos el diseño causal/cuasi-experimental (p. ej., regresión discontinua por umbrales de puntaje) porque el registro es observacional y no tenemos contrafactual; lo declaramos como límite. Descartamos imputar los 22 atípicos de edad >100: optamos por eliminación documentada + sensibilidad. Si el dataset de producción no llega (gitignored, depende de la API), usamos las evidencias versionadas y el catálogo y declaramos la cobertura; si la convocatoria 2023 no se publica, nuestro límite temporal queda explícito en 2021 — ya lo verificamos." *(Fuentes: informe base §4.1–4.2; maestro §04; verificacion_convocatoria_2023.md.)*

**Pregunta extra S3 (obligatoria de preparar). ¿Qué les devolvió la IA que descartaron porque estaba mal?**
Ver los tres episodios documentados en §4.2 (casos 1–3). Contarlos con archivo y línea; no inventar detalles.

---

## 4. S3 · 14 % — Trabajo en equipo, ética y uso declarado de IA

### 4.1 Estado: **VACÍO CRÍTICO**
- **No existe** la "Declaración de uso de IA y reparto del trabajo" (ni en la raíz, ni en `documentacion_auditoria/`, ni en el repo). Búsqueda por contenido ("declaración de uso de IA", "reparto del trabajo", "inteligencia artificial" en *.md) → 0 documentos de declaración.
- No constan **nombres de los integrantes, roles ni horas** en ningún material (los autores de git log pertenecen al proyecto auditado, no al equipo).
- La rúbrica: "No hay declaración de uso de IA, o es falsa a la luz de lo que muestra el documento … deja S3 en Insuficiente"; **y el documento (cuando exista) mostrará uso de IA**: los propios materiales lo evidencian (README de `documentacion_auditoria`, validadores descritos como "agente independiente", fichas por archivo generadas, ejecución reproducida). Declarar "no usamos IA" sería **falsa y detectable** → Insuficiente + daño de credibilidad en S1.

### 4.2 Borrador de la declaración (½ página, lista para adaptar)
> **Declaración de uso de IA y reparto del trabajo**
>
> *Uso declarado.* Usamos herramientas de IA generativa y agentes de IA en tres frentes: (i) **auditoría de código** del repositorio del observatorio (generación de fichas por archivo, orquestación de la ejecución de los 16 scripts y lectura de logs); (ii) **búsqueda de literatura y redacción asistida** del estado del arte, el informe base y este anteproyecto; y (iii) **validación independiente**, mediante agentes validador configurados para lectura crítica, verificación empírica y contraste con fuentes (informes en `documentacion_auditoria/data/validacion/`).
>
> *Cómo se verificó.* Nada se incorporó sin verificación: los números citados se contrastaron contra el código real y los datos (conteos con pandas sobre el XLSX/CSV: 50.891 vs 77.237 filas; 133 commits contra `git log`; reproducción empírica de los bugs de `redes.py:64`, `diversidad.py:78-79` y del dashboard HHI); las referencias del estado del arte se verificaron una a una por búsqueda web (ninguna fabricada; 2 correcciones de metadatos); y cada documento fue revisado por al menos un agente validador independiente y por [revisión humana de cada integrante — completar nombres].
>
> *Lo que la IA sugirió y descartamos porque estaba mal* (casos concretos): **1)** un agente describió como bug que `diversidad.py:145` lanzaba `KeyError: 'FEMENINO'` "si algún grupo étnico no tiene mujeres"; al reproducirlo vimos que con `unstack(fill_value=0)` la columna existe salvo que *ningún* grupo tenga mujeres → corregimos la condición (documentado en `validacion_factica.md`, P5). **2)** un agente marcó la cadena "SÃ, se ejecuta…" como ejemplo intencional de mojibake; la verificación byte a byte mostró que era un artefacto real de doble codificación ("Sí") en `objetivo_3/secciones/03_codigo.tex:3444` y `maestro …/05_codigo.tex:2495` → lo reportamos como defecto de QA por corregir. **3)** un agente afirmó que la sección de fichas de `objetivo_3` seguía el orden canónico de `capas.yaml`; la comparación mostró que el generador la producía en **orden alfabético** por nombre de capa (causa raíz: `_orden_por_capa()` usa el string, no el índice) → corregimos la afirmación y localizamos la causa (documentado en `validacion_reglas.md`, regla 3).
>
> *Riesgos éticos del proyecto.* El padrón contiene datos personales y **categorías sensibles** (etnia, discapacidad, condición de víctima, edad, género) → tratamiento bajo la **Ley 1581 de 2012** y decretos reglamentarios: minimización, finalidad, seguridad. Riesgos propios: (a) **reidentificación** de investigadores por combinación de cuasi-identificadores (departamento, área, edad) aun sobre agregados — mitigación: "gran tabla sin ID", agregación antes de publicar, análisis de riesgo de reidentificación, no publicar microdatos; (b) **sesgo de auto-declaración** en género/etnia/discapacidad y captura solo desde 2021 — mitigación: reportar como limitación y restringir la inferencia a cortes transversales; (c) **uso indebido del resultado** (clasificar o sancionar investigadores con nuestros indicadores) — mitigación: enmarcar todo bajo evaluación responsable (Leiden/DORA): evidencia de apoyo, no veredicto. *(Equipo: completar reparto real con nombres, quién redactó qué y quién revisó qué, horas por semana y fecha.)*

**Nota crítica:** los tres casos descritos arriba están **documentados en los informes de validación citados**, pero el equipo debe re-verificarlos antes de firmar la declaración (la rúbrica puede comprobarlos; un detalle mal citado en una declaración de honestidad es contraproducente). Si alguno de los episodios no coincide exactamente con lo que ocurrió, narrar el caso real del equipo: lo que importa es que sea **específico y verificable**.

### 4.3 Riesgos éticos a declarar (extraídos de materiales) y qué hacer
- Marco legal: Ley 1581/2012 (+ Decreto 1377/2013, hoy compilado) — el SotA §11 ya lo trae; falta citarlo en el anteproyecto y en la defensa.
- Riesgo de reidentificación: `rocher2019estimating` (SotA §11), k-anonimato, generalización de cuasi-identificadores.
- Sesgo de auto-declaración y cobertura 0 % antes de 2021 (informe base L4–L5): no extrapolar series.
- Celdas pequeñas en subgrupos (raizales, palenqueros, Rrom, discapacidad): reportar n y CV; no desagregar sin respaldo muestral (informe base L7).
- Uso indebido del resultado: marco Leiden/DORA (informe base §2.2, §3.1).

### 4.4 Qué más necesita el equipo para S3
1. **Reparto real del trabajo con nombres** (quién redactó cada sección del anteproyecto, quién hizo la revisión cruzada, quién valida cifras) — hoy inexistente.
2. Confirmación de **horas por semana por integrante** (pregunta típica D5 y criterio "reparto verificable en la sustentación").
3. Declaración de **herramientas concretas** (nombres de modelos/agentes usados) — nivel de especificidad Ejemplar.
4. Una línea de **política del equipo** para el resto del semestre (qué se permite/ no se permite con IA y cómo se registrará) para que la declaración no sea solo retrospectiva.

---

## 5. Formato / entrega — síntesis a 6–10 páginas

### 5.1 Viabilidad de la síntesis
**SÍ, es viable y los materiales sobran** (informe base ~345 líneas, maestro 126 págs., SotA 20 págs., 51 fichas, validaciones). El reto no es falta de contenido sino **selección, reencuadre y límite de extensión**. Advertencias de contexto:
- **Recontextualizar fechas/objeto:** el informe base dice "USTA 2026-I" y describe una auditoría ya ejecutada; el anteproyecto es la propuesta del semestre **2026-II** ("no evalúo resultados: evalúo si entendieron el problema"). Reusar el informe base *verbatim* hará que D5 parezca un cronograma ya cumplido.
- **Ambigüedad D1/D3 (riesgo de puerta bloqueante):** los objetivos del informe base (OE1–OE3) mezclan dos objetos: auditar el *dato/sistema MinCiencias* (calidad del padrón, indicadores, recomendaciones al observatorio) y *reparar el repositorio-código* (CI/CD, Dockerfile, tests, migración de R legacy). La rúbrica exige un problema único con actor, alcance y consecuencia. **Decisión que debe tomar el equipo:** si el problema es el *sistema de reconocimiento y su observatorio* (recomendado para la modalidad datos abiertos: "a quién le importaría este resultado y por qué"), los objetivos deben enunciarse a nivel del padrón/indicadores y tratar la reparación del repo solo como medio (puede ir en alcance/entregables). Si el objeto fuera "auditar el repositorio", la modalidad datos abiertos y la pertinencia pública se debilitan. Esta elección debe ser **explícita y consistente en D1–D3–D5**.
- **Modalidad datos abiertos** (la rúbrica lo exige en D1/D4): argumentar (i) a quién le importa y por qué (MinCiencias/ScienTI, política CTI — respaldado por SotA §04 y los artículos Universidad y Sociedad 2023 / CTS ~2010); (ii) procedencia: entidad, periodo, licencia y **enlace directo** (los enlaces existen en catálogo; la **licencia no está registrada en los materiales** → verificar la página "About" de cada dataset en datos.gov.co y citarla); (iii) por qué no está ya resuelto y publicado con esos datos (ver P6); (iv) limitaciones asumidas explícitamente.

### 5.2 Índice propuesto del anteproyecto (con extensión objetivo y qué recortar)
Total contenido 6–10 págs. (sin portada ni referencias); meta: **~8 págs.**. Sección por sección:

1. **Planteamiento del problema y contexto — 1½–2 págs. (D1, bloqueante).**
   - *De dónde:* informe base §1.1/§1.3/§1.6 y maestro 02 (cifras); catálogo; `verificacion_convocatoria_2023.md`.
   - *Qué escribir:* actor (investigadores reconocidos, MinCiencias/ScienTI, formuladores CTI), alcance (6 convocatorias 2013–2021, padrón 77.237/30.086, producción 3,16 M), frecuencia ("por convocatoria, cada 1–3 años; última publicada 2021"), estado actual con **2–3 cifras propias** (51 % Bogotá+Antioquia; 24 % vs 48 %; 3×–8× vs DANE; 3/6 convocatorias en el artefacto versionado), consecuencia de no intervenir, y la pregunta estadística respondible.
   - *Recortar:* de los 14 hallazgos, seleccionar 4–5; **no** incluir la tabla de estructura de carpetas ni el inventario de librerías.
2. **Estado del arte y antecedentes — 2–3 págs. (D2).**
   - *De dónde:* SotA 20 págs. (§§03–11) y su matriz §13.
   - *Qué escribir:* ≥8 fuentes recientes y verificables **organizadas por enfoque** (SciSci y evaluación responsable; sistemas nacionales de información curricular; calidad de datos y gobernanza; dinámica longitudinal; desigualdad/género; redes; ética); **contraste explícito** de 2 aproximaciones; vacío declarado ligado al proyecto; mundo vs Colombia; cita APA 7.
   - *Recortar:* de 11 dominios a 6–7; los 16 recursos web (SotA §14.2) reducirlos a los 4–5 que se citan de verdad; matriz §13 → solo 5–6 filas si se incluye.
3. **Objetivos — ½ pág. (D3, bloqueante).**
   - *De dónde:* informe base §3.1–3.2, **reescritos** como logros con verbo verificable y evidencia de cumplimiento, coherentes con el problema elegido en D1 (ver ambigüedad en §5.1).
   - *Recortar:* eliminar la redacción tipo actividad ("revisar la literatura", "realizar un perfilado…" → convertir el perfilado en logro medible); 3 específicos bastan.
4. **Datos disponibles y método preliminar — 1–2 págs. (D4).**
   - *De dónde:* maestro §04 (inventario/volúmenes/estado), catálogo (IDs `bqtm-4y2h`, `33dq-ab5a`, URLs, variables), informe base §1.4/§2 (métodos) y §4.2 (riesgos del dato).
   - *Qué escribir:* fuentes con procedencia, periodo, unidad de observación, volumen, condiciones de acceso/licencia (pendiente verificar licencia); variables ligadas a cada OE; ruta metodológica con ≥1 alternativa descartada con razón; plan si el dato no llega.
   - *Recortar:* tabla Wang & Strong completa → síntesis de 3–4 dimensiones; no listar las 30 variables, solo las que responden a objetivos.
5. **Alcance, riesgos y cronograma — 1 pág. (D5).**
   - *De dónde:* informe base §3.3 y §4.1–4.2.
   - *Qué escribir:* qué sí y qué no con razón (sin recolección primaria, sin causalidad, sin >2021, sin big data); cronograma 12 semanas por **hitos con entregables verificables** y 2 semanas de holgura; 2–3 riesgos concretos con contingencia (p. ej., producción ~1,2 GB no versionada → evidencias + catálogo; datos sensibles → Ley 1581 y agregación; bugs heredados del repo → corrección en OE1); horas/semana por integrante.
   - *Recortar:* tabla L1–L12 (12 filas) → 5–6 riesgos máx.; la tabla de fases 3.3 → convertirla en cronograma de hitos semanales.
6. **Declaración de uso de IA y reparto del trabajo — ½ pág. (S3).** Borrador en §4.2 + nombres/roles (falta completar).
7. **Referencias (APA 7) — no cuenta en el total.** Lista única con **solo las fuentes citadas** (~18–25) extraídas de `refs.bib` (39) y del informe base, convertidas a APA 7 (ver §6).

### 5.3 Cálculo de extensión
1,5–2 + 2–3 + 0,5 + 1–2 + 1 + 0,5 = **7–9,5 págs.** de contenido → dentro de 6–10. El riesgo es pasarse en D2 (el SotA da para 6 págs.); usar la matriz §13 como esqueleto y 1 figura por sección como máximo.

---

## 6. Citación APA 7

### 6.1 Estado actual de los materiales
- SotA: BibTeX/natbib, estilo `plainnat` (autor-año), 39 entradas en `refs.bib` (24 @article, 10 @book, 1 @techreport, 3 @misc, 1 @inproceedings); **bibliografía compilada con 38 ítems** (1 entrada nunca citada). Más una subsección de recursos web citados solo con título+URL.
- Informe base: lista de referencias en Markdown, estilo autor-año aproximado con enlaces URL, sin DOI; 1 entrada sospechosa ("Autores invitados (2019)… Journal of Science Communication / Taylor & Francis" — autoría no resuelta).
- Repo auditado (`MARCO_TEORICO.md`): lista heterogénea, algunas con formato casi-APA, sin DOI.

### 6.2 Trabajo de conversión a APA 7 (estimación: 1–2 días + verificación)
1. **Autores completos:** `plainnat` con "and others" (p. ej., Wilsdon et al. 2015) o listas largas → APA 7 lista hasta 20 autores; pasar de notación BibTeX "Apellido, Nombre" a "Apellido, N." es mecánico pero hay que **reescribir la lista final a mano** o con gestor (Zotero) para no introducir errores.
2. **DOI/URL:** APA 7 exige DOI cuando existe y URL para recursos en línea; la mayoría de las 39 entradas carecen de ambos → añadir DOIs **verificados** (riesgo: inventar DOIs = referencia que no se puede abrir → D2 a *Insuficiente*). Alternativa prudente: incluir solo DOI confirmado o URL estable del editor.
3. **Correcciones heredadas (ya detectadas por validadores):** `theil1967economics` está tipificada `@article`/journal North-Holland → debe ser **libro** (APA: Theil, H. (1967). *Economics and information theory*. North-Holland); `kimball2013data` citada en texto pero **ausente de la bibliografía compilada** (añadir cita o entrada); `@report` no definido en plainnat (cosmético); duplicación Souza 2023 (canónica vs. recurso web) → una sola entrada APA.
4. **Recursos web sin autor/fecha (SotA §14.2):** varios se citan por título+URL (política declarada "no atribuir autoría no verificada"). En APA 7, cuando no hay autor se usa el título en la posición de autor y fecha conocida o "(s. f.)" + fecha de consulta. El equipo ya verificó varias autorías (Kwiek y Szymula; Souza et al.) → **completar metadatos verificados** o mantener formato título+recuperación, consistente en todo el documento. La **inconsistencia de política** señalada por el validador (ítems 6 y 13 sí atribuyen autoría, el resto no) debe resolverse.
5. **Del informe base:** convertir las ~20 referencias del bloque "Literatura metodológica citada" a APA 7 estricta (volúmenes/números/páginas presentes en su mayoría) y resolver "Autores invitados (2019)" (buscar autoría real de "Women in Latin American science…" en T&F antes de citarla; si no se resuelve, **excluirla**).

### 6.3 ¿La bibliografía del estado del arte es rastreable (referencias reales)?
**SÍ — verificada por validación previa independiente** (`validacion_sota_referencias.md`): de las 27 entradas canónicas evaluadas, **26/27 con obra real y metadatos correctos**, 0 referencias fabricadas; los 16 recursos web son reales (URLs verificadas). La versión actual (39 entradas) incorpora además ética/visualización. Conclusión: el riesgo de "referencia inexistente" (que fulmina D2) es **bajo** si la conversión a APA 7 no introduce erratas; el riesgo operativo está en la conversión misma (DOIs, autorías, deduplicación) y en la entrada "Autores invitados" del informe base.

---

## 7. Qué puede prepararse YA con los materiales vs. qué falta producir (resumen accionable)

| Tarea | ¿Listo hoy con materiales? | Evidencia / acción |
|---|---|---|
| D1 problema con cifras propias | **SÍ (con redacción)** | Cifras verificadas en informe base §1.6, README, catálogo; falta redactar actor/alcance/consecuencia/pregunta y decidir el objeto único (§5.1) |
| D2 estado del arte 2–3 págs. | **SÍ (con selección)** | SotA 20 págs. + matriz §13; falta sintetizar a 2–3 págs. y declarar el vacío en una frase |
| D3 objetivos | **SÍ (con reescritura)** | Informe base §3.1–3.2; reescribir como logros con evidencia; alinear al D1 elegido |
| D4 datos y método | **SÍ** | Maestro §04 + catálogo + validaciones; **falta: licencia verificada y "alternativas descartadas" explícitas** |
| D5 alcance/riesgos/cronograma | **SÍ (con re-fechado)** | Informe base §4; rehacer cronograma a 2026-II con hitos semanales y horas por integrante |
| **S3 declaración IA + reparto** | **NO — vacío crítico** | Borrador en §4.2; falta: nombres, roles, horas, herramienta(s) concretas, firma |
| S1 banco de preguntas | **NO (banco propuesto aquí)** | Practicar §3 en voz alta, sin documentos; interiorizar §1.4 |
| S2 guion + diapositivas | **NO** | Construir las 9 diapositivas de §2.3 (3–4 son nuevas); ensayar con cronómetro |
| Referencias APA 7 | **PARCIAL** | Conversión de refs.bib/informe base (§6); añadir DOIs verificados; excluir/resolver "Autores invitados 2019" |
| PDF final 6–10 págs. | **NO** | Redactar siguiendo §5.2 |

---

## 8. Veredicto final

# NO LISTO para entregar en su estado actual — LISTO PARA PRODUCIR la entrega con calidad alta en 3–5 días de trabajo dirigido

**Fundamento:**
1. **Contenido (D1–D5): fuerte.** Los materiales aportan cifras propias verificadas, un estado del arte validado (0 referencias fabricadas) y decisiones documentadas; esto rara vez existe a este nivel en un anteproyecto. Con 2–3 días de síntesis y una decisión conceptual (objeto del proyecto, §5.1) el documento alcanza nivel **Competente–Ejemplar** en contenido.
2. **S3: vacío crítico hoy.** La declaración de IA y reparto **no existe**; su borrador (§4.2) está listo pero requiere nombres, roles y verificación de los 3 episodios. Sin ella, S3 cae a *Insuficiente* o *No pertinente* y, si se declara en falso, a un problema de integridad mayor. Es el entregable más urgente.
3. **S1/S2: sin preparación individual, el techo castiga.** La sustentación pesa 60 % y S1 es individual con techo `nota ≤ S1 + 1,0`. Un miembro que solo domine "su parte" deja el S1 en *En desarrollo* (3,0) y capa la nota en 4,0 aunque el documento sea excelente. El banco de §3 y el mapa de §1.4 deben practicarse **en voz alta, sin mirar los documentos, por cada integrante**; el guion de §2.3, ensayarse ≥2 veces con cronómetro.
4. **Riesgos propios de este equipo (a no ocultar):** producción intensiva con agentes de IA → la declaración honesta con casos concretos es la única vía segura en S3, y la sustentación debe demostrar que **los humanos** entienden el porqué (S1), no solo los datos. Recontextualizar todo a 2026-II y a la modalidad datos abiertos (incluida la licencia de los datasets, hoy sin registrar).

*Validador: solo lectura; no se modificó ningún material del equipo (el único archivo creado es este informe; se eliminó el extracto temporal de la rúbrica usado para la lectura).*
