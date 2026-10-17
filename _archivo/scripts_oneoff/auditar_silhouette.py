# -*- coding: utf-8 -*-
"""
Auditoría independiente del número central de F2-6: silhouette(k=2) = 0,2825.

Se reutilizan las funciones del propio script (cargar, codificar, kprototypes,
silhouette_mixta) SIN reescribirlas, y se compara el resultado con el publicado.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
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

t0 = time.time()
df = cf.cargar()
cat, z, info = cf.codificar(df)
print(f"filas {len(cat):,} · categóricas {cat.shape[1]} · numérica 1".replace(",", " "))

etq, coste = cf.kprototypes(cat, z, 2, 0.5, np.random.default_rng(cf.SEMILLA))
sil = cf.silhouette_mixta(cat, z, etq, 0.5, np.random.default_rng(cf.SEMILLA))
print(f"\nsilhouette(k=2) recalculada : {sil:.6f}")
cl = json.loads((RAIZ / "01_datos" / "resultados_json" / "clustering.json").read_text(encoding="utf-8"))
pub = cl["criterios_k"]["silhouette"][0]
print(f"publicada                  : {pub:.6f}")
print(f"diferencia                 : {abs(sil - pub):.2e}")
print(f"tamaños de los dos grupos  : {sorted(np.bincount(etq).tolist(), reverse=True)}")
print(f"coste (inercia intra)      : {coste:.1f} · publicado k=2: "
      f"{cl['criterios_k']['coste'][0]:.1f}")
print(f"tiempo: {time.time() - t0:.1f} s")
