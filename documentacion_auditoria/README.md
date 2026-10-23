# Documentación de Auditoría — Observatorio MinCiencias

Proyecto de documentación técnica generado de forma **reproducible** para la
consultoría universitaria (USTA · Ustadistica · 2026-I). Contiene la auditoría
integral del repositorio
[`Observatorio_Ministerio_de_Ciencias_Grupo8`](https://github.com/ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8).

## Estructura

```
documentacion_auditoria/
├── README.md                        # Este archivo
├── data/
│   ├── commits_timeline.csv         # Línea de tiempo: 133 commits (git log)
│   ├── inventario_codigo.csv        # Inventario de los 51 archivos de código
│   ├── analisis_codigo/             # JSON por archivo de código (auditoría)
│   │   └── *.json                   #   descripción, lógica, crítica, ejecutabilidad
│   ├── validacion/                  # Informes de los agentes validadores (R13)
│   ├── memoria/                     # Sistema del agente: RAG, grafo, reglas, decisiones
│   │   ├── decisiones.yaml          #   bitácora de decisiones (D001–D010)
│   │   ├── fuentes_externas.yaml    #   fuentes consultadas con URL verificada
│   │   ├── rag_indice*.json         #   índices TF-IDF y de embeddings (D007)
│   │   ├── grafo*.json / *.png      #   memoria estructural y sus figuras
│   │   ├── validacion_reglas.json   #   resultado de la última corrida de las 17 reglas
│   │   └── graficas_*/              #   figuras PNG de cada análisis (F2-2 … F2-11)
│   ├── capas.yaml / objetivos.yaml / glosario.yaml
│   └── ejecucion_resumen.csv        # EXIT y tiempo de los 16 scripts del auditado
├── src/
│   ├── generar_documento.py         # Genera secciones LaTeX desde data/
│   ├── compilar.py                  # Compila proyectos LaTeX a PDF (con puerta de reglas)
│   ├── analisis_longitudinal.py     # Panel, retención y transiciones
│   ├── eda_longitudinal.py          # EDA (Parte 1 de la metodología)
│   ├── estimadores_longitudinal.py  # Post-estratificación y GREG (Partes 2-3)
│   ├── diagnosticos_greg.py         # Diagnósticos de supuestos y g-weights (§7)
│   ├── genero_comun.py              # Colapso de categorías de género (§7.4)
│   ├── construir_herramienta.py     # Genera el visor de trayectorias (HTML)
│   ├── parsear_log.py               # Tabla EXIT/tiempo del pipeline auditado
│   ├── extraer_errores.py           # Tracebacks de los scripts que fallaron
│   └── memoria/                     # RAG + grafo + reglas (17) + herramientas CLI
├── latex/
│   ├── comun/preambulo.tex          # Preámbulo compartido (Overleaf-ready)
│   ├── maestro_auditoria/           # Documento maestro (proyecto Overleaf completo)
│   │   ├── main.tex
│   │   ├── preambulo.tex
│   │   ├── secciones/               # 01_portada … 09_apendice_inventario
│   │   └── refs.bib
│   └── objetivo_<n>/                # (generados desde data/objetivos.yaml)
├── scripts/                         # banco_preguntas.py, comparar_rag.py
├── zip_overleaf/                    # ZIPs listos para subir a Overleaf
└── pdf/                             # PDFs compilados
```

> **Los entregables de la Fase 2 ya no viven aquí.** Desde la reorganización de
> octubre, los JSON de resultados están en `01_datos/resultados_json/`, los
> dashboards en `02_dashboards/` y los informes en `03_informes/analisis_fase2/`.
> `data/memoria/` conserva lo que el sistema de memoria necesita para las reglas
> (índice RAG, grafo, decisiones, validación) y las figuras PNG de cada análisis.
> El resto de esta carpeta —`src/`, `latex/`, `pdf/`— sigue exactamente donde
> estaba.

> **Los logs del pipeline auditado no están en `data/`** sino en
> `_archivo/logs_pipeline_auditado/` (`ejecucion_log.txt`, `errores_ejecucion.txt`,
> `pip_install*.log`, `dependencias_latex.txt`); la tabla curada está en
> `data/ejecucion_resumen.csv`.

## Estado actual (versión 4 — LITE con reglas de build, glosario parametrizado, evidencia de código)

Mejoras de esta versión (todas verificadas con QA automático):
- **LITE ≠ completo**: la sección principal LITE = veredicto + 1-2 hallazgos de impacto (≤40% de palabras del completo). Si el LITE es idéntico al completo o supera el 40%, la build **FALLA** y no se emite el PDF (`_verificar_lite` en `generar_objetivo.py`).
- **Glosario parametrizado**: fuente de verdad única en `data/glosario.yaml`; cada PDF incluye SOLO los términos que aparecen en su propio texto (filtrado por claves). Verificado: objetivo_2 → Mojibake; objetivo_4 → HHI, k-prototypes; objetivo_5 → DuckDB, Sprint, CRISP-DM; objetivo_1 → ninguno.
- **Orden canónico por capa**: `data/capas.yaml` (ingesta → transformación → modelo → análisis → orquestación → visualización → docs → tests → legacy) usado por TODOS los documentos que listan archivos.
- **Evidencia de código**: cada hallazgo con referencia `archivo.py:N-M` incrusta el fragmento real del código (≤6 líneas) extraído del repositorio en el momento de la auditoría (84 bloques en las versiones completas).
- **Cobertura computada**: línea "Cobertura: X de Y archivos..." calculada de los conteos reales (51 de 51 completo; 18 de 51 LITE).
- **Commit auditado**: cada portada muestra el hash corto del commit auditado (`1528939`), además de la fecha de generación.
- **Autoconsistencia numérica**: `src/verificar_consistencia.py` compara cifras citadas en prosa contra conteos reales (commits, scripts, criterios, preguntas enumeradas, cobertura). Estado: 5/5 OK.

| Entregable | Estado |
|---|---|
| `pdf/maestro_auditoria.pdf` | ✅ (125 págs.) — auditoría integral, 51 fichas, 84 bloques de evidencia |
| `pdf/objetivo_1.pdf` · `_lite` | ✅ (4 + 4 págs.) — **Criterio 1**: Entendimiento del objetivo |
| `pdf/objetivo_2.pdf` · `_lite` | ✅ (5 + 4 págs.) — **Criterio 2**: Datos: suficiencia y corrección |
| `pdf/objetivo_3.pdf` · `_lite` | ✅ (106 + 20 págs.) — **Criterio 3**: Documentación y crítica de código (51 / 18 archivos) |
| `pdf/objetivo_4.pdf` · `_lite` | ✅ (5 + 5 págs.) — **Criterio 4**: Validación estadística |
| `pdf/objetivo_5.pdf` · `_lite` | ✅ (5 + 4 págs.) — **Criterio 5**: Lógica de creación y cumplimiento |
| `pdf/objetivo_6.pdf` · `_lite` | ✅ (8 + 4 págs.) — **Criterio 6**: Línea de tiempo (133 commits) |
| `zip_overleaf/*.zip` | ✅ 19 ZIPs Overleaf-ready (maestro + 6 criterios × 2 versiones + estado del arte + validación rúbrica + anteproyecto + diapositivas + guía de estudio + tarjetas de sustentación) |
| `data/analisis_codigo/*.json` | ✅ 51 fichas por archivo (cobertura 100%) |
| `data/ejecucion_resumen.csv` | ✅ 16 scripts ejecutados: 10 OK / 6 error (con causa) |
| `src/verificar_consistencia.py` | ✅ Autoconsistencia numérica: 7/7 OK |
| `pdf/estado_del_arte.pdf` | ✅ (20 págs.) — Estado del Arte multilingüe: 11 dominios, matriz de mejora, 39 referencias; validado por 2 agentes independientes |
| `pdf/anteproyecto.pdf` | ✅ (12 págs. totales; cuerpo 8 págs.) — **Entrega 1 · Anteproyecto USTA 2026-II** · modalidad datos abiertos · APA 7 · declaración de IA en §6 |
| `pdf/diapositivas_anteproyecto.pdf` | ✅ (10 láminas Beamer) — sustentación de 10 minutos |
| `pdf/guia_estudio.pdf` | ✅ (3 págs.) — guía de estudio para la sustentación (reparto, frases clave, banco de ~21 preguntas, checklist) |
| `pdf/tarjetas_sustentacion.pdf` | ✅ (3 págs.) — tarjetas de sustentación frase por frase, una página por integrante (Kevin · Valentina · Paula) |

### Entrega 1 — Anteproyecto (2026-II)

La **carpeta `05_entregas/ENTREGA_1/`** (raíz del repositorio) contiene **exactamente lo que
se califica**: `anteproyecto.pdf` (Documento D1–D5, 40 %), `diapositivas_anteproyecto.pdf`
(Sustentación S1–S3, 60 %) y `guia_estudio.pdf` / `tarjetas_sustentacion.pdf` (apoyo).
El README de la raíz es la guía de entrada para el docente. Validación final de
cierre contra la rúbrica: `data/validacion/validacion_cierre_D.md` y
`data/validacion/validacion_cierre_S.md`.

### Memoria del agente de IA (RAG + grafo + reglas)

Sistema de gestión de información del agente, en `src/memoria/`, ejecutado sobre
los datos reales del proyecto.

> **Dónde ejecutarlo.** El paquete se importa como `memoria`, así que estos
> comandos se lanzan **desde `documentacion_auditoria/src/`**:
>
> ```bash
> cd documentacion_auditoria/src     # desde la raíz del repositorio
> python -m memoria validar
> ```
>
> Desde `documentacion_auditoria/` también funciona con `python -m src.memoria …`.
> Los scripts de análisis, en cambio, se lanzan desde la raíz por ruta completa
> (`python documentacion_auditoria/src/eda_longitudinal.py`), porque resuelven sus
> rutas con `Path(__file__)`.

```bash
python -m memoria indexar                    # memoria semántica (TF-IDF; ver decisión D007)
python -m memoria consultar "tema" -k 5      # consulta el corpus ya escrito
python -m memoria antes-de-redactar "tema"   # RAG antes de escribir (queda en bitácora)
python -m memoria grafo                      # memoria estructural (networkx) + git real
python -m memoria dibujar --tipos Criterio,Documento   # figura para diapositiva (+ --html)
python -m memoria dibujar --tipos Criterio,Documento --interactivo   # PNG + HTML interactivo
python -m memoria dibujar-html --tipos Criterio,Documento   # solo el HTML interactivo (PyVis)
python -m memoria validar                    # 17 reglas (exit 1 si alguna FALLA)
python -m memoria evidencia                  # informe legible de la última ejecución
```

- **Memoria semántica:** 151 fragmentos de 25 documentos (6 criterios + LITE +
  maestro + 11 informes de validación + **el anteproyecto**). Bitácora en
  `data/memoria/consultas_rag.jsonl`.
- **Memoria estructural:** grafo de 255 nodos / 500 aristas construido desde los
  YAML/CSV **más datos vivos** del clon auditado (`git log`, `git ls-files`,
  commit `1528939`).
- **Vista interactiva del grafo (para sustentación):** `python -m memoria dibujar-html`
  genera `02_dashboards/grafo_interactivo.html` con **PyVis**. En la vista
  `Criterio,Documento` son 19 nodos y 18 relaciones: los criterios (azul oscuro, arriba)
  generan sus documentos (azul claro, abajo), su versión LITE va en gris y el maestro de
  auditoría en dorado; cada flecha lleva su etiqueta (`GENERA`, `RESUME EN`,
  `CONSOLIDA EN`) y al pasar el cursor se ve el tipo, el id y la ruta real del archivo.
  El layout es jerárquico (criterios arriba, documentos abajo) y el archivo es
  **autocontenido: funciona sin internet** y se abre con doble clic. El PNG de matplotlib
  (`dibujar`) se mantiene como respaldo. Si PyVis no está instalado, el comando sugiere
  `pip install pyvis` y no rompe nada.
- **Trazabilidad (requisito del docente):** `data/memoria/fuentes_externas.yaml`
  (fuentes consultadas, con URL verificada y archivo dependiente) y
  `data/memoria/decisiones.yaml` (bitácora de decisiones con supersesión
  explícita, p. ej. D007 supera a D002). R15 falla si una decisión **superada**
  sigue en el código sin declararlo, o si se presenta como vigente; si declara el
  respaldo y su motivo, lo registra como advertencia. R16 falla si queda alguna
  URL en "PENDIENTE".
- **Reglas:** puerta previa a la compilación dentro de `compilar.py` (aborta si
  algo FALLA; `--forzar` continúa, `--sin-validar` la desactiva).
  Última ejecución real: **15 PASA · 0 FALLA · 2 ADVERTENCIA** (17 reglas).
  Las advertencias son R12 (solapamiento completo/LITE) y R15 (TF-IDF se conserva
  como respaldo declarado de D007, ya implementada).
- **Evidencia:** `data/memoria/evidencia_validacion.md` y `validacion_reglas.json`.
  Texto justificativo de §6.2: `data/memoria/texto_seccion_6_2.md`, ya integrado
  como `latex/anteproyecto/secciones/06b_memoria_agente.tex`.
- **Repositorio autocontenido (sin el clon auditado).** El contenido versionado del
  proyecto auditado está copiado byte a byte en `04_auditoria/repo_original/`
  (236 archivos, commit `1528939`), verificado con `manifiesto_sha256.csv` y
  `python 04_auditoria/verificar_hashes.py`. Los dos cachés de git
  (`git_log_real.csv`, `git_ls_files_real.txt`) están **versionados**, así que R5,
  R6 y R9 se resuelven sin el clon; R7 usa el ancla
  `data/memoria/commit_auditado.txt` cuando el clon no está. `--refrescar-git` sí
  requiere el clon. Detalle en `04_auditoria/README.md`.
- Los artefactos derivados del RAG (corpus, matriz TF-IDF y vectorizador) están en
  `.gitignore`: se regeneran en segundos con `python -m memoria indexar`, que es el
  primer paso al clonar el repositorio.

### Estado del Arte (revisión de literatura)

`pdf/estado_del_arte.pdf` (proyecto Overleaf en `latex/estado_del_arte/`, ZIP
en `zip_overleaf/estado_del_arte_overleaf.zip`) es una guía de literatura para
mejorar el repositorio auditado, con fuentes en inglés, español y portugués.
Cubre: Ciencia de la Ciencia y evaluación responsable (Leiden/DORA/CoARA),
sistemas nacionales (Lattes/ScienTI/CVLAC, CONPES 4069), calidad de datos y
reproducibilidad (FAIR, DVC, observabilidad), dinámica longitudinal de carreras
(Markov, supervivencia, atrición), desigualdad/concentración, género y
diversidad, redes y jerarquías institucionales, datos mixtos, **ética y
protección de datos** (Ley 1581/2012, reidentificación) y **visualización
narrativa**, más una matriz de mejora priorizada. Validado por dos agentes
independientes (informes en `data/validacion/validacion_sota_*.md`).

## Cómo reproducir los PDFs

### Opción A — Overleaf (recomendada para la entrega)

1. Crear un proyecto nuevo en Overleaf (Blank Project).
2. Subir el contenido de `latex/<proyecto>/` (main.tex, preambulo.tex,
   secciones/, refs.bib) — comprimir la carpeta en ZIP y arrastrarla.
   Ya hay ZIPs preparados en `zip_overleaf/`.
3. Compilar con pdfLaTeX (por defecto). Sin dependencias adicionales:
   Overleaf usa TeX Live completo.

### Opción B — Compilación local (TinyTeX / TeX Live)

Dependencias instaladas y documentadas (vía `tlmgr install` en TinyTeX):

```
tcolorbox pgf environ trimspaces fp caption colortbl enumitem epigraph
fancyhdr listings microtype multirow parskip pdflscape siunitx titlesec
setspace natbib hyphen-spanish babel-spanish  (+ dependencias resueltas
automáticamente por el bucle de compilación, ver data/dependencias_latex.txt)
```

Compilar:

```bash
python src/generar_documento.py   # regenera secciones 05, 08, 09 desde data/
python src/generar_objetivo.py    # genera proyectos por objetivo (data/objetivos.yaml)
python src/compilar.py            # latexmk + copia PDFs a pdf/
```

Nota sobre el entorno Python local: el Python del sistema no tiene pandas ni
PyYAML. Para la ejecución de los scripts del repositorio se creó un venv en
una ruta corta (`%TEMP%/obs_venv`) porque el venv dentro de la carpeta
OneDrive falla por exceso de longitud de ruta (MAX_PATH de Windows,
`jedi/third_party/...`). Los logs de instalación y ejecución están en
`_archivo/logs_pipeline_auditado/` (`pip_install*.log`, `ejecucion_log.txt`,
`errores_ejecucion.txt`).

## Datos de auditoría

| Artefacto | Descripción |
|---|---|
| `commits_timeline.csv` | 133 commits: hash, fecha, autor, correo, asunto |
| `inventario_codigo.csv` | 51 archivos: ruta, lenguaje, líneas, KB, rol |
| `analisis_codigo/*.json` | Ficha por archivo: descripción, lógica, fortalezas, debilidades, mejoras, ejecutabilidad, producción esperada, bugs, recomendación |
| `ejecucion_resumen.csv` | Resultado de ejecutar cada script del repo en un venv Python (exit code, tiempo, causa del fallo) |
| `_archivo/logs_pipeline_auditado/ejecucion_log.txt` | Log crudo de esa ejecución (codificación mixta UTF-8/UTF-16LE; lo parsea `src/parsear_log.py`) |

## Notas de la auditoría

- El repositorio fue clonado con historial completo (133 commits) desde GitHub.
- La ejecución real de scripts se hizo en `.venv` dentro del clon del
  repositorio (ver `ejecucion_log.txt`); los scripts que requieren
  `datos/raw` (producción, ~1.2 GB, gitignored) no pudieron ejecutarse y se
  documenta como hallazgo de reproducibilidad.
