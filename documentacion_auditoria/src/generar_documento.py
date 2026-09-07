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
# Capas arquitectónicas (fuente de verdad: data/capas.yaml)
# ---------------------------------------------------------------------------
CAPAS_YAML = DATA / "capas.yaml"
CAPA_TITULOS = dict(ROLES_ORDEN) | {
    "otro": "Otros archivos",
}
_CAPAS_CACHE: dict | None = None


def _cargar_capas() -> tuple[list[str], dict[str, list[str]]]:
    """Carga orden y reglas de capas desde data/capas.yaml (fuente de verdad)."""
    global _CAPAS_CACHE
    if _CAPAS_CACHE is not None:
        return _CAPAS_CACHE
    if not CAPAS_YAML.exists():
        _CAPAS_CACHE = (["otro"], {"otro": []})
        return _CAPAS_CACHE
    import yaml as _yaml
    with open(CAPAS_YAML, encoding="utf-8-sig") as fh:
        data = _yaml.safe_load(fh)
    orden = data.get("orden", ["otro"])
    reglas = data.get("reglas", {})
    _CAPAS_CACHE = (orden, reglas)
    return _CAPAS_CACHE


def capa_de_ruta(ruta: str) -> str:
    """Asigna la capa canónica de un archivo según data/capas.yaml.
    Se evalúa en el orden de 'orden'; el primer prefijo que coincida gana."""
    orden, reglas = _cargar_capas()
    r = ruta.replace("\\", "/").lower()
    for capa in orden:
        for prefijo in reglas.get(capa, []):
            if r.startswith(prefijo.lower()):
                return capa
    return "otro"


def titulo_capa(capa: str) -> str:
    return CAPA_TITULOS.get(capa, capa.capitalize())


# ---------------------------------------------------------------------------
# Fragmentos de código reales (para hallazgos archivo.py:N-M)
# ---------------------------------------------------------------------------
REPO = RAIZ.parent / "Observatorio_Ministerio_de_Ciencias_Grupo8"
_FRAG_CACHE: dict[str, list[str]] = {}


def _leer_lineas_repo(ruta: str) -> list[str]:
    """Lee las líneas de un archivo del repositorio auditado (con caché)."""
    if ruta in _FRAG_CACHE:
        return _FRAG_CACHE[ruta]
    candidatos = [REPO / ruta]
    if "\\" in ruta or "/" in ruta:
        candidatos.append(REPO / ruta.replace("\\", "/"))
    else:  # solo nombre base: buscar en todo el repo
        candidatos = [p for p in REPO.rglob(ruta) if p.is_file()]
    for cand in candidatos:
        if cand and cand.exists():
            try:
                lineas = cand.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                lineas = []
            _FRAG_CACHE[ruta] = lineas
            return lineas
    _FRAG_CACHE[ruta] = []
    return []


def fragmento_latex(ruta: str, inicio: int, fin: int | None = None,
                    max_lineas: int = 6) -> str:
    """Extrae el fragmento real de código (ruta:N-M) y lo envuelve en un
    bloque lstlisting de máximo `max_lineas` líneas. Devuelve '' si no hay."""
    lineas = _leer_lineas_repo(ruta)
    if not lineas:
        return ""
    n = max(1, inicio)
    m = fin if fin is not None else n
    m = max(m, n)
    recorte = lineas[n - 1:m]
    truncado = len(recorte) > max_lineas
    recorte = recorte[:max_lineas]
    cuerpo = "\n".join(recorte)
    if truncado:
        cuerpo += "\n[...]"
    return ("\\begin{lstlisting}\n" + cuerpo + "\n\\end{lstlisting}\n")

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


def _bugs_con_fragmentos(bugs: list[str]) -> str:
    """Renderiza la lista de bugs y, para cada referencia archivo.py:N-M,
    incrusta el fragmento real del código (máx. 6 líneas)."""
    partes: list[str] = ["\\begin{itemize}"]
    patron = re.compile(r"([A-Za-z0-9_\-./\\]+\.(?:py|R|ipynb)):(\d+)(?:-(\d+))?")
    for bug in bugs:
        partes.append("  \\item " + escapar(bug))
        for m in patron.finditer(bug):
            ruta = m.group(1).replace("\\", "/")
            inicio = int(m.group(2))
            fin = int(m.group(3)) if m.group(3) else None
            frag = fragmento_latex(ruta, inicio, fin)
            if frag:
                partes.append("\\begin{quote}\\footnotesize\\ttfamily\n"
                              + f"\\noindent\\emph{{Evidencia en {escapar(ruta)} "
                              + f"(línea{'' if inicio == (fin or inicio) else 's'} "
                              + f"{inicio}{'-' + str(fin) if fin and fin != inicio else ''}):}}"
                              + "\n\\end{quote}")
                partes.append(frag)
    partes.append("\\end{itemize}")
    return "\n".join(partes)


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
            _bugs_con_fragmentos(a["bugs"]),
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
    # Agrupar por capa canónica (data/capas.yaml), no por rol del JSON
    orden_capas, _ = _cargar_capas()
    grupos: dict[str, list[dict]] = {}
    for a in analisis:
        capa = capa_de_ruta(a.get("archivo", ""))
        grupos.setdefault(capa, []).append(a)

    cuerpo: list[str] = []
    capas_presentes = [c for c in orden_capas if c in grupos]
    for capa in capas_presentes:
        titulo = titulo_capa(capa)
        cuerpo.append("\\subsection{" + escapar(titulo) + "}")
        cuerpo.append(f"\\noindent Archivos: {len(grupos[capa])}.")
        cuerpo.append("")
        for a in sorted(grupos[capa], key=lambda x: x.get("archivo", "")):
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
\\textbf{{{commits[0]['fecha']}}} y \\textbf{{{commits[-1]['fecha']}}} por 11
autores (\\textbf{{{len(por_autor)}}} identidades nombre+correo; la tabla
siguiente desglosa por identidad). La actividad no fue continua: tras la fase
académica (ago--nov 2025) hubo un \\textbf{{hiato de ~100 días}} (2025-11-18 a
2026-02-26) sin commits, y la fase de ingeniería de datos (pipelines,
sprints 2--6, DuckDB, dashboard) se concentró en feb--may 2026.

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
  \\item Entre el 2025-11-18 y el 2026-02-26 no hay actividad (\\textbf{{hiato de
        ~100 días}}); la consolidación del pipeline (ingesta, transformación,
        modelo dimensional y sprints) se concentra en feb--may 2026.
  \\item Los sprints 5 y 6 (abr--may 2026), liderados por Victor-Diaz-Usta
        (39 commits por nombre; 34 con un correo y 5 con otro), incorporan
        producción, calidad, tabla maestra IES y Sankeys, cerrando los ajustes
        del director.
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
