"""
Sprint 6 — Validación documentada de calidad de los datos.

Produce evidencia explícita del tratamiento de valores atípicos para que la
decisión metodológica quede auditable.

Salidas:
    evidencias/calidad_atipicos_edad.csv    — los 10 casos atípicos identificados
    evidencias/calidad_resumen.json         — antes/después + método aplicado
    evidencias/calidad_comparacion.csv      — métrica antes / con filtro / con imputación
    artifacts/sprint6_calidad/fig_edad_antes_despues.png

Uso:
    python scripts/sprint6_validacion_calidad.py
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from ingesta import cargar_consolidado
from Transformacion import transformar
from analisis.calidad import (
    detectar_atipicos_edad,
    resumen_tratamiento,
    filtrar,
    imputar_mediana,
    UMBRAL_EDAD_MAX,
)

ARTIFACTS = ROOT / "artifacts" / "sprint6_calidad"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main() -> None:
    print("[1/4] Cargando y transformando datos...")
    df = transformar(cargar_consolidado())

    print("\n[2/4] Detectando atípicos de edad...")
    atipicos = detectar_atipicos_edad(df)
    print(atipicos.to_string(index=False))

    print("\n[3/4] Comparando métodos de tratamiento...")
    resumen = resumen_tratamiento(df)
    for k, v in resumen.items():
        print(f"      {k}: {v}")

    # Comparación de estadísticos antes / con filtro / con imputación
    df_filtrado = filtrar(df)
    df_imputado = imputar_mediana(df)

    edad_stats = pd.DataFrame({
        "metodo": ["original", "eliminacion (>100)", "imputacion mediana por grupo"],
        "n_registros": [len(df), len(df_filtrado), len(df_imputado)],
        "media": [
            round(df["EDAD_ANOS_PR"].mean(), 2),
            round(df_filtrado["EDAD_ANOS_PR"].mean(), 2),
            round(df_imputado["EDAD_ANOS_PR"].mean(), 2),
        ],
        "mediana": [
            df["EDAD_ANOS_PR"].median(),
            df_filtrado["EDAD_ANOS_PR"].median(),
            df_imputado["EDAD_ANOS_PR"].median(),
        ],
        "desv_estandar": [
            round(df["EDAD_ANOS_PR"].std(), 2),
            round(df_filtrado["EDAD_ANOS_PR"].std(), 2),
            round(df_imputado["EDAD_ANOS_PR"].std(), 2),
        ],
        "max": [
            df["EDAD_ANOS_PR"].max(),
            df_filtrado["EDAD_ANOS_PR"].max(),
            df_imputado["EDAD_ANOS_PR"].max(),
        ],
    })
    print()
    print(edad_stats.to_string(index=False))

    print("\n[4/4] Figuras y exportación...")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    sns.histplot(df["EDAD_ANOS_PR"].dropna(), bins=80, ax=axes[0],
                 color="#cf625c", edgecolor="white", linewidth=0.4)
    axes[0].set_title(f"Antes del tratamiento (máximo: {int(df['EDAD_ANOS_PR'].max())} años)")
    axes[0].set_xlabel("Edad reportada")
    axes[0].axvline(UMBRAL_EDAD_MAX, color="black", linestyle="--",
                    linewidth=1, label=f"Umbral = {UMBRAL_EDAD_MAX}")
    axes[0].legend(loc="upper right", fontsize=9)

    sns.histplot(df_filtrado["EDAD_ANOS_PR"].dropna(), bins=80, ax=axes[1],
                 color="#3a7ca5", edgecolor="white", linewidth=0.4)
    axes[1].set_title(f"Después del filtro (n descartados: {len(df) - len(df_filtrado)})")
    axes[1].set_xlabel("Edad reportada")

    plt.suptitle("Distribución de edad antes y después del tratamiento de atípicos",
                 fontsize=12, y=1.02)
    plt.tight_layout()
    fig.savefig(ARTIFACTS / "fig_edad_antes_despues.png",
                dpi=150, bbox_inches="tight")
    plt.close()

    atipicos.to_csv(EVIDENCIAS / "calidad_atipicos_edad.csv", index=False)
    edad_stats.to_csv(EVIDENCIAS / "calidad_comparacion.csv", index=False)
    with open(EVIDENCIAS / "calidad_resumen.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    print(f"\nFigura : {ARTIFACTS.relative_to(ROOT)}/fig_edad_antes_despues.png")
    print(f"CSVs   : evidencias/calidad_*.csv, calidad_resumen.json")


if __name__ == "__main__":
    main()
