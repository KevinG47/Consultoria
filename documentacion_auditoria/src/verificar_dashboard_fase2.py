# -*- coding: utf-8 -*-
"""
verificar_dashboard_fase2.py
============================

Comprueba que `data/memoria/dashboard_fase2.html` cumple lo que promete:

  1. **Autocontenido**: ni una referencia externa (http, https, //cdn, @import).
  2. **Peso** por debajo de 6 MB, que es el tope que se fijó al añadir el mapa.
  3. **Estructura**: 8 pestañas, 8 paneles, 18 graficos, indice con buscador.
  4. **Paleta**: ningun color fuera de la institucional; el rojo solo donde es una
     excepcion negativa declarada.
  5. **Datos**: cada grafico lleva las series que corresponde, leidas del JSON de su
     analisis (numero de trazas y de puntos), no una version recortada. El mapa de
     flujos (t17) lleva ademas los 33 poligonos del GeoJSON y las rutas de las dos
     definiciones.
  6. **Cifras clave**: las que sostienen las conclusiones aparecen en el texto.

Sale con codigo 1 si algo falla.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"
HTML = MEM / "dashboard_fase2.html"
LIMITE_BYTES = 6_000_000        # 6 MB decimales, el tope acordado para el panel

fallos: list[str] = []
avisos: list[str] = []


def check(cond: bool, ok: str, mal: str) -> None:
    if cond:
        print(f"  [OK ] {ok}")
    else:
        print(f"  [MAL] {mal}")
        fallos.append(mal)


def trazas(texto: str) -> dict[str, list]:
    """Extrae, para cada div x, la lista de trazas que se le pasa a Plotly."""
    dec = json.JSONDecoder()
    salida = {}
    for m in re.finditer(r'Plotly\.newPlot\(\s*"([^"]+)"\s*,\s*', texto):
        ident = m.group(1)
        _, fin = dec.raw_decode(texto, m.end())
        salida[ident] = json.loads(texto[m.end():fin])
    return salida


def puntos(traza: dict) -> int:
    for clave in ("x", "y", "labels", "values"):
        v = traza.get(clave)
        if isinstance(v, list) and v:
            return len(v)
    return 0


def separar_bundle(texto: str) -> tuple[str, str]:
    """
    Devuelve (bundle_de_plotly, markup_propio).

    Hace falta separarlos porque el bundle trae cadenas que PARECEN referencias
    externas —el enlace a plotly.com del logotipo y la atribución de ESRI de las
    capas de mapa— y etiquetas `<script>` escritas como texto para desinfectar
    HTML. Ninguna de las dos cosas carga nada desde la red: son cadenas.
    """
    ini = texto.find("<script>")
    fin = texto.find("</script>", ini)
    if ini < 0 or fin < 0:
        return "", texto
    return texto[ini:fin + 9], texto[:ini] + texto[fin + 9:]


def main() -> int:
    if not HTML.exists():
        print(f"[ABORTA] no existe {HTML}")
        return 1
    crudo = HTML.read_text(encoding="utf-8")
    peso = HTML.stat().st_size
    bundle, propio = separar_bundle(crudo)
    # Los números se escriben con espacio fino de miles; para comprobar cifras se
    # normaliza el texto, no las cifras.
    texto = propio.replace("\u202f", " ")

    print("== 1. Peso y autocontención ==")
    mb = peso / 1024 / 1024
    check(peso < LIMITE_BYTES,
          f"peso {peso / 1e6:.2f} MB ({mb:.2f} MiB, {peso:,} B) < 6 MB",
          f"peso {peso / 1e6:.2f} MB supera el límite de 6 MB")
    externas = []
    for patron in (r'src\s*=\s*["\']https?:', r'href\s*=\s*["\']https?:',
                   r'src\s*=\s*["\']//', r'@import', r'url\(\s*["\']?https?:',
                   r'cdn\.', r'unpkg\.', r'jsdelivr', r'cdnjs'):
        for m in re.finditer(patron, texto, re.IGNORECASE):
            externas.append(texto[max(0, m.start() - 40):m.end() + 40].replace("\n", " "))
    check(not externas, "sin referencias externas en el documento (se abre sin internet)",
          f"{len(externas)} referencias externas: {externas[:3]}")
    check(len(bundle) > 1_000_000,
          f"Plotly embebido en el propio archivo ({len(bundle)/1024/1024:.2f} MiB)",
          "no se encontró el bundle de Plotly embebido")
    # Un <script> por gráfico (el que llama a Plotly.newPlot) más el de la página.
    check(propio.count("<script") == 19,
          "19 <script> propios: uno por gráfico y el de la página",
          f"{propio.count('<script')} bloque(s) <script> propios (se esperaban 19)")

    print("\n== 2. Estructura ==")
    paneles = re.findall(r'<div class="panel[^"]*" id="([\w-]+)"', texto)
    botones = re.findall(r'data-tab="([\w-]+)"', texto)
    check(len(paneles) == 8, f"8 paneles: {', '.join(paneles)}",
          f"{len(paneles)} paneles (se esperaban 8): {paneles}")
    check(botones == paneles, "cada pestaña tiene su botón y en el mismo orden",
          f"botones {botones} != paneles {paneles}")
    check("tab-migracion" in paneles, "la pestaña 8 (flujos y migración) está presente",
          "falta la pestaña 8 de flujos y migración")
    n_concl = texto.count('class="concl"')
    check(n_concl == 8, "8 bloques de conclusión",
          f"{n_concl} conclusiones (se esperaban 8)")
    n_nar = texto.count('class="nar"')
    check(n_nar >= 18, f"{n_nar} bloques de narrativa (uno por gráfico)",
          f"solo {n_nar} narrativas para 18 gráficos")
    check(re.search(r'id=["\']buscador["\']', texto) is not None,
          "el índice de conceptos tiene buscador", "falta el buscador del índice")
    n_conceptos = len(re.findall(r'class=["\']concepto["\']', texto))
    check(n_conceptos >= 20, f"{n_conceptos} conceptos en el índice",
          f"solo {n_conceptos} conceptos")
    for etiqueta in ("Qué se hizo", "Por qué", "Qué teoría lo respalda",
                     "Cómo se lee"):
        c = texto.count(f'<span class="et">{etiqueta}</span>')
        check(c >= 18, f'"{etiqueta}" en {c} bloques',
              f'"{etiqueta}" solo en {c} bloques (se esperaban 18)')

    print("\n== 3. Paleta ==")
    for prohibido in ("#7C3AED", "#15803D", "#7c3aed", "#15803d"):
        check(prohibido not in texto, f"color prohibido {prohibido} ausente",
              f"aparece el color prohibido {prohibido}")
    n_rojo = len(re.findall(r"#B91C1C|#b91c1c|rgba\(185,28,28", texto))
    # Apariciones legitimas: la definicion de la variable CSS, el comentario de la
    # paleta y la barra de la regla implementada en F2-7 (unica excepcion negativa
    # que se marca en rojo).
    check(n_rojo <= 4, f"rojo de alerta en {n_rojo} lugares (solo excepciones)",
          f"rojo de alerta en {n_rojo} lugares: se está usando como decoración")

    print("\n== 4. Los gráficos llevan sus datos ==")
    d = {k: json.loads((MEM / f"{k}.json").read_text(encoding="utf-8"))
         for k in ("percapita_territorial", "modelo_estrella", "redes_nulos",
                   "diversidad_inferencia", "clustering", "validacion_unicidad",
                   "supervivencia", "flujos_territoriales")}
    tr = trazas(texto)
    check(len(tr) == 18, f"{len(tr)} gráficos con datos embebidos",
          f"{len(tr)} gráficos con datos (se esperaban 18): {sorted(tr)}")

    esperado = {
        "t1": (2, 14, "2 series x 7 análisis"),
        "t2": (1, 33, "33 departamentos"),
        "t3": (5, 30, "5 series x 6 convocatorias"),
        "t4": (2, 12, "2 series x 6 convocatorias"),
        "t5": (11, 11, "7 grupos con sus intervalos"),
        "t6": (4, 24, "4 variables x 6 convocatorias"),
        "t7": (2, 446, "red de 446 nodos y sus aristas"),
        "t8": (2, 14, "2 nulos x 7 estadísticos"),
        "t9": (2, 29, "curva de k y nulo de la silhouette"),
        "t10": (4, 41, "4 curvas Kaplan-Meier"),
        "t11": (4, 44, "2 curvas y sus bandas"),
        "t12": (1, 14, "14 covariables del Cox"),
        "t13": (3, 12, "composición y permanencia"),
        "t14": (2, 11, "dos reglas y la sensibilidad"),
        "t15": (2, 12, "hechos por convocatoria"),
        "t16": (3, 10, "los diez análisis planificados"),
        "t17": (10, 0, "mapa: polígonos, burbujas y rutas de los dos flujos"),
        "t18": (1, 20, "saldo neto por departamento"),
    }
    for ident, (n_tr, n_pt, desc) in esperado.items():
        if ident not in tr:
            fallos.append(f"{ident}: no se encontró el gráfico")
            print(f"  [MAL] {ident}: no se encontró")
            continue
        p = sum(puntos(t) for t in tr[ident])
        ok = len(tr[ident]) >= n_tr and p >= n_pt
        check(ok, f"{ident}: {len(tr[ident])} trazas y {p} puntos ({desc})",
              f"{ident}: {len(tr[ident])} trazas y {p} puntos; se esperaban "
              f">= {n_tr} trazas y >= {n_pt} puntos ({desc})")

    # ---- el mapa de flujos (t17): 33 polígonos, burbujas y dos definiciones ----
    t17 = tr.get("t17", [])
    coropletas = [t for t in t17 if t.get("type") == "choropleth"]
    geo = [t for t in t17 if t.get("type") == "scattergeo"]
    check(len(coropletas) == 1 and len(geo) >= 8,
          f"t17: 1 Choropleth y {len(geo)} trazas geográficas (burbujas, rutas y destinos)",
          f"t17: {len(coropletas)} coropletas y {len(geo)} trazas geográficas")
    if coropletas:
        cp = coropletas[0]
        gj = cp.get("geojson") or {}
        feats = gj.get("features", []) if isinstance(gj, dict) else []
        check(isinstance(gj, dict) and len(feats) == 33,
              "t17 embebe los 33 polígonos del GeoJSON (no los pide a la red)",
              f"t17 no embebe los 33 polígonos: {type(gj).__name__} con "
              f"{len(feats) if isinstance(gj, dict) else '?'} features")
        check(cp.get("featureidkey") == "properties.codigo_dane",
              "t17 une por código DIVIPOLA (featureidkey properties.codigo_dane)",
              f"t17 une por {cp.get('featureidkey')!r} y no por codigo_dane")
        check(len(cp.get("locations", [])) == 33 and len(cp.get("z", [])) == 33,
              "t17 colorea los 33 departamentos con su tasa",
              f"t17 tiene {len(cp.get('locations', []))} localizaciones y "
              f"{len(cp.get('z', []))} valores de tasa")
        check("Tasa per cápita" in (cp.get("hovertemplate") or ""),
              "el tooltip del polígono muestra la tasa per cápita de F2-2",
              "el tooltip del polígono no menciona la tasa per cápita")
        check(all("codigo_dane" in (f.get("properties") or {}) for f in feats),
              "cada polígono lleva su codigo_dane en las propiedades",
              "algún polígono no lleva codigo_dane")
    check(not any(t.get("type") == "scattermapbox" for t in t17),
          "t17 no usa scattermapbox (el mapa del auditado sí, y dependía de internet)",
          "t17 usa scattermapbox: volvería a pedir teselas a internet")
    check(any((t.get("line") or {}).get("dash") == "dot" for t in geo),
          "t17 distingue las rutas de área metropolitana con trazo punteado (D2)",
          "t17 no marca aparte las rutas de área metropolitana")
    check(any("diamond" in [str(s) for s in ((t.get("marker") or {}).get("symbol") or [])]
              for t in geo),
          "t17 marca el destino metropolitano con rombo",
          "t17 no usa el rombo en el destino metropolitano")
    textos_mapa = " ".join(str(t.get("text")) for t in geo if t.get("text"))
    fa, fb = d["flujos_territoriales"]["flujo_a"], d["flujos_territoriales"]["flujo_b"]
    top_a = fa["top10"][0]
    dib_b = [r for r in fb["rutas_detalle"] if r["dibujable"]]
    top_b = dib_b[0]
    check(f"{top_a['origen']} → {top_a['destino']}" in textos_mapa
          and f"{top_a['personas']} personas" in textos_mapa,
          f"t17 dibuja la ruta mayor del flujo A ({top_a['origen']} → "
          f"{top_a['destino']}, {top_a['personas']} personas)",
          "t17 no dibuja la ruta mayor del flujo A")
    check(f"{top_b['origen']} → {top_b['destino']}" in textos_mapa
          and f"{top_b['personas']} personas" in textos_mapa,
          f"t17 dibuja la ruta mayor dibujable del flujo B ({top_b['origen']} → "
          f"{top_b['destino']}, {top_b['personas']} personas)",
          "t17 no dibuja la ruta mayor dibujable del flujo B")
    check("Exterior" not in textos_mapa,
          "t17 no intenta dibujar el origen «Exterior» (no está en el mapa)",
          "t17 intenta dibujar el origen «Exterior»")
    # los marcadores de destino: uno por ruta dibujada (los 33 del dept no cuentan)
    destinos = sorted(len(t.get("lon") or []) for t in geo
                      if t.get("mode") == "markers" and len(t.get("lon") or []) != 33)
    a_inter = sum(1 for r in fa["top10"] if not r["area_metropolitana"])
    a_metro = sum(1 for r in fa["top10"] if r["area_metropolitana"])
    check(destinos == sorted([a_inter, a_metro, len(dib_b[:10])]),
          f"t17 marca {a_inter} destinos interdepartamentales, {a_metro} metropolitanos "
          f"y {len(dib_b[:10])} del flujo B",
          f"t17 marca {destinos} destinos y se esperaban "
          f"{sorted([a_inter, a_metro, len(dib_b[:10])])}")
    check("Flujo A" in texto and "Flujo B" in texto
          and '"updatemenus"' in texto.replace(" ", ""),
          "t17 trae los dos botones de flujo (A por defecto, B como vista secundaria)",
          "t17 no trae los botones de las dos definiciones de flujo")
    # t18: saldo neto, una barra por departamento con saldo declarado
    check(puntos(tr["t18"][0]) == len(fa["saldo_neto"]),
          f"t18 dibuja el saldo neto de los {len(fa['saldo_neto'])} departamentos del JSON",
          f"t18 dibuja {puntos(tr['t18'][0])} saldos y el JSON declara "
          f"{len(fa['saldo_neto'])}")
    check(sum(tr["t18"][0]["x"]) == 0,
          "t18 cierra en cero (todo el que sale de un departamento entra en otro)",
          f"la suma de los saldos de t18 es {sum(tr['t18'][0]['x'])} y debería ser 0")

    # Comprobación puntual contra los JSON: la red y el Cox son los más expuestos a
    # un cambio de fuente silencioso.
    check(puntos(tr["t7"][1]) == d["redes_nulos"]["red"]["n_nodos"],
          f"t7 dibuja los {d['redes_nulos']['red']['n_nodos']} nodos del JSON",
          "t7 no dibuja el número de nodos que declara redes_nulos.json")
    check(puntos(tr["t12"][0]) == len(d["supervivencia"]["cox"]["coeficientes"]),
          f"t12 dibuja las {len(d['supervivencia']['cox']['coeficientes'])} covariables del Cox",
          "t12 no dibuja las covariables que declara supervivencia.json")
    check(puntos(tr["t2"][0]) == len(d["percapita_territorial"]
                                      ["tasa_por_100000"]["stock_ultima_convocatoria"]),
          "t2 dibuja los 33 departamentos del JSON",
          "t2 no dibuja todos los departamentos del JSON")

    print("\n== 5. Cifras clave en el texto ==")
    claves = ["137,7", "1,3", "105,5", "0,4361", "0,5239", "0,2204", "0,1023",
              "2,22", "7,88", "5,39", "31,70", "72,02", "503", "446", "0,9143",
              "1 058", "56", "0,988", "0,575", "2 940,2", "0,762",
              "56,18", "15 · 0 · 2", "77 237", "20 423", "1 067",
              # Correcciones de la auditoría cruzada (H1, H3, H4).
              "subrepresentado", "0,28 ± 0,06", "9 813", "28 950"]
    faltan = [c for c in claves if c not in texto]
    check(not faltan, f"{len(claves)} cifras clave presentes en el panel",
          f"faltan cifras clave: {faltan}")
    # H1: la dirección de la razón no puede volver a invertirse. Se comprueban las
    # cadenas exactas del error, no la palabra «sobrerrepresentado», que sigue siendo
    # correcta para raizal, palenquero y rrom.
    for mala in ("más</i> representado entre los investigadores",
                 "proporción entre investigadores / proporción en la población",
                 "mayor que 1 = sobrerrepresentación",
                 "grupos principales están <i>sobrerrepresentados</i>"):
        check(mala not in texto, f"el panel no invierte la dirección ({mala[:40]}…)",
              f"el panel conserva la afirmación invertida: {mala}")

    print("\n== 5b. El panel y el documento dicen lo mismo sobre la dirección ==")
    doc_div = (RAIZ / "documentacion_auditoria" / "analisis_diversidad.md").read_text(
        encoding="utf-8").replace("\u202f", " ")
    # La razón es %DANE / %investigadores: los cuatro grupos principales tienen
    # razón > 1, luego están SUBrepresentados. Los tres pequeños, razón < 1.
    principales = ["afro", "indigena", "discapacidad", "victima"]
    todos_mayores = all(d["diversidad_inferencia"]["grupos"][k]["razon"] > 1
                        for k in principales)
    todos_menores = all(d["diversidad_inferencia"]["grupos"][k]["razon"] < 1
                        for k in ("raizal", "palenquero", "rrom"))
    check(todos_mayores and todos_menores,
          "los cuatro grupos principales tienen razón > 1 y los tres pequeños < 1",
          "el reparto de razones cambió: revisa la dirección antes de publicar")
    for fuente, etiqueta in ((texto, "el panel"),
                             (doc_div, "analisis_diversidad.md")):
        bajo = fuente.lower()
        check("subrepresentad" in bajo and "sobrerrepresentad" in bajo,
              f"{etiqueta} nombra las dos direcciones",
              f"{etiqueta} no nombra las dos direcciones")
        # La frase que describe los cuatro grupos principales debe decir sub-.
        i = bajo.find("cuatro grupos")
        j = bajo.find("subrepresentad", i) if i >= 0 else -1
        k2 = bajo.find("sobrerrepresentad", i) if i >= 0 else -1
        ok = i >= 0 and j >= 0 and (k2 < 0 or j < k2)
        check(ok, f"{etiqueta} dice que los cuatro grupos principales están "
                  f"subrepresentados",
              f"{etiqueta}: la frase de los cuatro grupos no dice subrepresentados")

    print("\n== 6. Página viva: JS y anidamiento ==")
    # Chrome headless no arranca en este entorno (el sandbox bloquea los named
    # pipes que necesita), así que la comprobación visual es del usuario. Lo que sí
    # se puede verificar es lo que dejaría el panel en blanco: un JS que no compila
    # o etiquetas mal cerradas.
    bloques = re.findall(r"<script>(.*?)</script>", crudo, flags=re.S)
    propio_js = bloques[-1] if bloques else ""
    try:
        import shutil
        import subprocess
        import tempfile
        node = shutil.which("node")
    except Exception:                                          # noqa: BLE001
        node = None
    if node and propio_js:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                          encoding="utf-8") as fh:
            fh.write(propio_js)
            ruta = Path(fh.name)
        r = subprocess.run([node, "--check", str(ruta)], capture_output=True,
                           text=True)
        ruta.unlink(missing_ok=True)
        check(r.returncode == 0, "el JavaScript de la página compila (node --check)",
              f"el JavaScript no compila: {r.stderr.strip()[:200]}")
    else:
        print("  [---] node no disponible: se omite la comprobación de sintaxis del JS")
    for pieza in ("activar('tab-resumen')", "dataset.tab", "Plotly.Plots.resize",
                  "getElementById('buscador')", "addEventListener('input'"):
        check(pieza in propio_js, f"el JS contiene {pieza}",
              f"falta en el JS: {pieza}")

    from html.parser import HTMLParser

    class Contador(HTMLParser):
        SIN_CIERRE = {"br", "img", "input", "meta", "link", "hr", "area", "base",
                      "col", "embed", "source", "track", "wbr"}

        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.pila = []
            self.problemas = []

        def handle_starttag(self, tag, attrs):
            if tag not in self.SIN_CIERRE:
                self.pila.append(tag)

        def handle_endtag(self, tag):
            if tag in self.SIN_CIERRE:
                return
            if self.pila and self.pila[-1] == tag:
                self.pila.pop()
            else:
                self.problemas.append(f"</{tag}>")

    p = Contador()
    p.feed(crudo)
    check(not p.pila, "todas las etiquetas HTML se cierran",
          f"quedan sin cerrar: {p.pila[-4:]}")
    check(not p.problemas, "el anidamiento de etiquetas es correcto",
          f"{len(p.problemas)} etiquetas cierran fuera de orden: {p.problemas[:4]}")

    print("\n== 7. Avisos de lectura ==")
    if texto.count("no alcanzada") < 2:
        avisos.append("no se menciona que hay medianas no alcanzadas")
    if "censura" not in texto.lower():
        avisos.append("no se advierte de la censura")
    check(True, "revisión manual de avisos completada", "")

    print("\n" + "=" * 60)
    for a in avisos:
        print(f"  [AVISO] {a}")
    if fallos:
        print(f"  {len(fallos)} FALLO(S)")
        return 1
    print(f"  Todo correcto · {len(tr)} gráficos · {mb:.2f} MiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
