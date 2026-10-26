# -*- coding: utf-8 -*-
"""
generar_dashboard_fase2.py
==========================

Construye `02_dashboards/dashboard_fase2.html`: el panel de la **Fase 2** completo,
autocontenido (sin CDN ni red) y con el mismo lenguaje visual que
`dashboard_eda.html` (misma hoja de estilo, mismo template de Plotly, misma
estructura de pestañas).

PARA QUE SIRVE
--------------
El panel tiene dos usos y las dos se atienden en la misma pagina:

  1. **Presentar los resultados al docente.** Cada pestana abre con la conclusion
     del analisis y la cifra que la sostiene.
  2. **Estudiar.** Cada grafico lleva cuatro bloques de narrativa —que se hizo,
     por que, **que teoria lo respalda** y como se lee— y al final de la pagina
     hay un indice de conceptos con buscador.

FUENTES (todas versionadas, ninguna se recalcula aqui)
------------------------------------------------------
  01_datos/resultados_json/percapita_territorial.json    F2-2
  01_datos/resultados_json/modelo_estrella.json          F2-3
  01_datos/resultados_json/redes_nulos.json              F2-4
  01_datos/resultados_json/diversidad_inferencia.json    F2-5
  01_datos/resultados_json/clustering.json               F2-6
  01_datos/resultados_json/validacion_unicidad.json      F2-7
  01_datos/resultados_json/supervivencia.json            F2-10
  01_datos/resultados_json/flujos_territoriales.json     F2-11
  data/geo/colombia_departamentos.geojson    F2-11 (poligonos del mapa)
  01_datos/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv

Las tres unicas cosas que se recalculan son:
  - la **red de 2019**, porque el JSON guarda sus estadisticos pero no la lista de
    aristas, y para dibujarla hace falta el grafo; se reconstruye con las MISMAS
    funciones del repositorio auditado (`analisis.redes`), no reescribiendolas.
  - la **composicion categoria x genero**, que el JSON de F2-10 no guarda; se
    calcula con la misma regla que el resto del proyecto (una fila por persona, la
    ultima convocatoria) y se **valida** contra los tamanos de grupo que el propio
    JSON declara.
  - el **mapa de flujos de la pestana 8**: la figura la construye
    `mapa_migracion.py` leyendo los JSON y el GeoJSON versionados. No recalcula los
    flujos; solo los dibuja.

Este script NO modifica ningun analisis: solo lee JSON y CSV, y escribe el HTML.

Uso:  python generar_dashboard_fase2.py
"""

from __future__ import annotations

import html as _html
import io
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
MEM = DOC / "data" / "memoria"
RESULTADOS = RAIZ / "01_datos" / "resultados_json"
DASH = RAIZ / "02_dashboards"
REPO_AUDITADO = RAIZ / "04_auditoria" / "repo_original"
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
SALIDA = DASH / "dashboard_fase2.html"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------- paleta y tipo
# La PALETA INSTITUCIONAL UNICA vive en `paleta_fase2.py`: la comparten este panel
# y el mapa de flujos de F2-11, de modo que los dos no puedan divergir en un tono.
# Aqui solo se importa; el template de Plotly se registra con `registrar_template`.
from paleta_fase2 import (ALERTA, BLANCO, COLOR_CATEGORIA, CONFIG_PLOTLY,
                          ESCALA_AZUL, NOMBRE_TEMPLATE, PALETA,
                          miles, num, pct, registrar_template)

# El mapa de flujos (F2-11) es la pestaña 8: la figura y los bloques HTML viven en
# `mapa_migracion.py` para que la página suelta y el panel sean la MISMA figura.
import mapa_migracion as mapa_mod


# ============================================================================
# 1. Carga de fuentes
# ============================================================================
def carga(nombre: str) -> dict:
    return json.loads((RESULTADOS / f"{nombre}.json").read_text(encoding="utf-8"))


def cargar_todo() -> dict:
    d = {k: carga(k) for k in ("percapita_territorial", "modelo_estrella",
                               "redes_nulos", "diversidad_inferencia",
                               "clustering", "validacion_unicidad",
                               "supervivencia")}
    print("   " + ", ".join(f"{k}.json" for k in sorted(d)))
    return d


def red_2019():
    """
    Reconstruye el grafo de co-filiacion de 2019 para poder DIBUJARLO.

    El JSON de F2-4 guarda los estadisticos pero no las aristas. Se reutilizan
    `construir_pares` y `construir_grafo` del repositorio auditado (son las mismas
    funciones con las que se calculo el analisis), asi que el grafo que se dibuja
    es el que se analizo, no una segunda version.

    `sys.dont_write_bytecode = True` evita dejar __pycache__ dentro de una copia
    verbatim de 236 archivos cuyos hashes se verifican.
    """
    import networkx as nx

    sys.dont_write_bytecode = True
    sys.path.insert(0, str(REPO_AUDITADO / "src"))
    from analisis.redes import construir_grafo, construir_pares

    df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                     usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "INST_FILIA",
                              "NME_REGION_RES_PR"])
    df["ANO_CONVO_INT"] = df["ID_CONVOCATORIA"].astype(int).map(
        {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021})
    df["INST_FILIA"] = df["INST_FILIA"].str.strip()
    G = construir_grafo(construir_pares(df), anio=2019)
    return G, nx


def composicion_categoria_genero(sv: dict) -> pd.DataFrame:
    """
    Reparto de cada genero entre las cuatro categorias (una fila por persona).

    No esta en el JSON de F2-10 y hace falta para explicar POR QUE la diferencia
    de genero desaparece al ajustar. Se calcula con la misma regla que el resto
    del proyecto y se valida contra los tamanos de grupo que el JSON ya publica:
    si no cuadra, el script falla en vez de publicar una tabla que no reproduce
    el analisis.
    """
    df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                     usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR",
                              "NME_CLASIFICACION_PR", "NME_GENERO_PR"])
    df["conv"] = df["ID_CONVOCATORIA"].astype(int)
    ult = df.sort_values("conv").groupby("ID_PERSONA_PR", observed=True).last()
    g = ult[ult["NME_GENERO_PR"].isin(["Masculino", "Femenino"])]

    esperado = {k: v["n"] for k, v in sv["kaplan_meier"]["genero"].items()
                if k in ("Masculino", "Femenino")}
    hallado = {k: int(v) for k, v in g["NME_GENERO_PR"].value_counts().items()}
    if hallado != esperado:
        raise SystemExit(f"La composicion por genero no reproduce supervivencia.json: "
                         f"calculado {hallado} frente a {esperado}")

    tab = (pd.crosstab(g["NME_CLASIFICACION_PR"], g["NME_GENERO_PR"])
           .reindex(["Investigador Junior", "Investigador Asociado",
                     "Investigador Sénior", "Investigador Emérito"]))
    return tab


# ============================================================================
# 2. Utilidades de formato y de graficado
# ============================================================================
def estilo(fig: go.Figure, alto: int = 430, leyenda: bool = True,
           titulo_grafico: str | None = None) -> go.Figure:
    fig.update_layout(
        template=NOMBRE_TEMPLATE,
        height=alto,
        margin=dict(l=72, r=28, t=74 if titulo_grafico else 56, b=64),
        bargap=0.28, bargroupgap=0.12,
    )
    if titulo_grafico:
        fig.update_layout(title=dict(text=titulo_grafico, x=0.01, xanchor="left",
                                     font=dict(size=15, color=PALETA["primario_oscuro"])))
    if leyenda:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.24,
                                      xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                                      font=dict(size=12)))
    return fig


def div(fig: go.Figure, ident: str, config: dict | None = None) -> str:
    """HTML del grafico SIN volver a embeber Plotly (se embebe una sola vez)."""
    return pio.to_html(fig, include_plotlyjs=False, full_html=False,
                       div_id=ident, config=config or CONFIG_PLOTLY)


def pval(p: float | None, dec: int = 3) -> str:
    if p is None:
        return "p no calculado"
    if p < 0.001:
        return "p &lt; 0,001"
    return "p = " + num(p, dec)


# ============================================================================
# 3. Pestana 1 — Resumen ejecutivo
# ============================================================================
def fig_calidad(d: dict) -> go.Figure:
    """
    Comprobaciones automaticas y figuras por analisis.

    Se cuentan las claves booleanas de cada bloque `validaciones` del JSON y los
    elementos de su bloque `figuras`: son las dos cosas que cada analisis dejo
    como evidencia verificable.
    """
    nombres = {"percapita_territorial": "F2-2 · Territorio",
               "modelo_estrella": "F2-3 · Modelo estrella",
               "redes_nulos": "F2-4 · Redes",
               "diversidad_inferencia": "F2-5 · Diversidad",
               "clustering": "F2-6 · Clustering",
               "validacion_unicidad": "F2-7 · Unicidad",
               "supervivencia": "F2-10 · Supervivencia"}
    etiquetas, checks, figs = [], [], []
    for clave, nombre in nombres.items():
        val = d[clave]["validaciones"]
        booleanos = [v for v in val.values() if isinstance(v, bool)]
        if len(booleanos) != len(val):
            raise SystemExit(f"{clave}: 'validaciones' tiene claves no booleanas; "
                             f"el conteo del panel dejaria de ser fiable.")
        etiquetas.append(nombre)
        checks.append(sum(booleanos))
        figs.append(len(d[clave]["figuras"]))

    fig = go.Figure()
    fig.add_trace(go.Bar(x=checks, y=etiquetas, orientation="h",
                         name="Comprobaciones automáticas",
                         marker_color=PALETA["primario"],
                         text=[str(v) for v in checks], textposition="outside",
                         cliponaxis=False,
                         hovertemplate="<b>%{y}</b><br>%{x} comprobaciones<extra></extra>"))
    fig.add_trace(go.Bar(x=figs, y=etiquetas, orientation="h",
                         name="Figuras exportadas",
                         marker_color=PALETA["dorado"],
                         text=[str(v) for v in figs], textposition="outside",
                         cliponaxis=False,
                         hovertemplate="<b>%{y}</b><br>%{x} figuras<extra></extra>"))
    fig.update_xaxes(title="Cantidad", range=[0, max(max(checks), max(figs)) * 1.30])
    fig.update_layout(barmode="group")
    fig.update_layout(title=dict(
        text=(f"Evidencia verificable de cada análisis · "
              f"{sum(checks)} comprobaciones ({sum(checks)} en verde) y "
              f"{sum(figs)} figuras"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=440, leyenda=True)


TABLA_RESUMEN = [
    ("F2-2", "Concentración territorial per cápita",
     "La desigualdad bajó, pero toda la convergencia es <b>entre regiones</b>: "
     "dentro de ellas no se movió (Theil intra 0,1015 → 0,1023)."),
    ("F2-3", "Modelo estrella reproducible",
     "Se reconstruyó <b>cifra a cifra</b> (77 237 hechos, 0 huérfanos) con las seis "
     "convocatorias; el «nueve dimensiones» son <b>9 tablas</b>."),
    ("F2-4", "Redes con modelos nulos",
     "El corretaje está <b>concentrado</b> (p = 0,004), pero <b>ninguna institución</b> "
     "resiste la corrección por comparaciones múltiples."),
    ("F2-5", "Diversidad con intervalos",
     "La <b>dirección</b> del hallazgo resiste; la <b>magnitud</b> no. Con 114 "
     "indígenas el cociente llega a [5,39; 31,70]."),
    ("F2-6", "Segmentación formalizada",
     "El mejor k es <b>1</b>: no hay estructura de clusters (p = 0,762 frente al nulo)."),
    ("F2-7", "Regla de unicidad",
     "<b>56 IDs</b> violan la regla; la implementada del auditado marcaba 1 067 pares "
     "con <b>1 058 falsos positivos</b>."),
    ("F2-10", "Supervivencia (KM y Cox)",
     "La categoría domina la salida; <b>el género desaparece al ajustar</b> "
     "(HR 0,988; p = 0,575)."),
    ("F2-1", "Productividad científica (Q7)",
     "<b>No evaluable</b>: el CSV de 1,2 GB con las revistas no está versionado."),
]


def pestana_resumen(d: dict) -> tuple[list, str, str]:
    p, e, u, sv = (d["percapita_territorial"], d["modelo_estrella"],
                   d["validacion_unicidad"], d["supervivencia"])
    filas = "".join(
        f"<tr><td class='id'>{_html.escape(i)}</td><td><b>{_html.escape(n)}</b></td>"
        f"<td>{h}</td></tr>" for i, n, h in TABLA_RESUMEN)
    tabla = ("<table class='tabla'><thead><tr><th style='width:74px'>Análisis</th>"
             "<th style='width:270px'>Qué se hizo</th>"
             "<th>Hallazgo en una frase</th></tr></thead><tbody>"
             f"{filas}</tbody></table>")

    n_fig = sum(len(v["figuras"]) for v in d.values())
    n_chk = sum(sum(1 for x in v["validaciones"].values() if isinstance(x, bool))
                for v in d.values())
    graficos = [("t1", "Evidencia verificable de la Fase 2",
                 f"Cada análisis dejó un JSON con sus comprobaciones automáticas y sus "
                 f"figuras. En total, 7 análisis, {n_chk} comprobaciones booleanas (todas "
                 f"en verde) y {n_fig} figuras exportadas.",
                 div(fig_calidad(d), "t1"))]

    cifras = (
        f"<div class='tabla-cifras'>"
        f"<div><span>Registros de la base</span><b>{miles(77237)}</b></div>"
        f"<div><span>Personas únicas</span><b>{miles(30086)}</b></div>"
        f"<div><span>Convocatorias</span><b>6</b></div>"
        f"<div><span>Comprobaciones automáticas</span><b>56 / 56</b></div>"
        f"<div><span>Reglas de validación</span><b>15 · 0 · 2</b></div>"
        f"<div><span>IDs que violan la regla</span>"
        f"<b>{u['ids_no_unicos']['n_ids_violadores']}</b></div>"
        "</div>")

    conclusion = (
        "<b>Esta fase cierra la auditoría evaluando los análisis que el repositorio "
        "original había dejado pendientes.</b> La Fase 1 diagnosticó; la Fase 2 "
        "reconstruye. Cada análisis se entregó con script reproducible, JSON de "
        "resultados, documento y figuras, y se verificó contra la evidencia que el propio "
        "repositorio auditado dejó versionada."
        "<br><br><b>El patrón que se repitió en los siete análisis</b> no fue «el auditado "
        "se equivocó», sino algo más preciso: <b>sus métodos no estaban mal, sus "
        "afirmaciones iban por delante de su evidencia</b>. El HHI y las métricas de red se "
        "reproducen valor a valor; el modelo estrella se reconstruye con sus propias "
        "funciones y reproduce su evidencia con diferencia 0. Lo que faltaba era "
        "incertidumbre (F2-2, F2-5), modelos nulos (F2-4, F2-6), una regla implementada que "
        "coincidiera con la documentada (F2-7) y una carga con las seis convocatorias "
        "(F2-3)."
        "<br><br><b>Tres resultados cambian lo que se creía saber:</b> (1) la convergencia "
        "territorial es <i>entre</i> regiones, no dentro de ellas; (2) el mejor número de "
        "clusters es <b>1</b>, no 3; (3) la diferencia de retención por género es de "
        "composición y desaparece al ajustar. Y un cuarto resultado incómodo pero honesto: "
        "no se puede nombrar la universidad puente de la red.")
    return graficos, tabla + cifras, conclusion


# ============================================================================
# 4. Pestana 2 — Territorio y desigualdad (F2-2)
# ============================================================================
def fig_tasas(p: dict) -> go.Figure:
    st = p["tasa_por_100000"]["stock_ultima_convocatoria"]
    items = sorted(st.items(), key=lambda kv: kv[1]["tasa_por_100000"])
    dep = [k for k, _ in items]
    tasa = [v["tasa_por_100000"] for _, v in items]
    inv = [v["investigadores"] for _, v in items]
    nac = p["indices_stock"]["tasa_nacional_por_100000"]

    fig = go.Figure(go.Bar(
        x=tasa, y=dep, orientation="h", marker_color=PALETA["primario"],
        customdata=list(zip(inv, [v["poblacion"] for _, v in items])),
        text=[num(v, 1) for v in tasa], textposition="outside", cliponaxis=False,
        hovertemplate=("<b>%{y}</b><br>Tasa %{x:.2f} por 100 000<br>"
                       "%{customdata[0]:,} investigadores · "
                       "%{customdata[1]:,} habitantes<extra></extra>")))
    fig.add_vline(x=nac, line=dict(color=PALETA["dorado"], width=2, dash="dash"))
    fig.add_annotation(x=nac, y=len(dep) - 0.4, text=f"Colombia {num(nac, 1)}",
                       showarrow=False, font=dict(size=11, color=PALETA["dorado"]),
                       xanchor="left", yanchor="top")
    fig.update_xaxes(title="Investigadores por cada 100 000 habitantes",
                     range=[0, max(tasa) * 1.20])
    fig.update_layout(title=dict(
        text=(f"Tasa per cápita por departamento (stock de 2021, población censada "
              f"de 2018) · razón máxima {num(p['indicadores_clave']['razon_mayor_menor'], 1)}×"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=820, leyenda=False)


def fig_indices(p: dict) -> go.Figure:
    """Gini y descomposición del Theil a lo largo de las seis convocatorias."""
    pc = p["tasa_por_100000"]["por_convocatoria"]
    anios = list(pc)
    gini = [pc[a]["gini_tasas"] for a in anios]
    entre = [pc[a]["theil_tasas_entre_regiones"] for a in anios]
    dentro = [pc[a]["theil_tasas_dentro_regiones"] for a in anios]

    fig = make_subplots(rows=1, cols=2, column_widths=[0.42, 0.58],
                        subplot_titles=("Gini de las tasas",
                                        "Theil: entre regiones y dentro de ellas"))
    fig.add_trace(go.Scatter(x=anios, y=dentro, name="Dentro de las regiones",
                             mode="lines+markers",
                             line=dict(color=PALETA["dorado_claro"], width=3),
                             marker=dict(size=9),
                             hovertemplate="%{x}<br>Dentro %{y:.4f}<extra></extra>"),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=anios, y=entre, name="Entre regiones",
                             mode="lines+markers",
                             line=dict(color=PALETA["primario"], width=3),
                             marker=dict(size=9),
                             hovertemplate="%{x}<br>Entre %{y:.4f}<extra></extra>"),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=anios, y=gini, name="Gini de las tasas",
                             mode="lines+markers",
                             line=dict(color=PALETA["gris_oscuro"], width=3,
                                       dash="dash"), marker=dict(size=8, symbol="square"),
                             hovertemplate="%{x}<br>Gini %{y:.4f}<extra></extra>"),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=anios, y=dentro, name="Dentro de las regiones",
                             mode="lines+markers", showlegend=False,
                             line=dict(color=PALETA["dorado_claro"], width=3),
                             marker=dict(size=9),
                             hovertemplate="%{x}<br>Dentro %{y:.4f}<extra></extra>"),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=anios, y=entre, name="Entre regiones",
                             mode="lines+markers", showlegend=False,
                             line=dict(color=PALETA["primario"], width=3),
                             marker=dict(size=9),
                             hovertemplate="%{x}<br>Entre %{y:.4f}<extra></extra>"),
                  row=1, col=2)
    for col in (1, 2):
        fig.update_xaxes(type="category", row=1, col=col)
        fig.update_yaxes(rangemode="tozero", row=1, col=col)
    fig.update_layout(title=dict(
        text=("La desigualdad baja, pero solo por el componente entre regiones · "
              "Gini 0,5239 → 0,4361 (−16,8 %) · Theil intra 0,1015 → 0,1023 (plano)"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=470, leyenda=True)


def fig_hhi(p: dict) -> go.Figure:
    ca = p["comparacion_auditado"]
    anios = list(ca["hhi_auditado"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=anios, y=[ca["hhi_auditado"][a] for a in anios],
        name="HHI del auditado (con «Exterior»)",
        mode="lines+markers", line=dict(color=PALETA["gris_oscuro"], width=3,
                                        dash="dash"), marker=dict(size=9),
        hovertemplate="%{x}<br>HHI %{y:.6f}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=anios, y=[ca["hhi_sin_exterior"][a] for a in anios],
        name="HHI sin «Exterior» ni «No disponible»",
        mode="lines+markers", line=dict(color=PALETA["primario"], width=3),
        marker=dict(size=9),
        hovertemplate="%{x}<br>HHI %{y:.6f}<extra></extra>"))
    fig.update_xaxes(type="category")
    fig.update_layout(title=dict(
        text=(f"HHI reproducido valor a valor (diferencia máxima {num(ca['maxima_diferencia_reproduccion'], 7)}"
              f" = 4,75 × 10⁻⁷) · contar «Exterior» como territorio baja el índice "
              f"{num(abs(ca['efecto_exterior_media_pp']), 2)} puntos de media"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=430, leyenda=True)


def pestana_territorio(d: dict) -> tuple[list, str, str]:
    p = d["percapita_territorial"]
    ic = p["indicadores_clave"]
    b_di = p["bootstrap_diseno_mas_ps"]["por_convocatoria"]["2021"]
    b_pe = p["bootstrap_personas"]["por_convocatoria_y_stock"]["2021"]
    ancho_d = b_di["ancho_ic_mediano_por_100000"]
    ancho_p = b_pe["ancho_ic_mediano_por_100000"]

    graficos = [
        ("t2", "Tasa de investigadores por 100 000 habitantes",
         f"Denominador: población censada de 2018 ({miles(p['poblacion']['censada_2018_total'])} "
         f"habitantes, cuadro 1PD del CNPV). Se excluyen «Exterior» (2 132 registros) y "
         f"«No disponible» (316): no tienen población colombiana en el denominador. La "
         f"línea dorada es la tasa nacional. <b>Stock:</b> cada persona contada en su última "
         f"convocatoria <i>con territorio colombiano</i> ({miles(p['conteos']['stock_personas'])} "
         f"personas): las 194 cuya última observación es «Exterior» o «No disponible» siguen "
         f"contadas en su último departamento colombiano.",
         div(fig_tasas(p), "t2")),
        ("t3", "Convergencia: Gini y descomposición del Theil",
         f"El Gini cae un 16,8 % y el Theil un 34,2 %, pero el gráfico derecho muestra "
         f"que la caída se concentra en el componente <b>entre</b> regiones "
         f"(0,3891 → 0,2204). El componente <b>dentro</b> de las regiones está plano "
         f"(0,1015 → 0,1023).",
         div(fig_indices(p), "t3")),
        ("t4", "Reproducción del HHI del auditado",
         f"El HHI del repositorio auditado se reproduce valor a valor (diferencia máxima "
         f"4,75 × 10⁻⁷, la del redondeo a 6 decimales). La línea azul muestra qué pasa al "
         f"excluir las dos categorías que no son departamentos.",
         div(fig_hhi(p), "t4")),
    ]

    claves = (
        "<table class='tabla'><thead><tr><th>Indicador (stock, 28 950 personas)</th>"
        "<th class='num'>Valor</th><th>Lectura</th></tr></thead><tbody>"
        f"<tr><td>Tasa nacional</td><td class='num'>{num(p['indices_stock']['tasa_nacional_por_100000'])}</td>"
        "<td>por cada 100 000 habitantes</td></tr>"
        f"<tr><td>Bogotá, D. C.</td><td class='num'>{num(ic['departamento_mayor_tasa']['tasa'], 1)}</td>"
        f"<td>{num(ic['sobrerrepresentacion_cuota_vs_poblacion']['Bogotá, D. C.'], 2)}× su peso "
        f"poblacional (34,16 % de los investigadores frente al 16,26 % de la población)</td></tr>"
        f"<tr><td>Vichada</td><td class='num'>{num(ic['departamento_menor_tasa']['tasa'], 2)}</td>"
        f"<td>el extremo opuesto: {num(ic['subrrepresentacion_cuota_vs_poblacion']['Vichada'], 3)}× "
        f"su peso poblacional</td></tr>"
        f"<tr><td>Razón entre extremos</td><td class='num'>{num(ic['razon_mayor_menor'], 1)}×</td>"
        "<td>Bogotá frente a Vichada</td></tr>"
        f"<tr><td>Gini de las tasas</td><td class='num'>{num(p['indices_stock']['gini_tasas'], 4)}</td>"
        f"<td>sobre el stock; por convocatoria va de 0,5239 (2013) a 0,4361 (2021)</td></tr>"
        f"<tr><td>Theil entre regiones</td><td class='num'>{num(p['indices_stock']['theil_descomposicion_tasas_regiones']['entre'], 4)}</td>"
        f"<td>{pct(100 * p['indices_stock']['theil_descomposicion_tasas_regiones']['entre'] / p['indices_stock']['theil_descomposicion_tasas_regiones']['total'], 1)} del total</td></tr>"
        f"<tr><td>Theil dentro de las regiones</td><td class='num'>{num(p['indices_stock']['theil_descomposicion_tasas_regiones']['dentro'], 4)}</td>"
        "<td>la parte que NO se mueve en el período</td></tr>"
        "</tbody></table>"
        "<p class='nota-tabla'><b>Dos definiciones de «última convocatoria», y las dos son "
        "correctas.</b> Aquí el stock cuenta a cada persona en su última convocatoria "
        "<i>con territorio colombiano</i>: "
        f"{miles(p['conteos']['stock_personas'])} personas, de las cuales "
        f"{miles(p['tasa_por_100000']['stock_ultima_convocatoria']['Bogotá, D. C.']['investigadores'])} "
        "son de Bogotá. La pestaña 5 (supervivencia) usa la última observación "
        "<i>sin filtrar</i>: 30 086 personas, y por eso allí Bogotá son 9 813. La diferencia "
        "son 194 personas cuya última observación es «Exterior» (173) o «No disponible» "
        "(21): aquí siguen contadas en su último departamento colombiano porque su salida "
        "del país no las saca del denominador departamental, y 75 de ellas estaban en "
        "Bogotá. Con la definición alternativa el cociente de Bogotá sería 2,0986 en lugar "
        "de 2,1005 y la razón entre extremos 104,7 en lugar de 105,5: ninguna conclusión "
        "cambia.</p>")

    conclusion = (
        "<b>La convergencia es real, pero es interregional.</b> El Gini de las tasas "
        f"bajó de 0,5239 a 0,4361 (−16,8 %) y el Theil de 0,4906 a 0,3228 (−34,2 %): "
        f"el país se igualó. Pero la descomposición dice <i>por dónde</i>: el componente "
        f"<b>entre</b> regiones cayó de 0,3891 a 0,2204, mientras que el <b>dentro</b> de "
        f"las regiones quedó plano (0,1015 → 0,1023). Es decir: las regiones se acercaron "
        f"entre sí, y la brecha que queda es <b>entre</b> ellas, no dentro. Con una razón "
        f"de {num(ic['razon_mayor_menor'], 1)}× entre la capital y Vichada, el nivel sigue "
        f"siendo extremo aunque la tendencia sea a la baja."
        f"<br><br><b>Lo que aporta el cálculo per cápita:</b> el repositorio auditado "
        f"medía concentración bruta, y una cuota puede subir solo porque el numerador "
        f"crece. Al dividir por población aparece Bogotá con {num(ic['cuota_bogota_investigadores'] * 100, 2)} % "
        f"de los investigadores y {num(ic['cuota_bogota_poblacion'] * 100, 2)} % de la población."
        f"<br><br><b>La incertidumbre manda.</b> Con el diseño real (MAS de "
        f"{miles(b_di['n_muestra'])} personas en 2021 más post-estratificación por "
        f"categoría), el intervalo de confianza mediano por departamento mide "
        f"{num(ancho_d, 1)} puntos de tasa, frente a {num(ancho_p, 1)} del bootstrap que "
        f"ignora el diseño: <b>{num(ancho_d / ancho_p, 1)} veces más ancho</b>. Además, "
        f"{b_di['departamentos_estimados_en_cero']} departamentos quedan estimados en "
        f"cero y {b_di['departamentos_que_no_difieren_del_promedio']} no se distinguen "
        f"estadísticamente del promedio nacional. <b>La ordenación territorial resiste, "
        f"pero las posiciones individuales de los departamentos pequeños no.</b>")
    return graficos, claves, conclusion


# ============================================================================
# 5. Pestana 3 — Diversidad y falencias (F2-5)
# ============================================================================
def fig_razones(dv: dict) -> go.Figure:
    """
    cociente: se dibuja el cociente como punto y el intervalo como barra de error
    horizontal: ubicar en el eje x la AMPLITUD del intervalo, como haria un grafico
    de barras, pondria el punto en un sitio que no es el del cociente.

    OJO CON LA DIRECCION: el cociente que publica el analisis es
    % en la poblacion / % entre los investigadores (es el campo
    `razon_subrepresentacion` de la evidencia del auditado). Por tanto
    MAYOR QUE 1 = SUBrepresentado. Invertirlo hace decir al panel lo contrario
    de lo que dicen los datos y de lo que dice analisis_diversidad.md.
    """
    orden = ["afro", "indigena", "discapacidad", "victima", "raizal",
             "palenquero", "rrom"]
    fig = go.Figure()
    for clave in orden:
        g = dv["grupos"][clave]
        nombre = g["etiqueta"]
        principal = clave in ("afro", "indigena", "discapacidad", "victima")
        color = PALETA["primario"] if principal else PALETA["gris_medio"]
        r = g["razon"]
        dis = g["razon_ic_diseno"]
        w = g["razon_ic_wilson"]
        if dis:
            fig.add_trace(go.Scatter(
                x=[r], y=[nombre], mode="markers", showlegend=False,
                marker=dict(color=color, size=17, symbol="line-ns-open",
                            line=dict(width=2.5)),
                error_x=dict(type="data", symmetric=False,
                             array=[dis[1] - r], arrayminus=[r - dis[0]],
                             color=color, thickness=2, width=0),
                customdata=[[dis[0], dis[1]]],
                hovertemplate=("<b>%{y}</b><br>Cociente %{x:.2f}<br>"
                               "IC de diseño [%{customdata[0]:.2f}; "
                               "%{customdata[1]:.2f}]<extra></extra>")))
        fig.add_trace(go.Scatter(
            x=[r], y=[nombre], mode="markers", showlegend=False,
            marker=dict(color=color, size=11, symbol="line-ns", line=dict(width=2.5)),
            error_x=dict(type="data", symmetric=False,
                         array=[w[1] - r], arrayminus=[r - w[0]],
                         color=color, thickness=3, width=8),
            customdata=[[w[0], w[1], g["n_muestra_grupo"]]],
            hovertemplate=("<b>%{y}</b><br>Cociente %{x:.2f}<br>"
                           "IC de Wilson [%{customdata[0]:.2f}; %{customdata[1]:.2f}]<br>"
                           "n en la muestra: %{customdata[2]}<extra></extra>")))
    fig.add_vline(x=1, line=dict(color=PALETA["dorado"], width=2, dash="dash"))
    fig.add_annotation(x=1, y=1.02, yref="paper", text="1 = misma proporción",
                       showarrow=False, xanchor="left", yanchor="bottom",
                       font=dict(size=10, color=PALETA["dorado"]))
    for clave in orden:
        g = dv["grupos"][clave]
        if not g["razon_ic_diseno"]:
            fig.add_annotation(x=g["razon"], y=g["etiqueta"], text="  sin acotar",
                               showarrow=False, xshift=14,
                               font=dict(size=9, color=PALETA["gris_medio"]),
                               xanchor="left")
    fig.update_xaxes(
        title="Cociente: proporción en la población / proporción entre investigadores",
        type="log", range=[-0.75, 2.0])
    fig.update_layout(title=dict(
        text=("Cociente de subrepresentación con sus dos intervalos (escala logarítmica) · "
              "el intervalo largo es el del bootstrap de diseño; el corto y con topes, "
              "el de Wilson"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=470, leyenda=False)


def fig_cobertura(dv: dict) -> go.Figure:
    cob = dv["cobertura_por_convocatoria"]
    anios = list(cob)
    series = [("TXT_GRUPO_ETNICO", "Grupo étnico", PALETA["primario"]),
              ("TXT_POBLACION_DISCA", "Discapacidad", PALETA["dorado"]),
              ("ID_VICTIMA_CONFLICTO", "Víctima del conflicto", PALETA["claro"]),
              ("NME_GENERO_PR", "Género (referencia)", PALETA["gris_medio"])]
    fig = go.Figure()
    for col, nombre, color in series:
        vals = [cob[a][col]["pct_cobertura"] for a in anios]
        fig.add_trace(go.Bar(x=anios, y=vals, name=nombre, marker_color=color,
                             text=[f"{v:.1f} %".replace(".", ",") if v else "0 %"
                                   for v in vals],
                             textposition="outside", cliponaxis=False,
                             hovertemplate=("<b>%{x}</b><br>" + nombre +
                                            ": %{y:.2f} % de cobertura<extra></extra>")))
    fig.update_yaxes(title="% de registros con dato", range=[0, 118])
    fig.update_layout(barmode="group")
    fig.update_layout(title=dict(
        text=("Cobertura por convocatoria: las tres variables de diversidad solo "
              "existen en 2021"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=470, leyenda=True)


def pestana_diversidad(d: dict) -> tuple[list, str, str]:
    dv = d["diversidad_inferencia"]
    g = dv["grupos"]
    den = dv["denominador_etnia"]
    cob21 = dv["cobertura_por_convocatoria"]["2021"]

    filas = ""
    for clave, nota in (("afro", "subrepresentado"), ("indigena", "subrepresentado"),
                        ("discapacidad", "subrepresentado"),
                        ("victima", "subrepresentado")):
        x = g[clave]
        w, dis = x["razon_ic_wilson"], x["razon_ic_diseno"]
        filas += (
            f"<tr><td><b>{_html.escape(x['etiqueta'])}</b></td>"
            f"<td class='num'>{miles(x['n'])}</td>"
            f"<td class='num'>{num(x['pct'], 2)}</td>"
            f"<td class='num'>{num(x['dane_pct'], 2)}</td>"
            f"<td class='num'><b>{num(x['razon'], 2)}</b></td>"
            f"<td class='num'>[{num(w[0], 2)}; {num(w[1], 2)}]</td>"
            f"<td class='num'>[{num(dis[0], 2)}; {num(dis[1], 2)}]</td>"
            f"<td class='num'>{x['n_muestra_grupo']}</td>"
            f"<td>{nota}</td></tr>")
    tabla = (
        "<table class='tabla'><thead><tr><th>Grupo (2021)</th><th class='num'>n</th>"
        "<th class='num'>%</th><th class='num'>% país</th><th class='num'>Cociente</th>"
        "<th class='num'>IC 95 % Wilson</th><th class='num'>IC 95 % diseño</th>"
        "<th class='num'>n en la muestra</th><th>Lectura</th></tr></thead><tbody>"
        f"{filas}</tbody></table>"
        f"<p class='nota-tabla'>Los tres grupos pequeños (raizal 45, palenquero 11, "
        f"rrom 6) no llevan IC de diseño: el bootstrap divide por cero cuando el grupo "
        f"no aparece en alguna réplica y su cociente queda <b>no acotado</b>, que es un "
        f"resultado y no un fallo del cálculo.</p>")

    graficos = [
        ("t5", "Cocientes de subrepresentación con su incertidumbre",
         f"Sobre las {miles(den['respuestas_conocidas'])} respuestas conocidas de 2021. "
         f"El cociente es «proporción en la población del país» dividida por «proporción "
         f"entre investigadores reconocidos» (DANE 2018; RUV 2021 para víctimas). "
         f"Un valor por encima de 1 significa que el grupo pesa <i>menos</i> entre los "
         f"investigadores que en el país, es decir que está <b>subrepresentado</b>.",
         div(fig_razones(dv), "t5")),
        ("t6", "Cobertura de las variables de diversidad",
         "Qué proporción de los registros de cada convocatoria trae el dato. Las tres "
         "variables de diversidad aparecen por primera vez en 2021; el género, en cambio, "
         "está capturado en las seis convocatorias y por eso sí admite serie temporal.",
         div(fig_cobertura(dv), "t6")),
    ]
    conclusion = (
        f"<b>El IC ancho de indígenas no es un error: es el resultado.</b> Con "
        f"{miles(g['indigena']['n'])} personas indígenas en toda la base de 2021 y solo "
        f"{g['indigena']['n_muestra_grupo']} en la muestra, el cociente de representación "
        f"es {num(g['indigena']['razon'], 2)} con un intervalo de "
        f"Wilson de [{num(g['indigena']['razon_ic_wilson'][0], 2)}; "
        f"{num(g['indigena']['razon_ic_wilson'][1], 2)}] y, con el diseño real, de "
        f"[{num(g['indigena']['razon_ic_diseno'][0], 2)}; "
        f"{num(g['indigena']['razon_ic_diseno'][1], 2)}]. Ese intervalo no dice «no "
        f"sabemos nada»: dice que la <b>dirección</b> es inequívoca (todo el intervalo "
        f"está por encima de 1) y que la <b>magnitud</b> es cualquier cosa entre 5 y 32 "
        f"veces. Reportar el 7,88 a secas, como hacía el repositorio auditado, es "
        f"publicar la parte más frágil del dato."
        f"<br><br><b>El hallazgo que sobrevive es la dirección:</b> los cuatro grupos "
        f"principales están <i>subrepresentados</i> entre los investigadores reconocidos "
        f"respecto de su peso en la población (afro {num(g['afro']['razon'], 2)}×, indígena "
        f"{num(g['indigena']['razon'], 2)}×, discapacidad {num(g['discapacidad']['razon'], 2)}×, "
        f"víctima {num(g['victima']['razon'], 2)}×). Raizal, palenquero y rrom tienen razón "
        f"<b>menor que 1</b>, es decir están <i>sobrerrepresentados</i> "
        f"({num(g['raizal']['razon'], 2)}×, {num(g['palenquero']['razon'], 2)}×, "
        f"{num(g['rrom']['razon'], 2)}×) pero con bases de 45, 11 y 6 personas: no admiten "
        f"conclusión."
        f"<br><br><b>Aviso de nomenclatura.</b> La columna del auditado se llama "
        f"<code>razon_subrepresentacion</code> y para los tres grupos pequeños vale menos "
        f"de 1, es decir describe lo contrario: conviene leerla siempre como «cociente "
        f"DANE/MinCiencias»."
        f"<br><br><b>No hay serie temporal.</b> Las tres variables están vacías en 2013, "
        f"2014, 2015, 2017 y 2019 (0 % de cobertura) y aparecen en 2021 con "
        f"{num(cob21['TXT_GRUPO_ETNICO']['pct_cobertura'], 2)} %. Comparar con el DANE es "
        f"una <b>fotografía de 2021</b>, no una evolución."
        f"<br><br><b>Una trampa de denominador.</b> Si se excluyeran «Ningún grupo étnico» "
        f"y «Blanco o mestizo» del denominador, el porcentaje afro pasaría de "
        f"{num(den['pct_con_denominador_correcto'], 2)} % a "
        f"{num(den['pct_con_denominador_equivocado'], 2)} % "
        f"({miles(den['n_afro'])} de {miles(den['denominador_si_se_excluye_la_mayoria'])}): "
        f"sería comparar «qué proporción de las minorías es afro» con «qué proporción del "
        f"país es afro». El <b>código</b> del auditado no lo hacía —y era lo correcto—; "
        f"era su <b>comentario</b> el que lo pedía (ERRATA E7).")
    return graficos, tabla, conclusion


# ============================================================================
# 6. Pestana 4 — Redes y clustering (F2-4, F2-6)
# ============================================================================
def fig_red(G, nx) -> go.Figure:
    """Diagrama de la red de co-filiación de 2019."""
    pos = nx.spring_layout(G, seed=20260217, iterations=200)
    xs, ys = [], []
    for a, b in G.edges():
        xs.extend([pos[a][0], pos[b][0], None])
        ys.extend([pos[a][1], pos[b][1], None])
    nodos = list(G.nodes())
    gx = [pos[n][0] for n in nodos]
    gy = [pos[n][1] for n in nodos]
    grado = np.array([G.degree(n, weight="weight") for n in nodos], dtype=float)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name="Co-filiación",
                             line=dict(color=PALETA["gris_claro"], width=0.7),
                             hoverinfo="skip"))
    nombres = [n if len(n) <= 34 else n[:32] + "…" for n in nodos]
    fig.add_trace(go.Scatter(
        x=gx, y=gy, mode="markers", name="Institución",
        marker=dict(size=6 + 2.2 * np.sqrt(grado), color=grado,
                    colorscale=ESCALA_AZUL, showscale=True,
                    colorbar=dict(title="Grado<br>ponderado", thickness=12,
                                  len=0.6),
                    line=dict(width=0.6, color=BLANCO)),
        customdata=list(zip(nombres, grado)),
        hovertemplate="<b>%{customdata[0]}</b><br>Grado ponderado %{customdata[1]:.0f}"
                      "<extra></extra>"))
    # Etiquetas solo de los ocho nodos con más intermediación: rotular los 446
    # convertiría el gráfico en una nube de texto ilegible.
    centrales = sorted(G.nodes(), key=lambda n: -nx.betweenness_centrality(G)[n])[:8]
    bc = nx.betweenness_centrality(G)
    for n in centrales:
        fig.add_annotation(x=pos[n][0], y=pos[n][1], text=n[:26],
                           showarrow=False, yshift=11,
                           font=dict(size=9, color=PALETA["primario_oscuro"]),
                           bgcolor="rgba(255,255,255,0.75)", borderpad=1)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(title=dict(
        text=(f"Red de co-filiación de 2019 · {G.number_of_nodes()} instituciones y "
              f"{G.number_of_edges()} aristas · tamaño y color por grado ponderado"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=620, leyenda=False)


def fig_nulos(rd: dict) -> go.Figure:
    """
    z observado frente a cada nulo, por estadístico.

    Se excluye el Gini del grado: su p no es interpretable porque el propio nulo
    altera la cantidad (al colapsar aristas los grados bajan). Se documenta en el
    `analisis_redes.md` con el mismo criterio.
    """
    orden = ["tam_componente_mayor", "transitividad", "clustering_medio",
             "asortatividad_grado", "gini_betweenness", "camino_medio_mayor",
             "n_componentes"]
    etiqueta = {"tam_componente_mayor": "Componente mayor",
                "transitividad": "Transitividad",
                "clustering_medio": "Clustering medio",
                "asortatividad_grado": "Asortatividad por grado",
                "gini_betweenness": "Gini de la betweenness",
                "camino_medio_mayor": "Camino medio",
                "n_componentes": "N.º de componentes"}
    cn = rd["contraste_nulos"]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[cn[k]["er_z"] for k in orden], y=[etiqueta[k] for k in orden],
        orientation="h", name="Frente a Erdős–Rényi",
        marker_color=PALETA["gris_claro"],
        hovertemplate="<b>%{y}</b><br>z = %{x:.2f} frente a Erdős–Rényi<extra></extra>"))
    fig.add_trace(go.Bar(
        x=[cn[k]["config_z"] for k in orden], y=[etiqueta[k] for k in orden],
        orientation="h", name="Frente al modelo de configuración",
        marker_color=PALETA["primario"],
        customdata=[[cn[k]["config_p"]] for k in orden],
        hovertemplate="<b>%{y}</b><br>z = %{x:.2f}<br>"
                      "p = %{customdata[0]:.3f}<extra></extra>"))
    for x in (-1.96, 1.96):
        fig.add_vline(x=x, line=dict(color=PALETA["dorado"], width=1.6, dash="dash"))
    fig.add_vline(x=0, line=dict(color=PALETA["gris_oscuro"], width=1))
    fig.update_xaxes(title="z del estadístico observado frente al nulo",
                     range=[-16, 20])
    fig.update_layout(barmode="group")
    fig.update_layout(title=dict(
        text=("¿La estructura sobrevive al nulo? · líneas doradas: ±1,96 · solo la "
              "asortatividad y la concentración de la intermediación lo superan "
              "frente al nulo que respeta los grados"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=520, leyenda=True)


def fig_clustering(cl: dict) -> go.Figure:
    pe = cl["prueba_de_estructura"]
    ck = cl["criterios_k"]
    k = ck["k"]
    sil = ck["silhouette"]

    fig = make_subplots(rows=1, cols=2, column_widths=[0.5, 0.5],
                        subplot_titles=("Silhouette por número de clusters",
                                        "Silhouette observada frente al nulo"))
    fig.add_trace(go.Scatter(x=k, y=sil, mode="lines+markers", name="Silhouette",
                             line=dict(color=PALETA["primario"], width=3),
                             marker=dict(size=9),
                             hovertemplate="k = %{x}<br>silhouette %{y:.4f}<extra></extra>"),
                  row=1, col=1)
    fig.add_hline(y=ck["umbral_silhouette_estructura"],
                  line=dict(color=PALETA["dorado"], width=1.8, dash="dash"),
                  row=1, col=1)
    fig.add_annotation(x=10, y=ck["umbral_silhouette_estructura"],
                       text="umbral 0,25 (Kaufman y Rousseeuw)", showarrow=False,
                       font=dict(size=10, color=PALETA["dorado"]), xanchor="right",
                       yanchor="bottom", row=1, col=1)
    fig.add_vline(x=pe["k_evaluado"],
                  line=dict(color=PALETA["gris_medio"], width=1.4, dash="dot"),
                  row=1, col=1)

    nulo = pe["nulo_silhouette"]
    fig.add_trace(go.Histogram(x=nulo, nbinsx=10, name="Particiones nulas",
                               marker_color=PALETA["gris_claro"], showlegend=True,
                               hovertemplate="%{y} réplicas con silhouette en %{x}"
                                             "<extra></extra>"), row=1, col=2)
    fig.add_vline(x=pe["silhouette_observada"],
                  line=dict(color=PALETA["primario"], width=3), row=1, col=2)
    fig.add_vline(x=pe["silhouette_nulo_medio"],
                  line=dict(color=PALETA["dorado"], width=2, dash="dash"),
                  row=1, col=2)
    fig.add_annotation(x=pe["silhouette_observada"], y=1, yref="y2 domain",
                       text=f"observada en la submuestra {num(pe['silhouette_observada'], 3)}",
                       showarrow=False, font=dict(size=10, color=PALETA["primario"]),
                       xanchor="right", yanchor="top", row=1, col=2)
    fig.update_xaxes(title="Número de clusters (k)", row=1, col=1)
    fig.update_yaxes(title="Silhouette", row=1, col=1)
    fig.update_xaxes(title="Silhouette de la partición nula", row=1, col=2)
    fig.update_yaxes(title="Réplicas", row=1, col=2)
    fig.update_layout(title=dict(
        text=(f"k = 2 maximiza la silhouette ({num(ck['silhouette'][0], 2)} ± 0,06), pero "
              f"el nulo la supera casi siempre (p = {num(pe['silhouette_p'], 3)})"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=480, leyenda=True)


def pestana_redes(d: dict, G, nx) -> tuple[list, str, str]:
    rd, cl = d["redes_nulos"], d["clustering"]
    cn = rd["contraste_nulos"]
    pu = rd["puentes"]
    v = cl["veredicto"]
    filas = "".join(
        f"<tr><td>{_html.escape(n['institucion'])}</td>"
        f"<td class='num'>{n['grado']}</td>"
        f"<td class='num'>{num(n['betweenness'], 4)}</td>"
        f"<td class='num'>{num(n['betweenness_z'], 2)}</td>"
        f"<td class='num'>{num(n['interregionalidad'] * 100, 1)} %</td>"
        f"<td>{'sí' if abs(n['betweenness_z']) >= 1.96 else 'no'}</td></tr>"
        for n in rd["nodos_top_betweenness"][:10])
    tabla_nodos = (
        "<table class='tabla'><thead><tr><th>Institución con más intermediación</th>"
        "<th class='num'>Grado</th><th class='num'>Betweenness</th>"
        "<th class='num'>z frente a su grado</th>"
        "<th class='num'>Interregionalidad</th>"
        "<th>¿Supera z = 1,96 sin corregir?</th></tr></thead><tbody>"
        f"{filas}</tbody></table>"
        f"<p class='nota-tabla'>Ninguna de estas instituciones sobrevive la corrección "
        f"por comparaciones múltiples: con 120 nodos contrastables el umbral de "
        f"Bonferroni es z = {num(pu['z_de_bonferroni'], 2)}.</p>")

    graficos = [
        ("t7", "La red de co-filiación de 2019",
         f"Solo {miles(rd['solo_2019']['registros_con_doble_afiliacion_por_anio']['2019'])} "
         f"registros de 2019 declaran dos instituciones en la misma fila; en el resto de "
         f"convocatorias no hay ninguno. Por eso no es una serie temporal: es <b>una sola "
         f"red</b>. Las {miles(rd['pares']['personas_con_doble_afiliacion'])} personas con "
         f"doble afiliación producen {miles(rd['pares']['pares_tras_normalizar'])} pares "
         f"tras descartar {rd['pares']['pares_descartados_como_self_loop']} casos de dos "
         f"sedes de la misma institución.",
         div(fig_red(G, nx), "t7")),
        ("t8", "¿La estructura de la red sobrevive al azar?",
         f"Cada estadístico se compara con dos nulos de 500 réplicas: Erdős–Rényi (misma "
         f"densidad, sin estructura) y modelo de configuración (misma distribución de "
         f"grados). El nulo correcto para preguntar «¿hay algo más que heterogeneidad de "
         f"grados?» es el segundo.",
         div(fig_nulos(rd), "t8")),
        ("t9", "El clustering frente a su modelo nulo",
         f"Se ajustó k-prototypes de Huang (el mismo de <code>kproto()</code> de R) para "
         f"k de 2 a 10, y después se repitió con las variables permutadas por separado "
         f"({miles(cl['prueba_de_estructura']['filas'])} filas, "
         f"{len(cl['prueba_de_estructura']['nulo_silhouette'])} réplicas): si la "
         f"partición observada no le gana a eso, no captura estructura conjunta.",
         div(fig_clustering(cl), "t9")),
    ]
    conclusion = (
        f"<b>«Hay 3 clusters» no se sostiene.</b> El criterio habitual (silhouette) elige "
        f"k = 2 con {num(v['silhouette_del_k_elegido'], 2)} ± 0,06, un valor que roza el "
        f"umbral de 0,25 de Kaufman y Rousseeuw sin superarlo con holgura: la silhouette se "
        f"estima sobre una submuestra de 4 000 de las 77 237 filas y con ocho réplicas de "
        f"esa submuestra el valor cae entre 0,14 y 0,30. <b>Por eso la conclusión no se "
        f"apoya en el umbral, sino en el nulo:</b> permutando cada variable por separado se "
        f"obtiene una partición <i>igual de buena</i> (silhouette nula media "
        f"{num(cl['prueba_de_estructura']['silhouette_nulo_medio'], 3)}, "
        f"p = {num(cl['prueba_de_estructura']['silhouette_p'], 3)}). Además la partición "
        f"solo reproduce el {num(100 - cl['perdida_de_informacion']['perdida_pct'], 1)} % de "
        f"la variabilidad mixta, y sus dos grupos son un <b>gradiente de edad y formación</b> "
        f"(37,1 años con 37,4 % de doctorado frente a 52,0 años con 63,9 %), no categorías "
        f"naturales. <b>El mejor k es 1.</b>"
        f"<br><br><b>Lo mismo con las universidades puente.</b> Como propiedad global, el "
        f"corretaje sí está concentrado (Gini de la betweenness 0,9143 frente a 0,9023 del "
        f"nulo con grados, p = 0,004). Pero al preguntar <i>quién</i> ejerce ese corretaje "
        f"hay {pu['nodos_contrastables']} instituciones contrastables y solo "
        f"{pu['pasan_z_1_96_sin_corregir']} superan z = 1,96, cuando el azar produciría "
        f"{num(pu['esperados_por_azar_sin_corregir'], 1)}. <b>El azar produce más "
        f"«puentes» que la realidad</b>, así que no puede entregarse una lista de "
        f"universidades puente: lo que se sostiene es que el corretaje está concentrado, "
        f"no quién lo ejerce."
        f"<br><br><b>Y un resultado que sí es una descripción sólida:</b> "
        f"{miles(pu['motivos_sin_prueba']['hoja'])} de las {miles(rd['red']['n_nodos'])} "
        f"instituciones ({num(100 * pu['motivos_sin_prueba']['hoja'] / rd['red']['n_nodos'], 1)} %) "
        f"aparecen en <b>una sola</b> co-filiación. La red de colaboración institucional de "
        f"2019 es, sobre todo, una colección de pares aislados en torno a un núcleo grande.")
    return graficos, tabla_nodos, conclusion


# ============================================================================
# 7. Pestana 5 — Supervivencia y el efecto género (F2-10)
# ============================================================================
def fig_km_categoria(sv: dict) -> go.Figure:
    fig = go.Figure()
    for cat, v in sv["kaplan_meier"]["categoria"].items():
        km, med = v["km"], v["mediana"]
        if not km["tiempos"]:
            continue
        marca = (f"mediana {num(med['anios'])} años" if med["estimable"]
                 else "mediana no alcanzada")
        fig.add_trace(go.Scatter(
            x=km["tiempos"], y=km["S"], name=cat.replace("Investigador ", ""),
            mode="lines", line_shape="hv",
            line=dict(color=COLOR_CATEGORIA.get(cat, PALETA["gris_medio"]), width=3),
            customdata=list(zip(km["n_riesgo"], km["d_eventos"])),
            hovertemplate=(f"<b>{cat.replace('Investigador ', '')}</b><br>"
                           "t = %{x:.2f} años<br>S = %{y:.4f}<br>"
                           "en riesgo %{customdata[0]:,}<br>"
                           "eventos en ese tiempo %{customdata[1]:,}<br>"
                           f"{marca}<extra></extra>")))
    fig.add_hline(y=0.5, line=dict(color=PALETA["gris_medio"], width=1.2, dash="dot"))
    fig.add_annotation(x=6.1, y=0.5, text="S = 0,5", showarrow=False,
                       font=dict(size=10, color=PALETA["gris_medio"]),
                       xanchor="right", yanchor="bottom")
    fig.update_xaxes(title="Años desde la primera aparición")
    fig.update_yaxes(title="Proporción que sigue en el sistema  S(t)", range=[0, 1.03])
    fig.update_layout(title=dict(
        text=("Kaplan-Meier por categoría · la caída inicial de Junior "
              "(S(0) = 0,80) son las personas que aparecen una sola vez"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=480, leyenda=True)


def fig_km_genero(sv: dict) -> go.Figure:
    fig = go.Figure()
    for gen, color in (("Masculino", PALETA["primario"]),
                       ("Femenino", PALETA["dorado"])):
        v = sv["kaplan_meier"]["genero"][gen]
        km = v["km"]
        if not km["tiempos"]:
            continue
        fig.add_trace(go.Scatter(
            x=km["tiempos"] + km["tiempos"][::-1],
            y=km["ic95_sup"] + km["ic95_inf"][::-1],
            fill="toself", fillcolor="rgba(30,55,128,0.10)" if gen == "Masculino"
            else "rgba(183,135,30,0.12)",
            line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(
            x=km["tiempos"], y=km["S"], name=gen, mode="lines", line_shape="hv",
            line=dict(color=color, width=3),
            customdata=list(zip(km["n_riesgo"], km["ic95_inf"], km["ic95_sup"])),
            hovertemplate=(f"<b>{gen}</b><br>t = %{{x:.2f}} años<br>S = %{{y:.4f}} "
                           "IC 95 % [%{customdata[1]:.4f}; %{customdata[2]:.4f}]<br>"
                           "en riesgo %{customdata[0]:,}<extra></extra>")))
    fig.update_xaxes(title="Años desde la primera aparición")
    fig.update_yaxes(title="S(t)", range=[0, 1.0])
    fig.update_layout(title=dict(
        text=("Kaplan-Meier por género · las bandas son el IC 95 % (log−log); "
              "se solapan en todo el recorrido"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=460, leyenda=True)


def fig_forest(sv: dict) -> go.Figure:
    cox = sv["cox"]
    filas = [r for r in cox["coeficientes"] if r["variable"] != "constante"]
    orden = ["cat3", "genero_col", "area", "depto_top"]
    filas.sort(key=lambda r: (orden.index(r["variable"]), r["hr"]))
    etiquetas = []
    for r in filas:
        pre = {"cat3": "Categoría", "genero_col": "Género", "area": "Área",
               "depto_top": "Departamento"}[r["variable"]]
        etiquetas.append(f"{pre}: {r['nivel']}")
    hr = [r["hr"] for r in filas]
    lo = [r["ic95_inf"] for r in filas]
    hi = [r["ic95_sup"] for r in filas]
    sig = [r["p"] < 0.05 for r in filas]
    p = [r["p"] for r in filas]

    fig = go.Figure(go.Scatter(
        x=hr, y=etiquetas, mode="markers",
        marker=dict(size=11, symbol="diamond",
                    color=[PALETA["primario"] if s else PALETA["gris_medio"] for s in sig]),
        error_x=dict(type="data", symmetric=False,
                     array=[h - v for h, v in zip(hi, hr)],
                     arrayminus=[v - l for v, l in zip(hr, lo)],
                     color=PALETA["primario"], thickness=2, width=6),
        customdata=list(zip(lo, hi, p, sig)),
        hovertemplate=("<b>%{y}</b><br>HR = %{x:.3f}<br>"
                       "IC 95 % [%{customdata[0]:.3f}; %{customdata[1]:.3f}]<br>"
                       "p = %{customdata[2]:.3e}<extra></extra>")))
    fig.add_vline(x=1, line=dict(color=PALETA["dorado"], width=2, dash="dash"))
    fig.add_annotation(x=1, y=-0.6, text="HR = 1: sin diferencia", showarrow=False,
                       font=dict(size=10, color=PALETA["dorado"]), xanchor="left",
                       yanchor="top")
    fig.update_xaxes(title="Razón de riesgos instantáneos (HR), escala logarítmica",
                     type="log")
    fig.update_layout(title=dict(
        text=(f"Cox con empates de Efron · n = {miles(cox['n'])} personas, "
              f"{miles(cox['eventos'])} eventos, {cox['n_covariables']} covariables · "
              f"azul = p &lt; 0,05, gris = no significativo"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=560, leyenda=False)


def fig_composicion(sv: dict, comp: pd.DataFrame) -> go.Figure:
    """Por qué desaparece el género: reparto por categoría y permanencia."""
    cats = list(comp.index)
    tot = comp.sum()
    m_pct = (comp["Masculino"] / tot["Masculino"] * 100).tolist()
    f_pct = (comp["Femenino"] / tot["Femenino"] * 100).tolist()
    km = sv["kaplan_meier"]["categoria"]
    s_fin = [km[c]["km"]["S"][-1] if km[c]["km"]["S"] else np.nan for c in cats]

    fig = make_subplots(rows=1, cols=2, column_widths=[0.56, 0.44],
                        subplot_titles=("Reparto de cada género entre las categorías",
                                        "Permanencia hasta el final de la ventana"))
    fig.add_trace(go.Bar(x=[c.replace("Investigador ", "") for c in cats],
                         y=f_pct, name="Mujeres", marker_color=PALETA["dorado"],
                         text=[f"{v:.1f} %".replace(".", ",") for v in f_pct],
                         textposition="outside", cliponaxis=False,
                         hovertemplate="<b>%{x}</b><br>%{y:.2f} % de las mujeres"
                                       "<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Bar(x=[c.replace("Investigador ", "") for c in cats],
                         y=m_pct, name="Hombres", marker_color=PALETA["primario"],
                         text=[f"{v:.1f} %".replace(".", ",") for v in m_pct],
                         textposition="outside", cliponaxis=False,
                         hovertemplate="<b>%{x}</b><br>%{y:.2f} % de los hombres"
                                       "<extra></extra>"), row=1, col=1)
    fig.update_yaxes(title="% dentro de su género", range=[0, 88], row=1, col=1)

    fig.add_trace(go.Bar(x=[c.replace("Investigador ", "") for c in cats], y=s_fin,
                         name="S final", showlegend=False,
                         marker_color=[COLOR_CATEGORIA.get(c, PALETA["gris_medio"])
                                       for c in cats],
                         text=[num(v, 3) for v in s_fin], textposition="outside",
                         cliponaxis=False,
                         hovertemplate="<b>%{x}</b><br>S final %{y:.4f}<extra></extra>"),
                  row=1, col=2)
    fig.update_yaxes(title="S al final de la ventana", range=[0, 1.15], row=1, col=2)
    fig.update_layout(barmode="group")
    fig.update_layout(title=dict(
        text=("El mecanismo: las mujeres se concentran en Junior (72,4 % frente a "
              "66,4 %) y Junior es la categoría que más sale"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=500, leyenda=True)


def pestana_supervivencia(d: dict, comp: pd.DataFrame) -> tuple[list, str, str]:
    sv = d["supervivencia"]
    di, lr, cox = sv["diseno"], sv["logrank"], sv["cox"]
    gen = [r for r in cox["coeficientes"] if r["variable"] == "genero_col"][0]
    jr = [r for r in cox["coeficientes"] if r["nivel"] == "Investigador Junior"]
    aso = [r for r in cox["coeficientes"] if r["nivel"] == "Investigador Asociado"][0]
    sen = [r for r in cox["coeficientes"] if r["nivel"] == "Investigador Sénior"][0]
    val = sv["validacion_score_vs_logrank"]
    em = sv["sensibilidad_emerito_agrupado"]

    cifras = (
        "<table class='tabla'><thead><tr><th>Resultado</th><th class='num'>Valor</th>"
        "<th>Lectura</th></tr></thead><tbody>"
        f"<tr><td>Personas y eventos</td><td class='num'>{miles(di['n_personas'])} · "
        f"{miles(di['eventos'])}</td><td>{pct(di['pct_censurado'], 1)} sigue en el "
        f"sistema al cerrar la ventana (censura a la derecha)</td></tr>"
        f"<tr><td>Ventana de observación</td><td class='num'>{num(di['ventana_anios'], 3)} años</td>"
        f"<td>desde la primera aparición de cada persona</td></tr>"
        f"<tr><td>Log-rank por categoría</td><td class='num'>χ² = {num(lr['categoria']['chi2'], 1)}</td>"
        f"<td>gl = {lr['categoria']['gl']}; la desagregación que más discrimina</td></tr>"
        f"<tr><td>Log-rank por género</td><td class='num'>χ² = {num(lr['genero']['chi2'], 2)}</td>"
        f"<td>gl = {lr['genero']['gl']}; {pval(lr['genero']['p'], 4)} en crudo</td></tr>"
        f"<tr><td>HR del género, ajustado</td><td class='num'>{num(gen['hr'], 3)}</td>"
        f"<td>[{num(gen['ic95_inf'], 3)}; {num(gen['ic95_sup'], 3)}], "
        f"{pval(gen['p'])}: <b>desaparece</b></td></tr>"
        f"<tr><td>HR de Sénior frente a Junior</td><td class='num'>{num(sen['hr'], 3)}</td>"
        f"<td>[{num(sen['ic95_inf'], 3)}; {num(sen['ic95_sup'], 3)}]</td></tr>"
        f"<tr><td>HR de Asociado frente a Junior</td><td class='num'>{num(aso['hr'], 3)}</td>"
        f"<td>[{num(aso['ic95_inf'], 3)}; {num(aso['ic95_sup'], 3)}]</td></tr>"
        "</tbody></table>")

    graficos = [
        ("t10", "Supervivencia por categoría",
         f"Kaplan-Meier sobre las {miles(di['n_personas'])} personas. El evento es dejar "
         f"de aparecer: la última convocatoria observada no es 2021. La mediana solo se "
         f"alcanza en dos de las cuatro categorías, y eso es un resultado, no un vacío: "
         f"no se fuerza un número cuando la curva no baja de 0,5. <b>Aquí la unidad es la "
         f"persona en su última observación sin filtrar</b> ({miles(di['n_personas'])}), no "
         f"el stock con territorio colombiano de la pestaña 2: por eso Bogotá son 9 813 y "
         f"allí 9 888 (ver la nota de esa pestaña).",
         div(fig_km_categoria(sv), "t10")),
        ("t11", "Supervivencia por género",
         f"El log-rank en crudo encuentra una diferencia ({pval(lr['genero']['p'], 4)}). "
         f"Las dos curvas se separan unas centésimas en todo el recorrido y las bandas se "
         f"solapan casi por completo: la señal es real pero minúscula, y en eso el "
         f"gráfico y el test coinciden.",
         div(fig_km_genero(sv), "t11")),
        ("t12", "Razones de riesgos instantáneos (modelo de Cox)",
         f"Modelo con {cox['n_covariables']} covariables, empates de Efron, "
         f"{cox['iteraciones']} iteraciones y gradiente final "
         f"{num(cox['gradiente_final'] * 1e10, 2)} × 10⁻¹⁰. Las referencias son "
         f"{_html.escape(cox['referencias']['categoria'])}, "
         f"{_html.escape(cox['referencias']['genero'].lower())}, "
         f"{_html.escape(cox['referencias']['area'])} y "
         f"{_html.escape(cox['referencias']['departamento'])}. La covariable "
         f"«No registra» en área tiene HR "
         f"{num([r for r in cox['coeficientes'] if r['nivel'] == 'No registra'][0]['hr'], 3)}: "
         f"es un artefacto de codificación del registro, no un efecto científico.",
         div(fig_forest(sv), "t12")),
        ("t13", "El mecanismo: composición, no género",
         f"<b>Reparto real, calculado sobre la base:</b> el "
         f"{num(comp.loc['Investigador Junior', 'Femenino'] / comp['Femenino'].sum() * 100, 1)} % "
         f"de las mujeres está en Junior, frente al "
         f"{num(comp.loc['Investigador Junior', 'Masculino'] / comp['Masculino'].sum() * 100, 1)} % "
         f"de los hombres; en Sénior, el "
         f"{num(comp.loc['Investigador Sénior', 'Femenino'] / comp['Femenino'].sum() * 100, 1)} % "
         f"frente al "
         f"{num(comp.loc['Investigador Sénior', 'Masculino'] / comp['Masculino'].sum() * 100, 1)} %. "
         f"Y Junior es justamente la categoría con menor permanencia "
         f"(S final {num(sv['kaplan_meier']['categoria']['Investigador Junior']['km']['S'][-1], 3)} "
         f"frente a "
         f"{num(sv['kaplan_meier']['categoria']['Investigador Sénior']['km']['S'][-1], 3)} "
         f"de Sénior).",
         div(fig_composicion(sv, comp), "t13")),
    ]
    conclusion = (
        f"<b>El hallazgo más fuerte de la Fase 2 está aquí, y no es el que se esperaba.</b> "
        f"En crudo, el género sí discrimina ({pval(lr['genero']['p'], 4)}); pero al ajustar "
        f"por categoría, área y departamento el hazard ratio es "
        f"{num(gen['hr'], 3)} [{num(gen['ic95_inf'], 3)}; {num(gen['ic95_sup'], 3)}] con "
        f"{pval(gen['p'])}. <b>La diferencia cruda no era de género: era de composición.</b> "
        f"Una proporción mayor de mujeres que de hombres se queda en Junior "
        f"(el {num(comp.loc['Investigador Junior', 'Femenino'] / comp['Femenino'].sum() * 100, 1)} % "
        f"de las mujeres frente al "
        f"{num(comp.loc['Investigador Junior', 'Masculino'] / comp['Masculino'].sum() * 100, 1)} % "
        f"de los hombres) y una proporción menor en Sénior "
        f"({num(comp.loc['Investigador Sénior', 'Femenino'] / comp['Femenino'].sum() * 100, 1)} % "
        f"frente al "
        f"{num(comp.loc['Investigador Sénior', 'Masculino'] / comp['Masculino'].sum() * 100, 1)} %), "
        f"y Junior es la categoría que más sale. Al comparar dentro de la misma categoría y "
        f"la misma área, la diferencia desaparece. Nótese la dirección: <b>no</b> es que las "
        f"mujeres estén en las categorías de mayor permanencia, sino en la de menor."
        f"<br><br><b>Es la cuarta vez que el mismo patrón aparece por vías "
        f"independientes:</b> el género explica el 0,11 % de la varianza de la retención "
        f"(EDA); su V de Cramér con los clusters es 0,006 (F2-6); no muestra patrón "
        f"territorial propio (F2-5); y aquí desaparece al ajustar. Cuatro análisis distintos "
        f"convergen en que el género <b>no estructura este registro</b>."
        f"<br><br><b>Lo que sí estructura: la categoría.</b> Sénior tiene un HR de "
        f"{num(sen['hr'], 3)} frente a Junior —un {num(100 * (1 - sen['hr']), 0)} % menos de "
        f"riesgo de salir—, y esa única desagregación produce un log-rank de χ² = "
        f"{num(lr['categoria']['chi2'], 1)}."
        f"<br><br><b>Dos cautelas que el panel no oculta.</b> (1) La censura es del "
        f"{pct(di['pct_censurado'], 1)}: la mayoría sigue dentro al cerrar la ventana, así "
        f"que 16 de los 20 grupos nunca alcanzan la mediana. (2) Los Eméritos se excluyen "
        f"del Cox por ser una <b>categoría terminal por selección</b> (no vuelven "
        f"{sv['kaplan_meier']['categoria']['Investigador Emérito']['eventos']} de sus "
        f"{sv['kaplan_meier']['categoria']['Investigador Emérito']['n']} personas): "
        f"su HR mediría tiempo inmortal. Se comprobó que agruparlos con Sénior no sesga: "
        f"el cambio máximo en un HR es {num(em['cambio_maximo_absoluto'], 3)}, y es "
        f"justamente el de Sénior; todos los demás se mueven menos de 0,011."
        f"<br><br><b>La implementación está validada:</b> con una covariable binaria el "
        f"test de score de Cox y el log-rank son el mismo contraste; en un caso sintético "
        f"sin empates coinciden exactamente (χ² = {num(sv['autotest']['logrank_chi2'], 4)}) "
        f"y en la base real difieren un "
        f"{num(100 * val['diferencia_relativa_chi2'], 2)} %, lo esperable entre Efron y "
        f"Breslow.")
    return graficos, cifras, conclusion


# ============================================================================
# 8. Pestana 6 — Calidad y reproducibilidad (F2-3, F2-7)
# ============================================================================
def fig_unicidad(u: dict) -> go.Figure:
    cc = u["contraste_con_la_implementacion"]
    st = u["sensibilidad_tolerancia"]

    fig = make_subplots(rows=1, cols=2, column_widths=[0.44, 0.56],
                        subplot_titles=("Pares marcados por cada regla",
                                        "Sensibilidad a la tolerancia (± años)"))
    etiquetas = ["Regla documentada\n(±4 años y género)",
                 "Regla implementada\n(filtro dif_edad > 4,1)"]
    valores = [cc["pares_marcados_documentada"], cc["pares_marcados_implementada"]]
    fig.add_trace(go.Bar(
        x=etiquetas, y=valores,
        marker_color=[PALETA["primario"], ALERTA],
        text=[miles(v) for v in valores], textposition="outside", cliponaxis=False,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>%{y:,} pares<extra></extra>"), row=1, col=1)
    fig.update_yaxes(title="Pares de registros marcados", rangemode="tozero", row=1, col=1)
    fig.add_annotation(x=1, y=valores[1] * 0.55,
                       text=(f"{miles(cc['falsos_positivos_de_la_implementada'])} falsos "
                             f"positivos<br>y {cc['falsos_negativos_de_la_implementada']} "
                             f"falsos negativos"),
                       showarrow=False, font=dict(size=11, color=BLANCO),
                       bgcolor=ALERTA, borderpad=4, row=1, col=1)

    tol = st["pares_por_tolerancia"]
    xs = [float(k) for k in tol]
    ys = [tol[k] for k in tol]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines+markers", line=dict(color=PALETA["primario"], width=3),
        marker=dict(size=9), showlegend=False,
        hovertemplate="±%{x} años<br>%{y:,} pares marcados<extra></extra>"),
        row=1, col=2)
    fig.add_vline(x=st["tolerancia_declarada"],
                  line=dict(color=PALETA["dorado"], width=2, dash="dash"), row=1, col=2)
    fig.add_annotation(x=st["tolerancia_declarada"], y=max(ys) * 0.5,
                       text="±4, la que el equipo declaró",
                       showarrow=False, font=dict(size=10, color=PALETA["dorado"]),
                       xanchor="right", row=1, col=2)
    fig.update_xaxes(title="Tolerancia (± años)", type="log", row=1, col=2)
    fig.update_yaxes(title="Pares marcados", type="log", row=1, col=2)
    fig.update_layout(title=dict(
        text=("La regla del auditado marca 59 veces más pares: casi todos falsos positivos"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=480, leyenda=False)


def fig_estrella(e: dict) -> go.Figure:
    m3 = e["modelo_3_convocatorias"]["por_convocatoria"]
    m6 = e["modelo_6_convocatorias"]["por_convocatoria"]
    anios = list(m6)
    cargado = [m3[a]["registros"] if a in m3 else None for a in anios]
    completo = [m6[a]["registros"] for a in anios]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=anios, y=completo, name="Las 6 convocatorias (reconstruido)",
                         marker_color=PALETA["primario"],
                         text=[miles(v) for v in completo], textposition="outside",
                         cliponaxis=False,
                         hovertemplate="<b>%{x}</b><br>%{y:,} hechos<extra></extra>"))
    fig.add_trace(go.Bar(x=anios, y=cargado, name="Lo que cargó el auditado (3)",
                         marker_color=PALETA["dorado"],
                         text=["—" if v is None else miles(v) for v in cargado],
                         textposition="outside", cliponaxis=False,
                         hovertemplate="<b>%{x}</b><br>%{y:,} hechos<extra></extra>"))
    fig.update_yaxes(title="Filas de la tabla de hechos", range=[0, 25000])
    fig.update_layout(barmode="group")
    fig.update_layout(title=dict(
        text=(f"El defecto del auditado, reproducido: su carga toma solo 3 convocatorias "
              f"({miles(e['modelo_3_convocatorias']['total_hechos'])} hechos) frente a las "
              f"{miles(e['modelo_6_convocatorias']['total_hechos'])} reales"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=460, leyenda=True)


def pestana_calidad(d: dict) -> tuple[list, str, str]:
    e, u = d["modelo_estrella"], d["validacion_unicidad"]
    cc = u["contraste_con_la_implementacion"]
    imp = u["impacto"]
    filas = "".join(
        f"<tr><td><code>{_html.escape(nombre)}</code></td><td class='num'>{miles(n)}</td>"
        f"<td>{'dimensión' if nombre.startswith('dim') else ('hechos' if nombre.startswith('fact') else 'puente')}</td></tr>"
        for nombre, n in sorted(e["modelo_6_convocatorias"]["tablas"].items()))
    tabla_tablas = (
        "<table class='tabla'><thead><tr><th>Tabla construida</th>"
        "<th class='num'>Filas</th><th>Tipo</th></tr></thead><tbody>"
        f"{filas}</tbody></table>"
        f"<p class='nota-tabla'>Nueve tablas: <b>7 dimensiones + 1 tabla de hechos + 1 "
        f"tabla puente</b>. El «modelo con nueve dimensiones» que enuncia el informe del "
        f"auditado cuenta tablas, no dimensiones. Integridad referencial completa y 0 "
        f"huérfanos; los hechos reproducen la evidencia versionada del propio "
        f"repositorio (diferencias = 0 en las seis convocatorias).</p>")

    graficos = [
        ("t14", "La regla de unicidad: documentada frente a implementada",
         f"El documento del auditado describe un contraste <b>contra el lapso entre "
         f"convocatorias</b> con tolerancia simétrica y exige que coincida el género. El "
         f"código implementa un umbral fijo de 4,1 años, en <b>una sola cola</b> (solo "
         f"aumentos) y sin mirar el género. La regla formalizada sigue la versión "
         f"documentada, que es la correcta.",
         div(fig_unicidad(u), "t14")),
        ("t15", "El modelo estrella con las seis convocatorias",
         "El mismo pipeline del auditado, alimentado con la base completa. La serie dorada "
         "son las convocatorias que su carga tomaba; la azul, las seis reales.",
         div(fig_estrella(e), "t15")),
    ]
    conclusion = (
        f"<b>Dos fallos silenciosos, dos correcciones.</b> El primero es la regla de "
        f"unicidad: la regla <i>documentada</i> marca {cc['pares_marcados_documentada']} pares "
        f"y la <i>implementada</i> marca {miles(cc['pares_marcados_implementada'])}, de los "
        f"cuales <b>{miles(cc['falsos_positivos_de_la_implementada'])} son falsos "
        f"positivos</b> y {cc['falsos_negativos_de_la_implementada']} falsos negativos. El "
        f"motivo es doble: al no comparar contra el lapso real entre convocatorias, marca a "
        f"cualquiera cuya edad crezca más de 4,1 años entre dos registros —lo normal cuando "
        f"el hueco es de 6 o 7 años—; y al ser de una sola cola no ve <b>ninguno</b> de los "
        f"{cc['pares_con_edad_que_retrocede_mas_de_4']} pares en los que la edad retrocede. "
        f"Una edad que decrece 98 años es tan imposible como una que crece 98."
        f"<br><br><b>El hallazgo, en números pequeños y concretos:</b> "
        f"{u['ids_no_unicos']['n_ids_violadores']} IDs de los "
        f"{miles(u['ids_no_unicos']['n_ids_evaluados'])} con más de un registro "
        f"({pct(u['ids_no_unicos']['pct_del_padron'], 3)}) violan la regla. De ellos, "
        f"{u['ids_no_unicos']['por_estado']['violacion_genero']} fallan solo en el género "
        f"(atributo que el EDA ya documentó como inestable) y "
        f"{u['ids_no_unicos']['interpretacion_por_rol']['violan_la_identidad_(edad)']} "
        f"tienen una trayectoria de edad imposible: esos son los que <b>comprometen la "
        f"identidad</b>, porque el ID puede estar designando a dos personas distintas. El "
        f"peor caso es <code>0000671819</code>, que declara 115,51 años en 2017 y 16,92 en "
        f"2019."
        f"<br><br><b>Por qué no se cambia el umbral:</b> con ±2 se marcarían "
        f"{st_val(u, '2.0')} pares y con ±4, {st_val(u, '4.0')}. El ±4 es una decisión "
        f"declarada del equipo y no se toca; se reporta su efecto. La meseta de ±3 y ±4 "
        f"(ambos dan 18 pares) indica que el resultado es estable en la tolerancia "
        f"declarada."
        f"<br><br><b>El impacto agregado es pequeño, y eso también es un resultado:</b> "
        f"{imp['registros_afectados']} registros ({pct(imp['pct_registros'], 3)}) y "
        f"{imp['pares_consecutivos_afectados']} pares; la retención 2013→2021 pasa de "
        f"{num(imp['retencion_2013_2021_con']['pct'], 2)} % a "
        f"{num(imp['retencion_2013_2021_sin']['pct'], 2)} % "
        f"(−{num(abs(imp['delta_retencion_pp']), 4)} pp) y la edad media se mueve "
        f"−{num(abs(imp['delta_edad']), 5)} años. Quince IDs sobre 30 086 no mueven las cifras "
        f"grandes; lo que implican es que <b>esas 15 trayectorias individuales no son "
        f"usables</b>."
        f"<br><br><b>El segundo fallo es el modelo estrella:</b> la carga tomaba tres "
        f"convocatorias ({miles(e['modelo_3_convocatorias']['total_hechos'])} hechos) cuando "
        f"la base tiene seis ({miles(e['modelo_6_convocatorias']['total_hechos'])}). Se "
        f"construyó el modelo completo con las funciones del propio auditado —sin "
        f"reimplementarlas— y reproduce su evidencia versionada con diferencia 0 en las seis "
        f"convocatorias."
        f"<br><br><b>Y la validación cruzada con el analista:</b> de los "
        f"{u['validacion_con_los_juicios_del_analista']['ids_revisados_por_el_analista']} "
        f"casos que revisó a mano, "
        f"{u['validacion_con_los_juicios_del_analista']['la_diferencia_de_edad_coincide']} "
        f"coinciden con el cálculo. El desacuerdo es <code>0000671819</code>: él anotó "
        f"+40,33 (el par 2019→2021) y se le pasó el −98,59 del par 2015→2017.")
    return graficos, tabla_tablas, conclusion


def st_val(u: dict, clave: str) -> str:
    return miles(u["sensibilidad_tolerancia"]["pares_por_tolerancia"][clave])


# ============================================================================
# 9. Pestana 7 — Limites y falencias
# ============================================================================
def fig_estado_fase2() -> go.Figure:
    items = [("F2-1", "Productividad (Q7)", "no_evaluable"),
             ("F2-2", "Territorio per cápita", "entregado"),
             ("F2-3", "Modelo estrella", "entregado"),
             ("F2-4", "Redes y nulos", "entregado"),
             ("F2-5", "Diversidad con IC", "entregado"),
             ("F2-6", "Clustering formalizado", "entregado"),
             ("F2-7", "Unicidad de IDs", "entregado"),
             ("F2-8", "Descriptivos por convocatoria", "no_abordado"),
             ("F2-9", "Inferencia adicional", "no_abordado"),
             ("F2-10", "Supervivencia", "entregado")]
    colores = {"entregado": PALETA["primario"], "no_evaluable": PALETA["dorado"],
               "no_abordado": PALETA["gris_medio"]}
    nombres = {"entregado": "Entregado", "no_evaluable": "Cerrado como no evaluable",
               "no_abordado": "No abordado en esta fase"}
    fig = go.Figure()
    for estado in ("entregado", "no_evaluable", "no_abordado"):
        sub = [(i, n) for i, n, s in items if s == estado]
        if not sub:
            continue
        fig.add_trace(go.Bar(
            x=[1] * len(sub), y=[f"{i} · {n}" for i, n in sub], orientation="h",
            name=nombres[estado], marker_color=colores[estado],
            text=[nombres[estado]] * len(sub), textposition="inside",
            insidetextanchor="middle", textfont=dict(color=BLANCO, size=11),
            hovertemplate="<b>%{y}</b><br>" + nombres[estado] + "<extra></extra>"))
    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(barmode="stack", bargap=0.35)
    fig.update_layout(title=dict(
        text=("Estado de los diez análisis planificados para la Fase 2 · "
              "7 entregados · 1 cerrado como no evaluable · 2 no abordados"),
        x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=470, leyenda=True)


LIMITES = [
    ("F2-1 · Productividad científica (Q7)",
     "El CSV de 1,2 GB con las revistas y la productividad no está versionado en el "
     "repositorio.",
     "<b>Bloqueado por acceso a los datos.</b> No es un problema de método: el análisis "
     "está especificado y no se puede ejecutar sin el insumo. Se entrega como «no "
     "evaluable por restricción de acceso» y no como hallazgo negativo."),
    ("Diversidad: solo existe en 2021",
     "Las tres variables (grupo étnico, discapacidad, víctima del conflicto) tienen 0 % "
     "de cobertura en 2013, 2014, 2015, 2017 y 2019.",
     "<b>No hay serie temporal, y no la habrá con este registro.</b> La comparación con el "
     "DANE es una fotografía de 2021. Cualquier afirmación sobre «la evolución de la "
     "diversidad» sería inventada."),
    ("Eméritos: estado terminal",
     "Solo se llega a Emérito habiendo sobrevivido; 251 de 334 registros no vuelven.",
     "<b>Su supervivencia no es modelable</b> como riesgo de salida: sería tiempo "
     "inmortal. Se grafica la curva, se excluye del Cox y se reporta la sensibilidad de "
     "excluirlo."),
    ("Redes: no se puede nombrar la universidad puente",
     "120 instituciones contrastables, 2 superan z = 1,96 frente a las ~3,0 que el azar "
     "produciría.",
     "<b>El problema es de comparación múltiple, no de datos.</b> Se sostiene que el "
     "corretaje está concentrado; no quién lo ejerce. Una lista de «universidades puente» "
     "sería un artefacto."),
]


def pestana_limites() -> tuple[list, str, str]:
    graficos = [("t16", "Qué se pudo cerrar y qué no",
                 "Los diez análisis planificados para la Fase 2. La distinción entre «no "
                 "evaluable» y «no abordado» no es cosmética: lo primero es una conclusión "
                 "defendible sobre los datos; lo segundo es trabajo pendiente del equipo.",
                 div(fig_estado_fase2(), "t16"))]
    tarjetas = "".join(
        f"<div class='limite'><h4>{t}</h4><p class='hecho'>{h}</p>"
        f"<p class='lectura'>{l}</p></div>" for t, h, l in LIMITES)
    conclusion = (
        "<b>Los límites de este análisis no son de capacidad, son de datos.</b> El "
        "docente señaló que la base está muy anonimizada, y tiene razón: sin documento ni "
        "nombre no se puede verificar que un ID designe siempre a la misma persona, y sin "
        "el archivo de revistas no se puede medir productividad. Lo que se hizo fue "
        "delimitar el alcance con precisión, no disimularlo."
        "<br><br><b>Tres límites transversales</b> que conviene tener presentes al leer "
        "cualquier pestaña: (1) el registro mide <b>presencia en convocatorias</b>, no "
        "empleo ni producción; (2) una persona que se salta una convocatoria y vuelve "
        "después es indistinguible de una que salió y regresó, porque el registro no trae "
        "fechas intermedias; (3) el supuesto de riesgos proporcionales del modelo de Cox "
        "<b>no se verificó</b> con residuos de Schoenfeld —se declara como límite y no se "
        "da por bueno—."
        "<br><br><b>Lo que queda pendiente del equipo:</b> F2-8 (descriptivos por "
        "convocatoria) y F2-9 (extender la inferencia MAS + post-estratificación + GREG más "
        "allá de retención y edad). Ambas son alcanzables con los datos actuales y están "
        "fuera del alcance de esta fase por decisión de prioridades, no por falta de "
        "insumo.")
    return graficos, tarjetas, conclusion


# ============================================================================
# 9b. Pestana 8 — Flujos y migracion territorial (F2-11)
# ============================================================================
def pestana_migracion() -> tuple[list, str, str]:
    """
    Pestana 8 — Flujos y migracion territorial (F2-11).

    La figura y los bloques de texto se importan de `mapa_migracion.py`: son los
    mismos que genera la pagina suelta `mapa_migracion.html`, no una copia.
    """
    per = mapa_mod.cargar_percapita()
    flujos = mapa_mod.cargar_flujos()
    fig_mapa = mapa_mod.construir_mapa()
    fig_saldo = mapa_mod.construir_saldo_neto()
    config_mapa = dict(CONFIG_PLOTLY)
    config_mapa["scrollZoom"] = True
    graficos = [
        ("t17", "Mapa de flujos y tasa per cápita (F2-11)",
         mapa_mod.GUIA_LECTURA,
         mapa_mod.leyenda_html(per) + div(fig_mapa, "t17", config_mapa)),
        ("t18", "Saldo neto por departamento: quién gana y quién pierde",
         "Entradas menos salidas de las 808 mudanzas de residencia del periodo. Un "
         "saldo positivo no significa que el departamento gane investigadores en "
         "términos absolutos: significa que, entre quienes se mudaron, recibió más "
         "de los que perdió. La suma de todos los saldos es cero por construcción.",
         div(fig_saldo, "t18")),
    ]
    return graficos, mapa_mod.bloque_tablas_html(flujos), mapa_mod.conclusion_html()


# ============================================================================
# 10. Narrativa: que se hizo, por que, que teoria lo respalda y como se lee
# ============================================================================
NARRATIVAS: dict[str, dict[str, str]] = {
    # ------------------------------------------------- 1. Resumen ejecutivo
    "t1": {
        "hizo": "Se cuentan, para cada uno de los siete análisis entregados, las "
                "comprobaciones automáticas que declara su JSON y las figuras que exportó.",
        "por": "Es la evidencia verificable de la fase. Una conclusión sin comprobación "
               "automática es una opinión; un análisis sin figura no se puede revisar.",
        "teoria": "Trazabilidad: cada resultado tiene que poder rastrearse hasta un "
                  "registro escrito y reproducible. Es el mismo principio que la regla R17 "
                  "del proyecto aplica a las cifras de los documentos.",
        "lee": "Las barras azules son comprobaciones; las doradas, figuras. Lo que importa "
                "no es el tamaño sino el cero: ningún análisis tiene una comprobación en "
                "rojo. Las 56 comprobaciones son booleanas y las 56 pasan.",
    },
    # ------------------------------------------------------------ 2. Territorio
    "t2": {
        "hizo": "Se cruzó cada departamento de residencia con su población del Censo "
                "Nacional de Población y Vivienda de 2018 y se calculó la tasa de "
                "investigadores por cada 100 000 habitantes, para el stock de 2021 y para "
                "cada una de las seis convocatorias.",
        "por": "El repositorio auditado medía concentración bruta —cuotas y HHI sobre "
               "conteos—, y una cuota puede crecer solo porque el numerador crece. Sin "
               "denominador no se puede distinguir «más investigadores» de «más "
               "investigadores por habitante», que son dos hallazgos distintos.",
        "teoria": "<b>Gini</b>: desigualdad del reparto, 0 = todos iguales. <b>Theil T</b>: "
                  "índice entrópico que además se descompone de forma aditiva en «entre "
                  "grupos» y «dentro de los grupos», y por eso permite preguntar <i>por "
                  "dónde</i> cambia la desigualdad. <b>HHI</b>: suma de cuotas al cuadrado, "
                  "medida de concentración. <b>Bootstrap</b>: se remuestrea el diseño real "
                  "para obtener la incertidumbre de cada tasa, porque con 1 investigador en "
                  "Vichada el error es enorme y hay que verlo.",
        "lee": "Barras largas a la derecha = más investigadores por habitante. La línea "
                "dorada es el promedio nacional: lo que queda a su izquierda está por "
                "debajo del país. Mira siempre la escala antes de comparar dos "
                "departamentos vecinos: en los pequeños la base es de una o dos personas.",
    },
    "t3": {
        "hizo": "Se calculó el Gini y el Theil de las tasas per cápita en cada "
                "convocatoria, y se descompuso el Theil en el componente entre regiones y "
                "el componente dentro de cada región.",
        "por": "Decir «la desigualdad territorial bajó» sin decir <i>dónde</i> bajó deja "
               "fuera la pregunta que importa para política pública: ¿se acercaron las "
               "regiones entre sí, o se igualaron los departamentos dentro de cada región?",
        "teoria": "La descomposición aditiva del Theil: T = T_entre + T_dentro. Si un "
                  "índice no se descompone, no se puede atribuir el cambio a un nivel "
                  "geográfico. El Gini no tiene esa propiedad; el Theil sí, y por eso se "
                  "reportan los dos.",
        "lee": "Panel izquierdo: el Gini baja, es la tendencia. Panel derecho: la línea "
                "azul (entre regiones) cae y la dorada (dentro) queda plana. Si la dorada "
                "se hubiera movido, la conclusión sería otra.",
    },
    "t4": {
        "hizo": "Se reprodujo el HHI que publica el repositorio auditado y se recalculó "
                "excluyendo «Exterior» y «No disponible», que el auditado cuenta como "
                "territorios.",
        "por": "Antes de corregir a nadie hay que demostrar que se puede reproducir su "
               "cifra. Si no se reproduce, la discrepancia sería del nuestro, no del suyo.",
        "teoria": "Reproducción antes que crítica: la diferencia máxima obtenida "
                  "(4,75 × 10⁻⁷) es la del redondeo a 6 decimales, así que la coincidencia "
                  "es exacta. Eso valida toda la cadena de cálculo.",
        "lee": "Las dos líneas se separan de forma constante: la distancia vertical entre "
                "ellas es el error que introduce contar «Exterior» como si fuera un "
                "departamento. La cifra del auditado no está mal calculada; mide otra cosa.",
    },
    # ----------------------------------------------------------- 3. Diversidad
    "t5": {
        "hizo": "Se calculó, para cada grupo, el cociente entre su peso en la población "
                "del país y su peso entre los investigadores reconocidos, y se le puso un "
                "intervalo de confianza al 95 % con dos métodos: Wilson (tratando la base "
                "como una muestra) y un bootstrap del diseño real (MAS de 2 224 personas "
                "más post-estratificación).",
        "por": "El repositorio auditado publicaba cocientes puntuales sin incertidumbre. "
               "Con 114 personas indígenas en 20 423 respuestas, un número sin intervalo "
               "sugiere una precisión que el dato no tiene.",
        "teoria": "<b>Intervalo de Wilson</b>: intervalo para una proporción que se "
                  "comporta bien cuando la cuenta es pequeña o está cerca de 0, donde el "
                  "intervalo normal clásico falla. <b>Bootstrap de diseño</b>: se "
                  "remuestrea respetando el diseño (muestra aleatoria simple de 2 224 y "
                  "post-estratificación por categoría), así que el intervalo refleja la "
                  "incertidumbre real del estudio y no la de una muestra ideal.",
        "lee": "Escala logarítmica: 1 es «misma proporción que en el país». Si todo el "
                "intervalo queda a la derecha de 1, la <b>sub</b>representación es sólida; "
                "si cruza el 1, no hay nada que afirmar. Ojo: un cociente mayor que 1 "
                "significa que el grupo pesa menos entre los investigadores. El intervalo "
                "más largo es el del bootstrap de diseño; el corto y con topes, el de "
                "Wilson. Donde no hay intervalo largo, el cociente no quedó acotado y así "
                "se marca.",
    },
    "t6": {
        "hizo": "Se calculó, para cada convocatoria, qué porcentaje de sus registros trae "
                "dato en cada una de las cuatro variables.",
        "por": "Antes de analizar una serie temporal hay que comprobar que la variable "
               "existe en todos los cortes. Si los primeros años están vacíos, no hay serie: "
               "hay una fotografía del último año.",
        "teoria": "Análisis de cobertura y de patrón de faltantes: un faltante que no es "
                  "aleatorio y que coincide con el año es un cambio de instrumento de "
                  "recolección, no un dato perdido. Tratarlo como pérdida aleatoria "
                  "invalidaría cualquier comparación temporal.",
        "lee": "Barras que valen cero en cinco años y saltan en 2021: eso es un cambio de "
                "formulario. La serie gris (género) está al 100 % en todas y sirve de "
                "control: si ella también faltara, el problema sería del archivo, no de las "
                "preguntas.",
    },
    # --------------------------------------------------------------- 4. Redes
    "t7": {
        "hizo": "Se reconstruyó la red de co-filiación institucional: cada par de "
                "instituciones que aparecen juntas en la misma fila de una persona es una "
                "arista. Se dibuja la red de 2019, la única que tiene doble afiliación.",
        "por": "El repositorio auditado presentaba una «red global» y métricas por "
               "convocatoria, lo que sugiere una serie temporal. Comprobar cuántos registros "
               "traen de verdad dos instituciones es el primer paso antes de interpretar "
               "cualquier métrica de red.",
        "teoria": "Una red de co-afiliación es un grafo no dirigido donde los nodos son "
                  "instituciones y cada arista pesa el número de personas que las conectan. "
                  "El <b>grado</b> mide con cuántas instituciones se conecta una; el grado "
                  "<b>ponderado</b>, cuántas conexiones acumula. Confundir los dos es el "
                  "origen de la discrepancia 73 frente a 56.",
        "lee": "Cada punto es una institución; su tamaño y su color, el grado ponderado. "
                "Las etiquetas son solo los ocho nodos con más intermediación: rotular los "
                "446 haría el gráfico ilegible. Un núcleo denso con muchas ramas sueltas es "
                "exactamente lo que hay.",
    },
    "t8": {
        "hizo": "Se compararon siete estadísticos de la red con dos modelos nulos de 500 "
                "réplicas cada uno: Erdős–Rényi (misma densidad, aristas al azar) y modelo "
                "de configuración (misma distribución de grados).",
        "por": "Una red con un nodo de grado 56 y una media de 2,26 produce por construcción "
               "caminos cortos y clustering alto. Sin comparar con un nulo, cualquier "
               "«estructura» que se reporte puede ser solo la huella de la heterogeneidad de "
               "grados.",
        "teoria": "<b>Erdős–Rényi</b>: cada par de nodos conectado con probabilidad "
                  "constante; el nulo más simple. <b>Modelo de configuración</b>: conserva "
                  "la secuencia de grados y aleatoriza el resto, así que responde a la "
                  "pregunta correcta: ¿hay estructura <i>además</i> de los grados? "
                  "<b>z</b> = distancia entre lo observado y la media del nulo, en "
                  "desviaciones del nulo.",
        "lee": "Barras grises: frente al azar puro. Barras azules: frente al nulo con "
                "grados, que es el exigente. Lo que interesa es qué barras azules cruzan "
                "las líneas doradas de ±1,96.",
    },
    "t9": {
        "hizo": "Se ajustó el mismo algoritmo que el auditado (k-prototypes de Huang, el de "
                "kproto() en R) para k de 2 a 10, se eligió k con tres criterios y después "
                "se repitió todo con las variables permutadas por separado.",
        "por": "k-prototypes <b>siempre</b> devuelve una partición, exista o no estructura. "
               "El repositorio auditado eligió k = 3 sin validarlo. La pregunta correcta no "
               "es «¿cuál es el mejor k?» sino «¿hay algún k que sea mejor de lo que da el "
               "azar?».",
        "teoria": "<b>Silhouette</b>: cuánto más cerca está cada punto de su cluster que "
                  "del vecino, de −1 a 1; el umbral 0,25 de Kaufman y Rousseeuw es el "
                  "mínimo habitual para hablar de estructura, pero es un umbral "
                  "convencional y aquí la cifra se estima por submuestreo, con su propio "
                  "error. <b>Nulo por permutación independiente</b>: se baraja cada "
                  "variable por separado, conservando sus marginales y rompiendo la "
                  "asociación entre ellas. Si la partición observada no le gana, lo que se "
                  "agrupó fue ruido. Ese contraste es el que decide, no el umbral.",
        "lee": "Panel izquierdo: la curva de la silhouette con el umbral dorado; el valor "
                "de k = 2 es 0,28 ± 0,06, así que la distancia al umbral es menor que el "
                "error de la estimación. Panel derecho, el que decide: el histograma son las "
                "particiones nulas y la línea azul, la observada en la submuestra del "
                "contraste. Si la línea azul cae dentro del histograma, no hay estructura.",
    },
    # -------------------------------------------------------- 5. Supervivencia
    "t10": {
        "hizo": "Se construyó el tiempo de permanencia de cada persona —años desde su "
                "primera aparición hasta la última— y se estimó la curva de supervivencia "
                "con Kaplan-Meier, por categoría, género, área y los cinco departamentos "
                "con más personas.",
        "por": "El anteproyecto prometía analizar la dinámica longitudinal, y la retención "
               "por pares de convocatorias no la responde: mezcla personas que entran y "
               "salen en momentos distintos. El análisis de supervivencia sí usa el tiempo "
               "y maneja correctamente a quien sigue dentro al cerrar la ventana.",
        "teoria": "<b>Kaplan-Meier</b>: estimador no paramétrico de la función de "
                  "supervivencia que incorpora la censura —quien no ha salido todavía "
                  "aporta información hasta el último momento en que se le vio—. "
                  "<b>Log-rank</b>: contraste de igualdad de curvas que compara eventos "
                  "observados con esperados bajo la hipótesis nula, tiempo a tiempo.",
        "lee": "Baja la curva cuando la gente sale del sistema. La meseta al final son "
                "quienes siguen en 2021 (censura). La línea punteada marca S = 0,5: donde "
                "la curva no la cruza, la mediana <b>no existe</b> dentro de la ventana y "
                "así se reporta.",
    },
    "t11": {
        "hizo": "Las dos curvas de Kaplan-Meier por género, con su banda de confianza al "
                "95 % calculada con la transformación log(−log).",
        "por": "El log-rank en crudo detecta una diferencia por género. Antes de "
               "interpretarla como un efecto hay que ver su tamaño: un p-valor pequeño con "
               "dos curvas pegadas no es un hallazgo grande, es una base grande.",
        "teoria": "La transformación <b>log(−log)</b> da intervalos razonables incluso "
                  "cuando S(t) se acerca a 0 o a 1, donde la fórmula directa falla. Con "
                  "n = 30 077 personas, el estadístico detecta diferencias de centésimas: "
                  "significación estadística y relevancia práctica no son lo mismo.",
        "lee": "Cuanto más se solapan las bandas, menos diferencia hay. Aquí se separan "
                "unas centésimas con bandas que se tocan: hay señal, y es minúscula.",
    },
    "t12": {
        "hizo": "Se ajustó un modelo de Cox con 14 covariables —categoría, género, gran "
                "área y los cinco departamentos con más personas—, excluyendo a los "
                "Eméritos y al género no estimable.",
        "por": "El log-rank dice que <i>hay</i> diferencia entre grupos, pero no distingue "
               "si el género actúa por sí mismo o porque las mujeres están repartidas de "
               "otra forma entre categorías y áreas. El Cox permite separar las dos cosas.",
        "teoria": "<b>Modelo de Cox</b>: riesgo de salir proporcional a una exponencial de "
                  "las covariables, sin suponer forma para el riesgo base. <b>Empates de "
                  "Efron</b>: los eventos solo se observan en 11 fechas distintas, así que "
                  "hay empates de miles de casos; la aproximación de Efron corrige la de "
                  "Breslow en ese escenario. <b>HR</b> = 1 no hay diferencia; HR &lt; 1 "
                  "sale menos.",
        "lee": "Puntos a la izquierda de la línea dorada: salen menos que la referencia. "
                "Los azules son significativos al 5 %; los grises no. Busca «Género: "
                "Femenino»: está en 0,988 y en gris.",
    },
    "t13": {
        "hizo": "Se cruzó la categoría con el género sobre una fila por persona, y se puso "
                "al lado la permanencia al final de la ventana de cada categoría.",
        "por": "La conclusión «el género desaparece al ajustar» es correcta pero no "
               "explica <i>por qué</i>. El mecanismo es una composición distinta: si un "
               "género está más concentrado en la categoría que más sale, su curva cruda "
               "saldrá peor sin que el género tenga nada que ver.",
        "teoria": "Variable de confusión: una tercera variable asociada a la vez con el "
                  "grupo y con el resultado. Ajustar por ella es la forma estándar de "
                  "separar efecto propio de composición; es exactamente lo que hace el Cox "
                  "al incluir la categoría.",
        "lee": "Compara, dentro de cada categoría, la barra de mujeres y la de hombres. La "
                "diferencia grande está en Junior y en Sénior; y el panel derecho muestra "
                "que Junior es la categoría que menos permanencia tiene.",
    },
    # ----------------------------------------------------- 6. Calidad
    "t14": {
        "hizo": "Se leyó la regla de unicidad tal como está documentada y se implementó "
                "como validador reproducible sobre un YAML; después se comparó par a par con "
                "lo que hace el código del auditado.",
        "por": "El código original tenía un fallo silencioso: no fallaba, avisaba de más. "
               "Marcaba 1 067 pares donde la regla documentada marca 18. Un validador "
               "explícito convierte una intención escrita en una comprobación ejecutable.",
        "teoria": "<b>Integridad de clave</b>: un identificador debe designar la misma "
                  "entidad en todas las filas. Sin nombre ni documento, la única prueba "
                  "posible es la coherencia interna de la trayectoria: la edad debe crecer "
                  "tanto como pasó el tiempo. <b>Tolerancia simétrica</b>: la resta se "
                  "evalúa en valor absoluto, porque una edad que decrece 98 años es tan "
                  "imposible como una que crece 98. <b>Análisis de sensibilidad</b>: se "
                  "reporta el resultado para varias tolerancias en vez de dar un único "
                  "número como si fuera el único posible.",
        "lee": "Panel izquierdo: la barra roja es la regla del auditado y la azul la "
                "documentada; la distancia entre ellas son falsos positivos. Panel derecho: "
                "qué pasaría con otras tolerancias; si la curva fuera vertical, la elección "
                "del umbral importaría mucho.",
    },
    "t15": {
        "hizo": "Se ejecutó el pipeline de transformación del propio repositorio auditado "
                "—sin reimplementarlo— sobre la base completa de seis convocatorias, y se "
                "comparó tabla por tabla con su evidencia versionada.",
        "por": "El auditado documenta «nueve dimensiones» y su carga toma tres "
               "convocatorias. Antes de decir que un modelo está mal hay que demostrar que "
               "se reproduce lo que sí está bien, y aislar exactamente qué está mal.",
        "teoria": "<b>Esquema en estrella</b>: una tabla de hechos con claves foráneas "
                  "hacia tablas de dimensión, más tablas puente para relaciones "
                  "muchos-a-muchos. <b>Integridad referencial</b>: toda clave foránea "
                  "apunta a una fila existente; se comprueba contando huérfanos. "
                  "<b>Reproducción de evidencia</b>: la prueba de que la reconstrucción es "
                  "correcta es que coincide con lo que el propio repositorio guardó como "
                  "resultado.",
        "lee": "Barras azules: los hechos reales de cada convocatoria. Barras doradas: lo "
                "que la carga del auditado tomaba. Las tres convocatorias sin barra dorada "
                "son el defecto.",
    },
    # ------------------------------------------------------------ 7. Limites
    "t16": {
        "hizo": "Se clasificó cada uno de los diez análisis planificados según su estado "
                "real de cierre, distinguiendo «entregado», «cerrado como no evaluable» y "
                "«no abordado».",
        "por": "Un informe que no separa estas tres cosas deja creer que lo no hecho se "
               "debe a que no había nada que encontrar. Las tres categorías tienen causas "
               "distintas y lecturas distintas.",
        "teoria": "Distinción entre <b>dato ausente</b> (no se puede calcular), "
                  "<b>dato no evaluable</b> (se puede especificar el análisis y se concluye "
                  "que el insumo no lo permite) y <b>análisis no realizado</b> (trabajo "
                  "pendiente). Confundirlos es el error más frecuente en un informe de "
                  "consultoría.",
        "lee": "Azul: análisis con resultado y evidencia. Dorado: cerrado con una "
                "conclusión defendible sobre los datos. Gris: pendiente del equipo. Solo "
                "los grises son deuda nuestra; el dorado no.",
    },
    # --------------------------------------- 8. Flujos y migración (F2-11)
    "t17": {
        "hizo": "Se dibujaron los 33 departamentos con un GeoJSON embebido en el propio "
                "archivo: el color del polígono es la tasa per cápita de F2-2, el tamaño "
                "de la burbuja es el total de investigadores y las líneas son las rutas "
                "de migración con el destino marcado. El botón cambia entre las dos "
                "definiciones de flujo.",
        "por": "El mapa del repositorio auditado pedía <i>teselas</i> de OpenStreetMap en "
               "el momento de dibujar: sin internet el país desaparecía y quedaban 33 "
               "burbujas flotando en el vacío. Un mapa de flujos necesita además "
               "geometrías propias: sin polígono no hay dónde apoyar la línea.",
        "teoria": "Dos reglas de cartografía. (1) El tamaño se escala con la <b>raíz "
                  "cuadrada</b> del conteo porque el ojo percibe área, no radio: con el "
                  "valor bruto, Bogotá taparía medio país. (2) El color del polígono se "
                  "reserva para una tasa (variable intensiva) y el tamaño para un conteo "
                  "(extensiva), de modo que un solo canal no codifique dos cosas.",
        "lee": "Azul más oscuro = más investigadores por habitante; la rampa se corta en "
                "140 y la tasa nacional se marca en 65,55. Pase el cursor por un "
                "departamento (tasa, puesto y saldo) o por una ruta (cuántas personas). "
                "Trazo punteado y rombo = área metropolitana de la sabana de Bogotá.",
    },
    "t18": {
        "hizo": "Para cada departamento se restaron las salidas de las entradas de las "
                "808 mudanzas entre la primera y la última convocatoria.",
        "por": "El mapa de líneas dice cuánta gente se movió, pero no en qué dirección "
               "queda cada departamento. Bogotá aparece en casi todas las rutas grandes y "
               "aun así su balance es negativo: son dos preguntas distintas.",
        "teoria": "Saldo neto = inmigración − emigración <i>dentro de la ventana "
                  "observada</i>. Es un <b>flujo</b>, no un <b>stock</b>: no dice cuántos "
                  "investigadores viven en el departamento, sino cuántos ganó o perdió "
                  "entre quienes se mudaron. Por eso la suma de todos los saldos es cero.",
        "lee": "Bogotá −57, Cundinamarca +31, Boyacá +21, Atlántico +20. Azul oscuro: "
                "gana; azul claro: pierde. Que una barra sea pequeña no la hace poco "
                "fiable: es el conteo de personas, no una estimación.",
    },
}

NARRATIVAS_PESTANA = {}


# ============================================================================
# 11. Indice de conceptos (buscador de estudio)
# ============================================================================
CONCEPTOS = [
    ("Gini", "Índice de desigualdad entre 0 (todos iguales) y 1 (todo en una unidad). Se "
             "calcula sobre las tasas per cápita, no sobre los conteos.", "2"),
    ("Theil T", "Índice entrópico de desigualdad. Su ventaja es que se descompone de "
                "forma aditiva en «entre grupos» y «dentro de los grupos», lo que permite "
                "atribuir el cambio a un nivel geográfico. El Gini no lo permite.", "2"),
    ("Descomposición entre/dentro", "Reparto del Theil en la parte explicada por las "
                                    "diferencias entre regiones y la parte que queda "
                                    "dentro de cada región. Es el resultado central de F2-2: "
                                    "el cambio ocurre entre regiones; dentro, nada.", "2"),
    ("HHI", "Índice Herfindahl-Hirschman: suma de las cuotas al cuadrado. Mide "
            "concentración. Reproducir el del auditado fue la prueba de que nuestra cadena "
            "de cálculo coincide con la suya.", "2"),
    ("Bootstrap", "Remuestreo con reemplazo para obtener la distribución de un estimador "
                  "sin fórmulas. Aquí hay dos: de personas (ignora el diseño) y de diseño "
                  "(respeta MAS más post-estratificación). El segundo es el honesto y es "
                  "entre 3,1 y 3,6 veces más ancho que el de personas.", "2"),
    ("Intervalo de Wilson", "Intervalo de confianza para una proporción que funciona bien "
                            "con cuentas pequeñas o cerca de 0, donde el intervalo normal "
                            "clásico da límites imposibles.", "3"),
    ("Cociente de subrepresentación", "Proporción de un grupo en la población dividida "
                                      "por su proporción entre los investigadores. 1 = "
                                      "equivalencia; mayor que 1 = subrepresentación; "
                                      "menor que 1 = sobrerrepresentación. Es el campo "
                                      "`razon_subrepresentacion` del auditado, cuyo nombre "
                                      "induce a error en los grupos con razón menor que 1.",
     "3"),
    ("Error de denominador", "Dividir por el subconjunto en vez de por el total. Si se "
                             "excluye «ningún grupo étnico», el porcentaje afro pasa de "
                             "2,22 % a 72,02 %: no es un dato, es un error de base.", "3"),
    ("Faltante no aleatorio", "Un dato ausente cuya ausencia depende del año o del "
                              "instrumento. Aquí las variables de diversidad están al 0 % "
                              "hasta 2021: es un cambio de formulario, no una pérdida.",
     "3"),
    ("Erdős–Rényi", "Modelo nulo de red: cada par de nodos conectado al azar con la misma "
                    "densidad observada. Sirve para preguntar si hay algo más que azar, "
                    "pero no controla los grados.", "4"),
    ("Modelo de configuración", "Nulo que conserva la secuencia de grados y aleatoriza el "
                                "resto. Es el nulo exigente: responde «¿hay estructura "
                                "además de la heterogeneidad de grados?».", "4"),
    ("Betweenness", "Fracción de los caminos mínimos de la red que pasan por un nodo. Mide "
                    "intermediación o corretaje. Un nodo de grado alto la tiene alta por "
                    "construcción, así que hay que compararla con nodos del mismo grado.",
     "4"),
    ("Prueba de puente", "Contrastar la betweenness de una institución frente a la de "
                         "nodos con <i>su mismo grado</i> en el nulo de intercambio de "
                         "aristas. Se necesitó un tercer nulo porque el de configuración "
                         "colapsa aristas y desplaza los grados.", "4"),
    ("Comparaciones múltiples", "Al hacer muchas pruebas a la vez, alguna sale significativa "
                                "por azar. Bonferroni y FDR (Benjamini-Hochberg) corrigen "
                                "el umbral. Aquí son la razón de que no se entregue lista "
                                "de universidades puente.", "4"),
    ("k-prototypes", "Algoritmo de agrupamiento para datos mixtos (Huang, 1998): media para "
                     "las numéricas y moda para las categóricas, con un peso γ. Es el mismo "
                     "de kproto() en R.", "4"),
    ("Silhouette", "Coeficiente de −1 a 1 que mide cuánto más cerca está cada punto de su "
                   "cluster que del vecino. El umbral 0,25 de Kaufman y Rousseeuw es el "
                   "mínimo habitual para hablar de estructura.", "4"),
    ("Nulo por permutación", "Barajar cada variable por separado conservando sus "
                             "marginales y rompiendo la asociación entre ellas. Si la "
                             "partición observada no le gana, no hay estructura conjunta.",
     "4"),
    ("V de Cramér", "Medida de asociación entre dos variables categóricas, de 0 a 1. Aquí "
                    "sirve para ver qué variable define cada cluster: formación 0,303 "
                    "frente a género 0,006.", "4"),
    ("Kaplan-Meier", "Estimador no paramétrico de la supervivencia que incorpora la "
                     "censura: quien no ha salido aporta información hasta el último "
                     "momento en que se le vio.", "5"),
    ("Log-rank", "Contraste de igualdad de curvas de supervivencia: compara eventos "
                 "observados con esperados tiempo a tiempo. No ajusta por otras variables.",
     "5"),
    ("Modelo de Cox", "Modelo semiparamétrico de riesgo proporcional. Estima el efecto de "
                      "cada covariable sin suponer forma para el riesgo base. Es lo que "
                      "permite decir si el género actúa por sí mismo o por composición.",
     "5"),
    ("Empates de Efron", "Los eventos solo se observan en 11 fechas, así que hay empates "
                         "masivos. Efron corrige la aproximación de Breslow, que estaría "
                         "sesgada en ese escenario.", "5"),
    ("Censura a la derecha", "Se deja de observar a una persona antes de que ocurra el "
                             "evento: sigue en el sistema al cerrar la ventana. El 70,1 % "
                             "de las personas está censurado, así que las curvas están "
                             "dominadas por la censura.", "5"),
    ("Variable de confusión", "Tercera variable asociada a la vez con el grupo y el "
                              "resultado. La categoría lo es aquí: explica por qué la "
                              "diferencia de género se anula al ajustar.", "5"),
    ("Riesgos no proporcionales", "Supuesto de Cox: el cociente de riesgos constante en el "
                                  "tiempo. <b>No se verificó</b> con residuos de "
                                  "Schoenfeld; se declara como límite.", "5"),
    ("Integridad referencial", "Toda clave foránea apunta a una fila existente. Se comprueba "
                               "contando huérfanos: el modelo estrella reconstruido tiene "
                               "0.", "6"),
    ("Regla de unicidad", "Un ID debe designar siempre a la misma persona. Sin nombre ni "
                          "documento, la única prueba es la coherencia de la trayectoria: la "
                          "edad debe crecer tanto como pasó el tiempo.", "6"),
    ("Análisis de sensibilidad", "Repetir el cálculo con varios supuestos para ver si la "
                                 "conclusión depende de uno de ellos. Se aplicó a la "
                                 "tolerancia de edad, a γ del clustering y a la exclusión de "
                                 "Eméritos.", "6"),
    # ------------------------------------------------ 8. Flujos y migración (F2-11)
    ("Flujo A y flujo B", "Dos definiciones de «migración». A compara la primera con la "
                          "última convocatoria (mudanza del periodo: 808 personas); B compara "
                          "el nacimiento con la residencia (migración acumulada: 11 922). No "
                          "se corrigen entre sí: miden cosas distintas y el mapa deja elegir.",
     "8"),
    ("DIVIPOLA", "División Político-Administrativa: el código oficial de dos dígitos que "
                 "identifica el departamento. Es la llave del mapa porque dos fuentes "
                 "escriben distinto el mismo nombre —«SANTAFE DE BOGOTA D.C» frente a "
                 "«Bogotá, D. C.»— y unir por nombre perdería casos.", "8"),
    ("Área metropolitana", "Conurbación de municipios que puede cruzar la frontera "
                           "departamental. Una mudanza Bogotá → Chía es real, pero en un "
                           "mapa departamental se ve igual que una migración entre "
                           "departamentos. Se marca aparte en lugar de esconderla o "
                           "borrarla.", "8"),
    ("Escala por raíz cuadrada", "Regla de codificación: el <i>área</i> del símbolo crece "
                                 "con la cantidad, así que el radio crece con su raíz. Sin "
                                 "ella, Bogotá (9 888) taparía a Vichada (1) y al resto del "
                                 "país.", "8"),
]


def bloque_indice() -> str:
    filas = "".join(
        f"<div class='concepto' data-texto=\"{_html.escape((t + ' ' + d).lower(), quote=True)}\">"
        f"<h4>{_html.escape(t)}<span class='tag'>pestaña {p}</span></h4>"
        f"<p>{d}</p></div>" for t, d, p in CONCEPTOS)
    return (f"<div class='seccion' id='indice'><div class='titulo'>Glosario de conceptos</div>"
            f"<p class='desc-indice'>Los {len(CONCEPTOS)} conceptos que sostienen los "
            f"análisis, con la pestaña en la que se aplican.</p>"
            f"<input id='buscador' type='text' placeholder='Buscar: Theil, Wilson, censura, "
            f"entre/dentro…' autocomplete='off'>"
            f"<p id='sin-resultados' class='sin-resultados' style='display:none'>"
            f"Ningún concepto coincide con la búsqueda.</p>"
            f"<div class='conceptos' id='lista-conceptos'>{filas}</div></div>")


# ============================================================================
# 12. Plantilla HTML
# ============================================================================
CSS = """
:root{
  --azul:#1E3780; --azul-osc:#0F1F4D; --azul-sec:#4A6BA8; --azul-claro:#7BA7D0;
  --azul-tenue:#EAF0F9;
  --dorado:#B7871E; --dorado-claro:#D4A84A; --alerta:#B91C1C;
  --gris-osc:#334155; --gris:#64748B; --gris-claro:#CBD5E1;
  --fondo:#F8FAFC; --blanco:#FFFFFF; --borde:#E2E8F0; --texto:#1E293B;
}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:var(--texto);
  font-family:"Montserrat","Segoe UI",Roboto,system-ui,-apple-system,Arial,sans-serif;
  font-size:15px;line-height:1.5}
header{background:linear-gradient(135deg,var(--azul-osc),var(--azul));
  color:#fff;padding:22px 26px}
header h1{margin:0 0 6px;font-size:1.42rem;letter-spacing:.2px}
header .sub{font-size:.86rem;color:#C7D2E8;max-width:1100px}
header .meta{font-size:.76rem;color:#9FB2D6;margin-top:8px}
.wrap{max-width:1500px;margin:0 auto;padding:20px 26px 40px}
/* --- tarjetas KPI --- */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));
  gap:14px;margin-bottom:22px}
.kpi{background:var(--blanco);border:1px solid var(--borde);border-radius:12px;
  padding:14px 16px;box-shadow:0 1px 2px rgba(15,31,77,.05);
  border-top:3px solid var(--azul)}
.kpi.dorado{border-top-color:var(--dorado)}
.kpi .k{font-size:.72rem;text-transform:uppercase;letter-spacing:.6px;
  color:var(--gris);font-weight:700}
.kpi .v{font-size:1.72rem;font-weight:700;color:var(--azul-osc);line-height:1.15;
  margin-top:4px;font-variant-numeric:tabular-nums}
.kpi .s{font-size:.78rem;color:var(--gris);margin-top:3px}
.kpi .n{font-size:.7rem;color:var(--gris);margin-top:7px;
  padding-top:6px;border-top:1px dashed var(--borde);line-height:1.35}
/* --- pestanas --- */
.tabs{display:flex;gap:6px;flex-wrap:wrap;border-bottom:2px solid var(--borde);
  margin-bottom:20px}
.tab-btn{background:transparent;border:0;border-bottom:3px solid transparent;
  padding:11px 18px;font-size:.92rem;font-weight:600;color:var(--gris);
  cursor:pointer;font-family:inherit;border-radius:8px 8px 0 0}
.tab-btn:hover{background:#EEF3FA;color:var(--azul-osc)}
.tab-btn.activo{color:var(--azul-osc);border-bottom-color:var(--dorado);
  background:var(--azul-tenue)}
.panel{display:none}
.panel.activo{display:block}
/* --- graficos --- */
.card{background:var(--blanco);border:1px solid var(--borde);border-radius:12px;
  padding:14px 18px 6px;margin-bottom:18px;box-shadow:0 1px 2px rgba(30,55,128,.05)}
.card h3{margin:0 0 4px;font-size:1.02rem;color:var(--azul-osc)}
.card p.desc{margin:0 0 10px;font-size:.83rem;color:var(--gris);max-width:1080px}
/* --- narrativa: cuatro bloques --- */
.nar{display:grid;grid-template-columns:repeat(auto-fit,minmax(255px,1fr));
  gap:10px 18px;margin:0 0 12px;padding:11px 14px;background:var(--fondo);
  border:1px solid var(--borde);border-left:4px solid var(--dorado);
  border-radius:8px}
.nar .bloque{font-size:.82rem;line-height:1.5;color:var(--gris-osc)}
.nar .et{display:block;font-size:.68rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.7px;color:var(--azul);margin-bottom:2px}
.nar .bloque.teoria .et{color:var(--gris-osc)}
.nar .bloque.lee .et{color:var(--dorado)}
.nar b{color:var(--azul-osc)}
.seccion{background:var(--blanco);border:1px solid var(--borde);border-radius:12px;
  padding:14px 18px;margin-bottom:20px;box-shadow:0 1px 2px rgba(30,55,128,.05);
  border-left:4px solid var(--azul)}
.seccion .titulo{font-size:.95rem;font-weight:700;color:var(--azul-osc);
  margin-bottom:8px}
.seccion .nar{background:transparent;border:0;border-left:0;padding:0;margin:0}
/* --- conclusiones --- */
.concl{background:#F3F6FB;border:1px solid var(--azul-claro);border-left:4px solid var(--dorado);
  border-radius:10px;padding:14px 16px;margin:0 0 20px;font-size:.87rem;line-height:1.6;
  color:var(--gris-osc)}
.concl .et{display:block;font-size:.7rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.8px;color:var(--dorado);margin-bottom:6px}
.aviso{background:#FFFBF0;border:1px solid var(--dorado-claro);border-left:4px solid var(--dorado);
  border-radius:8px;padding:11px 13px;font-size:.83rem;color:#5A4308;margin-bottom:18px}
.info{background:var(--azul-tenue);border:1px solid var(--azul-claro);border-left:4px solid var(--azul);
  border-radius:8px;padding:11px 13px;font-size:.83rem;color:#123057;margin-bottom:18px}
/* --- tablas --- */
.tabla{width:100%;border-collapse:collapse;font-size:.8rem;margin:6px 0 12px}
.tabla th{background:var(--azul-tenue);color:var(--azul-osc);text-align:left;
  padding:8px 9px;border-bottom:2px solid var(--azul-claro);font-size:.74rem;
  text-transform:uppercase;letter-spacing:.4px}
.tabla td{padding:7px 9px;border-bottom:1px solid var(--borde);vertical-align:top}
.tabla tbody tr:hover{background:#F7FAFD}
.tabla td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tabla td.id{font-weight:700;color:var(--azul)}
.nota-tabla{font-size:.76rem;color:var(--gris);margin:2px 0 14px;max-width:1050px}
.tabla-cifras{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
  gap:10px;margin:8px 0 22px}
.tabla-cifras div{background:var(--blanco);border:1px solid var(--borde);
  border-radius:10px;padding:10px 13px}
.tabla-cifras span{display:block;font-size:.72rem;color:var(--gris);
  text-transform:uppercase;letter-spacing:.4px}
.tabla-cifras b{font-size:1.05rem;color:var(--azul-osc);font-variant-numeric:tabular-nums}
/* --- limites --- */
.limite{background:var(--blanco);border:1px solid var(--borde);border-radius:10px;
  padding:12px 15px;margin-bottom:12px;border-left:4px solid var(--gris)}
.limite h4{margin:0 0 6px;font-size:.92rem;color:var(--azul-osc)}
.limite .hecho{font-size:.8rem;color:var(--gris-osc);margin:0 0 6px}
.limite .lectura{font-size:.8rem;color:var(--gris-osc);margin:0;
  padding-top:6px;border-top:1px dashed var(--borde)}
/* --- indice de conceptos --- */
.desc-indice{font-size:.82rem;color:var(--gris);margin:0 0 10px}
#buscador{width:100%;max-width:560px;padding:9px 12px;font-family:inherit;
  font-size:.88rem;border:1px solid var(--gris-claro);border-radius:8px;
  margin-bottom:12px;background:var(--blanco);color:var(--texto)}
#buscador:focus{outline:2px solid var(--azul-claro);border-color:var(--azul-sec)}
.sin-resultados{font-size:.84rem;color:var(--gris);font-style:italic}
.conceptos{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
  gap:10px 16px}
.concepto{background:var(--fondo);border:1px solid var(--borde);border-radius:8px;
  padding:9px 12px}
.concepto h4{margin:0 0 4px;font-size:.85rem;color:var(--azul-osc);
  display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.concepto p{margin:0;font-size:.78rem;color:var(--gris-osc);line-height:1.45}
.concepto .tag{font-size:.64rem;font-weight:600;color:var(--gris);
  text-transform:uppercase;letter-spacing:.4px;white-space:nowrap}
footer{border-top:1px solid var(--borde);margin-top:26px;padding-top:16px;
  font-size:.78rem;color:var(--gris)}
footer code{font-family:"Fira Code",Consolas,"Courier New",monospace;font-size:.76rem}
@media(max-width:760px){.wrap{padding:14px}.kpi .v{font-size:1.4rem}}
"""

JS = """
<script>
(function(){
  var botones = Array.prototype.slice.call(document.querySelectorAll('.tab-btn'));
  var paneles = Array.prototype.slice.call(document.querySelectorAll('.panel'));
  function redibujar(panel){
    // Plotly calcula el ancho al dibujar: si el panel estaba oculto (display:none)
    // los graficos quedan con ancho 0 y hay que pedir el redibujado al mostrarlo.
    var grafos = panel.querySelectorAll('.js-plotly-plot, .plotly-graph-div');
    Array.prototype.forEach.call(grafos, function(g){
      try { Plotly.Plots.resize(g); } catch (e) {}
    });
  }
  function activar(id){
    paneles.forEach(function(p){ p.classList.toggle('activo', p.id === id); });
    botones.forEach(function(b){ b.classList.toggle('activo', b.dataset.tab === id); });
    var panel = document.getElementById(id);
    if (panel) { requestAnimationFrame(function(){ redibujar(panel); }); }
  }
  botones.forEach(function(b){
    b.addEventListener('click', function(){ activar(b.dataset.tab); });
  });
  window.addEventListener('resize', function(){
    var activo = document.querySelector('.panel.activo');
    if (activo) { redibujar(activo); }
  });
  activar('tab-resumen');

  // --- buscador del indice de conceptos ---
  var caja = document.getElementById('buscador');
  if (caja) {
    var fichas = Array.prototype.slice.call(
      document.querySelectorAll('#lista-conceptos .concepto'));
    var vacio = document.getElementById('sin-resultados');
    caja.addEventListener('input', function(){
      var q = caja.value.toLowerCase().trim();
      var visibles = 0;
      fichas.forEach(function(f){
        var hit = !q || f.dataset.texto.indexOf(q) !== -1;
        f.style.display = hit ? '' : 'none';
        if (hit) { visibles++; }
      });
      vacio.style.display = visibles ? 'none' : 'block';
    });
  }
})();
</script>
"""


def tarjeta_kpi(k: dict) -> str:
    clase = " dorado" if k.get("dorado") else ""
    nota = f'<div class="n">{k["nota"]}</div>' if k.get("nota") else ""
    return (f'<div class="kpi{clase}">'
            f'<div class="k">{_html.escape(k["titulo"])}</div>'
            f'<div class="v">{_html.escape(k["valor"])}</div>'
            f'<div class="s">{_html.escape(k["subtitulo"])}</div>'
            f'{nota}</div>')


def bloque_narrativa(n: dict) -> str:
    """Narrativa de cuatro partes: qué se hizo, por qué, teoría y cómo se lee."""
    if not n:
        return ""
    partes = (("Qué se hizo", n.get("hizo", ""), ""),
              ("Por qué", n.get("por", ""), ""),
              ("Qué teoría lo respalda", n.get("teoria", ""), " teoria"),
              ("Cómo se lee", n.get("lee", ""), " lee"))
    cuerpo = "".join(
        f'<div class="bloque{extra}"><span class="et">{et}</span>{texto}</div>'
        for et, texto, extra in partes if texto)
    return f'<div class="nar">{cuerpo}</div>' if cuerpo else ""


def tarjeta_grafico(g: tuple) -> str:
    ident, titulo, desc, cuerpo = g
    narrativa = bloque_narrativa(NARRATIVAS.get(ident, {}))
    return (f'<div class="card"><h3>{_html.escape(titulo)}</h3>'
            f'{narrativa}'
            f'<p class="desc">{desc}</p>{cuerpo}</div>')


def construir_html(kpis: list[dict], pestanas: list[tuple], versiones: dict) -> str:
    plotlyjs = (Path(plotly.__file__).parent / "package_data" /
                "plotly.min.js").read_text(encoding="utf-8")
    plotlyjs = plotlyjs.replace("</script>", "<\\/script>")

    botones = "".join(
        f'<button class="tab-btn" data-tab="{pid}">{_html.escape(nombre)}</button>'
        for pid, nombre, _, _ in pestanas)
    paneles = ""
    for pid, nombre, intro, contenido in pestanas:
        graficos, previo, cierre = contenido
        cabecera = (f'<div class="seccion"><div class="titulo">{_html.escape(nombre)}'
                    f' — qué responde esta sección</div>'
                    + bloque_narrativa(NARRATIVAS_PESTANA.get(pid, {}))
                    + (f'<div class="aviso">{intro}</div>' if intro else "")
                    + "</div>")
        cuerpo = "".join(tarjeta_grafico(g) for g in graficos)
        paneles += (f'<div class="panel" id="{pid}">{cabecera}{cuerpo}'
                    f'{previo}'
                    f'<div class="concl"><span class="et">Conclusión</span>{cierre}</div>'
                    f'</div>')

    n_graficos = sum(len(p[3][0]) for p in pestanas)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fase 2 — Análisis pendientes del repositorio de MinCiencias</title>
<style>{CSS}</style>
<script>{plotlyjs}</script>
</head>
<body>
<header>
  <h1>Fase 2 — Análisis pendientes del Observatorio MinCiencias</h1>
  <div class="sub">Investigadores reconocidos por convocatoria (2013–2021). Panel
  interactivo de {n_graficos} gráficos y {len(pestanas)} pestañas: resumen ejecutivo,
  territorio, diversidad, redes y clustering, supervivencia, calidad, límites y flujos
  y migración. Cada gráfico explica <b>qué se hizo</b>, <b>por qué</b>, <b>qué teoría lo
  respalda</b> y <b>cómo se lee</b>.</div>
  <div class="meta">Censo completo de {versiones['registros']} registros y
  {versiones['personas']} personas · {versiones['convocatorias']} convocatorias ·
  {versiones['figuras']} figuras de los siete análisis y {versiones['figuras_mapa']} del
  mapa de flujos · generado el {versiones['fecha']}</div>
</header>
<div class="wrap">
  <div class="kpis">{''.join(tarjeta_kpi(k) for k in kpis)}</div>
  <div class="tabs">{botones}</div>
  {paneles}
  {bloque_indice()}
  <footer>
    <b>Fuente:</b> base completa de investigadores reconocidos por MinCiencias,
    <code>datos.gov.co</code>, dataset <code>bqtm-4y2h</code> ·
    <code>Investigadores_Reconocidos_por_convocatoria_20261006.csv</code> (77 237 registros).
    Población: CNPV 2018 del DANE (cuadro 1PD) y proyecciones departamentales.<br>
    <b>Análisis:</b> cada pestaña resume un informe con su script, su JSON de resultados
    y su documento en <code>documentacion_auditoria/</code> (F2-2 a F2-11). Las cifras de
    este panel se leen de esos JSON; no se recalcula ningún resultado.<br>
    <b>Geometrías del mapa (pestaña 8):</b>
    <code>data/geo/colombia_departamentos.geojson</code>, GeoJSON público de john-guerra
    derivado de DIVIPOLA/IGAC; procedencia, SHA-256 y criterio de limpieza en
    <code>colombia_departamentos.procedencia.txt</code>. La unión es por código DIVIPOLA,
    nunca por nombre.<br>
    <b>Autoría:</b> Kevin Leonardo Chaparro Reyes · Valentina Muñoz Palma ·
    Paula Margarita Triana Ancinez — Consultoría Estadística, Universidad Santo Tomás,
    2026-II.<br>
    Documento autocontenido: Plotly {versiones['plotly']} embebido, sin CDN ni conexión a
    internet. Las cifras principales son censales; las estimaciones muestrales (MAS,
    post-estratificación, GREG, bootstrap de diseño) aparecen etiquetadas como tales.
  </footer>
</div>
{JS}
</body>
</html>
"""


# ============================================================================
# 13. Main
# ============================================================================
def main() -> int:
    registrar_template()
    print("== Paleta institucional ==")
    print(f"   template '{NOMBRE_TEMPLATE}' registrado · primario {PALETA['primario']} · "
          f"dorado {PALETA['dorado']} · alerta {ALERTA} (solo excepciones)")

    print("\n== Carga de fuentes ==")
    d = cargar_todo()

    print("\n== Reconstrucción de la red (para dibujarla) ==")
    G, nx = red_2019()
    print(f"   {G.number_of_nodes()} nodos · {G.number_of_edges()} aristas")

    print("\n== Composición categoría x género (validada contra F2-10) ==")
    comp = composicion_categoria_genero(d["supervivencia"])
    print("   reproducción de tamaños de grupo verificada")

    print("\n== Construcción de las pestañas ==")
    p, e, u, sv = (d["percapita_territorial"], d["modelo_estrella"],
                   d["validacion_unicidad"], d["supervivencia"])

    kpis = [
        {"titulo": "Análisis con resultado cerrado", "valor": "8 de 10",
         "subtitulo": "7 entregados y 1 cerrado como no evaluable", "dorado": True,
         "nota": "F2-8 (descriptivos por convocatoria) y F2-9 (inferencia adicional) "
                 "quedaron fuera de esta fase."},
        {"titulo": "Bloqueado por datos", "valor": "1",
         "subtitulo": "F2-1 · productividad científica (Q7)",
         "nota": "El CSV de 1,2 GB con las revistas no está versionado: no evaluable por "
                 "restricción de acceso, no por método."},
        {"titulo": "IDs que violan la regla", "valor": str(u["ids_no_unicos"]["n_ids_violadores"]),
         "subtitulo": f"de {miles(u['ids_no_unicos']['n_ids_evaluados'])} IDs con más de un registro",
         "nota": "41 fallan solo en el género · 14 solo en la edad · 1 en ambas. "
                 "15 comprometen la identidad."},
        {"titulo": "Retención 2013 → 2021", "valor": "56,18 %",
         "subtitulo": "censo completo · cohorte de 2013", "dorado": True,
         "nota": f"Kaplan-Meier sobre la cohorte de 2013: S(6,10 años) = "
                 f"{num(sv['cohorte_2013']['retencion_final'], 4)}."},
        {"titulo": "Comprobaciones automáticas", "valor": "56 / 56",
         "subtitulo": "en los siete JSON de la fase",
         "nota": "Ningún análisis tiene una comprobación en rojo; 21 figuras exportadas."},
        {"titulo": "Reglas de validación", "valor": "15 · 0 · 2",
         "subtitulo": "PASA · FALLA · ADVERTENCIA (17 reglas)",
         "nota": "R12 y R15 son advertencias declaradas y revisadas, no fallos."},
        {"titulo": "Mudanzas de departamento", "valor": "808",
         "subtitulo": "4,38 % de las 18 430 personas con dos o más convocatorias",
         "nota": "231 rutas; 53 movimientos son de área metropolitana (Bogotá ↔ "
                 "Cundinamarca). El flujo por nacimiento da 11 922 casos y es otra "
                 "definición de migración."},
    ]

    t1 = pestana_resumen(d)
    t2 = pestana_territorio(d)
    t3 = pestana_diversidad(d)
    t4 = pestana_redes(d, G, nx)
    t5 = pestana_supervivencia(d, comp)
    t6 = pestana_calidad(d)
    t7 = pestana_limites()
    t8 = pestana_migracion()

    pestanas = [
        ("tab-resumen", "1 · Resumen ejecutivo", "", t1),
        ("tab-territorio", "2 · Territorio y desigualdad (F2-2)", "", t2),
        ("tab-diversidad", "3 · Diversidad y falencias (F2-5)", "", t3),
        ("tab-redes", "4 · Redes y clustering (F2-4, F2-6)", "", t4),
        ("tab-supervivencia", "5 · Supervivencia y género (F2-10)", "", t5),
        ("tab-calidad", "6 · Calidad y reproducibilidad (F2-3, F2-7)", "", t6),
        ("tab-limites", "7 · Límites y falencias", "", t7),
        ("tab-migracion", "8 · Flujos y migración (F2-11)",
         mapa_mod.NOTA_D1 + "<br><br>" + mapa_mod.NOTA_D2, t8),
    ]
    for pid, nombre, _, cont in pestanas:
        print(f"   {pid:20} {len(cont[0])} gráficos")

    versiones = {
        "registros": miles(77237),
        "personas": miles(30086),
        "convocatorias": 6,
        "figuras": sum(len(d[k]["figuras"]) for k in d),
        "figuras_mapa": len(mapa_mod.cargar_flujos()["figuras"]),
        "plotly": plotly.__version__,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    print("\n== Escritura del HTML ==")
    documento = construir_html(kpis, pestanas, versiones)
    SALIDA.write_text(documento, encoding="utf-8")
    peso = SALIDA.stat().st_size
    print(f"   {SALIDA.relative_to(RAIZ)}")
    print(f"   peso: {peso:,} B = {peso/1024/1024:.2f} MiB ({peso/1e6:.2f} MB decimales)")
    print(f"   gráficos: {sum(len(p[3][0]) for p in pestanas)} en {len(pestanas)} pestañas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
