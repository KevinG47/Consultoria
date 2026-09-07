# -*- coding: utf-8 -*-
"""Verificaciones adicionales: convocatorias XLSX, tamanos, log errores, sprint4 figs."""
import pathlib, re

REPO = pathlib.Path(r"C:\Users\InfoPersonal\OneDrive - Universidad Santo Tomás\Escritorio\consultoria\Observatorio_Ministerio_de_Ciencias_Grupo8")
DATA = pathlib.Path(r"C:\Users\InfoPersonal\OneDrive - Universidad Santo Tomás\Escritorio\consultoria\documentacion_auditoria\data")

import pandas as pd

print("=" * 70)
print("1) Convocatorias en el XLSX real")
df = pd.read_excel(REPO / "datos" / "tarea_join" / "investigadores_consolidado.xlsx")
print("   shape:", df.shape)
for c in ["ANO_CONVO", "ID_CONVOCATORIA"]:
    if c in df.columns:
        vc = df[c].value_counts().sort_index()
        print(f"   {c}: {dict(vc)}")
        if c == "ID_CONVOCATORIA":
            print(f"   n convocatorias unicas: {df[c].nunique()}")

print("=" * 70)
print("2) Tamaño XLSX y CSV paralelo")
print(f"   xlsx: { (REPO/'datos'/'tarea_join'/'investigadores_consolidado.xlsx').stat().st_size/1e6:.1f} MB")
p = REPO / "datos" / "tarea_join" / "investigadores_consolidado.csv"
print(f"   csv paralelo existe: {p.exists()}")

print("=" * 70)
print("3) artifacts/sprint4_diversidad contenido")
d = REPO / "artifacts" / "sprint4_diversidad"
print("   ", sorted(x.name for x in d.iterdir()) if d.exists() else "NO EXISTE")

print("=" * 70)
print("4) duckdb_resumen_modelo.txt encabezado")
p = REPO / "evidencias" / "duckdb_resumen_modelo.txt"
if p.exists():
    txt = p.read_text(encoding="utf-8")
    print("   primeras 2 lineas:", txt.splitlines()[:2])
    print("   n consultas (separadores):", txt.count("-----"))
else:
    print("   NO EXISTE")

print("=" * 70)
print("5) Errores en ejecucion_log.txt (secciones ERROR)")
log = (DATA / "ejecucion_log.txt").read_text(encoding="utf-8", errors="replace")
# el log tiene espaciado raro (UTF-16?), normalizar
log_clean = log.replace("\x00", "")
secciones = re.split(r"={3,}\s*(sprint\S+)", log_clean)
# buscar lineas con ERROR/EXIT=1/Traceback
for m in re.finditer(r"===+\s*(sprint\S+)\s*===+", log_clean):
    pass
bloques = re.split(r"(={3,}\s*sprint[0-9a-z_]+\.py\s*={3,})", log_clean)
errores = []
for i in range(1, len(bloques), 2):
    nombre = bloques[i].strip("= ")
    cuerpo = bloques[i+1] if i+1 < len(bloques) else ""
    exit_line = [l for l in cuerpo.splitlines() if "EXIT=" in l]
    trace = [l for l in cuerpo.splitlines() if ("Error" in l or "Traceback" in l or "kaleido" in l.lower() or "FileNotFound" in l or "Unicode" in l)]
    errores.append((nombre, exit_line, trace[:6]))
for nombre, exit_line, trace in errores:
    if exit_line and "1" in exit_line[0]:
        print(f"   {nombre}")
        print(f"     EXIT: {exit_line[0].strip()}")
        for t in trace[:6]:
            print(f"     {t.strip()[:160]}")
    elif not exit_line:
        print(f"   {nombre}: sin linea EXIT (bloque incompleto)")

print("=" * 70)
print("6) Versiones en pyproject.toml")
pp = (REPO / "pyproject.toml").read_text(encoding="utf-8")
for dep in ["duckdb", "networkx", "pyvis", "streamlit", "openpyxl", "pandas", "matplotlib", "seaborn"]:
    m = re.search(rf'^\s*{dep}\s*=\s*["\^~]?([0-9^<>=. ]+)', pp, re.M)
    print(f"   {dep}: {m.group(1).strip() if m else 'NO DECLARADO'}")

print("=" * 70)
print("7) poetry.lock: openpyxl presente?")
lock = REPO / "poetry.lock"
if lock.exists():
    lt = lock.read_text(encoding="utf-8")
    print("   openpyxl en poetry.lock:", "name = \"openpyxl\"" in lt)
    print("   duckdb en poetry.lock:", "name = \"duckdb\"" in lt)
else:
    print("   poetry.lock NO existe")
