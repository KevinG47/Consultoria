"""
Sprint 2 — Análisis de concentración territorial HHI (Issue #13)

Calcula el índice de Herfindahl-Hirschman (HHI) por departamento y región
para las 6 convocatorias (2013–2021) y visualiza la distribución geográfica.

Uso:
    python scripts/sprint2_territorial.py

Salidas:
    artifacts/sprint2_territorial/fig01_top_departamentos.png
    artifacts/sprint2_territorial/fig02_hhi_evolucion.png
    artifacts/sprint2_territorial/fig03_heatmap_cuotas.png
    evidencias/territorial_*.csv
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
from analisis.territorial import hhi_por_convocatoria, top_territorios, tabla_cuotas

ARTIFACTS = ROOT / "artifacts" / "sprint2_territorial"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
EVIDENCIAS.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid")


def fig_top_departamentos(df) -> None:
    top_dept = top_territorios(df, col_geo="NME_DEPARTAMENTO_RES_PR", n=10)
    pivot = top_dept.pivot_table(
        index="NME_DEPARTAMENTO_RES_PR",
        columns="ANO_CONVO_INT",
        values="pct",
        aggfunc="sum",
        fill_value=0,
    )
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    pivot.T.plot(kind="bar", stacked=False, figsize=(13, 5), colormap="tab10")
    plt.title("Distribución de investigadores: top 10 departamentos por convocatoria")
    plt.xlabel("Convocatoria")
    plt.ylabel("Proporción de investigadores")
    plt.legend(title="Departamento", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig01_top_departamentos.png", dpi=150, bbox_inches="tight")
    plt.close()


def fig_hhi_evolucion(hhi_dept, hhi_region) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    for ax, data, titulo in zip(
        axes,
        [hhi_dept, hhi_region],
        ["HHI departamental", "HHI regional"],
    ):
        ax.plot(
            data["ANO_CONVO_INT"].astype(str),
            data["hhi"],
            marker="o",
            color="steelblue",
            linewidth=2,
        )
        ax.set_title(titulo)
        ax.set_xlabel("Convocatoria")
        ax.set_ylabel("HHI")
        ax.set_ylim(0, data["hhi"].max() * 1.25)
        for _, row in data.iterrows():
            ax.annotate(
                f"{row['hhi']:.3f}",
                (str(int(row["ANO_CONVO_INT"])), row["hhi"]),
                textcoords="offset points",
                xytext=(0, 7),
                ha="center",
                fontsize=8,
            )
    plt.suptitle("Evolución de la concentración territorial (HHI)", fontsize=13)
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig02_hhi_evolucion.png", dpi=150)
    plt.close()


def fig_heatmap_cuotas(df) -> None:
    cuotas_pivot = tabla_cuotas(df, n=15)
    plt.figure(figsize=(12, 7))
    sns.heatmap(
        cuotas_pivot * 100,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        linewidths=0.4,
        cbar_kws={"label": "% investigadores"},
    )
    plt.title("Cuota (%) de investigadores por departamento y convocatoria — top 15")
    plt.xlabel("Convocatoria")
    plt.ylabel("Departamento")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig03_heatmap_cuotas.png", dpi=150, bbox_inches="tight")
    plt.close()
    return cuotas_pivot


def main() -> None:
    print("[1/4] Cargando datos...")
    df = transformar(cargar_consolidado())

    print("[2/4] Top departamentos...")
    fig_top_departamentos(df)

    print("[3/4] Calculando HHI...")
    hhi_dept = hhi_por_convocatoria(df, col_geo="NME_DEPARTAMENTO_RES_PR")
    hhi_region = hhi_por_convocatoria(df, col_geo="NME_REGION_RES_PR")
    print("HHI departamental:")
    print(hhi_dept.to_string(index=False))
    print("\nHHI regional:")
    print(hhi_region.to_string(index=False))

    fig_hhi_evolucion(hhi_dept, hhi_region)
    cuotas_pivot = fig_heatmap_cuotas(df)

    print("[4/4] Exportando evidencias...")
    hhi_dept.to_csv(EVIDENCIAS / "territorial_hhi_por_convocatoria.csv", index=False)
    hhi_region.to_csv(EVIDENCIAS / "territorial_hhi_region_por_convocatoria.csv", index=False)
    cuotas_pivot.to_csv(EVIDENCIAS / "territorial_cuotas_departamento.csv")

    print(f"\nFiguras : {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs    : {EVIDENCIAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
