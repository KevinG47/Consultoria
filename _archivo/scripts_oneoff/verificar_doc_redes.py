# -*- coding: utf-8 -*-
"""Resume redes_nulos.json, verifica las figuras y comprueba el documento."""
from __future__ import annotations

import glob
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
J = json.loads((RAIZ / "01_datos" / "resultados_json" / "redes_nulos.json")
               .read_text(encoding="utf-8"))

print("=== datos de contexto ===")
print(f"  aristas observadas            : {J['modelo_configuracion']['aristas_observadas']}")
print(f"  aristas medias tras colapsar  : "
      f"{J['modelo_configuracion']['aristas_medias_tras_colapsar']:.1f}")
print(f"  grado máximo ponderado/simple : "
      f"{J['grado_max']['ponderado_como_el_auditado']} / {J['grado_max']['simple']}")
print(f"  grado medio                   : {J['red']['grado_medio']:.4f}")
print(f"  nodos contrastables           : {J['puentes']['nodos_contrastables']}")
print(f"  motivos sin prueba            : {J['puentes']['motivos_sin_prueba']}")
print(f"  esperados por azar            : "
      f"{J['puentes']['esperados_por_azar_sin_corregir']:.1f}")
print(f"  z Bonferroni                  : {J['puentes']['z_de_bonferroni']:.2f}")
print(f"  pasan FDR / Bonferroni        : "
      f"{J['puentes']['pasan_fdr_5pct']} / {J['puentes']['pasan_bonferroni']}")

print("\n=== figuras ===")
for p in sorted(glob.glob(str(DOC / "data" / "memoria" / "graficas_redes" / "*.png"))):
    from PIL import Image
    with Image.open(p) as im:
        sz = im.size
        im = im.convert("RGB")
        c = Counter(im.getdata())
    tot = sum(c.values())
    malos = 0
    for col, n in c.items():
        for proh in ("B91C1C", "15803D", "7C3AED"):
            pr, pg, pb = (int(proh[i:i + 2], 16) for i in (0, 2, 4))
            if abs(col[0] - pr) <= 12 and abs(col[1] - pg) <= 12 and abs(col[2] - pb) <= 12:
                malos += n
                break
    print(f"  {Path(p).name:44s} {sz[0]}x{sz[1]}  prohibidos={100*malos/tot:.4f}%")

# ------- comprobación del documento contra el JSON -------
TEXTO = (RAIZ / "03_informes" / "analisis_fase2" / "analisis_redes.md").read_text(encoding="utf-8")
# El documento usa el signo menos tipográfico (U+2212) en las cifras negativas.
TEXTO_N = TEXTO.replace("\u2212", "-")


def var(x: float) -> list[str]:
    """Formas en que el documento puede citar x: de 1 a 4 decimales, con coma."""
    out = []
    for dec in (0, 1, 2, 3, 4):
        s = f"{x:.{dec}f}".replace(".", ",")
        if s.endswith(",0"):
            s = s[:-2]
        out.append(s)
    return out


print("\n=== cifras del documento ===")
faltan = []
for k, d in J["contraste_nulos"].items():
    for etq, val in (("obs", d["observado"]), ("cfg", d["config_medio"]),
                     ("er", d["er_medio"])):
        if not any(t in TEXTO_N for t in var(val)):
            faltan.append((f"{k} {etq}", var(val)[2]))
    for etq in ("config_p", "er_p"):
        if not any(t in TEXTO_N for t in var(d[etq])[:3]):
            faltan.append((f"{k} {etq}", var(d[etq])[3]))

simples = [
    ("nodos", J["red"]["n_nodos"]),
    ("aristas", J["red"]["n_aristas"]),
    ("contrastables", J["puentes"]["nodos_contrastables"]),
    ("hojas", J["puentes"]["motivos_sin_prueba"]["hoja"]),
    ("pasan sin corregir", J["puentes"]["pasan_z_1_96_sin_corregir"]),
    ("grado simple max", J["grado_max"]["simple"]),
    ("grado ponderado max", J["grado_max"]["ponderado_como_el_auditado"]),
    ("aristas cf", J["modelo_configuracion"]["aristas_medias_tras_colapsar"]),
    ("esperados azar", J["puentes"]["esperados_por_azar_sin_corregir"]),
    ("z bonferroni", J["puentes"]["z_de_bonferroni"]),
    ("grado medio", J["red"]["grado_medio"]),
]
for etq, val in simples:
    if not any(t in TEXTO_N for t in var(val)):
        faltan.append((etq, var(val)[1]))

print(f"  comprobadas: {len(J['contraste_nulos']) * 5 + len(simples)} · "
      f"no encontradas: {len(faltan)}")
for d, t in faltan:
    print(f"    NO APARECE '{t}'  ({d})")

print("\n=== estructura de analisis_redes.md ===")
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
