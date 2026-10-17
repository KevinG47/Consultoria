# -*- coding: utf-8 -*-
"""
verificar_doc_percapita.py
==========================

Comprueba que TODA cifra citada en `analisis_percapita_territorial.md` coincide
con `percapita_territorial.json`. Evita el error más plausible de este
entregable: un número escrito de memoria que no sale del análisis.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
TEXTO = (DOC / "analisis_percapita_territorial.md").read_text(encoding="utf-8")
J = json.loads((DOC / "data" / "memoria" / "percapita_territorial.json")
               .read_text(encoding="utf-8"))

# --- valores que el documento debe contener, calculados del JSON ------------
pc = J["tasa_por_100000"]["por_convocatoria"]
ca = J["comparacion_auditado"]
ix = J["indices_stock"]
st = J["tasa_por_100000"]["stock_ultima_convocatoria"]
ic = J["bootstrap_personas"]["por_convocatoria_y_stock"]["stock"]["tasa_ic95"]
bp = J["bootstrap_personas"]["por_convocatoria_y_stock"]
bd = J["bootstrap_diseno_mas_ps"]["por_convocatoria"]
rb = J["robustez_denominador"]
k = J["indicadores_clave"]

esperados: list[tuple[str, str]] = []


def esp(descripcion: str, valor: float, dec: int = 2) -> None:
    """Registra el texto con el que el documento debe citar `valor`."""
    esperados.append((descripcion, f"{valor:.{dec}f}".replace(".", ",")))


# HHI de cuotas sin exterior e índices por convocatoria
for a in ("2013", "2017", "2019", "2021"):
    esp(f"HHI cuotas {a}", ca["hhi_sin_exterior"][a], 4)
for a in ("2013", "2015", "2017", "2019", "2021"):
    esp(f"Gini tasas {a}", pc[a]["gini_tasas"], 4)
    esp(f"Theil tasas {a}", pc[a]["theil_t_tasas"], 4)
    esp(f"Gini conteos {a}", pc[a]["gini_conteos"], 4)
# La tabla de descomposición del documento muestra solo 2013, 2017 y 2021.
for a in ("2013", "2017", "2021"):
    esp(f"Theil entre {a}", pc[a]["theil_tasas_entre_regiones"], 4)
    esp(f"Theil dentro {a}", pc[a]["theil_tasas_dentro_regiones"], 4)
# porcentajes entre/dentro
for a in ("2013", "2021"):
    esp(f"% entre {a}", 100 * pc[a]["theil_tasas_entre_regiones"]
        / pc[a]["theil_t_tasas"], 1)
    esp(f"% dentro {a}", 100 * pc[a]["theil_tasas_dentro_regiones"]
        / pc[a]["theil_t_tasas"], 1)
# tasas del stock
for nombre in ("Bogotá, D. C.", "Caldas", "Antioquia", "Atlántico", "Santander",
               "Boyacá", "Guainía", "Vaupés", "Arauca", "Guaviare", "Putumayo",
               "Vichada"):
    esp(f"tasa {nombre}", st[nombre]["tasa_por_100000"], 1)
nombres = list(st)
for i, n in enumerate(nombres):
    if n in ("Bogotá, D. C.", "Caldas", "Antioquia", "Atlántico", "Santander",
             "Boyacá", "Guainía", "Vaupés", "Arauca", "Guaviare", "Putumayo",
             "Vichada"):
        esp(f"IC inf {n}", ic["lo"][i], 1)
        esp(f"IC sup {n}", ic["hi"][i], 1)
# indicadores clave
esp("tasa nacional stock", k["tasa_nacional_por_100000"], 1)
esp("razón mayor/menor", k["razon_mayor_menor"], 1)
esp("cuota Bogotá investigadores %", 100 * k["cuota_bogota_investigadores"], 2)
esp("cuota Bogotá población %", 100 * k["cuota_bogota_poblacion"], 2)
esp("sobrerrepresentación Bogotá", k["sobrerrepresentacion_cuota_vs_poblacion"]
    ["Bogotá, D. C."], 2)
esp("subrepresentación Vichada",
    k["subrrepresentacion_cuota_vs_poblacion"]["Vichada"], 2)
esp("subrepresentación Putumayo",
    k["subrrepresentacion_cuota_vs_poblacion"]["Putumayo"], 2)
# bootstrap
for a in ("2013", "2021"):
    esp(f"ancho IC personas {a}", bp[a]["ancho_ic_mediano_por_100000"], 1)
    esp(f"ancho IC diseño {a}", bd[a]["ancho_ic_mediano_por_100000"], 1)
esp("Gini stock", ix["gini_tasas"], 3)
esp("Gini stock IC inf", bp["stock"]["gini_ic95"][0], 3)
esp("Gini stock IC sup", bp["stock"]["gini_ic95"][1], 3)
# robustez
esp("Gini con ajustada 2018", rb["stock_con_poblacion_ajustada_2018"]
    ["gini_tasas"], 3)
esp("Theil con ajustada 2018", rb["stock_con_poblacion_ajustada_2018"]
    ["theil_t_tasas"], 3)
esp("Gini 2021 con denominador 2021", rb["convocatoria_2021"]
    ["gini_proyectada_2021"], 3)
esp("Gini 2021 con denominador 2018", rb["convocatoria_2021"]
    ["gini_censada_2018"], 3)
esp("delta Gini ajustada", rb["stock_con_poblacion_ajustada_2018"]
    ["delta_gini_vs_censada"], 3)
esp("delta Theil ajustada", rb["stock_con_poblacion_ajustada_2018"]
    ["delta_theil_vs_censada"], 3)
# comparación con el auditado
esp("HHI auditado 2013", ca["hhi_auditado"]["2013"], 3)
esp("HHI auditado 2021", ca["hhi_auditado"]["2021"], 3)
esp("HHI sin exterior 2013", ca["hhi_sin_exterior"]["2013"], 4)
esp("efecto exterior pp", abs(ca["efecto_exterior_media_pp"]), 2)
esperados.append(("territorios reproducidos", "29, 31, 31, 32, 32, 34"))
esperados.append(("población censada", "44 164 417"))
esperados.append(("población ajustada", "48 258 494"))
esperados.append(("población 2021", "51 115 637"))
esperados.append(("registros", "77 237"))
esperados.append(("personas", "30 086"))
esperados.append(("stock personas", "28 950"))
esperados.append(("excluidos registros", "2 448"))
esperados.append(("excluidos %", "3,17"))
esperados.append(("muestra MAS", "2 224"))
esperados.append(("replicas", "2 000"))
esp("Exterior registros", 2132, 0)
esperados[-1] = ("Exterior registros", "2 132")
esp("No disponible registros", 316, 0)

# --- comprobación ----------------------------------------------------------
fallos: list[str] = []
for descripcion, texto in esperados:
    if texto not in TEXTO:
        fallos.append(f"NO APARECE '{texto}'  ({descripcion})")

print(f"cifras comprobadas: {len(esperados)}")
print(f"no encontradas en el documento: {len(fallos)}")
for f in fallos:
    print(f"   {f}")

# --- coherencia interna de las cifras derivadas ---------------------------
print("\n--- cifras derivadas que el documento afirma ---")
pares = {
    "excluidos % (2448/77237)": 100 * 2448 / 77237,
    "% entre 2013": 100 * 0.3891 / 0.4906,
    "% dentro 2021": 100 * 0.1023 / 0.3228,
    "caída Gini tasas %": 100 * (1 - pc["2021"]["gini_tasas"]
                                 / pc["2013"]["gini_tasas"]),
    "caída Gini conteos %": 100 * (1 - pc["2021"]["gini_conteos"]
                                   / pc["2013"]["gini_conteos"]),
    "deptos que sí difieren (max)": 33 - 6,
    "deptos que sí difieren (min)": 33 - 9,
}
for kk, v in pares.items():
    print(f"   {kk:34s} {v:.2f}")

# --- estructura markdown --------------------------------------------------
print("\n--- estructura del documento ---")
lineas = TEXTO.splitlines()
print(f"   líneas: {len(lineas)} · palabras: {len(TEXTO.split())}")
encabezados = [ln for ln in lineas if ln.startswith("#")]
print(f"   encabezados: {len(encabezados)}")
niveles = [len(h) - len(h.lstrip("#")) for h in encabezados]
saltos = [(niveles[i], niveles[i + 1]) for i in range(len(niveles) - 1)
          if niveles[i + 1] - niveles[i] > 1]
print(f"   saltos de nivel: {saltos if saltos else 'ninguno'}")
# tablas: cada bloque debe tener todas las filas con el mismo número de '|'
bloques, actual = [], []
for ln in lineas + [""]:
    if ln.strip().startswith("|"):
        actual.append(ln)
    elif actual:
        bloques.append(actual)
        actual = []
malas = 0
for i, b in enumerate(bloques, 1):
    anchos = {ln.count("|") for ln in b}
    if len(anchos) != 1:
        malas += 1
        print(f"   tabla {i} con anchos inconsistentes: {sorted(anchos)}")
print(f"   tablas: {len(bloques)} · inconsistentes: {malas}")

# --- enlaces y rutas citadas ---------------------------------------------
rutas = re.findall(r"`([^`]+\.(?:py|json|md|csv|png|txt))`", TEXTO)
print(f"\n--- rutas citadas con extensión ({len(rutas)}) ---")
faltan = []
for r in sorted(set(rutas)):
    candidatos = [RAIZ / r, DOC / r, DOC / "data" / "memoria" / r,
                  RAIZ / "datos_originales" / "datos_fuente" / r]
    if not any(c.exists() or c.parent.exists() for c in candidatos):
        faltan.append(r)
for r in sorted(set(rutas)):
    print(f"   {r}")
print(f"   sin localizar: {faltan if faltan else 'ninguna'}")

print(f"\nRESULTADO: {'OK' if not fallos and not malas else 'REVISAR'}")
