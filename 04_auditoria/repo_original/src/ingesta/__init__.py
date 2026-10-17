"""
Paquete de ingesta de datos — Observatorio MinCiencias.

Exporta cargar_consolidado() y cargar_produccion() para que los notebooks
y scripts puedan importarlas con:
    from ingesta import cargar_consolidado, cargar_produccion
"""

import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
_RAW = ROOT / "datos" / "raw" / "investigadores_consolidado.csv"
_TAREA = ROOT / "datos" / "tarea_join" / "investigadores_consolidado.xlsx"
_PROD = ROOT / "datos" / "raw" / "produccion_grupos.csv"


def cargar_consolidado() -> pd.DataFrame:
    """Carga el dataset consolidado de investigadores (77 237 registros, 30 cols).

    Prioridad: datos/raw/investigadores_consolidado.csv (Socrata)
               datos/tarea_join/investigadores_consolidado.xlsx (Excel local)
    """
    if _RAW.exists():
        print(f"[ingesta] Cargando CSV: {_RAW}")
        df = pd.read_csv(_RAW, low_memory=False)
    elif _TAREA.exists():
        print(f"[ingesta] Cargando XLSX: {_TAREA}")
        df = pd.read_excel(_TAREA)
    else:
        raise FileNotFoundError(
            "Dataset no encontrado. Ejecute: python -m src.ingesta.minciencias"
        )
    df.columns = df.columns.str.upper()
    print(f"[ingesta] {len(df):,} registros | {df.shape[1]} columnas")
    return df


def cargar_produccion() -> pd.DataFrame:
    """Carga el dataset de Producción de Grupos de Investigación (Socrata 33dq-ab5a).

    ~3.2M filas. Llave para cruzar con investigadores: ID_PERSONA_PD ↔ ID_PERSONA_PR.
    """
    if not _PROD.exists():
        raise FileNotFoundError(
            "Dataset de producción no encontrado. "
            "Ejecute: python -m src.ingesta.produccion"
        )
    print(f"[ingesta] Cargando CSV producción: {_PROD}")
    df = pd.read_csv(_PROD, low_memory=False)
    df.columns = df.columns.str.upper()
    print(f"[ingesta] {len(df):,} filas | {df.shape[1]} columnas")
    return df
