"""
analisis/genero.py

Análisis de género por área OCDE — Issue #22.

Calcula la representación femenina y la brecha de género en las
6 convocatorias (2013–2021) a los tres niveles de área OCDE.

Requiere que el DataFrame venga transformado (NME_GENERO_PR estandarizado
a MASCULINO / FEMENINO / NO REPORTADO y ANO_CONVO_INT disponible).
"""

import pandas as pd


def pct_femenino_por_area(
    df: pd.DataFrame,
    col_area: str = "NME_GRAN_AREA_PR",
    col_year: str = "ANO_CONVO_INT",
) -> pd.DataFrame:
    """
    Porcentaje de investigadoras femeninas por área y convocatoria.

    Excluye registros con género NO REPORTADO del denominador.
    Retorna columnas: [col_year, col_area, n_total, n_femenino, pct_femenino].
    """
    sub = df[df["NME_GENERO_PR"].isin(["FEMENINO", "MASCULINO"])].copy()
    grp = sub.groupby([col_year, col_area])
    conteos = grp["NME_GENERO_PR"].value_counts().unstack(fill_value=0)

    resultado = pd.DataFrame(index=conteos.index)
    resultado["n_femenino"] = conteos.get("FEMENINO", 0)
    resultado["n_masculino"] = conteos.get("MASCULINO", 0)
    resultado["n_total"] = resultado["n_femenino"] + resultado["n_masculino"]
    resultado["pct_femenino"] = (resultado["n_femenino"] / resultado["n_total"]).round(4)
    return resultado.reset_index()


def tabla_pivot_pct_femenino(
    df: pd.DataFrame,
    col_area: str = "NME_GRAN_AREA_PR",
    col_year: str = "ANO_CONVO_INT",
) -> pd.DataFrame:
    """
    Tabla pivoteada (área × convocatoria) con % femenino.
    Útil para heatmaps y exportación.
    """
    base = pct_femenino_por_area(df, col_area=col_area, col_year=col_year)
    pivot = base.pivot_table(
        index=col_area, columns=col_year, values="pct_femenino"
    )
    pivot["promedio"] = pivot.mean(axis=1).round(4)
    pivot = pivot.sort_values("promedio", ascending=False)
    return pivot


def brecha_genero(
    df: pd.DataFrame,
    col_area: str = "NME_GRAN_AREA_PR",
    col_year: str = "ANO_CONVO_INT",
) -> pd.DataFrame:
    """
    Brecha de género = pct_masculino − pct_femenino por área y convocatoria.
    Valores positivos indican mayor presencia masculina.
    """
    base = pct_femenino_por_area(df, col_area=col_area, col_year=col_year)
    base["pct_masculino"] = 1 - base["pct_femenino"]
    base["brecha"] = (base["pct_masculino"] - base["pct_femenino"]).round(4)
    return base


def evolucion_pct_femenino(
    df: pd.DataFrame,
    col_area: str = "NME_GRAN_AREA_PR",
    col_year: str = "ANO_CONVO_INT",
) -> pd.DataFrame:
    """
    Evolución del % femenino a lo largo de las convocatorias por área.
    Retorna el mismo DataFrame que pct_femenino_por_area, ordenado por año.
    """
    return (
        pct_femenino_por_area(df, col_area=col_area, col_year=col_year)
        .sort_values([col_year, col_area])
        .reset_index(drop=True)
    )
