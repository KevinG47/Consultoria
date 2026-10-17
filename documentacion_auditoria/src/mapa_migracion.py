# -*- coding: utf-8 -*-
"""
mapa_migracion.py
=================

Construye el **mapa interactivo de flujos territoriales** de la Fase 2 (F2-11):
los 33 departamentos como polígonos coloreados por la tasa per cápita de F2-2,
una burbuja por departamento con el total de investigadores y las rutas de
migración del periodo como líneas con el destino marcado.

DOS SALIDAS CON LA MISMA FIGURA
-------------------------------
  1. `data/memoria/mapa_migracion.html` — página autocontenida (Plotly embebido,
     GeoJSON embebido, cero referencias externas). Se abre sin internet.
  2. La **pestaña 8** de `dashboard_fase2.html`: este módulo expone la figura y
     los bloques HTML, y el panel los inserta. Es la misma figura, no una copia.

CÓMO SE DIBUJA SIN RED
----------------------
  go.Choropleth   con `geojson` = el archivo de `data/geo/` y
                  `featureidkey="properties.codigo_dane"`  → los polígonos
  go.Scattergeo   burbujas en el centroide de cada departamento
  go.Scattergeo   una línea de origen a destino por ruta + marcador en el destino

`fig.update_geos(fitbounds="locations", visible=False)` encuadra Colombia y
apaga el fondo del mundo: no hay teselas, no hay peticiones, no hay CDN. Es
exactamente lo que el auditado NO tenía: él pedía teselas de OpenStreetMap en
tiempo de renderizado y, sin internet, el país desaparecía.

LO QUE EL MAPA DICE Y LO QUE NO
-------------------------------
- La ruta por defecto es el **flujo A** (mudanza de residencia entre la primera y
  la última convocatoria, 808 personas). El **flujo B** (nacimiento → residencia,
  11 922 personas) es la vista secundaria conmutable.
- Las rutas **Bogotá ↔ Cundinamarca** se dibujan con trazo punteado, color más
  claro y rombo en el destino (decisión D2): son mudanzas reales de municipio a
  la sabana, pero un mapa departamental las pinta igual que una migración
  interdepartamental, y no es el mismo fenómeno.
- Plotly **no dibuja puntas de flecha** sobre un subplot `geo`. La dirección se
  comunica con el marcador del destino y con el texto del hover; prometer una
  flecha sería prometer algo que la herramienta no da.

Uso:  python mapa_migracion.py
"""

from __future__ import annotations

import html as _html
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import plotly
import plotly.graph_objects as go
import plotly.io as pio

from paleta_fase2 import (BLANCO, CONFIG_PLOTLY, ESCALA_AZUL, NOMBRE_TEMPLATE,
                          PALETA, miles, num, pct, registrar_template)

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
MEM = DOC / "data" / "memoria"
GEO = DOC / "data" / "geo" / "colombia_departamentos.geojson"
PERCAPITA = MEM / "percapita_territorial.json"
FLUJOS = MEM / "flujos_territoriales.json"
SALIDA = MEM / "mapa_migracion.html"
GRAFICAS = MEM / "graficas_flujos"

ZMAX = 140.0            # tope de la rampa de color: la tasa máxima es 137,69
ALTO_MAPA = 660

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOVER_DEPTO = (
    "<b>%{customdata[0]}</b><br>"
    "Tasa per cápita: %{customdata[3]} por 100 000<br>"
    "%{customdata[1]} investigadores · %{customdata[2]} habitantes<br>"
    "Puesto %{customdata[4]} en tasa · %{customdata[5]} del stock nacional<br>"
    "Saldo neto del flujo A (2013 → 2021): %{customdata[6]} investigadores"
    "<extra></extra>")


def _menos(x: float) -> str:
    """Signo explícito y menos tipográfico: +5 · −57 · 0."""
    if x == 0:
        return "0"
    signo = "+" if x > 0 else "\u2212"
    return f"{signo}{abs(int(x))}"


# ============================================================================
# 1. Carga de fuentes
# ============================================================================
def cargar_geojson() -> dict:
    if not GEO.exists():
        raise SystemExit(
            f"No existe {GEO}. Ejecute primero `python preparar_geojson.py`.")
    return json.loads(GEO.read_text(encoding="utf-8"))


def cargar_percapita() -> dict:
    return json.loads(PERCAPITA.read_text(encoding="utf-8"))


def cargar_flujos() -> dict:
    if not FLUJOS.exists():
        raise SystemExit(
            f"No existe {FLUJOS}. Ejecute primero `python flujos_territoriales.py`.")
    return json.loads(FLUJOS.read_text(encoding="utf-8"))


# ============================================================================
# 2. Centroides: el punto donde va la burbuja de cada departamento
# ============================================================================
def _area_y_centroide(anillo: list) -> tuple[float, tuple[float, float]]:
    """Área (grados²) y centroide por la fórmula del polígono (shoelace)."""
    a = cx = cy = 0.0
    for i in range(len(anillo) - 1):
        x0, y0 = anillo[i]
        x1, y1 = anillo[i + 1]
        cruz = x0 * y1 - x1 * y0
        a += cruz
        cx += (x0 + x1) * cruz
        cy += (y0 + y1) * cruz
    if abs(a) < 1e-12:
        return 0.0, (anillo[0][0], anillo[0][1])
    a *= 0.5
    return abs(a), (cx / (6 * a), cy / (6 * a))


def _punto_en_anillo(p: tuple[float, float], anillo: list) -> bool:
    """Ray casting (par-impar) para un anillo."""
    x, y = p
    dentro = False
    for i in range(len(anillo) - 1):
        x0, y0 = anillo[i]
        x1, y1 = anillo[i + 1]
        if (y0 > y) != (y1 > y):
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xi:
                dentro = not dentro
    return dentro


def _punto_en_geometria(p: tuple[float, float], geom: dict) -> bool:
    if geom["type"] == "Polygon":
        anillos = geom["coordinates"]
        if not _punto_en_anillo(p, anillos[0]):
            return False
        return not any(_punto_en_anillo(p, h) for h in anillos[1:])
    return any(_punto_en_geometria(p, {"type": "Polygon", "coordinates": poly})
               for poly in geom["coordinates"])


def _en_anillo_np(puntos: np.ndarray, anillo: list) -> np.ndarray:
    """Versión vectorizada del ray casting para la búsqueda por rejilla."""
    a = np.asarray(anillo, dtype=float)
    x, y = puntos[:, 0], puntos[:, 1]
    x0, y0 = a[:-1, 0], a[:-1, 1]
    x1, y1 = a[1:, 0], a[1:, 1]
    cond = (y0[None, :] > y[:, None]) != (y1[None, :] > y[:, None])
    dy = np.where(y1 - y0 == 0, 1e-12, y1 - y0)
    xi = x0[None, :] + (y[:, None] - y0[None, :]) * (x1 - x0)[None, :] / dy[None, :]
    return ((x[:, None] < xi) & cond).sum(axis=1) % 2 == 1


def _respaldo_rejilla(geom: dict, anillo: list) -> tuple[float, float]:
    """
    Si el centroide del anillo mayor cae fuera del polígono (pasa cuando el
    centroide cae en un hueco, por ejemplo Bogotá dentro de Cundinamarca), se
    busca el punto interior más alejado de la frontera en una rejilla.
    """
    a = np.asarray(anillo, dtype=float)
    xs = np.linspace(a[:, 0].min(), a[:, 0].max(), 240)
    ys = np.linspace(a[:, 1].min(), a[:, 1].max(), 240)
    malla = np.array([(x, y) for x in xs for y in ys])
    if geom["type"] == "Polygon":
        anillos = geom["coordinates"]
        dentro = _en_anillo_np(malla, anillos[0])
        for h in anillos[1:]:
            dentro &= ~_en_anillo_np(malla, h)
    else:
        dentro = np.zeros(len(malla), dtype=bool)
        for poly in geom["coordinates"]:
            d = _en_anillo_np(malla, poly[0])
            for h in poly[1:]:
                d &= ~_en_anillo_np(malla, h)
            dentro |= d
    candidatos = malla[dentro]
    if len(candidatos) == 0:
        raise SystemExit("No se encontró ningún punto interior en la rejilla")
    # distancia mínima a los vértices de todos los anillos (frontera aproximada)
    frontera = [(p[0], p[1]) for poly in ([geom["coordinates"]]
                                          if geom["type"] == "Polygon"
                                          else geom["coordinates"])
                for an in poly for p in an]
    fr = np.asarray(frontera, dtype=float)
    mejor, mejor_d = None, -1.0
    for c in candidatos:
        d = np.sqrt(((fr - c) ** 2).sum(axis=1)).min()
        if d > mejor_d:
            mejor, mejor_d = c, d
    return float(mejor[0]), float(mejor[1])


def centroides(gj: dict) -> tuple[dict[str, tuple[float, float]], int]:
    """{codigo: (lat, lon)} para los 33 departamentos. Devuelve también cuántos
    necesitaron el respaldo por rejilla."""
    salida: dict[str, tuple[float, float]] = {}
    n_respaldo = 0
    for f in gj["features"]:
        cod = f["properties"]["codigo_dane"]
        geom = f["geometry"]
        poligonos = ([geom["coordinates"]] if geom["type"] == "Polygon"
                     else geom["coordinates"])
        # anillo exterior de mayor área = la parte continental principal
        mayor, area = None, -1.0
        for poly in poligonos:
            a, _ = _area_y_centroide(poly[0])
            if a > area:
                mayor, area = poly[0], a
        _, centro = _area_y_centroide(mayor)
        if not _punto_en_geometria(centro, geom):
            cent = _respaldo_rejilla(geom, mayor)
            n_respaldo += 1
        else:
            cent = centro
        if not _punto_en_geometria(cent, geom):
            raise SystemExit(f"El centroide de {cod} sigue fuera del polígono")
        salida[cod] = (cent[1], cent[0])   # (lat, lon)
    if len(salida) != 33:
        raise SystemExit(f"Se esperaban 33 centroides, hay {len(salida)}")
    return salida, n_respaldo


# ============================================================================
# 3. Tabla de departamentos (F2-2 + centroide + saldo del flujo A)
# ============================================================================
def tabla_departamentos(gj: dict, per: dict, flujo_a: dict,
                        cent: dict[str, tuple[float, float]]) -> list[dict]:
    stock = per["tasa_por_100000"]["stock_ultima_convocatoria"]
    if len(stock) != 33:
        raise SystemExit(f"percapita_territorial.json trae {len(stock)} departamentos")
    saldo = flujo_a["saldo_neto"]
    filas = []
    for f in gj["features"]:
        cod = f["properties"]["codigo_dane"]
        nombre = f["properties"]["nombre"]
        if nombre not in stock:
            raise SystemExit(f"{nombre!r} no está en percapita_territorial.json")
        d = stock[nombre]
        lat, lon = cent[cod]
        filas.append({"codigo": cod, "nombre": nombre,
                      "investigadores": int(d["investigadores"]),
                      "poblacion": int(d["poblacion"]),
                      "tasa": float(d["tasa_por_100000"]),
                      "lat": lat, "lon": lon,
                      "saldo_a": int(saldo.get(nombre, 0))})
    filas.sort(key=lambda t: t["codigo"])
    orden = sorted(filas, key=lambda t: (-t["tasa"], t["codigo"]))
    for i, t in enumerate(orden, 1):
        t["rank"] = i
    total = sum(t["investigadores"] for t in filas)
    total_json = per["conteos"]["stock_personas"]
    if total != total_json:
        raise SystemExit(f"Las burbujas suman {total} y F2-2 declara {total_json}")
    return filas


# ============================================================================
# 4. La figura
# ============================================================================
def _trazas_de_rutas(rutas: list[dict], total: int, etiqueta_total: str,
                     cent: dict[str, tuple[float, float]], color: str,
                     dash: str | None, simbolo: str, factor_ancho: float = 1.0,
                     ) -> tuple[list[go.Scattergeo], go.Scattergeo | None]:
    """
    Trazas de línea (una por clase de grosor) y traza de marcadores de destino.

    El grosor de la línea va como √(personas): con 38 personas no se puede usar
    el valor bruto sin que las rutas grandes se coman el mapa. El texto de cada
    punto lleva la ruta completa, así que el hover explica qué se está viendo.
    """
    if not rutas:
        return [], None
    raiz = math.sqrt(max(r["personas"] for r in rutas))
    clases: dict[float, dict] = {}
    lon_m, lat_m, txt_m, tam_m, sim_m, col_m, cd_m = [], [], [], [], [], [], []

    for r in rutas:
        o, d = r["origen_codigo"], r["destino_codigo"]
        (lat_o, lon_o), (lat_d, lon_d) = cent[o], cent[d]
        ancho = factor_ancho * (0.9 + 2.4 * math.sqrt(r["personas"]) / raiz)
        clase = round(ancho * 2) / 2
        texto = (f"<b>{r['origen']} → {r['destino']}</b><br>"
                 f"{miles(r['personas'])} personas · "
                 f"{pct(r['pct_de_movimientos'], 2)} de los {etiqueta_total}")
        if r.get("area_metropolitana"):
            texto += ("<br>Área metropolitana de la sabana de Bogotá: "
                      "mudanza real de municipio, no migración interdepartamental")
        t = clases.setdefault(clase, {"lon": [], "lat": [], "txt": []})
        t["lon"] += [lon_o, lon_d, None]
        t["lat"] += [lat_o, lat_d, None]
        t["txt"] += [texto, texto, None]
        lon_m.append(lon_d)
        lat_m.append(lat_d)
        txt_m.append(texto)
        tam_m.append(4.5 + 6.0 * math.sqrt(r["personas"]) / raiz)
        sim_m.append(simbolo)
        col_m.append(color)

    lineas = [go.Scattergeo(
        lon=t["lon"], lat=t["lat"], mode="lines",
        line=dict(color=color, width=clase, dash=dash or "solid"),
        text=t["txt"], hovertemplate="%{text}<extra></extra>",
        showlegend=False,
    ) for clase, t in sorted(clases.items())]

    marcadores = go.Scattergeo(
        lon=lon_m, lat=lat_m, mode="markers",
        marker=dict(size=tam_m, symbol=sim_m, color=col_m,
                    line=dict(width=1.0, color=BLANCO), opacity=0.95),
        text=txt_m, hovertemplate="%{text}<extra></extra>",
        showlegend=False,
    )
    return lineas, marcadores


def _rutas_dibujables(flujo: dict) -> list[dict]:
    return [r for r in flujo["rutas_detalle"] if r["dibujable"]]


def figura_mapa(tabla: list[dict], gj: dict, flujos: dict,
                cent: dict[str, tuple[float, float]]) -> go.Figure:
    per = cargar_percapita()
    nacional = per["indicadores_clave"]["tasa_nacional_por_100000"]
    total_stock = per["conteos"]["stock_personas"]

    geo_por_codigo = {f["properties"]["codigo_dane"]: f["geometry"]
                      for f in gj["features"]}
    geojson_plot = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "id": t["codigo"],
                      "properties": {"codigo_dane": t["codigo"]},
                      "geometry": geo_por_codigo[t["codigo"]]} for t in tabla],
    }

    cd = [[t["nombre"], miles(t["investigadores"]), miles(t["poblacion"]),
           num(t["tasa"], 2), f"{t['rank']} de 33",
           pct(100 * t["investigadores"] / total_stock, 2),
           _menos(t["saldo_a"])] for t in tabla]

    coropleta = go.Choropleth(
        geojson=geojson_plot,
        locations=[t["codigo"] for t in tabla],
        z=[t["tasa"] for t in tabla],
        featureidkey="properties.codigo_dane",
        colorscale=ESCALA_AZUL, zmin=0.0, zmax=ZMAX,
        marker_line_color=BLANCO, marker_line_width=0.8,
        colorbar=dict(
            title=dict(text=f"Investigadores<br>por 100 000<br>"
                            f"(Colombia {num(nacional, 2)})", font=dict(size=10)),
            thickness=13, len=0.62, x=1.004, y=0.5, outlinewidth=0,
            tickvals=[0, round(nacional, 2), ZMAX],
            ticktext=["0", num(nacional, 2), num(ZMAX, 0)],
            tickfont=dict(size=10)),
        customdata=cd, hovertemplate=HOVER_DEPTO,
        name="Tasa per cápita (F2-2)", showlegend=False,
    )

    tam_max = max(t["investigadores"] for t in tabla)
    burbujas = go.Scattergeo(
        lon=[t["lon"] for t in tabla], lat=[t["lat"] for t in tabla],
        mode="markers",
        marker=dict(
            # piso de 5 px para que Vichada (1 investigador) no desaparezca
            size=[5.0 + 20.0 * math.sqrt(t["investigadores"]) / math.sqrt(tam_max)
                  for t in tabla],
            color=PALETA["dorado"], opacity=0.70,
            line=dict(width=1.1, color=BLANCO)),
        customdata=cd, hovertemplate=HOVER_DEPTO,
        name="Investigadores", showlegend=False,
    )

    # --- rutas del flujo A (por defecto) ------------------------------------
    # Se dibujan las 10 rutas mayores (decision D3): 231 rutas convertrian el
    # mapa en una maraña y el mensaje es la direccion, no la cola larga.
    a = flujos["flujo_a"]
    a_top = [r for r in a["top10"] if r["dibujable"]]
    a_inter = [r for r in a_top if not r["area_metropolitana"]]
    a_metro = [r for r in a_top if r["area_metropolitana"]]
    tot_a = a["movimientos"]
    lineas_a1, dest_a1 = _trazas_de_rutas(
        a_inter, tot_a, f"{miles(tot_a)} movimientos", cent,
        color=PALETA["primario"], dash=None, simbolo="circle")
    lineas_a2, dest_a2 = _trazas_de_rutas(
        a_metro, tot_a, f"{miles(tot_a)} movimientos", cent,
        color=PALETA["claro"], dash="dot", simbolo="diamond", factor_ancho=0.85)

    # --- rutas del flujo B (vista secundaria) -------------------------------
    b = flujos["flujo_b"]
    b_dib = _rutas_dibujables(b)
    b_top = b_dib[:10]          # top 10 que se pueden dibujar
    tot_b = b["movimientos"]
    lineas_b, dest_b = _trazas_de_rutas(
        b_top, tot_b, f"{miles(tot_b)} casos", cent,
        color=PALETA["secundario"], dash=None, simbolo="circle")

    trazas: list = [coropleta, burbujas]
    trazas += lineas_a1 + lineas_a2 + [t for t in (dest_a1, dest_a2) if t]
    n_a = len(trazas) - 2
    trazas += lineas_b + ([dest_b] if dest_b else [])
    n_b = len(trazas) - 2 - n_a

    vis_a = [True, True] + [True] * n_a + [False] * n_b
    vis_b = [True, True] + [False] * n_a + [True] * n_b
    for i, tr in enumerate(trazas):
        tr.visible = vis_a[i]

    fig = go.Figure(data=trazas)
    fig.update_layout(
        template=NOMBRE_TEMPLATE,
        height=ALTO_MAPA,
        margin=dict(l=6, r=6, t=58, b=6),
        paper_bgcolor=PALETA["fondo"],
        plot_bgcolor=BLANCO,
        showlegend=False,
        hovermode="closest",
        updatemenus=[dict(
            type="buttons", direction="right", x=0.0, y=1.0,
            xanchor="left", yanchor="bottom", pad=dict(t=2, r=8),
            bgcolor=BLANCO, bordercolor=PALETA["gris_claro"], font=dict(size=12),
            active=0, showactive=True,
            buttons=[
                dict(label=f"Flujo A · mudanza 2013 → 2021 ({miles(tot_a)})",
                     method="update", args=[{"visible": vis_a}]),
                dict(label=f"Flujo B · nacimiento → residencia ({miles(tot_b)})",
                     method="update", args=[{"visible": vis_b}]),
            ])],
    )
    fig.update_geos(fitbounds="locations", visible=False, bgcolor=PALETA["fondo"],
                    showframe=False, projection=dict(type="mercator"))
    return fig


def _corto(nombre: str) -> str:
    """Nombre corto para ejes: el de San Andrés ocupa tres renglones."""
    return (nombre.replace("Archipiélago de ", "")
            .replace(", Providencia y Santa Catalina", ""))


def figura_saldo_neto(flujo_a: dict) -> go.Figure:
    """Barras horizontales del saldo neto de las 808 mudanzas (entradas − salidas)."""
    rutas = flujo_a["rutas_detalle"]
    entra, sale = Counter(), Counter()
    for r in rutas:
        entra[r["destino"]] += r["personas"]
        sale[r["origen"]] += r["personas"]
    deps = sorted(set(entra) | set(sale),
                  key=lambda d: (-(entra[d] - sale[d]), d))
    for d in deps:
        if entra[d] - sale[d] != flujo_a["saldo_neto"].get(d, 0):
            raise SystemExit(f"El saldo de {d} no cuadra con el JSON")
    neto = [entra[d] - sale[d] for d in deps]
    nombres = [_corto(d) for d in deps]

    fig = go.Figure(go.Bar(
        x=neto, y=nombres, orientation="h",
        marker_color=[PALETA["primario"] if v > 0 else PALETA["claro"] for v in neto],
        text=[_menos(v) for v in neto], textposition="outside", cliponaxis=False,
        customdata=list(zip([entra[d] for d in deps], [sale[d] for d in deps])),
        hovertemplate=("<b>%{y}</b><br>Entran %{customdata[0]} · salen "
                       "%{customdata[1]}<br>Saldo neto %{x:+d} investigadores"
                       "<extra></extra>")))
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=10))
    fig.update_xaxes(title="Saldo neto (entradas − salidas) de las 808 mudanzas")
    fig.update_layout(title=dict(
        text=("Quién gana y quién pierde con las 808 mudanzas · azul oscuro gana, "
              "azul claro pierde · la suma de todos los saldos es 0"),
        x=0.01, xanchor="left", font=dict(size=14)))
    fig.update_layout(height=600, margin=dict(l=196, r=42, t=76, b=52),
                      bargap=0.24, showlegend=False)
    return fig


# ============================================================================
# 5. Bloques HTML (los comparten la página suelta y la pestaña 8)
# ============================================================================
NOTA_D1 = (
    "<b>Antes de leer el mapa: una mudanza de Bogotá a Chía se ve igual que una "
    "migración de Antioquia a Bogotá, y no son el mismo fenómeno.</b> En un mapa "
    "departamental las dos son «una línea entre dos departamentos». Pero la primera "
    "es un cambio de municipio dentro de la misma conurbación y la segunda es una "
    "migración interdepartamental. Aquí las 808 mudanzas del periodo <b>cambian "
    "también de municipio en los 808 casos</b> (0 conservan el mismo) y las de "
    "Bogotá ↔ Cundinamarca van a o desde Chía, Cajicá, Mosquera o Zipaquirá: son "
    "mudanzas reales, no ruido de captura. Por eso se dibujan aparte.")

NOTA_D2 = (
    "<b>Cómo distinguirlas en el mapa:</b> las rutas Bogotá ↔ Cundinamarca usan "
    "<b>trazo punteado, color más claro y rombo en el destino</b>; las demás, trazo "
    "continuo azul oscuro y punto en el destino. La ruta por defecto es el "
    "<b>flujo A</b> (mudanza 2013 → 2021, 808 personas en 231 rutas); el botón "
    "cambia al <b>flujo B</b> (nacimiento → residencia, 11 922 casos), que es "
    "migración acumulada de toda la vida y no del periodo.")

GUIA_LECTURA = (
    "El <b>color del departamento</b> es la tasa per cápita de F2-2 (stock de la "
    "última convocatoria, población censada de 2018, 28 950 personas; Colombia: "
    "65,55 por 100 000). El <b>tamaño de la burbuja</b> es el total de "
    "investigadores del departamento. El <b>grosor de la línea</b> va como la raíz "
    "del número de personas, y el <b>punto o rombo</b> marca el destino del flujo. "
    "Pase el cursor por un departamento para ver su tasa, su puesto y su saldo "
    "neto; pase el cursor por una ruta para ver cuántas personas la recorrieron.")


def _celda(texto: str) -> str:
    return _html.escape(str(texto))


def tabla_top10_html(flujo: dict, etiqueta: str, total: int) -> str:
    filas = ""
    for i, r in enumerate(flujo["top10"], 1):
        marca = (" <span style='color:#64748B;font-size:.92em'>· área metropolitana</span>"
                 if r.get("area_metropolitana") else "")
        filas += (f"<tr><td class='id'>{i}</td>"
                  f"<td>{_celda(r['origen'])} → {_celda(r['destino'])}{marca}</td>"
                  f"<td class='num'>{miles(r['personas'])}</td>"
                  f"<td class='num'>{pct(r['pct_de_movimientos'], 2)}</td></tr>")
    return ("<table class='tabla'><thead><tr>"
            "<th style='width:34px'>#</th><th>Ruta</th>"
            "<th style='width:96px'>Personas</th>"
            f"<th style='width:150px'>% de los {miles(total)}</th>"
            "</tr></thead><tbody>" + filas + "</tbody></table>")


def nota_top10_html(flujo: dict, total: int, clave: str) -> str:
    if clave == "a":
        return (f"<p class='nota-tabla'>Las 10 primeras rutas explican "
                f"<b>{pct(flujo['pct_movimientos_top10'], 2)}</b> de los "
                f"{miles(total)} movimientos; las 20 primeras, "
                f"{pct(flujo['pct_movimientos_top20'], 2)}. Las {flujo['rutas']} rutas "
                f"restantes son cola larga: {flujo['rutas_una_persona']} rutas tienen "
                f"una sola persona.</p>")
    return (f"<p class='nota-tabla'>Las 10 primeras rutas <b>dibujables</b> explican "
            f"<b>{pct(flujo['pct_movimientos_top10'], 2)}</b> de los {miles(total)} "
            f"casos. La ruta mayor real, <b>Exterior → Bogotá, D. C. (561 personas)</b>, "
            f"no se puede dibujar sobre un mapa de departamentos: en total "
            f"{miles(flujo['personas_no_dibujables'])} personas en "
            f"{flujo['rutas_no_dibujables']} rutas nacieron fuera de Colombia y solo "
            f"se declaran en el texto.</p>")


def leyenda_html(per: dict) -> str:
    nacional = per["indicadores_clave"]["tasa_nacional_por_100000"]
    sw = "display:inline-block;vertical-align:middle;margin-right:8px"
    return (
        "<div class='info' style='display:grid;"
        "grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:6px 18px'>"
        "<div><span style='%s;width:54px;height:10px;border-radius:2px;"
        "background:linear-gradient(90deg,#EAF0F9,#7BA7D0,#4A6BA8,#1E3780)'></span>"
        "Color del departamento: tasa per cápita de F2-2 · Colombia %s</div>"
        "<div><span style='%s;width:14px;height:14px;border-radius:50%%;"
        "background:#B7871E;opacity:.75'></span>"
        "Tamaño de la burbuja: investigadores reconocidos</div>"
        "<div><span style='%s;width:46px;border-top:3px solid #1E3780'></span>"
        "Ruta interdepartamental (grosor ∝ √personas)</div>"
        "<div><span style='%s;width:46px;border-top:2px dotted #7BA7D0'></span>"
        "Ruta de área metropolitana (Bogotá ↔ Cundinamarca)</div>"
        "<div><span style='%s;width:9px;height:9px;transform:rotate(45deg);"
        "background:#7BA7D0'></span>"
        "Destino del flujo (rombo = área metropolitana)</div>"
        "<div><span style='%s;width:9px;height:9px;border-radius:50%%;"
        "background:#1E3780'></span>"
        "Destino del flujo interdepartamental</div>"
        "</div>" % (sw, num(nacional, 2), sw, sw, sw, sw, sw))


def conclusion_html() -> str:
    return (
        "<b>Lo que el mapa dice:</b> en el periodo 2013 → 2021 se mudaron de "
        "departamento <b>808 personas</b> de las 18 430 comparables, es decir el "
        "<b>4,38 %</b>. No es un mapa espectacular y no se presenta como tal: la ruta "
        "mayor tiene 38 personas. Lo que sí muestra es una <b>dirección</b>: Bogotá "
        "pierde 57 investigadores en el balance neto, mientras Cundinamarca (+31), "
        "Boyacá (+21) y Atlántico (+20) ganan. Y muestra un <b>límite del instrumento</b>: "
        "con un mapa departamental no se puede separar la mudanza a la sabana de la "
        "migración interdepartamental, que es exactamente lo que el repositorio auditado "
        "prometía sin resolver."
        "<br><br><b>Por qué hay dos flujos:</b> el flujo B (11 922 personas, 41,58 %) "
        "no contradice al A: mide otra cosa. B es migración acumulada de toda la vida y "
        "su primera ruta nace fuera del país (Exterior → Bogotá, 561). A es la que "
        "promete el enunciado («entre 2013 y 2021») y por eso es la vista por defecto. "
        "Comparar los dos números como si uno corrigiera al otro sería el error que este "
        "mapa intenta evitar."
        "<br><br><b>De dónde sale este análisis:</b> F2-11 no es uno de los diez análisis "
        "planificados para la Fase 2; es un análisis nuevo, autorizado tras el estudio de "
        "viabilidad de los mapas. Por eso la pestaña 7 sigue contando <b>siete entregados</b> "
        "de los diez planificados: este se suma aparte y no cambia ese balance.")


def bloque_tablas_html(flujos: dict) -> str:
    a, b = flujos["flujo_a"], flujos["flujo_b"]
    return (
        "<div class='card'><h3>Flujo A · las 10 rutas de la mudanza 2013 → 2021</h3>"
        "<p class='desc'>Departamento de la primera convocatoria frente al de la última, "
        "para las 18 430 personas con dos o más convocatorias y departamento válido en "
        "ambas.</p>"
        + tabla_top10_html(a, "A", a["movimientos"])
        + nota_top10_html(a, a["movimientos"], "a")
        + "</div>"
        "<div class='card'><h3>Flujo B · las 10 rutas dibujables del nacimiento a la "
        "residencia</h3>"
        "<p class='desc'>Departamento de nacimiento frente al de residencia en la última "
        "convocatoria. Es migración acumulada, no del periodo.</p>"
        + tabla_top10_html(b, "B", b["movimientos"])
        + nota_top10_html(b, b["movimientos"], "b")
        + "</div>")


# ============================================================================
# 6. Página autocontenida
# ============================================================================
CSS_MAPA = """
:root{--azul:#1E3780;--azul-osc:#0F1F4D;--dorado:#B7871E;--dorado-claro:#D4A84A;
  --gris:#64748B;--gris-osc:#334155;--gris-claro:#CBD5E1;--fondo:#F8FAFC;
  --blanco:#FFFFFF;--borde:#E2E8F0;--texto:#1E293B;--tenue:#EAF0F9}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:var(--texto);
  font-family:"Montserrat","Segoe UI",Roboto,system-ui,-apple-system,Arial,sans-serif;
  font-size:15px;line-height:1.5}
header{background:linear-gradient(135deg,var(--azul-osc),var(--azul));color:#fff;
  padding:22px 26px}
header h1{margin:0 0 6px;font-size:1.42rem}
header .sub{font-size:.86rem;color:#C7D2E8;max-width:1100px}
header .meta{font-size:.76rem;color:#9FB2D6;margin-top:8px}
.wrap{max-width:1180px;margin:0 auto;padding:20px 26px 40px}
.card{background:var(--blanco);border:1px solid var(--borde);border-radius:12px;
  padding:14px 18px 10px;margin-bottom:18px;box-shadow:0 1px 2px rgba(30,55,128,.05)}
.card h3{margin:0 0 4px;font-size:1.02rem;color:var(--azul-osc)}
.card p.desc{margin:0 0 10px;font-size:.83rem;color:var(--gris);max-width:1080px}
.aviso{background:#FFFBF0;border:1px solid var(--dorado-claro);
  border-left:5px solid var(--dorado);border-radius:8px;padding:12px 14px;
  font-size:.86rem;color:#5A4308;margin-bottom:14px}
.info{background:var(--tenue);border:1px solid #7BA7D0;border-left:4px solid var(--azul);
  border-radius:8px;padding:11px 13px;font-size:.82rem;color:#123057;margin-bottom:14px}
.tabla{width:100%;border-collapse:collapse;font-size:.8rem;margin:6px 0 8px}
.tabla th{background:var(--tenue);color:var(--azul-osc);text-align:left;
  padding:8px 9px;border-bottom:2px solid #7BA7D0;font-size:.74rem;
  text-transform:uppercase;letter-spacing:.4px}
.tabla td{padding:7px 9px;border-bottom:1px solid var(--borde);vertical-align:top}
.tabla tbody tr:hover{background:#F7FAFD}
.tabla td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tabla td.id{font-weight:700;color:var(--azul)}
.nota-tabla{font-size:.76rem;color:var(--gris);margin:2px 0 8px;max-width:1050px}
.concl{background:#F3F6FB;border:1px solid #7BA7D0;border-left:4px solid var(--dorado);
  border-radius:10px;padding:14px 16px;margin:0 0 20px;font-size:.87rem;
  line-height:1.6;color:var(--gris-osc)}
footer{border-top:1px solid var(--borde);margin-top:26px;padding-top:16px;
  font-size:.78rem;color:var(--gris)}
footer code{font-family:"Fira Code",Consolas,"Courier New",monospace;font-size:.76rem}
@media(max-width:760px){.wrap{padding:14px}}
"""


def documento_html(fig_mapa: go.Figure, fig_saldo: go.Figure, flujos: dict,
                   per: dict) -> str:
    bundle = (Path(plotly.__file__).parent / "package_data" /
              "plotly.min.js").read_text(encoding="utf-8")
    bundle = bundle.replace("</script>", "<\\/script>")
    config = dict(CONFIG_PLOTLY)
    config["scrollZoom"] = True
    div_mapa = pio.to_html(fig_mapa, include_plotlyjs=False, full_html=False,
                           div_id="mapa-migracion", config=config)
    div_saldo = pio.to_html(fig_saldo, include_plotlyjs=False, full_html=False,
                            div_id="grafico-saldo", config=CONFIG_PLOTLY)
    a, b = flujos["flujo_a"], flujos["flujo_b"]
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>F2-11 · Mapas de flujos de migración territorial</title>
<style>{CSS_MAPA}</style>
<script>{bundle}</script>
</head>
<body>
<header>
  <h1>Flujos de migración territorial de los investigadores reconocidos</h1>
  <div class="sub">F2-11 · Mapa interactivo sobre los 33 departamentos: tasa per cápita
  de F2-2, burbujas de investigadores y rutas de migración. Dos definiciones
  conmutables: <b>A</b>, la mudanza entre la primera y la última convocatoria
  ({miles(a['movimientos'])} personas), y <b>B</b>, la residencia fuera del
  departamento de nacimiento ({miles(b['movimientos'])} casos).</div>
  <div class="meta">{miles(flujos['fuente']['registros'])} registros ·
  {miles(flujos['fuente']['personas'])} personas · 6 convocatorias (2013–2021) ·
  Plotly {plotly.__version__} embebido · sin CDN ni conexión a internet</div>
</header>
<div class="wrap">
  <div class="aviso">{NOTA_D1}<br><br>{NOTA_D2}</div>
  <div class="card">
    <h3>Mapa de flujos y tasa per cápita</h3>
    <p class="desc">{GUIA_LECTURA}</p>
    {leyenda_html(per)}
    {div_mapa}
  </div>
  <div class="card">
    <h3>Saldo neto por departamento</h3>
    <p class="desc">Entradas menos salidas de las 808 mudanzas. Un saldo positivo
    no significa que el departamento «gane» investigadores en términos absolutos:
    significa que, entre quienes se mudaron, recibió más de los que perdió.</p>
    {div_saldo}
  </div>
  {bloque_tablas_html(flujos)}
  <div class="concl"><span style="display:block;font-size:.7rem;font-weight:700;
    text-transform:uppercase;letter-spacing:.8px;color:#B7871E;margin-bottom:6px">
    Conclusión</span>{conclusion_html()}</div>
  <footer>
    <b>Fuente de los conteos:</b> base completa de investigadores reconocidos por
    MinCiencias, <code>datos.gov.co</code>, dataset <code>bqtm-4y2h</code> ·
    <code>Investigadores_Reconocidos_por_convocatoria_20261006.csv</code>
    ({miles(flujos['fuente']['registros'])} registros).<br>
    <b>Fuente de las tasas per cápita:</b> F2-2, <code>percapita_territorial.json</code>
    (población censada 2018 del DANE, cuadro 1PD).<br>
    <b>Geometrías:</b> <code>data/geo/colombia_departamentos.geojson</code>, GeoJSON
    público de john-guerra derivado de DIVIPOLA/IGAC; procedencia, SHA-256 y criterio
    de limpieza en <code>colombia_departamentos.procedencia.txt</code>. La unión es
    <b>por código DIVIPOLA</b>, nunca por nombre.<br>
    <b>Autoría:</b> Kevin Leonardo Chaparro Reyes · Valentina Muñoz Palma ·
    Paula Margarita Triana Ancinez — Consultoría Estadística, Universidad Santo Tomás,
    2026-II. Documento autocontenido: se abre sin internet.
  </footer>
</div>
</body>
</html>
"""


# ============================================================================
# 7. Figuras estáticas para el documento
# ============================================================================
def figuras_estaticas(flujos: dict) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    GRAFICAS.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": PALETA["gris_claro"],
                         "axes.labelcolor": PALETA["texto"],
                         "text.color": PALETA["texto"],
                         "xtick.color": PALETA["gris_medio"],
                         "ytick.color": PALETA["gris_oscuro"]})
    salidas = []

    def barras_top10(flujo: dict, titulo: str, archivo: str, metro: bool) -> None:
        rutas = flujo["top10"][::-1]
        fig, ax = plt.subplots(figsize=(7.4, 4.0), dpi=190)
        y = [f"{r['origen']} → {r['destino']}" for r in rutas]
        x = [r["personas"] for r in rutas]
        colores = [PALETA["claro"] if (metro and r.get("area_metropolitana"))
                   else PALETA["primario"] for r in rutas]
        ax.barh(y, x, color=colores, height=0.66)
        for i, v in enumerate(x):
            ax.text(v + max(x) * 0.012, i, miles(v), va="center",
                    fontsize=8.5, color=PALETA["gris_oscuro"])
        ax.set_xlim(0, max(x) * 1.16)
        ax.set_xlabel("Personas")
        ax.set_title(titulo, loc="left", fontsize=10.5,
                     color=PALETA["primario_oscuro"])
        ax.grid(axis="x", color=PALETA["gris_claro"], linewidth=0.7, alpha=0.8)
        ax.set_axisbelow(True)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        fig.tight_layout()
        fig.savefig(GRAFICAS / archivo, bbox_inches="tight")
        plt.close(fig)
        salidas.append(archivo)

    a, b = flujos["flujo_a"], flujos["flujo_b"]
    barras_top10(a, f"Flujo A · las 10 rutas de la mudanza 2013 → 2021 "
                    f"({miles(a['movimientos'])} personas en {a['rutas']} rutas)",
                 "flujos_top10_mudanzas.png", metro=True)
    barras_top10(b, "Flujo B · las 10 rutas del nacimiento a la residencia "
                    f"({miles(b['movimientos'])} casos en {b['rutas']} rutas)",
                 "flujos_top10_fuera_de_cuna.png", metro=False)

    # saldo neto (mismo calculo que la figura interactiva, en version estatica)
    rutas = a["rutas_detalle"]
    entra, sale = Counter(), Counter()
    for r in rutas:
        entra[r["destino"]] += r["personas"]
        sale[r["origen"]] += r["personas"]
    deps = sorted(set(entra) | set(sale), key=lambda d: (entra[d] - sale[d], d))
    neto = [entra[d] - sale[d] for d in deps]
    if sum(neto) != 0:
        raise SystemExit(f"La suma de los saldos no es 0: {sum(neto)}")
    fig2, ax = plt.subplots(figsize=(7.4, 5.6), dpi=190)
    ax.barh([_corto(d) for d in deps], neto, height=0.68,
            color=[PALETA["primario"] if v > 0 else PALETA["claro"] for v in neto])
    ax.axvline(0, color=PALETA["gris_oscuro"], linewidth=1)
    for i, v in enumerate(neto):
        ax.text(v + (0.9 if v >= 0 else -0.9), i, _menos(v), va="center",
                ha="left" if v >= 0 else "right", fontsize=7.8,
                color=PALETA["gris_oscuro"])
    ax.set_xlim(min(neto) * 1.25, max(neto) * 1.25)
    ax.set_xlabel("Saldo neto (entradas − salidas) de las 808 mudanzas")
    ax.set_title("Quién gana y quién pierde: saldo neto por departamento, 2013 → 2021",
                 loc="left", fontsize=10.5, color=PALETA["primario_oscuro"])
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="x", color=PALETA["gris_claro"], linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig2.tight_layout()
    fig2.savefig(GRAFICAS / "flujos_saldo_neto.png", bbox_inches="tight")
    plt.close(fig2)
    salidas.append("flujos_saldo_neto.png")
    return salidas


# ============================================================================
# 8. Puntos de entrada para el panel (misma figura, sin duplicarla)
# ============================================================================
def construir_mapa() -> go.Figure:
    """Figura del mapa, lista para embeber en el panel o en la pagina suelta."""
    gj = cargar_geojson()
    per = cargar_percapita()
    flujos = cargar_flujos()
    cent, _ = centroides(gj)
    tabla = tabla_departamentos(gj, per, flujos["flujo_a"], cent)
    return figura_mapa(tabla, gj, flujos, cent)


def construir_saldo_neto() -> go.Figure:
    return figura_saldo_neto(cargar_flujos()["flujo_a"])


# ============================================================================
# 9. Main
# ============================================================================
def main() -> int:
    registrar_template()
    print("== Fuentes ==")
    gj = cargar_geojson()
    per = cargar_percapita()
    flujos = cargar_flujos()
    print(f"   {len(gj['features'])} polígonos · {len(per['tasa_por_100000']['stock_ultima_convocatoria'])} "
          f"departamentos con tasa · flujos A {flujos['flujo_a']['movimientos']} y "
          f"B {flujos['flujo_b']['movimientos']}")

    print("\n== Centroides ==")
    cent, n_respaldo = centroides(gj)
    print(f"   33 centroides dentro de su polígono ({n_respaldo} por rejilla de respaldo)")

    print("\n== Tabla de departamentos ==")
    tabla = tabla_departamentos(gj, per, flujos["flujo_a"], cent)
    print(f"   burbujas suman {miles(sum(t['investigadores'] for t in tabla))} "
          f"= stock de F2-2")

    print("\n== Figura ==")
    fig_mapa = figura_mapa(tabla, gj, flujos, cent)
    print(f"   {len(fig_mapa.data)} trazas · geo con fitbounds y sin fondo externo")
    fig_saldo = figura_saldo_neto(flujos["flujo_a"])

    print("\n== Página autocontenida ==")
    doc = documento_html(fig_mapa, fig_saldo, flujos, per)
    SALIDA.write_text(doc, encoding="utf-8", newline="\n")
    peso = SALIDA.stat().st_size
    print(f"   {SALIDA.relative_to(RAIZ)}")
    print(f"   peso: {peso:,} B = {peso / 1024 / 1024:.2f} MiB "
          f"({peso / 1e6:.2f} MB decimales)")

    print("\n== Figuras estáticas ==")
    for nombre in figuras_estaticas(flujos):
        ruta = GRAFICAS / nombre
        print(f"   {ruta.relative_to(RAIZ)} · {ruta.stat().st_size:,} B")
    faltan = set(flujos["figuras"]) - {p.name for p in GRAFICAS.iterdir()}
    if faltan:
        raise SystemExit(f"El JSON declara figuras que no se generaron: {faltan}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
