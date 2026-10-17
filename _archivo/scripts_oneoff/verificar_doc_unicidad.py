# -*- coding: utf-8 -*-
"""Verifica analisis_unicidad.md contra validacion_unicidad.json y su estructura."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
TEXTO = (DOC / "analisis_unicidad.md").read_text(encoding="utf-8")
J = json.loads((DOC / "data" / "memoria" / "validacion_unicidad.json")
               .read_text(encoding="utf-8"))
T = TEXTO.replace("\u2212", "-").replace("\u00a0", " ")


def formas(x: float) -> list[str]:
    out = []
    for dec in (0, 1, 2, 3, 4):
        s = f"{x:,.{dec}f}"
        out.append(s.replace(",", "\u00a0").replace(".", ",").replace("\u00a0", " "))
        out.append(s.replace(",", "").replace(".", ","))
    return out


faltan = []
d = J["ids_no_unicos"]
simples = [
    ("ids evaluados", d["n_ids_evaluados"]),
    ("ids violadores", d["n_ids_violadores"]),
    ("pct padron", d["pct_del_padron"]),
    ("violan identidad", d["interpretacion_por_rol"]["violan_la_identidad_(edad)"]),
    ("solo genero", d["interpretacion_por_rol"]["solo_atributo_inestable_(genero)"]),
]
for e, n in d["por_estado"].items():
    simples.append((e, n))
for etq, val in simples:
    if not any(f in T for f in formas(val)):
        faltan.append((etq, val))

c = J["contraste_con_la_implementacion"]
for etq in ("pares_marcados_implementada", "pares_marcados_documentada",
            "falsos_positivos_de_la_implementada",
            "falsos_negativos_de_la_implementada",
            "pares_con_edad_que_retrocede_mas_de_4"):
    if not any(f in T for f in formas(c[etq])):
        faltan.append((etq, c[etq]))

for tol, val in J["sensibilidad_tolerancia"]["pares_por_tolerancia"].items():
    if not any(f in T for f in formas(val)):
        faltan.append((f"sensibilidad {tol}", val))

im = J["impacto"]
for etq in ("registros_afectados", "pct_registros", "pares_consecutivos_afectados",
            "pct_pares", "delta_retencion_pp", "edad_media_con", "edad_media_sin",
            "delta_edad"):
    if not any(f in T for f in formas(im[etq])):
        faltan.append((etq, im[etq]))
for k in ("retencion_2013_2021_con", "retencion_2013_2021_sin"):
    if not any(f in T for f in formas(im[k]["pct"])):
        faltan.append((k, im[k]["pct"]))

v = J["validacion_con_los_juicios_del_analista"]
for etq, val in (("revisados", v["ids_revisados_por_el_analista"]),
                 ("coinciden", v["la_diferencia_de_edad_coincide"])):
    if not any(f in T for f in formas(val)):
        faltan.append((etq, val))

# la tabla de los 15 IDs con violación de edad
edad_ids = [x for x in d["detalle"] if x["fallos_edad"] > 0]
for x in edad_ids:
    if x["id"] not in T:
        faltan.append(("id en la tabla", x["id"]))
    for clave in ("peor_residuo",):
        if not any(f in T for f in formas(abs(x[clave]))):
            faltan.append((f"{x['id']} residuo", x[clave]))

print(f"cifras comprobadas (aprox.): {len(simples) + 5 + 9 + 10 + 2 + 2 * len(edad_ids)}")
print(f"no encontradas: {len(faltan)}")
for etq, val in faltan[:30]:
    print(f"   NO APARECE '{val}'  ({etq})")

print("\n=== estructura ===")
lineas = TEXTO.splitlines()
enc = [ln for ln in lineas if ln.startswith("#")]
niveles = [len(h) - len(h.lstrip("#")) for h in enc]
saltos = [(niveles[i], niveles[i + 1]) for i in range(len(niveles) - 1)
          if niveles[i + 1] - niveles[i] > 1]
bloques, cur = [], []
for ln in lineas + [""]:
    if ln.strip().startswith("|"):
        cur.append(ln)
    elif cur:
        bloques.append(cur)
        cur = []
malas = [i for i, b in enumerate(bloques, 1)
         if len({x.count("|") for x in b}) != 1]
print(f"  {len(lineas)} líneas · {len(enc)} encabezados · {len(bloques)} tablas")
print(f"  saltos de nivel: {saltos or 'ninguno'} · tablas inconsistentes: "
      f"{malas or 'ninguna'}")
print(f"  IDs con violación de edad en el JSON: {len(edad_ids)}")
