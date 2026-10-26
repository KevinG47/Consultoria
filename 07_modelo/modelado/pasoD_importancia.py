#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pasoD_importancia.py
====================

PASO D: importancia de variables (gain) del XGBoost con mascaras.

- Top 20 por gain agregado (suma normalizada de los tres modelos).
- Agrupacion por familia: produccion, clase, tipologia, categoria, demografia.
- Se reporta que familia domina.

Uso: <python> 07_modelo/modelado/pasoD_importancia.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import metricas_umbral as mu  # noqa: E402
import modelo_mascaras as mm  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"
PRODUCCION = {"n_filas", "n_productos", "n_grupos_distintos", "dias_desde_ultimo"}


def familia(f: str) -> str:
    if f in PRODUCCION:
        return "produccion"
    if f.startswith("n_clase_"):
        return "clase_producto"
    if f.startswith("n_tipologia_"):
        return "tipologia"
    if f.startswith("n_categoria_"):
        return "categoria_calidad"
    return "otra"


def main() -> int:
    import joblib
    import pandas as pd

    contenedor = joblib.load(mu.MODELOS_DIR / "xgb_ventana_contiguo.joblib")
    feats = [f for f in contenedor["features"] if f != "ano"]
    df = mm.preparar(pd.read_parquet(SCRIPT_DIR.parent / "datos" / "derivados" /
                                     "modelo_dataset_ventana_contiguo.parquet"))
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    tr = df[np.isin(per, [17, 18, 19])]
    modelos, _ = mm.entrenar(tr, feats)
    acc, detalle = mm.ganancias(modelos, feats)

    orden = sorted(acc.items(), key=lambda kv: -kv[1])
    total = sum(acc.values())
    print("Top 20 por gain agregado (suma de los 3 modelos):")
    print("   #   feature                                                      gain_%  familia")
    top = []
    for i, (f, v) in enumerate(orden[:20], 1):
        pct = 100.0 * v / total
        top.append({"rank": i, "feature": f, "gain_pct": round(pct, 3),
                    "familia": familia(f)})
        print(f"   {i:<3d} {f[:60]:60s} {pct:6.2f}  {familia(f)}")

    fam = {}
    for f, v in acc.items():
        fam[familia(f)] = fam.get(familia(f), 0.0) + v
    print("\nGain por familia:")
    filas = []
    for k in sorted(fam, key=lambda x: -fam[x]):
        pct = 100.0 * fam[k] / total
        n = sum(1 for f in feats if familia(f) == k)
        filas.append({"familia": k, "gain_pct": round(pct, 3), "n_features": n})
        print(f"   {k:<20s} {pct:6.2f} %  ({n} features)")
    domina = max(fam, key=fam.get)
    print(f"\n   DOMINA: {domina} ({100.0*fam[domina]/total:.2f} % del gain)")

    print("\nTop 5 por modelo (IJ binario / I / IS):")
    for c, nom in ((0, "IJ binario"), (1, "I tricotomo"), (2, "IS tricotomo")):
        if c not in detalle:
            continue
        d = detalle[c]
        t5 = sorted(d.items(), key=lambda kv: -kv[1])[:5]
        print(f"   {nom}: " + ", ".join(f"{k}({100*v:.1f}%)" for k, v in t5))

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": "D", "modelo": "XGBoost mascaras sin 'ano'",
        "n_features": len(feats),
        "top20": top,
        "familias": filas,
        "familia_dominante": domina,
        "demografia": {"n_features": 0,
                       "nota": "el feature set del r1 no contiene variables demograficas"},
        "top5_por_modelo": {
            nom: [{"feature": k, "gain_pct": round(100 * v, 3)}
                  for k, v in sorted(detalle[c].items(), key=lambda kv: -kv[1])[:5]]
            for c, nom in ((0, "IJ"), (1, "I"), (2, "IS")) if c in detalle},
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("pasoD_importancia_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
