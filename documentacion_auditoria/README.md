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

## Estado actual (versión 3 — criterios enfocados + versión LITE)

Mejoras aplicadas tras la revisión del usuario:
- **Layout corregido**: 0 desbordes de línea significativos (de 400+ avisos *Overfull hbox* a 5 avisos <2 pt, invisibles) — se añadió control de quiebres en rutas, columnas `raggedright` y anchos de tabla ajustados.
- **Documentos enfocados**: cada PDF desarrolla SOLO su criterio (5-8 págs.) + guía de lectura con **glosario en lenguaje llano** + un breve cruce con el documento maestro (sin repetir contenido entre PDFs).
- **Crítica equilibrada**: las debilidades se presentan como "puntos de mejora (si aplican)"; si un archivo está bien construido se dice explícitamente ("No se identifican debilidades significativas").
- **Versión LITE** de cada criterio: archivos clave + fichas compactas (objetivo_3 pasa de 95 a 15 págs.).

| Entregable | Estado |
|---|---|
| `pdf/maestro_auditoria.pdf` | ✅ (114 págs.) — auditoría integral, 51 fichas de código |
| `pdf/objetivo_1.pdf` · `_lite` | ✅ (5 + 5 págs.) — **Criterio 1**: Entendimiento del objetivo |
| `pdf/objetivo_2.pdf` · `_lite` | ✅ (5 + 5 págs.) — **Criterio 2**: Datos: suficiencia y corrección |
| `pdf/objetivo_3.pdf` · `_lite` | ✅ (95 + 15 págs.) — **Criterio 3**: Documentación y crítica de código (51 / 18 archivos) |
| `pdf/objetivo_4.pdf` · `_lite` | ✅ (5 + 5 págs.) — **Criterio 4**: Validación estadística |
| `pdf/objetivo_5.pdf` · `_lite` | ✅ (5 + 5 págs.) — **Criterio 5**: Lógica de creación y cumplimiento |
| `pdf/objetivo_6.pdf` · `_lite` | ✅ (8 + 8 págs.) — **Criterio 6**: Línea de tiempo (133 commits) |
| `zip_overleaf/*.zip` | ✅ 13 ZIPs Overleaf-ready (maestro + 6 criterios × 2 versiones) |
| `data/analisis_codigo/*.json` | ✅ 51 fichas por archivo (cobertura 100%) |
| `data/ejecucion_resumen.csv` | ✅ 16 scripts ejecutados: 10 OK / 6 error (con causa) |

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
