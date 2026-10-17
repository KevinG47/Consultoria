# -*- coding: utf-8 -*-
"""
Comprueba que las 4 anclas del arreglo del enunciado «nueve dimensiones»
aparezcan EXACTAMENTE UNA VEZ en repo_mejorado/informe_final.md, y las muestra
en forma literal de Python para copiarlas sin errores de codificación.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
F = RAIZ / "04_auditoria" / "repo_mejorado" / "informe_final.md"
txt = F.read_text(encoding="utf-8")
print(f"archivo: {F.relative_to(RAIZ)}  ({len(txt)} caracteres)")
print(f"codificación: UTF-8 leído sin errores")

ANCLAS = {
    "K1 (OE4, línea ~38)": (
        "Diseñar y crear un modelo dimensional (esquema estrella) con nueve "
        "dimensiones y una tabla de hechos."),
    "K2 (diseño, línea ~80)": (
        "Diseño: se construyeron nueve dimensiones (por ejemplo: "
        "Dim-Investigador, Dim-Convocatoria, Dim-Universidad, Dim-Área, "
        "Dim-nacimiento, Dim-Género, Dim-residencia, Dim-formación, "
        "Dim-clasificación) y una tabla de hechos que centraliza métricas "
        "(p. ej. edad, victima de conflicto, grupo etnico y población "
        "discapacitada, además de los ID de las dimensiones). Normalización y "
        "llaves primarias/foráneas definidas."),
    "K3 (5.3, línea ~135)": (
        "Se definieron nueve dimensiones que describen atributos de los "
        "investigadores (persona, residencia, convocatoria, institucionales, "
        "formación, regionales, género, clasificación etc.) y una tabla de "
        "hechos"),
    "K4 (conclusiones, línea ~159)": (
        "El modelo dimensional (nueve dimensiones + tabla de hechos) es "
        "adecuado para alimentar dashboards y reportes."),
}

print()
ok = True
for nombre, ancla in ANCLAS.items():
    n = txt.count(ancla)
    estado = "OK " if n == 1 else "PROBLEMA"
    if n != 1:
        ok = False
    print(f"[{estado}] {nombre}: aparece {n} vez/veces")
    if n == 0:
        # ¿existe el prefijo? Sirve para localizar la diferencia.
        for corte in (200, 120, 80, 40):
            if txt.count(ancla[:corte]) >= 1:
                print(f"          el prefijo de {corte} caracteres SÍ aparece; "
                      f"la diferencia está después")
                i = txt.find(ancla[:corte])
                real = txt[i:i + len(ancla) + 40]
                print(f"          real: {real!r}")
                break
        else:
            print("          ni el prefijo de 40 caracteres aparece")

print(f"\n=== todas las anclas únicas: {ok} ===")
print("\n=== formas literales de Python (para el parche) ===")
for nombre, ancla in ANCLAS.items():
    print(f"\n# {nombre}\n{ancla!r}")
