# -*- coding: utf-8 -*-
"""Resume supervivencia.json y verifica las figuras de F2-10."""
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
J = json.loads((RAIZ / "01_datos" / "resultados_json" / "supervivencia.json")
               .read_text(encoding="utf-8"))

print("=== diseño ===")
d = J["diseno"]
for k in ("n_personas", "eventos", "censuradas", "pct_censurado",
          "ventana_anios", "tiempo_medio_observado"):
    print(f"  {k:26s} {d[k]}")

print("\n=== medianas por grupo ===")
for clave, grupos in J["kaplan_meier"].items():
    print(f"\n  {clave}:")
    for nombre, g in grupos.items():
        m = g["mediana"]
        if m["estimable"]:
            ii, ss = m.get("ic95_inf"), m.get("ic95_sup")
            ic = (f" [{ii:.2f};{ss:.2f}]" if (ii is not None and ss is not None)
                  else " [IC no informativo]")
            med = f"{m['anios']:.2f} a{ic}"
        else:
            med = "no alcanzada"
        print(f"    {nombre[:36]:38s} n={g['n']:6,d} ev={g['eventos']:6,d} "
              f"{med}".replace(",", " "))

print("\n=== log-rank ===")
for k, v in J["logrank"].items():
    print(f"  {k:20s} chi2={v['chi2']:9.2f} gl={v['gl']} p={v['p']:.3e}")

print("\n=== cohorte 2013 ===")
c = J["cohorte_2013"]
print(f"  n={c['n']:,} eventos={c['eventos']:,} S_final={c['retencion_final']:.4f}"
      .replace(",", " "))
print(f"  mediana: {c['mediana']}")

print("\n=== Cox: significativas ===")
print(f"  n={J['cox']['n']:,} eventos={J['cox']['eventos']:,} "
      f"covariables={J['cox']['n_covariables']} "
      f"iteraciones={J['cox']['iteraciones']}".replace(",", " "))
print(f"  {J['cox']['significativas_al_5pct']}")

print("\n=== sensibilidad Emérito agrupado ===")
s = J["sensibilidad_emerito_agrupado"]
print(f"  n={s['n']:,} convergio={s['convergio']} "
      f"cambio máximo en HR={s['cambio_maximo_absoluto']:.4f}".replace(",", " "))
for k, v in list(s["cambio_en_los_hr"].items())[:6]:
    print(f"    {k:44s} {v:+.4f}")

print("\n=== figuras ===")
for ruta in sorted(glob.glob(str(DOC / "data" / "memoria" / "graficas_supervivencia" / "*.png"))):
    from PIL import Image
    with Image.open(ruta) as img:
        sz = img.size
        img = img.convert("RGB")
        c = Counter(img.getdata())
    tot = sum(c.values())
    malos = 0
    for col, n in c.items():
        for proh in ("B91C1C", "15803D", "7C3AED"):
            pr, pg, pb = (int(proh[i:i + 2], 16) for i in (0, 2, 4))
            if abs(col[0] - pr) <= 12 and abs(col[1] - pg) <= 12 and abs(col[2] - pb) <= 12:
                malos += n
                break
    print(f"  {Path(ruta).name:40s} {sz[0]}x{sz[1]}  prohibidos={100*malos/tot:.4f}%")

print("\n=== autotest y validación ===")
print(f"  autotest: {J['autotest']['score_vs_logrank_coinciden']} "
      f"(chi2 {J['autotest']['logrank_chi2']:.4f} vs "
      f"{J['autotest']['cox_score_chi2']:.4f})")
v = J["validacion_score_vs_logrank"]
print(f"  real: log-rank {v['logrank_chi2']:.4f} vs score Cox "
      f"{v['cox_score_chi2']:.4f} · dif relativa "
      f"{v['diferencia_relativa_chi2']:.2%} · coinciden={v['coinciden']}")
