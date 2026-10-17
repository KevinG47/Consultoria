"""
Sprint 2 — Análisis de género por área OCDE (Issue #22)

Representación femenina y brecha de género en las 6 convocatorias (2013–2021)
a nivel de gran área, área y especialidad OCDE.

Uso:
    python scripts/sprint2_genero_ocde.py

Salidas:
    artifacts/sprint2_genero_ocde/fig01_barras_pct_femenino.png
    artifacts/sprint2_genero_ocde/fig02_heatmap_pct_femenino.png
    artifacts/sprint2_genero_ocde/fig03_lineas_evolucion.png
    artifacts/sprint2_genero_ocde/fig04_brecha_genero.png
    evidencias/genero_pct_femenino_por_gran_area.csv
    evidencias/genero_tabla_pivot_gran_area.csv
    evidencias/genero_brecha_por_gran_area.csv
    evidencias/genero_pct_femenino_por_area.csv
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
from analisis.genero import (
    pct_femenino_por_area,
    tabla_pivot_pct_femenino,
    brecha_genero,
    evolucion_pct_femenino,
)

ARTIFACTS = ROOT / "artifacts" / "sprint2_genero_ocde"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
EVIDENCIAS.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid")


def fig_barras_pct_femenino(df) -> None:
    """% femenino por gran área — promedio de todas las convocatorias."""
    pivot = tabla_pivot_pct_femenino(df, col_area="NME_GRAN_AREA_PR")
    promedio = (pivot["promedio"] * 100).sort_values()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(promedio.index, promedio.values, color="steelblue")
    ax.axvline(promedio.mean(), color="tomato", linestyle="--", linewidth=1.5,
               label=f"Promedio general: {promedio.mean():.1f}%")
    for bar, val in zip(bars, promedio.values):
        ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=9)
    ax.set_xlabel("% investigadoras femeninas")
    ax.set_title("Representacion femenina por gran area OCDE (promedio 2013-2021)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig01_barras_pct_femenino.png", dpi=150)
    plt.close()


def fig_heatmap_pct_femenino(df) -> None:
    """Heatmap % femenino: gran área × convocatoria."""
    pivot = tabla_pivot_pct_femenino(df, col_area="NME_GRAN_AREA_PR")
    pivot_plot = pivot.drop(columns="promedio") * 100

    fig, ax = plt.subplots(figsize=(11, 5))
    sns.heatmap(
        pivot_plot,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn",
        vmin=0,
        vmax=60,
        linewidths=0.4,
        cbar_kws={"label": "% femenino"},
        ax=ax,
    )
    ax.set_title("% investigadoras femeninas por gran area OCDE y convocatoria")
    ax.set_xlabel("Convocatoria")
    ax.set_ylabel("Gran area OCDE")
    ax.tick_params(axis="y", rotation=0)
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig02_heatmap_pct_femenino.png", dpi=150, bbox_inches="tight")
    plt.close()


def fig_lineas_evolucion(df) -> None:
    """Evolución del % femenino por gran área a lo largo del tiempo."""
    evol = evolucion_pct_femenino(df, col_area="NME_GRAN_AREA_PR")
    fig, ax = plt.subplots(figsize=(12, 5))
    for area, grupo in evol.groupby("NME_GRAN_AREA_PR"):
        ax.plot(
            grupo["ANO_CONVO_INT"].astype(str),
            grupo["pct_femenino"] * 100,
            marker="o",
            label=area,
            linewidth=1.8,
        )
    ax.axhline(50, color="gray", linestyle="--", linewidth=1, alpha=0.6, label="Paridad (50%)")
    ax.set_ylim(0, 70)
    ax.set_title("Evolucion del % femenino por gran area OCDE (2013-2021)")
    ax.set_xlabel("Convocatoria")
    ax.set_ylabel("% investigadoras femeninas")
    ax.legend(title="Gran area", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig03_lineas_evolucion.png", dpi=150, bbox_inches="tight")
    plt.close()


def fig_brecha_genero(df) -> None:
    """Brecha de género (M% - F%) por gran área — última convocatoria vs primera."""
    brecha_ini = brecha_genero(df, col_area="NME_GRAN_AREA_PR")

    anios = sorted(brecha_ini["ANO_CONVO_INT"].unique())
    a0, a1 = anios[0], anios[-1]

    b0 = brecha_ini[brecha_ini["ANO_CONVO_INT"] == a0].set_index("NME_GRAN_AREA_PR")["brecha"] * 100
    b1 = brecha_ini[brecha_ini["ANO_CONVO_INT"] == a1].set_index("NME_GRAN_AREA_PR")["brecha"] * 100
    areas = b1.sort_values(ascending=False).index

    x = range(len(areas))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar([i - width / 2 for i in x], b0.reindex(areas), width,
           label=str(a0), color="steelblue", alpha=0.8)
    ax.bar([i + width / 2 for i in x], b1.reindex(areas), width,
           label=str(a1), color="tomato", alpha=0.8)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(areas, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Brecha M% - F% (puntos porcentuales)")
    ax.set_title(f"Brecha de genero por gran area OCDE: {a0} vs {a1}")
    ax.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig04_brecha_genero.png", dpi=150, bbox_inches="tight")
    plt.close()


def main() -> None:
    print("[1/4] Cargando datos...")
    df = transformar(cargar_consolidado())

    # Resumen general
    genero_total = df[df["NME_GENERO_PR"].isin(["FEMENINO", "MASCULINO"])]["NME_GENERO_PR"].value_counts()
    pct_f = genero_total.get("FEMENINO", 0) / genero_total.sum() * 100
    print(f"      Femenino global: {pct_f:.1f}%  |  {genero_total.to_dict()}")

    print("[2/4] Generando figuras...")
    fig_barras_pct_femenino(df)
    fig_heatmap_pct_femenino(df)
    fig_lineas_evolucion(df)
    fig_brecha_genero(df)

    print("[3/4] Tablas resumen...")
    pct_gran = pct_femenino_por_area(df, col_area="NME_GRAN_AREA_PR")
    pivot_gran = tabla_pivot_pct_femenino(df, col_area="NME_GRAN_AREA_PR")
    brecha_gran = brecha_genero(df, col_area="NME_GRAN_AREA_PR")
    pct_area = pct_femenino_por_area(df, col_area="NME_AREA_PR")

    print("\n% femenino por gran area (promedio):")
    print((pivot_gran["promedio"] * 100).round(1).to_string())

    print("[4/4] Exportando evidencias...")
    pct_gran.to_csv(EVIDENCIAS / "genero_pct_femenino_por_gran_area.csv", index=False)
    pivot_gran.to_csv(EVIDENCIAS / "genero_tabla_pivot_gran_area.csv")
    brecha_gran.to_csv(EVIDENCIAS / "genero_brecha_por_gran_area.csv", index=False)
    pct_area.to_csv(EVIDENCIAS / "genero_pct_femenino_por_area.csv", index=False)

    print(f"\nFiguras : {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs    : {EVIDENCIAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
