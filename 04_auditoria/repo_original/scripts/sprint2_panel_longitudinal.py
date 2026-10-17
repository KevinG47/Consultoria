"""
Sprint 2 — Panel longitudinal de investigadores (Issue #11)

Análisis descriptivo de las 6 convocatorias (2013–2021) y seguimiento
individual de investigadores por ID_PERSONA_PR entre periodos consecutivos.

Uso:
    python scripts/sprint2_panel_longitudinal.py

Salidas:
    artifacts/sprint2_longitudinal/fig01_evolucion_total.png
    artifacts/sprint2_longitudinal/fig02_evolucion_genero.png
    artifacts/sprint2_longitudinal/fig03_evolucion_area.png
    artifacts/sprint2_longitudinal/fig04_categorias.png
    artifacts/sprint2_longitudinal/fig05_nuevos_ingresos.png
    artifacts/sprint2_longitudinal/fig06_tracking_periodos.png
    artifacts/sprint2_longitudinal/fig07_retencion.png
    evidencias/panel_longitudinal_*.csv
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ingesta import cargar_consolidado
from Transformacion import transformar
from analisis.longitudinal import (
    construir_panel,
    comparar_periodo,
    tracking_por_categoria,
    tracking_todos_periodos,
    tasa_retencion_por_periodo,
)

ARTIFACTS = ROOT / "artifacts" / "sprint2_longitudinal"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
EVIDENCIAS.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (11, 5)


def fig_evolucion_total(df: pd.DataFrame) -> None:
    evolucion = df.groupby("ANO_CONVO_INT").size().reset_index(name="n")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(evolucion["ANO_CONVO_INT"].astype(str), evolucion["n"],
           color="steelblue", edgecolor="white", width=0.5)
    for _, row in evolucion.iterrows():
        ax.text(str(row["ANO_CONVO_INT"]), row["n"] + 150,
                f'{row["n"]:,}', ha="center", fontsize=10)
    ax.set_title("Investigadores reconocidos por convocatoria")
    ax.set_xlabel("Convocatoria")
    ax.set_ylabel("Investigadores")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig01_evolucion_total.png", dpi=150)
    plt.close()


def fig_evolucion_genero(df: pd.DataFrame) -> None:
    genero_anio = (
        df.groupby(["ANO_CONVO_INT", "NME_GENERO_PR"])
        .size()
        .reset_index(name="n")
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    for genero, grupo in genero_anio.groupby("NME_GENERO_PR"):
        ax.plot(grupo["ANO_CONVO_INT"].astype(str), grupo["n"],
                marker="o", label=genero)
    ax.set_title("Evolución de investigadores por género")
    ax.set_xlabel("Convocatoria")
    ax.set_ylabel("Investigadores")
    ax.legend(title="Género")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig02_evolucion_genero.png", dpi=150)
    plt.close()


def fig_evolucion_area(df: pd.DataFrame) -> None:
    top_areas = df["NME_GRAN_AREA_PR"].value_counts().head(5).index.tolist()
    area_anio = (
        df[df["NME_GRAN_AREA_PR"].isin(top_areas)]
        .groupby(["ANO_CONVO_INT", "NME_GRAN_AREA_PR"])
        .size()
        .reset_index(name="n")
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    for area, grupo in area_anio.groupby("NME_GRAN_AREA_PR"):
        ax.plot(grupo["ANO_CONVO_INT"].astype(str), grupo["n"],
                marker="o", label=area)
    ax.set_title("Evolución por gran área de conocimiento (top 5)")
    ax.set_xlabel("Convocatoria")
    ax.set_ylabel("Investigadores")
    ax.legend(title="Gran área", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig03_evolucion_area.png", dpi=150)
    plt.close()


def fig_categorias(df: pd.DataFrame) -> None:
    clas_anio = (
        df.groupby(["ANO_CONVO_INT", "NME_CLASIFICACION_PR"])
        .size()
        .unstack(fill_value=0)
    )
    clas_anio.T.plot(kind="bar", figsize=(12, 5), colormap="tab10")
    plt.title("Categorías de clasificación por convocatoria")
    plt.xlabel("Categoría")
    plt.ylabel("Investigadores")
    plt.xticks(rotation=35, ha="right")
    plt.legend(title="Convocatoria")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig04_categorias.png", dpi=150)
    plt.close()


def fig_nuevos_ingresos(panel: pd.DataFrame) -> pd.DataFrame:
    anios = sorted(panel["ANO_CONVO_INT"].unique())
    filas = []
    for i, anio in enumerate(anios):
        ids_actual = set(panel.loc[panel["ANO_CONVO_INT"] == anio, "ID_PERSONA_PR"])
        ids_previos = set(panel.loc[panel["ANO_CONVO_INT"].isin(anios[:i]), "ID_PERSONA_PR"])
        nuevos = len(ids_actual - ids_previos)
        filas.append({"convocatoria": anio, "total": len(ids_actual), "nuevos": nuevos})
    df_ing = pd.DataFrame(filas)
    df_ing["pct_nuevos"] = (df_ing["nuevos"] / df_ing["total"]).round(3)

    fig, ax = plt.subplots(figsize=(10, 4))
    x = df_ing["convocatoria"].astype(str)
    ax.bar(x, df_ing["total"], label="Total", color="steelblue", alpha=0.7)
    ax.bar(x, df_ing["nuevos"], label="Nuevos (sin historial previo)", color="tomato", alpha=0.85)
    ax.set_title("Investigadores por convocatoria: total vs. nuevos ingresos")
    ax.set_xlabel("Convocatoria")
    ax.set_ylabel("Investigadores")
    ax.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig05_nuevos_ingresos.png", dpi=150)
    plt.close()
    return df_ing


def fig_tracking(resumen_all: pd.DataFrame) -> None:
    colores = {
        "Se mantiene": "steelblue",
        "Desaparece": "gray",
        "Sube": "seagreen",
        "Baja": "tomato",
    }
    periodos = resumen_all["periodo"].unique()
    fig, axes = plt.subplots(1, len(periodos), figsize=(18, 5), sharey=False)
    for ax, periodo in zip(axes, periodos):
        sub = resumen_all[resumen_all["periodo"] == periodo].set_index("resultado")
        orden = ["Se mantiene", "Desaparece", "Sube", "Baja"]
        cats = [r for r in orden if r in sub.index]
        ax.bar(cats, [sub.loc[r, "n"] for r in cats], color=[colores[r] for r in cats])
        ax.set_title(periodo, fontsize=10)
        ax.set_ylabel("Investigadores")
        ax.tick_params(axis="x", rotation=30)
    plt.suptitle("Tracking longitudinal — todos los periodos consecutivos", fontsize=13)
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig06_tracking_periodos.png", dpi=150)
    plt.close()


def fig_retencion(retencion: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(retencion["periodo"], retencion["tasa_retencion"] * 100,
            marker="o", color="steelblue", linewidth=2, label="Retención (%)")
    ax.bar(retencion["periodo"],
           retencion["nuevos_en_final"] / retencion["total_inicial"] * 100,
           alpha=0.4, color="tomato", label="Nuevos / total anterior (%)")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Porcentaje (%)")
    ax.set_title("Tasas de retención y nuevos ingresos entre convocatorias consecutivas")
    ax.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig07_retencion.png", dpi=150)
    plt.close()


def main() -> None:
    print("[1/4] Cargando datos...")
    df = transformar(cargar_consolidado())
    print(f"      Shape: {df.shape}")

    print("[2/4] Generando figuras descriptivas...")
    fig_evolucion_total(df)
    fig_evolucion_genero(df)
    fig_evolucion_area(df)
    fig_categorias(df)

    print("[3/4] Panel longitudinal...")
    panel = construir_panel(df)
    print(f"      {len(panel):,} filas | {panel['ID_PERSONA_PR'].nunique():,} investigadores únicos")
    anios = sorted(panel["ANO_CONVO_INT"].unique())

    df_ingresos = fig_nuevos_ingresos(panel)
    resumen_all = tracking_todos_periodos(panel)
    print(resumen_all.to_string(index=False))
    fig_tracking(resumen_all)

    retencion = tasa_retencion_por_periodo(panel)
    print(retencion.to_string(index=False))
    fig_retencion(retencion)

    print("[4/4] Exportando evidencias...")
    resumen_all.to_csv(EVIDENCIAS / "panel_longitudinal_resumen_todos_periodos.csv", index=False)
    df_ingresos.to_csv(EVIDENCIAS / "panel_longitudinal_ingresos_por_convocatoria.csv", index=False)
    retencion.to_csv(EVIDENCIAS / "panel_longitudinal_tasas_retencion.csv", index=False)
    for a0, a1 in zip(anios, anios[1:]):
        comp = comparar_periodo(panel, a0, a1)
        tracking_por_categoria(comp).to_csv(
            EVIDENCIAS / f"panel_longitudinal_cat_{a0}_{a1}.csv"
        )

    print(f"\nFiguras : {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs    : {EVIDENCIAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
