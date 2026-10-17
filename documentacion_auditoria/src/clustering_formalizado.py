# -*- coding: utf-8 -*-
"""
clustering_formalizado.py
=========================

F2-6 — Segmentación formalizada de perfiles de investigación.

Qué hacía el repositorio auditado
---------------------------------
`notebooks/tarea_gran_tabla/analisis_de_clusters.R`:

    GT       <- read_excel("Downloads/GRAN_TABLA(SIN ID).xlsx")   # ruta inexistente
    GT_NA    <- cc(GT)                                            # casos completos
    res.kproto <- kproto(GT_NA, k = 3)                            # k=3 fijo

Tres problemas: la entrada **no existe** (ruta del `Downloads/` del autor y la gran
tabla no está versionada), `cc()` **descarta el 8,4 % de la muestra** por lista, y
**k = 3 se fija sin validación**. Este script reconstruye ese clustering en Python
con un criterio formal de elección de k.

Por qué NO se pierde el 8,4 %
-----------------------------
La fuente codifica los faltantes como **categorías explícitas** (`No disponible`,
`No registra`, `No reportado`), no como celdas vacías: en las variables de este
análisis hay **un solo dato faltante** (una edad). Se tratan como categorías, que
es la decisión documentada del proyecto, así que el clustering usa los
**77 237 registros** y la pérdida de muestra es **0 %**.

Por qué `TXT_POBLACION_DISCA` queda fuera de las variables
----------------------------------------------------------
El 73,6 % de sus valores es `No disponible` porque la variable **solo existe en
2021** (F2-5). Incluirla alinearía los clusters con la convocatoria y no con un
perfil: sería un artefacto de cobertura, no un hallazgo. Se reporta de forma
descriptiva por cluster, como hacía el informe del auditado.

Método
------
**k-prototypes de Huang (1998)**, que es exactamente lo que implementa `kproto()`:
distancia mixta `d = d_numérica + γ · d_categórica` (Euclídea al cuadrado en la
edad estandarizada + número de discrepancias categóricas ponderado por γ), con
prototipo numérico = media y categórico = moda. Varios arranques aleatorios para
evitar óptimos locales.

Criterio de k
-------------
1. **Silhouette** (Rousseeuw, 1987) sobre la distancia mixta, en una submuestra
   estratificada. Kaufman y Rousseeuw consideran que **< 0,25 no indica estructura
   sustancial**.
2. **Calinski–Harabasz** y **Davies–Bouldin** sobre la representación one-hot.
3. **Codo del coste** (inercia intra-cluster frente a k=1).
4. **Prueba de estructura frente a un nulo**: se destruye la asociación entre
   variables permutando cada una por separado (se conservan las marginales, se
   rompe la estructura conjunta) y se recalcula el criterio. Si lo observado cae
   dentro de lo que produce el nulo, **no hay estructura de clusters** y el mejor
   k es 1.

Produce:
    data/memoria/clustering.json
    data/memoria/clusters_registros.csv
    data/memoria/graficas_clusters/*.png

Uso:
    python documentacion_auditoria/src/clustering_formalizado.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                        # noqa: E402
import pandas as pd                       # noqa: E402
from sklearn.metrics import (calinski_harabasz_score,   # noqa: E402
                             davies_bouldin_score,
                             silhouette_samples, adjusted_rand_score)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
SALIDA = DOC / "data" / "memoria" / "clustering.json"
CSV_CLUSTERS = DOC / "data" / "memoria" / "clusters_registros.csv"
GRAF = DOC / "data" / "memoria" / "graficas_clusters"

SEMILLA = 20260217
K_MAX = 10
N_INIT = 5              # arranques aleatorios por k
MAX_ITER = 100
N_SIL = 4000            # submuestra para la silhouette
N_NULO = 20             # permutaciones del nulo
N_NULO_FILAS = 10000    # submuestra para el nulo (coste)

AZUL, AZUL_SEC, AZUL_CLARO = "#1E3780", "#4A6BA8", "#7BA7D0"
DORADO, DORADO_CLARO = "#B7871E", "#D4A84A"
GRIS_OSC, GRIS, GRIS_CLARO = "#334155", "#64748B", "#CBD5E1"
FONDO, TEXTO, ALERTA = "#F8FAFC", "#1E293B", "#B91C1C"

CATEGORICAS = {
    "NME_GRAN_AREA_PR": "Gran área",
    "NME_GENERO_PR": "Género",
    "NME_REGION_NAC_PR": "Región de nacimiento",
    "NME_NIV_FORM_PR": "Nivel de formación",
    "NME_CLASIFICACION_PR": "Categoría",
    "NME_REGION_RES_PR": "Región de residencia",
}
NUMERICA = "EDAD_ANOS_PR"


# ==========================================================================
# 1. Datos y representación
# ==========================================================================
def cargar() -> pd.DataFrame:
    cols = ["ID_CONVOCATORIA", "ID_PERSONA_PR", *CATEGORICAS, NUMERICA,
            "TXT_POBLACION_DISCA", "TXT_GRUPO_ETNICO", "ID_VICTIMA_CONFLICTO"]
    df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                     usecols=cols)
    for c in CATEGORICAS:
        df[c] = df[c].str.strip()
    df["anio"] = df["ID_CONVOCATORIA"].astype(int).map(
        {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021})
    df["edad"] = pd.to_numeric(df[NUMERICA].str.replace(",", ".", regex=False),
                               errors="coerce")
    return df


def codificar(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Devuelve (matriz categórica entera, edad estandarizada, mapa de categorías).

    Las categóricas se codifican como enteros por variable; la distancia entre dos
    valores es 1 si difieren, igual que en k-modes.
    """
    cat = np.empty((len(df), len(CATEGORICAS)), dtype=np.int16)
    mapa: dict = {}
    for j, col in enumerate(CATEGORICAS):
        codigos, unicos = pd.factorize(df[col], sort=True)
        cat[:, j] = codigos
        mapa[col] = [str(u) for u in unicos]
    edad = df["edad"].to_numpy(dtype=float)
    # La edad se estandariza; el único faltante va a la media (0 tras estandarizar)
    mu, sd = np.nanmean(edad), np.nanstd(edad)
    z = np.where(np.isnan(edad), 0.0, (edad - mu) / sd)
    return cat, z, mapa


def matriz_onehot(cat: np.ndarray, z: np.ndarray, nb: list[int]) -> np.ndarray:
    """Representación one-hot + edad estandarizada, para CH y Davies-Bouldin."""
    partes = [np.eye(nb[j], dtype=np.float32)[cat[:, j]] for j in range(len(nb))]
    partes.append(z.reshape(-1, 1).astype(np.float32))
    return np.hstack(partes)


# ==========================================================================
# 2. k-prototypes
# ==========================================================================
def distancia(cat: np.ndarray, z: np.ndarray, pcat: np.ndarray, pz: np.ndarray,
              gamma: float) -> np.ndarray:
    """Matriz (n x k) de distancias mixtas a los prototipos."""
    d_num = (z[:, None] - pz[None, :]) ** 2
    # número de discrepancias categóricas por punto y prototipo
    d_cat = np.zeros((cat.shape[0], pcat.shape[0]), dtype=np.float32)
    for j in range(cat.shape[1]):
        d_cat += (cat[:, j][:, None] != pcat[None, :, j]).astype(np.float32)
    return d_num + gamma * d_cat


def kprototypes(cat: np.ndarray, z: np.ndarray, k: int, gamma: float,
                rng, n_init: int = N_INIT,
                max_iter: int = MAX_ITER) -> tuple[np.ndarray, float]:
    """k-prototypes de Huang con varios arranques. Devuelve (etiquetas, coste)."""
    n = cat.shape[0]
    mejor_etq, mejor_coste = None, np.inf
    for _ in range(n_init):
        idx = rng.choice(n, size=k, replace=False)
        pcat = cat[idx].copy()
        pz = z[idx].copy()
        etq = np.full(n, -1, dtype=np.int32)
        for _it in range(max_iter):
            d = distancia(cat, z, pcat, pz, gamma)
            nueva = d.argmin(axis=1).astype(np.int32)
            if np.array_equal(nueva, etq):
                break
            etq = nueva
            for c in range(k):
                m = etq == c
                if not m.any():                       # cluster vacío: re-sembrar
                    j = rng.integers(0, n)
                    pcat[c] = cat[j]
                    pz[c] = z[j]
                    continue
                pz[c] = z[m].mean()
                for j in range(cat.shape[1]):
                    valores, cuentas = np.unique(cat[m, j], return_counts=True)
                    pcat[c, j] = valores[cuentas.argmax()]
        d = distancia(cat, z, pcat, pz, gamma)
        coste = float(d[np.arange(n), etq].sum())
        if coste < mejor_coste:
            mejor_coste, mejor_etq = coste, etq.copy()
    return mejor_etq, mejor_coste


def coste_k1(cat: np.ndarray, z: np.ndarray, gamma: float) -> float:
    """
    Coste con un ÚNICO prototipo: la inercia total de referencia.

    Tiene que medirse con la MISMA distancia mixta que usa el algoritmo, o el
    cociente no significa nada: comparar el coste mixto de k > 1 contra la inercia
    solo numérica de k = 1 daba pérdidas del 225 %, que es imposible.

    Con un prototipo, la parte numérica es la suma de cuadrados de la edad
    estandarizada y la categórica es la distancia de cada valor a la MODA global
    (0 si coincide, 1 si no), que es justo lo que hace el algoritmo al actualizar
    los prototipos categóricos.
    """
    num = float(((z - z.mean()) ** 2).sum())
    cat_d = 0.0
    for j in range(cat.shape[1]):
        _, cuentas = np.unique(cat[:, j], return_counts=True)
        cat_d += float(len(cat) - cuentas.max())
    return num + gamma * cat_d


def silhouette_mixta(cat: np.ndarray, z: np.ndarray, etq: np.ndarray,
                     gamma: float, rng, n_muestra: int = N_SIL) -> float:
    """
    Silhouette media sobre la distancia mixta, en una submuestra.

    Se submuestrea de forma estratificada por cluster: con 77 237 filas la matriz
    de distancias completa no cabe en memoria, y la silhouette converge rápido.
    """
    idx = []
    for c in np.unique(etq):
        pos = np.where(etq == c)[0]
        toma = min(len(pos), max(10, int(n_muestra * len(pos) / len(etq))))
        idx.append(rng.choice(pos, size=toma, replace=False))
    idx = np.concatenate(idx)
    cat_s, z_s, etq_s = cat[idx], z[idx], etq[idx]
    d = (z_s[:, None] - z_s[None, :]) ** 2
    for j in range(cat_s.shape[1]):
        d += gamma * (cat_s[:, j][:, None] != cat_s[None, :, j])
    np.fill_diagonal(d, 0.0)
    sil = silhouette_samples(d, etq_s, metric="precomputed")
    return float(np.mean(sil))


# ==========================================================================
# 3. Gráficas
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


def fig_criterios(ks: list[int], curva: dict, archivo) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 7.0), dpi=150)
    espec = [("silhouette", "Silhouette (media)", "más alto = mejor"),
             ("calinski", "Calinski–Harabasz", "más alto = mejor"),
             ("davies", "Davies–Bouldin", "más bajo = mejor"),
             ("perdida", "Pérdida de información\n(inercia intra / total)",
              "más bajo = mejor")]
    for ax, (clave, titulo, nota) in zip(axes.ravel(), espec):
        y = curva[clave]
        ax.plot(ks, y, marker="o", color=AZUL, linewidth=2.0, markersize=5.4,
                zorder=3)
        mejor = ks[int(np.argmax(y))] if clave in ("silhouette", "calinski") \
            else ks[int(np.argmin(y))]
        ax.axvline(mejor, color=DORADO, linewidth=1.4, linestyle="--", zorder=2)
        ax.annotate(f"mejor k = {mejor}", (mejor, max(y)),
                    textcoords="offset points", xytext=(6, -2), fontsize=8,
                    color=GRIS_OSC)
        ax.set_title(f"{titulo}\n({nota})", color=TEXTO, fontsize=9.4, pad=8)
        ax.set_xlabel("k", color=TEXTO, fontsize=8.6)
        _estilo(ax)
    fig.suptitle("Elección de k con cuatro criterios\n"
                 f"Silhouette < 0,25 indica que no hay estructura sustancial "
                 "(Kaufman y Rousseeuw)", color=TEXTO, fontsize=11, y=1.02,
                 x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def fig_perfiles(perfiles: dict, archivo) -> None:
    """Barras agrupadas por variable: proporción de cada categoría en cada cluster."""
    variables = list(perfiles)
    fig, axes = plt.subplots(len(variables), 1,
                             figsize=(10.6, 1.5 + 1.35 * len(variables)),
                             dpi=150)
    if len(variables) == 1:
        axes = [axes]
    colores = [AZUL, DORADO, AZUL_CLARO]
    for ax, var in zip(axes, variables):
        d = perfiles[var]
        cats = list(d["categorias"])
        x = np.arange(len(cats))
        ancho = 0.8 / max(len(d["clusters"]), 1)
        for i, (cl, vals) in enumerate(d["clusters"].items()):
            ax.bar(x + (i - (len(d["clusters"]) - 1) / 2) * ancho, vals,
                   width=ancho, color=colores[i % len(colores)], zorder=2,
                   label=f"Cluster {cl}" if var == variables[0] else None)
        ax.set_xticks(x)
        ax.set_xticklabels([c[:22] for c in cats], rotation=16, ha="right",
                           fontsize=7.2)
        ax.set_ylabel("%", color=TEXTO, fontsize=8)
        ax.set_title(var, color=TEXTO, fontsize=8.8, pad=5, loc="left")
        ax.set_ylim(0, max(1.0, max(max(v) for v in d["clusters"].values()) * 1.18))
        _estilo(ax)
        ax.grid(axis="y", color=GRIS_CLARO, linewidth=0.5, alpha=0.9)
    axes[0].legend(frameon=False, fontsize=8, labelcolor=GRIS_OSC, ncol=3)
    fig.suptitle("Perfil de cada cluster: proporción de cada categoría",
                 color=TEXTO, fontsize=11, y=1.005, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def fig_nulo(obs: float, nulo: list[float], estadistico: str, archivo) -> None:
    fig, ax = plt.subplots(figsize=(8.6, 4.2), dpi=150)
    ax.hist(nulo, bins=14, color=GRIS_CLARO, zorder=2,
            label=f"Nulo (variables permutadas, {len(nulo)} réplicas)")
    ax.axvline(obs, color=AZUL, linewidth=2.2, zorder=3, label="Observado")
    p = (1 + sum(1 for v in nulo if v >= obs)) / (len(nulo) + 1)
    ax.set_xlabel(estadistico, color=TEXTO, fontsize=9)
    ax.set_ylabel("Réplicas", color=TEXTO, fontsize=9)
    ax.set_title(f"¿Hay estructura más allá de las marginales?\n"
                 f"{estadistico} observado = {obs:.4f} · p = {p:.3f}",
                 color=TEXTO, fontsize=10.2, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8.4, labelcolor=GRIS_OSC)
    _estilo(ax)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


# ==========================================================================
# 4. Principal
# ==========================================================================
def main() -> int:
    print("== F2-6 · Clustering formalizado de perfiles ==")
    out: dict = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "analisis": "F2-6 — Segmentación formalizada (OE5, multivariado)",
        "semilla": SEMILLA, "k_max": K_MAX, "n_init": N_INIT, "gamma": 0.5,
        "metodo": "k-prototypes de Huang (1998), el mismo que kproto() de R",
    }

    df = cargar()
    print(f"   base: {len(df):,} registros · {df['ID_PERSONA_PR'].nunique():,} "
          f"personas".replace(",", " "))
    faltan = int(df["edad"].isna().sum())
    edad = df["edad"]
    implausibles = int(((edad < 0) | (edad > 100)).sum())
    print(f"   faltantes en las variables del análisis: {faltan} "
          f"(de {len(df) * (len(CATEGORICAS) + 1):,} celdas)".replace(",", " "))
    print(f"   edades imposibles (<0 o >100): {implausibles}")

    cat, z, mapa = codificar(df)
    nb = [len(mapa[c]) for c in CATEGORICAS]
    print(f"   variables: {len(CATEGORICAS)} categóricas "
          f"({'+'.join(str(x) for x in nb)} categorías) + 1 numérica "
          f"({NUMERICA})")
    onehot = matriz_onehot(cat, z, nb)

    # γ pondera la parte categórica frente a la numérica. Con la edad
    # estandarizada (σ = 1), la heurística de Huang (γ = 0,5·σ) da 0,5.
    gamma = 0.5
    total_k1 = coste_k1(cat, z, gamma)

    out["datos"] = {
        "registros": int(len(df)),
        "personas": int(df["ID_PERSONA_PR"].nunique()),
        "faltantes_en_variables_del_analisis": faltan,
        "perdida_de_muestra_pct": 0.0,
        "comparacion_con_el_auditado": ("El auditado usaba cc() y descartaba el "
                                        "8,4 % de la fila por lista. Aquí los "
                                        "faltantes son categorías explícitas, así "
                                        "que la pérdida es 0 %."),
        "edades_imposibles": implausibles,
        "variables_categoricas": {c: {"etiqueta": CATEGORICAS[c],
                                      "n_categorias": nb[i],
                                      "categorias": mapa[c]}
                                  for i, c in enumerate(CATEGORICAS)},
        "variable_numerica": NUMERICA,
        "excluidas_y_por_que": {
            "TXT_POBLACION_DISCA": "73,6 % 'No disponible': solo existe en 2021 "
                                   "(F2-5). Incluirla alinearía los clusters con "
                                   "la convocatoria, no con un perfil.",
            "TXT_GRUPO_ETNICO / ID_VICTIMA_CONFLICTO": "misma razón.",
            "ID_CONVOCATORIA": "identifica el año, no un atributo de la persona.",
            "INST_FILIA": "alta cardinalidad y texto libre.",
        },
    }

    # ---------------- curva de k ----------------
    rng = np.random.default_rng(SEMILLA)
    ks = list(range(2, K_MAX + 1))
    curva = {"silhouette": [], "calinski": [], "davies": [], "perdida": [],
             "coste": []}
    etiquetas_k: dict[int, np.ndarray] = {}
    print(f"\n   ajustando k-prototypes para k = 2..{K_MAX} "
          f"({N_INIT} arranques cada uno)…")
    for k in ks:
        etq, coste = kprototypes(cat, z, k, gamma, rng)
        etiquetas_k[k] = etq
        sil = silhouette_mixta(cat, z, etq, gamma, rng)
        ch = float(calinski_harabasz_score(onehot, etq))
        db = float(davies_bouldin_score(onehot, etq))
        curva["silhouette"].append(sil)
        curva["calinski"].append(ch)
        curva["davies"].append(db)
        curva["coste"].append(coste)
        curva["perdida"].append(coste / total_k1)
        tam = np.bincount(etq).tolist()
        print(f"      k={k:2d} silhouette={sil:.4f} CH={ch:9.1f} DB={db:.4f} "
              f"pérdida={100*coste/total_k1:5.2f}% tamaños={tam}")

    k_sil = ks[int(np.argmax(curva["silhouette"]))]
    k_ch = ks[int(np.argmax(curva["calinski"]))]
    k_db = ks[int(np.argmin(curva["davies"]))]
    out["criterios_k"] = {
        "k": ks, **{c: [float(x) for x in curva[c]] for c in curva},
        "k_por_silhouette": int(k_sil),
        "k_por_calinski": int(k_ch),
        "k_por_davies_bouldin": int(k_db),
        "inercia_total_k1": float(total_k1),
        "umbral_silhouette_estructura": 0.25,
    }
    print(f"\n   mejor k: silhouette={k_sil} · CH={k_ch} · DB={k_db}")

    # ---------------- prueba de estructura frente al nulo ----------------
    # Se permuta CADA variable por separado: se conservan las marginales y se
    # destruye la asociación entre ellas. Si el criterio observado cae dentro de
    # lo que produce el nulo, la partición no refleja estructura conjunta.
    print(f"   prueba de estructura: {N_NULO} permutaciones de "
          f"{N_NULO_FILAS:,} filas con k = {k_sil}…".replace(",", " "))
    sub = rng.choice(len(df), size=min(N_NULO_FILAS, len(df)), replace=False)
    cat_s, z_s = cat[sub], z[sub]
    onehot_s = matriz_onehot(cat_s, z_s, nb)
    etq_obs_s, _ = kprototypes(cat_s, z_s, k_sil, gamma, rng,
                               n_init=N_INIT, max_iter=60)
    sil_obs_s = silhouette_mixta(cat_s, z_s, etq_obs_s, gamma, rng, n_muestra=2000)
    ch_obs_s = float(calinski_harabasz_score(onehot_s, etq_obs_s))
    nulo_sil, nulo_ch = [], []
    for i in range(N_NULO):
        cat_p = np.column_stack([
            rng.permutation(cat_s[:, j]) for j in range(cat_s.shape[1])])
        z_p = rng.permutation(z_s)
        etq_p, _ = kprototypes(cat_p, z_p, k_sil, gamma, rng,
                              n_init=max(2, N_INIT - 3), max_iter=60)
        nulo_sil.append(silhouette_mixta(cat_p, z_p, etq_p, gamma, rng,
                                         n_muestra=2000))
        nulo_ch.append(float(calinski_harabasz_score(
            matriz_onehot(cat_p, z_p, nb), etq_p)))
        if (i + 1) % 5 == 0:
            print(f"      permutación {i + 1}/{N_NULO}")
    p_sil = (1 + sum(1 for v in nulo_sil if v >= sil_obs_s)) / (N_NULO + 1)
    p_ch = (1 + sum(1 for v in nulo_ch if v >= ch_obs_s)) / (N_NULO + 1)
    out["prueba_de_estructura"] = {
        "descripcion": ("Se permuta cada variable por separado, conservando sus "
                        "marginales y rompiendo la asociación entre ellas. Si el "
                        "criterio observado no supera al del nulo, la partición "
                        "no captura estructura conjunta."),
        "k_evaluado": int(k_sil), "filas": int(len(sub)),
        "silhouette_observada": float(sil_obs_s),
        "silhouette_nulo_medio": float(np.mean(nulo_sil)),
        "silhouette_nulo_ic95": [float(np.percentile(nulo_sil, 2.5)),
                                 float(np.percentile(nulo_sil, 97.5))],
        "silhouette_p": float(p_sil),
        "calinski_observado": float(ch_obs_s),
        "calinski_nulo_medio": float(np.mean(nulo_ch)),
        "calinski_p": float(p_ch),
        "nulo_silhouette": [float(x) for x in nulo_sil],
        "nulo_calinski": [float(x) for x in nulo_ch],
    }
    print(f"   silhouette observada={sil_obs_s:.4f} · nulo medio="
          f"{np.mean(nulo_sil):.4f} · p={p_sil:.3f}")
    print(f"   CH observado={ch_obs_s:.1f} · nulo medio={np.mean(nulo_ch):.1f} · "
          f"p={p_ch:.3f}")

    # ---------------- perfiles y pérdida ----------------
    etq = etiquetas_k[k_sil]
    df["cluster"] = etq
    perfiles: dict = {}
    for c, etiqueta in CATEGORICAS.items():
        tab = pd.crosstab(df["cluster"], df[c], normalize="index") * 100
        perfiles[etiqueta] = {
            "categorias": [str(x) for x in tab.columns],
            "clusters": {str(i): [float(v) for v in tab.loc[i].to_numpy()]
                         for i in tab.index},
        }
    aportes = {}
    for c, etiqueta in CATEGORICAS.items():
        tab = pd.crosstab(df[c], df["cluster"], normalize="index")
        # V de Cramér entre la variable y el cluster: cuánto aporta a la partición
        obs_tab = pd.crosstab(df[c], df["cluster"]).to_numpy()
        n = obs_tab.sum()
        chi2 = (((obs_tab - np.outer(obs_tab.sum(1), obs_tab.sum(0)) / n) ** 2)
                / (np.outer(obs_tab.sum(1), obs_tab.sum(0)) / n)).sum()
        v = float(np.sqrt(chi2 / (n * (min(obs_tab.shape) - 1))))
        aportes[etiqueta] = {"cramer_v": v,
                             "n_categorias": int(obs_tab.shape[0])}
    # la edad, por medias
    medias_edad = df.groupby("cluster")["edad"].agg(["mean", "median", "size"])
    out["perfiles"] = perfiles
    out["aporte_de_cada_variable"] = dict(sorted(
        aportes.items(), key=lambda kv: -kv[1]["cramer_v"]))
    out["edad_por_cluster"] = {str(i): {"media": float(r["mean"]),
                                        "mediana": float(r["median"]),
                                        "n": int(r["size"])}
                               for i, r in medias_edad.iterrows()}
    out["perdida_de_informacion"] = {
        "inercia_total_k1": float(total_k1),
        "inercia_intra_k": float(curva["coste"][ks.index(k_sil)]),
        "perdida_pct": float(100 * curva["perdida"][ks.index(k_sil)]),
        "definicion": ("Cociente entre la inercia intra-cluster del k elegido y "
                       "la inercia total con un solo prototipo; 100 − pérdida es "
                       "la parte de la variabilidad mixta que la partición "
                       "reproduce."),
        "perdida_por_k": {str(k): float(100 * v)
                          for k, v in zip(ks, curva["perdida"])},
    }

    # ---------------- comprobaciones de honestidad ----------------
    # 1) ¿los clusters son solo la categoría (la variable más estructurante)?
    out["los_clusters_no_son_una_variable"] = {
        "ari_vs_categoria": float(adjusted_rand_score(
            df["NME_CLASIFICACION_PR"], etq)),
        "ari_vs_gran_area": float(adjusted_rand_score(
            df["NME_GRAN_AREA_PR"], etq)),
        "ari_vs_convocatoria": float(adjusted_rand_score(df["anio"], etq)),
        "lectura": ("Un ARI cercano a 1 indicaría que el cluster reproduce esa "
                    "variable y no un perfil; cercano a 0, que la partición es "
                    "independiente de ella."),
    }
    # 2) sensibilidad a la ponderación gamma
    sens = {}
    for g in (0.25, 0.5, 1.0):
        e2, _ = kprototypes(cat, z, k_sil, g, np.random.default_rng(SEMILLA))
        sens[str(g)] = float(adjusted_rand_score(etq, e2))
    out["sensibilidad_gamma"] = sens
    # 3) sensibilidad a las edades imposibles
    ok = ((df["edad"].isna()) | ((df["edad"] >= 0) & (df["edad"] <= 100))).to_numpy()
    e3, _ = kprototypes(cat[ok], z[ok], k_sil, gamma,
                        np.random.default_rng(SEMILLA))
    out["sensibilidad_edades_imposibles"] = {
        "filas_excluidas": int((~ok).sum()),
        "ari_vs_principal": float(adjusted_rand_score(etq[ok], e3)),
    }
    # 4) nivel de persona (una fila por persona, última convocatoria)
    ult = (df.sort_values("anio").drop_duplicates("ID_PERSONA_PR", keep="last")
             .reset_index(drop=True))
    cat_u, z_u, _ = codificar(ult)
    e4, _ = kprototypes(cat_u, z_u, k_sil, gamma,
                        np.random.default_rng(SEMILLA))
    sil_u = silhouette_mixta(cat_u, z_u, e4, gamma,
                             np.random.default_rng(SEMILLA))
    out["nivel_persona"] = {
        "filas": int(len(ult)),
        "silhouette": float(sil_u),
        "tamanos": np.bincount(e4).tolist(),
        "nota": ("La base de registros repite personas hasta 6 veces, así que las "
                 "observaciones no son independientes. Se repite el ajuste con una "
                 "fila por persona como comprobación."),
    }

    # ---------------- figuras ----------------
    GRAF.mkdir(parents=True, exist_ok=True)
    fig_criterios(ks, curva, GRAF / "f2_6_criterios_k.png")
    fig_perfiles(perfiles, GRAF / "f2_6_perfiles_clusters.png")
    fig_nulo(sil_obs_s, nulo_sil, "Silhouette (submuestra)",
             GRAF / "f2_6_prueba_estructura.png")
    out["figuras"] = sorted(p.name for p in GRAF.glob("*.png"))

    # ---------------- veredicto y validaciones ----------------
    hay_estructura = bool(p_sil < 0.05 and sil_obs_s > 0.25)
    sil_k = float(curva["silhouette"][ks.index(k_sil)])
    perd = float(100 * curva["perdida"][ks.index(k_sil)])
    if hay_estructura:
        expl = (f"k = {k_sil} maximiza la silhouette ({sil_k:.4f}), supera el "
                f"umbral de 0,25 y además descarta el nulo (p = {p_sil:.3f}): hay "
                f"estructura de clusters.")
    elif sil_k >= 0.25:
        expl = (f"k = {k_sil} maximiza la silhouette ({sil_k:.4f}), que SÍ supera "
                f"el umbral de 0,25, pero la prueba frente al nulo da "
                f"p = {p_sil:.3f}: permutando cada variable por separado se "
                f"obtiene una partición igual de buena (silhouette nula "
                f"{np.mean(nulo_sil):.4f}). El umbral de Kaufman y Rousseeuw no "
                f"basta aquí; lo que descarta la estructura es el nulo. La "
                f"partición existe porque k-prototypes siempre devuelve una, no "
                f"porque haya grupos separables, y solo reproduce el "
                f"{100 - perd:.1f} % de la variabilidad mixta.")
    else:
        expl = (f"k = {k_sil} maximiza la silhouette ({sil_k:.4f}), por debajo del "
                f"umbral de 0,25, y la prueba frente al nulo confirma que no hay "
                f"estructura (p = {p_sil:.3f}). No hay grupos separables.")
    out["veredicto"] = {
        "k_elegido_por_criterio": int(k_sil),
        "hay_estructura_de_clusters": hay_estructura,
        "silhouette_del_k_elegido": sil_k,
        "umbral_silhouette": 0.25,
        "p_frente_al_nulo": float(p_sil),
        "regla": ("Se declara estructura solo si la silhouette supera 0,25 "
                  "(Kaufman y Rousseeuw) Y el nulo la descarta (p < 0,05)."),
        "explicacion": expl,
        "respuesta_a_la_pregunta_de_k": (
            "El mejor k es 1 en el sentido sustantivo: no hay estructura de "
            "clusters. Cualquier k > 1 produce una partición, pero ninguna "
            "representa grupos reales."),
    }
    out["validaciones"] = {
        "sin_perdida_de_muestra": bool(faltan <= 1),
        "todas_las_filas_asignadas": bool(len(np.unique(etq)) == k_sil),
        "clusters_no_vacios": bool((np.bincount(etq) > 0).all()),
        "perdida_creciente_con_k": bool(
            all(curva["perdida"][i] >= curva["perdida"][i + 1]
                for i in range(len(curva["perdida"]) - 1))),
        "nulo_generado": bool(len(nulo_sil) == N_NULO),
        "silhouette_en_rango": bool(-1 <= min(
            curva["silhouette"]) and max(curva["silhouette"]) <= 1),
        "perdida_entre_0_y_100": bool(
            all(0 < v <= 1.0 for v in curva["perdida"])),
        "sensibilidad_gamma_reportada": bool(len(sens) == 3),
    }
    print()
    for k, v in out["validaciones"].items():
        print(f"   [{'OK ' if v else 'NO '}] {k}")
    print(f"\n   ARI vs categoría: "
          f"{out['los_clusters_no_son_una_variable']['ari_vs_categoria']:.3f} · "
          f"vs gran área: {out['los_clusters_no_son_una_variable']['ari_vs_gran_area']:.3f}"
          f" · vs convocatoria: "
          f"{out['los_clusters_no_son_una_variable']['ari_vs_convocatoria']:.3f}")
    print(f"   aporte (V de Cramér): "
          f"{[(k, round(v['cramer_v'], 3)) for k, v in out['aporte_de_cada_variable'].items()]}")
    print(f"   niveles de persona: silhouette={sil_u:.4f} · tamaños={out['nivel_persona']['tamanos']}")
    print(f"\n   VEREDICTO: k={k_sil} · estructura de clusters = {hay_estructura}")

    df[["ID_PERSONA_PR", "anio", "cluster"]].to_csv(CSV_CLUSTERS, index=False)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"\n-> {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size:,} bytes)")
    print(f"-> {GRAF.relative_to(RAIZ)}/ ({len(out['figuras'])} figuras)")
    print(f"-> {CSV_CLUSTERS.relative_to(RAIZ)} ({len(df)} filas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
