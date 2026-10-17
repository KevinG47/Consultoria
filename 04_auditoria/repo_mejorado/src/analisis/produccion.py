"""
analisis/produccion.py

Análisis de Producción de Grupos de Investigación (Sprint 5).

Cruza el dataset de productos (Socrata 33dq-ab5a) con el de investigadores
reconocidos (bqtm-4y2h) usando id_persona_pd ↔ id_persona_pr.

Preguntas críticas que responde este módulo:
1. ¿Qué % de la producción la firman investigadores reconocidos vs autores no
   reconocidos? (cobertura de reconocimiento)
2. ¿Producen más Senior que Junior? ¿Y los Eméritos antes de desaparecer?
3. ¿La brecha de género en representación se replica o agudiza en producción?
4. ¿La concentración territorial (Bogotá+Antioquia=51%) se replica en outputs?
5. ¿Investigadores reconocidos sin producción registrada? (calidad de captura)
6. ¿Cuáles son las tipologías de producto dominantes por categoría / género?
"""

from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# Helpers de carga / normalización
# ---------------------------------------------------------------------------

def normalizar_produccion(prod: pd.DataFrame) -> pd.DataFrame:
    """Normaliza columnas y tipos para que crucen con investigadores.

    - Garantiza columnas en MAYÚSCULAS.
    - Asegura ID_PERSONA_PD e ID_CONVOCATORIA como int (mismo formato que
      ID_PERSONA_PR e ID_CONVOCATORIA en investigadores).
    - Extrae año de ANO_CONVO si viene como timestamp.
    """
    df = prod.copy()
    df.columns = df.columns.str.upper()

    for c in ("ID_PERSONA_PD", "ID_CONVOCATORIA"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

    if "ANO_CONVO" in df.columns:
        df["ANO_CONVO_INT"] = pd.to_datetime(df["ANO_CONVO"], errors="coerce").dt.year.astype("Int64")

    return df


# ---------------------------------------------------------------------------
# 1. Cobertura: % de productos firmados por investigadores reconocidos
# ---------------------------------------------------------------------------

def cobertura_reconocidos(
    prod: pd.DataFrame,
    inv: pd.DataFrame,
    col_year: str = "ANO_CONVO_INT",
) -> pd.DataFrame:
    """
    Por convocatoria, cuántos productos firman investigadores reconocidos
    (en cualquier convocatoria) vs autores que nunca fueron reconocidos.

    Devuelve [ano, n_productos, n_reconocidos, n_no_reconocidos, pct_reconocidos].
    """
    ids_reconocidos = set(inv["ID_PERSONA_PR"].dropna().astype("Int64"))
    p = prod.copy()
    p["es_reconocido"] = p["ID_PERSONA_PD"].isin(ids_reconocidos)

    out = (
        p.groupby(col_year)
        .agg(
            n_productos=("ID_PERSONA_PD", "size"),
            n_reconocidos=("es_reconocido", "sum"),
        )
        .reset_index()
    )
    out["n_no_reconocidos"] = out["n_productos"] - out["n_reconocidos"]
    out["pct_reconocidos"] = (out["n_reconocidos"] / out["n_productos"] * 100).round(2)
    return out


def cobertura_autores_unicos(prod: pd.DataFrame, inv: pd.DataFrame) -> dict:
    """% de autores únicos en producción que son investigadores reconocidos."""
    ids_reconocidos = set(inv["ID_PERSONA_PR"].dropna().astype("Int64"))
    autores_unicos = set(prod["ID_PERSONA_PD"].dropna().astype("Int64"))
    overlap = autores_unicos & ids_reconocidos
    return {
        "autores_unicos_total": len(autores_unicos),
        "investigadores_reconocidos_total": len(ids_reconocidos),
        "autores_que_son_reconocidos": len(overlap),
        "pct_autores_reconocidos": round(len(overlap) / len(autores_unicos) * 100, 2),
        "reconocidos_que_aparecen_en_produccion": len(overlap),
        "pct_reconocidos_con_produccion": round(len(overlap) / len(ids_reconocidos) * 100, 2),
        "reconocidos_sin_produccion": len(ids_reconocidos - overlap),
    }


# ---------------------------------------------------------------------------
# 2. Productividad por categoría de reconocimiento
# ---------------------------------------------------------------------------

def productividad_por_categoria(
    prod: pd.DataFrame, inv: pd.DataFrame
) -> pd.DataFrame:
    """
    Cuenta productos por (id_persona_pr, id_convocatoria) y los une al dataset
    de investigadores para obtener categoría. Devuelve una fila por
    (categoría, convocatoria) con: n_investigadores, n_productos,
    productos_promedio, productos_mediana.
    """
    conteos = (
        prod.groupby(["ID_PERSONA_PD", "ID_CONVOCATORIA"])
        .size()
        .rename("n_productos")
        .reset_index()
        .rename(columns={"ID_PERSONA_PD": "ID_PERSONA_PR"})
    )

    base = inv.merge(
        conteos,
        on=["ID_PERSONA_PR", "ID_CONVOCATORIA"],
        how="left",
    )
    base["n_productos"] = base["n_productos"].fillna(0).astype(int)

    out = (
        base.groupby(["ANO_CONVO_INT", "NME_CLASIFICACION_PR"])
        .agg(
            n_investigadores=("ID_PERSONA_PR", "nunique"),
            n_productos_total=("n_productos", "sum"),
            productos_promedio=("n_productos", "mean"),
            productos_mediana=("n_productos", "median"),
            pct_con_al_menos_un_producto=(
                "n_productos", lambda s: (s > 0).mean() * 100
            ),
        )
        .round(2)
        .reset_index()
    )
    return out


# ---------------------------------------------------------------------------
# 3. Productividad × género × área OCDE
# ---------------------------------------------------------------------------

def productividad_por_genero_area(
    prod: pd.DataFrame,
    inv: pd.DataFrame,
    col_area: str = "NME_GRAN_AREA_PR",
) -> pd.DataFrame:
    """
    Productos promedio por investigador, segmentado por gran área OCDE y género.
    """
    conteos = (
        prod.groupby(["ID_PERSONA_PD", "ID_CONVOCATORIA"])
        .size()
        .rename("n_productos")
        .reset_index()
        .rename(columns={"ID_PERSONA_PD": "ID_PERSONA_PR"})
    )

    base = inv[inv["NME_GENERO_PR"].isin(["FEMENINO", "MASCULINO"])].merge(
        conteos,
        on=["ID_PERSONA_PR", "ID_CONVOCATORIA"],
        how="left",
    )
    base["n_productos"] = base["n_productos"].fillna(0).astype(int)

    out = (
        base.groupby([col_area, "NME_GENERO_PR"])
        .agg(
            n_investigadores=("ID_PERSONA_PR", "nunique"),
            productos_promedio=("n_productos", "mean"),
            productos_mediana=("n_productos", "median"),
        )
        .round(2)
        .reset_index()
    )
    return out


def brecha_productividad_genero(
    prod: pd.DataFrame, inv: pd.DataFrame, col_area: str = "NME_GRAN_AREA_PR"
) -> pd.DataFrame:
    """
    Pivot por área con productos_promedio_femenino, masculino y brecha.
    Brecha negativa => mujeres producen menos en promedio.
    """
    base = productividad_por_genero_area(prod, inv, col_area=col_area)
    pivot = base.pivot_table(
        index=col_area,
        columns="NME_GENERO_PR",
        values="productos_promedio",
    ).reset_index()
    pivot.columns.name = None
    pivot = pivot.rename(
        columns={"FEMENINO": "prom_femenino", "MASCULINO": "prom_masculino"}
    )
    pivot["brecha_abs"] = (pivot["prom_femenino"] - pivot["prom_masculino"]).round(2)
    pivot["razon_f_m"] = (pivot["prom_femenino"] / pivot["prom_masculino"]).round(3)
    return pivot.sort_values("brecha_abs")


# ---------------------------------------------------------------------------
# 4. Concentración territorial de la producción
# ---------------------------------------------------------------------------

def productividad_territorial(
    prod: pd.DataFrame,
    inv: pd.DataFrame,
    col_terr: str = "NME_DEPARTAMENTO_RES_PR",
) -> pd.DataFrame:
    """
    Suma productos por territorio del autor reconocido.
    Devuelve [territorio, n_investigadores, n_productos, productos_per_capita,
    pct_productos, pct_investigadores, ratio_concentracion].
    Ratio > 1 => el territorio concentra más outputs que investigadores.
    """
    conteos = (
        prod.groupby(["ID_PERSONA_PD", "ID_CONVOCATORIA"])
        .size()
        .rename("n_productos")
        .reset_index()
        .rename(columns={"ID_PERSONA_PD": "ID_PERSONA_PR"})
    )

    base = inv.merge(
        conteos,
        on=["ID_PERSONA_PR", "ID_CONVOCATORIA"],
        how="left",
    )
    base["n_productos"] = base["n_productos"].fillna(0).astype(int)

    out = (
        base.groupby(col_terr)
        .agg(
            n_investigadores=("ID_PERSONA_PR", "nunique"),
            n_productos=("n_productos", "sum"),
        )
        .reset_index()
    )
    out["productos_per_capita"] = (
        out["n_productos"] / out["n_investigadores"]
    ).round(2)
    total_prod = out["n_productos"].sum()
    total_inv = out["n_investigadores"].sum()
    out["pct_productos"] = (out["n_productos"] / total_prod * 100).round(2)
    out["pct_investigadores"] = (out["n_investigadores"] / total_inv * 100).round(2)
    out["ratio_concentracion"] = (
        out["pct_productos"] / out["pct_investigadores"]
    ).round(2)
    return out.sort_values("n_productos", ascending=False)


# ---------------------------------------------------------------------------
# 5. Tipologías de producto dominantes
# ---------------------------------------------------------------------------

def mix_tipologias(
    prod: pd.DataFrame,
    col_tip: str = "NME_TIPO_MEDICION_PD",
) -> pd.DataFrame:
    """
    Distribución de tipos de medición MinCiencias (apropiación social,
    formación de recursos, generación de nuevo conocimiento, etc.) por
    convocatoria.
    """
    out = (
        prod.groupby(["ANO_CONVO_INT", col_tip])
        .size()
        .rename("n_productos")
        .reset_index()
    )
    total_por_anio = out.groupby("ANO_CONVO_INT")["n_productos"].transform("sum")
    out["pct"] = (out["n_productos"] / total_por_anio * 100).round(2)
    return out.sort_values(["ANO_CONVO_INT", "n_productos"], ascending=[True, False])


def tipologias_por_categoria(
    prod: pd.DataFrame, inv: pd.DataFrame, col_tip: str = "NME_TIPO_MEDICION_PD"
) -> pd.DataFrame:
    """
    Mix de tipologías de producto por categoría de investigador (Junior /
    Asociado / Senior / Emérito). Útil para ver si los Senior concentran
    más "nuevo conocimiento" y los Junior más "formación de recursos".
    """
    enriched = prod.merge(
        inv[["ID_PERSONA_PR", "ID_CONVOCATORIA", "NME_CLASIFICACION_PR"]].rename(
            columns={"ID_PERSONA_PR": "ID_PERSONA_PD"}
        ),
        on=["ID_PERSONA_PD", "ID_CONVOCATORIA"],
        how="inner",
    )
    out = (
        enriched.groupby(["NME_CLASIFICACION_PR", col_tip])
        .size()
        .rename("n_productos")
        .reset_index()
    )
    total_por_cat = out.groupby("NME_CLASIFICACION_PR")["n_productos"].transform("sum")
    out["pct"] = (out["n_productos"] / total_por_cat * 100).round(2)
    return out.sort_values(["NME_CLASIFICACION_PR", "n_productos"], ascending=[True, False])


# ---------------------------------------------------------------------------
# 6. Investigadores reconocidos sin producción
# ---------------------------------------------------------------------------

def reconocidos_sin_produccion(
    prod: pd.DataFrame, inv: pd.DataFrame
) -> pd.DataFrame:
    """
    Por convocatoria, % de investigadores reconocidos que NO tienen producto
    asociado en esa misma convocatoria. Indicador de calidad de captura
    o de "reconocimiento sin obra".
    """
    autores_por_conv = (
        prod.groupby("ID_CONVOCATORIA")["ID_PERSONA_PD"]
        .apply(lambda s: set(s.dropna().astype("Int64")))
        .to_dict()
    )

    rows = []
    for ano, grupo in inv.groupby(["ANO_CONVO_INT", "ID_CONVOCATORIA"]):
        ano_int, id_conv = ano
        ids = set(grupo["ID_PERSONA_PR"].dropna().astype("Int64"))
        autores = autores_por_conv.get(id_conv, set())
        con_prod = ids & autores
        rows.append(
            {
                "ANO_CONVO_INT": ano_int,
                "ID_CONVOCATORIA": id_conv,
                "n_reconocidos": len(ids),
                "n_con_produccion": len(con_prod),
                "n_sin_produccion": len(ids) - len(con_prod),
                "pct_sin_produccion": round(
                    (len(ids) - len(con_prod)) / len(ids) * 100, 2
                ) if ids else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values("ANO_CONVO_INT")
