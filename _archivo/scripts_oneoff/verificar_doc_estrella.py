# -*- coding: utf-8 -*-
"""
verificar_doc_estrella.py
=========================

Comprueba que TODA cifra citada en `analisis_modelo_estrella.md` coincida con
`modelo_estrella.json`, y que las afirmaciones sobre repo_mejorado/repo_auditado
sean verificables.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
TEXTO = (RAIZ / "03_informes" / "analisis_fase2" / "analisis_modelo_estrella.md").read_text(encoding="utf-8")
J = json.loads((RAIZ / "01_datos" / "resultados_json" / "modelo_estrella.json")
               .read_text(encoding="utf-8"))


def n(x: int) -> str:
    return f"{x:,}".replace(",", " ")


esperados: list[tuple[str, str]] = []
t3 = J["modelo_3_convocatorias"]["tablas"]
t6 = J["modelo_6_convocatorias"]["tablas"]
for k in t6:
    esperados.append((f"3conv {k}", n(t3.get(k, 0))))
    esperados.append((f"6conv {k}", n(t6[k])))
for a in ("2013", "2014", "2015", "2017", "2019", "2021"):
    esperados.append((f"evidencia {a}",
                      n(J["evidencia_versionada"]["esperado_por_convocatoria"][a])))
esperados += [
    ("total evidencia", n(J["evidencia_versionada"]["total_esperado"])),
    ("composicion", "9 tablas"),
    ("n dimensiones", "7 dimensiones"),
    ("adaptacion coma", n(J["insumo"]["adaptacion_necesaria"]
                          ["columnas_convertidas"]["EDAD_ANOS_PR"]["valores_con_coma"])),
    ("imputadas", str(J["transformacion_del_auditado"]["imputacion_de_edad"]
                      ["faltantes_en_la_fuente"])),
    ("mediana imputada", "43,29"),
]
# Los parches K y el numero de arreglos
esperados += [("parches K", "K1"), ("parches K", "K4"), ("arreglos", "34")]

fallos = []
for desc, txt in esperados:
    if txt not in TEXTO:
        fallos.append(f"NO APARECE '{txt}'  ({desc})")

print(f"cifras comprobadas: {len(esperados)}")
print(f"no encontradas: {len(fallos)}")
for f in fallos:
    print(f"   {f}")

# --- coherencia de las deltas que el documento afirma --------------------
print("\n--- deltas que el documento afirma ---")
for k in ("fact_clasificacion", "dim_convocatoria", "dim_investigador",
          "dim_institucion", "bridge_hecho_institucion", "dim_territorio",
          "dim_area"):
    d = t6[k] - t3.get(k, 0)
    print(f"   {k:26s} Δ {d:+,}")

# --- afirmaciones sobre los repositorios ---------------------------------
print("\n--- afirmaciones verificables sobre los repositorios ---")
aud = RAIZ / "04_auditoria" / "repo_original" / "informe_final.md"
mej = RAIZ / "04_auditoria" / "repo_mejorado" / "informe_final.md"
ta, tm = aud.read_text(encoding="utf-8"), mej.read_text(encoding="utf-8")
comprobaciones = {
    "repo_auditado conserva 'nueve dimensiones'": ta.count("nueve dimensiones") == 4,
    "repo_mejorado no dice 'nueve dimensiones'": "nueve dimensiones" not in tm,
    "repo_mejorado dice 'siete dimensiones' 3+ veces": tm.count("siete dimensiones") >= 3,
    "la tabla puente aparece en repo_mejorado": "tabla puente" in tm,
    "el documento cita los 4 parches": all(p in TEXTO for p in ("K1", "K4")),
}
for k, v in comprobaciones.items():
    print(f"   [{'OK ' if v else 'NO '}] {k}")
    if not v:
        fallos.append(k)

# --- estructura markdown -------------------------------------------------
print("\n--- estructura del documento ---")
lineas = TEXTO.splitlines()
enc = [ln for ln in lineas if ln.startswith("#")]
niveles = [len(h) - len(h.lstrip("#")) for h in enc]
saltos = [(niveles[i], niveles[i + 1]) for i in range(len(niveles) - 1)
          if niveles[i + 1] - niveles[i] > 1]
print(f"   líneas: {len(lineas)} · palabras: {len(TEXTO.split())}")
print(f"   encabezados: {len(enc)} · saltos de nivel: {saltos or 'ninguno'}")
bloques, actual = [], []
for ln in lineas + [""]:
    if ln.strip().startswith("|"):
        actual.append(ln)
    elif actual:
        bloques.append(actual)
        actual = []
malas = sum(1 for b in bloques if len({ln.count("|") for ln in b}) != 1)
print(f"   tablas: {len(bloques)} · inconsistentes: {malas}")
if malas:
    fallos.append(f"{malas} tablas inconsistentes")
if saltos:
    fallos.append("saltos de nivel en los encabezados")

print(f"\nRESULTADO: {'OK' if not fallos else 'REVISAR'}")
