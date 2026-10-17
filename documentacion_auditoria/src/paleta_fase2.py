# -*- coding: utf-8 -*-
"""
paleta_fase2.py
===============

**Una sola paleta institucional** para todos los artefactos de la Fase 2.

Existe para que el panel (`generar_dashboard_fase2.py`) y el mapa de flujos
(`mapa_migracion.py`) no puedan divergir en un tono: los dos importan de aquí.
Antes de este módulo la paleta vivía dentro del panel y el mapa tenía que
repetirla a mano.

Regla de color del proyecto:

  - barras y líneas → azul primario; con dos series, azul + dorado;
  - series de contexto o sin señal → gris;
  - rojo → SOLO excepciones negativas declaradas (falsos positivos, umbrales
    superados). Nunca decorativo y nunca más de cuatro veces en un panel.

Degradado y verde están prohibidos en este proyecto: no aparecen aquí.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

PALETA = {
    "primario": "#1E3780",
    "primario_oscuro": "#0F1F4D",
    "secundario": "#4A6BA8",
    "claro": "#7BA7D0",
    "dorado": "#B7871E",
    "dorado_claro": "#D4A84A",
    "gris_oscuro": "#334155",
    "gris_medio": "#64748B",
    "gris_claro": "#CBD5E1",
    "fondo": "#F8FAFC",
    "texto": "#1E293B",
}
ALERTA = "#B91C1C"        # solo excepciones negativas
BLANCO = "#FFFFFF"
TENUE = "#EAF0F9"         # azul tenue de fondos y tablas

ESCALA_AZUL = [[0.0, "#EAF0F9"], [0.35, PALETA["claro"]],
               [0.7, PALETA["secundario"]], [1.0, PALETA["primario"]]]

FUENTE_TXT = ('Segoe UI, Montserrat, Roboto, system-ui, -apple-system, '
              'Arial, sans-serif')
NOMBRE_TEMPLATE = "usta_institucional"

COLOR_CATEGORIA = {
    "Investigador Junior": PALETA["claro"],
    "Investigador Asociado": PALETA["secundario"],
    "Investigador Sénior": PALETA["primario"],
    "Investigador Emérito": PALETA["dorado"],
}

CONFIG_PLOTLY = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "filename": "fase2_minciencias",
                             "scale": 2},
}

COLORES_PERMITIDOS = frozenset(
    [v.lower() for v in PALETA.values()] + [ALERTA.lower(), BLANCO.lower(),
                                            TENUE.lower()])


# --------------------------------------------------------------- formato comun
# El mismo formato de cifras en el panel y en el mapa: miles con espacio fino
# (U+202F) y coma decimal, como el resto de los documentos de la Fase 2.
def miles(n) -> str:
    """Entero con separador de miles: 28 950."""
    return f"{int(n):,}".replace(",", " ")


def num(x: float, dec: int = 2) -> str:
    """Número con coma decimal y espacio fino de miles: 65,55 · 28 950,00."""
    return f"{x:,.{dec}f}".replace(",", "\u202f").replace(".", ",")


def pct(x: float, dec: int = 2) -> str:
    return num(x, dec) + " %"


def registrar_template() -> None:
    """Registra el template institucional y lo deja como predeterminado."""
    pio.templates[NOMBRE_TEMPLATE] = go.layout.Template(layout=go.Layout(
        font=dict(family=FUENTE_TXT, color=PALETA["texto"], size=12),
        paper_bgcolor=PALETA["fondo"],
        plot_bgcolor=BLANCO,
        colorway=[PALETA["primario"], PALETA["dorado"], PALETA["secundario"],
                  PALETA["dorado_claro"], PALETA["claro"], PALETA["gris_medio"]],
        xaxis=dict(gridcolor=PALETA["gris_claro"],
                   zerolinecolor=PALETA["gris_claro"], linecolor=PALETA["gris_claro"]),
        yaxis=dict(gridcolor=PALETA["gris_claro"],
                   zerolinecolor=PALETA["gris_claro"], linecolor=PALETA["gris_claro"]),
        hoverlabel=dict(font=dict(family=FUENTE_TXT, size=13), bgcolor=BLANCO,
                        bordercolor=PALETA["gris_claro"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
        separators=",.",
    ))
    pio.templates.default = NOMBRE_TEMPLATE
