# VALIDACIÓN EXTERNA — BLOQUE DOCUMENTO (D1–D5)
**Anteproyecto**: *Auditoría estadística reproducible del sistema de reconocimiento de investigadores de MinCiencias (2013–2021) con datos abiertos y propuesta de mejora para su observatorio* — Grupo 8 (Chaparro, Muñoz, Triana), Consultoría Estadística USTA 2026-II, modalidad **datos abiertos**.

**Evaluador**: jurado externo independiente (simulación de sustentación).
**Fuentes leídas**: `rubrica_texto.txt` (rúbrica oficial, fuente de verdad) y `anteproyecto_texto.txt` (documento evaluado). Respaldo factual puntual en el repositorio `Observatorio_Ministerio_de_Ciencias_Grupo8` (solo para contrastar hechos, no se evalúa).
**Fecha de validación**: 6 de septiembre de 2026.

---

## 1. Requisitos de forma (pre-check)

| Requisito | Estado | Evidencia |
|---|---|---|
| Portada con nombres de los 3 integrantes | ✅ | Pág. 1 del PDF: Kevin Leonardo Chaparro Reyes, Valentina Muñoz Palma, Paula Margarita Triana Ancinez. |
| Estructura problema / estado del arte / objetivos / datos y método / alcance-riesgos-cronograma | ✅ | Secciones 1→5 exactamente en ese orden; sección 6 (IA y reparto) adicional, como pide la rúbrica para S3. |
| Extensión del cuerpo 6–10 págs. **sin** portada ni referencias | ✅ | PDF de 12 págs.: 1 portada + 1 índice + **8 págs. de cuerpo** (págs. PDF 3–10) + 2 págs. de referencias. Contando el índice como página del documento serían 9: **en ambos conteos cae en 6–10**. |
| Declaración de IA y reparto del trabajo | ✅ | Sección 6.1 (reparto por rol) y 6.2 (declaración específica con casos de lo descartado). Corresponde a S3, no a D, pero se constata. |

---

## 2. Tabla resumen del bloque Documento

Pesos oficiales del curso: D1 = 12 %, D2 = 9 %, D3 = 8 %, D4 = 6 %, D5 = 5 % (Σ = 40 %). Para expresar la nota del bloque en 0–5 se normalizan al bloque (D1 30 %, D2 22,5 %, D3 20 %, D4 15 %, D5 12,5 %).

| Criterio | Peso | Nivel | Puntos (sobre 5,0) | Justificación |
|---|---|---|---|---|
| **D1** Problema, contexto y estado actual (⛔ bloqueante) | 30 % | **Ejemplar** | **1,50** | Problema con actor, alcance, frecuencia y consecuencia; distinguido de sus síntomas; estado actual cuantificado con cifras propias verificadas (sec. 1.1–1.2); pregunta estadística respondible (1.3); pertinencia argumentada para modalidad datos abiertos. |
| **D2** Estado del arte y rigor bibliográfico | 22,5 % | **Competente** | **0,90** | Revisión por enfoques (2.1–2.3), contraste explícito de supuestos (2.4), vacío declarado, mundo vs. Colombia; ≈28 referencias verificables y **ninguna fabricada** (contrastadas 8 en web). No llega a Ejemplar por errores menores de citación APA 7 (título incompleto en Cañibano & Bozeman; referencia huérfana Rocher et al. 2019). |
| **D3** Objetivos, general y específicos (⛔ bloqueante) | 20 % | **Ejemplar** | **1,00** | General responde exactamente al problema (3.1); 3 específicos secuenciales, verbos verificables y evidencia de cumplimiento declarada para cada uno (3.2). |
| **D4** Datos y aproximación metodológica preliminar | 15 % | **Ejemplar** | **0,75** | Fuentes con procedencia, periodo, unidad de observación, volumen **verificado**, acceso y licencia (Tabla 1, 4.1); variables por objetivo (4.2); ruta metodológica con alternativa descartada y plan si el dato no llega (4.3–4.4). |
| **D5** Alcance, viabilidad y plan de trabajo | 12,5 % | **Ejemplar** | **0,625** | Sí/no con razón de exclusión (5.1); 3 riesgos con contingencia (5.2); cronograma por hitos con entregables verificables, holgura y horas (5.3). |
| **TOTAL BLOQUE D** | 100 % | — | **4,78 / 5,00** | — |

---

## 3. Análisis criterio por criterio

### D1 — Problema, contexto y estado actual · peso 12 % · **Ejemplar (logro 1,0 → 5,0)** · 1,50/5,0 en el bloque

- **Actor, alcance, frecuencia y consecuencia explícitos (sec. 1.1)**: "Desde 2013, el Ministerio de Ciencia, Tecnología e Innovación de Colombia (MinCiencias) reconoce periódicamente a los investigadores activos del país a través de convocatorias nacionales (640/2013, 693/2014, 737/2015, 781/2017, 833/2018 y 894/2021)". Actor afectado declarado: "a MinCiencias y al SNCTI… a los investigadores reconocidos… a los tomadores de decisión de política de CTI".
- **Distingue problema de síntoma**: "Este problema no es un síntoma ni una preferencia metodológica: es una pregunta sobre la validez de un instrumento público de medición" (sec. 1.1).
- **Cifra propia cuantificada, no tomada de informe general (sec. 1.2 "evidencia propia")**: "el dataset público bqtm-4y2h declara 77 237 registros y 6 convocatorias… la verificación directa muestra solo 50 891 filas y 3 convocatorias"; "22 registros con edad mayor a 100 años (máximo 956)"; "Bogotá y Antioquia concentran el 51 %"; "retención de Bogotá alcanza el 92 %"; brecha de género "24 % de mujeres en Ingeniería frente a 48 %"; subrepresentación afro 3×, indígena 7,9×, discapacidad 8×; "solo el 36,9 % de los autores únicos… son investigadores reconocidos". **Contraste de respaldo**: el repositorio confirma la base de esa evidencia (`datos/auditoria/calidad_resumen.json`: `"n_total": 50891`; 133 commits en git, como declara la sec. 6.2).
- **Consecuencia de no intervenir (sec. 1.3)**: "si nadie hace nada, el país seguirá tomando decisiones de política de ciencia sobre un registro cuya calidad no ha sido auditada… con el riesgo de perpetuar inequidades y de basar evaluaciones individuales en datos no comparables".
- **Pregunta estadística respondible (sec. 1.3)**: enunciada en forma interrogativa y desglosable en las tres dimensiones (fiabilidad / comparabilidad / equidad).
- **Modalidad datos abiertos**: la pertinencia se argumenta explícitamente ("A quién le importa…") y se sostiene con análisis colombianos recientes (Categorización… SNCTI, 2023; Revista CTS, 2010; CONPES 4069).
- **Veredicto del bloqueante D1**: **CUMPLE con nivel Ejemplar**. Observación menor: las cifras propias se declaran "verificables… con métodos reproducibles" sin mostrar la ruta de reproducción dentro del anteproyecto; conviene tenerla lista (repositorio) para la sustentación.

### D2 — Estado del arte y rigor bibliográfico · peso 9 % · **Competente (logro 0,8 → 4,0)** · 0,90/5,0 en el bloque

**Lo que alcanza el nivel Ejemplar en contenido:**
- Organización **por enfoque, no por autor** (sec. 2.1 ciencia de la ciencia/evaluación responsable; 2.2 calidad de datos y dinámica longitudinal; 2.3 desigualdad/género/diversidad/redes).
- **Contraste de dos aproximaciones con diferencia de supuestos** (sec. 2.4): "las cadenas de Markov suponen que la transición depende solo del estado actual (homogeneidad), mientras los modelos de supervivencia modelan el tiempo hasta el evento con covariables y censura".
- **Vacío declarado y ligado al proyecto** (sec. 2.4): "no se ha publicado una auditoría estadística reproducible del padrón… que combine… calidad + trazabilidad longitudinal + equidad…; lo publicado en Colombia es descriptivo o normativo".
- Distingue lo hecho en el mundo de lo hecho en Colombia (sec. 2.1).
- Fuentes: ≈28 referencias en la lista; muy por encima de las ≥8 recientes y verificables exigidas.

**Por qué NO es Ejemplar (citación APA 7 "sin errores" no se cumple):**
1. **Título bibliográfico incompleto/alterado**: la entrada *Cañibano & Bozeman (2009)* figura como "Curriculum vitae method in science policy research", pero el título real (verificable en Semantic Scholar/Research Policy) es "Curriculum vitae method in science policy **and research evaluation: the state-of-the-art**". Revista, volumen, páginas y DOI sí son correctos → la fuente es rastreable.
2. **Referencia huérfana**: *Rocher, Hendrickx & de Montjoye (2019)* aparece en la lista de referencias pero **no se cita en ningún punto del cuerpo** (verificado por búsqueda en todo el texto). APA 7 exige correspondencia lista–texto.
3. **Forma**: la entrada SciELO ("Categorización de grupos e investigadores…", 2023) muestra la URL con un espacio interno ("script=sci abstract") y la citación en texto se hace por el título completo, estilo poco estándar.

**Verificación de referencias inventadas (penalización de la rúbrica: una inexistente ⇒ D2 Insuficiente) — NO se encontró ninguna fabricada.** Se contrastaron en web las más riesgosas:

| Referencia del documento | Resultado de la verificación |
|---|---|
| Categorización de grupos e investigadores… (2023), *Universidad y Sociedad*, 15(5) | **Existe** (SciELO Cuba, pid S2218-36202023000500133) |
| Revista CTS (2010), "Dos países latinoamericanos…", 5(13) | **Existe y verificable** (PDF oficial revistacts.net, vol. 5, nro. 13) |
| Souza et al. (2023), arXiv 2308.09004 | **Existe** (arXiv/ADS) |
| Cañibano & Bozeman (2009), *Research Policy* 38(2) 259–266 | **Existe**, con título real ligeramente distinto (ver arriba) |
| Dataset MinCiencias 33dq-ab5a (producción de grupos) | **Existe** en datos.gov.co (API/Socrata) |
| Dataset MinCiencias bqtm-4y2h (padrón) | Verificable (URL oficial en el documento; estructura de variables corroborada en fuentes académicas que usan el mismo padrón) |
| Rocher et al. (2019), *Nature Communications* 10, 3069 | **Existe** (artículo real), pero **no citado en el cuerpo** |
| Clásicos (Kemeny & Snell 1976; Theil 1967; Newman 2001; Wang & Strong 1996; Crenshaw 1989) | Reales, entradas correctas |

**Regla del propio docente** ("Si dudan entre dos niveles, están en el de abajo") refuerza Competente: el contenido es Ejemplar, pero la higiene citacional tiene defectos reales (aunque menores y que no impiden rastrear, que es el umbral de Insuficiente). **No aplica la pena de Insuficiente por referencias inventadas.**

### D3 — Objetivos · peso 8 % · **Ejemplar (logro 1,0 → 5,0)** · 1,00/5,0 en el bloque

- **General (3.1) coherente con el problema, sin desbordarlo**: "Cuantificar y auditar de forma reproducible la fiabilidad, comparabilidad y equidad del padrón de investigadores reconocidos de MinCiencias (convocatorias 2013–2021)… y entregar un marco de indicadores y un tablero de auditoría…". El propio texto argumenta la correspondencia exacta con la pregunta de 1.3 (ni más ancho ni más angosto). El componente de entregables (marco + tablero) responde a la segunda parte de la pregunta ("qué mejoras… permitirían convertirlo en la base de un observatorio").
- **Tres específicos (dentro del rango 3–5), verbos verificables y evidencia declarada** (3.2):
  - OE1 "**Cuantificar** la calidad del registro… Evidencia de cumplimiento: tabla de indicadores de calidad por convocatoria con conteos verificables… y código reproducible que la genera".
  - OE2 "**Estimar** la dinámica longitudinal… Evidencia: matrices de transición con IC, curvas de Kaplan–Meier y un modelo de Cox con covariables".
  - OE3 "**Cuantificar** la equidad… Evidencia: tabla de indicadores… con intervalos de confianza y figura resumen".
- **Secuencia visible y sin solape**: "sin el registro limpio (OE1) no hay panel longitudinal fiable (OE2), y sin ambos no hay lectura de equidad comparable (OE3)".
- **Veredicto del bloqueante D3**: **CUMPLE con nivel Ejemplar**. Observación menor: cuidar en la sustentación la posible lectura de que el "tablero" es un entregable de producto y no parte del logro analítico (está justificado, pero conviene declararlo como medio para el fin del observatorio).

### D4 — Datos y aproximación metodológica preliminar · peso 6 % · **Ejemplar (logro 1,0 → 5,0)** · 0,75/5,0 en el bloque

- **Fuentes con procedencia, periodo, unidad de observación, volumen, acceso y licencia (Tabla 1, sec. 4.1)**: entidad (MinCiencias), identificador Socrata (bqtm-4y2h / 33dq-ab5a), enlace, periodo 2013–2021, unidad de observación (Investigador × convocatoria; Producto × autor), volumen **declarado y verificado** ("el XLSX del clon tiene 50 891"), variables, acceso (API Socrata / CSV, sin autenticación), licencia y llave de cruce. Cumple el estándar de la modalidad datos abiertos (procedencia + licencia + enlace directo + verificación real de que existe).
- **Variables ligadas a cada objetivo específico (4.2)**: OE1 (ID PERSONA PR, ANO CONVO, EDAD…), OE2 (ID CLAS PR/NME CLASIFICACION…), OE3 (NME DEPARTAMENTO, NME GENERO, TXT GRUPO ETNICO, TXT POBLACION DISCA, ID VICTIMA…).
- **Ruta metodológica ligada a los objetivos (4.3)**: flujo en 3 etapas (calidad → longitudinal → equidad) con técnicas nombradas y ligadas a OE; herramientas declaradas (Python, DuckDB, versionado reproducible).
- **Alternativa considerada y descartada con razón**: índice h "se descartó… porque el cruce de 3,2 millones de filas requiere descargar 1,2 GB y su disponibilidad es intermitente, y porque el objetivo de esta entrega es la auditoría del padrón".
- **Plan si el dato no llega o cambia (4.3)**: OE1–OE3 no dependen del dataset de producción; contratos de esquema para cambios del padrón.
- **Por qué no está ya resuelto (4.4)**: requisito específico de la modalidad datos abiertos, cumplido (no existe auditoría reproducible publicada que combine las tres dimensiones y documente los defectos).

### D5 — Alcance, viabilidad y plan de trabajo · peso 5 % · **Ejemplar (logro 1,0 → 5,0)** · 0,625/5,0 en el bloque

- **Qué sí y qué no, con razón de cada exclusión (5.1)**: 4 exclusiones declaradas y justificadas (validación contra registros internos no accesibles; modelos predictivos/causalidad fuera del alcance semestral; índice h por el dataset de 1,2 GB; convocatorias posteriores a 2021).
- **Riesgos concretos con contingencia (5.2)**: 3 riesgos (discrepancia 77 237 vs. 50 891 ya detectada y convertida en hallazgo; producción no descargable; tiempo insuficiente) cada uno con su plan.
- **Cronograma por hitos con entregables verificables (5.3)**: 12 semanas, 7 hitos con entregables nombrados (scripts + catálogo, tabla de indicadores, matrices con IC, KM + Cox, indicadores de equidad con IC, tablero + marco, informe final); holgura declarada ("semanas 6 y 11… 2 semanas acumuladas") y presupuesto de horas: 216 disponibles vs. 180 estimadas (17 % de holgura), coherente con el semestre.
- Observación menor: la nota "(Ajustable a la dedicación real declarada por cada integrante)" introduce un matiz de provisionalidad; el supuesto "6 h semanales × 3 integrantes" debería confirmarse con la dedicación real en la sustentación.

---

## 4. Verificación de los hechos que la rúbrica penaliza (resumen)

1. **Extensión del cuerpo**: ✅ 8 págs. (u 8–9 contando el índice) dentro de 6–10, sin contar portada ni referencias.
2. **APA 7 en referencias**: ⚠️ Errores **menores** que no impiden rastrear ninguna fuente (título incompleto de Cañibano & Bozeman 2009; Rocher et al. 2019 huérfana; forma/URL de la entrada SciELO). Ninguna referencia impide rastrear el original → no se activa Insuficiente.
3. **Referencias inventadas**: ✅ **No se detectó ninguna** entre las 8 contrastadas en web (SciELO 2023, Revista CTS 2010, Souza et al. 2023, Cañibano & Bozeman 2009, Rocher et al. 2019, datasets 33dq-ab5a/bqtm-4y2h, clásicos).
4. **Objetivos verificables (D3)**: ✅ Verbos verificables y evidencia de cumplimiento explícita por objetivo.
5. **D1 y D3 bloqueantes**: ✅ Ambos en Ejemplar → la **puerta de aprobación está abierta**.

---

## 5. Cálculo de la nota del bloque Documento

**Fórmula oficial** (rúbrica): `nota ponderada = Σ (logro × peso) × 5`.

| Criterio | Logro (0–1) | Peso (curso) | Aporte (curso) | Nota 0–5 | Peso normalizado al bloque | Puntos en el bloque (0–5) |
|---|---|---|---|---|---|---|
| D1 | 1,0 | 0,12 | 0,120 | 5,0 | 30 % | 1,500 |
| D2 | 0,8 | 0,09 | 0,072 | 4,0 | 22,5 % | 0,900 |
| D3 | 1,0 | 0,08 | 0,080 | 5,0 | 20 % | 1,000 |
| D4 | 1,0 | 0,06 | 0,060 | 5,0 | 15 % | 0,750 |
| D5 | 1,0 | 0,05 | 0,050 | 5,0 | 12,5 % | 0,625 |
| **Total** | — | **0,40** | **0,382** | — | 100 % | **4,775** |

- **Nota del bloque Documento (escala 0–5)**: Σ(logro × peso normalizado) × 5 = **4,775 ≈ 4,78 / 5,00**.
- **Aporte del documento a la nota final del curso** (fórmula directa con pesos del curso: Σ(logro × peso_curso) × 5): **1,91 de 2,0 puntos máximos** (el Documento vale 40 % de la asignatura).

---

## 6. Veredicto

# ✅ APROBADO CON OBSERVACIONES — Nota del bloque Documento: **4,78 / 5,00**

- Pasa la **puerta de aprobación**: D1 (problema) y D3 (objetivos), los dos criterios **bloqueantes**, quedan en **Ejemplar** — no hay devolución a corrección.
- Ningún criterio en Insuficiente; no hay referencias fabricadas; extensión, portada y estructura en regla.
- La observación que impide el 5,0 pleno es de **rigor bibliográfico formal (D2, Competente)**: el contenido del estado del arte es de nivel Ejemplar (enfoques, contraste de supuestos, vacío, mundo/Colombia), pero la citación APA 7 no está libre de errores.

---

## 7. Correcciones accionables, priorizadas

1. **(Alta · D2)** Corregir el título de la entrada *Cañibano & Bozeman (2009)* al título real: "Curriculum vitae method in science policy and research evaluation: the state-of-the-art" (mantener revista/volumen/páginas/DOI, que están correctos).
2. **(Alta · D2)** Resolver la referencia huérfana *Rocher et al. (2019)*: o citarla en el cuerpo donde corresponde — encaja en la sección 6.3 como soporte técnico de la decisión de "no publicar microdatos identificables" (riesgo de re-identificación) — o retirarla de la lista.
3. **(Media · D2/forma)** Sanear la entrada SciELO de "Categorización de grupos e investigadores… (2023)": revisar la URL (aparece con espacio interno "script=sci abstract") y normalizar la citación en texto (autor/título corto) conforme a APA 7.
4. **(Media · D1/sustentación)** Preparar la evidencia reproducible de las cifras propias de la sección 1.2 (scripts + salidas del repositorio, incluido `calidad_resumen.json` con `n_total = 50891`) para mostrarla en la sustentación; el anteproyecto las declara verificables pero no muestra la ruta.
5. **(Baja · D5)** Confirmar la dedicación horaria real por integrante (el presupuesto asume 6 h × 3 × 12 semanas) y retirar el matiz "(Ajustable a la dedicación real…)" para que el alcance sea defendible tal como está escrito.
6. **(Baja · D3)** En la sustentación, explicitar que el "marco de indicadores y tablero" del objetivo general es el medio para la mejora del observatorio (segunda parte de la pregunta), no un ensanchamiento del problema.

*Nota metodológica de la auditoría: la evaluación de formato APA 7 se hizo sobre el texto plano extraído del PDF, en el que no es posible verificar cursivas ni saltos de línea reales; los hallazgos citacionales son los verificables en esa forma y vía búsqueda web.*
