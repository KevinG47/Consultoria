# Validación independiente y crítica — Criterios D1–D5 del anteproyecto (Rúbrica «Entrega 1 · Anteproyecto», USTA 2026-II)

**Validador:** agente independiente y no complaciente (solo lectura; no se modificó ningún archivo del equipo).
**Objeto:** suficiencia de los materiales existentes del equipo como base de evidencia para redactar el anteproyecto *«Auditoría estadística del sistema de reconocimiento de investigadores de MinCiencias (Colombia) como base para mejorar el observatorio de datos abiertos»* — modalidad **DATOS ABIERTOS** (sin organización cliente).
**Rúbrica evaluada:** `Rúbrica — Entrega 1 · Anteproyecto.pdf` (15 págs.), extraída íntegramente con pymupdf; se usaron las columnas de la matriz (págs. 5–6), el apartado «Qué mira cada criterio» (págs. 8–10) y los ajustes de la modalidad datos abiertos (pág. 7).
**Materiales evaluados:**
- `informe_consultoria_observatorio_minciencias.md` (informe base, 4 secciones)
- `documentacion_auditoria/pdf/estado_del_arte.pdf` (20 págs.) y sus fuentes `latex/estado_del_arte/secciones/*.tex` + `latex/estado_del_arte/refs.bib` (39 entradas)
- `documentacion_auditoria/pdf/maestro_auditoria.pdf` (126 págs., texto extraído y verificado)
- `documentacion_auditoria/data/ejecucion_resumen.csv` y `commits_timeline.csv`
- `Observatorio_Ministerio_de_Ciencias_Grupo8/README.md` y `datos/catalogo.yaml`
- Validaciones previas del equipo: `data/validacion/validacion_factica.md`, `validacion_rubrica.md`, `validacion_sota_referencias.md`, `validacion_sota_cobertura.md`

**Advertencia metodológica (importante para leer las notas):** el anteproyecto **todavía no está redactado**. Los niveles asignados califican la **capacidad de los materiales de sostener cada criterio hoy** (qué evidencia verificable existe ya y qué habría que redactar o producir desde cero). Donde un criterio es BLOQUEANTE, se indica además el riesgo de que el anteproyecto, entregado tal cual con estos materiales, caiga al nivel inferior («si dudan entre dos niveles, están en el de abajo», rúbrica pág. 2).

---

## 0. Tabla resumen D1–D5

Escala de logro: Ejemplar 1,0 · Competente 0,8 · En desarrollo 0,6 · Insuficiente 0,4 · No pertinente 0,0.
Nota parcial = logro × peso (columna «logro × peso»), y su equivalente en escala 0–5 (×5). La suma de aportes del bloque Documento sobre 5,0 es **1,26** (máximo posible del bloque: 2,0 = 40 % × 5).

| Criterio | Peso | Nivel asignado | Logro | Logro × peso | Nota parcial (0–5, ×5) | ¿Bloqueante? |
|---|---|---|---|---|---|---|
| D1 Problema, contexto y estado actual | 12 % | **EN DESARROLLO** (riesgo alto de INSUFICIENTE si se entrega sin redactar) | 0,6 | 0,072 | **0,36** | 🔒 SÍ |
| D2 Estado del arte y rigor bibliográfico | 9 % | **EN DESARROLLO** | 0,6 | 0,054 | **0,27** | No |
| D3 Objetivos, general y específicos | 8 % | **EN DESARROLLO** (riesgo alto de INSUFICIENTE) | 0,6 | 0,048 | **0,24** | 🔒 SÍ |
| D4 Datos y aproximación metodológica preliminar | 6 % | **COMPETENTE** | 0,8 | 0,048 | **0,24** | No |
| D5 Alcance, viabilidad y plan de trabajo | 5 % | **EN DESARROLLO** | 0,6 | 0,030 | **0,15** | No |
| **Suma bloque Documento** | **40 %** | | | **0,252** | **1,26 / 5,0** (63 % del bloque) | |

**Lectura:** con los materiales actuales el bloque Documento aportaría ~1,26 puntos de los 2,0 posibles. Los dos criterios bloqueantes (D1, D3) están exactamente donde los materiales tienen **menos contenido redactable directamente** (no hay problema declarado ni objetivos del nuevo proyecto), lo que confirma que son la prioridad de redacción.

---

## 1. D1 — Problema, contexto y estado actual (12 %, 🔒 BLOQUEANTE)

### Nivel asignado: EN DESARROLLO (60 %)

### Qué pide el «Ejemplar» y qué hay en los materiales

| Requisito Ejemplar | Estado en materiales | Evidencia concreta |
|---|---|---|
| Delimita el problema con **actor, alcance, frecuencia y consecuencia** explícitos, distinguido de sus **síntomas** | ✗ **Ausente como enunciado.** No existe en ningún material una sección «problema» con actor/alcance/frecuencia/consecuencia. El actor se infiere (MinCiencias publica el padrón; investigadores y tomadores de decisión lo usan); la consecuencia de no intervenir nunca se formula (solo se dice que el repo «no es reproducible», que es consecuencia técnica del proyecto previo, no del problema de política/datos) | Informe base §1 y §4 describen *estado técnico de un repositorio*, no un problema con actor; `maestro_auditoria.pdf` §1.2–1.5 (resumen ejecutivo) concluye en brechas de ingeniería (CI/CD rota, mojibake, tests mínimos), no en un problema del sistema de reconocimiento |
| Cuantifica el estado actual con **al menos una cifra propia** (no de informe general): cuántos casos, qué tasa de error, qué costo | ✅ **Cumplido con holgura, pero las cifras describen el sistema/síntomas, no «cómo se resuelve hoy el problema»** | Cifras propias verificadas: 77 237 registros / 30 086 investigadores únicos (README líneas 17–25; `catalogo.yaml`); 51 % Bogotá+Antioquia (README hallazgo 1); 24 % vs 48 % mujeres por área (hallazgo 2); cobertura 0 % de etnia/discapacidad/víctimas antes de 2021 (hallazgo 4); solo 36,9 % de los autores en producción son reconocidos (hallazgo 8); 22 edades >100 años (hallazgo 7); ejecución real 10/16 scripts OK, 6 ERROR (`data/ejecucion_resumen.csv`) |
| Explica **qué ocurre si nadie hace nada** | ✗ Ausente | Solo hay consecuencia a nivel de repositorio («un clon fresco no reproduce el pipeline», `maestro_auditoria.pdf` sección 3/5); no hay consecuencia para el sistema de reconocimiento ni para quien usa el dato abierto |
| El problema queda formulado como **pregunta estadística respondible** | ✗ Ausente | Las 7 «preguntas de investigación» (README líneas 45–53 y `maestro` §2.2) pertenecen al proyecto previo, son amplias y no estadísticas («¿Qué tan confiable es la información…?» no define métrica ni comparación); ninguna es la pregunta del nuevo anteproyecto |
| **Modalidad datos abiertos:** argumento explícito de **a quién le importaría** este resultado, sostenido con **al menos una fuente que documente la magnitud del problema en Colombia** | ✗ **Ausente.** El SotA §13.2 aporta estudios críticos colombianos (categorización SNCTI en *Universidad y Sociedad* 2023; Publindex/ScienTI en *Revista Científica* UDistrital; artículo comparativo CTS ~2010) y el informe cita CONPES 4069 (ciencia abierta), pero **ninguno cuantifica la magnitud** del problema específico (p. ej., aspirantes vs. reconocidos, cobertura del sistema, horas de trazabilidad) | `estado_del_arte.pdf` §13.2; informe §2.5 (artículo «post-war Colombia»); no hay cifra externa (MinCiencias/OCDE/DANE/CONPES) que ancle la magnitud en Colombia |
| Distingue problema de **técnica** («aplicar series de tiempo») | ✅ No hay confusión con técnica (los materiales son ricos en contenido sustantivo) | Todo el material es sustantivo |

### Vacíos (materiales)
1. No existe enunciado formal del problema (actor + alcance + frecuencia + consecuencia) en ninguna pieza.
2. No existe la pregunta estadística respondible del anteproyecto (los materiales dan las piezas: fiabilidad/comparabilidad del padrón, cobertura del reconocimiento, calidad de los datos abiertos).
3. No existe la cadena de justificación de modalidad datos abiertos: beneficiario concreto del resultado + fuente externa (no propia) que documente la magnitud en Colombia.
4. Las cifras propias existen pero hay que **re-etiquetarlas como «línea base del estado actual»** de un problema (hoy están presentadas como hallazgos de una auditoría ya hecha, no como evidencia de un problema vigente que el anteproyecto va a atender).

### Qué escribir/añadir para llegar a EJEMPLAR
- Redactar 1½–2 págs. de «Planteamiento del problema» con: **actor** (investigadores postulantes, MinCiencias como responsable del registro, usuarios del dato abierto / política científica), **alcance** (padrón de reconocidos 2013–2021 publicado en datos.gov.co), **frecuencia** (convocatorias cada 1–3 años; p. ej. 6 convocatorias en 8 años, `catalogo.yaml` «periodicidad: por convocatoria… cada 1–3 años»), y **consecuencia** explícita si nadie actúa.
- Separar síntomas (mojibake, etiquetado erróneo, atípicos, cobertura selectiva) del problema raíz (el dato oficial de reconocimiento no es auditable/comparable y no existe verificación pública reproducible → decisiones y métricas de política construidas sobre datos sin control de calidad declarado).
- Formular 1 pregunta estadística respondible (ej.: «¿qué proporción de los registros del padrón de reconocidos viola criterios mínimos de calidad/comparabilidad y cómo se distribuye por convocatoria, área y territorio?»).
- Añadir 1–2 fuentes externas que documenten la magnitud en Colombia (p. ej., metas SNCTI/CONPES 4069, cifras MinCiencias de investigadores reconocidos vs. aspirantes, OCDE *Main Science and Technology Indicators* para Colombia) y declarar explícitamente «a quién le importa este resultado y por qué».

---

## 2. D2 — Estado del arte y rigor bibliográfico (9 %)

### Nivel asignado: EN DESARROLLO (60 %)

### Qué pide el «Ejemplar» y qué hay en los materiales

| Requisito Ejemplar | Estado | Evidencia concreta |
|---|---|---|
| Sintetiza **≥ 8 fuentes recientes y verificables** | ◐ **Limítrofe.** Solo la bibliografía formal tiene **7 entradas ≥ 2018** (Fortunato 2018; van Buuren 2018; Rocher 2019; Zeng 2021; Wang & Barabási 2021; CoARA 2022; Souza 2023). Se supera 8 solo contando los 14 recursos con URL de §13.2 (varios 2022–2024: *J. Informetrics* 2023, FEBS Letters 2024, Research in Higher Education 2023, Nature 2022…) | `refs.bib` (39 entradas; conteo por `year`); `estado_del_arte.pdf` §13.2 |
| Organiza **por enfoque, no por autor** | ✅ Cumplido | Secciones 02–12 por eje metodológico (SciSci, sistemas nacionales, calidad de datos, longitudinal, desigualdad, género, redes, datos mixtos, ética, visualización), cada una con patrón «Qué dice la literatura / Relación con el repositorio / Mejoras recomendadas» |
| **Contrasta ≥ 2 aproximaciones señalando en qué difieren sus supuestos** | ✗ **No explícito.** Hay contraposiciones implícitas (Markov sin memoria vs. modelos condicionados a historia; supervivencia con censura vs. transición; k-prototypes vs. k-means/Gower; indicadores cuantitativos Leiden/CoARA vs. crítica CLACSO) pero **ningún pasaje dice «el enfoque A asume X, el enfoque B asume Y, por eso difieren y por eso elegimos…»** | §06, §10, §03 del SotA; la matriz §12 solo enumera mejoras |
| **Declara el vacío que su proyecto atiende** | ✗ **Ausente para el nuevo proyecto.** La síntesis (§12 y «Hallazgo» final) declara la «agenda de mejora del repositorio» previo (inferencia formal, robustez, visualización auditable), no un vacío de conocimiento del anteproyecto (p. ej., «no existe una auditoría estadística verificable del padrón de reconocimiento publicado como dato abierto en Colombia») | `estado_del_arte.pdf` §12, págs. 14–15 |
| **Distingue mundo vs. Colombia** | ◐ **Parcial.** Hay material (SotA §04 sistemas nacionales: Lattes/Sucupira vs. ScienTI-CVLAC/Publindex, CONPES 4069; §13.2 con estudios colombianos), pero no está sintetizado como «qué se ha hecho en el mundo vs. qué en Colombia» aplicado al problema del anteproyecto; el SotA fue escrito para *mejorar el repo*, no para situar un proyecto nuevo | SotA §04, §13.2; `validacion_sota_cobertura.md` ya criticó la sobre-generalización de la fuente CTS ~2010 |
| **Citación APA 7 sin errores** | ✗ **No cumple.** El documento usa `\bibliographystyle{plainnat}` con natbib (autor-año en corchetes), **no APA 7**: (a) en el texto: «Fortunato et al. [2018]», «[DORA, 2012]», «Wang and Barabási [2021]» (APA exige paréntesis, «&», sin corchetes); (b) en la lista: autores con nombre completo no invertido («Mark EJ Newman.» en vez de «Newman, M. E. J.»), año tras punto («…2018.» en vez de «(2018).»), volumen(número):páginas con dos puntos («359(6379):eaao0185» en vez de «359(6379), eaao0185»), **sin DOIs**, URLs con la etiqueta «URL», títulos en minúscula | `main.tex` (línea 36), `estado_del_arte.pdf` págs. 18–20 (citas textuales extraídas); el propio doc admite «en formato autor-año» (§13.1) |
| **Riesgo de referencias inventadas** | ✅ **0 fabricadas (confirmado).** | Ver Anexo A |

### Vacíos y defectos adicionales (materiales)
1. **El SotA no está escrito para este anteproyecto:** su objetivo declarado es «traducir la literatura en acciones de mejora para *este repositorio*» (`02_introduccion.tex`, propósito); para D2 del anteproyecto hay que re-enmarcar hacia el problema nuevo (qué se ha hecho en auditoría de registros administrativos de reconocimiento con datos abiertos, qué falta en Colombia).
2. **Formato de citación:** conversión integral a APA 7 (biblatex-apa o manual) de las 39 entradas + recursos 13.2, con DOIs donde existan.
3. Contraste explícito de ≥ 2 enfoques con supuestos y vacío declarado: redactar (ver tabla).
4. **Referencias cruzadas internas desactualizadas en el PDF compilado:** el texto cita «la sección 11 consolida…», «sección 12.1/12.2» pero la numeración real es §12 Síntesis y §13 Referencias (13.1/13.2) — defecto visible de coherencia tras insertar las secciones de ética y visualización (`estado_del_arte.pdf` pág. 4 y en §§03–06, 09; verificado contra el TOC del mismo PDF). Debe corregirse para no restar rigor al entregable.
5. La ventana declarada «2018–2026» (SotA §1.2) no coincide con la distribución real (7 canónicas ≥2018; la mayoría son clásicos 1926–2017) — si se va a argumentar «recientes», conviene seleccionar ≥8 fuentes de los últimos ~8 años en la sección D2 del anteproyecto.

### Qué escribir/añadir para llegar a EJEMPLAR
- Reusar las secciones temáticas (organización por enfoque ya existe y es buena), pero: (i) re-enfocar la revisión a la pregunta del anteproyecto; (ii) añadir un párrafo de contraste de ≥2 aproximaciones con sus supuestos (p. ej., evaluación por indicadores bibliométricos del registro vs. evaluación de pares del modelo MinCiencias; o auditoría de calidad orientada al dato vs. análisis de redes/productividad) y la decisión tomada; (iii) declarar el vacío que atiende este proyecto; (iv) añadir una síntesis mundo vs. Colombia; (v) convertir toda la citación a APA 7 con DOI; (vi) completar ≥8 fuentes recientes verificables en la selección final.

---

## 3. D3 — Objetivos, general y específicos (8 %, 🔒 BLOQUEANTE)

### Nivel asignado: EN DESARROLLO (60 %)

### Qué hay en los materiales
- Objetivo general en `informe_consultoria_observatorio_minciencias.md` §3.1 (líneas 230–234): *«Diseñar e implementar una auditoría estadística integral y reproducible del sistema de reconocimiento de investigadores de MinCiencias (convocatorias 2013–2021), que evalúe… la fiabilidad, comparabilidad y equidad del padrón oficial… y que entregue un sistema de indicadores críticos, un dashboard de auditoría y documentación metodológica formal, listos para integrarse al informe institucional del observatorio»*.
- Tres específicos OE1–OE3 (§3.2, líneas 236–254): OE1 «exploración, auditoría de calidad y consolidación de datos»; OE2 «modelado estadístico e inferencia analítica»; OE3 «implementación, despliegue y documentación de resultados», cada uno con sub-bullets y «Entregables».

### Análisis crítico contra la rúbrica

| Requisito Ejemplar | Estado | Evidencia / argumento |
|---|---|---|
| General que **responde exactamente al problema de D1** (ni más ancho ni más angosto) | ✗ **No verificable hoy** (D1 no está formulado) y con riesgo de desborde: el OG incluye «sistema de indicadores + dashboard + documentación lista para integrarse al informe institucional del observatorio», entregables de sistema heredados del proyecto previo, más anchos que una pregunta estadística de auditoría | §3.1 del informe |
| 3–5 específicos que **agotan el general sin solaparse** | ✗ **No demostrable.** Los OE1–OE3 son 3, pero OE2 acumula ~5 sub-resultados (supervivencia, índices con IC, modelos logísticos de brechas, redes contra nulos, migración de clustering) → es un programa, no un específico; OE1 (corregir mojibake/dataset v2) y OE2 (modelar calidad) y OE3 (reparar CI, tests, dashboard del repo previo) se solapan con el alcance del proyecto que ya se ejecutó | §3.2 del informe |
| Cada específico **empieza por verbo verificable** y deja ver **con qué evidencia** se declarará cumplido | ◐ **Parcial.** Verbos en su mayoría de actividad o no medibles: «realizar», «corregir y documentar», «ampliar el modelo longitudinal», «robustecer la medición», «consolidar el dashboard», «reparar la cadena de reproducibilidad». Sí declaran «Entregables» (evidencia parcial), pero sin criterio de logro (qué cifra/umbral demuestra cumplimiento) | §3.2 |
| **Secuencia visible** (cada uno habilita al siguiente) | ✅ Parcialmente (fases I→II→III explícitas) | §3.3 tabla Fases |
| No confundir **actividades con logros** | ✗ Varios OE describen actividades del cronograma («reparar la cadena de reproducibilidad», «publicar el informe», «migrar al pipeline Python») | §3.2 OE2–OE3 |

**Observación clave:** estos objetivos documentan la consultoría **ya ejecutada en 2026-I** (auditoría del repositorio). El anteproyecto 2026-II necesita objetivos **nuevos** que respondan a la pregunta de D1; copiar OE1–OE3 tal cual pondría a D3 en la frontera de INSUFICIENTE (específicos que describen actividades del cronograma y no se sabe con qué evidencia se declaran cumplidos, rúbrica pág. 5).

### Qué escribir/añadir para llegar a EJEMPLAR
- Redactar 1 objetivo general que responda exactamente a la pregunta estadística de D1 (sin arrastrar dashboard/CI/tests del proyecto previo salvo que sean parte declarada del alcance).
- 3–5 específicos con verbos de logro medible y evidencia de cumplimiento definida (p. ej., OE-A «Estimar la tasa y la distribución de incumplimientos de calidad… → evidencia: tabla de métricas por convocatoria con IC»; OE-B «Comparar la composición del padrón frente a la producción y el censo… → evidencia: odds ratios con IC y n»; OE-C «Diseñar el índice/indicador de auditabilidad y validarlo con análisis de sensibilidad → evidencia: especificación + resultados de robustez»).
- Verificar con la prueba de la rúbrica: «si cumplen los 3–5 específicos, ¿ya resolvieron el general?» y eliminar solapamientos (cada métrica/indicador debe aparecer en un solo OE).

---

## 4. D4 — Datos y aproximación metodológica preliminar (6 %)

### Nivel asignado: COMPETENTE (80 %)

### Qué pide el «Ejemplar» (modalidad datos abiertos) y qué hay

| Requisito Ejemplar | Estado | Evidencia concreta |
|---|---|---|
| Fuentes con **procedencia** (entidad responsable, plataforma, enlace directo) | ✅ Cumplido | `catalogo.yaml`: entidad MinCiencias vía datos.gov.co (Socrata), URLs directas `https://www.datos.gov.co/resource/bqtm-4y2h.csv` y `…/33dq-ab5a.csv`; README líneas 9–43; `maestro_auditoria.pdf` tabla 2 |
| **Periodo** | ✅ Cumplido | 6 convocatorias 2013–2021, desglose por convocatoria y registros (`catalogo.yaml`; README líneas 17–25; periodicidad «por convocatoria, cada 1–3 años» declarada) |
| **Unidad de observación** | ✅ Cumplido | Fila = investigador × convocatoria (padrón); fila = producto-autor (producción); llave `id_persona_pr ↔ id_persona_pd` (+ `id_convocatoria`) (`catalogo.yaml`; README líneas 27–43) |
| **Volumen aproximado** | ✅ Cumplido | 77 237 registros / 30 086 investigadores únicos / 30 variables; 3 166 629 productos / 77 401 autores; ~1.2 GB (README; `catalogo.yaml`; informe §1.3) |
| **Condiciones de acceso o licencia verificadas** | ✗ **Ausente por escrito.** `catalogo.yaml` no tiene campo de licencia (grep: 0 resultados fuera de `.venv`); README e informe tampoco la declaran. Se usó la API Socrata (sodapy, paginada) pero la licencia/condiciones de reuso del dataset no están documentadas en ningún material | `catalogo.yaml` completo; README; informe §1.3–1.4 |
| **Variables ligadas a cada objetivo específico** | ◐ Parcial. Existe diccionario completo (30+ variables con «uso_analítico» en `catalogo.yaml`) y el informe §2/SotA mapean ejes→módulos→métodos, pero **no hay una tabla formal «objetivo específico → variables → método»** del nuevo proyecto (la matriz del SotA §12 es por eje técnico del repo, no por objetivo del anteproyecto) | `catalogo.yaml`; informe §2.10 matriz; SotA §12 |
| **Ruta metodológica con ≥1 alternativa considerada y descartada con razón** | ◐ Parcial. Hay decisiones documentadas con su alternativa (atípicos: eliminación vs. imputación por mediana del grupo, con razón, `src/analisis/calidad.py` + informe §1.4; clustering: k-prototypes vs. k-means/Gower, SotA §10; índices: HHI vs. HHI+Gini+Theil con IC, SotA §07; imputación: casos completos vs. imputación múltiple). Falta presentarlas **como ruta del anteproyecto** (elegida + descartada con razón por específico) | Informe §1.4, §2.3–2.7; SotA §07, §10; `maestro_auditoria.pdf` (§2.3 decisiones) |
| **Declara qué haría si el dato no llega** | ✗ **Ausente.** Solo se menciona que la ingesta depende de la API (~1.2 GB) y que sin `produccion_grupos.csv` 3 scripts fallan (`ejecucion_resumen.csv`: 3 ERROR por «falta dataset de producción (gitignored)»); no hay Plan B declarado para el anteproyecto | `ejecucion_resumen.csv`; maestro §3 |
| **Argumento de «por qué este problema no está ya resuelto y publicado con esos mismos datos»** | ✗ **Ausente.** Los materiales demuestran que *ellos* ya hicieron análisis sobre estos datos, pero no argumentan que el problema no esté ya resuelto/publicado por otros (el SotA §13.2 documenta estudios colombianos previos, lo que obliga a diferenciarse explícitamente) | SotA §04 y §13.2 |

### Vacíos (materiales) y qué añadir para EJEMPLAR
1. Declarar la **licencia/condiciones de uso** de los dos datasets (verificar en la página del dataset en datos.gov.co y citarla) — requisito explícito de la modalidad datos abiertos.
2. Tabla formal **objetivo específico → variables → método → salida esperada** (los materiales contienen las piezas en `catalogo.yaml` y el SotA §12; falta ensamblarla).
3. Redactar la **ruta metodológica con alternativa descartada con razón** (los materiales tienen las alternativas; falta el argumento de selección por específico).
4. Escribir el **Plan B si el dato no llega** (p. ej., trabajar con el consolidado XLSX versionado 3/6 convocatorias o el CSV 6/6 ya descargado — material que de hecho existe en el repo —, o restringir alcance; y declararlo).
5. Escribir el **argumento de novedad** («no está resuelto y publicado con esos datos») diferenciándose de los estudios colombianos ya citados en §13.2.

---

## 5. D5 — Alcance, viabilidad y plan de trabajo (5 %)

### Nivel asignado: EN DESARROLLO (60 %)

### Qué pide el «Ejemplar» y qué hay

| Requisito Ejemplar | Estado | Evidencia concreta |
|---|---|---|
| Declara explícitamente **qué hará y qué no**, con la **razón de cada exclusión** | ✅ Cumplido (para el proyecto previo; reutilizable con adaptación). 5 exclusiones con razón: sin recolección primaria ni validación contra registros internos; sin modelos predictivos de alto riesgo ni causales; sin convocatorias posteriores a 2021; sin análisis cualitativo; sin big data distribuida | Informe §4.1 (líneas 270–283) |
| **Cronograma por hitos** con **entregables verificables** y **holgura** | ✗ **No cumplido.** Solo hay tabla de 3 fases con rangos de semanas (I: 1–3; II: 4–8; III: 9–12) y «productos clave»; sin hitos intermedios, sin entregable verificable por hito, sin holgura, y es el cronograma del proyecto ya ejecutado, no uno del semestre del anteproyecto | Informe §3.3 (líneas 256–262) |
| Identifica **2–3 riesgos concretos con su plan de contingencia** | ✅ **Cumplido con exceso** (12 riesgos L1–L12 con mitigación en informe §4.2) — pero están calibrados al proyecto previo (mojibake, CI/CD, DuckDB…); para el anteproyecto hay que **priorizar 3** y adaptar la contingencia al semestre real | Informe §4.2 (líneas 285–301); `ejecucion_resumen.csv` (10/16 OK, 6 ERROR — evidencia empírica de riesgos de reproducibilidad y datos) |
| **Alcance coherente con las horas reales del semestre** | ✗ **No verificable.** Ningún material estima horas disponibles/integrante/semana; la línea de tiempo de commits muestra un patrón de trabajo real disperso con hiato nov-2025–feb-2026 (`commits_timeline.csv`), que debería informar el presupuesto de tiempo | `commits_timeline.csv`; `validacion_rubrica.md` §5 |

### Vacíos (materiales) y qué añadir para EJEMPLAR
1. Construir cronograma **por hitos semanales/quincenales con entregable verificable** (tabla de hitos: H1…Hn, fecha, entregable, criterio de aceptación) y **holgura explícita** (al menos 1–2 semanas de colchón).
2. Presupuesto de horas por integrante (cuántas horas reales por semana × semanas del semestre) y demostrar que el alcance cabe (la pregunta de la rúbrica: «¿cuántas horas por semana le puede dedicar cada uno de verdad?»).
3. Re-declarar exclusiones del *anteproyecto* (no las del informe de auditoría previa, aunque varias se reutilizan) y priorizar 2–3 riesgos con contingencia específica (p. ej., R1: la API Socrata cambia/cae → usar consolidados ya descargados; R2: sobrecarga de OE con 5 métodos → recorte de ejes por decisión previa; R3: disponibilidad del equipo → holgura + mínimos por hito).

---

## 6. Hallazgos transversales

1. **Los materiales son de alta calidad como evidencia empírica, pero están orientados a un proyecto ya terminado (2026-I), no al anteproyecto (2026-II).** Casi todo lo que la rúbrica pide «redactado» (problema con actor/frecuencia/consecuencia, pregunta estadística, objetivos nuevos, cronograma por hitos del semestre, argumento datos abiertos de pertinencia y novedad) no existe en ninguna pieza; lo que sí existe es la materia prima verificada (cifras, diccionario de datos, decisiones metodológicas, literatura).
2. **Los dos criterios bloqueantes (D1 y D3) son los que menos contenido redactable directo tienen** → si el equipo solo «arma» el anteproyecto con los materiales sin redactar problema y objetivos, D1 y D3 quedan en el límite INSUFICIENTE y el anteproyecto **se devuelve** aunque la nota global pase de 3,0 (rúbrica pág. 3).
3. **El SotA es el material más maduro para D2 (0 fabricadas, organizado por enfoque, 39+14 referencias verificables), pero falla en lo que la rúbrica vigila primero: citación APA 7 (hoy plainnat) y contraste explícito de enfoques + vacío declarado** — defectos de formato y de estructura argumentativa, no de contenido.
4. D4 es el único criterio en nivel COMPETENTE: procedencia, periodo, unidad, volumen, acceso y diccionario de variables están verificados en el repositorio; faltan solo licencia, plan B, tabla objetivo→variables y el argumento de novedad.
5. D5 tiene el mejor «insumo de riesgos» (12 riesgos con mitigación) pero el peor «plan»: no hay cronograma por hitos, ni holgura, ni presupuesto de horas — todo por construir.

---

## 7. Los 3 hallazgos más importantes

1. **D1 (bloqueante) parte casi de cero en lo formal:** existe una base cuantitativa propia excepcional (77 237 registros, 51 % de concentración, 36,9 % de cobertura del padrón, 10/16 scripts reproducibles…), pero **no hay problema declarado con actor/alcance/frecuencia/consecuencia, no hay pregunta estadística respondible y no hay fuente externa de magnitud en Colombia** que sostenga la pertinencia en modalidad datos abiertos. Sin esos tres párrafos redactados, D1 no aprueba la puerta.
2. **D3 (bloqueante) no puede heredarse:** los objetivos existentes documentan la consultoría ya ejecutada, mezclan logros con actividades del cronograma («ampliar», «robustecer», «reparar CI/CD») y no responden a un problema de D1 que aún no existe; si se copian tal cual, el anteproyecto se devuelve por D3. Hay que re-escribir general + 3–5 específicos con verbos verificables, evidencia de cumplimiento y sin solapamiento.
3. **El SotA (D2) es un activo real pero requiere conversión APA 7 + re-enfoque:** 0 referencias fabricadas (confirmado), organización por enfoque correcta y material colombiano aprovechable; sin embargo la citación es plainnat autor-año (no APA 7, requisito explícito del entregable), no contrasta dos enfoques señalando supuestos, no declara el vacío del proyecto nuevo y sus referencias cruzadas internas están desactualizadas en el PDF (dice «sección 12.2» donde hoy es §13.2).

---

## Anexo A — Confirmación del riesgo de «referencias inventadas» (D2)

**Veredicto: 0 referencias fabricadas. Riesgo actual: no detectado.**
- `validacion_sota_referencias.md` (validación previa, archivada en `data/validacion/`) verificó 27 entradas canónicas + 16 recursos URL: 26/27 correctas (1 error de medio histórico —Theil como `@article`— **ya corregido** a `@book` en el `refs.bib` actual, líneas 229–234) y los 16 URLs reales; ninguna obra inventada.
- Las **12 entradas añadidas** en revisión (Sinatra et al. 2016 *Science* aaf5239; Deville et al. 2014 *PNAS*; Petersen et al. 2012 *PNAS*; Barabási & Albert 1999 *Science*; Frenken et al. 2009 *J. Informetrics*; Waltman 2016 *J. Informetrics*; van Buuren 2018; Christen 2012; Rocher et al. 2019 *Nature Communications*; Segel & Heer 2010 *IEEE TVCG*; Cañibano & Bozeman 2009 *Research Policy*; Mena-Chalco 2009 ScriptLattes) **no están cubiertas por la validación archivada** (que se hizo con 27 entradas); verifiqué por lectura que son obras reales y canónicas con metadatos correctos (autoría/año/revista/páginas coinciden con la literatura establecida). Recomendación: ejecutar la verificación empírica web de esas 12 antes de la entrega para dejar el «0 fabricadas» cerrado al 100 % con trazabilidad.
- Detalles menores de metadatos (no fabricación): «Kimberle Crenshaw» sin tilde en `refs.bib:215` (APA: Kimberlé); `wilsdon2015metric` como `@techreport` con «James Wilsdon and others» (pierde coautores); `coara2022`/`dora2012` como autor corporativo. Nada que impida rastrear la fuente.

---

*Fin de la validación. No se modificó ningún archivo del equipo ni del repositorio; los archivos temporales de extracción (`_scratch_*.txt`) se eliminarán tras la entrega de este informe.*
