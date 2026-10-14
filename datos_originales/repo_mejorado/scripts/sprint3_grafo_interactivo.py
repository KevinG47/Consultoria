"""
Sprint 3 — Visualizacion de grafo interactivo (Issue #16)

Genera HTMLs interactivos con Pyvis del grafo de co-filiacion institucional.

Uso:
    python scripts/sprint3_grafo_interactivo.py

Salidas:
    hallazgos/sprint3_grafo_completo.html      (498 nodos)
    hallazgos/sprint3_grafo_filtrado.html      (146 nodos, grado >= 2)
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ingesta import cargar_consolidado
from Transformacion import transformar
from analisis.redes import (
    construir_pares,
    construir_grafo,
    subgrafo_grado_minimo,
    generar_html_pyvis,
    metricas_grafo,
)

HALLAZGOS = ROOT / "hallazgos"
HALLAZGOS.mkdir(exist_ok=True)


def main() -> None:
    print("[1/4] Cargando datos...")
    df = transformar(cargar_consolidado())

    print("[2/4] Construyendo grafo...")
    pares = construir_pares(df)
    G_completo = construir_grafo(pares)
    G_filtrado = subgrafo_grado_minimo(G_completo, grado_min=2)

    m_c = metricas_grafo(G_completo)
    m_f = metricas_grafo(G_filtrado)
    print(f"      Grafo completo : {m_c['n_nodos']} nodos, {m_c['n_aristas']} aristas")
    print(f"      Grafo filtrado : {m_f['n_nodos']} nodos, {m_f['n_aristas']} aristas (grado >= 2)")

    print("[3/4] Generando HTML grafo completo...")
    ruta_completo = HALLAZGOS / "sprint3_grafo_completo.html"
    generar_html_pyvis(
        G_completo,
        ruta_completo,
        titulo="Co-filiacion institucional — Grafo completo (2019)",
    )
    print(f"      Guardado: {ruta_completo.relative_to(ROOT)}")

    print("[4/4] Generando HTML grafo filtrado (grado >= 2)...")
    ruta_filtrado = HALLAZGOS / "sprint3_grafo_filtrado.html"
    generar_html_pyvis(
        G_filtrado,
        ruta_filtrado,
        titulo="Co-filiacion institucional — Instituciones con multiples enlaces (2019)",
    )
    print(f"      Guardado: {ruta_filtrado.relative_to(ROOT)}")

    print("\nAbrir en navegador:")
    print(f"  {ruta_completo}")
    print(f"  {ruta_filtrado}")


if __name__ == "__main__":
    main()