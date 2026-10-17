# -*- coding: utf-8 -*-
"""
Transformacion.py

Módulo de transformación de datos para el Observatorio de Ciencia,
Tecnología e Innovación — Investigadores Reconocidos Minciencias (Grupo 7).

Aplica limpieza, estandarización y enriquecimiento al DataFrame consolidado
generado por ingesta.py, dejándolo listo para análisis y visualización.
"""

import pathlib
import re
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "datos" / "tarea_join"

# Columnas numéricas del dataset
COLS_NUMERICAS = ["NRO_ORDEN_FORM_PR", "ORDEN_CLAS_PR", "EDAD_ANOS_PR"]

# Columnas categóricas clave
COLS_CATEGORICAS = [
    "NME_CONVOCATORIA",
    "NME_GRAN_AREA_PR",
    "NME_AREA_PR",
    "NME_ESP_AREA_PR",
    "NME_GENERO_PR",
    "NME_NIV_FORM_PR",
    "NME_CLASIFICACION_PR",
    "NME_PAIS_NAC_PR",
    "NME_REGION_NAC_PR",
    "NME_DEPARTAMENTO_NAC_PR",
    "NME_MUNICIPIO_NAC_PR",
    "NME_PAIS_RES_PR",
    "NME_REGION_RES_PR",
    "NME_DEPARTAMENTO_RES_PR",
    "NME_MUNICIPIO_RES_PR",
    "TXT_GRUPO_ETNICO",
    "TXT_POBLACION_DISCA",
    "ID_VICTIMA_CONFLICTO",
]


# ---------------------------------------------------------------------------
# Funciones de limpieza
# ---------------------------------------------------------------------------

def limpiar_texto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza las columnas de texto: elimina espacios extra y convierte a
    mayúsculas.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df = df.copy()
    for col in COLS_CATEGORICAS:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.upper()
                .replace({"NAN": np.nan, "NONE": np.nan, "": np.nan})
            )
    return df


def parsear_ano_convocatoria(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrae el año de la columna ANO_CONVO y lo almacena como entero en la
    columna ANO_CONVO_INT.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df = df.copy()
    if "ANO_CONVO" not in df.columns:
        return df

    s = df["ANO_CONVO"].astype(str).str.strip()

    # Intento 1: formato de texto con fecha (dd/mm/aaaa o similar)
    fecha = pd.to_datetime(s, dayfirst=True, errors="coerce")

    # Intento 2: serial numérico de Excel
    s_num = pd.to_numeric(s, errors="coerce")
    fecha_serial = pd.to_datetime(
        s_num, unit="D", origin="1899-12-30", errors="coerce"
    )

    # Intento 3: año de 4 dígitos embebido en el texto
    anio_regex = s.str.extract(r"\b(20[0-9]{2})\b")[0]
    fecha_regex = pd.to_datetime(anio_regex, format="%Y", errors="coerce")

    # Combinar los tres intentos por orden de prioridad
    df["ANO_CONVO_FECHA"] = (
        fecha
        .where(fecha.notna(), fecha_serial)
        .where(fecha.notna() | fecha_serial.notna(), fecha_regex)
    )
    df["ANO_CONVO_INT"] = df["ANO_CONVO_FECHA"].dt.year.astype("Int64")
    return df


def tratar_faltantes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Imputa o marca los valores faltantes en las columnas numéricas y
    categóricas.

    * Numéricas: rellena con la mediana.
    * Categóricas: deja NaN (se etiquetan explícitamente como 'NO REPORTADO').

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df = df.copy()
    for col in COLS_NUMERICAS:
        if col in df.columns:
            mediana = df[col].median()
            df[col] = df[col].fillna(mediana)

    for col in COLS_CATEGORICAS:
        if col in df.columns:
            df[col] = df[col].fillna("NO REPORTADO")

    return df


def estandarizar_genero(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza los valores de la columna NME_GENERO_PR a
    {'MASCULINO', 'FEMENINO', 'NO REPORTADO'}.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df = df.copy()
    if "NME_GENERO_PR" not in df.columns:
        return df

    mapa = {
        "M": "MASCULINO",
        "MASCULINO": "MASCULINO",
        "HOMBRE": "MASCULINO",
        "F": "FEMENINO",
        "FEMENINO": "FEMENINO",
        "MUJER": "FEMENINO",
    }
    df["NME_GENERO_PR"] = (
        df["NME_GENERO_PR"]
        .str.strip()
        .str.upper()
        .map(mapa)
        .fillna("NO REPORTADO")
    )
    return df


# ---------------------------------------------------------------------------
# Pipeline completo
# ---------------------------------------------------------------------------

def transformar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica el pipeline completo de transformación al DataFrame consolidado.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame en bruto devuelto por ingesta.cargar_consolidado().

    Returns
    -------
    pd.DataFrame
        DataFrame transformado y listo para análisis.
    """
    df = limpiar_texto(df)
    df = parsear_ano_convocatoria(df)
    df = estandarizar_genero(df)
    df = tratar_faltantes(df)
    print(f"[transformacion] Pipeline completado. Shape final: {df.shape}")
    return df


# ---------------------------------------------------------------------------
# Ejecución directa
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from ingesta import cargar_consolidado

    df_raw = cargar_consolidado()
    df_clean = transformar(df_raw)
    print(df_clean.head())
