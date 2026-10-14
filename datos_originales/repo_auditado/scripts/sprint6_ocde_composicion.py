"""
Sprint 6 — Composición de la producción por gran área OCDE.

Cruza el dataset de producción (33dq-ab5a) con el padrón de investigadores
(bqtm-4y2h) para responder dos preguntas que pidió el director:

  1. ¿Qué rama del conocimiento produce más en Colombia?
  2. ¿Cómo se compone esa producción (formación, apropiación, nuevo
     conocimiento) por gran área OCDE?

Uso:
    python scripts/sprint6_ocde_composicion.py

Salidas:
    artifacts/sprint6_ocde/fig_volumen_por_area.png
    artifacts/sprint6_ocde/fig_composicion_tipo_por_area.png
    artifacts/sprint6_ocde/fig_productividad_por_area.png
    evidencias/ocde_composicion_por_area.csv
    evidencias/ocde_volumen_por_area.csv
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from ingesta import cargar_consolidado, cargar_produccion
from Transformacion import transformar
from analisis.produccion import normalizar_produccion

ARTIFACTS = ROOT / "artifacts" / "sprint6_ocde"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")


# Paleta consistente con la presentación
PALETA_TIPO = {
    "Nuevo conocimiento Top":                                "#1f6feb",
    "Nuevo conocimiento Tipo A":                             "#388bfd",
    "Nuevo conocimiento Tipo B":                             "#79b8ff",
    "Formación de recursos humano Tipo A":                   "#f9a825",
    "Formación de recursos humano Tipo B":                   "#fbc02d",
    "Apropiación social del conocimiento":                   "#2e7d32",
    "Apropiación social del conocimiento y divulgación pública de la ciencia": "#4caf50",
    "No categorizado":                                       "#9e9e9e",
}


def cruzar(prod: pd.DataFrame, inv: pd.DataFrame) -> pd.DataFrame:
    """Une cada producto con la gran área OCDE del autor reconocido (cuando aplica)."""
    inv_slim = (inv[["ID_PERSONA_PR", "ID_CONVOCATORIA", "NME_GRAN_AREA_PR"]]
                .rename(columns={"ID_PERSONA_PR": "ID_PERSONA_PD"}))
    df = prod.merge(inv_slim, on=["ID_PERSONA_PD", "ID_CONVOCATORIA"], how="inner")
    # Limpieza mínima: descartar areas no informadas
    df = df[~df["NME_GRAN_AREA_PR"].isin(["NO REGISTRA", "NO REPORTADO"])]
    return df


def fig_volumen_por_area(volumen: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    paleta = sns.color_palette("crest", n_colors=len(volumen))
    ax.barh(volumen["gran_area"], volumen["n_productos"], color=paleta)
    for i, row in volumen.reset_index(drop=True).iterrows():
        ax.text(row["n_productos"], i, f"  {row['n_productos']:,}".replace(",", "."),
                va="center", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Productos contabilizados (2013-2021)")
    ax.set_title("¿Qué rama del conocimiento produce más en Colombia?")
    plt.tight_layout()
    fig.savefig(ARTIFACTS / "fig_volumen_por_area.png", dpi=150, bbox_inches="tight")
    plt.close()


def fig_composicion_por_area(comp: pd.DataFrame) -> None:
    pivot = comp.pivot_table(index="NME_GRAN_AREA_PR",
                              columns="NME_TIPO_MEDICION_PD",
                              values="pct",
                              fill_value=0)
    # Ordenar columnas por volumen global
    orden_cols = comp.groupby("NME_TIPO_MEDICION_PD")["n_productos"].sum().sort_values(ascending=False).index
    pivot = pivot[orden_cols]
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(12, 6))
    colores = [PALETA_TIPO.get(c, "#888") for c in pivot.columns]
    pivot.plot(kind="barh", stacked=True, ax=ax, color=colores, width=0.78)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("% de productos del área")
    ax.set_ylabel("")
    ax.set_title("Composición de la producción por tipo de medición y gran área OCDE")
    ax.legend(title="Tipo de medición MinCiencias",
              bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    fig.savefig(ARTIFACTS / "fig_composicion_tipo_por_area.png",
                dpi=150, bbox_inches="tight")
    plt.close()


def fig_productividad_por_area(prod_area: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    sub = prod_area.sort_values("productos_por_investigador", ascending=False)
    paleta = sns.color_palette("flare", n_colors=len(sub))
    ax.barh(sub["gran_area"], sub["productos_por_investigador"], color=paleta)
    for i, row in sub.reset_index(drop=True).iterrows():
        ax.text(row["productos_por_investigador"], i,
                f"  {row['productos_por_investigador']:.1f}",
                va="center", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Productos promedio por investigador reconocido")
    ax.set_title("Productividad media por gran área OCDE")
    plt.tight_layout()
    fig.savefig(ARTIFACTS / "fig_productividad_por_area.png",
                dpi=150, bbox_inches="tight")
    plt.close()


def main() -> None:
    print("[1/5] Cargando datasets...")
    inv = transformar(cargar_consolidado())
    prod = normalizar_produccion(cargar_produccion())
    print(f"      investigadores: {inv.shape}, produccion: {prod.shape}")

    print("\n[2/5] Cruzando produccion con gran area OCDE...")
    df = cruzar(prod, inv)
    print(f"      productos con area asignada: {len(df):,}")

    print("\n[3/5] Volumen y productividad por area...")
    volumen = (df.groupby("NME_GRAN_AREA_PR")
                 .size()
                 .reset_index(name="n_productos")
                 .rename(columns={"NME_GRAN_AREA_PR": "gran_area"})
                 .sort_values("n_productos", ascending=False))

    # Investigadores únicos por área (denominador limpio)
    inv_por_area = (inv[inv["NME_GRAN_AREA_PR"].isin(volumen["gran_area"])]
                    .groupby("NME_GRAN_AREA_PR")["ID_PERSONA_PR"]
                    .nunique()
                    .reset_index(name="n_investigadores")
                    .rename(columns={"NME_GRAN_AREA_PR": "gran_area"}))

    prod_area = volumen.merge(inv_por_area, on="gran_area")
    prod_area["productos_por_investigador"] = (
        prod_area["n_productos"] / prod_area["n_investigadores"]
    ).round(2)

    print(volumen.to_string(index=False))
    print()
    print(prod_area[["gran_area", "n_productos", "n_investigadores",
                      "productos_por_investigador"]].to_string(index=False))

    print("\n[4/5] Composicion por tipo de medicion...")
    comp = (df.groupby(["NME_GRAN_AREA_PR", "NME_TIPO_MEDICION_PD"])
              .size()
              .reset_index(name="n_productos"))
    total_por_area = comp.groupby("NME_GRAN_AREA_PR")["n_productos"].transform("sum")
    comp["pct"] = (comp["n_productos"] / total_por_area * 100).round(2)
    print(comp.head(20).to_string(index=False))

    print("\n[5/5] Exportando figuras y CSVs...")
    fig_volumen_por_area(volumen)
    fig_composicion_por_area(comp)
    fig_productividad_por_area(prod_area)

    volumen.to_csv(EVIDENCIAS / "ocde_volumen_por_area.csv", index=False)
    prod_area.to_csv(EVIDENCIAS / "ocde_productividad_por_area.csv", index=False)
    comp.to_csv(EVIDENCIAS / "ocde_composicion_por_area.csv", index=False)

    print(f"\nFiguras: {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs:    {EVIDENCIAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
