"""
analisis/longitudinal.py

Panel longitudinal de investigadores — Issue #11.

Funciones para construir el panel analítico y calcular el tracking de
investigadores entre convocatorias consecutivas usando ID_PERSONA_PR.
Cubre las 6 convocatorias históricas (2013, 2014, 2015, 2017, 2019, 2021).
"""

import pandas as pd

# Orden ordinal de las categorías de clasificación
ORDEN_CATEGORIAS: dict = {
    "Junior": 1,
    "Asociado": 2,
    "Senior": 3,
    "Emérito": 4,
}


def normalizar_categoria(x: str):
    """Normaliza texto libre de categoría a una de las 4 etiquetas canónicas."""
    s = str(x).strip().lower()
    if "junior" in s:
        return "Junior"
    if "asociado" in s:
        return "Asociado"
    if "sénior" in s or "senior" in s:
        return "Senior"
    if "emérito" in s or "emerito" in s:
        return "Emérito"
    return None


def construir_panel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye la base analítica mínima para el panel longitudinal.

    Requiere columnas: ID_PERSONA_PR, ANO_CONVO_INT, NME_CLASIFICACION_PR.
    Retorna una fila por investigador y convocatoria, sin duplicados.
    En caso de registros duplicados para el mismo investigador y año
    se conserva el de mayor categoría.
    """
    cols = ["ID_PERSONA_PR", "ANO_CONVO_INT", "NME_CLASIFICACION_PR"]
    panel = df[cols].copy()
    panel["categoria"] = panel["NME_CLASIFICACION_PR"].apply(normalizar_categoria)
    panel["orden"] = panel["categoria"].map(ORDEN_CATEGORIAS)
    panel = panel.dropna(subset=["ID_PERSONA_PR", "ANO_CONVO_INT", "categoria"])
    panel["ANO_CONVO_INT"] = panel["ANO_CONVO_INT"].astype(int)
    # Deduplicar: ante duplicados (ID, año) conservar la categoría más alta
    panel = (
        panel.sort_values("orden", ascending=False)
        .drop_duplicates(subset=["ID_PERSONA_PR", "ANO_CONVO_INT"])
        .reset_index(drop=True)
    )
    return panel[["ID_PERSONA_PR", "ANO_CONVO_INT", "categoria", "orden"]]


def comparar_periodo(
    panel: pd.DataFrame, anio_inicial: int, anio_final: int
) -> pd.DataFrame:
    """
    Compara la trayectoria de investigadores entre dos convocatorias.

    Realiza un left join desde anio_inicial hacia anio_final para que los
    investigadores que desaparecen queden representados.

    Retorna columnas:
        ID_PERSONA_PR, categoria_inicial, orden_inicial,
        categoria_final, orden_final, resultado, periodo
    """
    t0 = panel[panel["ANO_CONVO_INT"] == anio_inicial][
        ["ID_PERSONA_PR", "categoria", "orden"]
    ].rename(columns={"categoria": "categoria_inicial", "orden": "orden_inicial"})

    t1 = panel[panel["ANO_CONVO_INT"] == anio_final][
        ["ID_PERSONA_PR", "categoria", "orden"]
    ].rename(columns={"categoria": "categoria_final", "orden": "orden_final"})

    comp = t0.merge(t1, on="ID_PERSONA_PR", how="left")

    def _clasificar(row):
        if pd.isna(row["categoria_final"]):
            return "Desaparece"
        if row["orden_final"] > row["orden_inicial"]:
            return "Sube"
        if row["orden_final"] < row["orden_inicial"]:
            return "Baja"
        return "Se mantiene"

    comp["resultado"] = comp.apply(_clasificar, axis=1)
    comp["periodo"] = f"{anio_inicial}–{anio_final}"
    return comp


def resumen_tracking(comp: pd.DataFrame) -> pd.DataFrame:
    """Cuenta y porcentaje de cada resultado para un periodo dado."""
    resumen = (
        comp["resultado"]
        .value_counts()
        .rename_axis("resultado")
        .reset_index(name="n")
    )
    resumen["pct"] = (resumen["n"] / resumen["n"].sum()).round(4)
    if "periodo" in comp.columns:
        resumen.insert(0, "periodo", comp["periodo"].iloc[0])
    return resumen


def tracking_por_categoria(comp: pd.DataFrame) -> pd.DataFrame:
    """Desglose del tracking por categoría inicial."""
    return (
        comp.groupby(["categoria_inicial", "resultado"])
        .size()
        .unstack(fill_value=0)
    )


def tracking_todos_periodos(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Ejecuta comparar_periodo para todos los pares de años consecutivos
    presentes en el panel y devuelve los resúmenes apilados.
    """
    anios = sorted(panel["ANO_CONVO_INT"].unique())
    bloques = []
    for a0, a1 in zip(anios, anios[1:]):
        comp = comparar_periodo(panel, a0, a1)
        bloques.append(resumen_tracking(comp))
    return pd.concat(bloques, ignore_index=True)


def matriz_transicion(
    comp: pd.DataFrame, incluir_desaparece: bool = False
) -> tuple:
    """
    Calcula la matriz de conteos y la de probabilidades de transición.

    Parameters
    ----------
    comp : resultado de comparar_periodo
    incluir_desaparece : si True agrega "Desaparece" como estado final posible

    Returns
    -------
    (conteos, probabilidades) — ambos DataFrames con filas = categoría inicial
    """
    temp = comp.copy()
    if incluir_desaparece:
        col_final = "categoria_final_ext"
        temp[col_final] = temp["categoria_final"].fillna("Desaparece")
    else:
        col_final = "categoria_final"
        temp = temp.dropna(subset=["categoria_final"])

    conteos = pd.crosstab(temp["categoria_inicial"], temp[col_final])
    # Ordenar columnas por orden canónico cuando es posible
    orden_cols = [c for c in [*ORDEN_CATEGORIAS.keys(), "Desaparece"] if c in conteos.columns]
    conteos = conteos[orden_cols]
    probs = conteos.div(conteos.sum(axis=1), axis=0).round(4)
    return conteos, probs


def matrices_todos_periodos(
    panel: pd.DataFrame, incluir_desaparece: bool = True
) -> dict:
    """
    Calcula matrices de transición para todos los pares consecutivos.

    Retorna un dict con estructura:
        { "2013–2014": (conteos_df, probs_df), ... }
    """
    anios = sorted(panel["ANO_CONVO_INT"].unique())
    resultado = {}
    for a0, a1 in zip(anios, anios[1:]):
        comp = comparar_periodo(panel, a0, a1)
        periodo = f"{a0}–{a1}"
        resultado[periodo] = matriz_transicion(comp, incluir_desaparece=incluir_desaparece)
    return resultado


def tasa_retencion_por_periodo(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la tasa de retención entre convocatorias consecutivas.

    Retención = investigadores presentes en t0 que también aparecen en t1
                dividido entre el total en t0.
    También reporta la cantidad de investigadores nuevos en t1 (sin historial previo).
    """
    anios = sorted(panel["ANO_CONVO_INT"].unique())
    filas = []
    for a0, a1 in zip(anios, anios[1:]):
        ids_a0 = set(panel.loc[panel["ANO_CONVO_INT"] == a0, "ID_PERSONA_PR"])
        ids_a1 = set(panel.loc[panel["ANO_CONVO_INT"] == a1, "ID_PERSONA_PR"])
        retenidos = len(ids_a0 & ids_a1)
        total = len(ids_a0)
        nuevos = len(ids_a1 - ids_a0)
        filas.append({
            "periodo": f"{a0}–{a1}",
            "anio_inicial": a0,
            "anio_final": a1,
            "total_inicial": total,
            "retenidos": retenidos,
            "tasa_retencion": round(retenidos / total, 4) if total else None,
            "nuevos_en_final": nuevos,
        })
    return pd.DataFrame(filas)
