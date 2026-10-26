#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluar_ronda2.py
=================

Fase 5, ronda 2: lee el JSON que deja entrenar_ronda2.py y presenta la
comparacion completa (ronda 1 vs cada mejora) en VAL, mas la recomendacion
de combinacion. Test NO se toca.

Uso:
    <python con xgboost> 07_modelo/modelado/evaluar_ronda2.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTADOS_DIR = SCRIPT_DIR / "resultados"


def cargar_ultimo() -> tuple[Path, dict]:
    candidatos = sorted(RESULTADOS_DIR.glob("ronda2_*.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidatos:
        raise SystemExit("No hay resultados de ronda 2; ejecute antes entrenar_ronda2.py")
    return candidatos[0], json.loads(candidatos[0].read_text(encoding="utf-8"))


def main() -> int:
    ruta, datos = cargar_ultimo()
    print(f"Fuente: {ruta.name}")
    print(f"Interprete del entrenamiento: {datos.get('interprete')}")
    print("REGLA: evaluacion en val (destino 2019); test no usado.")
    print(f"\nAno fuera: {datos.get('ano_fuera')} | delta sin ano: {datos.get('delta_sin_ano')}")

    print("\nTabla comparativa (val) — orden de clases: baja / se_mantiene / sube")
    print(f"{'dataset':<20} {'variante':<15} {'F1macro':>8} {'F1sube':>7} {'F1mant':>7} "
          f"{'F1baja':>7} {'AUCbaja':>8} {'Brier':>7} {'feats':>6}")
    mejor_global = None
    for ds, r in datos["datasets"].items():
        for nombre, v in r["variantes"].items():
            f = v["f1_por_clase"]
            a = v["auc_ovr_por_clase"]["baja"]
            b = v["brier_multiclase"]
            print(f"{ds:<20} {nombre:<15} {v['f1_macro']:>8.4f} {f['sube']:>7.3f} "
                  f"{f['se_mantiene']:>7.3f} {f['baja']:>7.3f} "
                  f"{(a if a is not None else float('nan')):>8.3f} "
                  f"{(b if b is not None else float('nan')):>7.4f} {v['n_features']:>6}")
            if mejor_global is None or v["f1_macro"] > mejor_global["f1_macro"]:
                mejor_global = {"dataset": ds, "variante": nombre, **v}
        print()

    print("Umbrales (sobre el mejor modelo base sin ano):")
    for ds, r in datos["datasets"].items():
        u = r["umbrales"]
        print(f"   {ds} (base={u['base']}): argmax F1baja={u['argmax']['f1_baja']:.3f} | "
              f"umbral macro={u['macro']['umbral']} -> F1={u['macro']['f1_macro']:.3f} | "
              f"umbral baja={u['baja']['umbral']} -> F1baja={u['baja']['f1_baja']:.3f}")

    print("\nF1 de 'baja' por categoria de origen (mejor variante por dataset):")
    for ds, r in datos["datasets"].items():
        print(f"   {ds} (mejor={r['mejor']}):")
        for orden, v in r["por_origen"].items():
            print(f"      {v['categoria']:<16} n={v['n']:>5} | bajas reales={v['n_baja_real']:>4} | "
                  f"predichas baja={v['n_pred_baja']:>4} | F1 baja={v['f1_baja']:.3f} | "
                  f"F1 macro={v['f1_macro']:.3f}")

    # ---- recomendacion ----
    print("\n=== RECOMENDACION ===")
    for ds, r in datos["datasets"].items():
        r1 = r["variantes"]["r1"]["f1_macro"]
        mejor = max(r["variantes"].items(), key=lambda kv: kv[1]["f1_macro"])
        delta_pp = 100 * (mejor[1]["f1_macro"] - r1)
        auc_baja = mejor[1]["auc_ovr_por_clase"]["baja"]
        print(f"   {ds}: mejor={mejor[0]} F1={mejor[1]['f1_macro']:.4f} "
              f"(r1={r1:.4f}; delta={delta_pp:+.1f} pp) | AUC baja={auc_baja}")
    print(f"\n   Mejor global: {mejor_global['dataset']} / {mejor_global['variante']} "
          f"F1={mejor_global['f1_macro']:.4f}")

    r1_global = max(r["variantes"]["r1"]["f1_macro"] for r in datos["datasets"].values())
    delta_global_pp = 100 * (mejor_global["f1_macro"] - r1_global)
    if delta_global_pp < 2.0:
        print("   La mejor mejora NO supera +2 pp sobre la ronda 1: el frecuentista "
              "esta en su techo con estas features.")
        print("   Recomendacion: abrir el enfoque bayesiano (jerarquico por categoria/"
              "convocatoria) para modelar la incertidumbre y la escasez de 'baja'.")
    else:
        print(f"   La mejor mejora supera +2 pp ({delta_global_pp:+.1f} pp): "
              "consolidar la combinacion ganadora y seguir con el enfoque frecuentista.")
    print(f"   AUC 'baja' global: {mejor_global['auc_ovr_por_clase']['baja']}")

    salida = RESULTADOS_DIR / f"evaluacion_ronda2_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    salida.write_text(json.dumps({
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente": str(ruta),
        "mejor_global": {"dataset": mejor_global["dataset"],
                         "variante": mejor_global["variante"],
                         "f1_macro": mejor_global["f1_macro"],
                         "delta_pp_vs_r1": round(delta_global_pp, 2)},
        "recomendacion": ("bayesiano" if delta_global_pp < 2.0 else "frecuentista"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
