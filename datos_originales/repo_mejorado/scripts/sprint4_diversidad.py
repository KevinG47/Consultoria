"""
Sprint 4 — Analisis de variables de conflicto, etnia y discapacidad (Issue #20).

Comparacion con proporciones poblacionales DANE 2018 / RUV 2021.

Hallazgo critico: estas variables solo se capturan desde 2021 (convocatoria 894).
Las 5 convocatorias previas (2013-2019) tienen 100% NO REGISTRA / NO DISPONIBLE.

Uso:
    python scripts/sprint4_diversidad.py

Salidas:
    artifacts/sprint4_diversidad/fig01_cobertura_temporal.png
    artifacts/sprint4_diversidad/fig02_comparacion_dane.png
    artifacts/sprint4_diversidad/fig03_categorias_por_minoria.png
    evidencias/diversidad_cobertura_por_convocatoria.csv
    evidencias/diversidad_distribucion_etnia_2021.csv
    evidencias/diversidad_distribucion_discapacidad_2021.csv
    evidencias/diversidad_comparacion_dane.csv
    evidencias/diversidad_interseccional_genero_etnia.csv
    evidencias/diversidad_categorias_por_etnia.csv
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
from analisis.diversidad import (
    cobertura_por_convocatoria,
    distribucion_categoria,
    comparar_dane,
    interseccional_genero_etnia,
    categoria_por_minoria,
)

ARTIFACTS = ROOT / "artifacts" / "sprint4_diversidad"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")


def fig_cobertura_temporal(cob_df) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    anios = cob_df["ANO_CONVO_INT"].astype(str)
    cols = [
        ("ID_VICTIMA_CONFLICTO_pct_cobertura", "Victima conflicto"),
        ("TXT_GRUPO_ETNICO_pct_cobertura", "Grupo etnico"),
        ("TXT_POBLACION_DISCA_pct_cobertura", "Discapacidad"),
    ]
    for col, label in cols:
        ax.plot(anios, cob_df[col], marker="o", linewidth=2, label=label)
    ax.set_ylim(-5, 105)
    ax.set_ylabel("% de cobertura (registros con dato real)")
    ax.set_xlabel("Convocatoria")
    ax.set_title("Cobertura de variables de diversidad por convocatoria")
    ax.axhline(50, color="gray", linestyle="--", alpha=0.5)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig01_cobertura_temporal.png", dpi=150)
    plt.close()


def fig_comparacion_dane(comp_df) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    x = range(len(comp_df))
    width = 0.35
    ax.bar([i - width / 2 for i in x], comp_df["pct_minciencias"], width,
           label="Investigadores 2021", color="steelblue")
    ax.bar([i + width / 2 for i in x], comp_df["pct_dane_2018"], width,
           label="Poblacion (DANE/RUV)", color="tomato")

    for i, (m, d) in enumerate(zip(comp_df["pct_minciencias"], comp_df["pct_dane_2018"])):
        ax.text(i - width / 2, m + 0.2, f"{m:.1f}%", ha="center", fontsize=8)
        ax.text(i + width / 2, d + 0.2, f"{d:.1f}%", ha="center", fontsize=8)

    ax.set_xticks(list(x))
    ax.set_xticklabels(
        [g.replace("/", "/\n") for g in comp_df["grupo"]],
        rotation=20, ha="right", fontsize=9,
    )
    ax.set_ylabel("% de la poblacion respectiva")
    ax.set_title("Subrepresentacion de minorias: investigadores 2021 vs poblacion colombiana")
    ax.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig02_comparacion_dane.png", dpi=150, bbox_inches="tight")
    plt.close()


def fig_categorias_por_minoria(df_2021) -> None:
    """Distribucion porcentual de categorias academicas para minorias etnicas."""
    cat_etnia = categoria_por_minoria(df_2021, "TXT_GRUPO_ETNICO")
    # Solo grupos minoritarios (excluir NINGUN GRUPO ETNICO)
    cat_etnia = cat_etnia[~cat_etnia["TXT_GRUPO_ETNICO"].str.contains("NING", case=False, na=False)]

    cats = ["INVESTIGADOR JUNIOR", "INVESTIGADOR ASOCIADO", "INVESTIGADOR SÉNIOR", "INVESTIGADOR EMÉRITO"]
    cats_disponibles = [c for c in cats if c in cat_etnia.columns]
    pct = cat_etnia.set_index("TXT_GRUPO_ETNICO")[cats_disponibles].div(
        cat_etnia.set_index("TXT_GRUPO_ETNICO")["total"], axis=0
    ) * 100

    fig, ax = plt.subplots(figsize=(11, 5))
    pct.plot(kind="barh", stacked=True, ax=ax, colormap="viridis")
    ax.set_xlabel("% de investigadores en cada categoria")
    ax.set_title("Categoria academica por grupo etnico (convocatoria 2021)")
    ax.legend(title="Categoria", bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "fig03_categorias_por_minoria.png", dpi=150, bbox_inches="tight")
    plt.close()


def main() -> None:
    print("[1/5] Cargando datos...")
    df = transformar(cargar_consolidado())

    print("[2/5] Cobertura temporal de variables de diversidad...")
    cob = cobertura_por_convocatoria(df)
    print(cob[["ANO_CONVO_INT", "n_total",
               "ID_VICTIMA_CONFLICTO_pct_cobertura",
               "TXT_GRUPO_ETNICO_pct_cobertura",
               "TXT_POBLACION_DISCA_pct_cobertura"]].to_string(index=False))

    df_2021 = df[df["ANO_CONVO_INT"] == 2021].copy()
    print(f"\n      Convocatoria 2021: {len(df_2021):,} registros")

    print("[3/5] Distribuciones (2021, excluyendo NO DISPONIBLE)...")
    dist_etnia = distribucion_categoria(df_2021, "TXT_GRUPO_ETNICO")
    dist_disca = distribucion_categoria(df_2021, "TXT_POBLACION_DISCA")
    dist_vict = distribucion_categoria(df_2021, "ID_VICTIMA_CONFLICTO")
    print("\nEtnia:")
    print(dist_etnia.to_string(index=False))
    print("\nDiscapacidad:")
    print(dist_disca.to_string(index=False))
    print("\nVictimas conflicto:")
    print(dist_vict.to_string(index=False))

    print("\n[4/5] Comparacion con DANE/RUV...")
    comp = comparar_dane(df_2021)
    print(comp.to_string(index=False))

    print("\n[5/5] Generando figuras y exportando evidencias...")
    fig_cobertura_temporal(cob)
    fig_comparacion_dane(comp)
    fig_categorias_por_minoria(df_2021)

    cob.to_csv(EVIDENCIAS / "diversidad_cobertura_por_convocatoria.csv", index=False)
    dist_etnia.to_csv(EVIDENCIAS / "diversidad_distribucion_etnia_2021.csv", index=False)
    dist_disca.to_csv(EVIDENCIAS / "diversidad_distribucion_discapacidad_2021.csv", index=False)
    dist_vict.to_csv(EVIDENCIAS / "diversidad_distribucion_victimas_2021.csv", index=False)
    comp.to_csv(EVIDENCIAS / "diversidad_comparacion_dane.csv", index=False)
    interseccional_genero_etnia(df_2021).to_csv(
        EVIDENCIAS / "diversidad_interseccional_genero_etnia.csv", index=False
    )
    categoria_por_minoria(df_2021, "TXT_GRUPO_ETNICO").to_csv(
        EVIDENCIAS / "diversidad_categorias_por_etnia.csv", index=False
    )

    print(f"\nFiguras : {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs    : {EVIDENCIAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
