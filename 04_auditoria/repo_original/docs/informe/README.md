# Informe final — Observatorio MinCiencias

Documento en LaTeX que consolida los doce hallazgos del observatorio.

## Estructura

- `informe_final.tex` — fuente principal
- Las figuras se cargan desde `../../artifacts/sprint*/` con paths relativos. No es necesario duplicarlas.
- Sin bibliografía externa: las fuentes están listadas en el anexo D.

## Compilación

### Opción A — Overleaf (sin instalar nada)

1. Subir el archivo `informe_final.tex` a un proyecto nuevo de [Overleaf](https://www.overleaf.com).
2. Subir también el contenido de la carpeta `artifacts/` manteniendo la estructura `artifacts/sprint*/`.
3. Compilar con **pdfLaTeX** (botón verde). Dos pasadas para resolver el índice.

### Opción B — Local (TeX Live / MacTeX)

Instalar la distribución completa una sola vez:

```bash
# macOS
brew install --cask mactex          # ~6 GB, incluye GUI
# Alternativa ligera (sólo CLI):
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install latexmk titlesec tcolorbox enumitem siunitx \
                   collection-fontsrecommended collection-langspanish
```

Luego, desde esta carpeta:

```bash
latexmk -pdf informe_final.tex
# o equivalentemente
pdflatex informe_final.tex
pdflatex informe_final.tex          # segunda pasada para el índice
```

### Opción C — Tectonic (un solo binario, sin LaTeX completo)

```bash
brew install tectonic
tectonic informe_final.tex          # descarga paquetes bajo demanda
```

## Paquetes utilizados

`inputenc`, `fontenc`, `babel` (español), `lmodern`, `microtype`, `geometry`, `setspace`, `parskip`, `xcolor`, `hyperref`, `graphicx`, `caption`, `booktabs`, `siunitx`, `tabularx`, `multirow`, `enumitem`, `epigraph`, `titlesec`, `fancyhdr`, `tcolorbox`, `listings`.

Todos vienen con TeX Live 2023+ y MacTeX. Si compilas con BasicTeX, instala los del bloque `tlmgr install` arriba.

## Personalización

Los datos del autor están al inicio del `.tex` como comandos editables:

```latex
\newcommand{\autorInforme}{Víctor Díaz Bautista}
\newcommand{\directorInforme}{Iván Zainea}
\newcommand{\universidad}{Universidad Santo Tomás}
\newcommand{\unidad}{Ustadistica · Consultoría e Investigación}
\newcommand{\periodo}{2026-I}
```

Modificarlos cambia portada y pie sin tocar el resto del documento.

## Salida esperada

PDF de aproximadamente 30–35 páginas, A4, con tabla de contenidos, doce figuras y los anexos completos.
