# -*- coding: utf-8 -*-
"""
verificar_doc_diversidad.py
===========================

Comprueba, 1) que toda cifra de `analisis_diversidad.md` salga del JSON, y
2) la estructura markdown de ese documento y de `datos_originales/ERRATA.md`.
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
TEXTO = (DOC / "analisis_diversidad.md").read_text(encoding="utf-8")
ERRATA = (RAIZ / "datos_originales" / "ERRATA.md").read_text(encoding="utf-8")
J = json.loads((DOC / "data" / "memoria" / "diversidad_inferencia.json")
               .read_text(encoding="utf-8"))


def e(x: float, dec: int) -> str:
    """Número en formato español con coma decimal."""
    return f"{x:,.{dec}f}".replace(",", "\u00a0").replace(".", ",").replace(
        "\u00a0", " ")


esperados: list[tuple[str, str]] = []
for g, d in J["grupos"].items():
    esperados.append((f"{g} n", e(d["n"], 0)))
    esperados.append((f"{g} pct", e(d["pct"], 2)))
    esperados.append((f"{g} wilson low", e(d["ic95_wilson_pct"][0], 2)))
    esperados.append((f"{g} wilson high", e(d["ic95_wilson_pct"][1], 2)))
    esperados.append((f"{g} razon", e(d["razon"], 2)))
    esperados.append((f"{g} razon low", e(d["razon_ic_wilson"][0], 2)))
    esperados.append((f"{g} razon high", e(d["razon_ic_wilson"][1], 2)))
    esperados.append((f"{g} muestra", e(d["n_muestra_grupo"], 0)))
    if d["razon_ic_diseno"]:
        esperados.append((f"{g} diseno low", e(d["razon_ic_diseno"][0], 2)))
        esperados.append((f"{g} diseno high", e(d["razon_ic_diseno"][1], 2)))

de = J["denominador_etnia"]
esperados += [
    ("denominador conocido", e(de["respuestas_conocidas"], 0)),
    ("mayoria", e(de["mayoria_declarada_incluida"], 0)),
    ("denominador equivocado", e(de["denominador_si_se_excluye_la_mayoria"], 0)),
    ("pct equivocado", e(de["pct_con_denominador_equivocado"], 1)),
    ("respuestas discapacidad",
     e(J["grupos"]["discapacidad"]["denominador_respuestas_conocidas"], 0)),
]
for a, d in J["cobertura_por_convocatoria"].items():
    if a == "2021":
        for col in ("TXT_GRUPO_ETNICO", "TXT_POBLACION_DISCA",
                    "ID_VICTIMA_CONFLICTO"):
            esperados.append((f"cobertura {col} 2021",
                              e(d[col]["pct_cobertura"], 2)))

# anchuras y veces (se calculan)
for g in ("afro", "indigena", "discapacidad", "victima"):
    d = J["grupos"][g]
    if d["razon_ic_diseno"]:
        w = d["razon_ic_wilson"]
        ancho_w = w[1] - w[0]
        ancho_b = d["razon_ic_diseno"][1] - d["razon_ic_diseno"][0]
        esperados.append((f"{g} ancho wilson", e(ancho_w, 2)))
        esperados.append((f"{g} ancho diseno", e(ancho_b, 2)))
        esperados.append((f"{g} veces", e(ancho_b / ancho_w, 1)))

esperados += [("fuente registros", "77 237"), ("muestra MAS", "2 224"),
              ("muestra 2021", "1 554")]

fallos = [f"NO APARECE '{t}'  ({d})" for d, t in esperados if t not in TEXTO]
print(f"cifras comprobadas: {len(esperados)}")
print(f"no encontradas: {len(fallos)}")
for f in fallos:
    print(f"   {f}")


def revisar_md(nombre: str, texto: str) -> list[str]:
    """Encabezados sin saltos de nivel y tablas con el mismo número de columnas."""
    problemas = []
    lineas = texto.splitlines()
    enc = [ln for ln in lineas if ln.startswith("#")]
    niveles = [len(h) - len(h.lstrip("#")) for h in enc]
    saltos = [(niveles[i], niveles[i + 1]) for i in range(len(niveles) - 1)
              if niveles[i + 1] - niveles[i] > 1]
    if saltos:
        problemas.append(f"{nombre}: saltos de nivel {saltos}")
    bloques, cur = [], []
    for ln in lineas + [""]:
        if ln.strip().startswith("|"):
            cur.append(ln)
        elif cur:
            bloques.append(cur)
            cur = []
    malas = [i for i, b in enumerate(bloques, 1)
             if len({x.count("|") for x in b}) != 1]
    if malas:
        problemas.append(f"{nombre}: tablas inconsistentes {malas}")
    print(f"   {nombre}: {len(lineas)} líneas · {len(enc)} encabezados · "
          f"{len(bloques)} tablas · problemas: "
          f"{'ninguno' if not problemas else problemas}")
    return problemas


print("\n--- estructura ---")
fallos += revisar_md("analisis_diversidad.md", TEXTO)
fallos += revisar_md("ERRATA.md", ERRATA)

print("\n--- ERRATA: entradas y reconciliación ---")
comprobaciones = {
    "E7 presente": "## E7 ·" in ERRATA,
    "E7 cita el parche E1": "parche **E1**" in ERRATA,
    "E7 da el 72,0 %": "72,0 %" in ERRATA,
    "E1 incluye la reconciliación": "22 registros son 11 personas" in ERRATA,
    "E1 cita el caso 0000671819": "0000671819" in ERRATA,
    "E1 da las tres cifras": all(x in ERRATA for x in ("**22**", "**12**", "**11**")),
    "E7 explica por qué no lo ve un verificador":
        "no la ve un verificador de sintaxis" in ERRATA,
}
for k, v in comprobaciones.items():
    print(f"   [{'OK ' if v else 'NO '}] {k}")
    if not v:
        fallos.append(k)

print(f"\nRESULTADO: {'OK' if not fallos else 'REVISAR (' + str(len(fallos)) + ')'}")
