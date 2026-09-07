# -*- coding: utf-8 -*-
"""Verificacion empirica de los hallazgos estrella + evidencias."""
import pathlib, sys, warnings
warnings.filterwarnings("ignore")

REPO = pathlib.Path(r"C:\Users\InfoPersonal\OneDrive - Universidad Santo Tomás\Escritorio\consultoria\Observatorio_Ministerio_de_Ciencias_Grupo8")
sys.path.insert(0, str(REPO / "src"))

import pandas as pd

print("=" * 70)
print("A) BUG HHI dashboard: hhi_por_convocatoria().reset_index() + columns=['Año','HHI']")
from analisis.territorial import hhi_por_convocatoria
df = pd.DataFrame({
    "ANO_CONVO_INT": [2013, 2013, 2013, 2015, 2015],
    "NME_DEPARTAMENTO_RES_PR": ["BOGOTA", "BOGOTA", "ANTIOQUIA", "VALLE", "BOGOTA"],
})
hhi_df = hhi_por_convocatoria(df, col_geo="NME_DEPARTAMENTO_RES_PR")
print("   columnas de hhi_por_convocatoria:", list(hhi_df.columns))
hhi_df2 = hhi_df.reset_index()
print("   columnas tras .reset_index():", list(hhi_df2.columns), "-> n cols:", hhi_df2.shape[1])
try:
    hhi_df2.columns = ["Año", "HHI"]
    print("   assignment OK (NO ValueError)")
except ValueError as e:
    print(f"   ValueError CONFIRMADO: {e}")

print("=" * 70)
print("B) redes.py construir_pares con 3+ afiliaciones")
from analisis.redes import construir_pares
dfr = pd.DataFrame({
    "ID_PERSONA_PR": [1],
    "ANO_CONVO_INT": [2021],
    "INST_FILIA": ["UNAL Bogota | UNAL Medellin | EAFIT"],
})
pares = construir_pares(dfr, normalizar=False)
print("   pares resultantes para 'A|B|C':")
print(pares.to_string(index=False))
print("   -> se pierden combinaciones (A,C) y (B,C)?", "SÍ" if len(pares) < 3 else "NO")

print("=" * 70)
print("C) diversidad.py:145 KeyError si ningun grupo tiene mujeres")
from analisis.diversidad import interseccional_genero_etnia
dfd = pd.DataFrame({
    "TXT_GRUPO_ETNICO": ["INDIGENA", "INDIGENA", "AFROCOLOMBIANO"],
    "NME_GENERO_PR": ["MASCULINO", "MASCULINO", "MASCULINO"],  # nadie femenino
})
try:
    r = interseccional_genero_etnia(dfd)
    print("   sin KeyError; resultado:")
    print(r.to_string(index=False))
except KeyError as e:
    print(f"   KeyError CONFIRMADO: {e}")

print("=" * 70)
print("D) comparar_dane: comentario vs codigo (NINGUN GRUPO ETNICO)")
src = (REPO / "src" / "analisis" / "diversidad.py").read_text(encoding="utf-8").splitlines()
print(f"   linea 78: {src[77]}")
print(f"   linea 79: {src[78]}")
# simulacion del efecto
dfc = pd.DataFrame({
    "TXT_GRUPO_ETNICO": ["NINGUN GRUPO ETNICO", "NINGUN GRUPO ETNICO", "INDIGENA", "NO DISPONIBLE"],
    "TXT_POBLACION_DISCA": ["NINGUNA"] * 4,
    "ID_VICTIMA_CONFLICTO": ["NO"] * 4,
})
etnia = dfc[dfc["TXT_GRUPO_ETNICO"] != "NO DISPONIBLE"]
print(f"   n_etnia_resp (denominador) incluye NINGUN GRUPO ETNICO: {len(etnia)} filas (3)")
print(f"   -> si se excluyera NINGUN GRUPO ETNICO el denominador seria {len(etnia[etnia['TXT_GRUPO_ETNICO'] != 'NINGUN GRUPO ETNICO'])}")

print("=" * 70)
print("E) Evidencias y artefactos declarados")
checks = [
    REPO / "evidencias" / "duckdb_resumen_modelo.txt",
    REPO / "evidencias" / "territorial_hhi_por_convocatoria.csv",
    REPO / "evidencias" / "territorial_hhi_region_por_convocatoria.csv",
    REPO / "evidencias" / "territorial_cuotas_departamento.csv",
    REPO / "evidencias" / "genero_pct_femenino_por_gran_area.csv",
    REPO / "evidencias" / "genero_tabla_pivot_gran_area.csv",
    REPO / "evidencias" / "genero_brecha_por_gran_area.csv",
    REPO / "evidencias" / "genero_pct_femenino_por_area.csv",
    REPO / "evidencias" / "diversidad_cobertura_por_convocatoria.csv",
    REPO / "evidencias" / "diversidad_comparacion_dane.csv",
    REPO / "evidencias" / "diversidad_interseccional_genero_etnia.csv",
    REPO / "evidencias" / "diversidad_categorias_por_etnia.csv",
    REPO / "evidencias" / "redes_pares_cofiliacion.csv",
    REPO / "evidencias" / "redes_nodos_global.csv",
    REPO / "evidencias" / "redes_aristas_global.csv",
    REPO / "evidencias" / "redes_metricas_por_convocatoria.csv",
    REPO / "evidencias" / "calidad_atipicos_edad.csv",
    REPO / "evidencias" / "calidad_comparacion.csv",
    REPO / "evidencias" / "calidad_resumen.json",
    REPO / "evidencias" / "tabla_maestra_ies.csv",
    REPO / "evidencias" / "geografia_resumen_por_dpto_residencia.csv",
    REPO / "evidencias" / "geografia_top_flujos.csv",
    REPO / "evidencias" / "ocde_volumen_por_area.csv",
    REPO / "evidencias" / "ocde_productividad_por_area.csv",
    REPO / "evidencias" / "ocde_composicion_por_area.csv",
    REPO / "evidencias" / "mapping_inst_filia_to_ies.csv",
    REPO / "hallazgos" / "sprint3_grafo_completo.html",
    REPO / "hallazgos" / "sprint3_grafo_filtrado.html",
    REPO / "artifacts" / "sprint2_territorial" / "fig01_top_departamentos.png",
    REPO / "artifacts" / "sprint2_territorial" / "fig02_hhi_evolucion.png",
    REPO / "artifacts" / "sprint2_territorial" / "fig03_heatmap_cuotas.png",
    REPO / "artifacts" / "sprint2_genero_ocde" / "fig01_barras_pct_femenino.png",
    REPO / "artifacts" / "sprint2_genero_ocde" / "fig02_heatmap_pct_femenino.png",
    REPO / "artifacts" / "sprint2_genero_ocde" / "fig03_lineas_evolucion.png",
    REPO / "artifacts" / "sprint2_genero_ocde" / "fig04_brecha_genero.png",
    REPO / "artifacts" / "sprint2_transiciones" / "fig01_heatmaps_ext.png",
    REPO / "artifacts" / "sprint2_transiciones" / "fig02_heatmaps_obs.png",
    REPO / "artifacts" / "sprint4_diversidad" / "fig01.png",
    REPO / "datos" / "processed" / "observatorio.duckdb",
]
n_ok = 0
for p in checks:
    ok = p.exists()
    n_ok += ok
    if not ok:
        print(f"   FALTA: {p.relative_to(REPO)}")
print(f"   presentes: {n_ok}/{len(checks)}")

print("=" * 70)
print("F) datos/raw contenido y .venv")
raw = list((REPO / "datos" / "raw").iterdir()) if (REPO / "datos" / "raw").exists() else []
print("   datos/raw:", [p.name for p in raw])
venv_sp = REPO / ".venv" / "Lib" / "site-packages"
if venv_sp.exists():
    names = [p.name for p in venv_sp.iterdir()]
    print(f"   .venv site-packages: {len(names)} paquetes | muestra: {sorted(names)[:10]}")
else:
    print("   .venv site-packages NO existe")

print("=" * 70)
print("G) pyproject.toml y requirements.txt")
pp = (REPO / "pyproject.toml").read_text(encoding="utf-8") if (REPO / "pyproject.toml").exists() else ""
req = (REPO / "requirements.txt").read_text(encoding="utf-8") if (REPO / "requirements.txt").exists() else ""
for dep in ["duckdb", "networkx", "pyvis", "openpyxl", "pyyaml", "streamlit", "nbformat", "seaborn"]:
    in_pp = dep in pp
    in_req = dep in req
    print(f"   {dep:12s} pyproject={in_pp} requirements={in_req}")
