# -*- coding: utf-8 -*-
"""Comprobación genérica de tablas y encabezados en los documentos tocados."""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
ARCHIVOS = [
    "README.md",
    "datos_originales/ERRATA.md",
    "datos_originales/README.md",
    "documentacion_auditoria/evaluacion_cumplimiento.md",
    "documentacion_auditoria/analisis_diversidad.md",
    "documentacion_auditoria/analisis_modelo_estrella.md",
    "documentacion_auditoria/analisis_percapita_territorial.md",
]

fallos = 0
for rel in ARCHIVOS:
    p = RAIZ / rel
    texto = p.read_text(encoding="utf-8", errors="replace")
    lineas = texto.splitlines()
    # Los bloques de código cercados por ``` contienen líneas que empiezan por
    # '#' (comentarios de shell) y pipes de tablas de ejemplo: se excluyen para
    # no reportar como encabezado lo que es un comentario.
    limpias, dentro = [], False
    for ln in lineas:
        if ln.lstrip().startswith("```"):
            dentro = not dentro
            continue
        if not dentro:
            limpias.append(ln)
    bloques, cur = [], []
    for ln in limpias + [""]:
        if ln.strip().startswith("|"):
            cur.append(ln)
        elif cur:
            bloques.append(cur)
            cur = []
    malas = []
    for i, b in enumerate(bloques, 1):
        anchos = {ln.count("|") for ln in b}
        if len(anchos) != 1:
            malas.append((i, sorted(anchos), len(b)))
    enc = [ln for ln in limpias if ln.startswith("#")]
    niveles = [len(h) - len(h.lstrip("#")) for h in enc]
    saltos = [(niveles[i], niveles[i + 1]) for i in range(len(niveles) - 1)
              if niveles[i + 1] - niveles[i] > 1]
    estado = "OK " if not malas and not saltos else "NO "
    if malas or saltos:
        fallos += 1
    print(f"[{estado}] {rel}")
    print(f"        {len(lineas)} líneas · {len(enc)} encabezados · "
          f"{len(bloques)} tablas")
    if malas:
        print(f"        tablas inconsistentes: {malas}")
    if saltos:
        print(f"        saltos de nivel: {saltos}")

print(f"\narchivos con problemas: {fallos}")
