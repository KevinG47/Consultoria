"""
Sprint 2 — Modelo dimensional en DuckDB (Issue #14)

Construye el modelo estrella a partir del dataset transformado y lo persiste
en datos/processed/observatorio.duckdb. Ejecuta un conjunto de consultas de
validación para verificar integridad referencial y calidad del modelo.

Esquema estrella:
    dim_convocatoria, dim_investigador, dim_categoria, dim_area,
    dim_territorio, dim_formacion, dim_institucion
    → fact_clasificacion
    → bridge_hecho_institucion  (N:N con dim_institucion)

Uso:
    python scripts/sprint2_duckdb.py

Salidas:
    datos/processed/observatorio.duckdb
    evidencias/duckdb_resumen_modelo.txt
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ingesta import cargar_consolidado
from Transformacion import transformar
from modelo.dimensional import cargar_en_duckdb, resumen_modelo, DB_PATH

EVIDENCIAS = ROOT / "evidencias"
EVIDENCIAS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Consultas de validación
# ---------------------------------------------------------------------------

CONSULTAS = {
    "investigadores_por_convocatoria": """
        SELECT c.ano_convo_int, COUNT(*) AS n_registros,
               COUNT(DISTINCT f.id_persona_pr) AS n_investigadores
        FROM fact_clasificacion f
        JOIN dim_convocatoria c USING (id_convocatoria)
        GROUP BY c.ano_convo_int
        ORDER BY c.ano_convo_int
    """,
    "distribucion_categorias": """
        SELECT cat.nme_clasificacion_pr, cat.orden_clas_pr,
               COUNT(*) AS n_registros
        FROM fact_clasificacion f
        JOIN dim_categoria cat USING (id_clas_pr)
        GROUP BY cat.nme_clasificacion_pr, cat.orden_clas_pr
        ORDER BY cat.orden_clas_pr
    """,
    "top10_instituciones": """
        SELECT i.nme_institucion, COUNT(*) AS apariciones
        FROM bridge_hecho_institucion b
        JOIN dim_institucion i USING (sk_institucion)
        GROUP BY i.nme_institucion
        ORDER BY apariciones DESC
        LIMIT 10
    """,
    "investigadores_por_gran_area": """
        SELECT a.nme_gran_area_pr, COUNT(DISTINCT f.id_persona_pr) AS n_investigadores
        FROM fact_clasificacion f
        JOIN dim_area a USING (id_area_con_pr)
        GROUP BY a.nme_gran_area_pr
        ORDER BY n_investigadores DESC
    """,
    "concentracion_bogota_medellin_cali": """
        SELECT t.nme_municipio_res_pr, COUNT(*) AS n_registros,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
        FROM fact_clasificacion f
        JOIN dim_territorio t USING (sk_territorio)
        WHERE t.nme_municipio_res_pr ILIKE '%bogot%'
           OR t.nme_municipio_res_pr ILIKE '%medell%'
           OR t.nme_municipio_res_pr ILIKE 'cali'
        GROUP BY t.nme_municipio_res_pr
        ORDER BY n_registros DESC
    """,
    "edad_promedio_por_categoria_y_anio": """
        SELECT c.ano_convo_int, cat.categoria_normalizada,
               ROUND(AVG(f.edad_anos_pr), 1) AS edad_promedio,
               COUNT(*) AS n
        FROM fact_clasificacion f
        JOIN dim_convocatoria c USING (id_convocatoria)
        JOIN dim_categoria cat USING (id_clas_pr)
        WHERE f.edad_anos_pr BETWEEN 18 AND 100
        GROUP BY c.ano_convo_int, cat.categoria_normalizada, cat.orden_normalizado
        ORDER BY c.ano_convo_int, cat.orden_normalizado
    """,
}


def main() -> None:
    print("[1/3] Cargando y transformando datos...")
    df = transformar(cargar_consolidado())
    print(f"      Shape: {df.shape}")

    print("\n[2/3] Construyendo modelo estrella en DuckDB...")
    con = cargar_en_duckdb(df, path=DB_PATH, verbose=True)
    resumen_modelo(con)

    print("\n[3/3] Ejecutando consultas de validacion...\n")
    lineas_reporte = [f"Modelo estrella — observatorio.duckdb\n{'='*50}\n"]

    for nombre, sql in CONSULTAS.items():
        resultado = con.execute(sql).fetchdf()
        separador = f"\n{'-'*50}\n{nombre}\n{'-'*50}"
        print(separador)
        print(resultado.to_string(index=False))
        lineas_reporte.append(separador)
        lineas_reporte.append(resultado.to_string(index=False))

    # Guardar reporte de texto
    reporte_path = EVIDENCIAS / "duckdb_resumen_modelo.txt"
    reporte_path.write_text("\n".join(lineas_reporte), encoding="utf-8")

    con.close()
    print(f"\nBase de datos : {DB_PATH.relative_to(ROOT)}")
    print(f"Reporte       : {reporte_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
