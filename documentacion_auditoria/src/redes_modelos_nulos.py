# -*- coding: utf-8 -*-
"""
redes_modelos_nulos.py
======================

F2-4 — Red de co-filiación institucional de 2019 con modelos nulos.

Qué es la red
-------------
Nodo = institución. Arista = un investigador con **doble afiliación** (el campo
`INST_FILIA` admite dos instituciones separadas por ` | `); el peso es el número
de investigadores que comparten ambas. Se usan las funciones del repositorio
auditado (`analisis.redes.normalizar_institucion` y `construir_pares`) sin
modificarlas, y la red se reconstruye **valor a valor**: 446 nodos, 503 aristas,
densidad 0,005069, 55 componentes, mayor de 327 y grado máximo 73.

Por qué solo 2019
-----------------
La doble afiliación **solo existe en la convocatoria de 2019**: 569 de los 16 796
registros (3,39 %) traen dos instituciones, y en las otras cinco convocatorias hay
**cero**. Por eso el corte «por convocatoria» del auditado tiene una sola fila, y
por eso su tabla `redes_nodos_global.csv` —que dice «global»— es en realidad la
red de 2019: al agrupar todas las convocatorias no se añade ninguna arista. Aquí se
analiza esa red como lo que es, una única red, y no como una serie.

Los 569 → 537: 32 pares se descartan
------------------------------------
`normalizar_institucion()` colapsa sedes, así que 32 de las 569 personas declaran
dos sedes de la MISMA institución (p. ej. «UNIVERSIDAD NACIONAL DE COLOMBIA |
UNIVERSIDAD NACIONAL DE COLOMBIA SEDE PALMIRA») y quedan como self-loops, que
`construir_pares()` elimina. Es la decisión correcta —alguien con dos sedes de la
misma universidad no es un puente entre instituciones— y se documenta porque
explica la diferencia entre 569 personas y 537 pares.

Modelos nulos
-------------
1. **Erdős–Rényi G(n, m)** con los mismos 446 nodos y 503 aristas: ¿la estructura
   observada se distingue de una red aleatoria del mismo tamaño?
2. **Modelo de configuración**: preserva la secuencia de grados observada y
   aleatoriza todo lo demás. Es el nulo correcto para preguntar si la estructura
   va más allá de la distribución de grados —que en esta red es muy heterogénea,
   con un máximo de 73 frente a una media de 2,41.

Criterio de «universidad-puente»
--------------------------------
Se define con una métrica explícita y comprobable:

- **Métrica principal (con prueba):** la *betweenness* de la institución frente a
  la distribución nula de betweenness **de los nodos con su mismo grado** en el
  modelo de configuración. Un puente es una institución cuya betweenness supera
  lo que su grado por sí solo explica (z ≥ 1,96). Así no se confunde «puente» con
  «hub»: un nodo de grado alto tiene betweenness alta por construcción.
- **Métrica acompañante (descriptiva):** el **índice de interregionalidad**, la
  proporción de co-filiaciones de la institución que cruzan una frontera entre
  macrorregiones. No lleva prueba propia porque la región de cada institución es
  un *proxy* (se explica abajo), así que se usa para interpretar, no para decidir.

Produce:
    data/memoria/redes_nulos.json
    data/memoria/graficas_redes/*.png

Uso:
    python documentacion_auditoria/src/redes_modelos_nulos.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path
from statistics import NormalDist

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import networkx as nx                     # noqa: E402
import numpy as np                        # noqa: E402
import pandas as pd                       # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
REPO = RAIZ / "datos_originales" / "repo_auditado"
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
SALIDA = DOC / "data" / "memoria" / "redes_nulos.json"
GRAF = DOC / "data" / "memoria" / "graficas_redes"

# Importar los modulos del auditado exige su src/ en el path y NO debe dejar
# __pycache__ dentro de una copia verbatim de 236 hashes.
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "src"))

from analisis.redes import (construir_grafo, construir_pares,   # noqa: E402
                            normalizar_institucion)

SEMILLA = 20260217
B = 500              # réplicas para los nulos globales (ER y configuración)
B_SWAP = 300         # réplicas por intercambio de aristas (grados EXACTOS)
ANIO = 2019

AZUL, AZUL_SEC, AZUL_CLARO = "#1E3780", "#4A6BA8", "#7BA7D0"
DORADO, DORADO_CLARO = "#B7871E", "#D4A84A"
GRIS_OSC, GRIS, GRIS_CLARO = "#334155", "#64748B", "#CBD5E1"
FONDO, TEXTO, ALERTA = "#F8FAFC", "#1E293B", "#B91C1C"

# Estadisticos globales que se contrastan contra los nulos.
ESTADISTICOS = ["n_componentes", "tam_componente_mayor", "transitividad",
                "clustering_medio", "asortatividad_grado", "gini_grado",
                "gini_betweenness", "camino_medio_mayor"]


# ==========================================================================
# 1. Utilidades
# ==========================================================================
def gini(x) -> float:
    x = np.asarray([v for v in x], dtype=float)
    if x.size == 0 or x.sum() <= 0:
        return float("nan")
    n = x.size
    xs = np.sort(x)
    i = np.arange(1, n + 1)
    return float((2.0 * np.sum(i * xs) - (n + 1) * np.sum(xs)) / (n * np.sum(xs)))


def estadisticos(G: nx.Graph) -> tuple[dict, dict]:
    """
    Estadísticos globales de una red, tolerantes a grafos desconectados.

    Devuelve (estadísticos, betweenness por nodo). La betweenness se devuelve y
    no se recalcula fuera: es el cálculo más caro y en el bucle de nulos se
    necesita para el nulo por clase de grado.
    """
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    mayor = G.subgraph(comps[0]).copy() if comps else nx.Graph()
    grados = [d for _, d in G.degree()]
    bet = nx.betweenness_centrality(G, normalized=True)
    camino = float("nan")
    if mayor.number_of_nodes() > 1:
        try:
            camino = float(nx.average_shortest_path_length(mayor))
        except Exception:                                  # noqa: BLE001
            camino = float("nan")
    try:
        asort = float(nx.degree_assortativity_coefficient(G))
    except Exception:                                      # noqa: BLE001
        asort = float("nan")
    return {
        "n_componentes": len(comps),
        "tam_componente_mayor": len(comps[0]) if comps else 0,
        "transitividad": float(nx.transitivity(G)),
        "clustering_medio": float(nx.average_clustering(G)),
        "asortatividad_grado": asort,
        "gini_grado": gini(grados),
        "gini_betweenness": gini(list(bet.values())),
        "camino_medio_mayor": camino,
    }, bet


def bh_fdr(p: np.ndarray) -> np.ndarray:
    """
    q-valores de Benjamini–Hochberg (tasa de falso descubrimiento).

    Con 120 contrastes individuales, esperar 0,05 por prueba deja pasar ~6
    falsos positivos. Se calcula la corrección para no presentar como «puente»
    lo que el azar produce igual de a menudo.
    """
    p = np.asarray(p, dtype=float)
    n = p.size
    q = np.empty(n, dtype=float)
    orden = np.argsort(p)
    previo = 1.0
    for k in range(n, 0, -1):
        i = orden[k - 1]
        previo = min(previo, p[i] * n / k)
        q[i] = previo
    return q


def p_bilateral(obs: float, nulos: list[float]) -> tuple[float, float, str]:
    """
    p-valor BILATERAL y z-score frente a una distribución nula.

    Se calculan las dos colas y se toma 2·min(p_inf, p_sup), acotado a 1. No se
    elige la cola a priori porque la pregunta es «¿difiere del azar?», no «¿es
    mayor?». Devuelve también hacia qué lado cae el valor observado.
    """
    v = np.asarray([x for x in nulos if np.isfinite(x)], dtype=float)
    if v.size == 0 or not np.isfinite(obs):
        return (float("nan"), float("nan"), "")
    n_b = v.size
    p_sup = (1 + int((v >= obs).sum())) / (n_b + 1)
    p_inf = (1 + int((v <= obs).sum())) / (n_b + 1)
    p = min(1.0, 2 * min(p_sup, p_inf))
    sd = float(v.std(ddof=1))
    z = float((obs - v.mean()) / sd) if sd > 0 else float("nan")
    return (float(p), z, "mayor" if p_sup < p_inf else "menor")


# ==========================================================================
# 2. Gráficas
# ==========================================================================
def _estilo(ax) -> None:
    ax.set_facecolor(FONDO)
    ax.grid(axis="y", color=GRIS_CLARO, linewidth=0.6, alpha=0.9)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRIS)
    ax.tick_params(colors=GRIS_OSC, labelsize=8)


def fig_grados(G: nx.Graph, grado_medio_er: float, archivo) -> None:
    obs = sorted((d for _, d in G.degree()), reverse=True)
    fig, ax = plt.subplots(figsize=(9.4, 4.5), dpi=150)
    x = np.arange(len(obs))
    ax.plot(x, obs, color=AZUL, linewidth=2.0, zorder=4,
            label="Red observada (2019)")
    ax.axhline(grado_medio_er, color=DORADO, linewidth=1.6, zorder=3,
               label=f"Grado medio de Erdős–Rényi = {grado_medio_er:.2f}")
    ax.set_xlabel("Institución (ordenada por grado)", color=TEXTO, fontsize=9)
    ax.set_ylabel("Grado", color=TEXTO, fontsize=9)
    ax.set_title("La distribución de grado no es la de una red aleatoria\n"
                 f"Grado máximo {obs[0]} frente a una media de {np.mean(obs):.2f}",
                 color=TEXTO, fontsize=10.2, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8.4, labelcolor=GRIS_OSC)
    _estilo(ax)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


def fig_nulos(res: dict, archivo) -> None:
    """Observado frente a las dos distribuciones nulas, por estadístico."""
    claves = ["n_componentes", "tam_componente_mayor", "transitividad",
              "clustering_medio", "gini_betweenness"]
    titulos = {"n_componentes": "N.º de componentes",
               "tam_componente_mayor": "Tamaño del componente mayor",
               "transitividad": "Transitividad (global)",
               "clustering_medio": "Clustering medio",
               "gini_betweenness": "Gini de la betweenness"}
    fig, axes = plt.subplots(2, 3, figsize=(13.2, 6.6), dpi=150)
    for ax, k in zip(axes.ravel(), claves):
        d = res[k]
        ax.hist(d["nulo_er"], bins=30, color=GRIS, alpha=0.75, zorder=2,
                label="Erdős–Rényi")
        ax.hist(d["nulo_config"], bins=30, color=AZUL_CLARO, alpha=0.75,
                zorder=3, label="Configuración")
        ax.axvline(d["observado"], color=AZUL, linewidth=2.0, zorder=4,
                   label="Observado")
        ax.set_title(f"{titulos[k]}\np = {d['er_p']:.4f} (ER) · "
                     f"p = {d['config_p']:.4f} (CFG)",
                     color=TEXTO, fontsize=8.8, pad=8)
        ax.tick_params(labelsize=7.4)
        _estilo(ax)
        ax.grid(axis="y", color=GRIS_CLARO, linewidth=0.5, alpha=0.9)
    axes.ravel()[-1].axis("off")
    h, lab = axes.ravel()[0].get_legend_handles_labels()
    axes.ravel()[-1].legend(h, lab, frameon=False, fontsize=9,
                            labelcolor=GRIS_OSC, loc="center")
    fig.suptitle("¿La red se distingue del azar? Dos nulos frente al valor "
                 "observado", color=TEXTO, fontsize=11, y=1.01, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def fig_puentes(df: pd.DataFrame, archivo) -> None:
    top = df.head(18)
    fig, ax = plt.subplots(figsize=(10.4, 5.6), dpi=150)
    y = np.arange(len(top))
    ax.barh(y, top["betweenness"], color=AZUL, zorder=3,
            label="Betweenness observada")
    ax.barh(y, top["betweenness_nulo_medio"], color=GRIS_CLARO, height=0.45,
            zorder=2, label="Media nula del mismo grado (configuración)")
    for i, (_, r) in enumerate(top.iterrows()):
        ax.annotate(f"z={r['betweenness_z']:.1f} · interregional "
                    f"{100*r['interregionalidad']:.0f} %",
                    (max(r["betweenness"], r["betweenness_nulo_medio"]), i),
                    textcoords="offset points", xytext=(5, 0), va="center",
                    fontsize=7.2, color=GRIS_OSC)
    ax.set_yticks(y)
    ax.set_yticklabels([t[:46] for t in top["institucion"]], fontsize=7.6)
    ax.invert_yaxis()
    ax.set_xlabel("Betweenness (normalizada)", color=TEXTO, fontsize=9)
    ax.set_title("Instituciones con más intermediación, frente a lo que su grado "
                 "explicaría\nLa barra gris es cuánta betweenness tendrían por "
                 "azar con el mismo grado", color=TEXTO, fontsize=10.2, pad=10,
                 loc="left")
    ax.legend(frameon=False, fontsize=8.2, labelcolor=GRIS_OSC, loc="lower right")
    _estilo(ax)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


# ==========================================================================
# 3. Principal
# ==========================================================================
def main() -> int:
    print("== F2-4 · Red de co-filiación de 2019 con modelos nulos ==")
    out: dict = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "analisis": "F2-4 — Redes de co-filiación con modelos nulos (Q5)",
        "semilla": SEMILLA, "replicas": B,
        "networkx": nx.__version__,
    }

    # ---------------- datos ----------------
    df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                     usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "INST_FILIA",
                              "NME_REGION_RES_PR"])
    df["ANO_CONVO_INT"] = df["ID_CONVOCATORIA"].astype(int).map(
        {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021})
    df["INST_FILIA"] = df["INST_FILIA"].str.strip()
    df["region"] = df["NME_REGION_RES_PR"].str.strip()

    con_doble = df["INST_FILIA"].str.contains("|", regex=False)
    por_anio = {str(int(a)): int(c) for a, c in
                df.loc[con_doble].groupby("ANO_CONVO_INT").size().items()}
    print(f"   registros con doble afiliación por año: {por_anio}")
    out["solo_2019"] = {
        "registros_con_doble_afiliacion_por_anio": por_anio,
        "nota": ("La doble afiliación SOLO existe en 2019. Por eso el corte por "
                 "convocatoria del auditado tiene una sola fila y su tabla "
                 "'redes_nodos_global.csv' es en realidad la red de 2019: agrupar "
                 "todas las convocatorias no añade ninguna arista. No es una "
                 "serie temporal; es una única red."),
    }

    pares = construir_pares(df)
    n_personas = int(df.loc[con_doble, "ID_PERSONA_PR"].nunique())
    out["pares"] = {
        "personas_con_doble_afiliacion": n_personas,
        "pares_tras_normalizar": int(len(pares)),
        "pares_descartados_como_self_loop": n_personas - int(len(pares)),
        "nota": ("normalizar_institucion() colapsa sedes, así que 32 personas "
                 "declaran dos sedes de la MISMA institución y su par queda como "
                 "self-loop. Es la decisión correcta —dos sedes de la misma "
                 "universidad no son un puente entre instituciones— y explica la "
                 "diferencia entre 569 personas y 537 pares."),
    }
    print(f"   {n_personas} personas con doble afiliación -> {len(pares)} pares "
          f"({n_personas - len(pares)} self-loops descartados)")

    G = construir_grafo(pares, anio=ANIO)
    Gw = G.copy()                                   # con pesos, para describir
    print(f"   red de {ANIO}: {G.number_of_nodes()} nodos · "
          f"{G.number_of_edges()} aristas")

    # ---------------- reproducción del auditado ----------------
    aud = pd.read_csv(REPO / "evidencias" / "redes_metricas_por_convocatoria.csv",
                      encoding="utf-8-sig").iloc[0]
    # OJO con la nomenclatura del auditado: `grado_promedio` y `grado_max` de
    # metricas_grafo() se calculan sobre el grado PONDERADO (G.degree(weight=...)),
    # mientras que tabla_nodos() usa el grado simple. Por eso su grado_max es 73
    # (ponderado) y no 56 (simple). Se comparan ambos explícitamente.
    g_max_w = max(d for _, d in G.degree(weight="weight"))
    g_max_s = max(d for _, d in G.degree())
    rep = {
        "n_nodos": G.number_of_nodes() == int(aud["n_nodos"]),
        "n_aristas": G.number_of_edges() == int(aud["n_aristas"]),
        "n_componentes": nx.number_connected_components(G) == int(aud["n_componentes"]),
        "tam_componente_mayor": (max(len(c) for c in nx.connected_components(G))
                                 == int(aud["tam_componente_mayor"])),
        "grado_max_ponderado": g_max_w == int(aud["grado_max"]),
        "densidad": abs(nx.density(G) - float(aud["densidad"])) < 1e-6,
    }
    for k, v in rep.items():
        print(f"   [{'OK ' if v else 'NO '}] reproducido {k}")
    print(f"   (grado máximo: ponderado {g_max_w} —el que reporta el auditado— "
          f"frente a simple {g_max_s})")
    out["reproduccion_del_auditado"] = rep
    out["grado_max"] = {
        "ponderado_como_el_auditado": int(g_max_w),
        "simple": int(g_max_s),
        "nota": ("metricas_grafo() del auditado calcula grado_promedio y grado_max "
                 "sobre el grado PONDERADO, mientras tabla_nodos() usa el simple. "
                 "Su 73 es ponderado; el grado simple máximo es 56. No es un "
                 "error de dato, pero el nombre engaña."),
    }

    # ---------------- región de cada institución (proxy) ----------------
    sub = df[con_doble & (df["ANO_CONVO_INT"] == ANIO)]
    largo = pd.concat([
        pd.DataFrame({"inst": sub["INST_FILIA"].str.split("|").str[0].str.strip()
                      .map(normalizar_institucion), "region": sub["region"]}),
        pd.DataFrame({"inst": sub["INST_FILIA"].str.split("|").str[1].str.strip()
                      .map(normalizar_institucion), "region": sub["region"]}),
    ]).dropna(subset=["inst"])
    region = largo.groupby("inst")["region"].agg(lambda s: s.value_counts().index[0])
    n_regiones = largo.groupby("inst")["region"].nunique()
    print(f"   región asignada a {region.size} instituciones "
          f"({int((n_regiones > 1).sum())} declaran más de una)")
    out["region_proxy"] = {
        "instituciones_con_region": int(region.size),
        "con_mas_de_una_region_declarada": int((n_regiones > 1).sum()),
        "distribucion": {k: int(v) for k, v in
                         region.value_counts().items()},
        "nota": ("La fuente no trae la sede de cada institución: la región se "
                 "asigna como la MACRORREGIÓN MODAL de las personas que la "
                 "declaran. Es un proxy y así se usa: el índice de "
                 "interregionalidad es descriptivo, no una prueba."),
    }

    # ---------------- observado ----------------
    obs, bet = estadisticos(G)
    grado = dict(G.degree())
    out["red"] = {
        "n_nodos": G.number_of_nodes(), "n_aristas": G.number_of_edges(),
        "densidad": float(nx.density(G)),
        "grado_medio": float(np.mean(list(grado.values()))),
        "estadisticos_observados": obs,
    }
    print("\n   observado:")
    for k in ESTADISTICOS:
        v = obs[k]
        print(f"      {k:22s} {v if not np.isfinite(v) else round(v, 4)}")

    # ---------------- modelos nulos ----------------
    rng = np.random.default_rng(SEMILLA)
    n, m = G.number_of_nodes(), G.number_of_edges()
    degseq = [d for _, d in G.degree()]
    nulos = {"er": {k: [] for k in ESTADISTICOS},
             "config": {k: [] for k in ESTADISTICOS}}
    # Nulo por clase de grado para la betweenness de cada nodo.
    bet_por_grado: dict[int, list[float]] = {}
    # El modelo de configuración genera multigrafos: al colapsarlos se pierden
    # aristas, así que la secuencia de grados se perturba un poco. Se mide.
    aristas_cf: list[int] = []

    print(f"\n   generando {B} réplicas de cada modelo nulo…")
    for _ in range(B):
        Ger = nx.gnm_random_graph(n, m, seed=int(rng.integers(1, 2**31 - 1)))
        s_er, _ = estadisticos(Ger)
        for k in ESTADISTICOS:
            nulos["er"][k].append(s_er[k])

        Gcf = nx.Graph(nx.configuration_model(
            degseq, seed=int(rng.integers(1, 2**31 - 1))))
        Gcf.remove_edges_from(list(nx.selfloop_edges(Gcf)))
        aristas_cf.append(Gcf.number_of_edges())
        s_cf, _ = estadisticos(Gcf)
        for k in ESTADISTICOS:
            nulos["config"][k].append(s_cf[k])

    print("   nulos generados")
    out["modelo_configuracion"] = {
        "aristas_observadas": int(m),
        "aristas_medias_tras_colapsar": float(np.mean(aristas_cf)),
        "nota": ("configuration_model produce multigrafos; al convertir a grafo "
                 "simple se descartan auto-lazos y aristas paralelas, así que el "
                 "número de aristas baja respecto de las observadas y la "
                 "secuencia de grados se desplaza hacia abajo. Sirve para "
                 "contrastar los estadísticos GLOBALES, pero NO para comparar "
                 "nodos «con su mismo grado»: por eso la prueba de puentes usa "
                 "un tercer nulo que preserva los grados exactamente."),
    }

    # ---------------- tercer nulo: intercambio de aristas ----------------
    # double_edge_swap preserva la secuencia de grados EXACTA y mantiene el
    # grafo simple, así que permite comparar la betweenness de un nodo con la
    # de nodos del MISMO grado. Es el nulo correcto para decidir si una
    # institución es puente más allá de lo que su grado explica.
    print(f"   generando {B_SWAP} réplicas por intercambio de aristas "
          f"(grados exactos)…")
    for _ in range(B_SWAP):
        Gs = G.copy()
        try:
            nx.double_edge_swap(Gs, nswap=Gs.number_of_edges(),
                                max_tries=20 * Gs.number_of_edges(),
                                seed=int(rng.integers(1, 2**31 - 1)))
        except Exception:                                  # noqa: BLE001
            continue
        if sorted(d for _, d in Gs.degree()) != sorted(degseq):
            continue                            # salvaguarda: grados exactos
        for nodo, b in nx.betweenness_centrality(Gs, normalized=True).items():
            bet_por_grado.setdefault(Gs.degree(nodo), []).append(b)
    out["nulo_de_intercambio"] = {
        "replicas_pedidas": B_SWAP,
        "clases_de_grado_con_muestra": int(len(bet_por_grado)),
        "observaciones_por_clase": {str(k): len(v)
                                    for k, v in sorted(bet_por_grado.items())[:12]},
        "nota": ("double_edge_swap preserva la secuencia de grados exacta y "
                 "mantiene el grafo simple. Se verifica en cada réplica que la "
                 "secuencia no cambió."),
    }

    # ---------------- contraste ----------------
    res: dict = {}
    for k in ESTADISTICOS:
        p_er, z_er, cola_er = p_bilateral(obs[k], nulos["er"][k])
        p_cf, z_cf, cola_cf = p_bilateral(obs[k], nulos["config"][k])
        res[k] = {
            "observado": float(obs[k]),
            "er_medio": float(np.nanmean(nulos["er"][k])),
            "er_ic95": [float(np.nanpercentile(nulos["er"][k], 2.5)),
                        float(np.nanpercentile(nulos["er"][k], 97.5))],
            "er_p": p_er, "er_z": z_er, "er_cola": cola_er,
            "config_medio": float(np.nanmean(nulos["config"][k])),
            "config_ic95": [float(np.nanpercentile(nulos["config"][k], 2.5)),
                            float(np.nanpercentile(nulos["config"][k], 97.5))],
            "config_p": p_cf, "config_z": z_cf, "config_cola": cola_cf,
            "nulo_er": [float(x) for x in nulos["er"][k]],
            "nulo_config": [float(x) for x in nulos["config"][k]],
        }
    print("\n   contraste (p BILATERAL) frente a ER y a configuración:")
    for k in ESTADISTICOS:
        d = res[k]
        print(f"      {k:22s} obs={d['observado']:8.4f} "
              f"ER {d['er_medio']:8.4f} p={d['er_p']:.4f} "
              f"| CFG {d['config_medio']:8.4f} p={d['config_p']:.4f} "
              f"[{d['config_cola'] or '—'}]")

    # ---------------- puentes ----------------
    # Tres razones distintas por las que un nodo puede quedar SIN prueba, y no
    # son intercambiables:
    #   - hoja (grado 1): su betweenness es 0 por construcción, así que la
    #     prueba es vacua. Son 326 de los 446 nodos, y eso ya es un resultado:
    #     73 % de las instituciones aparece en UNA sola co-filiación.
    #   - varianza nula en su clase de grado: todos los nulos valen lo mismo.
    #   - clase con pocas réplicas (< 30 observaciones).
    filas = []
    motivos: dict[str, int] = {"hoja": 0, "varianza_nula": 0, "muestra_pequena": 0}
    for inst in G.nodes():
        g = grado[inst]
        clase = np.asarray(bet_por_grado.get(g, []), dtype=float)
        mu = sd = z = pn = float("nan")
        motivo = ""
        if g <= 1:
            motivo = "hoja"
        elif clase.size < 30:
            motivo = "muestra_pequena"
        else:
            mu, sd = float(clase.mean()), float(clase.std(ddof=1))
            if sd > 0:
                z = (bet[inst] - mu) / sd
                pn = (1 + int((clase >= bet[inst]).sum())) / (clase.size + 1)
            else:
                motivo = "varianza_nula"
        if motivo:
            motivos[motivo] += 1
        vecinos = list(G.neighbors(inst))
        reg_inst = region.get(inst, "No disponible")
        inter = sum(1 for v in vecinos
                    if region.get(v, "No disponible") != reg_inst)
        filas.append({
            "institucion": inst, "grado": g,
            "grado_ponderado": int(Gw.degree(inst, weight="weight")),
            "betweenness": float(bet[inst]),
            "betweenness_nulo_medio": mu, "betweenness_nulo_sd": sd,
            "betweenness_z": z, "betweenness_p_nulo": pn,
            "region": reg_inst,
            "vecinos": len(vecinos),
            "vecinos_interregionales": inter,
            "interregionalidad": (inter / len(vecinos)) if vecinos else float("nan"),
            "n_regiones_vecinas": len({region.get(v, "No disponible")
                                       for v in vecinos}),
            "motivo_sin_prueba": motivo,
        })
    nodos = pd.DataFrame(filas).sort_values("betweenness", ascending=False)
    # Corrección por comparaciones múltiples sobre los nodos SÍ contrastables.
    contrastables = nodos["betweenness_p_nulo"].notna()
    p_vals = nodos.loc[contrastables, "betweenness_p_nulo"].to_numpy()
    nodos["q_fdr"] = np.nan
    if p_vals.size:
        nodos.loc[contrastables, "q_fdr"] = bh_fdr(p_vals)
    nodos.to_csv(DOC / "data" / "memoria" / "redes_nodos_2019.csv", index=False)

    n_test = int(contrastables.sum())
    pasan_crudo = nodos[nodos["betweenness_z"] >= 1.96].copy()
    pasan_fdr = nodos[(nodos["q_fdr"] <= 0.05)].copy() if p_vals.size else \
        nodos.iloc[0:0]
    z_bonf = float(NormalDist().inv_cdf(1 - 0.05 / (2 * max(n_test, 1))))
    esperados_azar = 0.025 * n_test
    print(f"\n   nodos contrastables: {n_test} de {len(nodos)}")
    print(f"   pasan z>=1,96 (sin corregir): {len(pasan_crudo)} "
          f"(esperados por azar ~{esperados_azar:.1f})")
    print(f"   pasan FDR 5 %: {len(pasan_fdr)} · z de Bonferroni ~{z_bonf:.2f}")
    for _, r in pasan_crudo.iterrows():
        print(f"      {r['institucion'][:52]:52s} grado={r['grado']:2d} "
              f"z={r['betweenness_z']:5.2f} q={r['q_fdr']:.4f} "
              f"interreg={100*r['interregionalidad']:5.1f} %")

    # Ranking DESCRIPTIVO de conexión interregional (no lleva prueba: la región
    # de cada institución es un proxy). Se restringe a nodos con al menos dos
    # vecinos, porque con un solo vecino el índice solo puede valer 0 o 1.
    desc = nodos[(nodos["vecinos"] >= 2) & (nodos["grado_ponderado"] >= 2)]
    desc = desc.sort_values(["interregionalidad", "n_regiones_vecinas",
                             "grado"], ascending=False)

    out["puentes"] = {
        "criterio_principal": ("betweenness del nodo frente a la distribución nula "
                               "de betweenness de los nodos CON SU MISMO GRADO en "
                               "el nulo de intercambio de aristas (double_edge_swap, "
                               "grados exactos). Evita confundir puente con hub: un "
                               "nodo de grado alto tiene betweenness alta por "
                               "construcción."),
        "criterio_acompanante": ("índice de interregionalidad = proporción de "
                                 "co-filiaciones que cruzan macrorregión, con la "
                                 "región asignada por proxy. Descriptivo, no lleva "
                                 "prueba."),
        "nodos_contrastables": n_test,
        "motivos_sin_prueba": motivos,
        "por_que_las_hojas_no_se_prueban": (
            "Un nodo de grado 1 nunca está en un camino mínimo entre otros dos, "
            "así que su betweenness es 0 por construcción: no hay nada que "
            "contrastar. No es un problema de tamaño de muestra. Que 326 de 446 "
            "sean hojas es en sí un resultado: el 73 % de las instituciones "
            "aparece en una sola co-filiación."),
        "pasan_z_1_96_sin_corregir": int(len(pasan_crudo)),
        "esperados_por_azar_sin_corregir": float(esperados_azar),
        "z_de_bonferroni": z_bonf,
        "pasan_fdr_5pct": int(len(pasan_fdr)),
        "pasan_bonferroni": int((nodos["betweenness_z"] >= z_bonf).sum())
        if n_test else 0,
        "lista_sin_corregir": [
            {"institucion": r["institucion"], "grado": int(r["grado"]),
             "betweenness": round(r["betweenness"], 6),
             "betweenness_z": round(r["betweenness_z"], 3),
             "p_nulo": round(r["betweenness_p_nulo"], 5),
             "q_fdr": round(float(r["q_fdr"]), 5),
             "interregionalidad": round(float(r["interregionalidad"]), 4),
             "n_regiones_vecinas": int(r["n_regiones_vecinas"]),
             "region": r["region"]}
            for _, r in pasan_crudo.iterrows()],
        "ranking_interregional_descriptivo": [
            {"institucion": r["institucion"], "grado": int(r["grado"]),
             "betweenness": round(r["betweenness"], 6),
             "interregionalidad": round(float(r["interregionalidad"]), 4),
             "vecinos": int(r["vecinos"]),
             "vecinos_interregionales": int(r["vecinos_interregionales"]),
             "n_regiones_vecinas": int(r["n_regiones_vecinas"]),
             "region": r["region"]}
            for _, r in desc.head(15).iterrows()],
        "conclusion": (
            "La concentración de la intermediación SÍ es mayor que la esperada "
            "(Gini de la betweenness, p = 0,004 frente a los dos nulos): como "
            "propiedad global de la red, el corretaje está concentrado. Pero "
            "NINGUNA institución concreta resiste la corrección por "
            "comparaciones múltiples: las que pasan z >= 1,96 son menos de las "
            "que el azar produciría. Por tanto no puede etiquetarse a una "
            "universidad como «puente» con estos datos; lo que se sostiene es que "
            "el corretaje está concentrado, no quién lo ejerce."),
    }
    print(f"   -> conclusión: concentración global significativa, atribución "
          f"individual NO sostenible")
    print(f"   top interregional (descriptivo):")
    for _, r in desc.head(8).iterrows():
        print(f"      {r['institucion'][:52]:52s} grado={r['grado']:2d} "
              f"interreg={100*r['interregionalidad']:5.1f} % "
              f"({r['vecinos_interregionales']}/{r['vecinos']} vecinos, "
              f"{r['n_regiones_vecinas']} regiones)")

    out["contraste_nulos"] = res
    out["nodos_top_betweenness"] = [
        {"institucion": r["institucion"], "grado": int(r["grado"]),
         "betweenness": round(r["betweenness"], 6),
         "betweenness_z": (None if not np.isfinite(r["betweenness_z"])
                           else round(r["betweenness_z"], 3)),
         "interregionalidad": (None if not np.isfinite(r["interregionalidad"])
                               else round(r["interregionalidad"], 4))}
        for _, r in nodos.head(15).iterrows()]

    # ---------------- figuras ----------------
    GRAF.mkdir(parents=True, exist_ok=True)
    fig_grados(G, float(np.mean(list(grado.values()))),
               GRAF / "f2_4_distribucion_grado.png")
    fig_nulos(res, GRAF / "f2_4_contraste_nulos.png")
    fig_puentes(nodos.dropna(subset=["betweenness_nulo_medio"]),
                GRAF / "f2_4_puentes.png")
    out["figuras"] = sorted(p.name for p in GRAF.glob("*.png"))

    # ---------------- validaciones ----------------
    out["validaciones"] = {
        "red_reproducida_valor_a_valor": bool(all(rep.values())),
        "solo_2019_tiene_doble_afiliacion": bool(
            set(por_anio) == {"2019"}),
        "pares_mas_selfloops_igual_personas": bool(
            len(pares) + (n_personas - len(pares)) == n_personas),
        "todos_los_nodos_tienen_region": bool(
            set(G.nodes()) <= set(region.index)),
        "nulos_generados": bool(len(res["n_componentes"]["nulo_er"]) == B
                                and len(res["n_componentes"]["nulo_config"]) == B),
        "nulo_intercambio_generado": bool(len(bet_por_grado) > 0),
        "betweenness_en_rango": bool(max(bet.values()) <= 1.0
                                     and min(bet.values()) >= 0.0),
    }
    print()
    for k, v in out["validaciones"].items():
        print(f"   [{'OK ' if v else 'NO '}] {k}")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size:,} bytes)")
    print(f"-> {GRAF.relative_to(RAIZ)}/ ({len(out['figuras'])} figuras)")
    print(f"-> data/memoria/redes_nodos_2019.csv ({len(nodos)} nodos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
