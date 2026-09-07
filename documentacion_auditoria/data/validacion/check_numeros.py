# -*- coding: utf-8 -*-
"""Verificacion de numeros clave para la validacion factica."""
import csv
import json
import subprocess
import pathlib

REPO = pathlib.Path(r"C:\Users\InfoPersonal\OneDrive - Universidad Santo Tomás\Escritorio\consultoria\Observatorio_Ministerio_de_Ciencias_Grupo8")
DATA = pathlib.Path(r"C:\Users\InfoPersonal\OneDrive - Universidad Santo Tomás\Escritorio\consultoria\documentacion_auditoria\data")

print("=" * 70)
print("1) XLSX consolidado: filas reales")
xlsx = REPO / "datos" / "tarea_join" / "investigadores_consolidado.xlsx"
if xlsx.exists():
    import pandas as pd
    df = pd.read_excel(xlsx)
    print(f"   {xlsx.name}: shape={df.shape} -> {df.shape[0]} filas | declarado en tex: 77.237 (texto) / 50.891 (ficha xlsx)")
else:
    print("   XLSX NO EXISTE")

print("=" * 70)
print("2) commits_timeline.csv")
commits_csv = DATA / "commits_timeline.csv"
if commits_csv.exists():
    with open(commits_csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"   filas={len(rows)} | columnas={list(rows[0].keys()) if rows else 'ninguna'}")
else:
    print("   NO EXISTE en data/ — buscando...")
    for p in DATA.rglob("commits_timeline.csv"):
        print("   encontrado:", p)

print("=" * 70)
print("3) git ls-files con filtro .py/.R/.ipynb (excluye .venv)")
out = subprocess.run(
    ["git", "ls-files"], cwd=str(REPO), capture_output=True, text=True
)
files = [l for l in out.stdout.splitlines() if l]
code_files = [l for l in files if l.endswith((".py", ".R", ".ipynb"))]
print(f"   total archivos rastreados: {len(files)}")
print(f"   archivos .py/.R/.ipynb: {len(code_files)}")
for l in sorted(code_files):
    print("     ", l)

print("=" * 70)
print("4) ejecucion_resumen.csv")
ej = DATA / "ejecucion_resumen.csv"
with open(ej, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
n_ok = sum(1 for r in rows if r["estado"] == "OK")
n_err = sum(1 for r in rows if r["estado"] == "ERROR")
print(f"   scripts={len(rows)} | OK={n_ok} | ERROR={n_err}")

print("=" * 70)
print("5) Evidencias de calidad (22 vs 10 atipicos)")
for name in ["calidad_resumen.json", "calidad_atipicos_edad.csv", "calidad_comparacion.csv"]:
    p = REPO / "evidencias" / name
    print(f"   {name}: {'EXISTE' if p.exists() else 'NO EXISTE'}")
p = REPO / "evidencias" / "calidad_resumen.json"
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("   contenido:", json.dumps(d, ensure_ascii=False)[:600])
p = REPO / "evidencias" / "calidad_atipicos_edad.csv"
if p.exists():
    with open(p, encoding="utf-8") as f:
        n = sum(1 for _ in f) - 1
    print(f"   filas atipicos (sin header): {n}")

print("=" * 70)
print("6) docs/manual.ipynb: celdas")
nb = REPO / "docs" / "manual.ipynb"
if nb.exists():
    nbjson = json.loads(nb.read_text(encoding="utf-8"))
    cells = nbjson.get("cells", [])
    md_c = sum(1 for c in cells if c["cell_type"] == "markdown")
    code_c = sum(1 for c in cells if c["cell_type"] == "code")
    ejec = [c for c in cells if c.get("execution_count") is not None]
    print(f"   celdas totales={len(cells)} | md={md_c} | code={code_c} | con execution_count={len(ejec)}")
else:
    print("   NO EXISTE")

print("=" * 70)
print("7) Commits en git (contador real)")
out2 = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=str(REPO), capture_output=True, text=True)
print("   rev-list --count HEAD:", out2.stdout.strip() or out2.stderr.strip()[:200])
