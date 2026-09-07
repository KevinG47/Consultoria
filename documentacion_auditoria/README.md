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
│   └── ejecucion_log.txt            # Log de ejecución real de los scripts
├── src/
│   ├── generar_documento.py         # Genera secciones LaTeX desde data/
│   └── compilar.py                  # Compila proyectos LaTeX a PDF
├── latex/
│   ├── comun/preambulo.tex          # Preámbulo compartido (Overleaf-ready)
│   ├── maestro_auditoria/           # Documento maestro (proyecto Overleaf completo)
│   │   ├── main.tex
│   │   ├── preambulo.tex
│   │   ├── secciones/               # 01_portada … 09_apendice_inventario
│   │   └── refs.bib
│   └── objetivo_<n>/                # (generados desde data/objetivos.yaml)
└── pdf/                             # PDFs compilados
```

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

La **carpeta `ENTREGA_1/`** (raíz del repositorio) contiene **exactamente lo que
se califica**: `anteproyecto.pdf` (Documento D1–D5, 40 %), `diapositivas_anteproyecto.pdf`
(Sustentación S1–S3, 60 %) y `guia_estudio.pdf` / `tarjetas_sustentacion.pdf` (apoyo).
El README de la raíz es la guía de entrada para el docente. Validación final de
cierre contra la rúbrica: `data/validacion/validacion_cierre_D.md` y
`data/validacion/validacion_cierre_S.md`.

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
`data/pip_install*.log` y `data/ejecucion_log.txt`.

## Datos de auditoría

| Artefacto | Descripción |
|---|---|
| `commits_timeline.csv` | 133 commits: hash, fecha, autor, correo, asunto |
| `inventario_codigo.csv` | 51 archivos: ruta, lenguaje, líneas, KB, rol |
| `analisis_codigo/*.json` | Ficha por archivo: descripción, lógica, fortalezas, debilidades, mejoras, ejecutabilidad, producción esperada, bugs, recomendación |
| `ejecucion_log.txt` | Resultado de ejecutar cada script del repo en un venv Python (exit code, tiempo, salidas) |

## Notas de la auditoría

- El repositorio fue clonado con historial completo (133 commits) desde GitHub.
- La ejecución real de scripts se hizo en `.venv` dentro del clon del
  repositorio (ver `ejecucion_log.txt`); los scripts que requieren
  `datos/raw` (producción, ~1.2 GB, gitignored) no pudieron ejecutarse y se
  documenta como hallazgo de reproducibilidad.
