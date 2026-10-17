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


def aviso_produccion_ausente(exc: Exception) -> int:
    """
    Avisa de que falta el dataset de produccion y devuelve el codigo de salida 3.

    `cargar_produccion()` necesita `datos/raw/produccion_grupos.csv` (~1,2 GB),
    que NO se versiona en el repositorio. Sin el, los scripts de produccion no
    pueden producir sus salidas: antes morian con un traceback que parecia un bug
    de codigo. Ahora informan y terminan con un codigo distinto de 1 para que
    quien orqueste pueda distinguir "faltan datos" de "el script fallo".

    El texto vive aqui, junto a `cargar_produccion()`, para no repetirlo en los
    tres scripts que la usan.
    """
    print("\n" + "=" * 70)
    print("[datos faltantes] no se puede continuar sin el dataset de produccion")
    print("=" * 70)
    print(f"  detalle: {exc}")
    print("  El archivo NO esta versionado (~1,2 GB). Para obtenerlo:")
    print("      python -m src.ingesta.produccion")
    print("  Requiere conexion a la API de Socrata. Sin el, este script no puede")
    print("  generar sus tablas ni figuras: se prefiere avisar antes que dejar")
    print("  evidencia parcial que parezca completa.")
    print("=" * 70)
    return 3


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
