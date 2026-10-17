"""
Sprint 3 — Network analysis de co-filiacion institucional (Issue #15)

Grafo donde nodo = institucion, arista = investigadores con doble afiliacion.

Uso:
    python scripts/sprint3_redes.py

Salidas:
    artifacts/sprint3_redes/fig01_distribucion_grado.png
    artifacts/sprint3_redes/fig02_evolucion_aristas.png
    artifacts/sprint3_redes/fig03_top_instituciones.png
    evidencias/redes_pares_cofiliacion.csv
    evidencias/redes_nodos_global.csv
    evidencias/redes_aristas_global.csv
    evidencias/redes_metricas_por_convocatoria.csv
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from ingesta import cargar_consolidado
from Transformacion import transformar
from analisis.redes import (
    construir_pares,
    construir_grafo,
    metricas_grafo,
    tabla_nodos,
    tabla_aristas,
    metricas_por_convocatoria,
)

ARTIFACTS = ROOT / "artifacts" / "sprint3_redes"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")


def fig_distribucion_grado(G) -> None:
    grados = sorted([d for _, d in G.degree()], reverse=True)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(range(len(grados)), grados, color="steelblue", width=1.0)
    ax.set_xlabel("Nodo (ordenado por grado)")
    ax.set_ylabel("Grado")
    ax.set_title("Distribucion de grado — grafo global de co-filiacion")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig01_distribucion_grado.png", dpi=150)
    plt.close()


def fig_evolucion_aristas(metricas_df) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    anios = metricas_df["anio"].astype(str)

    axes[0].plot(anios, metricas_df["n_aristas"], marker="o", color="steelblue")
    axes[0].set_title("Aristas por convocatoria")
    axes[0].set_ylabel("N aristas")

    axes[1].plot(anios, metricas_df["n_nodos"], marker="o", color="tomato")
    axes[1].set_title("Nodos (instituciones) por convocatoria")
    axes[1].set_ylabel("N nodos")

    for ax in axes:
        ax.set_xlabel("Convocatoria")
    plt.suptitle("Evolucion del grafo de co-filiacion (2013-2021)")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig02_evolucion_aristas.png", dpi=150)
    plt.close()


def fig_top_instituciones(nodos_df, top_n=20) -> None:
    top = nodos_df.head(top_n)
    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(top["institucion"], top["grado_ponderado"], color="steelblue")
    for bar, val in zip(bars, top["grado_ponderado"]):
        ax.text(val + 0.1, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Grado ponderado (investigadores compartidos)")
    ax.set_title(f"Top {top_n} instituciones por co-filiacion (global 2013-2021)")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig03_top_instituciones.png", dpi=150)
    plt.close()


def main() -> None:
    print("[1/5] Cargando datos...")
    df = transformar(cargar_consolidado())

    print("[2/5] Construyendo pares de co-filiacion...")
    pares = construir_pares(df)
    print(f"      {len(pares):,} investigadores con doble afiliacion")
    print(f"      {pares['inst_a'].nunique() + pares['inst_b'].nunique()} instituciones mencionadas")

    print("[3/5] Construyendo grafo global...")
    G = construir_grafo(pares)
    m = metricas_grafo(G)
    print(f"      Nodos     : {m['n_nodos']}")
    print(f"      Aristas   : {m['n_aristas']}")
    print(f"      Densidad  : {m['densidad']}")
    print(f"      Componentes: {m['n_componentes']}")
    print(f"      Hub principal: {m['nodo_mayor_grado']} (grado {m['grado_max']})")

    print("[4/5] Generando figuras...")
    nodos_df = tabla_nodos(G)
    metricas_df = metricas_por_convocatoria(pares)

    fig_distribucion_grado(G)
    fig_evolucion_aristas(metricas_df)
    fig_top_instituciones(nodos_df)

    print("[5/5] Exportando evidencias...")
    pares.to_csv(EVIDENCIAS / "redes_pares_cofiliacion.csv", index=False)
    nodos_df.to_csv(EVIDENCIAS / "redes_nodos_global.csv", index=False)
    tabla_aristas(G).to_csv(EVIDENCIAS / "redes_aristas_global.csv", index=False)
    metricas_df.to_csv(EVIDENCIAS / "redes_metricas_por_convocatoria.csv", index=False)

    print("\nResumen por convocatoria:")
    print(metricas_df[["anio", "n_nodos", "n_aristas", "grado_max", "nodo_mayor_grado"]].to_string(index=False))
    print(f"\nFiguras : {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs    : {EVIDENCIAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
