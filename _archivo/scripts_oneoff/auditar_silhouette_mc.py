# -*- coding: utf-8 -*-
"""
¿Cuánto varía la silhouette publicada (0,2825) según la submuestra?

`silhouette_mixta` estima la silhouette en una submuestra estratificada de N_SIL
filas elegida con un `rng`. Con la MISMA partición y semillas distintas, el valor
se mueve: eso es el error de Monte Carlo de la cifra que el documento presenta con
cuatro decimales.
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "documentacion_auditoria" / "src"))
sys.dont_write_bytecode = True

real = sys.stdout
sys.stdout = io.TextIOWrapper(open(os.devnull, "wb"), encoding="utf-8")
try:
    import clustering_formalizado as cf
finally:
    sys.stdout = real

import numpy as np

print(f"N_SIL (filas que se submuestrean) = {cf.N_SIL}")
df = cf.cargar()
cat, z, info = cf.codificar(df)
etq, coste = cf.kprototypes(cat, z, 2, 0.5, np.random.default_rng(cf.SEMILLA))
print(f"partición fija: tamaños {sorted(np.bincount(etq).tolist(), reverse=True)} · "
      f"coste {coste:.1f}")

vals = [cf.silhouette_mixta(cat, z, etq, 0.5, np.random.default_rng(s))
        for s in (1, 2, 3, 4, 5, 6, 7, 8)]
print("\nsilhouette con la MISMA partición y 8 semillas distintas de submuestreo:")
for v in vals:
    print(f"   {v:.6f}")
print(f"\n  media {np.mean(vals):.6f} · desviación {np.std(vals, ddof=1):.6f} "
      f"· rango [{min(vals):.6f}; {max(vals):.6f}]")
print(f"  publicado en clustering.json: 0.282501")
print(f"  ¿cae 0,2825 dentro del rango de 8 semillas? "
      f"{min(vals) <= 0.282501 <= max(vals)}")
print(f"  margen frente al umbral 0,25: 0,2825 - 0,25 = 0,0325 "
      f"({0.0325 / np.std(vals, ddof=1):.1f} desviaciones del error de Monte Carlo)")

cl = json.loads((RAIZ / "documentacion_auditoria" / "data" / "memoria"
                 / "clustering.json").read_text(encoding="utf-8"))
nulo = cl["prueba_de_estructura"]["nulo_silhouette"]
print(f"\n  nulo publicado: media {np.mean(nulo):.6f} · "
      f"mínimo {min(nulo):.6f} · máximo {max(nulo):.6f}")
print(f"  El nulo es {np.mean(nulo) - 0.282501:+.6f} respecto de la cifra publicada: "
      f"la conclusión no depende de esta variación.")
