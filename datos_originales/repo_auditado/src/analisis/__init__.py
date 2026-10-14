"""
Paquete de análisis — Observatorio MinCiencias.
"""
from .genero import pct_femenino_por_area, tabla_pivot_pct_femenino, brecha_genero, evolucion_pct_femenino
from .territorial import hhi, hhi_por_convocatoria, top_territorios, tabla_cuotas
from .redes import (
    construir_pares, construir_grafo, metricas_grafo,
    tabla_nodos, tabla_aristas, metricas_por_convocatoria,
    subgrafo_grado_minimo, generar_html_pyvis, normalizar_institucion,
)
from .diversidad import (
    cobertura_por_convocatoria, distribucion_categoria, comparar_dane,
    interseccional_genero_etnia, categoria_por_minoria, DANE_REFERENCIA,
)
from .longitudinal import (
    construir_panel,
    comparar_periodo,
    resumen_tracking,
    tracking_por_categoria,
    tracking_todos_periodos,
    tasa_retencion_por_periodo,
    matriz_transicion,
    matrices_todos_periodos,
)
from .produccion import (
    normalizar_produccion,
    cobertura_reconocidos,
    cobertura_autores_unicos,
    productividad_por_categoria,
    productividad_por_genero_area,
    brecha_productividad_genero,
    productividad_territorial,
    mix_tipologias,
    tipologias_por_categoria,
    reconocidos_sin_produccion,
)

__all__ = [
    "construir_pares",
    "construir_grafo",
    "metricas_grafo",
    "tabla_nodos",
    "tabla_aristas",
    "metricas_por_convocatoria",
    "subgrafo_grado_minimo",
    "generar_html_pyvis",
    "normalizar_institucion",
    "cobertura_por_convocatoria",
    "distribucion_categoria",
    "comparar_dane",
    "interseccional_genero_etnia",
    "categoria_por_minoria",
    "DANE_REFERENCIA",
    "pct_femenino_por_area",
    "tabla_pivot_pct_femenino",
    "brecha_genero",
    "evolucion_pct_femenino",
    "hhi",
    "hhi_por_convocatoria",
    "top_territorios",
    "tabla_cuotas",
    "construir_panel",
    "comparar_periodo",
    "resumen_tracking",
    "tracking_por_categoria",
    "tracking_todos_periodos",
    "tasa_retencion_por_periodo",
    "matriz_transicion",
    "matrices_todos_periodos",
    "normalizar_produccion",
    "cobertura_reconocidos",
    "cobertura_autores_unicos",
    "productividad_por_categoria",
    "productividad_por_genero_area",
    "brecha_productividad_genero",
    "productividad_territorial",
    "mix_tipologias",
    "tipologias_por_categoria",
    "reconocidos_sin_produccion",
]
