"""
Sprint 5 — Extensión del modelo en DuckDB con la tabla de Producción.

Añade tres objetos al observatorio.duckdb existente:

    fact_produccion           : una fila por (id_persona_pd, id_convocatoria, id_producto_pd)
    dim_producto              : catálogo de productos
    dim_grupo                 : catálogo de grupos de investigación
    vw_investigador_x_produccion : vista lista para análisis cruzados

Requiere:
    - observatorio.duckdb ya construido (correr scripts/sprint2_duckdb.py antes)
    - datos/raw/produccion_grupos.csv (correr python -m src.ingesta.produccion)

Uso:
    python scripts/sprint5_duckdb.py
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import duckdb

from ingesta import cargar_produccion
from analisis.produccion import normalizar_produccion

DB_PATH = ROOT / "datos" / "processed" / "observatorio.duckdb"
EVIDENCIAS = ROOT / "evidencias"
EVIDENCIAS.mkdir(exist_ok=True)


CONSULTAS_VALIDACION = {
    "productos_por_convocatoria": """
        SELECT id_convocatoria,
               COUNT(*) AS n_productos,
               COUNT(DISTINCT id_persona_pd) AS n_autores_unicos,
               COUNT(DISTINCT id_producto_pd) AS n_productos_unicos
        FROM fact_produccion
        GROUP BY id_convocatoria
        ORDER BY id_convocatoria
    """,
    "cobertura_reconocimiento": """
        SELECT v.ano_convo_int,
               COUNT(*) AS n_productos,
               SUM(CASE WHEN v.es_reconocido THEN 1 ELSE 0 END) AS firmados_por_reconocido,
               ROUND(100.0 * SUM(CASE WHEN v.es_reconocido THEN 1 ELSE 0 END)
                     / COUNT(*), 2) AS pct_reconocido
        FROM vw_investigador_x_produccion v
        GROUP BY v.ano_convo_int
        ORDER BY v.ano_convo_int
    """,
    "productividad_por_categoria": """
        SELECT cat.categoria_normalizada,
               COUNT(DISTINCT v.id_persona_pd) AS n_investigadores,
               COUNT(*) AS n_productos,
               ROUND(COUNT(*)::DOUBLE / COUNT(DISTINCT v.id_persona_pd), 2) AS prom_productos
        FROM vw_investigador_x_produccion v
        JOIN dim_categoria cat ON v.id_clas_pr = cat.id_clas_pr
        WHERE v.id_clas_pr IS NOT NULL
        GROUP BY cat.categoria_normalizada, cat.orden_normalizado
        ORDER BY cat.orden_normalizado
    """,
    "top_grupos_productivos": """
        SELECT g.nme_grupo_gr, g.cod_grupo_gr,
               COUNT(*) AS n_productos
        FROM fact_produccion f
        JOIN dim_grupo g USING (cod_grupo_gr)
        GROUP BY g.nme_grupo_gr, g.cod_grupo_gr
        ORDER BY n_productos DESC
        LIMIT 10
    """,
    "tipologias_dominantes": """
        SELECT nme_tipo_medicion_pd,
               COUNT(*) AS n_productos,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
        FROM fact_produccion
        GROUP BY nme_tipo_medicion_pd
        ORDER BY n_productos DESC
        LIMIT 15
    """,
}


def construir_tablas(con: duckdb.DuckDBPyConnection) -> None:
    print("[1/4] Cargando dataset de producción...")
    prod = normalizar_produccion(cargar_produccion())
    print(f"      Shape: {prod.shape}")

    print("[2/4] Insertando tablas en DuckDB...")

    con.register("prod_raw", prod)

    con.execute("DROP TABLE IF EXISTS fact_produccion")
    con.execute("""
        CREATE TABLE fact_produccion AS
        SELECT
            id_persona_pd,
            id_convocatoria,
            id_producto_pd,
            cod_grupo_gr,
            ano_convo_int,
            nme_categoria_pd,
            nme_clase_pd,
            nme_tipo_medicion_pd,
            nme_tipologia_pd,
            id_tipo_pd_med,
            fcreacion_pd
        FROM prod_raw
    """)

    con.execute("DROP TABLE IF EXISTS dim_producto")
    con.execute("""
        CREATE TABLE dim_producto AS
        SELECT DISTINCT
            id_producto_pd,
            nme_producto_pd,
            nme_categoria_pd,
            nme_clase_pd,
            nme_tipo_medicion_pd,
            nme_tipologia_pd
        FROM prod_raw
        WHERE id_producto_pd IS NOT NULL
    """)

    con.execute("DROP TABLE IF EXISTS dim_grupo")
    con.execute("""
        CREATE TABLE dim_grupo AS
        SELECT DISTINCT cod_grupo_gr, nme_grupo_gr
        FROM prod_raw
        WHERE cod_grupo_gr IS NOT NULL
    """)

    con.unregister("prod_raw")

    print("[3/4] Creando vista vw_investigador_x_produccion...")
    con.execute("DROP VIEW IF EXISTS vw_investigador_x_produccion")
    con.execute("""
        CREATE VIEW vw_investigador_x_produccion AS
        SELECT
            f.id_persona_pd,
            f.id_convocatoria,
            f.id_producto_pd,
            f.cod_grupo_gr,
            f.nme_categoria_pd,
            f.nme_tipo_medicion_pd,
            f.ano_convo_int,
            fc.id_clas_pr,
            fc.id_area_con_pr,
            fc.edad_anos_pr,
            (fc.id_persona_pr IS NOT NULL) AS es_reconocido
        FROM fact_produccion f
        LEFT JOIN fact_clasificacion fc
               ON f.id_persona_pd = fc.id_persona_pr
              AND f.id_convocatoria = fc.id_convocatoria
    """)

    print("[4/4] Validación tablas creadas:")
    for tabla in ("fact_produccion", "dim_producto", "dim_grupo"):
        n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"      {tabla:25s} → {n:>10,} filas")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"No existe {DB_PATH}. Ejecute primero: python scripts/sprint2_duckdb.py"
        )

    con = duckdb.connect(str(DB_PATH))
    construir_tablas(con)

    print("\n--- Consultas de validación ---\n")
    lineas = [f"Modelo extendido — Sprint 5 (Producción)\n{'='*55}\n"]
    for nombre, sql in CONSULTAS_VALIDACION.items():
        sep = f"\n{'-'*55}\n{nombre}\n{'-'*55}"
        print(sep)
        df = con.execute(sql).fetchdf()
        print(df.to_string(index=False))
        lineas.append(sep)
        lineas.append(df.to_string(index=False))

    reporte = EVIDENCIAS / "duckdb_resumen_sprint5.txt"
    reporte.write_text("\n".join(lineas), encoding="utf-8")
    con.close()
    print(f"\nDB     : {DB_PATH.relative_to(ROOT)}")
    print(f"Reporte: {reporte.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
