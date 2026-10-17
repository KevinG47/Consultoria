# -*- coding: utf-8 -*-
"""Verifica analisis_supervivencia.md contra supervivencia.json y su estructura."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
TEXTO = (RAIZ / "03_informes" / "analisis_fase2" / "analisis_supervivencia.md").read_text(encoding="utf-8")
J = json.loads((RAIZ / "01_datos" / "resultados_json" / "supervivencia.json")
               .read_text(encoding="utf-8"))
T = TEXTO.replace("\u2212", "-").replace("\u00a0", " ")


def formas(x: float, dec_max: int = 4) -> list[str]:
    out = []
    for dec in range(0, dec_max + 1):
        s = f"{x:,.{dec}f}"
        out.append(s.replace(",", "\u00a0").replace(".", ",").replace("\u00a0", " "))
        out.append(s.replace(",", "").replace(".", ","))
    return out


faltan = []
d = J["diseno"]
for etq, val in (("personas", d["n_personas"]), ("eventos", d["eventos"]),
                 ("censuradas", d["censuradas"]),
                 ("pct censurado", d["pct_censurado"]),
                 ("ventana", d["ventana_anios"]),
                 ("tiempo medio", d["tiempo_medio_observado"])):
    if not any(f in T for f in formas(val)):
        faltan.append((etq, val))

c = J["cohorte_2013"]
for etq, val in (("n cohorte", c["n"]), ("eventos cohorte", c["eventos"]),
                 ("S final", c["retencion_final"])):
    if not any(f in T for f in formas(val)):
        faltan.append((etq, val))

for k, v in J["logrank"].items():
    if not any(f in T for f in formas(v["chi2"], 2)):
        faltan.append((f"logrank {k}", v["chi2"]))
    if v["gl"] and not any(f in T for f in formas(v["gl"], 0)):
        faltan.append((f"gl {k}", v["gl"]))

cx = J["cox"]
for etq, val in (("n cox", cx["n"]), ("eventos cox", cx["eventos"]),
                 ("covariables", cx["n_covariables"]),
                 ("iteraciones", cx["iteraciones"])):
    if not any(f in T for f in formas(val)):
        faltan.append((etq, val))
for r in cx["coeficientes"]:
    for clave in ("hr", "ic95_inf", "ic95_sup"):
        if not any(f in T for f in formas(r[clave], 3)):
            faltan.append((f"{r['variable']}={r['nivel']} {clave}", r[clave]))

s = J["sensibilidad_emerito_agrupado"]
if not any(f in T for f in formas(s["cambio_maximo_absoluto"], 3)):
    faltan.append(("cambio maximo", s["cambio_maximo_absoluto"]))

a = J["autotest"]
for etq, val in (("autotest logrank", a["logrank_chi2"]),
                 ("autotest score", a["cox_score_chi2"])):
    if not any(f in T for f in formas(val, 4)):
        faltan.append((etq, val))
v = J["validacion_score_vs_logrank"]
for etq, val in (("real logrank", v["logrank_chi2"]),
                 ("real score", v["cox_score_chi2"])):
    if not any(f in T for f in formas(val, 4)):
        faltan.append((etq, val))

# medianas estimables
for clave, grupos in J["kaplan_meier"].items():
    for nombre, g in grupos.items():
        m = g["mediana"]
        if m["estimable"] and not any(f in T for f in formas(m["anios"], 2)):
            faltan.append((f"mediana {nombre}", m["anios"]))

print(f"cifras no encontradas: {len(faltan)}")
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

# grupos cuya mediana no se alcanza
no_alcanzadas = sum(1 for gs in J["kaplan_meier"].values()
                    for g in gs.values() if not g["mediana"]["estimable"])
total_grupos = sum(len(gs) for gs in J["kaplan_meier"].values())
print(f"  grupos con mediana no alcanzada: {no_alcanzadas} de {total_grupos}")
