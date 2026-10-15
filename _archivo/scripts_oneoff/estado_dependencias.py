"""Estado real de las dependencias en el interprete actual.

Uso: python _archivo/scripts_oneoff/estado_dependencias.py
"""

from __future__ import annotations

import importlib.metadata as md

QUIERO = [
    "pandas", "numpy", "matplotlib", "seaborn", "plotly", "kaleido", "duckdb",
    "openpyxl", "nbformat", "streamlit", "scikit-learn", "scipy", "PyYAML",
    "ipython", "pytest", "networkx", "pyvis", "sodapy", "pandera", "nbclient",
    "nbconvert", "jupyter", "jupyter-client", "ipykernel", "altair", "pillow",
    "pyarrow", "requests", "ruff", "notebook",
]

inst = {}
for d in md.distributions():
    nombre = d.metadata["Name"]
    if nombre:
        inst[nombre.lower()] = d.version

print(f"total distribuciones instaladas: {len(inst)}")
print()
print(f"  {'paquete':<18} {'estado'}")
print(f"  {'-'*18} {'-'*16}")
faltan = []
for n in QUIERO:
    v = inst.get(n.lower())
    if v is None:
        faltan.append(n)
        print(f"  {n:<18} NO INSTALADO")
    else:
        print(f"  {n:<18} {v}")
print()
print(f"faltan {len(faltan)}: {', '.join(faltan)}")
