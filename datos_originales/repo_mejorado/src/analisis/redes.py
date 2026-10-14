"""
analisis/redes.py

Network analysis de co-filiacion institucional — Issues #15 y #16.

Un investigador con dos instituciones en inst_filia crea un enlace entre ambas.
Nodo = institucion; arista = investigadores compartidos (peso = conteo).
"""

import pathlib
import re

import pandas as pd


def normalizar_institucion(nombre) -> str:
    """
    Colapsa variantes (sedes, parentesis, mayusculas) a una sola entidad.

    Reglas:
    - Si hay parentesis y contiene una institucion (Universidad/Instituto/etc),
      ese parentesis ES la institucion madre -> usarlo
    - Si no, eliminar contenido entre parentesis
    - Eliminar sufijos de sede: " SEDE X", " SECCIONAL X", " - SEDE"
    - Mayusculas y espacios normalizados
    """
    if pd.isna(nombre) or not str(nombre).strip():
        return nombre
    s = str(nombre).upper().strip()

    # Detectar institucion madre dentro de parentesis
    m = re.search(r"\(([^)]+)\)", s)
    if m:
        contenido = m.group(1).strip()
        marcadores = ["UNIVERSIDAD", "INSTITUTO", "CORPORACION", "FUNDACION",
                      "COLEGIO", "ESCUELA", "POLITECNICO", "POLITÉCNICO",
                      "CENTRO", "HOSPITAL"]
        if len(contenido.split()) >= 2 and any(k in contenido for k in marcadores):
            s = contenido
        else:
            s = re.sub(r"\s*\([^)]*\)", "", s).strip()

    # Eliminar sufijos de sedes / seccionales
    for marcador in [" SEDE ", " SECCIONAL ", " - SEDE", " - SECCIONAL"]:
        if marcador in s:
            s = s.split(marcador)[0].strip()

    return " ".join(s.split())
import networkx as nx


def construir_pares(df: pd.DataFrame, normalizar: bool = True) -> pd.DataFrame:
    """
    Extrae pares (inst_a, inst_b) de investigadores con doble afiliacion.

    Si normalizar=True (default), aplica normalizar_institucion() para colapsar
    sedes y variantes (UNAL Bogota + UNAL Medellin -> UNAL).

    Retorna columnas: [ID_PERSONA_PR, ANO_CONVO_INT, inst_a, inst_b]
    """
    multi = df[df["INST_FILIA"].str.contains("|", na=False, regex=False)].copy()
    multi[["inst_a", "inst_b"]] = (
        multi["INST_FILIA"]
        .str.split("|", n=1, expand=True)
        .apply(lambda s: s.str.strip())
    )
    if normalizar:
        multi["inst_a"] = multi["inst_a"].map(normalizar_institucion)
        multi["inst_b"] = multi["inst_b"].map(normalizar_institucion)
    else:
        multi["inst_a"] = multi["inst_a"].str.upper().str.strip()
        multi["inst_b"] = multi["inst_b"].str.upper().str.strip()
    # Eliminar self-loops generados por la normalizacion (ej: UNAL Bogota | UNAL Medellin -> UNAL | UNAL)
    multi = multi[multi["inst_a"] != multi["inst_b"]].copy()
    # Normalizar orden para que (A,B) == (B,A)
    multi[["inst_a", "inst_b"]] = pd.DataFrame(
        [sorted([a, b]) for a, b in zip(multi["inst_a"], multi["inst_b"])],
        index=multi.index,
    )
    return multi[["ID_PERSONA_PR", "ANO_CONVO_INT", "inst_a", "inst_b"]].reset_index(drop=True)


def construir_grafo(pares: pd.DataFrame, anio: int = None) -> nx.Graph:
    """
    Construye grafo de co-filiacion a partir de los pares.

    Si anio != None filtra por convocatoria. Peso de arista = n investigadores compartidos.
    """
    if anio is not None:
        pares = pares[pares["ANO_CONVO_INT"] == anio]

    G = nx.Graph()
    for (a, b), grp in pares.groupby(["inst_a", "inst_b"]):
        peso = len(grp)
        if G.has_edge(a, b):
            G[a][b]["weight"] += peso
        else:
            G.add_edge(a, b, weight=peso)
    return G


def metricas_grafo(G: nx.Graph) -> dict:
    """Metricas globales del grafo."""
    if len(G) == 0:
        return {}
    componentes = list(nx.connected_components(G))
    grado = dict(G.degree(weight="weight"))
    return {
        "n_nodos": G.number_of_nodes(),
        "n_aristas": G.number_of_edges(),
        "densidad": round(nx.density(G), 6),
        "n_componentes": len(componentes),
        "tam_componente_mayor": max(len(c) for c in componentes),
        "grado_promedio": round(sum(grado.values()) / len(grado), 2),
        "grado_max": max(grado.values()),
        "nodo_mayor_grado": max(grado, key=grado.get),
    }


def tabla_nodos(G: nx.Graph) -> pd.DataFrame:
    """
    DataFrame de nodos con grado, grado ponderado y betweenness.
    """
    if len(G) == 0:
        return pd.DataFrame()
    grado = dict(G.degree())
    grado_w = dict(G.degree(weight="weight"))
    between = nx.betweenness_centrality(G, weight="weight", normalized=True)
    df = pd.DataFrame({
        "institucion": list(grado.keys()),
        "grado": [grado[n] for n in grado],
        "grado_ponderado": [grado_w[n] for n in grado],
        "betweenness": [round(between[n], 6) for n in grado],
    })
    return df.sort_values("grado_ponderado", ascending=False).reset_index(drop=True)


def tabla_aristas(G: nx.Graph) -> pd.DataFrame:
    """DataFrame de aristas con peso."""
    rows = [{"inst_a": u, "inst_b": v, "peso": d["weight"]} for u, v, d in G.edges(data=True)]
    return pd.DataFrame(rows).sort_values("peso", ascending=False).reset_index(drop=True)


def metricas_por_convocatoria(pares: pd.DataFrame) -> pd.DataFrame:
    """Metricas globales del grafo para cada convocatoria."""
    rows = []
    for anio in sorted(pares["ANO_CONVO_INT"].unique()):
        G = construir_grafo(pares, anio=anio)
        m = metricas_grafo(G)
        m["anio"] = anio
        rows.append(m)
    return pd.DataFrame(rows)[["anio", "n_nodos", "n_aristas", "densidad",
                                "n_componentes", "tam_componente_mayor",
                                "grado_promedio", "grado_max", "nodo_mayor_grado"]]


def subgrafo_grado_minimo(G: nx.Graph, grado_min: int = 2) -> nx.Graph:
    """Subgrafo con nodos de grado >= grado_min (excluye hojas aisladas)."""
    nodos = [n for n, d in G.degree() if d >= grado_min]
    return G.subgraph(nodos).copy()


def generar_html_pyvis(
    G: nx.Graph,
    ruta_salida: pathlib.Path,
    titulo: str = "Co-filiacion institucional",
) -> None:
    """
    Genera visualizacion interactiva HTML con Pyvis.

    Tamano de nodo proporcional al grado ponderado.
    Grosor de arista proporcional al peso.
    Color de nodo segun betweenness (blanco=bajo, rojo=alto).
    """
    from pyvis.network import Network
    import networkx as nx_local

    between = nx.betweenness_centrality(G, weight="weight", normalized=True)
    grado_w = dict(G.degree(weight="weight"))
    max_grado = max(grado_w.values()) if grado_w else 1
    max_between = max(between.values()) if between else 1

    net = Network(
        height="750px",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="white",
        notebook=False,
    )
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=120)

    for node in G.nodes():
        g = grado_w.get(node, 1)
        b = between.get(node, 0)
        size = 8 + (g / max_grado) * 40
        # Color: escala de azul claro (baja centralidad) a rojo (alta)
        r = int(50 + (b / max_between) * 205)
        gb = int(120 - (b / max_between) * 100)
        color = f"#{r:02x}{gb:02x}{gb:02x}"
        label = node if len(node) <= 40 else node[:37] + "..."
        net.add_node(
            node,
            label=label,
            title=f"{node}<br>Grado ponderado: {g}<br>Betweenness: {b:.4f}",
            size=size,
            color=color,
        )

    max_peso = max((d["weight"] for _, _, d in G.edges(data=True)), default=1)
    for u, v, data in G.edges(data=True):
        peso = data["weight"]
        width = 1 + (peso / max_peso) * 6
        net.add_edge(u, v, value=peso, width=width,
                     title=f"{u} — {v}<br>Investigadores compartidos: {peso}")

    net.set_options("""
    {
      "nodes": {"font": {"size": 11}},
      "edges": {"color": {"opacity": 0.5}},
      "physics": {"stabilization": {"iterations": 200}}
    }
    """)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(ruta_salida))

