# -*- coding: utf-8 -*-
"""
verificar_mapa.py
=================

Comprueba que el mapa de la F2-11 (`02_dashboards/mapa_migracion.html`) y sus
insumos cumplen lo que prometen:

  1. **Autocontenido y peso**: sin una sola referencia externa y por debajo de 6 MB.
  2. **GeoJSON**: 33 features, los 33 códigos DIVIPOLA del DANE, sin propiedades
     sobrantes, anillos cerrados, coordenadas dentro de Colombia y el SHA-256 que
     declara su `.procedencia.txt`.
  3. **Flujos**: los números del JSON cierran (rutas que suman movimientos, top 10
     que suma, saldo neto que suma cero) y coinciden con los auditados.
  4. **Figura**: un solo Choropleth con los 33 polígonos embebidos, burbujas que
     suman el stock de F2-2, rutas de las dos definiciones, hover con la tasa per
     cápita y con la información del flujo, y las rutas metropolitanas marcadas.
  5. **La misma figura en el panel**: la pestaña 8 de `dashboard_fase2.html` dibuja
     exactamente las mismas trazas que la página suelta (no una copia recortada).
  6. **Centroides**: cada burbuja cae dentro de su polígono.
  7. **Figuras estáticas y notas**: las tres PNG que declara el JSON existen y la
     nota de área metropolitana está en el texto.

Uso:  python verificar_mapa.py   (sale con 1 si algo falla)
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
MEM = DOC / "data" / "memoria"
RESULTADOS = RAIZ / "01_datos" / "resultados_json"
DASH = RAIZ / "02_dashboards"
GEO = DOC / "data" / "geo" / "colombia_departamentos.geojson"
PROCEDENCIA = DOC / "data" / "geo" / "colombia_departamentos.procedencia.txt"
DANE = (RAIZ / "01_datos" / "datos_fuente"
        / "dane_cnpv2018_poblacion_departamental.csv")
HTML = DASH / "mapa_migracion.html"
PANEL = DASH / "dashboard_fase2.html"
FLUJOS = RESULTADOS / "flujos_territoriales.json"
PERCAPITA = RESULTADOS / "percapita_territorial.json"
GRAFICAS = MEM / "graficas_flujos"
LIMITE_BYTES = 6_000_000

fallos: list[str] = []
avisos: list[str] = []


def check(cond: bool, ok: str, mal: str) -> None:
    if cond:
        print(f"  [OK ] {ok}")
    else:
        print(f"  [MAL] {mal}")
        fallos.append(mal)


def separar_bundle(texto: str) -> tuple[str, str]:
    """Separa el bundle de Plotly del markup propio (el bundle trae cadenas que
    parecen enlaces: el logo de plotly.com y la atribución de ESRI)."""
    ini = texto.find("<script>")
    fin = texto.find("</script>", ini)
    if ini < 0 or fin < 0:
        return "", texto
    return texto[ini:fin + 9], texto[:ini] + texto[fin + 9:]


def trazas_de(texto: str, ident: str) -> list[dict]:
    dec = json.JSONDecoder()
    for m in re.finditer(rf'Plotly\.newPlot\(\s*"{re.escape(ident)}"\s*,\s*', texto):
        _, fin = dec.raw_decode(texto, m.end())
        return json.loads(texto[m.end():fin])
    return []


def main() -> int:
    for ruta in (HTML, GEO, PROCEDENCIA, FLUJOS, PANEL):
        if not ruta.exists():
            print(f"[ABORTA] no existe {ruta}")
            return 1

    crudo = HTML.read_text(encoding="utf-8")
    peso = HTML.stat().st_size
    bundle, propio = separar_bundle(crudo)
    texto = propio.replace("\u202f", " ")
    gj = json.loads(GEO.read_text(encoding="utf-8"))
    flujos = json.loads(FLUJOS.read_text(encoding="utf-8"))
    per = json.loads(PERCAPITA.read_text(encoding="utf-8"))
    fa, fb = flujos["flujo_a"], flujos["flujo_b"]

    print("== 1. Peso y autocontención ==")
    check(peso < LIMITE_BYTES,
          f"peso {peso / 1e6:.2f} MB ({peso / 1024 / 1024:.2f} MiB, {peso:,} B) < 6 MB",
          f"peso {peso / 1e6:.2f} MB supera el límite de 6 MB")
    externas = []
    for patron in (r'src\s*=\s*["\']https?:', r'href\s*=\s*["\']https?:',
                   r'src\s*=\s*["\']//', r'@import', r'url\(\s*["\']?https?:',
                   r'cdn\.', r'unpkg\.', r'jsdelivr', r'cdnjs'):
        externas += [texto[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
                     for m in re.finditer(patron, texto, re.IGNORECASE)]
    check(not externas, "sin referencias externas: el mapa se abre sin internet",
          f"{len(externas)} referencias externas: {externas[:3]}")
    check(len(bundle) > 1_000_000,
          f"Plotly embebido en el archivo ({len(bundle) / 1024 / 1024:.2f} MiB)",
          "no se encontró el bundle de Plotly embebido")
    check((DASH / "mapa_migracion.html").name in str(HTML) and
          "open-street-map" not in texto and "mapbox" not in texto.lower(),
          "no hay teselas ni mapbox: el país lo dibujan los polígonos del GeoJSON",
          "el mapa menciona mapbox/OpenStreetMap: volvería a depender de la red")

    print("\n== 2. GeoJSON ==")
    feats = gj["features"]
    check(gj["type"] == "FeatureCollection" and len(feats) == 33,
          f"FeatureCollection con {len(feats)} departamentos",
          f"el GeoJSON trae {len(feats)} features")
    codigos_gj = sorted(f["properties"]["codigo_dane"] for f in feats)
    with DANE.open(encoding="utf-8", newline="") as fh:
        import csv
        codigos_dane = sorted(r["codigo_dane"].strip() for r in csv.DictReader(fh))
    check(codigos_gj == codigos_dane,
          "los 33 códigos DIVIPOLA coinciden 33 de 33 con el CSV del DANE de F2-2",
          f"códigos distintos: GeoJSON {codigos_gj[:5]}… frente a DANE {codigos_dane[:5]}…")
    props = {tuple(sorted(f["properties"])) for f in feats}
    check(props == {("codigo_dane", "nombre")},
          "cada feature lleva solo codigo_dane y nombre (sin AREA ni HECTARES)",
          f"propiedades inesperadas: {props}")
    n_anillos = n_mal = 0
    fuera = []
    for f in feats:
        g = f["geometry"]
        polis = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for anillo in polis:
            n_anillos += 1
            if anillo[0] != anillo[-1]:
                n_mal += 1
            for lon, lat in anillo[0]:
                if not (-82.0 <= lon <= -66.0 and -5.0 <= lat <= 14.0):
                    fuera.append((f["properties"]["codigo_dane"], lon, lat))
                    break
    check(n_mal == 0, f"{n_anillos} anillos cerrados (primer punto = último)",
          f"{n_mal} anillos sin cerrar")
    check(not fuera, "todas las coordenadas caen en el rectángulo de Colombia",
          f"coordenadas fuera de Colombia: {fuera[:3]}")
    proc = PROCEDENCIA.read_text(encoding="utf-8")
    sha_declarado = re.search(r"SHA-256 del archivo versionado:\s*([0-9A-F]{64})", proc)
    sha_real = hashlib.sha256(GEO.read_bytes()).hexdigest().upper()
    check(sha_declarado is not None and sha_declarado.group(1) == sha_real,
          f"el procedencia.txt declara el SHA-256 del geojson versionado ({sha_real[:12]}…)",
          "el SHA-256 del geojson no coincide con el que declara su procedencia")
    check("gist.githubusercontent.com/john-guerra" in proc and "DIVIPOLA" in proc,
          "el procedencia.txt declara fuente, URL, fecha y criterio de limpieza",
          "el procedencia.txt no declara la fuente o la URL")

    print("\n== 3. Flujos ==")
    val = flujos["validaciones"]
    check(all(v for v in val.values()), f"las {len(val)} validaciones del JSON pasan",
          f"validaciones en falso: {[k for k, v in val.items() if not v]}")
    check(fa["personas_2_mas_convocatorias"] == 19215 and fa["comparables"] == 18430,
          "A: 19 215 personas con 2+ convocatorias y 18 430 comparables",
          f"A: {fa['personas_2_mas_convocatorias']} con 2+ y {fa['comparables']} comparables")
    check(fa["movimientos"] == 808 and fa["rutas"] == 231,
          "A: 808 mudanzas en 231 rutas (los números auditados)",
          f"A: {fa['movimientos']} mudanzas en {fa['rutas']} rutas")
    check(abs(fa["pct_de_comparables"] - 100 * 808 / 18430) < 0.01,
          f"A: el {fa['pct_de_comparables']:.2f} % de las comparables se mudó",
          "el porcentaje de A no cuadra con 808/18 430")
    check(sum(r["personas"] for r in fa["rutas_detalle"]) == fa["movimientos"],
          "A: las 231 rutas suman exactamente las 808 personas",
          "las rutas de A no suman los movimientos")
    check(sum(r["personas"] for r in fa["top10"]) == fa["personas_top10"]
          and abs(100 * fa["personas_top10"] / fa["movimientos"]
                  - fa["pct_movimientos_top10"]) < 0.01,
          f"A: el top 10 suma {fa['personas_top10']} personas "
          f"({fa['pct_movimientos_top10']:.2f} %)",
          "el top 10 de A no cuadra con su total")
    check(sum(fa["saldo_neto"].values()) == 0,
          "A: el saldo neto de todos los departamentos suma cero",
          "el saldo neto no suma cero")
    check(fa["rutas_con_mismo_municipio"] == 0,
          "A: las 808 personas cambian también de municipio (0 conservan el mismo)",
          "hay personas que cambian de departamento sin cambiar de municipio")
    metro = fa["area_metropolitana"]
    check(metro["movimientos"] == 53 and metro["rutas"] == 2,
          "A: 53 de las 808 mudanzas son de área metropolitana (Bogotá ↔ Cundinamarca)",
          f"A: el área metropolitana suma {metro['movimientos']} en {metro['rutas']} rutas")
    parejas_metro = {("11", "25"), ("25", "11")}
    check(all(bool(r["area_metropolitana"]) ==
              ((r["origen_codigo"], r["destino_codigo"]) in parejas_metro)
              for r in fa["rutas_detalle"]),
          "la marca de área metropolitana solo la llevan las rutas Bogotá ↔ Cundinamarca",
          "hay rutas marcadas como metropolitanas fuera de Bogotá ↔ Cundinamarca")
    check(fb["movimientos"] == 11922 and fb["rutas"] == 577 and fb["comparables"] == 28673,
          "B: 11 922 de 28 673 personas residen fuera de su cuna, en 577 rutas",
          f"B: {fb['movimientos']}/{fb['comparables']} en {fb['rutas']} rutas")
    check(sum(r["personas"] for r in fb["rutas_detalle"]) == fb["movimientos"],
          "B: las 577 rutas suman los 11 922 casos",
          "las rutas de B no suman los casos")
    check(fb["personas_no_dibujables"] == 1402
          and fb["rutas_no_dibujables"] == 25,
          "B: 1 402 personas (25 rutas) nacieron fuera de Colombia y no se dibujan",
          f"B: {fb['personas_no_dibujables']} personas no dibujables en "
          f"{fb['rutas_no_dibujables']} rutas")

    print("\n== 4. La figura ==")
    trazas = trazas_de(texto, "mapa-migracion")
    check(len(trazas) >= 9, f"{len(trazas)} trazas en el mapa",
          f"solo {len(trazas)} trazas en el mapa")
    choro = [t for t in trazas if t.get("type") == "choropleth"]
    geo = [t for t in trazas if t.get("type") == "scattergeo"]
    check(len(choro) == 1, "un solo Choropleth con los polígonos",
          f"{len(choro)} choropleths")
    cp = choro[0] if choro else {}
    geo_inc = cp.get("geojson") or {}
    check(len(geo_inc.get("features", [])) == 33,
          "el mapa embebe los 33 polígonos (no los pide a la red)",
          "el mapa no embebe los 33 polígonos")
    check(cp.get("featureidkey") == "properties.codigo_dane",
          "la unión es por codigo_dane (nunca por nombre)",
          f"featureidkey = {cp.get('featureidkey')!r}")
    check(len(cp.get("locations", [])) == 33 and len(cp.get("z", [])) == 33,
          "colorea los 33 departamentos",
          "no colorea los 33 departamentos")
    # el polígono dibujado es exactamente el del archivo versionado
    geom_dib = {f["properties"]["codigo_dane"]: f["geometry"]
                for f in geo_inc.get("features", [])}
    geom_arch = {f["properties"]["codigo_dane"]: f["geometry"] for f in feats}
    check(geom_dib == geom_arch,
          "las geometrías dibujadas son idénticas a las del geojson versionado",
          "las geometrías embebidas difieren del archivo versionado")
    check("Tasa per cápita" in (cp.get("hovertemplate") or "")
          and "investigadores" in (cp.get("hovertemplate") or ""),
          "el hover del polígono da la tasa per cápita y los investigadores de F2-2",
          "el hover del polígono no da la tasa per cápita de F2-2")
    burbujas = [t for t in geo if t.get("mode") == "markers"
                and len(t.get("lon") or []) == 33]
    check(len(burbujas) == 1, "33 burbujas, una por departamento",
          f"{len(burbujas)} trazas de 33 burbujas")
    if burbujas:
        b = burbujas[0]
        check(sum(1 for x in (b.get("customdata") or [])) == 33,
              "cada burbuja lleva su tasa, sus habitantes y su puesto en el tooltip",
              "faltan datos por burbuja en el tooltip")
    textos = " ".join(str(t.get("text")) for t in geo if t.get("text"))
    check("→" in textos and "personas" in textos,
          "el hover de las rutas dice origen → destino y cuántas personas",
          "el hover de las rutas no da la información del flujo")
    check(any((t.get("line") or {}).get("dash") == "dot" for t in geo),
          "las rutas de área metropolitana van con trazo punteado (D2)",
          "no hay trazo punteado para las rutas metropolitanas")
    check(any("diamond" in [str(s) for s in ((t.get("marker") or {}).get("symbol") or [])]
              for t in geo),
          "el destino metropolitano va con rombo (D2)",
          "no hay rombo en el destino metropolitano")
    destinos = sorted(len(t.get("lon") or []) for t in geo
                      if t.get("mode") == "markers" and len(t.get("lon") or []) != 33)
    check(destinos == [2, 8, 10],
          "10 destinos del flujo A (8 interdepartamentales + 2 metropolitanos) y 10 del B",
          f"destinos marcados: {destinos} y se esperaban [2, 8, 10]")
    check('"updatemenus"' in propio.replace(" ", "") and "Flujo A" in propio
          and "Flujo B" in propio,
          "el mapa trae los dos botones de flujo (A por defecto, B secundario)",
          "el mapa no trae los dos botones de flujo")
    check('"visible":false' in propio.replace(" ", ""),
          "el flujo B arranca oculto: la vista por defecto es A (D1)",
          "no se puede comprobar que el flujo B arranque oculto")

    print("\n== 5. La misma figura en el panel (pestaña 8) ==")
    panel = PANEL.read_text(encoding="utf-8")
    _, propio_panel = separar_bundle(panel)
    propio_panel = propio_panel.replace("\u202f", " ")
    trazas_panel = trazas_de(propio_panel, "t17")
    check(bool(trazas_panel), "la pestaña 8 del panel tiene el mapa",
          "la pestaña 8 no tiene el mapa")
    check(json.dumps(trazas, sort_keys=True) == json.dumps(trazas_panel, sort_keys=True),
          "la pestaña 8 dibuja EXACTAMENTE las mismas trazas que la página suelta",
          "la figura de la página suelta y la de la pestaña 8 difieren")
    check("t18" in propio_panel and "saldo" in propio_panel.lower(),
          "la pestaña 8 trae además el saldo neto por departamento",
          "la pestaña 8 no trae el saldo neto")

    print("\n== 6. Centroides dentro de su polígono ==")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import mapa_migracion as mm
        cent, n_respaldo = mm.centroides(gj)
        dentro = sum(1 for cod, (lat, lon) in cent.items()
                     if mm._punto_en_geometria((lon, lat),
                                               {f["properties"]["codigo_dane"]: f["geometry"]
                                                for f in feats}[cod]))
        check(dentro == 33, f"los 33 centroides caen dentro de su polígono "
                            f"({n_respaldo} por rejilla de respaldo)",
              f"solo {dentro} centroides caen dentro de su polígono")
        per2 = json.loads(PERCAPITA.read_text(encoding="utf-8"))
        stock = per2["conteos"]["stock_personas"]
        check(stock == 28950, f"el stock de F2-2 es {stock} personas",
              f"el stock de F2-2 cambió: {stock}")
    except SystemExit as exc:                                   # noqa: PERF203
        check(False, "", f"no se pudieron calcular los centroides: {exc}")

    print("\n== 7. Figuras estáticas y notas ==")
    check(len(flujos["figuras"]) == 3,
          f"el JSON declara sus 3 figuras: {', '.join(flujos['figuras'])}",
          f"el JSON declara {len(flujos['figuras'])} figuras y se esperaban 3")
    for nombre in flujos["figuras"]:
        ruta = GRAFICAS / nombre
        check(ruta.exists() and ruta.stat().st_size > 40_000,
              f"{nombre} ({ruta.stat().st_size:,} B)" if ruta.exists() else nombre,
              f"falta la figura {nombre}")
    nota = "una mudanza de Bogotá a Chía se ve igual que una migración de Antioquia a Bogotá"
    check(nota in texto,
          "la nota de área metropolitana está en el texto del mapa (D1/D2)",
          "falta la nota que advierte de la ambigüedad del mapa departamental")
    for cifra in ("808", "4,38 %", "231", "18 430", "11 922", "41,58 %",
                  "28 950", "65,55", "Chía", "Cajicá", "Exterior"):
        check(cifra in texto, f"la cifra «{cifra}» está en el texto",
              f"falta la cifra «{cifra}» en el texto del mapa")
    for archivo in (GEO, PROCEDENCIA, FLUJOS, GRAFICAS):
        check(archivo.exists(), f"{archivo.relative_to(RAIZ)} versionado",
              f"falta {archivo.relative_to(RAIZ)}")

    print("\n" + "=" * 60)
    for a in avisos:
        print(f"  [AVISO] {a}")
    if fallos:
        print(f"  {len(fallos)} FALLO(S)")
        return 1
    print(f"  Todo correcto · mapa de {peso / 1e6:.2f} MB con las dos definiciones de "
          f"flujo y las 33 geometrías")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
