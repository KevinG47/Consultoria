"""
analisis/territorial.py

Análisis de concentración territorial — Issue #13.

Calcula el índice de Herfindahl-Hirschman (HHI) y métricas de distribución
geográfica de investigadores por departamento y convocatoria.

HHI = Σ sᵢ²  donde sᵢ = fracción de investigadores en la unidad geográfica i.
  HHI → 1  : concentración total (todos en un lugar)
  HHI → 0  : distribución perfectamente uniforme
"""

import pandas as pd
import numpy as np


def hhi(series: pd.Series) -> float:
    """
    Calcula el índice HHI para una serie de conteos o cuotas.

    Acepta tanto conteos absolutos como proporciones; normaliza internamente.
    Retorna un float en [0, 1].
    """
    s = series.dropna()
    if s.sum() == 0:
        return np.nan
    cuotas = s / s.sum()
    return float((cuotas ** 2).sum())


def hhi_por_convocatoria(
    df: pd.DataFrame,
    col_geo: str = "NME_DEPARTAMENTO_RES_PR",
    col_year: str = "ANO_CONVO_INT",
) -> pd.DataFrame:
    """
    Calcula el HHI de concentración geográfica para cada convocatoria.

    Filtra filas con geo o año faltante antes de calcular.
    Retorna DataFrame con columnas: [col_year, 'hhi', 'n_total', 'n_territorios'].
    """
    sub = df[[col_geo, col_year]].dropna()
    sub = sub[sub[col_geo].str.strip().str.upper() != "NO REPORTADO"]

    filas = []
    for anio, g in sub.groupby(col_year):
        conteos = g[col_geo].value_counts()
        filas.append({
            col_year: int(anio),
            "hhi": round(hhi(conteos), 6),
            "n_total": int(conteos.sum()),
            "n_territorios": int(len(conteos)),
        })
    return pd.DataFrame(filas).sort_values(col_year).reset_index(drop=True)


def top_territorios(
    df: pd.DataFrame,
    col_geo: str = "NME_DEPARTAMENTO_RES_PR",
    col_year: str = "ANO_CONVO_INT",
    n: int = 10,
) -> pd.DataFrame:
    """
    Cuenta investigadores por unidad geográfica y convocatoria.

    Retorna un DataFrame con columnas: [col_year, col_geo, 'n', 'pct'].
    Solo incluye los `n` territorios con mayor presencia en el total acumulado.
    """
    sub = df[[col_geo, col_year]].dropna()
    sub = sub[sub[col_geo].str.strip().str.upper() != "NO REPORTADO"]

    conteos = (
        sub.groupby([col_year, col_geo])
        .size()
        .reset_index(name="n")
    )
    totales = conteos.groupby(col_year)["n"].transform("sum")
    conteos["pct"] = (conteos["n"] / totales).round(4)

    top = (
        sub[col_geo]
        .value_counts()
        .head(n)
        .index.tolist()
    )
    return conteos[conteos[col_geo].isin(top)].reset_index(drop=True)


def tabla_cuotas(
    df: pd.DataFrame,
    col_geo: str = "NME_DEPARTAMENTO_RES_PR",
    col_year: str = "ANO_CONVO_INT",
    n: int = 15,
) -> pd.DataFrame:
    """
    Devuelve una tabla pivoteada (departamento × año) con la cuota (%) de
    investigadores. Incluye solo los `n` departamentos más frecuentes.
    """
    top_df = top_territorios(df, col_geo=col_geo, col_year=col_year, n=n)
    pivot = top_df.pivot_table(
        index=col_geo, columns=col_year, values="pct", aggfunc="sum", fill_value=0
    )
    # Ordenar por presencia total acumulada
    pivot["_total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("_total", ascending=False).drop(columns="_total")
    return pivot
