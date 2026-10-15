# -*- coding: utf-8 -*-
"""
generar_dashboard_eda.py
========================

Construye `data/memoria/dashboard_eda.html`: el analisis exploratorio completo
como panel interactivo de 4 pestanas, **autocontenido** (sin red, sin CDN) y con
el mismo lenguaje visual que `herramienta_trayectorias.html`.

Fuentes (todas versionadas):
  - data/memoria/eda_resultados.json
  - data/memoria/diagnosticos_greg.json
  - data/memoria/estimadores_resultados.json
  - datos_originales/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv

POR QUE HAY QUE RECALCULAR ALGO
-------------------------------
Los JSON guardan **estadisticos resumidos**, no los vectores por observacion.
Cuatro graficos necesitan el vector:

  1. histograma y boxplot de la edad        -> vector de edades del censo
  2. Q-Q plot de la edad                    -> idem
  3. residuos vs valores ajustados          -> vector `Xs @ beta` del modelo
  4. distribucion de los g-weights          -> vector de g-weights

Los tres ultimos se regeneran con las **mismas funciones del proyecto**
(importadas de `estimadores_longitudinal` y `diagnosticos_greg`, no reescritas) y
despues se **validan** contra los estadisticos ya guardados en los JSON. Si la
validacion no cuadra, el script **falla**: es preferible no generar el panel a
generarlo con cifras que no reproducen las ya publicadas.

REGLA DE LOS KPI
----------------
El valor principal de cada tarjeta es siempre **censal**. Las estimaciones
muestrales (MAS, post-estratificacion, GREG) van como nota metodologica
secundaria, nunca como cifra principal.

Este script NO modifica ningun analisis previo: solo lee los JSON y el CSV, y
escribe el HTML.

Uso:  python generar_dashboard_eda.py
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
from scipy import stats

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
MEM = DOC / "data" / "memoria"
SRC = Path(__file__).resolve().parent
CSV = RAIZ / "datos_originales" / "datos_fuente" / \
    "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
SALIDA = MEM / "dashboard_eda.html"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------- paleta y tipo
# Los colores son los mismos de herramienta_trayectorias.html, para que los dos
# entregables se lean como parte del mismo sistema.
AZUL, AZUL_OSC, DORADO = "#1E3780", "#0F1F4D", "#B7871E"
VERDE, ROJO, AMBAR = "#15803D", "#B91C1C", "#B45309"
GRIS, GRIS_CLARO = "#64748B", "#94A3B8"
MORADO, TEAL = "#7C3AED", "#0E7490"
FONDO, BLANCO, BORDE = "#F3F6FC", "#FFFFFF", "#D6DEEE"

# Montserrat y Fira Code no estan instaladas en este equipo; se declaran primero
# y caen a la pila que usa la herramienta de trayectorias, de modo que el
# resultado visual coincide con ella cuando no estan disponibles.
FUENTE_TXT = ('Montserrat, "Segoe UI", Roboto, system-ui, -apple-system, '
              'Arial, sans-serif')
FUENTE_MONO = 'Fira Code, Consolas, "Courier New", monospace'

COLOR_CATEGORIA = {
    "Investigador Junior": TEAL,
    "Investigador Asociado": AZUL,
    "Investigador Sénior": DORADO,
    "Investigador Emérito": MORADO,
}

CONFIG_PLOTLY = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "filename": "eda_minciencias",
                             "scale": 2},
}


# ============================================================================
# 1. Datos de entrada
# ============================================================================
def cargar_json() -> tuple[dict, dict, dict]:
    eda = json.loads((MEM / "eda_resultados.json").read_text(encoding="utf-8"))
    est = json.loads((MEM / "estimadores_resultados.json").read_text(encoding="utf-8"))
    dg = json.loads((MEM / "diagnosticos_greg.json").read_text(encoding="utf-8"))
    return eda, est, dg


def cargar_poblacion() -> tuple[pd.DataFrame, pd.Series]:
    """
    Devuelve (personas, edad) del CENSO, con la MISMA regla que el resto del
    analisis: una fila por persona (ultima convocatoria observada) y la edad
    leida como texto con coma decimal.

    Se importan las funciones del proyecto en lugar de reescribirlas, para no
    duplicar ni la matriz auxiliar ni el calculo de los g-weights.

    OJO: los modulos del pipeline hacen `sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, ...)` al importarse. Como todos envuelven el MISMO buffer,
    al quedarse sin referencias el recolector lo cierra y la salida original
    muere ("I/O operation on closed file"). Para que ese efecto caiga en un flujo
    desechable, la importacion se hace con `sys.stdout` apuntando a devnull.
    """
    import os

    real = sys.stdout
    sys.path.insert(0, str(SRC))
    sys.stdout = io.TextIOWrapper(open(os.devnull, "wb"), encoding="utf-8")
    try:
        from eda_longitudinal import cargar as cargar_eda
        from estimadores_longitudinal import AUX_EDAD, IDS, matriz_aux
        from diagnosticos_greg import g_weights
    finally:
        sys.stdout = real

    df = cargar_eda()
    ult = df.sort_values("conv_i").groupby("ID_PERSONA_PR", observed=True).last()
    edad = pd.to_numeric(ult["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                         errors="coerce")
    return ult, edad, AUX_EDAD, IDS, matriz_aux, g_weights


def regenerar_vectores(eda: dict, dg: dict) -> dict:
    """
    Reconstruye los cuatro vectores que faltan y los VALIDA contra lo guardado.
    Si alguno no reproduce las cifras publicadas, se aborta.
    """
    ult, edad, AUX_EDAD, IDS, matriz_aux, g_weights = cargar_poblacion()
    print(f"   poblacion: {len(ult):,} personas | edad no nula: {edad.notna().sum():,}")

    # ---- 1-2. edades del censo -------------------------------------------
    edades = edad.dropna().to_numpy()
    e = eda["edad"]
    comprobaciones = [
        ("n de edades", len(edades), e["n"]),
        ("media de edad", round(float(edades.mean()), 6), round(e["media"], 6)),
        ("desviacion de edad", round(float(edades.std(ddof=1)), 6), round(e["desv"], 6)),
        ("maximo de edad", round(float(edades.max()), 6), round(e["maximo"], 6)),
        ("minimo de edad", round(float(edades.min()), 6), round(e["minimo"], 6)),
        ("casos > 100 anos", int((edades > 100).sum()), e["mayores_100"]),
    ]
    fallos = [f"{n}: reconstruido {v} != guardado {g}"
              for n, v, g in comprobaciones if v != g]
    if fallos:
        raise SystemExit("El vector de edades NO reproduce el JSON:\n  " +
                         "\n  ".join(fallos))
    print(f"   [ok] vector de edades validado contra eda_resultados.json "
          f"({len(comprobaciones)} comprobaciones)")

    # ---- 3-4. modelo de edad: ajustados y g-weights ----------------------
    ids = set(pd.read_csv(IDS, dtype=str, keep_default_na=False)["ID_PERSONA_PR"])
    pop = ult.loc[edad.notna()]
    y_U = edad[edad.notna()].to_numpy()
    samp = pop.loc[pop.index.isin(ids)]
    y_s = pd.to_numeric(samp["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                        errors="coerce").to_numpy()
    X_U, X_s = matriz_aux(pop, samp, AUX_EDAD)
    Xs = np.hstack([np.ones((len(X_s), 1)), X_s])
    beta, *_ = np.linalg.lstsq(Xs, y_s, rcond=None)
    ajustados = Xs @ beta
    resid = y_s - ajustados
    g, *_ = g_weights(X_s, X_U, len(pop))

    inf = dg["modelo_edad"]["influencia"]
    gw = dg["modelo_edad"]["g_weights"]
    comprobaciones = [
        ("n del modelo", len(y_s), dg["modelo_edad"]["n_modelo"]),
        ("parametros", int(Xs.shape[1]), dg["modelo_edad"]["n_parametros"]),
        ("s2", round(float((resid ** 2).sum() / (len(y_s) - Xs.shape[1])), 6),
         round(inf["s2"], 6)),
        ("min residuo", round(float(resid.min()), 6),
         round(float(np.min(inf["resid"])), 6)),
        ("max residuo", round(float(resid.max()), 6),
         round(float(np.max(inf["resid"])), 6)),
        ("n g-weights", len(g), dg["modelo_edad"]["n_modelo"]),
        ("min g-weight", round(float(g.min()), 9), round(gw["min"], 9)),
        ("max g-weight", round(float(g.max()), 9), round(gw["max"], 9)),
        ("mediana g-weight", round(float(np.quantile(g, 0.5)), 9),
         round(gw["cuantiles"]["50"], 9)),
        ("g > 5", int((g > 5).sum()), gw["n_sobre_5"]),
        ("g > 10", int((g > 10).sum()), gw["n_sobre_10"]),
    ]
    fallos = [f"{n}: reconstruido {v} != guardado {gr}"
              for n, v, gr in comprobaciones if v != gr]
    if fallos:
        raise SystemExit("Los vectores del modelo NO reproducen el JSON:\n  " +
                         "\n  ".join(fallos))
    print(f"   [ok] ajustados, residuos y g-weights validados contra "
          f"diagnosticos_greg.json ({len(comprobaciones)} comprobaciones)")

    # ---- cruce categoria x gran area (para el treemap) -------------------
    cruce = (ult.groupby(["NME_CLASIFICACION_PR", "NME_GRAN_AREA_PR"],
                         observed=True).size().reset_index(name="n"))
    cruce = cruce.sort_values("n", ascending=False)

    return {"edades": edades, "y_U": y_U, "samp": samp, "y_s": y_s,
            "ajustados": ajustados, "resid": resid, "g": g, "cruce": cruce,
            "n_censo": len(pop), "n_muestra": len(y_s)}


# ============================================================================
# 2. Utilidades de graficado
# ============================================================================
def estilo(fig: go.Figure, alto: int = 430, leyenda: bool = True) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        font=dict(family=FUENTE_TXT, size=13, color="#0F172A"),
        height=alto,
        margin=dict(l=72, r=28, t=56, b=64),
        paper_bgcolor=BLANCO,
        plot_bgcolor=BLANCO,
        hoverlabel=dict(font=dict(family=FUENTE_TXT, size=13), bgcolor=BLANCO,
                        bordercolor=BORDE),
        colorway=[AZUL, DORADO, TEAL, MORADO, VERDE, AMBAR, ROJO, GRIS, GRIS_CLARO],
        separators=",.",
    )
    fig.update_xaxes(gridcolor="#E9EEF7", linecolor=BORDE, zeroline=False,
                     tickfont=dict(size=12))
    fig.update_yaxes(gridcolor="#E9EEF7", linecolor=BORDE, zeroline=False,
                     tickfont=dict(size=12))
    if leyenda:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.22,
                                      xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                                      font=dict(size=12)))
    return fig


def div(fig: go.Figure, ident: str) -> str:
    """
    HTML del grafico SIN volver a embeber Plotly (se embebe una sola vez).

    Nota de version: `plotly.offline.plot(output_type="div")` ya NO acepta
    `div_id` en Plotly 7 (se elimino junto con `post_script`). El equivalente
    moderno es `plotly.io.to_html(..., full_html=False)`, que produce el mismo
    div y sigue admitiendo `div_id`.
    """
    return pio.to_html(fig, include_plotlyjs=False, full_html=False,
                       div_id=ident, config=CONFIG_PLOTLY)


def miles(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def num(x: float, dec: int = 2) -> str:
    """
    Numero con coma decimal, como el resto del panel.

    Hace falta porque `separators=",."` de Plotly solo afecta a los ejes y a los
    tooltips: los titulos y anotaciones escritos a mano en Python se quedaban con
    punto decimal, y el panel mezclaba «7,08 %» con «rango [0.5839, 1.4708]».
    """
    return f"{x:,.{dec}f}".replace(",", "\u202f").replace(".", ",")


def pval(p: float | None, dec: int = 3) -> str:
    """p-valor legible: los muy pequenos se resumen como «p < 0,001»."""
    if p is None:
        return "p no calculado"
    if p < 0.001:
        return "p &lt; 0,001"
    return "p = " + num(p, dec)


def barras_categoricas(dist: dict, titulo: str, color=AZUL, top: int | None = None,
                       horizontal: bool = False, alto: int = 430) -> go.Figure:
    items = sorted(dist.items(), key=lambda kv: kv[1]["n"], reverse=True)
    if top:
        items = items[:top]
    etiquetas = [k for k, _ in items]
    valores = [v["n"] for _, v in items]
    pcts = [v["pct"] for _, v in items]
    texto = [f"{miles(v)} ({p:.1f} %)".replace(".", ",") for v, p in zip(valores, pcts)]

    if horizontal:
        etiquetas = etiquetas[::-1]
        valores, pcts, texto = valores[::-1], pcts[::-1], texto[::-1]
        fig = go.Figure(go.Bar(
            x=valores, y=etiquetas, orientation="h", marker_color=color,
            text=texto, textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:,} personas<br>%{text}<extra></extra>",
        ))
        fig.update_xaxes(title="Personas", range=[0, max(valores) * 1.22])
    else:
        fig = go.Figure(go.Bar(
            x=etiquetas, y=valores, marker_color=color, text=texto,
            textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>%{y:,} personas<br>%{text}<extra></extra>",
        ))
        fig.update_yaxes(title="Personas", range=[0, max(valores) * 1.18])
        fig.update_xaxes(tickangle=-18)
    fig.update_layout(title=dict(text=titulo, x=0.01, xanchor="left", font=dict(size=15)))
    return estilo(fig, alto=alto, leyenda=False)


# ============================================================================
# 3. Las cuatro pestanas
# ============================================================================
def pestana_univariado(eda: dict, vec: dict) -> list[tuple[str, str, str, str]]:
    u = eda["univariado_persona"]
    graficos = []

    graficos.append(("u1", "Distribución por categoría",
                     f"Categoría del investigador en su última convocatoria observada "
                     f"({eda['universo']['convocatorias']} convocatorias, {miles(eda['universo']['personas'])} personas).",
                     div(barras_categoricas(u["NME_CLASIFICACION_PR"]["distribucion"],
                                            "Personas por categoría", color=AZUL), "u1")))

    graficos.append(("u2", "Distribución por género",
                     "Se usa la columna colapsada: las etiquetas «Intersexual» y "
                     "«No disponible» agrupan 9 personas en el censo y no permiten calibrar.",
                     div(barras_categoricas(u["NME_GENERO_COL"]["distribucion"],
                                            "Personas por género", color=DORADO), "u2")))

    graficos.append(("u3", "Distribución por gran área de conocimiento",
                     "Siete gran áreas OCDE; «No registra» es un valor propio del dataset.",
                     div(barras_categoricas(u["NME_GRAN_AREA_PR"]["distribucion"],
                                            "Personas por gran área", color=TEAL,
                                            alto=470), "u3")))

    graficos.append(("u4", "Distribución por departamento (top 10)",
                     f"De {u['NME_DEPARTAMENTO_RES_PR']['n_categorias']} departamentos "
                     f"de residencia se muestran los 10 mayores por número de personas.",
                     div(barras_categoricas(u["NME_DEPARTAMENTO_RES_PR"]["distribucion"],
                                            "Personas por departamento de residencia",
                                            color=MORADO, top=10, horizontal=True,
                                            alto=470), "u4")))

    graficos.append(("u5", "Distribución por nivel de formación",
                     "Nivel de formación declarado en la última convocatoria observada.",
                     div(barras_categoricas(u["NME_NIV_FORM_PR"]["distribucion"],
                                            "Personas por nivel de formación",
                                            color=AMBAR, alto=470), "u5")))

    # Edad: histograma + caja, con el vector censal completo (30 085 edades).
    edades = vec["edades"]
    e = eda["edad"]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28],
                        vertical_spacing=0.06,
                        subplot_titles=("Histograma (60 intervalos)", "Diagrama de caja"))
    fig.add_trace(go.Histogram(x=edades, nbinsx=60, marker_color=AZUL,
                               name="Personas",
                               hovertemplate="Edad %{x}<br>%{y} personas<extra></extra>"),
                  row=1, col=1)
    fig.add_trace(go.Box(x=edades, marker_color=DORADO, name="Caja",
                         boxpoints="outliers", marker=dict(size=3, opacity=0.5),
                         hovertemplate="Edad %{x}<extra></extra>"),
                  row=2, col=1)
    fig.update_xaxes(range=[0, 105], row=1, col=1)
    fig.update_xaxes(title="Edad (años)", range=[0, 105], row=2, col=1)
    fig.update_yaxes(title="Personas", row=1, col=1)
    fig.update_layout(title=dict(
        text=(f"Edad — censo completo: media {num(e['media'])} · mediana "
              f"{num(e['cuantiles']['0.5'])} · desviación {num(e['desv'])}"),
        x=0.01, xanchor="left", font=dict(size=15)))
    fig.add_annotation(x=100, y=0.98, xref="x", yref="paper", showarrow=False,
                       text=f"{e['mayores_100']} casos con edad &gt; 100 años, "
                            f"máximo {num(e['maximo'])} (fuera del rango mostrado)",
                       font=dict(size=11, color=ROJO), xanchor="right")
    graficos.append(("u6", "Distribución de la edad",
                     f"Histograma y caja sobre las {miles(e['n'])} personas con edad "
                     f"registrada. Los {e['atipicos_bigote']} atípicos de bigote y los "
                     f"{e['mayores_100']} casos con edad mayor que 100 explican la "
                     f"asimetría positiva: la media ({num(e['media'])}) supera a la "
                     f"mediana ({num(e['cuantiles']['0.5'])}).",
                     div(estilo(fig, alto=560, leyenda=False), "u6")))
    return graficos


def pestana_bivariado(eda: dict, est: dict) -> list[tuple[str, str, str, str]]:
    biv = eda["bivariado"]["pares"]
    pares = list(biv)
    graficos = []

    def serie(estrato: str, categoria: str) -> tuple[list, list]:
        """Tasa censal de esa categoría en cada par (None si no existe)."""
        xs, ys = [], []
        for p in pares:
            d = biv[p].get(estrato, {}).get(categoria)
            xs.append(p)
            ys.append(d["tasa"] * 100 if d else None)
        return xs, ys

    # 1. Retención por categoría (barras agrupadas)
    cats = ["Investigador Junior", "Investigador Asociado", "Investigador Sénior",
            "Investigador Emérito"]
    fig = go.Figure()
    for c in cats:
        if not any(c in biv[p].get("NME_CLASIFICACION_PR", {}) for p in pares):
            continue
        xs, ys = serie("NME_CLASIFICACION_PR", c)
        ns = [biv[p]["NME_CLASIFICACION_PR"][c]["n"] if c in biv[p].get("NME_CLASIFICACION_PR", {}) else None for p in pares]
        fig.add_trace(go.Bar(
            x=xs, y=ys, name=c.replace("Investigador ", ""),
            marker_color=COLOR_CATEGORIA[c],
            customdata=ns,
            hovertemplate=("<b>%{fullData.name}</b><br>%{x}<br>"
                           "Retención %{y:.1f} %<br>Base %{customdata:,} personas"
                           "<extra></extra>")))
    fig.update_yaxes(title="Tasa de retención (%)", range=[0, 105])
    fig.update_layout(title=dict(text="Retención censal por categoría y par de convocatorias",
                                 x=0.01, xanchor="left", font=dict(size=15)),
                      barmode="group")
    graficos.append(("r1", "Retención por categoría",
                     "Sénior y Asociado retienen muy por encima de Junior en todos los "
                     "pares: es el estrato que más explica la varianza. La categoría "
                     "Emérito solo aparece en los pares recientes.",
                     div(estilo(fig, alto=470), "r1")))

    # 2. Retención por gran área (mapa de calor)
    areas = sorted({a for p in pares for a in biv[p].get("NME_GRAN_AREA_PR", {})})
    z = [[biv[p].get("NME_GRAN_AREA_PR", {}).get(a, {}).get("tasa", None)
          for p in pares] for a in areas]
    z = [[v * 100 if v is not None else None for v in fila] for fila in z]
    base = [[biv[p].get("NME_GRAN_AREA_PR", {}).get(a, {}).get("n", None)
             for p in pares] for a in areas]
    fig = go.Figure(go.Heatmap(
        z=z, x=pares, y=areas, colorscale=[[0, "#FDEEEC"], [0.5, "#FFF1D6"], [1, "#DCE9F8"]],
        zmin=30, zmax=90, customdata=base,
        text=[[f"{v:.0f} %" if v is not None else "—" for v in fila] for fila in z],
        texttemplate="%{text}", textfont=dict(size=11),
        hovertemplate=("<b>%{y}</b><br>%{x}<br>Retención %{z:.1f} %<br>"
                       "Base %{customdata:,} personas<extra></extra>"),
        colorbar=dict(title="Retención<br>(%)")))
    fig.update_layout(title=dict(text="Retención censal por gran área y par",
                                 x=0.01, xanchor="left", font=dict(size=15)))
    graficos.append(("r2", "Retención por gran área",
                     "Humanidades y Ciencias Sociales retienen menos que Ciencias "
                     "Médicas e Ingeniería en todos los pares.",
                     div(estilo(fig, alto=470, leyenda=False), "r2")))

    # 3. Retención por género
    fig = go.Figure()
    for gen, color in (("Masculino", AZUL), ("Femenino", DORADO),
                       ("Otro / No especificado", GRIS)):
        xs, ys = serie("NME_GENERO_COL", gen)
        if all(v is None for v in ys):
            continue
        fig.add_trace(go.Scatter(x=xs, y=ys, name=gen, mode="lines+markers",
                                 line=dict(color=color, width=3), marker=dict(size=9),
                                 connectgaps=False,
                                 hovertemplate=("<b>%{fullData.name}</b><br>%{x}<br>"
                                                "Retención %{y:.1f} %<extra></extra>")))
    fig.update_yaxes(title="Tasa de retención (%)", range=[0, 105])
    fig.update_layout(title=dict(text="Retención censal por género", x=0.01,
                                 xanchor="left", font=dict(size=15)))
    graficos.append(("r3", "Retención por género",
                     "La diferencia por género es de menos de un punto porcentual: "
                     "coherente con que el género explique solo el 0,11 % de la varianza.",
                     div(estilo(fig, alto=450), "r3")))

    # 4. Retención por departamento (top 5 por base del último par)
    ultimo = pares[-1]
    deptos = sorted(biv[ultimo]["NME_DEPARTAMENTO_RES_PR"].items(),
                    key=lambda kv: kv[1]["n"], reverse=True)[:5]
    nombres = [d for d, _ in deptos]
    z = [[biv[p].get("NME_DEPARTAMENTO_RES_PR", {}).get(d, {}).get("tasa", None)
          for p in pares] for d in nombres]
    z = [[v * 100 if v is not None else None for v in fila] for fila in z]
    base = [[biv[p].get("NME_DEPARTAMENTO_RES_PR", {}).get(d, {}).get("n", None)
             for p in pares] for d in nombres]
    fig = go.Figure(go.Heatmap(
        z=z, x=pares, y=nombres,
        colorscale=[[0, "#FDEEEC"], [0.5, "#FFF1D6"], [1, "#DCE9F8"]],
        zmin=20, zmax=95, customdata=base,
        text=[[f"{v:.0f} %" if v is not None else "—" for v in fila] for fila in z],
        texttemplate="%{text}", textfont=dict(size=11),
        hovertemplate=("<b>%{y}</b><br>%{x}<br>Retención %{z:.1f} %<br>"
                       "Base %{customdata:,} personas<extra></extra>"),
        colorbar=dict(title="Retención<br>(%)")))
    fig.update_layout(title=dict(
        text=f"Retención censal — 5 departamentos con más personas en {ultimo}",
        x=0.01, xanchor="left", font=dict(size=15)))
    graficos.append(("r4", "Retención por departamento (top 5)",
                     f"Los cinco departamentos con mayor base en {ultimo}. "
                     "Los valores bajos de los pares iniciales corresponden a bases "
                     "pequeñas: leerlos junto al tamaño de muestra del tooltip.",
                     div(estilo(fig, alto=470, leyenda=False), "r4")))

    # 5. Serie temporal: censo (principal) + estimaciones (secundarias)
    r = est["retencion"]
    cortos = [k for k in ("2013→2014", "2014→2015", "2015→2017", "2017→2019",
                          "2019→2021") if k in r]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cortos, y=[r[k]["censo"] * 100 for k in cortos], name="Censo (valor principal)",
        mode="lines+markers", line=dict(color=AZUL, width=4), marker=dict(size=11),
        hovertemplate="<b>Censo</b><br>%{x}<br>Retención %{y:.1f} %<extra></extra>"))
    for nombre, clave, color, guion in (
            ("Estimación MAS", "mas", DORADO, "dash"),
            ("Post-estratificada", "post_estratificado", TEAL, "dot"),
            ("GREG", "greg_lineal", VERDE, "dashdot")):
        fig.add_trace(go.Scatter(
            x=cortos, y=[r[k][clave]["estimador"] * 100 for k in cortos], name=nombre,
            mode="lines+markers", line=dict(color=color, width=2, dash=guion),
            marker=dict(size=7),
            hovertemplate=f"<b>{nombre}</b><br>%{{x}}<br>%{{y:.1f}} %<extra></extra>"))
    j = r.get("2013→2021")
    if j:
        fig.add_annotation(x=cortos[0], y=j["censo"] * 100, xref="x", yref="y",
                           text=f"2013→2021 completo: {num(j['censo']*100, 1)} % (censo)",
                           showarrow=True, arrowhead=2, ax=60, ay=-38,
                           font=dict(size=11, color=AZUL_OSC), bgcolor="#EAF2FD",
                           bordercolor="#B9D0EE", borderpad=4)
    fig.update_yaxes(title="Tasa de retención (%)")
    fig.update_layout(title=dict(text="Retención por par de convocatorias",
                                 x=0.01, xanchor="left", font=dict(size=15)))
    graficos.append(("r5", "Retención por par de convocatorias",
                     "Línea gruesa: valores censales (la cifra principal). Líneas "
                     "punteadas: las tres estimaciones sobre la muestra MAS "
                     "(n = 2 224), que reproducen el censo con diferencias de décimas.",
                     div(estilo(fig, alto=480), "r5")))
    return graficos


def pestana_varianza(eda: dict, vec: dict) -> list[tuple[str, str, str, str]]:
    cand = eda["estratos_candidatos"]
    dec = eda["bivariado"]["decomposicion_varianza"]

    simples = ["NME_CLASIFICACION_PR", "NME_GRAN_AREA_PR", "NME_DEPARTAMENTO_RES_PR",
               "NME_NIV_FORM_PR", "NME_GENERO_COL"]
    nombre = {"NME_CLASIFICACION_PR": "Categoría", "NME_GRAN_AREA_PR": "Gran área",
              "NME_DEPARTAMENTO_RES_PR": "Departamento", "NME_NIV_FORM_PR": "Nivel de formación",
              "NME_GENERO_COL": "Género"}
    items = sorted(((nombre.get(k, k), v["pct_varianza_explicada"], v["n_estratos"],
                     v.get("p_valor"))
                    for k, v in cand.items()), key=lambda t: t[1])
    etiquetas = [f"{t[0]}<br><span style='font-size:10px;color:{GRIS}'>"
                 f"{t[2]} estratos</span>" for t in items]
    valores = [t[1] for t in items]
    colores = [AZUL if t[0] in nombre.values() else GRIS_CLARO for t in items]

    fig = make_subplots(rows=1, cols=2, column_widths=[0.56, 0.44],
                        subplot_titles=("Varianza explicada por cada estrato",
                                        "Reparto entre / dentro — Categoría"))
    fig.add_trace(go.Bar(
        x=valores, y=etiquetas, orientation="h", marker_color=colores,
        text=[f"{v:.2f} %".replace(".", ",") for v in valores],
        textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Explica %{x:.2f} % de la varianza<extra></extra>",
        showlegend=False), row=1, col=1)
    fig.update_xaxes(title="% de la varianza de la retención", range=[0, max(valores) * 1.30],
                     row=1, col=1)

    dcat = dec["NME_CLASIFICACION_PR"]
    # Dos trazas + barmode="stack" para que la barra muestre el reparto
    # entre/dentro: una sola traza con dos valores dibujaria dos barras aparte.
    fig.add_trace(go.Bar(
        x=[dcat["pct_entre"]], y=["Categoría"], orientation="h",
        marker_color=AZUL, showlegend=False,
        text=[f"entre estratos {dcat['pct_entre']:.2f} %".replace(".", ",")],
        textposition="outside", cliponaxis=False,
        hovertemplate="Entre estratos: %{x:.2f} %<extra></extra>"), row=1, col=2)
    fig.add_trace(go.Bar(
        x=[dcat["pct_dentro"]], y=["Categoría"], orientation="h",
        marker_color="#D6DEEE", showlegend=False,
        text=[f"dentro de los estratos {dcat['pct_dentro']:.2f} %".replace(".", ",")],
        textposition="inside", insidetextanchor="middle",
        hovertemplate="Dentro de los estratos: %{x:.2f} %<extra></extra>"),
        row=1, col=2)
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title="% de la varianza total", range=[0, 100], row=1, col=2)
    fig.update_yaxes(showticklabels=False, row=1, col=2)
    fig.update_layout(title=dict(
        text=(f"Estrato de categoría: χ² = {num(dcat['chi2'], 1)} (gl = {dcat['gl']}, "
              f"{pval(dcat['p_valor'], 1)}) · referencia censal {dcat['referencia']}"),
        x=0.01, xanchor="left", font=dict(size=15)))
    graficos = [("v1", "Varianza entre grupos por estrato",
                 "La categoría explica el 7,08 % de la varianza de la retención y el "
                 "género el 0,11 %. Este es el gráfico que justifica el diseño "
                 "estratificado: solo la categoría aporta una reducción relevante "
                 "(el 92,92 % restante es variación dentro de los estratos).",
                 div(estilo(fig, alto=520, leyenda=False), "v1"))]

    # Treemap: composición categoría -> gran área
    cruce = vec["cruce"]
    etiquetas, padres, valores, colores, textos = ["Población"], [""], [int(cruce["n"].sum())], [AZUL_OSC], [""]
    for cat, sub in cruce.groupby("NME_CLASIFICACION_PR", observed=True):
        etiquetas.append(cat)
        padres.append("Población")
        valores.append(int(sub["n"].sum()))
        colores.append(COLOR_CATEGORIA.get(cat, GRIS))
        textos.append(f"{miles(int(sub['n'].sum()))} personas")
        for _, fila in sub.iterrows():
            etiquetas.append(f"{fila['NME_GRAN_AREA_PR']}")
            padres.append(cat)
            valores.append(int(fila["n"]))
            colores.append(COLOR_CATEGORIA.get(cat, GRIS))
            textos.append(f"{miles(int(fila['n']))} personas")
    fig = go.Figure(go.Treemap(
        labels=etiquetas, parents=padres, values=valores, branchvalues="total",
        marker=dict(colors=colores, line=dict(width=1.5, color=BLANCO)),
        text=textos, textinfo="label+text",
        hovertemplate="<b>%{label}</b><br>%{value:,} personas<br>"
                      "%{percentRoot:.1%} de la población<extra></extra>",
        tiling=dict(pad=2), sort=True, root_color="#EAF2FD"))
    fig.update_layout(title=dict(
        text="Composición de la población: categoría y gran área",
        x=0.01, xanchor="left", font=dict(size=15)))
    graficos.append(("v2", "Composición por categoría y gran área",
                     "Cada rectángulo es proporcional a las personas. El bloque "
                     "«Junior» domina la población y explica por qué el estrato de "
                     "categoría, aunque solo explique el 7,08 %, sea el único que "
                     "reduce la varianza de forma apreciable.",
                     div(estilo(fig, alto=560, leyenda=False), "v2")))
    return graficos


def pestana_diagnosticos(eda: dict, dg: dict, vec: dict) -> list[tuple[str, str, str, str]]:
    m = dg["modelo_edad"]
    inf = m["influencia"]
    graficos = []

    # Q-Q de la edad (censo)
    edades = np.sort(vec["edades"])
    n = len(edades)
    teorico = stats.norm.ppf((np.arange(1, n + 1) - 0.5) / n)
    media, desv = float(edades.mean()), float(edades.std(ddof=1))
    cola = edades > 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=teorico, y=edades, mode="markers", name="Edad observada",
        marker=dict(size=4, color=AZUL, opacity=0.35), showlegend=False,
        hovertemplate="Cuantil teórico %{x:.2f}<br>Edad %{y:.2f}<extra></extra>"))
    if cola.any():
        fig.add_trace(go.Scatter(
            x=teorico[cola], y=edades[cola], mode="markers",
            name=f"Edad &gt; 100 ({int(cola.sum())} casos)",
            marker=dict(size=9, color=ROJO, symbol="diamond"),
            hovertemplate="<b>Cola derecha</b><br>Cuantil %{x:.2f}<br>Edad %{y:.2f}<extra></extra>"))
    linea = np.array([teorico.min(), teorico.max()])
    fig.add_trace(go.Scatter(x=linea, y=media + desv * linea, mode="lines",
                             name="Normal con la misma media y desviación",
                             line=dict(color=DORADO, width=2, dash="dash"), hoverinfo="skip"))
    nc = dg["normalidad"]["censo"]
    fig.update_xaxes(title="Cuantiles teóricos de la normal estándar")
    fig.update_yaxes(title="Edad observada (años)")
    fig.update_layout(title=dict(
        text=(f"Q-Q de la edad (censo, n = {miles(nc['n'])}) · asimetría "
              f"{num(nc['asimetria'], 1)} · exceso de curtosis {num(nc['curtosis_exceso'], 0)}"),
        x=0.01, xanchor="left", font=dict(size=15)))
    graficos.append(("d1", "Q-Q plot de la edad",
                     f"La edad NO es normal: la asimetría ({num(nc['asimetria'], 1)}) y el "
                     f"exceso de curtosis ({num(nc['curtosis_exceso'], 0)}) se concentran en "
                     f"la cola derecha, donde están los {eda['edad']['mayores_100']} "
                     "casos con edad mayor que 100. Shapiro-Wilk W = "
                     f"{num(nc['shapiro']['W'], 4)}; Lilliefors {pval(nc['lilliefors']['p_valor_montecarlo'], 4)}.",
                     div(estilo(fig, alto=520, leyenda=False), "d1")))

    # Residuos vs ajustados (+ scale-location)
    aj, resid = vec["ajustados"], vec["resid"]
    r_est = np.array(inf["residuo_estudentizado"])
    bp = m["breusch_pagan"]
    fig = make_subplots(rows=1, cols=2, shared_yaxes=False,
                        subplot_titles=("Residuos vs valores ajustados",
                                        "Scale-location"))
    fig.add_trace(go.Scatter(
        x=aj, y=resid, mode="markers", showlegend=False,
        marker=dict(size=4, color=AZUL, opacity=0.35),
        hovertemplate="Ajustada %{x:.1f} años<br>Residuo %{y:.1f}<extra></extra>"),
        row=1, col=1)
    fig.add_hline(y=0, line=dict(color=ROJO, width=1.6), row=1, col=1)
    raiz = np.sqrt(np.abs(r_est))
    fig.add_trace(go.Scatter(
        x=aj, y=raiz, mode="markers", showlegend=False,
        marker=dict(size=4, color=DORADO, opacity=0.35),
        hovertemplate="Ajustada %{x:.1f}<br>√|residuo| %{y:.2f}<extra></extra>"),
        row=1, col=2)
    cortes = pd.qcut(pd.Series(aj), 12, duplicates="drop")
    tendencia = pd.Series(raiz).groupby(cortes, observed=True).mean()
    centros = [iv.mid for iv in tendencia.index]
    fig.add_trace(go.Scatter(x=centros, y=tendencia.to_numpy(), mode="lines+markers",
                             showlegend=False, line=dict(color=ROJO, width=2.5),
                             marker=dict(size=6),
                             hovertemplate="Media por doceavo: %{y:.2f}<extra></extra>"),
                  row=1, col=2)
    fig.update_xaxes(title="Edad ajustada por el modelo (años)", row=1, col=1)
    fig.update_xaxes(title="Edad ajustada por el modelo (años)", row=1, col=2)
    fig.update_yaxes(title="Residuo (años)", row=1, col=1)
    fig.update_yaxes(title="√|residuo estudentizado|", row=1, col=2)
    fig.update_layout(title=dict(
        text=(f"Breusch-Pagan LM = {num(bp['LM'], 1)} (gl = {bp['gl']}, "
              f"{pval(bp['p_valor'])}) · errores HC3/clásico = "
              f"{num(m['errores_robustos']['ratio_hc3_clasico'], 3)}"),
        x=0.01, xanchor="left", font=dict(size=15)))
    graficos.append(("d2", "Residuos vs valores ajustados",
                     "No se aprecia estructura en los residuos y la dispersión es "
                     "estable a lo largo del ajuste: el supuesto de homocedasticidad "
                     "se sostiene (Breusch-Pagan " + pval(bp["p_valor"]) + "; Levene "
                     "entre celdas "
                     f"{pval(m['homocedasticidad_celdas']['levene']['p_valor'])}).",
                     div(estilo(fig, alto=500, leyenda=False), "d2")))

    # g-weights
    g = vec["g"]
    gw = m["g_weights"]
    fig = make_subplots(rows=1, cols=2, subplot_titles=(
        "Distribución de los g-weights", "Valores extremos (25 mayores)"))
    fig.add_trace(go.Histogram(x=g, nbinsx=50, marker_color=VERDE, showlegend=False,
                               hovertemplate="g ∈ %{x}<br>%{y} personas<extra></extra>"),
                  row=1, col=1)
    fig.add_vline(x=gw["min"], line=dict(color=GRIS, width=1, dash="dot"), row=1, col=1)
    fig.add_vline(x=gw["max"], line=dict(color=GRIS, width=1, dash="dot"), row=1, col=1)
    orden = np.sort(g)[::-1][:25]
    fig.add_trace(go.Bar(x=list(range(1, len(orden) + 1)), y=orden,
                         marker_color=DORADO, showlegend=False,
                         hovertemplate="Puesto %{x}<br>g = %{y:.4f}<extra></extra>"),
                  row=1, col=2)
    fig.add_hline(y=1.0, line=dict(color=GRIS, width=1.4, dash="dash"), row=1, col=2)
    fig.update_xaxes(title="g-weight", row=1, col=1)
    fig.update_yaxes(title="Personas", row=1, col=1)
    fig.update_xaxes(title="Puesto (de mayor a menor)", row=1, col=2)
    fig.update_yaxes(title="g-weight", row=1, col=2)
    fig.update_layout(title=dict(
        text=(f"g-weights del modelo de edad · rango [{num(gw['min'], 4)}, "
              f"{num(gw['max'], 4)}] · media {num(gw['media'], 4)}"),
        x=0.01, xanchor="left", font=dict(size=15)))
    graficos.append(("d3", "Distribución de los g-weights",
                     f"Los g-weights miden cuánto se aleja el peso calibrado del de "
                     f"diseño. Ninguno supera 5 (0 casos) ni 10 (0 casos): la "
                     f"calibración no produce pesos extremos, así que el GREG no "
                     f"depende de unas pocas observaciones dominantes.",
                     div(estilo(fig, alto=500, leyenda=False), "d3")))

    # Cook y leverage
    lev = np.array(inf["leverage"])
    cook = np.array(inf["cook"])
    fig = make_subplots(rows=1, cols=2, subplot_titles=(
        "Leverage vs distancia de Cook", "Distancia de Cook por observación"))
    fig.add_trace(go.Scatter(
        x=lev, y=cook, mode="markers", showlegend=False,
        marker=dict(size=5, color=AZUL, opacity=0.4),
        hovertemplate="Leverage %{x:.4f}<br>Cook %{y:.5f}<extra></extra>"),
        row=1, col=1)
    fig.add_vline(x=inf["umbral_leverage"], line=dict(color=DORADO, width=1.6, dash="dash"),
                  row=1, col=1)
    fig.add_hline(y=inf["umbral_cook"], line=dict(color=ROJO, width=1.6, dash="dash"),
                  row=1, col=1)
    fig.add_trace(go.Scatter(
        x=list(range(len(cook))), y=cook, mode="markers", showlegend=False,
        marker=dict(size=5, color=TEAL, opacity=0.4),
        hovertemplate="Observación %{x}<br>Cook %{y:.5f}<extra></extra>"),
        row=1, col=2)
    fig.add_hline(y=inf["umbral_cook"], line=dict(color=ROJO, width=1.6, dash="dash"),
                  row=1, col=2)
    fig.add_annotation(x=1.0, y=0.06, xref="paper", yref="paper", showarrow=False,
                       xanchor="right",
                       text=(f"{inf['n_sobre_umbral_leverage']} obs. sobre el umbral de "
                             f"leverage · {inf['n_sobre_umbral_cook']} sobre el de Cook · "
                             f"Cook máx = {num(inf['cook_max'], 5)}"),
                       font=dict(size=11, color=GRIS))
    fig.update_xaxes(title="Leverage (h<sub>ii</sub>)", row=1, col=1)
    fig.update_yaxes(title="Distancia de Cook", row=1, col=1)
    fig.update_xaxes(title="Observación (orden de la muestra)", row=1, col=2)
    fig.update_yaxes(title="Distancia de Cook", row=1, col=2)
    fig.update_layout(title=dict(
        text=("Influencia de las observaciones · umbral de leverage "
              f"= {num(inf['umbral_leverage'], 4)} (2k/n) · umbral de Cook "
              f"= {num(inf['umbral_cook'], 5)}"),
        x=0.01, xanchor="left", font=dict(size=15)))
    graficos.append(("d4", "Distancia de Cook y leverage",
                     f"Las líneas discontinuas marcan los umbrales habituales. "
                     f"{inf['n_sobre_umbral_leverage']} observaciones superan el umbral "
                     f"de leverage y {inf['n_sobre_umbral_cook']} el de Cook, pero el "
                     f"máximo de Cook ({num(inf['cook_max'], 5)}) está muy por debajo de 1: "
                     f"ninguna observación individual cambia las conclusiones.",
                     div(estilo(fig, alto=500, leyenda=False), "d4")))
    return graficos


# ============================================================================
# 4. Plantilla HTML
# ============================================================================
CSS = """
:root{
  --azul:#1E3780; --azul-osc:#0F1F4D; --dorado:#B7871E; --verde:#15803D;
  --rojo:#B91C1C; --ambar:#B45309; --gris:#64748B; --gris-claro:#94A3B8;
  --fondo:#F3F6FC; --blanco:#FFFFFF; --borde:#D6DEEE; --morado:#7C3AED;
  --teal:#0E7490;
}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:#0F172A;
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
.kpi .n{font-size:.7rem;color:var(--gris-claro);margin-top:7px;
  padding-top:6px;border-top:1px dashed var(--borde);line-height:1.35}
/* --- pestanas --- */
.tabs{display:flex;gap:6px;flex-wrap:wrap;border-bottom:2px solid var(--borde);
  margin-bottom:20px}
.tab-btn{background:transparent;border:0;border-bottom:3px solid transparent;
  padding:11px 18px;font-size:.92rem;font-weight:600;color:var(--gris);
  cursor:pointer;font-family:inherit;border-radius:8px 8px 0 0}
.tab-btn:hover{background:#E8EEF9;color:var(--azul-osc)}
.tab-btn.activo{color:var(--azul-osc);border-bottom-color:var(--dorado);
  background:#EAF2FD}
.panel{display:none}
.panel.activo{display:block}
/* --- graficos --- */
.card{background:var(--blanco);border:1px solid var(--borde);border-radius:12px;
  padding:14px 18px 6px;margin-bottom:18px;box-shadow:0 1px 2px rgba(15,31,77,.05)}
.card h3{margin:0 0 4px;font-size:1.02rem;color:var(--azul-osc)}
.card p.desc{margin:0 0 8px;font-size:.83rem;color:var(--gris);max-width:1080px}
.aviso{background:#FFF7E6;border:1px solid #E8C77A;border-left:4px solid var(--dorado);
  border-radius:8px;padding:11px 13px;font-size:.83rem;color:#5A4308;margin-bottom:18px}
.info{background:#EAF2FD;border:1px solid #B9D0EE;border-left:4px solid var(--azul);
  border-radius:8px;padding:11px 13px;font-size:.83rem;color:#123057;margin-bottom:18px}
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
    // Plotly calcula el ancho al dibujar. Si el panel estaba oculto (display:none)
    // los graficos quedan con ancho 0; al mostrarlo hay que pedir el redibujado.
    // Se buscan las dos clases: `plotly-graph-div` esta en el HTML y
    // `js-plotly-plot` la anade Plotly al dibujar.
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
  activar('tab-univariado');
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


def tarjeta_grafico(g: tuple) -> str:
    _, titulo, desc, cuerpo = g
    return (f'<div class="card"><h3>{_html.escape(titulo)}</h3>'
            f'<p class="desc">{desc}</p>{cuerpo}</div>')


def construir_html(kpis: list[dict], pestanas: list[tuple[str, str, str, list]],
                   versiones: dict) -> str:
    plotlyjs = (Path(plotly.__file__).parent / "package_data" /
                "plotly.min.js").read_text(encoding="utf-8")
    # El bundle se inserta dentro de una etiqueta <script>: si contuviera la
    # secuencia de cierre, el HTML se rompería ahi mismo.
    plotlyjs = plotlyjs.replace("</script>", "<\\/script>")

    botones = "".join(
        f'<button class="tab-btn" data-tab="{pid}">{_html.escape(nombre)}</button>'
        for pid, nombre, _, _ in pestanas)
    paneles = ""
    for pid, nombre, intro, graficos in pestanas:
        aviso = f'<div class="info">{intro}</div>' if intro else ""
        paneles += (f'<div class="panel" id="{pid}">{aviso}'
                    + "".join(tarjeta_grafico(g) for g in graficos) + "</div>")

    n_graficos = sum(len(p[3]) for p in pestanas)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análisis exploratorio de datos — Observatorio MinCiencias</title>
<style>{CSS}</style>
<script>{plotlyjs}</script>
</head>
<body>
<header>
  <h1>Análisis exploratorio de datos — Observatorio MinCiencias</h1>
  <div class="sub">Investigadores reconocidos por convocatoria (2013–2021).
  Panel interactivo de {n_graficos} gráficos en 4 pestañas: univariado, bivariado de
  retención, varianza entre grupos y diagnósticos del modelo GREG.</div>
  <div class="meta">Censo completo de {versiones['registros']} registros y
  {versiones['personas']} personas · {versiones['convocatorias']} convocatorias ·
  muestra MAS de {versiones['n_muestra']} personas (semilla 2026) ·
  generado el {versiones['fecha']}</div>
</header>
<div class="wrap">
  <div class="kpis">{''.join(tarjeta_kpi(k) for k in kpis)}</div>
  <div class="tabs">{botones}</div>
  {paneles}
  <footer>
    <b>Fuente:</b> base completa de investigadores reconocidos por MinCiencias,
    <code>datos.gov.co</code>, dataset <code>bqtm-4y2h</code> ·
    <code>Investigadores_Reconocidos_por_convocatoria_20261006.csv</code> (77 237 registros).
    El género se analiza con la columna colapsada; ver la decisión D010 y la
    ERRATA del proyecto para los matices de las cifras de edad.<br>
    <b>Autoría:</b> Kevin Leonardo Chaparro Reyes · Valentina Muñoz Palma ·
    Paula Margarita Triana Ancinez — Consultoría Estadística, Universidad Santo Tomás,
    2026-II.<br>
    Documento autocontenido: Plotly {versiones['plotly']} embebido, sin CDN ni
    conexión a internet. Las cifras principales son censales; las estimaciones
    muestrales (MAS, post-estratificación, GREG) aparecen etiquetadas como tales.
  </footer>
</div>
{JS}
</body>
</html>
"""


# ============================================================================
# 5. Main
# ============================================================================
def main() -> int:
    print("== Carga de fuentes ==")
    eda, est, dg = cargar_json()
    print(f"   eda_resultados.json, estimadores_resultados.json, "
          f"diagnosticos_greg.json")

    print("\n== Regeneración y validación de los vectores que faltan ==")
    vec = regenerar_vectores(eda, dg)

    print("\n== Construcción de las pestañas ==")
    u = eda["univariado_persona"]
    e = eda["edad"]
    r21 = est["retencion"]["2013\u21922021"]

    kpis = [
        {"titulo": "Registros", "valor": miles(eda["universo"]["registros"]),
         "subtitulo": "Censo completo · 6 convocatorias (2013–2021)",
         "nota": ""},
        {"titulo": "Personas únicas", "valor": miles(eda["universo"]["personas"]),
         "subtitulo": "Censo completo", "dorado": True, "nota": ""},
        {"titulo": "Convocatorias", "valor": str(eda["universo"]["convocatorias"]),
         "subtitulo": "2013, 2014, 2015, 2017, 2019 y 2021", "nota": ""},
        {"titulo": "Edad media", "valor": f"{e['media']:.2f}".replace(".", ","),
         "subtitulo": f"Censo completo ({miles(e['n'])} personas con edad registrada)",
         "nota": ("Estimación MAS: "
                  f"{est['edad']['mas']['estimador']:.2f}".replace(".", ",") +
                  " · post-estratificada: "
                  f"{est['edad']['post_estratificado']['estimador']:.2f}".replace(".", ",") +
                  " · GREG: "
                  f"{est['edad']['greg_lineal']['estimador']:.2f}".replace(".", ",") +
                  f" (n = {miles(est['edad']['n_muestra'])})")},
        {"titulo": "Retención 2013 → 2021", "valor": f"{r21['censo']*100:.1f} %".replace(".", ","),
         "subtitulo": f"Censo completo ({miles(eda['universo']['personas'])} personas)",
         "dorado": True,
         "nota": (f"Estimación MAS: {r21['mas']['estimador']*100:.1f} %".replace(".", ",") +
                  f" (n = {r21['mas']['n']} en 2013) · post-estratificada: "
                  f"{r21['post_estratificado']['estimador']*100:.1f} %".replace(".", ",") +
                  " · GREG: "
                  f"{r21['greg_lineal']['estimador']*100:.1f} %".replace(".", ","))},
    ]

    g1 = pestana_univariado(eda, vec)
    g2 = pestana_bivariado(eda, est)
    g3 = pestana_varianza(eda, vec)
    g4 = pestana_diagnosticos(eda, dg, vec)
    for nombre, gs in (("Univariado", g1), ("Bivariado", g2),
                       ("Varianza", g3), ("Diagnósticos", g4)):
        print(f"   {nombre:14} {len(gs)} gráficos")

    pestanas = [
        ("tab-univariado", "1 · Univariado", "", g1),
        ("tab-bivariado", "2 · Bivariado (retención)",
         "Todas las tasas de esta pestaña son <b>censales</b>: se calculan sobre el "
         "total de personas de cada convocatoria, no sobre la muestra. La pestaña 2 "
         "responde a «qué grupos se quedan y cuáles no».", g2),
        ("tab-varianza", "3 · Varianza entre grupos",
         "Cuánta varianza de la retención explica cada variable de estratificación. "
         "Es la evidencia que justifica el diseño de muestreo estratificado.", g3),
        ("tab-diagnosticos", "4 · Diagnósticos",
         "<b>Atención al alcance:</b> a diferencia de las tres pestañas anteriores, "
         "estos diagnósticos se calculan sobre la <b>muestra MAS</b> "
         f"(n = {vec['n_muestra']}), no sobre el censo: son propiedades del "
         "estimador GREG, no de la población. El censo se usa solo como referencia "
         "de normalidad de la edad (n = " + miles(vec["n_censo"]) + ").", g4),
    ]

    versiones = {
        "registros": miles(eda["universo"]["registros"]),
        "personas": miles(eda["universo"]["personas"]),
        "convocatorias": eda["universo"]["convocatorias"],
        "n_muestra": miles(vec["n_muestra"]),
        "plotly": plotly.__version__,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    print("\n== Escritura del HTML ==")
    documento = construir_html(kpis, pestanas, versiones)
    SALIDA.write_text(documento, encoding="utf-8")
    peso = SALIDA.stat().st_size
    print(f"   {SALIDA.relative_to(RAIZ)}")
    print(f"   peso: {peso:,} B = {peso/1024/1024:.2f} MB ({peso/1e6:.2f} MB decimales)")
    print(f"   gráficos: {sum(len(p[3]) for p in pestanas)} en "
          f"{len(pestanas)} pestañas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
