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

Uso:
    python -m memoria dibujar                                  # figura por defecto
    python -m memoria dibujar --tipos Criterio,Documento        # solo esos tipos
    python -m memoria dibujar --html                            # además, HTML
"""

from __future__ import annotations

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
