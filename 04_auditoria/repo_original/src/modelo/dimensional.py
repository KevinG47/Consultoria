"""
modelo/dimensional.py

Modelo estrella para el Observatorio MinCiencias — Issue #14.

Construye y puebla las tablas dimensionales y la tabla de hechos en DuckDB
a partir del DataFrame transformado (77.237 registros, 6 convocatorias).

Esquema estrella
----------------
    dim_convocatoria   ←┐
    dim_investigador   ←┤
    dim_categoria      ←┤── fact_clasificacion
    dim_area           ←┤
    dim_territorio     ←┤
    dim_formacion      ←┘

Nota sobre INST_FILIA: el campo contiene instituciones separadas por '|'.
Se construye adicionalmente dim_institucion y la tabla puente
bridge_hecho_institucion para representar la relación N:N.
"""

import pathlib
import duckdb
import pandas as pd

from analisis.longitudinal import normalizar_categoria, ORDEN_CATEGORIAS

DB_PATH = pathlib.Path(__file__).resolve().parents[2] / "datos" / "processed" / "observatorio.duckdb"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conexion(path: pathlib.Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def _drop_and_create(con: duckdb.DuckDBPyConnection, ddl: str) -> None:
    table = ddl.split("(")[0].split()[-1]
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(ddl)


# ---------------------------------------------------------------------------
# Dimensiones
# ---------------------------------------------------------------------------

def construir_dim_convocatoria(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["ID_CONVOCATORIA", "NME_CONVOCATORIA", "ANO_CONVO_INT", "ANO_CONVO_FECHA"]
    dim = df[cols].drop_duplicates(subset=["ID_CONVOCATORIA"]).copy()
    dim = dim.sort_values("ANO_CONVO_INT").reset_index(drop=True)
    dim.columns = dim.columns.str.lower()
    return dim


def construir_dim_investigador(df: pd.DataFrame) -> pd.DataFrame:
    """Snapshot: atributos del investigador en su primera aparición."""
    cols = [
        "ID_PERSONA_PR",
        "NME_GENERO_PR",
        "NME_PAIS_NAC_PR",
        "NME_REGION_NAC_PR",
        "NME_DEPARTAMENTO_NAC_PR",
        "NME_MUNICIPIO_NAC_PR",
    ]
    dim = (
        df[cols]
        .sort_values("ID_PERSONA_PR")
        .drop_duplicates(subset=["ID_PERSONA_PR"], keep="first")
        .reset_index(drop=True)
    )
    dim.columns = dim.columns.str.lower()
    return dim


def construir_dim_categoria(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["ID_CLAS_PR", "NME_CLASIFICACION_PR", "ORDEN_CLAS_PR"]
    dim = df[cols].drop_duplicates(subset=["ID_CLAS_PR"]).copy()
    dim["CATEGORIA_NORMALIZADA"] = dim["NME_CLASIFICACION_PR"].apply(normalizar_categoria)
    dim["ORDEN_NORMALIZADO"] = dim["CATEGORIA_NORMALIZADA"].map(ORDEN_CATEGORIAS)
    dim = dim.sort_values("ORDEN_CLAS_PR").reset_index(drop=True)
    dim.columns = dim.columns.str.lower()
    return dim


def construir_dim_area(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["ID_AREA_CON_PR", "NME_GRAN_AREA_PR", "NME_AREA_PR", "NME_ESP_AREA_PR"]
    dim = (
        df[cols]
        .drop_duplicates(subset=["ID_AREA_CON_PR"])
        .sort_values("ID_AREA_CON_PR")
        .reset_index(drop=True)
    )
    dim.columns = dim.columns.str.lower()
    return dim


def construir_dim_territorio(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "COD_DANE_RES_PR",
        "NME_PAIS_RES_PR",
        "NME_REGION_RES_PR",
        "NME_DEPARTAMENTO_RES_PR",
        "NME_MUNICIPIO_RES_PR",
    ]
    dim = (
        df[cols]
        .drop_duplicates()
        .sort_values("COD_DANE_RES_PR")
        .reset_index(drop=True)
    )
    dim.insert(0, "SK_TERRITORIO", range(1, len(dim) + 1))
    dim.columns = dim.columns.str.lower()
    return dim


def construir_dim_formacion(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["ID_NIV_FORMACION_PR", "NME_NIV_FORM_PR", "NRO_ORDEN_FORM_PR"]
    dim = (
        df[cols]
        .drop_duplicates(subset=["ID_NIV_FORMACION_PR"])
        .sort_values("NRO_ORDEN_FORM_PR")
        .reset_index(drop=True)
    )
    dim.columns = dim.columns.str.lower()
    return dim


def construir_dim_institucion(df: pd.DataFrame) -> pd.DataFrame:
    """Desagrega INST_FILIA (pipe-separated) en una dimensión de instituciones."""
    instituciones = (
        df["INST_FILIA"]
        .dropna()
        .str.split("|")
        .explode()
        .str.strip()
        .str.upper()
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )
    dim = pd.DataFrame({
        "sk_institucion": range(1, len(instituciones) + 1),
        "nme_institucion": instituciones.values,
    })
    return dim


# ---------------------------------------------------------------------------
# Tabla de hechos
# ---------------------------------------------------------------------------

def construir_fact_clasificacion(
    df: pd.DataFrame,
    dim_territorio: pd.DataFrame,
) -> pd.DataFrame:
    """
    Tabla de hechos: un registro por investigador × convocatoria.

    Agrega la SK de territorio mediante join sobre las columnas geográficas.
    """
    geo_cols = [
        "cod_dane_res_pr",
        "nme_pais_res_pr",
        "nme_region_res_pr",
        "nme_departamento_res_pr",
        "nme_municipio_res_pr",
    ]
    df_lower = df.copy()
    df_lower.columns = df_lower.columns.str.lower()

    fact = df_lower[[
        "id_convocatoria",
        "id_persona_pr",
        "id_clas_pr",
        "id_area_con_pr",
        "id_niv_formacion_pr",
        *geo_cols,
        "edad_anos_pr",
        "id_victima_conflicto",
        "txt_grupo_etnico",
        "txt_poblacion_disca",
        "inst_filia",
    ]].copy()

    # Unir SK de territorio
    fact = fact.merge(
        dim_territorio[["sk_territorio", *geo_cols]],
        on=geo_cols,
        how="left",
    )
    fact = fact.drop(columns=geo_cols)
    fact.insert(0, "sk_hecho", range(1, len(fact) + 1))
    return fact


# ---------------------------------------------------------------------------
# Bridge hecho ↔ institución
# ---------------------------------------------------------------------------

def construir_bridge_institucion(
    fact: pd.DataFrame,
    dim_inst: pd.DataFrame,
) -> pd.DataFrame:
    """Tabla puente N:N entre fact_clasificacion y dim_institucion."""
    inst_map = dict(zip(dim_inst["nme_institucion"], dim_inst["sk_institucion"]))

    filas = []
    for _, row in fact[["sk_hecho", "inst_filia"]].dropna(subset=["inst_filia"]).iterrows():
        for inst in str(row["inst_filia"]).split("|"):
            inst_clean = inst.strip().upper()
            sk = inst_map.get(inst_clean)
            if sk:
                filas.append({"sk_hecho": row["sk_hecho"], "sk_institucion": sk})

    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Carga en DuckDB
# ---------------------------------------------------------------------------

def cargar_en_duckdb(
    df: pd.DataFrame,
    path: pathlib.Path = DB_PATH,
    verbose: bool = True,
) -> duckdb.DuckDBPyConnection:
    """
    Construye todas las dimensiones y la tabla de hechos y las carga en DuckDB.

    Retorna la conexión abierta para consultas inmediatas.
    """
    def log(msg):
        if verbose:
            print(msg)

    log("Construyendo dimensiones...")
    dim_conv   = construir_dim_convocatoria(df)
    dim_inv    = construir_dim_investigador(df)
    dim_cat    = construir_dim_categoria(df)
    dim_area   = construir_dim_area(df)
    dim_terr   = construir_dim_territorio(df)
    dim_form   = construir_dim_formacion(df)
    dim_inst   = construir_dim_institucion(df)

    log("Construyendo tabla de hechos...")
    fact       = construir_fact_clasificacion(df, dim_terr)
    bridge     = construir_bridge_institucion(fact, dim_inst)

    log(f"Conectando a DuckDB: {path}")
    con = _conexion(path)

    tablas = {
        "dim_convocatoria":  dim_conv,
        "dim_investigador":  dim_inv,
        "dim_categoria":     dim_cat,
        "dim_area":          dim_area,
        "dim_territorio":    dim_terr,
        "dim_formacion":     dim_form,
        "dim_institucion":   dim_inst,
        "fact_clasificacion": fact.drop(columns=["inst_filia"]),
        "bridge_hecho_institucion": bridge,
    }

    for nombre, tabla in tablas.items():
        con.execute(f"DROP TABLE IF EXISTS {nombre}")
        con.execute(f"CREATE TABLE {nombre} AS SELECT * FROM tabla")
        log(f"  OK {nombre:35s} {len(tabla):>7,} filas")

    return con


def resumen_modelo(con: duckdb.DuckDBPyConnection) -> None:
    """Imprime un resumen del modelo estrella cargado."""
    print("\n=== Modelo estrella en DuckDB ===")
    tablas = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY 1"
    ).fetchdf()
    for t in tablas["table_name"]:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:35s} {n:>8,} filas")
