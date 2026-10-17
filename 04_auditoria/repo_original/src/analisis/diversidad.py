"""
analisis/diversidad.py

Analisis de variables de diversidad (Issue #20):
- ID_VICTIMA_CONFLICTO
- TXT_GRUPO_ETNICO
- TXT_POBLACION_DISCA

Hallazgo central: estas variables solo se capturaron a partir de la
convocatoria 2021. Las 5 convocatorias previas tienen 100% NO REGISTRA.
"""

import pandas as pd

# Proporciones poblacionales de referencia (DANE 2018 / RUV 2021)
DANE_REFERENCIA = {
    "etnia": {
        "NEGRO/AFROCOLOMBIANO": 6.7,
        "INDIGENA": 4.4,
        "RAIZAL": 0.06,
        "PALENQUERO": 0.014,
        "RROM": 0.005,
    },
    "discapacidad_pct_total": 7.1,
    "victimas_conflicto_pct_total": 17.7,  # RUV 2021 / poblacion 2021
}

VALORES_NULOS = {
    "ID_VICTIMA_CONFLICTO": "NO REGISTRA",
    "TXT_GRUPO_ETNICO": "NO DISPONIBLE",
    "TXT_POBLACION_DISCA": "NO DISPONIBLE",
}


def cobertura_por_convocatoria(df: pd.DataFrame) -> pd.DataFrame:
    """
    % de registros con valor "NO REGISTRA" / "NO DISPONIBLE" por convocatoria.
    Cobertura = 100 - %_no_registra.
    """
    rows = []
    for ano, grupo in df.groupby("ANO_CONVO_INT"):
        fila = {"ANO_CONVO_INT": ano, "n_total": len(grupo)}
        for col, val_nulo in VALORES_NULOS.items():
            pct_nulo = (grupo[col] == val_nulo).mean() * 100
            fila[f"{col}_pct_no_registra"] = round(pct_nulo, 2)
            fila[f"{col}_pct_cobertura"] = round(100 - pct_nulo, 2)
        rows.append(fila)
    return pd.DataFrame(rows)


def distribucion_categoria(
    df: pd.DataFrame,
    columna: str,
    excluir_nulo: bool = True,
) -> pd.DataFrame:
    """
    Distribucion de valores de una variable de diversidad.
    Si excluir_nulo, descarta el valor "NO REGISTRA"/"NO DISPONIBLE" del denominador.
    """
    base = df.copy()
    val_nulo = VALORES_NULOS[columna]
    if excluir_nulo:
        base = base[base[columna] != val_nulo]
    conteo = base[columna].value_counts()
    pct = (conteo / conteo.sum() * 100).round(2)
    return pd.DataFrame({
        "valor": conteo.index,
        "n": conteo.values,
        "pct": pct.values,
    })


def comparar_dane(df_2021: pd.DataFrame) -> pd.DataFrame:
    """
    Compara la representacion en investigadores 2021 con la poblacion DANE.
    Calcula la razon de subrepresentacion (DANE / MinCiencias).
    """
    # Etnia: excluir "NINGUN GRUPO ETNICO" del denominador para ver minorias
    etnia = df_2021[df_2021["TXT_GRUPO_ETNICO"] != "NO DISPONIBLE"]
    n_etnia_resp = len(etnia)

    rows = []
    for nombre_dane, pct_dane in DANE_REFERENCIA["etnia"].items():
        # Mapear nombres MinCiencias -> DANE
        if "AFRO" in nombre_dane:
            mascara = etnia["TXT_GRUPO_ETNICO"].str.contains("AFRO|NEGRA", case=False, na=False)
        elif "INDIGENA" in nombre_dane:
            mascara = etnia["TXT_GRUPO_ETNICO"].str.contains("INDIGENA|IND.GENA", case=False, na=False, regex=True)
        elif "RAIZAL" in nombre_dane:
            mascara = etnia["TXT_GRUPO_ETNICO"].str.contains("RAIZAL", case=False, na=False)
        elif "PALENQUERO" in nombre_dane:
            mascara = etnia["TXT_GRUPO_ETNICO"].str.contains("PALENQUERO", case=False, na=False)
        elif "RROM" in nombre_dane:
            mascara = etnia["TXT_GRUPO_ETNICO"].str.contains("RROM|GITANO", case=False, na=False)
        else:
            mascara = pd.Series(False, index=etnia.index)
        n = mascara.sum()
        pct_minc = (n / n_etnia_resp * 100) if n_etnia_resp > 0 else 0
        rows.append({
            "grupo": nombre_dane,
            "n_minciencias_2021": n,
            "pct_minciencias": round(pct_minc, 2),
            "pct_dane_2018": pct_dane,
            "razon_subrepresentacion": round(pct_dane / pct_minc, 1) if pct_minc > 0 else None,
        })

    # Discapacidad
    disca = df_2021[df_2021["TXT_POBLACION_DISCA"] != "NO DISPONIBLE"]
    n_con_disca = len(disca[disca["TXT_POBLACION_DISCA"] != "NINGUNA"])
    pct_disca = (n_con_disca / len(disca) * 100) if len(disca) > 0 else 0
    rows.append({
        "grupo": "DISCAPACIDAD (cualquiera)",
        "n_minciencias_2021": n_con_disca,
        "pct_minciencias": round(pct_disca, 2),
        "pct_dane_2018": DANE_REFERENCIA["discapacidad_pct_total"],
        "razon_subrepresentacion": round(DANE_REFERENCIA["discapacidad_pct_total"] / pct_disca, 1) if pct_disca > 0 else None,
    })

    # Victimas conflicto
    vict = df_2021[df_2021["ID_VICTIMA_CONFLICTO"] != "NO REGISTRA"]
    n_vict = (vict["ID_VICTIMA_CONFLICTO"] == "SÍ").sum()
    pct_vict = (n_vict / len(vict) * 100) if len(vict) > 0 else 0
    rows.append({
        "grupo": "VICTIMA CONFLICTO",
        "n_minciencias_2021": n_vict,
        "pct_minciencias": round(pct_vict, 2),
        "pct_dane_2018": DANE_REFERENCIA["victimas_conflicto_pct_total"],
        "razon_subrepresentacion": round(DANE_REFERENCIA["victimas_conflicto_pct_total"] / pct_vict, 1) if pct_vict > 0 else None,
    })

    return pd.DataFrame(rows)


def interseccional_genero_etnia(df_2021: pd.DataFrame) -> pd.DataFrame:
    """Cruce genero x etnia (excluyendo NO DISPONIBLE / NO REPORTADO)."""
    sub = df_2021[
        (df_2021["TXT_GRUPO_ETNICO"] != "NO DISPONIBLE")
        & (df_2021["NME_GENERO_PR"].isin(["FEMENINO", "MASCULINO"]))
    ]
    return (
        sub.groupby(["TXT_GRUPO_ETNICO", "NME_GENERO_PR"])
        .size()
        .unstack(fill_value=0)
        .assign(total=lambda d: d.sum(axis=1))
        .assign(pct_femenino=lambda d: (d["FEMENINO"] / d["total"] * 100).round(1))
        .sort_values("total", ascending=False)
        .reset_index()
    )


def categoria_por_minoria(df_2021: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Distribucion de categorias academicas por valor de la variable de diversidad."""
    val_nulo = VALORES_NULOS[columna]
    sub = df_2021[df_2021[columna] != val_nulo]
    return (
        sub.groupby([columna, "NME_CLASIFICACION_PR"])
        .size()
        .unstack(fill_value=0)
        .assign(total=lambda d: d.sum(axis=1))
        .sort_values("total", ascending=False)
        .reset_index()
    )
