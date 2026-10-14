# -*- coding: utf-8 -*-
"""
probar_kaleido_browser.py
=========================

Prueba si se puede exportar un PNG con plotly+kaleido 1.x sin descargar nada,
apuntando `BROWSER_PATH` al Chrome ya instalado en la maquina.

Contexto: kaleido 1.x ya no trae su propio motor: usa `choreographer` para
manejar un navegador Chromium real. Sin navegador detectable, `write_image()`
falla con `choreographer...BrowserFailedError: The browser seemed to close
immediately after starting`. En esta maquina hay Chrome instalado en
`C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe`, pero no esta en el
PATH, asi que kaleido no lo encuentra.
"""

from __future__ import annotations

import io
import os
import shutil
import sys
import traceback

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CANDIDATOS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

import plotly.graph_objects as go  # noqa: E402


def figura():
    return go.Figure(go.Sankey(
        node=dict(label=["A", "B", "C"], pad=15, thickness=20),
        link=dict(source=[0, 1], target=[1, 2], value=[8, 4])))


def intentar(etiqueta: str, env: dict | None = None) -> bool:
    if env:
        os.environ.update(env)
    print(f"\n--- {etiqueta}")
    if env:
        for k, v in env.items():
            print(f"    {k}={v}")
    try:
        figura().write_image("_prueba_kaleido.png", width=400, height=300)
        ok = os.path.exists("_prueba_kaleido.png")
        print(f"    RESULTADO: OK, PNG creado ({os.path.getsize('_prueba_kaleido.png')} bytes)")
        return ok
    except Exception as e:
        raiz = [c.__module__.split(".")[0] for c in type(e).__mro__
                if c.__module__ not in ("builtins",)]
        print(f"    RESULTADO: FALLA -> {type(e).__name__} (modulos: {raiz})")
        print(f"    mensaje: {str(e)[:160]}")
        return False


print("navegadores detectables en PATH:")
for c in ("chrome", "chromium", "msedge"):
    print(f"  {c:10s} {shutil.which(c) or 'no encontrado'}")

existentes = [c for c in CANDIDATOS if os.path.exists(c)]
print(f"\nnavegadores instalados fuera del PATH: {len(existentes)}")
for c in existentes:
    print(f"  {c}")

resultados = {}
os.environ.pop("BROWSER_PATH", None)
resultados["sin BROWSER_PATH"] = intentar("sin BROWSER_PATH (como estaba)")

for c in existentes:
    resultados[f"BROWSER_PATH={os.path.basename(os.path.dirname(os.path.dirname(c)))}"] = \
        intentar(f"apuntando al navegador instalado", {"BROWSER_PATH": c})
    if resultados[[k for k in resultados][-1]]:
        break

print("\n" + "=" * 70)
for k, v in resultados.items():
    print(f"  {'OK   ' if v else 'FALLA'}  {k}")

# limpieza
for f in ("_prueba_kaleido.png",):
    if os.path.exists(f):
        os.remove(f)
print("\n(archivo de prueba eliminado)")
