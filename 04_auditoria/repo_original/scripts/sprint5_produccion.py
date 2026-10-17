"""
Sprint 5 — Análisis de Producción de Grupos de Investigación.

Cruza el dataset de productos (Socrata 33dq-ab5a) con investigadores
reconocidos (bqtm-4y2h) usando id_persona_pd ↔ id_persona_pr.

Hallazgos centrales que produce:
    1. Cobertura de reconocimiento: % de productos firmados por
       investigadores reconocidos vs. autores no reconocidos.
    2. Productividad por categoría (Junior / Asociado / Senior / Emérito).
    3. Brecha de productividad por género × gran área OCDE.
    4. Concentración territorial de productos vs. concentración de
       investigadores (ratio).
    5. Mix de tipologías de producto por convocatoria y por categoría.
    6. Reconocidos sin producción registrada (calidad de captura).

Uso:
    python scripts/sprint5_produccion.py

Salidas:
    artifacts/sprint5_produccion/fig01_cobertura_reconocidos.png
    artifacts/sprint5_produccion/fig02_productividad_por_categoria.png
    artifacts/sprint5_produccion/fig03_brecha_genero_productividad.png
    artifacts/sprint5_produccion/fig04_concentracion_territorial.png
    artifacts/sprint5_produccion/fig05_mix_tipologias.png
    artifacts/sprint5_produccion/fig06_reconocidos_sin_produccion.png
    evidencias/produccion_*.csv
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from ingesta import cargar_consolidado, cargar_produccion
from Transformacion import transformar
from analisis.produccion import (
    normalizar_produccion,
    cobertura_reconocidos,
    cobertura_autores_unicos,
    productividad_por_categoria,
    productividad_por_genero_area,
    brecha_productividad_genero,
    productividad_territorial,
    mix_tipologias,
    tipologias_por_categoria,
    reconocidos_sin_produccion,
)

ARTIFACTS = ROOT / "artifacts" / "sprint5_produccion"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

def fig_cobertura_reconocidos(cob_df) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    x = cob_df["ANO_CONVO_INT"].astype(str)
    ax.bar(x, cob_df["n_reconocidos"], label="Firmados por investigadores reconocidos",
           color="steelblue")
    ax.bar(x, cob_df["n_no_reconocidos"], bottom=cob_df["n_reconocidos"],
           label="Firmados por autores NO reconocidos", color="lightgray")
    for i, (rec, total, pct) in enumerate(
        zip(cob_df["n_reconocidos"], cob_df["n_productos"], cob_df["pct_reconocidos"])
    ):
        ax.text(i, total + 5000, f"{pct:.1f}%", ha="center", fontsize=9)
    ax.set_ylabel("# productos")
    ax.set_xlabel("Convocatoria")
    ax.set_title("Cobertura de reconocimiento: ¿quién firma los productos?")
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig01_cobertura_reconocidos.png", dpi=150)
    plt.close()


def fig_productividad_por_categoria(prod_cat_df) -> None:
    pivot = prod_cat_df.pivot_table(
        index="ANO_CONVO_INT",
        columns="NME_CLASIFICACION_PR",
        values="productos_promedio",
    )
    fig, ax = plt.subplots(figsize=(11, 6))
    pivot.plot(marker="o", ax=ax, linewidth=2)
    ax.set_ylabel("Productos promedio por investigador (en su convocatoria)")
    ax.set_xlabel("Convocatoria")
    ax.set_title("Productividad promedio por categoría de reconocimiento")
    ax.legend(title="Categoría", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig02_productividad_por_categoria.png",
                dpi=150, bbox_inches="tight")
    plt.close()


def fig_brecha_genero(brecha_df) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(brecha_df))
    width = 0.38
    ax.bar(x - width / 2, brecha_df["prom_femenino"], width,
           label="Mujeres", color="purple")
    ax.bar(x + width / 2, brecha_df["prom_masculino"], width,
           label="Hombres", color="darkorange")
    ax.set_xticks(x)
    ax.set_xticklabels([str(g)[:25] for g in brecha_df["NME_GRAN_AREA_PR"]],
                        rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("Productos promedio por investigador")
    ax.set_title("Brecha de productividad por género — gran área OCDE")
    ax.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig03_brecha_genero_productividad.png",
                dpi=150, bbox_inches="tight")
    plt.close()


def fig_concentracion_territorial(terr_df, top_n: int = 15) -> None:
    top = terr_df.head(top_n).copy()
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(top))
    width = 0.38
    ax.bar(x - width / 2, top["pct_productos"], width,
           label="% de productos", color="steelblue")
    ax.bar(x + width / 2, top["pct_investigadores"], width,
           label="% de investigadores", color="lightcoral")
    ax.set_xticks(x)
    ax.set_xticklabels([str(t)[:18] for t in top["NME_DEPARTAMENTO_RES_PR"]],
                        rotation=40, ha="right", fontsize=9)
    ax.set_ylabel("% del total nacional")
    ax.set_title("Top departamentos: ¿concentran más productos que investigadores?")
    ax.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig04_concentracion_territorial.png",
                dpi=150, bbox_inches="tight")
    plt.close()


def fig_mix_tipologias(mix_df) -> None:
    pivot = mix_df.pivot_table(
        index="ANO_CONVO_INT",
        columns="NME_TIPO_MEDICION_PD",
        values="pct",
        fill_value=0,
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    pivot.plot(kind="bar", stacked=True, ax=ax, colormap="tab20")
    ax.set_ylabel("% de productos por tipo de medición")
    ax.set_xlabel("Convocatoria")
    ax.set_title("Composición de la producción por tipo de medición MinCiencias")
    ax.legend(title="Tipo medición", bbox_to_anchor=(1.02, 1),
              loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig05_mix_tipologias.png",
                dpi=150, bbox_inches="tight")
    plt.close()


def fig_reconocidos_sin_produccion(sin_prod_df) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    x = sin_prod_df["ANO_CONVO_INT"].astype(str)
    ax.bar(x, sin_prod_df["n_con_produccion"], label="Reconocidos con producción",
           color="seagreen")
    ax.bar(x, sin_prod_df["n_sin_produccion"], bottom=sin_prod_df["n_con_produccion"],
           label="Reconocidos sin producción", color="firebrick")
    for i, pct in enumerate(sin_prod_df["pct_sin_produccion"]):
        total = sin_prod_df.iloc[i]["n_reconocidos"]
        ax.text(i, total + 200, f"{pct:.1f}% sin", ha="center", fontsize=9)
    ax.set_ylabel("# investigadores reconocidos")
    ax.set_xlabel("Convocatoria")
    ax.set_title("¿Cuántos investigadores reconocidos no tienen producción registrada?")
    ax.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig06_reconocidos_sin_produccion.png", dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("[1/8] Cargando datasets...")
    inv = transformar(cargar_consolidado())
    prod = normalizar_produccion(cargar_produccion())
    print(f"      investigadores: {inv.shape}")
    print(f"      produccion:     {prod.shape}")

    print("\n[2/8] Cobertura de reconocimiento (autores únicos)...")
    cov_unicos = cobertura_autores_unicos(prod, inv)
    for k, v in cov_unicos.items():
        print(f"      {k}: {v:,}" if isinstance(v, int) else f"      {k}: {v}")

    print("\n[3/8] Cobertura de reconocimiento por convocatoria...")
    cov = cobertura_reconocidos(prod, inv)
    print(cov.to_string(index=False))

    print("\n[4/8] Productividad por categoría de reconocimiento...")
    prod_cat = productividad_por_categoria(prod, inv)
    print(prod_cat.head(20).to_string(index=False))

    print("\n[5/8] Brecha de productividad por género × área OCDE...")
    brecha = brecha_productividad_genero(prod, inv)
    print(brecha.to_string(index=False))

    print("\n[6/8] Concentración territorial...")
    terr = productividad_territorial(prod, inv)
    print(terr.head(15).to_string(index=False))

    print("\n[7/8] Mix de tipologías y reconocidos sin producción...")
    mix = mix_tipologias(prod)
    sin_prod = reconocidos_sin_produccion(prod, inv)
    tip_cat = tipologias_por_categoria(prod, inv)
    print("\n  Reconocidos sin producción por convocatoria:")
    print(sin_prod.to_string(index=False))

    print("\n[8/8] Generando figuras y exportando evidencias...")
    fig_cobertura_reconocidos(cov)
    fig_productividad_por_categoria(prod_cat)
    fig_brecha_genero(brecha)
    fig_concentracion_territorial(terr)
    fig_mix_tipologias(mix)
    fig_reconocidos_sin_produccion(sin_prod)

    cov.to_csv(EVIDENCIAS / "produccion_cobertura_por_convocatoria.csv", index=False)
    prod_cat.to_csv(EVIDENCIAS / "produccion_productividad_por_categoria.csv", index=False)
    brecha.to_csv(EVIDENCIAS / "produccion_brecha_genero.csv", index=False)
    terr.to_csv(EVIDENCIAS / "produccion_concentracion_territorial.csv", index=False)
    mix.to_csv(EVIDENCIAS / "produccion_mix_tipologias.csv", index=False)
    tip_cat.to_csv(EVIDENCIAS / "produccion_tipologias_por_categoria.csv", index=False)
    sin_prod.to_csv(EVIDENCIAS / "produccion_reconocidos_sin_produccion.csv", index=False)

    # Resumen de cobertura de autores únicos
    import json
    with open(EVIDENCIAS / "produccion_resumen_cobertura.json", "w", encoding="utf-8") as f:
        json.dump(cov_unicos, f, ensure_ascii=False, indent=2)

    print(f"\nFiguras : {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs    : {EVIDENCIAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
