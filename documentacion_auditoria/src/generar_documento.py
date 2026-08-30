# -*- coding: utf-8 -*-
"""
generar_documento.py
====================

Generador de secciones LaTeX para la documentación de auditoría del
repositorio Observatorio MinCiencias.

Función
-------
Lee tres fuentes de datos de la auditoría y produce las secciones
LaTeX del documento maestro:

  1. data/analisis_codigo/*.json        -> secciones/05_codigo.tex
     (documentación y crítica por archivo de código, producida por los
      agentes de auditoría)
  2. data/commits_timeline.csv          -> secciones/08_timeline.tex
     (línea de tiempo de commits: resumen por autor, por mes y tabla completa)
  3. data/inventario_codigo.csv         -> secciones/09_apendice_inventario.tex
     (inventario de los archivos de código del repositorio)

Uso
---
    python generar_documento.py            # genera las 3 secciones del maestro
    python generar_documento.py --solo 05  # solo una sección (05|08|09)

Dependencias: solo la biblioteca estándar (pathlib, json, csv, re).

Salida
------
Escribe los archivos .tex en:
    latex/maestro_auditoria/secciones/

Nota de diseño: el generador es intencionalmente simple (sin plantillas
externas) para que sea auditable y re-ejecutable por cualquier miembro del
equipo. La codificación de salida es UTF-8, compatible con Overleaf.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]  # documentacion_auditoria/
DATA = RAIZ / "data"
ANALISIS = DATA / "analisis_codigo"
TIMELINE_CSV = DATA / "commits_timeline.csv"
INVENTARIO_CSV = DATA / "inventario_codigo.csv"
SECCIONES = RAIZ / "latex" / "maestro_auditoria" / "secciones"

# Orden canónico de roles para agrupar la sección de código
ROLES_ORDEN = [
    ("ingesta", "Ingesta de datos"),
    ("transformacion", "Transformación y limpieza"),
    ("modelado", "Modelado dimensional"),
    ("analisis", "Análisis estadístico"),
    ("orquestacion", "Orquestación de análisis (scripts por sprint)"),
    ("visualizacion", "Visualización y dashboard"),
    ("documentacion", "Documentación ejecutable"),
    ("eda", "Análisis exploratorio de datos"),
    ("testing", "Pruebas automatizadas"),
    ("legacy", "Código legacy (etapa académica inicial)"),
]

# ---------------------------------------------------------------------------
# Utilidades LaTeX
# ---------------------------------------------------------------------------


def limpiar_controles(texto: str) -> str:
    """Elimina caracteres de control (0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F, 0x7F)
    que puedan colarse en los JSON (p. ej. '\\b' decodificado como backspace)."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", texto)


def escapar(texto: str) -> str:
    """Escapa caracteres especiales de LaTeX en texto plano."""
    if not texto:
        return ""
    texto = limpiar_controles(texto)
    reemplazos = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        # Símbolos Unicode habituales en las fichas de auditoría
        "≈": r"$\approx$",
        "≥": r"$\geq$",
        "≤": r"$\leq$",
        "≠": r"$\neq$",
        "±": r"$\pm$",
        "×": r"$\times$",
        "÷": r"$\div$",
        "→": r"$\rightarrow$",
        "←": r"$\leftarrow$",
        "↔": r"$\leftrightarrow$",
        "⇒": r"$\Rightarrow$",
        "·": r"$\cdot$",
        "°": r"$^\circ$",
        "…": r"\dots{}",
        "—": "---",
        "–": "--",
        "“": "``",
        "”": "''",
        "‘": "`",
        "’": "'",
        "™": r"\texttrademark{}",
        "®": r"\textregistered{}",
        "©": r"\textcopyright{}",
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto


def codigo_en_linea(texto: str) -> str:
    """Convierte a \\texttt{} un fragmento de código/ruta con puntos de
    quiebre tras guiones bajos y barras (evita desbordes de línea)."""
    t = escapar(texto)
    t = t.replace("/", "/\\allowbreak ")
    return r"\texttt{" + t + "}"


def lista_latex(items: list[str], itemize: bool = True) -> str:
    """Convierte una lista de strings a itemize/enumerate LaTeX."""
    if not items:
        return ""
    env = "itemize" if itemize else "enumerate"
    cuerpo = "\n".join(rf"  \item {escapar(i)}" for i in items)
    return f"\\begin{{{env}}}\n{cuerpo}\n\\end{{{env}}}"


# ---------------------------------------------------------------------------
# Sección 05 — Código
# ---------------------------------------------------------------------------


def _leer_analisis() -> list[dict]:
    """Lee todos los JSON de data/analisis_codigo/."""
    if not ANALISIS.exists():
        return []
    resultados = []
    for f in sorted(ANALISIS.glob("*.json")):
        try:
            # utf-8-sig tolera el BOM que añaden algunos editores Windows
            with open(f, encoding="utf-8-sig") as fh:
                resultados.append(json.load(fh))
        except (json.JSONDecodeError, OSError) as e:
            print(f"[aviso] No se pudo leer {f.name}: {e}")
    return resultados


def _render_ficha(a: dict) -> str:
    """Renderiza una ficha LaTeX por archivo de código."""
    archivo = a.get("archivo", "desconocido")
    rol = a.get("rol", "")
    lineas = a.get("lineas", "")

    partes = [
        "\\subsubsection{" + escapar(archivo) + "}",
        f"\\textbf{{Rol:}} {escapar(rol)} · \\textbf{{Líneas:}} {escapar(str(lineas))}",
        "",
        "\\paragraph{Descripción funcional}",
        escapar(a.get("descripcion", "—")),
        "",
        "\\paragraph{Análisis de la lógica}",
        escapar(a.get("logica", "—")),
        "",
    ]

    if a.get("critica_fortalezas"):
        partes += ["\\paragraph{Fortalezas}", lista_latex(a["critica_fortalezas"]), ""]
    if a.get("critica_debilidades"):
        partes += ["\\paragraph{Debilidades}", lista_latex(a["critica_debilidades"]), ""]
    if a.get("mejoras"):
        partes += ["\\paragraph{Mejoras propuestas}", lista_latex(a["mejoras"]), ""]

    partes += [
        "\\paragraph{Ejecutabilidad}",
        escapar(a.get("ejecutabilidad", "—")),
        "",
        "\\paragraph{¿Produce lo esperado?}",
        escapar(a.get("produce_esperado", "—")),
        "",
    ]

    if a.get("bugs"):
        partes += [
            "\\begin{tcolorbox}[riesgo]",
            "\\textbf{Bugs / problemas detectados:}",
            lista_latex(a["bugs"]),
            "\\end{tcolorbox}",
            "",
        ]

    partes += [
        "\\paragraph{Recomendación de auditoría}",
        "\\textbf{" + escapar(str(a.get("recomendacion", "—"))) + "}",
        "",
        "\\medskip",
        "\\hrule",
        "",
    ]
    return "\n".join(partes)


def generar_05() -> Path:
    """Genera secciones/05_codigo.tex con las fichas por archivo."""
    analisis = _leer_analisis()
    destino = SECCIONES / "05_codigo.tex"

    header = [
        "% ============ 05. Documentación por archivo de código ============",
        "",
        "\\section{Documentación y crítica por archivo de código}",
        "",
        "Esta sección documenta, para cada archivo de código del repositorio:",
        "qué hace (descripción), cómo está construido (lógica), una crítica de",
        "calidad (fortalezas, debilidades, mejoras), su ejecutabilidad real y",
        "si produce los resultados que los investigadores buscaban.",
        "",
        f"\\noindent Archivos documentados: \\textbf{{{len(analisis)}}}.",
        "",
    ]

    # Agrupar por rol
    grupos: dict[str, list[dict]] = {}
    for a in analisis:
        rol = a.get("rol", "legacy")
        grupos.setdefault(rol, []).append(a)

    cuerpo: list[str] = []
    roles_presentes = [r for r, _ in ROLES_ORDEN if r in grupos]
    roles_extra = [r for r in grupos if r not in dict(ROLES_ORDEN)]
    for rol in roles_presentes + roles_extra:
        titulo = dict(ROLES_ORDEN).get(rol, rol.capitalize())
        cuerpo.append("\\subsection{" + escapar(titulo) + "}")
        cuerpo.append(f"\\noindent Archivos: {len(grupos[rol])}.")
        cuerpo.append("")
        for a in sorted(grupos[rol], key=lambda x: x.get("archivo", "")):
            cuerpo.append(_render_ficha(a))

    contenido = "\n".join(header + cuerpo) + "\n"
    destino.write_text(contenido, encoding="utf-8")
    print(f"[05] {destino} ({len(analisis)} fichas)")
    return destino


# ---------------------------------------------------------------------------
# Sección 08 — Línea de tiempo de commits
# ---------------------------------------------------------------------------


def _leer_commits() -> list[dict]:
    if not TIMELINE_CSV.exists():
        return []
    with open(TIMELINE_CSV, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _celda_quiebre(texto: str) -> str:
    """Escapa texto de celda añadiendo puntos de quiebre tras guiones,
    arrobas, signos +, puntos y barras (tokens largos como correos o
    'copilot-swe-agent[bot]' no deben desbordar la celda)."""
    t = escapar(texto)
    for sep in ("-", "@", "+", ".", "/"):
        t = t.replace(sep, sep + "\\allowbreak ")
    return t


def render_tabla_commits(commits: list[dict]) -> str:
    """Devuelve el LaTeX de la tabla completa de commits (longtable)."""
    filas = ""
    for i, c in enumerate(commits, 1):
        filas += (
            f"    {i} & {_celda_quiebre(c['fecha'])} & {_celda_quiebre(c['autor'])} & "
            f"\\texttt{{{c['hash'][:8]}}} & {_celda_quiebre(c['asunto'])} \\\\\n"
        )
    return f"""\\begingroup
\\scriptsize
\\setlength{{\\tabcolsep}}{{3pt}}
\\begin{{longtable}}{{r >{{\\raggedright\\arraybackslash}}p{{1.8cm}} >{{\\raggedright\\arraybackslash}}p{{2.8cm}} >{{\\raggedright\\arraybackslash}}p{{1.2cm}} >{{\\raggedright\\arraybackslash}}p{{7.7cm}}}}
\\caption{{Línea de tiempo completa de commits (orden cronológico)}}
\\label{{tab:commits}}\\\\
\\toprule
\\textbf{{\\#}} & \\textbf{{Fecha}} & \\textbf{{Autor}} & \\textbf{{Hash}} & \\textbf{{Asunto}} \\\\
\\midrule
\\endfirsthead
\\toprule
\\textbf{{\\#}} & \\textbf{{Fecha}} & \\textbf{{Autor}} & \\textbf{{Hash}} & \\textbf{{Asunto}} \\\\
\\midrule
\\endhead
{filas}\\bottomrule
\\end{{longtable}}
\\endgroup
"""


def _leer_inventario() -> list[dict]:
    if not INVENTARIO_CSV.exists():
        return []
    with open(INVENTARIO_CSV, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def generar_08() -> Path:
    """Genera secciones/08_timeline.tex con la línea de tiempo de commits."""
    commits = _leer_commits()
    destino = SECCIONES / "08_timeline.tex"

    if not commits:
        destino.write_text(
            "% timeline pendiente: ejecutar extracción de git\n", encoding="utf-8"
        )
        return destino

    # Resumen por autor
    por_autor: dict[str, list] = {}
    por_mes: dict[str, int] = {}
    for c in commits:
        autor = f"{c['autor']} <{c['email']}>"
        por_autor.setdefault(autor, []).append(c)
        mes = c["fecha"][:7]
        por_mes[mes] = por_mes.get(mes, 0) + 1

    n = len(commits)
    filas_autor = ""
    for autor, cs in sorted(por_autor.items(), key=lambda kv: -len(kv[1])):
        pct = len(cs) / n * 100
        filas_autor += (
            f"    {_celda_quiebre(cs[0]['autor'])} & {_celda_quiebre(cs[0]['email'])} & "
            f"{len(cs)} & {pct:.1f}\\% \\\\\n"
        )

    filas_mes = ""
    for mes in sorted(por_mes):
        filas_mes += f"    {escapar(mes)} & {por_mes[mes]} \\\\\n"

    filas_tabla = ""
    for i, c in enumerate(commits, 1):
        filas_tabla += (
            f"    {i} & {_celda_quiebre(c['fecha'])} & {_celda_quiebre(c['autor'])} & "
            f"\\texttt{{{c['hash'][:8]}}} & {_celda_quiebre(c['asunto'])} \\\\\n"
        )

    contenido = f"""% ============ 08. Línea de tiempo de commits ============
\\section{{Línea de tiempo de la construcción del repositorio}}
\\label{{sec:timeline}}

\\subsection{{Resumen general}}

El repositorio fue construido con \\textbf{{{n} commits}} entre
\\textbf{{{commits[0]['fecha']}}} y \\textbf{{{commits[-1]['fecha']}}} por
\\textbf{{{len(por_autor)}}} identidades de autor (12 personas/roles
distintos). La construcción muestra dos etapas claras: una fase académica
inicial (tareas de análisis por convocatoria, ago--oct 2025) y una fase de
ingeniería de datos (pipelines, sprints 2--6, oct 2025 -- may 2026).

\\subsection{{Distribución de autoría}}

\\begin{{table}}[htbp]
\\centering
\\small
\\begin{{tabularx}}{{\\linewidth}}{{p{{3.2cm}}p{{4.6cm}}rr}}
\\toprule
\\textbf{{Autor}} & \\textbf{{Correo}} & \\textbf{{Commits}} & \\textbf{{\\%}} \\\\
\\midrule
{filas_autor}\\bottomrule
\\end{{tabularx}}
\\caption{{Commits por autor}}
\\end{{table}}

\\subsection{{Actividad por mes}}

\\begin{{table}}[htbp]
\\centering
\\small
\\begin{{tabularx}}{{0.5\\linewidth}}{{lr}}
\\toprule
\\textbf{{Mes}} & \\textbf{{Commits}} \\\\
\\midrule
{filas_mes}\\bottomrule
\\end{{tabularx}}
\\caption{{Commits por mes}}
\\end{{table}}

\\subsection{{Tabla completa de commits}}

\\begingroup
\\scriptsize
\\setlength{{\\tabcolsep}}{{3pt}}
\\begin{{longtable}}{{r >{{\\raggedright\\arraybackslash}}p{{1.8cm}} >{{\\raggedright\\arraybackslash}}p{{2.8cm}} >{{\\raggedright\\arraybackslash}}p{{1.2cm}} >{{\\raggedright\\arraybackslash}}p{{7.7cm}}}}
\\caption{{Línea de tiempo completa de commits (orden cronológico)}}
\\label{{tab:commits}}\\\\
\\toprule
\\textbf{{\\#}} & \\textbf{{Fecha}} & \\textbf{{Autor}} & \\textbf{{Hash}} & \\textbf{{Asunto}} \\\\
\\midrule
\\endfirsthead
\\toprule
\\textbf{{\\#}} & \\textbf{{Fecha}} & \\textbf{{Autor}} & \\textbf{{Hash}} & \\textbf{{Asunto}} \\\\
\\midrule
\\endhead
{filas_tabla}\\bottomrule
\\end{{longtable}}
\\endgroup

\\subsection{{Lectura de la línea de tiempo}}

\\begin{{itemize}}
  \\item El commit inicial (2025-08-24) y los primeros mensajes son de
        documentación y carga de tareas (\\texttt{{README}}, \\texttt{{Add files
        via upload}}), característicos de la fase académica.
  \\item A partir de oct/nov 2025 se observa la consolidación del pipeline:
        ingesta, transformación, modelo dimensional y sprints de análisis.
  \\item Los sprints 5 y 6 (abr--may 2026), liderados por Victor-Diaz-Usta,
        incorporan producción, calidad, tabla maestra IES y Sankeys, cerrando
        los ajustes del director.
\\end{{itemize}}
"""
    destino.write_text(contenido, encoding="utf-8")
    print(f"[08] {destino} ({n} commits)")
    return destino


# ---------------------------------------------------------------------------
# Sección 09 — Apéndice: inventario de código
# ---------------------------------------------------------------------------


def _rol_por_ruta(ruta: str, analisis: list[dict]) -> str:
    """Deriva el rol de un archivo desde su ruta o desde el JSON si existe."""
    base = Path(ruta).name
    for a in analisis:
        if Path(a.get("archivo", "")).name == base:
            return a.get("rol", "")
    if ruta.startswith("src/ingesta"):
        return "ingesta"
    if ruta.startswith("src/Transformacion"):
        return "transformacion"
    if ruta.startswith("src/modelo"):
        return "modelado"
    if ruta.startswith("src/analisis"):
        return "analisis"
    if ruta.startswith("scripts/"):
        return "orquestacion"
    if ruta.startswith("notebooks/tarea"):
        return "legacy"
    if "streamlit" in ruta or ruta.startswith("app/"):
        return "visualizacion"
    if ruta.startswith("tests/"):
        return "testing"
    if ruta.startswith("docs/") or ruta.startswith("notebooks/01"):
        return "documentacion" if "manual" in ruta else "eda"
    return "otro"


def generar_09() -> Path:
    """Genera secciones/09_apendice_inventario.tex con el inventario."""
    destino = SECCIONES / "09_apendice_inventario.tex"
    if not INVENTARIO_CSV.exists():
        destino.write_text("% inventario pendiente\n", encoding="utf-8")
        return destino

    analisis = _leer_analisis()
    filas = _leer_inventario()

    cuerpo = ""
    for f in filas:
        rol = _rol_por_ruta(f["ruta"], analisis)
        cuerpo += (
            f"    {codigo_en_linea(f['ruta'])} & {f['lenguaje']} & {f['lineas']} & "
            f"{f['kb']} & {escapar(rol)} \\\\\n"
        )

    contenido = f"""% ============ 09. Apéndice: inventario de código ============
\\section{{Apéndice A: Inventario de archivos de código}}

\\begingroup
\\scriptsize
\\begin{{longtable}}{{>{{\\raggedright\\arraybackslash}}p{{6.2cm}} l rr >{{\\raggedright\\arraybackslash}}p{{3.0cm}}}}
\\caption{{Inventario de los {len(filas)} archivos de código del repositorio}}
\\label{{tab:inventario}}\\\\
\\toprule
\\textbf{{Ruta}} & \\textbf{{Lenguaje}} & \\textbf{{Líneas}} & \\textbf{{KB}} & \\textbf{{Rol}} \\\\
\\midrule
\\endfirsthead
\\toprule
\\textbf{{Ruta}} & \\textbf{{Lenguaje}} & \\textbf{{Líneas}} & \\textbf{{KB}} & \\textbf{{Rol}} \\\\
\\midrule
\\endhead
{cuerpo}\\bottomrule
\\end{{longtable}}
\\endgroup
"""
    destino.write_text(contenido, encoding="utf-8")
    print(f"[09] {destino} ({len(filas)} archivos)")
    return destino


def _verificar_controles(archivo: Path) -> None:
    """Comprueba que el .tex generado no contenga caracteres de control
    (p. ej. 0x08 por '\\b' mal escapado en un f-string)."""
    datos = archivo.read_bytes()
    malos = sorted({b for b in datos if b < 32 and b not in (9, 10, 13)})
    if malos:
        print(f"[AVISO] {archivo.name} contiene caracteres de control: "
              f"{[hex(m) for m in malos]}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

SECCIONES_DISPONIBLES = {"05": generar_05, "08": generar_08, "09": generar_09}


def main() -> None:
    solo = None
    if "--solo" in sys.argv:
        i = sys.argv.index("--solo")
        solo = sys.argv[i + 1]

    SECCIONES.mkdir(parents=True, exist_ok=True)
    if solo:
        if solo in SECCIONES_DISPONIBLES:
            SECCIONES_DISPONIBLES[solo]()
        else:
            print(f"Sección desconocida: {solo}. Disponibles: {list(SECCIONES_DISPONIBLES)}")
        return

    for gen in SECCIONES_DISPONIBLES.values():
        destino = gen()
        _verificar_controles(destino)
    print("Generación de secciones completada.")


if __name__ == "__main__":
    main()
