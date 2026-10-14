"""
Sprint 2 — Matrices de transición de categoría (Issue #12)

Calcula y visualiza las matrices de probabilidad de transición entre
las categorías Junior/Asociado/Senior/Emérito para los 5 periodos
consecutivos de las 6 convocatorias (2013–2021).

Uso:
    python scripts/sprint2_matrices_transicion.py

Salidas:
    artifacts/sprint2_transiciones/fig01_heatmaps_ext.png
    artifacts/sprint2_transiciones/fig02_heatmaps_obs.png
    evidencias/matriz_transicion_*.csv
    evidencias/matriz_probabilidades_*.csv
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
from analisis.longitudinal import (
    construir_panel,
    comparar_periodo,
    matriz_transicion,
    matrices_todos_periodos,
)

ARTIFACTS = ROOT / "artifacts" / "sprint2_transiciones"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
EVIDENCIAS.mkdir(exist_ok=True)

sns.set_theme(style="white")


def fig_heatmaps(matrices: dict, titulo: str, cmap: str, path: pathlib.Path) -> None:
    periodos = list(matrices.keys())
    n = len(periodos)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4))
    for ax, periodo in zip(axes, periodos):
        _, probs = matrices[periodo]
        sns.heatmap(
            probs,
            annot=True,
            fmt=".2f",
            cmap=cmap,
            vmin=0,
            vmax=1,
            linewidths=0.5,
            ax=ax,
            cbar=False,
        )
        ax.set_title(periodo, fontsize=10)
        ax.set_xlabel("Categoría final")
        ax.set_ylabel("Categoría inicial")
        ax.tick_params(axis="x", rotation=35)
        ax.tick_params(axis="y", rotation=0)
    plt.suptitle(titulo, fontsize=13)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def main() -> None:
    print("[1/4] Cargando datos...")
    df = transformar(cargar_consolidado())

    print("[2/4] Construyendo panel...")
    panel = construir_panel(df)
    anios = sorted(panel["ANO_CONVO_INT"].unique())

    print("[3/4] Calculando y mostrando matrices...")
    for a0, a1 in zip(anios, anios[1:]):
        comp = comparar_periodo(panel, a0, a1)
        _, probs_obs = matriz_transicion(comp, incluir_desaparece=False)
        _, probs_ext = matriz_transicion(comp, incluir_desaparece=True)
        print(f"\n{'='*55}")
        print(f"Periodo {a0}–{a1} — Observada (solo retenidos):")
        print(probs_obs.to_string())
        print(f"\nPeriodo {a0}–{a1} — Extendida (incluye Desaparece):")
        print(probs_ext.to_string())

    print("\n[4/4] Generando figuras y exportando...")
    matrices_ext = matrices_todos_periodos(panel, incluir_desaparece=True)
    matrices_obs = matrices_todos_periodos(panel, incluir_desaparece=False)

    fig_heatmaps(
        matrices_ext,
        "Matrices de probabilidad de transición — extendida (incluye Desaparece)",
        "Blues",
        ARTIFACTS / "fig01_heatmaps_ext.png",
    )
    fig_heatmaps(
        matrices_obs,
        "Matrices de probabilidad de transición — observada (solo retenidos)",
        "Greens",
        ARTIFACTS / "fig02_heatmaps_obs.png",
    )

    for periodo, (conteos, probs) in matrices_ext.items():
        pf = periodo.replace("–", "_")
        conteos.to_csv(EVIDENCIAS / f"matriz_transicion_ext_{pf}.csv")
        probs.to_csv(EVIDENCIAS / f"matriz_probabilidades_ext_{pf}.csv")

    for periodo, (conteos, probs) in matrices_obs.items():
        pf = periodo.replace("–", "_")
        conteos.to_csv(EVIDENCIAS / f"matriz_transicion_obs_{pf}.csv")
        probs.to_csv(EVIDENCIAS / f"matriz_probabilidades_obs_{pf}.csv")

    print(f"\nFiguras : {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs    : {EVIDENCIAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
