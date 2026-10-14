# -*- coding: utf-8 -*-
"""Busca como configurar el navegador que usa kaleido 1.x (choreographer)."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

base = Path(sys.prefix) / "Lib" / "site-packages"
PAT_ENV = re.compile(r"""environ(?:\.get)?\s*[\[\(]\s*["']([A-Za-z_]{4,})["']""")
PAT_ENV2 = re.compile(r"""getenv\s*\(\s*["']([A-Za-z_]{4,})["']""")

for pkg in ["kaleido", "choreographer"]:
    d = base / pkg
    if not d.exists():
        print(f"=== {pkg}: no existe ===")
        continue
    print(f"=== {pkg} ===")
    vistos = set()
    for f in sorted(d.rglob("*.py")):
        t = f.read_text(encoding="utf-8", errors="replace")
        for pat in (PAT_ENV, PAT_ENV2):
            for m in pat.finditer(t):
                clave = (f.relative_to(d).as_posix(), m.group(1))
                if clave not in vistos:
                    vistos.add(clave)
                    print(f"  {clave[0]:34s} {clave[1]}")

print("\n=== API publica de kaleido ===")
import kaleido  # noqa: E402
print("  kaleido:", [x for x in dir(kaleido) if not x.startswith("_")])

print("\n=== firma de kaleido.Kaleido / write_fig ===")
import inspect  # noqa: E402
for nombre in ("Kaleido", "write_fig", "start_sync_server"):
    obj = getattr(kaleido, nombre, None)
    if obj is not None:
        try:
            print(f"  {nombre}{inspect.signature(obj)}")
        except Exception as e:
            print(f"  {nombre}: {type(e).__name__}")

print("\n=== opciones de navegador en choreographer ===")
try:
    from choreographer.browsers import chromium
    print("  chromium:", [x for x in dir(chromium) if not x.startswith("_")][:25])
    for nombre in ("ChromiumOptions", "ChromiumBrowser"):
        obj = getattr(chromium, nombre, None)
        if obj is not None:
            print(f"  {nombre} campos: "
                  f"{[x for x in dir(obj) if not x.startswith('_')][:20]}")
except Exception as e:
    print("  ", type(e).__name__, e)
