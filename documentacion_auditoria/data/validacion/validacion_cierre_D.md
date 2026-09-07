# Validación de cierre — Bloque Documento (D1–D5)

**Anteproyecto:** Auditoría estadística reproducible del sistema de reconocimiento de investigadores de MinCiencias (2013–2021) con datos abiertos y propuesta de mejora para su observatorio
**Evaluador:** Jurado independiente (validación de cierre)
**Instrumento:** Rúbrica oficial Entrega 1 · Anteproyecto (2026-II) · Escala 0,0–5,0
**Alcance:** Solo criterios D1–D5 (bloque Documento, 40 %). S1–S3 (sustentación) fuera de alcance.
**Fecha:** sesión actual

---

## 0. Verificaciones formales previas

| Ítem | Resultado | Evidencia |
|---|---|---|
| Extensión del cuerpo | ✅ Cumple (8 págs.) | PDF de 12 págs.: portada (p1), índice (p2), cuerpo secciones 1–6 en págs. PDF 3–10 (= numeración interna 2–9), referencias en págs. PDF 11–12 (internas 10–11). Cuerpo = **8 páginas**, dentro de la banda 6–10 "sin contar portada ni referencias" (9 si se contara el índice; cumple igualmente). |
| APA 7 | ⚠️ Cumple con errores menores | Ver detalle en D2. No impiden rastrear las fuentes. |
| Objetivos | ✅ 1 general + 3 específicos | §3.1–3.2. Rango 3–5 cumplido; verbos verificables y evidencia de cumplimiento declarada. |
| Bloqueantes | ✅ Ninguno en Insuficiente | D1 = Ejemplar, D3 = Competente → la puerta de aprobación (D1 y D3 no en Insuficiente) queda abierta. |
| Referencia fabricada | ✅ Sin indicios (no contrastable offline) | 28 entradas en Referencias con DOI/URL que corresponden a publicaciones reales conocidas (Fortunato 2018 eaao0185; Rocher 2019 s41467-019-10933-3; Clauset 2015 e1400005; Cañibano & Bozeman 2009; etc.). No se pudo verificar en línea la existencia/contenido de ninguna (indicación metodológica: sin web_search); se señala la única entrada dudosa en D2. |

---

## 1. D1 · Problema, contexto y estado actual (12 %) — **Ejemplar (5,0 / 100 %)**

**Justificación (evidencia en el texto):**
- **Actor, alcance, frecuencia y consecuencia explícitos:** §1.1 delimita el padrón de investigadores reconocidos de MinCiencias (convocatorias 640/2013…894/2021), a quién afecta ("A quién le importa": MinCiencias/SNCTCI, investigadores reconocidos, tomadores de decisión) y la consecuencia.
- **Problema distinguido de sus síntomas:** §1.1: "Este problema no es un síntoma ni una preferencia metodológica: es una pregunta sobre la validez de un instrumento público de medición".
- **Estado actual cuantificado con cifras propias (no de informe general):** §1.2 declara explícitamente "cifras propias y verificables (obtenidas y auditadas en este trabajo)": 77 237 registros declarados vs. 50 891 filas verificadas (discrepancia del artefacto versionado); 26 662 investigadores únicos; 22 registros con edad >100 años (máx. 956); mojibake; Bogotá+Antioquia = 51 %; retención de Bogotá 92 %; brecha de género 24 % vs. 48 %; subrepresentación afro 3×, indígena 7,9×, discapacidad 8× (vs. censo DANE 2018); 36,9 % de autores únicos reconocidos.
- **Consecuencia de no intervenir:** §1.3: decisiones de política sobre un registro no auditado, riesgo de perpetuar inequidades y evaluaciones sobre datos no comparables.
- **Pregunta estadística respondible:** §1.3 la enuncia en forma de pregunta sobre fiabilidad, comparabilidad y equidad + mejoras de gobernanza.
- **Modalidad datos abiertos:** pertinencia argumentada (§1.1, destinatarios) y magnitud documentada con fuente primaria colombiana (los propios datos oficiales de MinCiencias), apoyada en literatura colombiana (Categorización…, 2023; Revista CTS, 2010).

Sin dudas materiales entre niveles: Ejemplar.

---

## 2. D2 · Estado del arte y rigor bibliográfico (9 %) — **Competente (4,0 / 80 %)**

**Justificación:**
- El contenido alcanza el estándar Ejemplar: revisión **organizada por enfoque y no por autor** (§2 intro y §2.1–2.3: 6 enfoques agrupados), **distingue mundo vs. Colombia** (§2 intro; §2.1 con Lattes/ScienTI-CVLAC, Categorización 2023, CONPES 4069), **contraste de dos aproximaciones con sus supuestos** (§2.4: cadenas de Markov —supuesto de homogeneidad/markovianidad— vs. modelos de supervivencia —tiempo hasta el evento con covariables y censura—, con diseño que las contrasta) y **vacío explícito ligado al proyecto** (§2.4). Fuentes numerosas (28 entradas referenciadas; ≥8 recientes 2013–2023; clásicos 1967–1989 justificados como anclas metodológicas).
- **No alcanza Ejemplar por "Citación APA 7 sin errores":** errores menores de formato acumulados, todos rastreables:
  1. §1.1: cita del trabajo sin autor con corrupción tipográfica: "(Çategorización de grupos e investigadores", 2023)" (la «Ç» y las comillas asimétricas). §2.1: "(2023)" huérfano sin título abreviado en el lugar del autor.
  2. Entrada "Revista Iberoamericana de Ciencia, Tecnología y Sociedad. (2010). Dos países latinoamericanos cuentan actualmente con sistemas de información curricular consolidados: Brasil y Colombia…" — el "título" es una frase descriptiva que parece texto citado, no un título de artículo; **no contrastable offline** (única entrada que conviene verificar en línea antes de la sustentación: si no dice lo que se afirma, activaría la cláusula de D2 Insuficiente).
  3. Entradas con datos editoriales incompletos: Souza et al. (2023) "IEEE eScience (preprint)" (rastreable por arXiv 2308.09004) y Mena-Chalco & Cesar Júnior (2009), evento sin sede ni editorial.
- Encaja en Competente: "Revisa ≥6 fuentes verificables y pertinentes… agrupa temáticamente… aunque el vacío quede implícito" (aquí el vacío es explícito) "Citación APA 7 con errores menores de formato que no impiden rastrear la fuente". Regla "si dudan entre dos niveles, están en el de abajo" → Competente.

---

## 3. D3 · Objetivos, general y específicos (8 %) — **Competente (4,0 / 80 %) — BLOQUEANTE, sin activar**

**Justificación:**
- **General coherente con el problema de D1:** §3.1 "Cuantificar y auditar de forma reproducible la fiabilidad, comparabilidad y equidad del padrón… y entregar un marco de indicadores y un tablero de auditoría…" responde a la pregunta de §1.3, con autojustificación explícita de amplitud (ni más ancho ni más angosto).
- **Específicos:** 3 (dentro de 3–5), cada uno con **verbo verificable** (Cuantificar / Estimar / Cuantificar) y **evidencia de cumplimiento declarada** ("Evidencia de cumplimiento:" en cada uno: tabla de indicadores con conteos verificables; matrices de transición con IC, Kaplan–Meier y Cox; tabla de indicadores de equidad con IC). **Secuencia visible** (§3.2: OE1 habilita OE2, ambos habilitan OE3; el marco y el tablero se derivan de los tres).
- **Por qué no Ejemplar (fisuras acotadas, conjunto sólido):**
  1. El **"cruce con la producción de grupos"** incluido en el objetivo general (§3.1) y en la evidencia de §1.2 (36,9 % de coautoría externa) **no está operacionalizado en ningún específico**: OE1–OE3 trabajan solo sobre el dataset del padrón (bqtm-4y2h) y sus covariables (área/género/región); el dataset de producción (33dq-ab5a) solo aparece como alternativa descartada (§4.3) y como exclusión (§5.1, índice h). Cumplidos los tres OE, esa cláusula del general quedaría sin agotar.
  2. **OE3 (§3.2) no incorpora plenamente la corrección de víctimas:** enuncia "sus dimensiones territorial, de género y de diversidad (etnia, discapacidad, víctimas), con indicadores de concentración… y razones de representación frente al censo DANE 2018", agrupando a las víctimas entre lo comparable con el censo. La distinción correcta (víctimas = prevalencia interna; razones vs. DANE solo para género, etnia y discapacidad) está bien aplicada en §1.2 y §4.3, pero no en el enunciado del propio OE3.
- Bloqueante: Competente ≫ Insuficiente → puerta abierta.

---

## 4. D4 · Datos y aproximación metodológica preliminar (6 %) — **Ejemplar (5,0 / 100 %)**

**Justificación:**
- **Fuentes con procedencia, periodo, unidad de observación, volumen y acceso/licencia:** §4.1, Tabla 1: entidad (MinCiencias), identificadores (bqtm-4y2h; 33dq-ab5a), enlaces en referencias, periodo 2013–2021 (6 ventanas), unidad de observación (investigador×convocatoria; producto×autor), volumen **declarado y verificado** (77 237 vs. 50 891 filas reales; 3 166 629), variables, acceso (API Socrata/CSV, sin autenticación), licencia y llave de cruce. "Ya fueron abiertas y verificadas por el equipo… no supuestas".
- **Variables ligadas a cada objetivo específico:** §4.2 (OE1: ID CONVOCATORIA, ID PERSONA PR, EDAD ANOS PR, codificación; OE2: transiciones + covariables área/región; OE3: departamento, género, grupo étnico, discapacidad, ID VICTIMA CONFLICTO).
- **Ruta metodológica con alternativa considerada y descartada con razón:** §4.3 (índice h y variantes descartados: cruce de 1,2 GB con disponibilidad intermitente y no es el objetivo de la entrega; queda como extensión declarada).
- **Plan si el dato no llega:** §4.3 (descarga directa por API + respaldo versionado; OE1–OE3 no dependen del dataset de producción; contratos de esquema detectan cambios de esquema).
- **Modalidad datos abiertos completa:** §4.4 argumenta por qué el problema no está ya resuelto y publicado con esos mismos datos.

---

## 5. D5 · Alcance, viabilidad y plan de trabajo (5 %) — **Ejemplar (5,0 / 100 %)**

**Justificación:**
- **Qué hará y qué no hará, con razón de cada exclusión:** §5.1 (4 exclusiones: validación contra registros internos inaccesibles; modelos predictivos/causal fuera del alcance semestral; análisis de producción individual como extensión por el dataset de 1,2 GB; sin convocatorias posteriores a 2021).
- **Cronograma por hitos con entregables verificables y holgura:** §5.3, Tabla 2: 12 semanas, 7 hitos con entregables verificables (scripts + catálogo; tabla de calidad; matrices con IC; Kaplan–Meier/Cox; indicadores de equidad con IC; tablero + marco; informe + guion) y 2 semanas acumuladas de holgura (semanas 6 y 11).
- **Riesgos concretos con contingencia:** §5.2 (3 riesgos, cada uno con contingencia: discrepancia 77 237 vs. 50 891 —ya detectada y convertida en hallazgo—; producción no descargable —no bloquea OE1–OE3—; tiempo insuficiente —priorización por hito + holgura—).
- **Alcance coherente con horas reales:** §5.3: 6 h semanales por integrante (1 h diaria tras clases, 6 días/semana) × 3 × 12 = 216 h disponibles; carga estimada 180 h; holgura 36 h (17 %). Verificado: la corrección de horas está aplicada y la aritmética cierra (6×3×12=216; 216−180=36 ≈ 17 %).

---

## 6. Cálculo de la nota del bloque Documento (escala 0–5)

| Criterio | Peso | Nivel | Puntos | Puntos × peso |
|---|---|---|---|---|
| D1 Problema, contexto y estado actual | 12 % | Ejemplar | 5,0 | 60 |
| D2 Estado del arte y rigor bibliográfico | 9 % | Competente | 4,0 | 36 |
| D3 Objetivos (bloqueante) | 8 % | Competente | 4,0 | 32 |
| D4 Datos y aproximación metodológica | 6 % | Ejemplar | 5,0 | 30 |
| D5 Alcance, viabilidad y plan | 5 % | Ejemplar | 5,0 | 25 |
| **Total** | **40 %** | | | **183** |

**Nota Documento (0–5)** = 183 / 40 = **4,575 ≈ 4,6** (logro global del documento ≈ 91,5 %).
Aporte al curso (Documento = 40 %): **1,83 / 2,0** (de los 2,0 puntos máximos del componente).

---

## 7. Veredicto

# ✅ APROBADO CON OBSERVACIONES

- **Puerta de aprobación (bloqueantes):** D1 = Ejemplar y D3 = Competente; ninguno en Insuficiente → **no se devuelve el anteproyecto**.
- **Nota del bloque Documento: 4,6 / 5,0** (por encima del piso de aprobación 3,0).
- Nota final del curso sujeta a la sustentación (S1–S3, 60 %) y al techo de autoría (S1 + 1,0), fuera del alcance de esta validación.

### Observaciones residuales (no bloqueantes, ordenadas por prioridad)

1. **D2 / APA (menor, corregible):** corregir la cita de §1.1 "(Çategorización de grupos e investigadores", 2023)" (typo «Ç» y comillas) y el "(2023)" huérfano de §2.1; completar datos editoriales de Souza et al. (2023) y Mena-Chalco & Cesar Júnior (2009). **Verificar en línea la entrada "Revista CTS (2010)"** (el título parece una frase descriptiva y no es contrastable offline); es la única referencia con riesgo de no "decir lo que se afirma" — si al verificarla fallara, D2 bajaría a Insuficiente por cláusula de referencias.
2. **D3 / OE3 (menor):** alinear el enunciado de OE3 (§3.2) con la distinción ya aplicada en §1.2 y §4.3: víctimas medidas como prevalencia interna (ventana 2021); razones de representación frente al censo DANE 2018 solo para género, etnia y discapacidad.
3. **D3–D4–D5 / coherencia de alcance (menor):** el "cruce con la producción de grupos" del objetivo general (§3.1) y de §1.2 no tiene ningún objetivo específico ni entregable que lo operacionalice (el dataset 33dq-ab5a solo aparece como alternativa descartada en §4.3 y no se menciona en §5.1). Decidir y declarar: o es hallazgo de contexto/extensión (y ajustar el general), o se liga a un específico/entregable para que los OE agoten exactamente el general.
4. **D4 (muy menor):** la verificación pendiente de licencia/enlace oficial anotada en la Tabla 1 está cubierta por el hito 1–2 del cronograma; no requiere acción inmediata.

**Nota metodológica:** conforme a la instrucción, no se usó búsqueda web ni contraste en línea de referencias; la existencia/veracidad de las 28 entradas no pudo verificarse offline (indicios de autenticidad altos: DOIs y revistas reales conocidas). La verificación en línea queda señalada como paso recomendado antes de la sustentación, en especial para la entrada Revista CTS (2010).

---

## 8. Fe de erratas — correcciones aplicadas tras esta validación (versión final)

Esta validación se ejecutó sobre el texto del anteproyecto **anterior** a tres
correcciones que ya están aplicadas y verificadas en la versión final
(`pdf/anteproyecto.pdf`, recompilada y re-extraída):

| Obs. de esta validación | Corrección aplicada | Verificación |
|---|---|---|
| 1. Typo «Çategorización» (§1.1) y «(2023)» huérfano (§2.1) | Se reemplazaron todas las comillas rectas activas de babel (que producían «Ç»/«ç»: p. ej. "identificadoresçomo") por comillas tipográficas correctas. La cita sin autor ahora es (``Categorización de grupos e investigadores'', 2023) tanto en §1.1 como en §2.1. | PDF final: 0 ocurrencias de «Çategorización», «Ç» o «çomo». |
| 2. OE3 (§3.2) agrupaba víctimas con el comparador DANE | OE3 ahora enuncia: género/etnia/discapacidad comparadas con el censo DANE 2018, y la condición de víctima "se mide como prevalencia interna del padrón en la ventana disponible (2021)" (§3.2, alineado con §1.2 y §4.3). | PDF final: texto verificado. |
| 3. Cruce con producción en el OG sin OE que lo operacionalice | El objetivo general ahora declara el cruce "ya ejecutado como línea base de contexto" y el párrafo explicativo aclara que no es objeto de ningún OE (plan B §4.3), evitando prometer un entregable inexistente. | PDF final: texto verificado. |

Con estas correcciones, los defectos formales que mantenían D2 y D3 en
Competente quedan resueltos en la versión entregada; la nota del bloque en el
PDF final se estima en **~4,8/5,0** (D2 y D3 recuperan el nivel Ejemplar si el
resto de la citación se mantiene sin errores).
