"""
Sprint 6 — Análisis geográfico institucional.

Cruza el departamento de residencia del investigador con el departamento de
la sede de su institución (vía la tabla maestra). Responde la pregunta del
director:

    "Para mí lo más importante es el análisis geográfico. No solo se concentra
    en el departamento, sino en el departamento de la institución. Los de
    Vichada probablemente estuvieron en instituciones del Meta o Bogotá."

Salidas:
    artifacts/sprint6_geografia/fig_heatmap_residencia_institucion.png
    artifacts/sprint6_geografia/fig_pct_local_por_dpto.png
    artifacts/sprint6_geografia/fig_top_destinos_pequenos.png
    evidencias/geografia_flujo_completo.csv
    evidencias/geografia_resumen_por_dpto_residencia.csv
    evidencias/geografia_top_flujos.csv

Uso:
    python scripts/sprint6_geografia_institucional.py
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

from ingesta import cargar_consolidado
from Transformacion import transformar

ARTIFACTS = ROOT / "artifacts" / "sprint6_geografia"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")


# Normalización de nombres de departamento — el padrón usa mayúsculas con coma
# (ej. "BOGOTÁ, D. C."), la tabla maestra usa "Bogotá D.C.". Unificamos a un
# formato canónico interno en mayúsculas sin acentos especiales.
NORM_DPTO = {
    "BOGOTÁ, D. C.": "BOGOTA",
    "BOGOTÁ D.C.":   "BOGOTA",
    "BOGOTA D.C.":   "BOGOTA",
    "BOGOTA":        "BOGOTA",
    "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA": "SAN ANDRES",
    "SAN ANDRES":    "SAN ANDRES",
    "EXTRANJERO":    "EXTRANJERO",
    "EXTERIOR":      "EXTERIOR",
    "NO IDENTIFICADO": "NO IDENTIFICADO",
}

import unicodedata
def normalizar_dpto(s):
    if pd.isna(s) or s in ("SIN_FILIA", "NO_MAPEADA"):
        return s
    s = str(s).strip().upper()
    if s in NORM_DPTO:
        return NORM_DPTO[s]
    # Quitar acentos y normalizar a uppercase
    sin_acentos = "".join(c for c in unicodedata.normalize("NFD", s)
                          if unicodedata.category(c) != "Mn")
    return sin_acentos.strip()


def asignar_institucion_principal(df: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """
    Asigna a cada investigador el departamento de su institución principal.
    Cuando inst_filia tiene varias instituciones (separadas por |) usa la primera.
    """
    df = df.copy()
    primera = (df["INST_FILIA"]
               .fillna("")
               .astype(str)
               .str.split("|")
               .str[0]
               .str.strip()
               .str.upper())
    df["INST_PRIMERA"] = primera.replace({"": np.nan, "NAN": np.nan, "NO REPORTADO": np.nan})

    map_dict = (mapping
                .dropna(subset=["nombre_canonico"])
                .set_index("inst_filia_str")[["nombre_canonico", "sigla", "departamento_sede", "naturaleza"]]
                .to_dict("index"))

    def lookup(s):
        if pd.isna(s):
            return ("SIN_FILIA", None, "SIN_FILIA", None)
        m = map_dict.get(s)
        if m is None:
            return ("NO_MAPEADA", None, "NO_MAPEADA", None)
        return (m["nombre_canonico"], m["sigla"], m["departamento_sede"], m["naturaleza"])

    enriquecido = df["INST_PRIMERA"].map(lookup)
    df["INST_CANONICA"]   = [x[0] for x in enriquecido]
    df["INST_SIGLA"]      = [x[1] for x in enriquecido]
    df["DPTO_INSTITUCION"] = [normalizar_dpto(x[2]) for x in enriquecido]
    df["INST_NATURALEZA"] = [x[3] for x in enriquecido]
    df["DPTO_RESIDENCIA"] = df["NME_DEPARTAMENTO_RES_PR"].map(normalizar_dpto)
    return df


def tabla_flujos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cuenta investigadores únicos por par (residencia, institución).
    Usa los strings normalizados para que la comparación residencia == institución
    sea consistente.
    """
    sub = df[~df["DPTO_INSTITUCION"].isin(["NO_MAPEADA", "SIN_FILIA"])]
    sub = sub[sub["DPTO_RESIDENCIA"].notna()]
    flujo = (sub.groupby(["DPTO_RESIDENCIA", "DPTO_INSTITUCION"])
                 ["ID_PERSONA_PR"]
                 .nunique()
                 .reset_index(name="n_investigadores"))
    flujo = flujo.sort_values("n_investigadores", ascending=False)
    return flujo


def resumen_por_residencia(flujo: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada departamento de residencia: cuántos investigadores trabajan en su
    propio departamento vs. afuera. Identifica el destino más frecuente cuando
    salen.
    """
    rows = []
    for dpto, grupo in flujo.groupby("DPTO_RESIDENCIA"):
        total = grupo["n_investigadores"].sum()
        local = grupo.loc[grupo["DPTO_INSTITUCION"] == dpto,
                          "n_investigadores"].sum()
        afuera = total - local
        # Destino más frecuente fuera del propio departamento
        fuera = grupo[grupo["DPTO_INSTITUCION"] != dpto]
        if len(fuera):
            top = fuera.iloc[0]
            top_destino = top["DPTO_INSTITUCION"]
            top_n = int(top["n_investigadores"])
        else:
            top_destino, top_n = pd.NA, 0
        rows.append({
            "dpto_residencia": dpto,
            "total_investigadores": int(total),
            "trabajan_en_su_dpto": int(local),
            "trabajan_fuera": int(afuera),
            "pct_local": round(local / total * 100, 1) if total else 0,
            "destino_principal_fuera": top_destino,
            "n_destino_principal": top_n,
        })
    return pd.DataFrame(rows).sort_values("total_investigadores", ascending=False)


def fig_heatmap_top(flujo: pd.DataFrame, top_res: int = 15, top_inst: int = 12) -> None:
    """Heatmap de flujos: top departamentos de residencia × top de institución."""
    top_residencias = (flujo.groupby("DPTO_RESIDENCIA")["n_investigadores"]
                            .sum().nlargest(top_res).index)
    top_dpto_inst = (flujo.groupby("DPTO_INSTITUCION")["n_investigadores"]
                          .sum().nlargest(top_inst).index)

    sub = flujo[flujo["DPTO_RESIDENCIA"].isin(top_residencias) &
                flujo["DPTO_INSTITUCION"].isin(top_dpto_inst)]
    pivot = sub.pivot_table(index="DPTO_RESIDENCIA",
                              columns="DPTO_INSTITUCION",
                              values="n_investigadores",
                              fill_value=0).astype(int)
    pivot = pivot.loc[top_residencias, top_dpto_inst]

    fig, ax = plt.subplots(figsize=(13, 8))
    sns.heatmap(pivot, annot=True, fmt="d", cmap="YlGnBu",
                cbar_kws={"label": "Investigadores"},
                linewidths=0.4, linecolor="white", ax=ax)
    ax.set_xlabel("Departamento de la institución")
    ax.set_ylabel("Departamento de residencia")
    ax.set_title("Flujos investigador → institución (top 15 × top 12)")
    plt.tight_layout()
    fig.savefig(ARTIFACTS / "fig_heatmap_residencia_institucion.png",
                dpi=150, bbox_inches="tight")
    plt.close()


def fig_pct_local(resumen: pd.DataFrame) -> None:
    """% de investigadores que trabajan en su mismo departamento."""
    top = resumen.head(25).copy()
    top = top.sort_values("pct_local")
    paleta = sns.color_palette("RdYlGn", n_colors=len(top))

    fig, ax = plt.subplots(figsize=(11, 8))
    bars = ax.barh(top["dpto_residencia"], top["pct_local"], color=paleta)
    for bar, val, total in zip(bars, top["pct_local"], top["total_investigadores"]):
        ax.text(val + 0.6, bar.get_y() + bar.get_height()/2,
                f"{val:.0f}%  (n={int(total):,})",
                va="center", fontsize=9, color="#333")
    ax.set_xlim(0, 105)
    ax.set_xlabel("% de investigadores que trabajan en su propio departamento")
    ax.set_ylabel("")
    ax.set_title("¿Dónde reside el investigador vs. dónde está su institución?\n"
                 "Top 25 departamentos por número de investigadores")
    plt.tight_layout()
    fig.savefig(ARTIFACTS / "fig_pct_local_por_dpto.png",
                dpi=150, bbox_inches="tight")
    plt.close()


def fig_destinos_pequenos(flujo: pd.DataFrame, resumen: pd.DataFrame) -> None:
    """
    Foco en los departamentos más pequeños: ¿hacia dónde se va su gente?
    """
    pequenos = ["VICHADA", "VAUPES", "GUAINIA", "AMAZONAS", "GUAVIARE",
                "PUTUMAYO", "CHOCO", "ARAUCA", "CASANARE", "LA GUAJIRA",
                "SUCRE", "CAQUETA"]
    sub = flujo[flujo["DPTO_RESIDENCIA"].isin(pequenos)]
    pivot = (sub.pivot_table(index="DPTO_RESIDENCIA",
                              columns="DPTO_INSTITUCION",
                              values="n_investigadores",
                              fill_value=0))
    if pivot.empty:
        print("    (sin datos para departamentos pequenos)")
        return

    pivot["_total"] = pivot.sum(axis=1)
    top_dest = (pivot.drop(columns="_total").sum(axis=0).sort_values(ascending=False).head(8).index)
    pivot_pct = pivot[top_dest].div(pivot["_total"], axis=0) * 100
    pivot_pct = pivot_pct.loc[[d for d in pequenos if d in pivot_pct.index]]

    fig, ax = plt.subplots(figsize=(12, 6))
    pivot_pct.plot(kind="barh", stacked=True, ax=ax,
                    colormap="tab20", width=0.78)
    ax.invert_yaxis()
    ax.set_xlabel("% de investigadores del departamento")
    ax.set_xlim(0, 100)
    ax.set_title("Departamentos con menos investigación: ¿hacia dónde se afilian?")
    ax.legend(title="Departamento de institución",
              bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    fig.savefig(ARTIFACTS / "fig_top_destinos_pequenos.png",
                dpi=150, bbox_inches="tight")
    plt.close()


def main() -> None:
    print("[1/5] Cargando datos y mapping...")
    df = transformar(cargar_consolidado())
    mapping = pd.read_csv(EVIDENCIAS / "mapping_inst_filia_to_ies.csv")
    print(f"      investigadores: {df.shape}, mapping: {len(mapping):,} entradas")

    print("\n[2/5] Asignando departamento de la institución principal...")
    df = asignar_institucion_principal(df, mapping)
    print(df["DPTO_INSTITUCION"].value_counts(normalize=True).head(8).round(3).mul(100).astype(str) + " %")

    n_mapeado = (~df["DPTO_INSTITUCION"].isin(["NO_MAPEADA", "SIN_FILIA"])).sum()
    print(f"      con dpto de institucion asignado: {n_mapeado:,} de {len(df):,} "
          f"({n_mapeado/len(df)*100:.1f}%)")

    print("\n[3/5] Construyendo tabla de flujos residencia → institución...")
    flujo = tabla_flujos(df)
    print(f"      pares unicos: {len(flujo):,}")

    print("\n[4/5] Resumen por departamento de residencia...")
    resumen = resumen_por_residencia(flujo)
    print(resumen.head(15).to_string(index=False))

    # Top flujos transversales (residencia ≠ institucion)
    transversales = flujo[flujo["DPTO_RESIDENCIA"] != flujo["DPTO_INSTITUCION"]]
    top_flujos = transversales.head(20)
    print("\n--- Top 20 flujos transversales (residencia → institución) ---")
    print(top_flujos.to_string(index=False))

    print("\n[5/5] Generando figuras y exportando evidencias...")
    fig_heatmap_top(flujo)
    fig_pct_local(resumen)
    fig_destinos_pequenos(flujo, resumen)

    flujo.to_csv(EVIDENCIAS / "geografia_flujo_completo.csv", index=False)
    resumen.to_csv(EVIDENCIAS / "geografia_resumen_por_dpto_residencia.csv", index=False)
    transversales.to_csv(EVIDENCIAS / "geografia_top_flujos.csv", index=False)

    print(f"\nFiguras: {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs   : evidencias/geografia_*.csv")

    # Highlights
    print("\n--- Highlights ---")
    for foco in ("VICHADA", "VAUPES", "GUAINIA", "AMAZONAS", "CHOCO",
                 "BOGOTA", "ANTIOQUIA"):
        sub = resumen[resumen["dpto_residencia"] == foco]
        if sub.empty:
            continue
        v = sub.iloc[0]
        print(f"{foco}: {int(v['total_investigadores']):,} investigadores, "
              f"{v['pct_local']:.0f}% trabajan en su dpto, "
              f"destino externo principal: {v['destino_principal_fuera']} "
              f"({int(v['n_destino_principal'])})")


if __name__ == "__main__":
    main()
