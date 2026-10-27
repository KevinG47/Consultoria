# Contexto del proyecto — Auditoría estadística del Observatorio MinCiencias

> **Actualizado al 27-oct-2026.**
>
> **Nota de migración (26-oct-2026):** este archivo se creó en la raíz del repo a partir de la copia de markitdwon (9 secciones). El traspaso actualizado del 25-oct-2026 tiene 16 secciones; las secciones §10–§16 están en el chat de esa fecha y pendientes de migrar aquí. Markitdwon conserva la versión vieja (9 secciones).

## 1. Instrucción para la IA que recibe este documento

Este documento es el contexto de un proyecto que veníamos trabajando en otros chats. Léelo, no continúes el trabajo todavía y responde con un resumen de lo que entendiste y 5 dudas.

> Regla permanente para todas las respuestas de este chat: responde siempre en español.

## 2. Objetivo del proyecto y quién es Kevin

- **Kevin** (Kevin Leonardo Chaparro Reyes) es estudiante de la consultoría estadística **Auditoría del Observatorio MinCiencias**, USTA, 2026-II. Trabaja en equipo con **Valentina Muñoz Palma** y **Paula Margarita Triana Ancinez**. El profesor es **Javier Mauricio Sierra**.
- **Objeto de la consultoría:** auditar el repositorio `ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8` (trabajo del Grupo 8, 2026-I), que analiza el padrón de investigadores reconocidos de MinCiencias.
- **Dos encargos distintos y sucesivos del profesor:**
  1. **Actividad "Nada sin fuente"** (30 % del corte): demostrar, funcionando y no solo descrito, cómo el agente de IA usado en el proyecto gestiona la información — memoria, validación de consultas y validación de resultados — con herramientas justificadas. Cinco entregas: inventario de fallos, experimento con 3 tratamientos (A control, B búsqueda propia, C RAG), sistema de fuentes y trazabilidad, evaluación de fidelidad y memoria final.
  2. **Proyecto de cierre posterior a la sustentación:** evaluar el cumplimiento de los objetivos del repositorio auditado (Fase 1) y completar los análisis que quedaron parciales (Fase 2), con un póster como entregable visible.
- **El equipo construyó el sistema antes de recibir la rúbrica formal** (el encargo inicial fue verbal). Eso se documentó como "orden invertido" y se resolvió corriendo el experimento de medición de forma retroactiva.

## 3. Repositorios, rutas y herramientas

- **Repo de trabajo:** `github.com/KevinG47/Consultoria`, clonado en `C:\Users\InfoPersonal\OneDrive - Universidad Santo Tomás\Escritorio\consultoria`. Todo se trabaja sobre `main`.
- **Historial de commits, en orden cronológico** (para que no haya confusión sobre cuál es el HEAD):
  1. `9243ba1` — cierre de las 5 entregas de "Nada sin fuente" (chat con Claude).
  2. `f4057d4`, `a4ccb49`, `3792bca` — arreglos de Docker y del bug de `verificar_consistencia.py` en Linux (`3792bca` es del 2026-10-17).
  3. `3a1048a`, `22dd51b`, `b8672ff` — correcciones del guion, §7.2 y muestreo integrado en el PDF de Objetivo 1.
  4. `0b44b9b` — shell de presentación con la paleta institucional USTA.
  Antes de este tramo está `b0cafbf` ("R15 simétrica: aceptar una decisión superada conservada como respaldo declarado").
- **Repo auditado:** `ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8`, **commit auditado 1528939**. Vive clonado dentro del repo de trabajo y **no se modifica**.
- **Estructura de carpetas tras la reorganización:** `01_datos/`, `02_dashboards/`, `03_informes/`, `04_auditoria/`, `05_entregas/`. Dentro de `01_datos/datos_fuente/` está `Investigadores_Reconocidos_por_convocatoria_20261006.csv`.
- **Intocables:** `documentacion_auditoria/src/`, `documentacion_auditoria/data/` y `documentacion_auditoria/latex/` — los scripts y las 17 reglas usan rutas relativas exactas y se rompen si se mueven.
- **Stack:** Python 3.11, pandas, scikit-learn, networkx, plotly, matplotlib, PyYAML, PyMuPDF, LaTeX (TinyTeX) y git. Gestión de dependencias con Poetry.
- **El harness (DeepSeek Harness, CLI `dsh`)** es la herramienta con la que se construyó todo: `/deepseek-ai/dsh` 0.1.1-rc.2 con `deepseek-v4-flash`. Límites observados:
  - **No puede hacer push**: el sandbox bloquea el almacén de credenciales de Windows; el push lo hace Kevin en su terminal.
  - **Sandbox sin red por defecto**: no puede instalar paquetes ni consultar URLs salvo que se amplíe el permiso (`escalate sandbox to danger-full-access`).
  - **A veces responde en chino** (y una vez respondió en inglés); por eso cada prompt empieza con la línea `INSTRUCCIÓN OBLIGATORIA: RESPONDE SIEMPRE EN ESPAÑOL.`
  - **Trabaja por fases y espera aprobación** cuando el cambio es grande: primero audita y reporta, después ejecuta.

## 4. Estado actual

### Terminado

- **Las 5 entregas de "Nada sin fuente"** (inventario de fallos, experimento de tratamientos, sistema de fuentes y trazabilidad, evaluación de fidelidad, memoria), cerradas y commiteadas.
- **Sistema de memoria del agente**: `python -m memoria {indexar, consultar, dibujar, grafo, validar}` sobre `documentacion_auditoria/src/memoria/` (RAG con TF-IDF y embeddings Granite como experimento, grafo en networkx, 17 reglas de validación, puerta en `compilar.py`). Estado de las reglas: **17 reglas → 15 PASA / 0 FALLA / 2 ADVERTENCIA**, idéntico en local y dentro de Docker.
- **Fase 1** (evaluación de cumplimiento del repo auditado, entregable `documentacion_auditoria/evaluacion_cumplimiento.md`) y **Fase 2** (análisis parciales: per cápita, diversidad, redes, clustering, unicidad de IDs, supervivencia Kaplan-Meier y Cox, mapa de migración). La Fase 2 cerró con **el 100 % de los análisis entregados, salvo Q7 bloqueado por datos**.
- **Dashboards HTML autocontenidos**: `dashboard_eda.html`, `dashboard_fase2.html` (8 paneles), `mapa_migracion.html` (5,39 MB), `herramienta_trayectorias.html` (2,52 MB) y `grafo_interactivo.html`.
- **Repo autosuficiente**: `datos_originales/repo_mejorado/` con los scripts arreglados para que el próximo grupo no dependa del repo auditado.
- **Docker**: imagen funcional (`docker build -t observatorio .`), con `python -m memoria validar` y los dashboards corriendo dentro del contenedor.
- **Reorganización del repo** en `01_datos` … `05_entregas` y limpieza de basura.
- **Guion de sustentación** redactado; **declaración de uso de IA y reparto** (`DECLARACION_IA_Y_REPARTO.md`) con reparto honesto del trabajo.
- **Cierre del 23 de octubre** (tercer chat, continuación tras un corte de sesión):
  - **PDF de Objetivo 1 actualizado**: `metodologia_muestreo.md` integrado como sección nueva (`06_muestreo.tex`), §7.2 de `comparacion_tfidf_vs_embeddings.md` corregido y cifras del guion llevadas a **15 PASA / 0 FALLA / 2 ADVERTENCIA** (antes decían 15/1/1 y "R15 FALLA").
  - **`02_dashboards/presentacion.html` + `servir_presentacion.bat`**: un shell de navegación (barra lateral estilo la plantilla del docente, portada, flechas) que carga en un iframe los tres dashboards existentes (`dashboard_fase2.html`, `dashboard_eda.html`, `herramienta_trayectorias.html`) sin modificarlos.
  - **Paleta institucional aplicada**: azul marino `#0A1F44` + dorado `#C5A065`, con `--secondary-texto: #8F6D0A` para que el texto pequeño cumpla **WCAG AA (4,82:1)**.
  - **`05_entregas/guion_exposicion_paneles.md`**: guion hablado para Kevin, Valentina y Paula (10–12 minutos, sin jerga de IA).

### En curso / pendiente

- **Póster del Pulse (11 de noviembre):** el póster **no existe** — hay la idea y tres prompts escritos (D54, D67 y D84 de la bitácora), pero nunca se envió el encargo. El contenido debe salir de los análisis de Fase 1 y Fase 2 y de los paneles del dashboard.
- **Objetivo del último corte: el modelo de machine learning.** El docente propuso **XGBoost con enfoque bayesiano** por escasez de datos; eso todavía **no está en el repo**. Ojo con el rigor: *XGBoost no es bayesiano*, así que hay que precisar si se refiere a BART, a un ajuste bayesiano de hiperparámetros de XGBoost o a un modelo distinto (INLA/brms/PyMC). El harness **no tiene red**, así que no puede buscar literatura: o se le pasan PDFs, o se escala el sandbox, o se asume el riesgo de citas inventadas.
- **Entrega de objetivos: 23 de octubre** (presentación + PDF de Objetivo 1). Al 5 de octubre el plan era: avance de la comparación TF-IDF vs embeddings, diseño y ejecución del muestreo del Objetivo 1, y esqueleto y contenido del póster.
- **D007 (migrar a embeddings)** sigue formalmente `pendiente_implementacion`: se probó embeddings locales (Granite R2) sin que superara a TF-IDF, y R15 vigila esa deuda.

## 5. Decisiones tomadas (y por qué)

- **D001 · Usar RAG para la memoria semántica** — el corpus de auditoría crece y debe mantenerse consistente entre documentos.
- **D002 · TF-IDF en vez de embeddings** — corpus pequeño (~24 documentos) y homogéneo; sin dependencias externas ni costo. **Estado: superada por D007.**
- **D003 · Grafo en memoria con networkx, no Neo4j/Memgraph** — escala real de 255 nodos; un motor externo sería infraestructura desproporcionada. **Vigente.**
- **D004 · Descartar Obsidian Vault del pipeline automatizado** — no tiene API programática que el agente pueda consultar o validar; su rol queda como navegación humana. **Vigente.**
- **D005 · Extender el grafo con datos en vivo del repo auditado** (clon real + `git log`), no con una copia congelada. **Vigente.**
- **D006 · Validación como puerta antes de compilar** — `compilar.py` aborta con exit 2 si hay reglas en FALLA. **Vigente.**
- **D007 · Migrar el RAG de TF-IDF a embeddings por API key** — decisión del docente por reproducibilidad. **Estado: pendiente de implementación.** Choque a considerar: subir el corpus a la nube puede comprometer el criterio de datos de la contraparte, por eso se probó con modelo local.
- **D008 · Arreglar el indexador del RAG** — el fix cambió el corpus de 145 fragmentos / 105 167 palabras a 150 fragmentos / 116 277 palabras. **Vigente.**
- **D009 · Cerrar el ciclo de D008 y añadir R17** — actualizar las cifras obsoletas en 6 sitios y crear la regla que vigila que las cifras citadas en los documentos no queden desactualizadas. **Vigente.**
- **D010 · El 36,9 % "sin fuente" sí es recomputable y el 22 vs 19 es correcto sobre otro universo** — se registró la corrección de una crítica previa del propio equipo. **Vigente.** Consecuencia: R17 falló por una cita del §6.2 que decía "9 registradas" cuando ya eran 10; se dejó documentado como deuda declarada.
- **D011 · Registrar el análisis longitudinal como decisión — NO se registró**, para evitar la cascada de R17 (ya hay 10 decisiones, D001–D010). La decisión metodológica se documenta en `metodologia_muestreo.md` §7.4.
- **Migrar de Kaleido a Plotly-Mirage** en `repo_mejorado` y en el contenedor, para no heredar la dependencia de Chrome en el próximo grupo.

## 6. Hallazgos y cifras clave (con su fuente)

- **Universo:** 77 237 registros, 30 086 personas únicas, 6 convocatorias (2013–2021). Fuente: `01_datos/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv`.
- **Base de reserva del repo auditado:** 50 891 registros y 3 convocatorias (2017, 2019, 2021), 26 662 investigadores únicos; es una muestra de método no explicado, no datos completos. Fuente: `repo_auditado` (archivo versionado) y contexto del chat.
- **Muestra del muestreo:** MAS de **2 224 personas** (Cochran 1977 con corrección por población finita: n₀ = 2 401, n = 2 223,6), semilla 2026.
- **Retención 2013→2021:** **56,2 % censal** (universo completo) frente a **56,6 %** estimado por la muestra MAS con IC [52,7; 60,5]. La cifra oficial del dashboard es la censal. Fuente: `analisis_longitudinal.md` y el dashboard EDA.
- **22 vs 19:** no es un error de aritmética — son universos distintos. Los 22 registros con edad imposible pertenecen a 12 personas; al colapsar a una fila por persona quedan **11** ("reconciliación 11 ↔ 22"). Fuente: `analisis_longitudinal.md` y `02_edad.png` (etiquetado corregido de "registros" a "personas").
- **Bogotá + Antioquia:** 56,2 % en 2013, 52,0 % en 2017 y 47,9 % en 2021 — citar siempre con año; 51 % sin año es impreciso.
- **Subrepresentación frente al censo DANE 2018:** afro ~3×, indígena 7,9×, discapacidad 8×. La fila `VICTIMA CONFLICTO` con 17,7 % viene del **RUV 2021**, no del censo DANE 2018 (error heredado en `diversidad.py`).
- **Calidad de datos:** 11 personas (22 registros) con edad imposible, máximo 956 años.
- **Supervivencia (F2-10):** 8 992 eventos de salida del sistema, 29,9 % de las personas.
- **36,9 % sin fuente (artefacto):** el artefacto existe y es recomputable; quedó registrado en D010.
- **Género:** 59,7 % hombres / 40,3 % mujeres en el padrón (brecha 19,4 pp), según el dashboard EDA.

## 7. Errores resueltos y lecciones

- **OneDrive y Docker:** el CSV de `01_datos/datos_fuente/` pesa 31,32 MB y era un **marcador de posición en la nube** (`Attributes: Archive, ReparsePoint`). Docker Desktop no puede leer archivos virtuales de OneDrive → `invalid file request`. Solución: excluirlo del contexto con `.dockerignore` (el CSV queda versionado en Git y se monta por volumen cuando hace falta), no "sacarlo del repo".
- **Orden de archivos NTFS vs ext4:** `verificar_consistencia.py` contaba mal las preguntas dentro del contenedor Linux porque `_contar_preguntas()` buscaba sobre la concatenación de los 133 `.tex` con una expresión regular perezosa; en NTFS el archivo maestro se leía primero y en ext4, otro. Solución: leer archivo por archivo, ordenar alfabéticamente y exigir que el enunciado y su lista estén en el mismo archivo. **No era CRLF ni BOM.**
- **Razón de diversidad invertida (H1, error del propio harness):** en `dashboard_fase2.html` la razón se presentaba como sobrerrepresentación cuando en realidad era subrepresentación de los grupos étnicos. Lo detectó la auditoría cruzada independiente (`reporte_validacion_cruzada.md`); sin eso el equipo habría sustentado una conclusión invertida.
- **Reglas que se autoauditan:** al registrar D010, R17 detectó que un documento seguía citando "9 decisiones" cuando ya eran 10. El sistema vigila sus propias cifras.
- **El RAG no alucina cuando no tiene cobertura:** en el banco de preguntas, 16 de 18 no trajeron el dato exacto porque el PDF de auditoría nunca se indexó; el sistema devolvió fragmentos débiles pero reales en vez de inventar cifras.
- **Los prompts largos se contestan mejor por fases:** casi todos los encargos grandes incluyen un "haz FASE 0 / diagnóstico y espera mi aprobación antes de tocar nada".
- **Los iframes `file://` no funcionan:** Chrome, Edge y Firefox los bloquean por aislamiento de origen. Un HTML que navega entre dashboards tiene que servirse desde `http://localhost` (de ahí el `.bat` con `python -m http.server`); si no, los iframes salen en blanco.
- **El contraste también se mide:** el dorado `#C5A065` sobre blanco no alcanza WCAG AA para texto pequeño; se resolvió con `#8F6D0A` (4,82:1). El harness calculó los ratios en vez de suponerlos.
- **El harness no hace git:** en una sesión intentó `git add`/commit cuando el prompt no lo pedía; desde entonces todos los prompts terminan con "NO hagas `git add`, commit ni push". Los commits (`3a1048a`, `22dd51b`, `b8672ff`, `0b44b9b`) y el push los hace Kevin; el último push se hizo desde el perfil de Valentina para que el historial refleje el trabajo en equipo.

## 8. Reglas de trabajo de este proyecto

1. **Responder siempre en español**; al harness se le pega al inicio de cada prompt la línea `INSTRUCCIÓN OBLIGATORIA: RESPONDE SIEMPRE EN ESPAÑOL.`
2. **Un paso a la vez.** Preferir instrucciones acotadas y verificables antes que encargos enormes.
3. **Verificar antes de afirmar:** nada se entrega sin haberlo corrido sobre el repo real; si algo falla o no se puede comprobar, se dice explícitamente.
4. **El harness primero analiza y reporta, y no ejecuta cambios grandes sin aprobación.** El patrón es: diagnóstico → plan → espera OK → ejecución → reporte con commit.
5. **No inventar cifras ni fuentes.** Si un dato no consta, se marca como no consta; si una URL no se verificó, se deja como pendiente explícito.
6. **Los commits y el push los hace Kevin, no el harness.** Todo prompt dirigido al harness termina con: «NO hagas `git add`, commit ni push». El harness deja los archivos modificados y verificados; Kevin revisa, commitea y pushea (`git push origin main`).
7. **No tocar el repo auditado ni las carpetas críticas del sistema de memoria.**

## 9. Próximos pasos inmediatos

1. **Modelo de machine learning del corte:** ~~decidir qué significa "bayesiano" en el pedido del docente y redactar el anteproyecto del modelo antes de ejecutarlo (el repo no tiene nada de `xgboost`/`bayes` todavía)~~ → **hecho y cerrado, ver §17**.
2. **Póster del Pulse (11 de noviembre):** enviar al harness el prompt del póster (D84) cuando el alcance esté claro; debe apoyarse en los paneles del `dashboard_fase2.html` y en las cifras de Fase 1/Fase 2.
3. **Sustentación:** ensayar el `guion_exposicion_paneles.md` y el `presentacion.html` (doble clic en `servir_presentacion.bat`, nunca abrir el HTML con `file://`).
4. **Deuda declarada:** D007 (embeddings) sigue pendiente y R15 lo refleja; D011 quedó decidida como no registrada.

---
*Documento generado a partir de las bitácoras y los chats del proyecto. Todo lo que aquí se afirma consta en esos archivos; lo que no constaba se ha dejado fuera o se ha marcado como no consta.*

---

## 17. Modelo de ML (Fase 3, cerrado 26-oct-2026)

**Qué se hizo.** XGBoost con **máscaras estructurales** por categoría de origen
(Junior: binario sube/se mantiene, porque IJ no puede bajar; Asociado y Senior:
tricótomos; Emérito excluido). Sobre **43 187 transiciones contiguas** (5
cohortes 2013→2021), con **172 features** de producción de las que **111 tienen
gain > 0 en el modelo final** (43 en el fold más pequeño, entrenado solo con la
cohorte 17). Configuración final: **100 árboles**, `gamma=0.1`,
`subsample=0.8`, `max_depth=7`, `learning_rate=0.05`, umbral de «baja» 0,15.

**Métricas en test** (13 355 filas, evaluadas **una sola vez**, cohorte
2019→2021): **F1 «baja» 0,4234 · recall 0,7878 · precisión 0,2895 · F1 macro
0,5109 · Brier 0,4692**.

**Modelo bayesiano jerárquico.** Ordinal acumulativo (cumulative link) con
efectos aleatorios de categoría y periodo, versión mínima de 12 predictores y
2 cadenas × 1000+1000: **AUC «baja» 0,82** y **Brier 0,437**. No es operativo:
se documenta como **capa de incertidumbre** (probabilidades mejor calibradas que
el XGBoost) y como ruta metodológica. El run completo de 25 predictores no
terminó en 3 h sin compilador C: deuda técnica declarada.

**Cuatro rondas de mejora sin cambio.** (1) tuning de 54 configuraciones de
regularización; (2) reducción de features a top 50/80/120; (3) demografía
(género, edad, departamento, institución); (4) trayectoria (tiempo en categoría,
historial de subidas/bajadas, momentum) y red de grupos. Ninguna superó el umbral
de +2 pp. **Techo del dato, no del método:** solo 5 cohortes históricas, el
`produccion_grupos.csv` no contiene coautorías (1,02 autores por producto) y hay
un cambio de prevalencia de «baja» del **5,2 % → 10,2 %** entre train y test.

**Artefactos:** `07_modelo/modelado/model_card.md` (ficha del modelo) y
`07_modelo/modelado/validacion_honesta.md` (bitácora de validación y del techo
del dato). Resumen compacto: `07_modelo/documentacion/CONTEXTO_FASE_ML.md`.


---

## 18. Auditoría de datos y modelo limpio (27-oct-2026)

**Fuga por identidad.** El split es temporal (train 2014/15/17, val 2019, test
2021) y no hay fuga de etiqueta: las nueve comprobaciones V01–V09 del manifiesto
pasan. Pero **el 64,31 % de las personas de test (8 589 de 13 355) ya aparecían
en train o val**, porque un panel comparte individuos entre periodos. Es
estructural al diseño y **no invalida el uso operativo** (puntuar a quienes ya
están en ScienTI), aunque impide afirmar generalización a investigadores nuevos.
Benchmark de entidad disjunta (B, sin IDs compartidos): **F1 «baja» 0,4016** frente
a 0,4234 del operativo, es decir **delta A−B = +2,18 pp**. El control de volumen
(mismas 5 005 filas, identidad permitida) da 0,4222: **el efecto es de identidad
(+2,06 pp), no de volumen (+0,12 pp)**. Con delta < 5 pp el modelo se considera
robusto y se cierra.

**EDA de diagnóstico.** Sobre las 172 features: **49 redundantes** (34 duplicados
exactos con r = 1,00000 y 15 con VIF > 10; tras la limpieza quedan 123 con VIF
máximo 4,95), **86 features con > 99 % de ceros** (132 con > 90 %, 66 con gain = 0
en el modelo base) y **3 features con drift severo (PSI > 0,25)**: proyecto de I+D
con calidad (0,384), artículos (0,316) y artículos de generación de contenido
(0,316). Además, 628 filas (1,45 %) superan el p99 de `n_productos` (105; máx.
613) y hay 128 filas con fecha de producto posterior a la convocatoria (0,004 %,
concentradas en 2013-2014 y ausentes en 2019-2021).

**Modelo limpio (solo folds, test intacto).** Quitando las 49 redundantes, las 86
muertas y winsorizando `n_productos` al p99: **F1 «baja» OOS 0,2877 con 123
features (−1,08 pp)** y **0,2834 con 56 (−1,51 pp)**, con Brier 0,4223 frente a
0,4196. Es decir, **la limpieza no mejora: baja el F1, sube la desviación entre
folds y empeora el Brier**. Se descarta; las features redundantes actuaban como
regularización implícita.

**Conclusión.** El modelo **Ronda 2 con 172 features es el óptimo** de este
conjunto de datos: F1 «baja» 0,4234 · recall 0,7878 · precisión 0,2895 · F1 macro
0,5109 · Brier 0,4692 en test. El EDA queda como documentación y deuda de
robustez, no como palanca. Detalle completo en
`07_modelo/documentacion/auditoria_base_datos.md` (§2, §6 y §7).
