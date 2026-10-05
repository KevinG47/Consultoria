# -*- coding: utf-8 -*-
"""
memoria.visual
==============

Dibujo del grafo de memoria (`python -m memoria dibujar`).

Objetivo: producir una figura legible en una diapositiva. El grafo completo
(255 nodos) es ilegible con etiquetas, así que por defecto se dibuja un
subconjunto estructural y se permite filtrar por tipo de nodo con --tipos.

Salidas:
  - PNG con matplotlib (determinista: layout con semilla fija).
  - HTML interactivo con plotly si se pide --html.
  - HTML interactivo con PyVis: comandos `dibujar --interactivo` (PNG + HTML) y
    `dibujar-html` (solo el HTML). Autocontenido (funciona sin internet), con
    etiquetas de relación, colores y formas por tipo, tooltips y leyenda.
    Pensado para sustentación en pantalla.

Uso:
    python -m memoria dibujar                                  # figura por defecto
    python -m memoria dibujar --tipos Criterio,Documento        # solo esos tipos
    python -m memoria dibujar --html                            # además, HTML (plotly)
    python -m memoria dibujar --interactivo                     # además, HTML (PyVis)
    python -m memoria dibujar-html --tipos Criterio,Documento   # solo el HTML PyVis
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import config, grafo

# Colores por tipo de nodo (legibles en proyector)
COLORES = {
    "Criterio": "#1e3780",
    "Documento": "#3d7ebf",
    "DocumentoValidacion": "#7fb3d5",
    "TerminoGlosario": "#b7871e",
    "Capa": "#4f8f4f",
    "ArchivoCodigo": "#8f6f4f",
    "Commit": "#999999",
    "Autor": "#c0504d",
}
# Tipos que se dibujan por defecto (el resto haría la figura ilegible)
TIPOS_POR_DEFECTO = ["Criterio", "Documento", "TerminoGlosario", "Capa", "DocumentoValidacion"]


def _subgrafo(g, tipos: list[str] | None):
    keep = {n for n, d in g.nodes(data=True) if not tipos or d.get("tipo") in tipos}
    sub = g.subgraph(keep).copy()
    return sub


def dibujar(tipos: list[str] | None = None,
            salida: Path | None = None,
            titulo: str | None = None,
            html: bool = False,
            refrescar_git: bool = False) -> dict:
    """Genera la figura del grafo filtrada por tipos de nodo."""
    import matplotlib
    matplotlib.use("Agg")                    # sin ventana interactiva
    import matplotlib.pyplot as plt
    import networkx as nx

    g, resumen = grafo.construir(refrescar_git=refrescar_git, guardar=False)
    tipos = tipos or TIPOS_POR_DEFECTO
    sub = _subgrafo(g, tipos)

    salida = salida or config.GRAFICO_PNG
    salida.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 9))
    pos = nx.spring_layout(sub, k=0.9, iterations=250, seed=7)

    por_tipo: dict[str, list] = {}
    for n, d in sub.nodes(data=True):
        por_tipo.setdefault(d.get("tipo", "?"), []).append(n)

    for tipo, nodos in por_tipo.items():
        grados = [max(1, sub.degree(n)) for n in nodos]
        nx.draw_networkx_nodes(sub, pos, nodelist=nodos, ax=ax,
                               node_color=COLORES.get(tipo, "#888888"),
                               node_size=[260 + 90 * gr for gr in grados],
                               edgecolors="white", linewidths=1.0, label=f"{tipo} ({len(nodos)})")
    nx.draw_networkx_edges(sub, pos, ax=ax, alpha=0.35, arrows=True,
                           arrowsize=9, edge_color="#666666", width=0.8)

    etiquetas = {}
    for n, d in sub.nodes(data=True):
        tipo = d.get("tipo")
        if tipo == "Criterio":
            etiquetas[n] = d.get("titulo", n)[:28]
        elif tipo == "Documento":
            etiquetas[n] = d.get("nombre", n).replace("doc::", "")
        elif tipo == "Capa":
            etiquetas[n] = d.get("nombre", n)
        elif tipo == "TerminoGlosario":
            etiquetas[n] = d.get("termino", "")[:22]
        elif tipo == "DocumentoValidacion":
            etiquetas[n] = d.get("nombre", "")[:20]
    nx.draw_networkx_labels(sub, pos, labels=etiquetas, ax=ax, font_size=7)

    ax.set_title(titulo or (f"Memoria estructural del agente — {sub.number_of_nodes()} nodos / "
                            f"{sub.number_of_edges()} aristas (tipos: {', '.join(tipos)})"),
                 fontsize=12)
    ax.legend(loc="upper left", fontsize=8, frameon=True)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(salida, dpi=160, bbox_inches="tight")
    plt.close(fig)

    resultado = {
        "salida": str(salida),
        "nodos_dibujados": sub.number_of_nodes(),
        "aristas_dibujadas": sub.number_of_edges(),
        "tipos": tipos,
        "nodos_totales_grafo": resumen.total_nodos,
        "aristas_totales_grafo": resumen.total_aristas,
    }

    if html:
        try:
            import plotly.graph_objects as go
            pos3 = nx.spring_layout(sub, dim=3, seed=7)
            aristas_x, aristas_y, aristas_z = [], [], []
            for u, v in sub.edges():
                aristas_x += [pos3[u][0], pos3[v][0], None]
                aristas_y += [pos3[u][1], pos3[v][1], None]
                aristas_z += [pos3[u][2], pos3[v][2], None]
            trazas = [go.Scatter3d(x=aristas_x, y=aristas_y, z=aristas_z, mode="lines",
                                   line=dict(color="#888", width=2), hoverinfo="none", name="relaciones")]
            for tipo, nodos in por_tipo.items():
                trazas.append(go.Scatter3d(
                    x=[pos3[n][0] for n in nodos], y=[pos3[n][1] for n in nodos], z=[pos3[n][2] for n in nodos],
                    mode="markers+text", name=tipo,
                    text=[etiquetas.get(n, n) for n in nodos], textposition="top center",
                    marker=dict(size=5, color=COLORES.get(tipo, "#888")),
                    hovertext=[f"{n} · {tipo}" for n in nodos]))
            fig3 = go.Figure(data=trazas)
            fig3.update_layout(title="Memoria estructural del agente (interactivo)",
                               showlegend=True, margin=dict(l=0, r=0, t=40, b=0))
            html_path = salida.with_suffix(".html")
            fig3.write_html(str(html_path))
            resultado["salida_html"] = str(html_path)
        except Exception as exc:                                  # noqa: BLE001
            resultado["aviso_html"] = f"No se pudo generar HTML: {exc}"

    return resultado


# --------------------------------------------------------------------------
# Vista interactiva con PyVis (sustentación en pantalla)
# --------------------------------------------------------------------------
# Paleta pedida para la sustentación. NO sustituye a COLORES: el PNG de
# matplotlib sigue igual (es el respaldo). Aquí los Documento se separan por
# variante y el maestro de auditoría tiene color y tamaño propios.
COLORES_INTERACTIVO = {
    "Criterio": "#1E3780",             # azul oscuro
    "Documento": "#7BA7D0",            # azul claro (documento completo del criterio)
    "DocumentoLite": "#B0B0B0",        # gris (versión LITE)
    "DocumentoMaestro": "#B7871E",     # dorado (maestro de auditoría)
    "DocumentoValidacion": "#8E7CC3",  # violeta
    "TerminoGlosario": "#2E7D32",      # verde
    "Capa": "#00695C",                 # verde azulado
    "ArchivoCodigo": "#795548",        # marrón
    "Commit": "#607D8B",               # gris azulado
    "Autor": "#C62828",                # rojo
}

# Etiquetas legibles de las relaciones REALES del grafo (nombres y dirección
# tomados de grafo.py, no supuestos).
REL_ETIQUETAS = {
    "tiene_documento": "GENERA",          # Criterio -> Documento completo
    "consolidado_en": "CONSOLIDA EN",     # Criterio -> maestro de auditoría
    "verificado_por": "VERIFICADO POR",   # Criterio -> informe de validación
    "usa_termino": "USA TÉRMINO",         # Documento -> término del glosario
    "pertenece_a": "PERTENECE A",         # ArchivoCodigo -> Capa
    "documenta": "DOCUMENTA",             # Documento -> ArchivoCodigo / Commit
    "tiene_autor": "AUTOR",               # Commit -> Autor
}
REL_ETIQUETA_LITE = "RESUME EN"           # Criterio -> Documento variante LITE

COLORES_REL = {
    "tiene_documento": "#1E3780",
    "consolidado_en": "#B7871E",
    "verificado_por": "#8E7CC3",
    "usa_termino": "#2E7D32",
    "pertenece_a": "#00695C",
    "documenta": "#795548",
    "tiene_autor": "#607D8B",
}

FORMAS_INTERACTIVO = {
    "Criterio": "dot", "Documento": "box", "DocumentoValidacion": "box",
    "TerminoGlosario": "ellipse", "Capa": "box", "ArchivoCodigo": "box",
    "Commit": "dot", "Autor": "ellipse",
}
# Niveles del layout jerárquico. vis.js exige que TODOS los nodos tengan nivel si
# alguno lo tiene, así que se define para los 9 tipos (no solo los de la vista
# filtrada). El maestro de auditoría va al último nivel para que la lectura sea de
# arriba abajo (criterios -> documentos -> maestro que los consolida), en vez de
# quedar al final de la fila de documentos.
# Nota medida: el NÚMERO de cruces de aristas resultó inestable entre mediciones
# (31 / 57 / 58 / 6 para layouts casi idénticos), así que no se usa como criterio.
# Los cruces que quedan son estructurales: el maestro recibe 6 aristas desde la
# fila de criterios y cualquier layout tiene que atravesar la fila de documentos.
NIVELES_HIERARQUICOS = {
    "Criterio": 0, "Documento": 1, "DocumentoValidacion": 1, "DocumentoMaestro": 2,
    "TerminoGlosario": 2, "ArchivoCodigo": 2, "Commit": 2, "Capa": 3, "Autor": 3,
}
TAMANOS_INTERACTIVO = {"Criterio": 46, "DocumentoValidacion": 14, "TerminoGlosario": 16,
                       "Capa": 18, "ArchivoCodigo": 12, "Commit": 10, "Autor": 16}
# Los nodos con forma "box" se dimensionan por su etiqueta: la jerarquía visual
# se controla con la fuente y el margen (el maestro es el más grande de todos).
FUENTE_INTERACTIVO = {"Criterio": 19, "Documento": 17, "DocumentoLite": 14,
                      "DocumentoMaestro": 20, "DocumentoValidacion": 13,
                      "TerminoGlosario": 14, "Capa": 16, "ArchivoCodigo": 11,
                      "Commit": 11, "Autor": 14}
MARGEN_INTERACTIVO = {"Documento": 14, "DocumentoLite": 9, "DocumentoMaestro": 20,
                      "DocumentoValidacion": 8, "Capa": 12, "ArchivoCodigo": 6}
ANCHO_ETIQUETA = {"Criterio": 22, "TerminoGlosario": 18, "ArchivoCodigo": 24,
                  "Autor": 16, "DocumentoValidacion": 20, "Documento": 22}
DESCRIPCION_REL = {
    "GENERA": "el criterio genera su documento completo",
    "RESUME EN": "el criterio tiene versión LITE (resumen del completo)",
    "CONSOLIDA EN": "el criterio se consolida en el maestro de auditoría",
    "VERIFICADO POR": "el criterio fue verificado por ese informe",
    "USA TÉRMINO": "el documento usa ese término del glosario",
    "PERTENECE A": "el archivo pertenece a esa capa del pipeline",
    "DOCUMENTA": "el documento documenta ese archivo de código o commit",
    "AUTOR": "el commit fue hecho por ese autor",
}
DESCRIPCION_TIPO = {
    "Criterio": "criterio de la rúbrica (nodo raíz)",
    "Documento": "documento completo del criterio",
    "DocumentoLite": "versión LITE del documento",
    "DocumentoMaestro": "maestro de auditoría (integra los 6 criterios)",
    "DocumentoValidacion": "informe de validación del criterio",
    "TerminoGlosario": "término del glosario",
    "Capa": "capa del pipeline",
    "ArchivoCodigo": "archivo de código del repo auditado",
    "Commit": "commit del repositorio auditado",
    "Autor": "autor de commits",
}

GRAFICO_HTML = config.MEMORIA / "grafo_interactivo.html"
TIPOS_POR_DEFECTO_HTML = ["Criterio", "Documento"]

_OPCIONES_INTERACTIVO = {
    "layout": {"hierarchical": {"enabled": True, "direction": "UD", "sortMethod": "directed",
                                "levelSeparation": 260, "nodeSpacing": 260,
                                "treeSpacing": 300, "blockShifting": True,
                                "edgeMinimization": True, "parentCentralization": True}},
    "physics": {"enabled": False},
    "interaction": {"dragNodes": True, "dragView": True, "zoomView": True, "hover": True,
                    "tooltipDelay": 120, "navigationButtons": True, "keyboard": True},
    "nodes": {"borderWidth": 2, "borderWidthSelected": 4,
              "font": {"face": "Segoe UI, Arial, sans-serif", "strokeWidth": 4,
                       "strokeColor": "#ffffff"},
              "shadow": {"enabled": True, "color": "rgba(0,0,0,0.15)", "size": 8, "x": 2, "y": 3}},
    "edges": {"arrows": {"to": {"enabled": True, "scaleFactor": 1.1}},
              "font": {"size": 15, "align": "middle", "face": "Segoe UI, Arial, sans-serif",
                       "strokeWidth": 4, "strokeColor": "#ffffff"},
              "smooth": {"enabled": True, "type": "cubicBezier",
                         "forceDirection": "vertical", "roundness": 0.45}},
}


def _clave_visual(n, d) -> str:
    """Clave de color/fuente: separa los Documento por variante y maestro."""
    tipo = d.get("tipo", "?")
    if tipo != "Documento":
        return tipo
    nombre = str(d.get("nombre", n))
    if nombre == "maestro_auditoria" or str(d.get("ruta", "")).endswith("maestro_auditoria"):
        return "DocumentoMaestro"
    return "DocumentoLite" if d.get("variante") == "lite" else "Documento"


def _nivel(n, d) -> int:
    """Nivel jerárquico del nodo (el maestro de auditoría va al último)."""
    return NIVELES_HIERARQUICOS.get(_clave_visual(n, d), 1)


def _envolver(texto: str, ancho: int) -> str:
    """Envuelve la etiqueta en varias líneas (vis.js no corta por sí solo)."""
    import textwrap
    return "\n".join(textwrap.wrap(texto, ancho)) or texto


def _etiqueta_nodo(n, d) -> str:
    """Etiqueta legible: nunca el id interno cuando hay algo mejor."""
    tipo = d.get("tipo")
    if tipo == "Criterio":
        return _envolver(str(d.get("titulo", n)), ANCHO_ETIQUETA["Criterio"])
    if tipo == "Documento":
        nombre = str(d.get("nombre", str(n).replace("doc::", "")))
        if nombre == "maestro_auditoria":
            return "MAESTRO DE\nAUDITORÍA"
        m = re.match(r"objetivo_(\d+)(_lite)?$", nombre)
        if m:
            return f"Criterio {m.group(1)}\n{'LITE' if m.group(2) else 'completo'}"
        return _envolver(nombre, ANCHO_ETIQUETA["Documento"])
    if tipo == "TerminoGlosario":
        return _envolver(str(d.get("termino", n)), ANCHO_ETIQUETA["TerminoGlosario"])
    if tipo == "DocumentoValidacion":
        return _envolver(str(d.get("nombre", n)), ANCHO_ETIQUETA["DocumentoValidacion"])
    if tipo == "Capa":
        return str(d.get("nombre", n))
    if tipo == "ArchivoCodigo":
        return _envolver(str(d.get("ruta", n)).split("/")[-1], ANCHO_ETIQUETA["ArchivoCodigo"])
    if tipo == "Commit":
        return str(d.get("hash", n))[:7]
    if tipo == "Autor":
        return _envolver(str(d.get("nombre", n)), ANCHO_ETIQUETA["Autor"])
    return str(n)


def _tooltip_nodo(n, d) -> str:
    """Tooltip HTML: tipo, id y —si aplica— la ruta real en el repositorio."""
    tipo = d.get("tipo", "?")
    filas = [f"<b>{tipo}</b>"]
    if tipo == "Criterio":
        filas += [f"id: <code>{n}</code>", f"título: {d.get('titulo', '')}"]
    elif tipo == "Documento":
        clave = _clave_visual(n, d)
        filas += [f"nombre: <code>{d.get('nombre', '')}</code>",
                  {"DocumentoMaestro": "maestro de auditoría (integra los 6 criterios)",
                   "DocumentoLite": "versión LITE", "Documento": "documento completo"}[clave],
                  f"ruta: <code>{d.get('ruta', '')}</code>",
                  f"palabras: {d.get('palabras', '?')}"]
    elif tipo == "DocumentoValidacion":
        filas += [f"archivo: <code>{d.get('nombre', '')}</code>",
                  f"ruta: <code>{d.get('ruta', '')}</code>", f"tamaño: {d.get('kb', '?')} KB"]
    elif tipo == "TerminoGlosario":
        filas += [f"término: <b>{d.get('termino', '')}</b>"]
    elif tipo == "Capa":
        filas += [f"capa: <b>{d.get('nombre', '')}</b>"]
    elif tipo == "ArchivoCodigo":
        filas += [f"ruta: <code>{d.get('ruta', '')}</code>", f"capa: {d.get('capa', '?')}",
                  f"documentado: {d.get('documentado')}", f"real: {d.get('real')}"]
    elif tipo == "Commit":
        filas += [f"hash: <code>{d.get('hash', '')}</code>", f"fecha: {d.get('fecha', '')}",
                  f"asunto: {str(d.get('asunto', ''))[:80]}", f"documentado: {d.get('documentado')}"]
    elif tipo == "Autor":
        filas += [f"autor: {d.get('nombre', '')}", f"email: {d.get('email', '')}"]
    return "<br>".join(filas)


def _etiqueta_rel(d) -> str:
    """Etiqueta de la arista según la relación real (y la variante del documento)."""
    rel = str(d.get("rel", ""))
    if rel == "tiene_documento" and d.get("variante") == "lite":
        return REL_ETIQUETA_LITE
    return REL_ETIQUETAS.get(rel, rel.upper().replace("_", " "))


def _leyenda_html(claves: list[str], relaciones: list[tuple[str, str]], n_nodos: int,
                  n_aristas: int, titulo: str) -> str:
    """Tarjeta de leyenda incrustada en el HTML (sin dependencias externas)."""
    caja = ('width:15px;height:15px;border-radius:50%;display:inline-block;flex:0 0 auto;')
    filas = []
    for c in claves:
        forma = "border-radius:50%" if FORMAS_INTERACTIVO.get(c, "dot") == "dot" else "border-radius:3px"
        filas.append(
            f'<div style="display:flex;align-items:center;gap:9px;margin:4px 0">'
            f'<span style="{caja}{forma};background:{COLORES_INTERACTIVO.get(c, "#888")}"></span>'
            f'<span><b>{c}</b> — {DESCRIPCION_TIPO.get(c, "")}</span></div>')
    rels = "".join(
        f'<div style="display:flex;align-items:center;gap:9px;margin:4px 0">'
        f'<span style="width:26px;height:0;border-top:3px solid {color};'
        f'display:inline-block;flex:0 0 auto"></span>'
        f'<span><b>{etiqueta}</b> — {DESCRIPCION_REL.get(etiqueta, "")}</span></div>'
        for etiqueta, color in relaciones)
    return f"""
<div id="leyenda-memoria" style="position:fixed;top:14px;right:14px;z-index:9999;
     background:rgba(255,255,255,0.97);border:1px solid #d0d0d0;border-radius:12px;
     padding:14px 16px;font:13px/1.5 'Segoe UI',Arial,sans-serif;color:#222;
     box-shadow:0 3px 14px rgba(0,0,0,0.18);max-width:330px">
  <div style="font-size:15px;font-weight:700;margin-bottom:2px">{titulo}</div>
  <div style="color:#666;margin-bottom:8px">{n_nodos} nodos · {n_aristas} relaciones</div>
  <div style="font-weight:700;margin:6px 0 2px">Qué es cada nodo</div>
  {''.join(filas)}
  <div style="font-weight:700;margin:10px 0 2px">Qué representa cada flecha</div>
  {rels}
  <div style="color:#666;margin-top:10px;border-top:1px solid #eee;padding-top:8px">
    Arrastra los nodos · rueda del ratón para acercar · pasa el cursor para ver el detalle
    (tipo, id y ruta real del archivo).
  </div>
</div>
"""


def dibujar_html(tipos: list[str] | None = None,
                 salida: Path | None = None,
                 titulo: str | None = None,
                 refrescar_git: bool = False) -> dict:
    """
    Genera la vista interactiva del grafo con PyVis (HTML autocontenido).

    El layout es jerárquico con niveles explícitos por tipo: criterios arriba,
    documentos en el medio y el maestro de auditoría (y el resto de tipos) abajo,
    de modo que la lectura sea de arriba abajo. Antes, sin niveles, vis.js dejaba
    el maestro al final de la fila de documentos.

    Devuelve un dict con la ruta, los conteos y el detalle de tipos. Si PyVis no
    está instalado, devuelve {'error', 'sugerencia'} en vez de fallar: el comando
    lo imprime y sugiere `pip install pyvis`.
    """
    try:
        from pyvis.network import Network
    except Exception as exc:                                       # noqa: BLE001
        return {"error": f"PyVis no está instalado ({type(exc).__name__}).",
                "sugerencia": "pip install pyvis"}

    g, resumen = grafo.construir(refrescar_git=refrescar_git, guardar=False)
    tipos = tipos or TIPOS_POR_DEFECTO_HTML
    sub = _subgrafo(g, tipos)

    salida = Path(salida) if salida else GRAFICO_HTML
    salida.parent.mkdir(parents=True, exist_ok=True)
    n_nodos, n_aristas = sub.number_of_nodes(), sub.number_of_edges()
    encabezado = titulo or "Memoria estructural del agente"

    net = Network(height="900px", width="100%", directed=True, bgcolor="#ffffff",
                  font_color="#222222", cdn_resources="in_line", heading=encabezado)

    claves_presentes: list[str] = []
    for n, d in sub.nodes(data=True):
        clave = _clave_visual(n, d)
        if clave not in claves_presentes:
            claves_presentes.append(clave)
        net.add_node(n, label=_etiqueta_nodo(n, d), title=_tooltip_nodo(n, d),
                     color=COLORES_INTERACTIVO.get(clave, "#888888"),
                     shape=FORMAS_INTERACTIVO.get(d.get("tipo", ""), "dot"),
                     size=TAMANOS_INTERACTIVO.get(clave, 18),
                     font={"size": FUENTE_INTERACTIVO.get(clave, 14)},
                     margin=MARGEN_INTERACTIVO.get(clave, 10),
                     level=_nivel(n, d),
                     borderWidth=4 if clave == "DocumentoMaestro" else 2)

    relaciones_presentes: list[str] = []
    etiquetas_rel: list[tuple[str, str]] = []          # (etiqueta visible, color)
    for u, v, d in sub.edges(data=True):
        rel = str(d.get("rel", ""))
        if rel not in relaciones_presentes:
            relaciones_presentes.append(rel)
        etiqueta = _etiqueta_rel(d)
        color_rel = (COLORES_INTERACTIVO["DocumentoLite"] if etiqueta == REL_ETIQUETA_LITE
                     else COLORES_REL.get(rel, "#888888"))
        if (etiqueta, color_rel) not in etiquetas_rel:
            etiquetas_rel.append((etiqueta, color_rel))
        net.add_edge(u, v, label=etiqueta, title=f"relación: {rel}" +
                     (f" · variante: {d.get('variante')}" if d.get("variante") else ""),
                     color=color_rel,
                     width=2.6 if rel in ("tiene_documento", "consolidado_en") else 1.6,
                     font={"size": 15})

    net.set_options(json.dumps(_OPCIONES_INTERACTIVO, indent=2))

    # PyVis 0.3.x escribe el HTML con la codificación por defecto de Windows
    # (cp1252) y el bundle de vis.js trae caracteres fuera de cp1252, lo que hace
    # fallar write_html con UnicodeEncodeError. Se genera en memoria y se escribe
    # aquí en UTF-8 (y así la leyenda se inyecta antes de guardar).
    html = net.generate_html(notebook=False)

    # El template de PyVis deja Bootstrap por CDN (solo lo usan los menús
    # opcionales de selección/filtro, que no activamos): se elimina para que el
    # HTML funcione sin internet y no haga ninguna petición de red.
    html = re.sub(r'<script[^>]+src="https?://[^"]+"[^>]*>\s*</script>', "", html)
    html = re.sub(r'<link[^>]+href="https?://[^"]+"[^>]*>', "", html)

    leyenda = _leyenda_html(claves_presentes, etiquetas_rel, n_nodos, n_aristas, encabezado)
    from datetime import datetime as _dt
    pie = (f'<div style="position:fixed;bottom:8px;left:14px;z-index:9999;font:12px \'Segoe UI\',Arial;'
           f'color:#666;background:rgba(255,255,255,.9);padding:4px 10px;border-radius:8px">'
           f'Generado por <code>python -m memoria dibujar-html</code> · '
           f'{_dt.now():%Y-%m-%d %H:%M} · {resumen.total_nodos} nodos / {resumen.total_aristas} '
           f'relaciones en el grafo completo</div>')
    ajuste = ('<script>setTimeout(function(){try{ if (typeof network !== "undefined" && '
              'network && network.fit) { network.fit({animation:false}); } }catch(e){}}, 350);</script>')
    html = html.replace("</body>", leyenda + pie + ajuste + "</body>")
    salida.write_text(html, encoding="utf-8")

    # Autocontenido = sin NINGUNA carga externa real (se ignoran comentarios y
    # las URLs que van dentro del JS, que no se descargan).
    _sin_comentarios = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    _cargas = [u for u in re.findall(r'<(?:script|link|img)[^>]*?(?:src|href)="([^"]+)"',
                                     _sin_comentarios)
               if not u.startswith(("data:", "#"))]
    sin_internet = not _cargas
    return {
        "salida": str(salida),
        "nodos_dibujados": n_nodos,
        "aristas_dibujadas": n_aristas,
        "tipos": tipos,
        "claves_visuales": claves_presentes,
        "relaciones_dibujadas": relaciones_presentes,
        "nodos_totales_grafo": resumen.total_nodos,
        "aristas_totales_grafo": resumen.total_aristas,
        "peso_kb": round(salida.stat().st_size / 1024, 1),
        "autocontenido": sin_internet,
    }
