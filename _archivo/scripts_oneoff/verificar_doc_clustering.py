# -*- coding: utf-8 -*-
"""Verifica analisis_clustering.md contra clustering.json y su estructura."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
TEXTO = (DOC / "analisis_clustering.md").read_text(encoding="utf-8")
J = json.loads((DOC / "data" / "memoria" / "clustering.json")
               .read_text(encoding="utf-8"))
T = TEXTO.replace("\u2212", "-").replace("\u00a0", " ")


def v(x: float, dec: int) -> str:
    return f"{x:,.{dec}f}".replace(",", "\u00a0").replace(".", ",").replace(
        "\u00a0", " ")


def formas(x: float) -> list[str]:
    """Comma decimal y espacio de miles, en 0-4 decimales."""
    out = []
    for dec in (0, 1, 2, 3, 4):
        out.append(v(x, dec))
        out.append(v(x, dec).replace(" ", ""))
    return out


faltan = []
ck = J["criterios_k"]
for i, k in enumerate(ck["k"]):
    for clave in ("silhouette", "calinski", "davies"):
        if not any(f in T for f in formas(ck[clave][i])):
            faltan.append((f"{clave} k={k}", v(ck[clave][i], 3)))
    if not any(f in T for f in formas(ck["perdida"][i] * 100)):
        faltan.append((f"pérdida k={k}", v(ck["perdida"][i] * 100, 2)))

p = J["prueba_de_estructura"]
for etq, val in (("silhouette obs", p["silhouette_observada"]),
                 ("silhouette nulo", p["silhouette_nulo_medio"]),
                 ("silhouette p", p["silhouette_p"]),
                 ("ch obs", p["calinski_observado"]),
                 ("ch nulo", p["calinski_nulo_medio"]),
                 ("ch p", p["calinski_p"])):
    if not any(f in T for f in formas(val)):
        faltan.append((etq, v(val, 3)))
for lo, hi in (p["silhouette_nulo_ic95"],):
    for x in (lo, hi):
        if not any(f in T for f in formas(x)):
            faltan.append(("IC nulo", v(x, 4)))

lcn = J["los_clusters_no_son_una_variable"]
for etq, val in (("ARI categoría", lcn["ari_vs_categoria"]),
                 ("ARI gran área", lcn["ari_vs_gran_area"]),
                 ("ARI convocatoria", lcn["ari_vs_convocatoria"])):
    if not any(f in T for f in formas(val)):
        faltan.append((etq, v(val, 3)))

for nombre, d in J["aporte_de_cada_variable"].items():
    if not any(f in T for f in formas(d["cramer_v"])):
        faltan.append((f"V {nombre}", v(d["cramer_v"], 3)))

pi = J["perdida_de_informacion"]
for etq, val in (("inercia total", pi["inercia_total_k1"]),
                 ("inercia intra", pi["inercia_intra_k"]),
                 ("pérdida", pi["perdida_pct"])):
    if not any(f in T for f in formas(val)):
        faltan.append((etq, v(val, 1)))

for k, d in J["edad_por_cluster"].items():
    for etq, val in (("media", d["media"]), ("mediana", d["mediana"]),
                     ("n", d["n"])):
        if not any(f in T for f in formas(val)):
            faltan.append((f"edad cluster {k} {etq}", v(val, 2)))

for g, val in J["sensibilidad_gamma"].items():
    if not any(f in T for f in formas(val)):
        faltan.append((f"ARI gamma {g}", v(val, 3)))
if not any(f in T for f in formas(J["sensibilidad_edades_imposibles"]
                                 ["ari_vs_principal"])):
    faltan.append(("ARI edades", "?"))
np_ = J["nivel_persona"]
for etq, val in (("silhouette persona", np_["silhouette"]),):
    if not any(f in T for f in formas(val)):
        faltan.append((etq, v(val, 4)))
for n in np_["tamanos"]:
    if not any(f in T for f in formas(n)):
        faltan.append(("tamaño persona", v(n, 0)))

for etq, val in (("registros", J["datos"]["registros"]),
                 ("personas", J["datos"]["personas"]),
                 ("edades imposibles", J["datos"]["edades_imposibles"]),
                 ("celdas", J["datos"]["registros"] * 7)):
    if not any(f in T for f in formas(val)):
        faltan.append((etq, v(val, 0)))

# perfiles del k=2
perf = J["perfiles"]
for var, d in perf.items():
    for i, cat in enumerate(d["categorias"]):
        for cl in d["clusters"]:
            val = d["clusters"][cl][i]
            if val >= 1.0 and not any(f in T for f in formas(val)):
                faltan.append((f"{var}/{cat}/{cl}", v(val, 1)))

print(f"cifras comprobadas (aprox.): "
      f"{len(ck['k']) * 4 + 20 + 6 + 3 + len(perf) * 8}")
print(f"no encontradas: {len(faltan)}")
for etq, val in faltan[:40]:
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
