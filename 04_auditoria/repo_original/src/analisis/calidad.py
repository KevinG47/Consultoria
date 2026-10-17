"""
analisis/calidad.py

Validación documentada de calidad de los datos del padrón de investigadores
reconocidos. La decisión metodológica adoptada se documenta de forma explícita
para que cualquier auditor pueda reproducirla y discutirla.

Atípicos de edad
----------------
La variable EDAD_ANOS_PR tiene diez registros con valor mayor a 100. El máximo
observado es 956, claramente un error de digitación.

Métodos considerados:
    1. Eliminación de casos (escoja: ``filtrar``).
       Borra los registros con edad > 100 cuando el análisis depende de la edad.
       Justificación: 10 sobre 77.237 (0.013%). El sesgo introducido por
       eliminación es despreciable. Es la opción más conservadora y reproducible.

    2. Imputación por mediana del grupo (escoja: ``imputar_mediana``).
       Reemplaza el valor por la mediana de edad dentro del grupo definido por
       (gran área OCDE, categoría, género). Se ofrece como alternativa pero no
       se aplica por defecto: los 10 casos no afectan la mediana y la
       trazabilidad del valor original se pierde.

Decisión adoptada: **eliminación** para análisis que dependen de edad. El
filtro se aplica de manera transparente y se reporta el conteo antes/después.

Otros casos atípicos detectados pero no tratados aquí (se mantienen):
    - Departamento "NO DISPONIBLE": 5.2% del padrón. Mantener (subgrupo sin
      geolocalización; tratarlo como categoría aparte en mapas).
    - Género "NO REPORTADO": 2.7%. Mantener (excluido sólo del análisis de
      brecha por género).
    - Convocatoria 833 con ANO_CONVO_INT = 2019: NO es un error de digitación
      sino la fecha de publicación de resultados. Se documenta en el catalogo
      y se reporta como caveat.
"""

from __future__ import annotations
import pandas as pd

UMBRAL_EDAD_MAX = 100


def detectar_atipicos_edad(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve los registros con edad > UMBRAL_EDAD_MAX para inspección.

    Las columnas devueltas son las mínimas necesarias para identificar y
    reportar el caso. La función no modifica el dataframe original.
    """
    cols = [c for c in (
        "ID_PERSONA_PR", "ID_CONVOCATORIA", "ANO_CONVO_INT", "EDAD_ANOS_PR",
        "NME_CLASIFICACION_PR", "NME_GENERO_PR", "NME_DEPARTAMENTO_RES_PR",
    ) if c in df.columns]
    fuera = df.loc[df["EDAD_ANOS_PR"] > UMBRAL_EDAD_MAX, cols].copy()
    return fuera.sort_values("EDAD_ANOS_PR", ascending=False).reset_index(drop=True)


def resumen_tratamiento(df: pd.DataFrame) -> dict:
    """Reporte tabular del antes/después aplicando el filtro."""
    n_total = len(df)
    n_atipicos = int((df["EDAD_ANOS_PR"] > UMBRAL_EDAD_MAX).sum())
    n_validos = n_total - n_atipicos
    return {
        "n_total": n_total,
        "n_atipicos_edad": n_atipicos,
        "n_validos_edad": n_validos,
        "pct_atipicos": round(n_atipicos / n_total * 100, 4),
        "umbral_aplicado": UMBRAL_EDAD_MAX,
        "metodo": "eliminacion",
        "justificacion": (
            f"{n_atipicos} casos sobre {n_total} ({n_atipicos/n_total*100:.3f}%). "
            "Sesgo despreciable. Eliminación preferida sobre imputación por "
            "trazabilidad y reproducibilidad."
        ),
    }


def filtrar(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica el método elegido (eliminación) y devuelve dataframe limpio."""
    return df[df["EDAD_ANOS_PR"] <= UMBRAL_EDAD_MAX].copy()


def imputar_mediana(
    df: pd.DataFrame,
    grupos: tuple = ("NME_GRAN_AREA_PR", "NME_CLASIFICACION_PR", "NME_GENERO_PR"),
) -> pd.DataFrame:
    """
    Alternativa: reemplaza valores atípicos con la mediana del grupo.
    No es la decisión por defecto. Se ofrece para reproducir comparaciones.
    """
    out = df.copy()
    atipicos = out["EDAD_ANOS_PR"] > UMBRAL_EDAD_MAX
    if not atipicos.any():
        return out
    medianas = (out.loc[~atipicos]
                  .groupby(list(grupos))["EDAD_ANOS_PR"]
                  .median())
    def _imputar(row):
        if row["EDAD_ANOS_PR"] <= UMBRAL_EDAD_MAX:
            return row["EDAD_ANOS_PR"]
        clave = tuple(row[g] for g in grupos)
        return medianas.get(clave, out.loc[~atipicos, "EDAD_ANOS_PR"].median())
    out["EDAD_ANOS_PR"] = out.apply(_imputar, axis=1)
    return out
