# -*- coding: utf-8 -*-
"""
probar_librerias_reales.py
==========================

Ejecuta los 6 scripts arreglados de `repo_mejorado/` con las librerias REALES
(seaborn, plotly, kaleido, duckdb, openpyxl...), sin los dobles de prueba de
`_stubs/`.

Diferencia con `verificar_arreglos.py`
--------------------------------------
- `verificar_arreglos.py` usa **dobles** porque se escribio cuando el entorno no
  tenia las dependencias. Prueba el flujo de control y los arreglos.
- Este script usa **las librerias de verdad**: prueba tambien el dibujo, la
  exportacion de imagenes y las consultas. Es la prueba fuerte.

Se ejecuta sobre una COPIA DESECHABLE (`_prueba_ejecucion`) porque los scripts
escriben figuras y CSV: `repo_mejorado/` conserva la evidencia original del
proyecto auditado y no debe quedar alterado por una corrida de prueba.

Requisitos de datos
-------------------
- Consolidado: `datos/tarea_join/investigadores_consolidado.xlsx` (versionado).
  Se usa la ruta real de `cargar_consolidado()`, que ahora si puede leer el XLSX
  porque openpyxl esta instalado.
- `datos/processed/observatorio.duckdb`: se copia del clon local si existe, para
  que `sprint5_duckdb.py` llegue a la comprobacion de produccion en lugar de
  pararse antes.
- `datos/raw/produccion_grupos.csv` (~1,2 GB): **no existe** y no se puede
  descargar sin red. Los 3 scripts de produccion deben salir con codigo 3.

Uso:  python datos_originales/probar_librerias_reales.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fs_robusto import borrar_arbol  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
MEJORADO = RAIZ / "datos_originales" / "repo_mejorado"
PRUEBA = RAIZ / "datos_originales" / "_prueba_ejecucion"
CLON = RAIZ / "Observatorio_Ministerio_de_Ciencias_Grupo8"

SCRIPTS = [
    "scripts/sprint6_geografia_institucional.py",
    "scripts/sprint6_sankey_categoria.py",
    "scripts/sprint6_sankey_territorial.py",
    "scripts/sprint5_produccion.py",
    "scripts/sprint6_ocde_composicion.py",
    "scripts/sprint5_duckdb.py",
]

# Lo que cada script declara producir (docstring + codigo)
ESPERADO = {
    "scripts/sprint6_geografia_institucional.py": [
        "artifacts/sprint6_geografia/fig_heatmap_residencia_institucion.png",
        "artifacts/sprint6_geografia/fig_pct_local_por_dpto.png",
        "artifacts/sprint6_geografia/fig_top_destinos_pequenos.png",
        "evidencias/geografia_flujo_completo.csv",
        "evidencias/geografia_resumen_por_dpto_residencia.csv",
        "evidencias/geografia_top_flujos.csv",
    ],
    "scripts/sprint6_sankey_categoria.py": [
        # Los pares dependen de las convocatorias presentes en la entrada. El
        # consolidado versionado tiene 3 (2017/2019/2021), asi que salen 2 pares;
        # los 5 HTML del proyecto auditado se generaron con las 6 convocatorias.
        "evidencias/sankey_transiciones.csv",
        "artifacts/sprint6_sankey/sankey_2017_2019.html",
        "artifacts/sprint6_sankey/sankey_2017_2019.png",
        "artifacts/sprint6_sankey/sankey_2019_2021.html",
        "artifacts/sprint6_sankey/sankey_2019_2021.png",
    ],
    "scripts/sprint6_sankey_territorial.py": [
        "artifacts/sprint6_sankey/sankey_territorial.html",
        "artifacts/sprint6_sankey/sankey_territorial.png",
    ],
    "scripts/sprint5_produccion.py": [
        "evidencias/produccion_resumen_cobertura.json",
        "evidencias/produccion_productividad_por_categoria.csv",
    ],
    "scripts/sprint6_ocde_composicion.py": [
        "evidencias/ocde_volumen_por_area.csv",
        "evidencias/ocde_composicion_por_area.csv",
    ],
    "scripts/sprint5_duckdb.py": [
        "evidencias/duckdb_resumen_sprint5.txt",
    ],
}


def inventario(base: Path) -> dict[str, float]:
    return {p.relative_to(base).as_posix(): p.stat().st_mtime
            for p in base.rglob("*") if p.is_file()}


def main() -> int:
    import importlib.metadata as md
    print("LIBRERIAS REALES EN USO")
    for p in ["pandas", "numpy", "matplotlib", "seaborn", "plotly", "kaleido",
              "duckdb", "openpyxl", "nbformat"]:
        try:
            print(f"  {p:12s} {md.version(p)}")
        except Exception:
            print(f"  {p:12s} NO INSTALADA")

    borrar_arbol(PRUEBA)
    print(f"\ncreando copia desechable {PRUEBA.name}/ ...")
    shutil.copytree(MEJORADO, PRUEBA, dirs_exist_ok=True)

    # El .duckdb no esta versionado: se toma del clon para poder ejecutar
    # sprint5_duckdb.py hasta su comprobacion de produccion.
    db = CLON / "datos" / "processed" / "observatorio.duckdb"
    destino_db = PRUEBA / "datos" / "processed" / "observatorio.duckdb"
    if db.exists():
        destino_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db, destino_db)
        print(f"  [datos] observatorio.duckdb copiado del clon "
              f"({db.stat().st_size / 1e6:.2f} MB)")
    else:
        print("  [datos] no hay observatorio.duckdb: sprint5_duckdb.py saldra "
              "con codigo 3 por la base, no por produccion")

    prod = PRUEBA / "datos" / "raw" / "produccion_grupos.csv"
    print(f"  [datos] produccion_grupos.csv presente: "
          f"{prod.exists()}  (se espera False: ~1,2 GB no versionados)")

    antes = inventario(PRUEBA)
    resultados = []
    for script in SCRIPTS:
        print("\n" + "=" * 78)
        print(f"EJECUTANDO {script}")
        print("=" * 78)
        t0 = time.time()
        r = subprocess.run([sys.executable, str(PRUEBA / script)],
                           cwd=str(PRUEBA), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
        dt = time.time() - t0
        salida = ((r.stdout or "") + (r.stderr or ""))
        print(salida.strip()[-2500:] if salida.strip() else "(sin salida)")
        print(f"\n-> EXIT={r.returncode}  ({dt:.1f} s)")

        despues = inventario(PRUEBA)
        generados = [k for k, v in despues.items() if antes.get(k) != v]
        esperados = ESPERADO[script]
        # OJO: que un archivo EXISTA no significa que este script lo haya
        # producido. La copia trae las salidas del proyecto auditado, asi que la
        # primera version de este informe daba "OK" a PNG que nadie regenero. Se
        # distingue regenerado / preexistente / ausente.
        estado_salidas = {}
        for e in esperados:
            existe = (PRUEBA / e).exists()
            if e in generados:
                estado_salidas[e] = "REGENERADO"
            elif existe:
                estado_salidas[e] = "preexistente (no regenerado)"
            else:
                estado_salidas[e] = "AUSENTE"
        print("   salidas declaradas por el script:")
        for e, est in estado_salidas.items():
            print(f"     [{est:28s}] {e}")
        otros = [g for g in generados if g not in esperados]
        if otros:
            print(f"   otros archivos escritos: {len(otros)}")
            for o in sorted(otros)[:8]:
                print(f"     - {o}")
        resultados.append({
            "script": script, "exit": r.returncode, "seg": round(dt, 1),
            "salida": salida, "esperados": esperados,
            "estado_salidas": estado_salidas, "generados": generados,
        })
        antes = despues

    # ------------------------------------------------------------------ informe
    print("\n" + "=" * 78)
    print("INFORME")
    print("=" * 78)
    print(f"  {'script':46s} {'exit':>4} {'s':>6}  regeneradas / preexistentes / ausentes")
    for x in resultados:
        est = list(x["estado_salidas"].values())
        r = sum(1 for e in est if e == "REGENERADO")
        p = sum(1 for e in est if e.startswith("preexistente"))
        a = sum(1 for e in est if e == "AUSENTE")
        print(f"  {x['script']:46s} {x['exit']:>4} {x['seg']:>6}  {r} / {p} / {a}")

    fallos = [x for x in resultados if x["exit"] not in (0, 3)]
    print(f"\n  con EXIT=0 (corre completo)  : "
          f"{sum(1 for x in resultados if x['exit'] == 0)}")
    print(f"  con EXIT=3 (faltan datos)    : "
          f"{sum(1 for x in resultados if x['exit'] == 3)}")
    print(f"  con error real               : {len(fallos)}")

    # Un PNG que no se regenera NO es un fallo del script si el motor de imagen no
    # puede arrancar en este entorno: es una limitacion declarada. Se informa.
    no_png = [s for x in resultados for s, e in x["estado_salidas"].items()
              if s.endswith(".png") and e != "REGENERADO"]
    if no_png:
        print(f"\n  PNG no regenerados: {len(no_png)}")
        print("  -> si el aviso del script habla del navegador, es una limitacion")
        print("     del entorno (kaleido necesita un Chromium que aqui no arranca),")
        print("     no un defecto del script: el HTML y los CSV si se generan.")

    if fallos:
        print("\n  ERRORES REALES:")
        for x in fallos:
            print(f"    [x] {x['script']} EXIT={x['exit']}")
            ultimas = [l for l in x["salida"].strip().splitlines() if l.strip()]
            for l in ultimas[-8:]:
                print(f"        {l[:150]}")

    if PRUEBA.exists():
        borrar_arbol(PRUEBA)
        print(f"\n  copia desechable {PRUEBA.name}/ eliminada")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
