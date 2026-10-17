# -*- coding: utf-8 -*-
"""Resume diversidad_inferencia.json y verifica las figuras de F2-5."""
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
J = json.loads((DOC / "data" / "memoria" / "diversidad_inferencia.json")
               .read_text(encoding="utf-8"))

print("=== claves raíz ===")
print(list(J.keys()))

print("\n=== grupos: proporción, IC de Wilson y cociente con su IC ===")
print(f"{'grupo':12s} {'n':>5s} {'p%':>6s} {'IC95 Wilson':>16s} {'razón':>7s} "
      f"{'IC razón (Wilson)':>19s} {'n muestra':>10s} {'IC razón (diseño)':>20s}")
for g, d in J["grupos"].items():
    w = d["razon_ic_wilson"]
    b = d["razon_ic_diseno"]
    icd = f"[{b[0]:.2f}; {b[1]:.2f}]" if b else "no acotado"
    print(f"{g:12s} {d['n']:5d} {d['pct']:6.2f} "
          f"[{d['ic95_wilson_pct'][0]:6.2f};{d['ic95_wilson_pct'][1]:6.2f}] "
          f"{d['razon']:7.2f} [{w[0]:7.2f};{w[1]:7.2f}] "
          f"{d['n_muestra_grupo']:10d} {icd:>20s}")

print("\n=== banderas ===")
for k in ("grupos_no_estimables_con_la_muestra",
          "grupos_cuyo_cociente_no_queda_acotado",
          "grupos_cuyo_cociente_no_quedó_acotado"):
    if k in J:
        print(f"  {k}: {J[k]}")

print(f"\n  denominador etnia: {J['denominador_etnia']['respuestas_conocidas']} "
      f"conocidas, mayoría {J['denominador_etnia']['mayoria_declarada_incluida']}, "
      f"pct correcto {J['denominador_etnia']['pct_con_denominador_correcto']:.2f} %, "
      f"pct equivocado {J['denominador_etnia']['pct_con_denominador_equivocado']:.1f} %")
print(f"  alcance: {J['alcance_temporal']['con_datos']} "
      f"· sin datos {J['alcance_temporal']['sin_datos']}")

print("\n=== validaciones ===")
for k, v in J["validaciones"].items():
    print(f"  [{'OK ' if v else 'NO '}] {k}")

print("\n=== cobertura por convocatoria ===")
for a, d in sorted(J["cobertura_por_convocatoria"].items()):
    print(f"  {a}: n={d['n']:6,d} etnia={d['TXT_GRUPO_ETNICO']['pct_cobertura']:6.2f} "
          f"disca={d['TXT_POBLACION_DISCA']['pct_cobertura']:6.2f} "
          f"vict={d['ID_VICTIMA_CONFLICTO']['pct_cobertura']:6.2f}".replace(",", " "))

print("\n=== figuras ===")
for p in sorted(glob.glob(str(DOC / "data" / "memoria" / "graficas_diversidad" / "*.png"))):
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
    print(f"  {Path(p).name:46s} {sz[0]}x{sz[1]}  prohibidos={100*malos/tot:.4f}%")
