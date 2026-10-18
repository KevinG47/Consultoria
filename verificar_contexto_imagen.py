"""
verificar_contexto_imagen.py
============================

Comprueba que el contexto de la imagen Docker trae TODO lo que las reglas leen,
que esos archivos no llegaron vacios y, en Windows, los hidrata leyendolos.

POR QUE EXISTE
--------------
Este proyecto se construye sobre una carpeta de OneDrive. OneDrive deja los
archivos que no se han abierto como "marcadores de posicion" (archivos en la
nube con el atributo REPARSE_POINT). Docker Desktop, al leer el contexto de
build a traves de Windows, puede recibirlos vacios o no recibirlos, y **el build
no falla**: sale una imagen que arranca y verifica, pero con menos reglas en
verde y sin decir por que.

Paso de verdad: `documentacion_auditoria/data/ejecucion_resumen.csv` llego vacio
a la imagen. R14 compara la cifra de scripts citada en los .tex contra ese
archivo; al no poder contarla, una de sus siete comprobaciones fallo y el estado
quedo en **13 PASA / 2 FALLA (R14 y R17) / 2 ADVERTENCIA** en vez de 15/0/2.
Reproducido a proposito: borrar ese unico archivo -o dejarlo en 0 bytes- da
exactamente ese resultado; borrar las 51 fichas da 3 FALLA, no 2.

QUE HACE
--------
1. Comprueba que estan los archivos que cada regla lee y que ninguno esta vacio
   (los CSV deben tener filas, no solo la cabecera).
2. LEE EL CONTENIDO COMPLETO de esos archivos. En OneDrive, leer es lo que
   hidrata: tras pasar este script, el `docker build` ve bytes locales.
3. Informa de los archivos que Windows marca como REPARSE_POINT / en la nube.

COMO SE USA
-----------
    python verificar_contexto_imagen.py                 # revisa e hidrata el arbol
    python verificar_contexto_imagen.py  <ruta>         # revisa otro contexto

El Dockerfile lo ejecuta despues del COPY, de modo que un contexto incompleto
hace fallar el BUILD (diciendo que archivo) en lugar de producir una imagen que
miente.

Salida: 0 si todo esta, 1 si falta o esta vacio algo.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Cuantas fichas de analisis de codigo tiene el inventario (R9 y R14 lo exigen).
FICHAS_ESPERADAS = 51

# Archivos que alguna regla lee. Si falta uno, alguna regla cambia de veredicto.
REQUERIDOS = {
    "data/commits_timeline.csv": "R5 y R14 cuentan los commits",
    "data/inventario_codigo.csv": "R6, R9 y R14 cuentan los archivos de codigo",
    "data/ejecucion_resumen.csv": "R14 compara la cifra de scripts de los .tex",
    "data/objetivos.yaml": "R1 y R14 leen los criterios",
    "data/glosario.yaml": "R4 comprueba que el glosario se use",
    "data/capas.yaml": "R8 reparte los archivos por capa",
    "data/memoria/git_log_real.csv": "R5: cache versionado del git log real",
    "data/memoria/git_ls_files_real.txt": "R9: cache versionado de git ls-files",
    "data/memoria/commit_auditado.txt": "R7: ancla del commit auditado",
    "data/memoria/rag_indice.json": "R11 y R13: frescura del indice RAG",
    "data/memoria/rag_corpus.jsonl": "R11: cobertura del corpus",
    "data/memoria/grafo_resumen.json": "R10: integridad del grafo",
    "data/memoria/decisiones.yaml": "R15 y R16: bitacora de decisiones",
    "data/memoria/fuentes_externas.yaml": "R16: fuentes externas consultadas",
}

# Bits de atributos de Windows que delatan un archivo en la nube.
BITS_NUBE = {
    0x400: "REPARSE_POINT",
    0x1000: "OFFLINE",
    0x40000: "RECALL_ON_OPEN",
    0x400000: "RECALL_ON_DATA_ACCESS",
}


def _atributos_windows(ruta: Path) -> int | None:
    """
    Atributos reales del archivo, o None si no es Windows.

    Se usa la API de Windows y NO `os.stat().st_file_attributes`: para estos
    archivos de OneDrive Python devuelve 0x80020 (sin el bit de reparse) cuando
    la API devuelve 0x80420 (ARCHIVE + REPARSE_POINT + PINNED). Confiar en
    Python aqui hace que el aviso nunca salte.
    """
    if os.name != "nt":
        return None
    try:
        import ctypes

        return int(ctypes.windll.kernel32.GetFileAttributesW(str(ruta)))
    except Exception:                                   # noqa: BLE001
        return None


def _etiqueta_nube(atributos: int | None) -> str:
    if atributos is None or atributos < 0:
        return ""
    activos = [nombre for bit, nombre in BITS_NUBE.items() if atributos & bit]
    return "+".join(activos)


def _hidratar_y_comprobar(ruta: Path) -> int:
    """
    Lee el archivo entero (en OneDrive, leer hidrata) y devuelve los bytes leidos.

    Devuelve -1 si no se pudo leer.
    """
    leidos = 0
    try:
        with open(ruta, "rb") as fh:
            while True:
                bloque = fh.read(1 << 20)
                if not bloque:
                    break
                leidos += len(bloque)
    except OSError:
        return -1
    return leidos


def _contar_lineas(ruta: Path) -> int:
    try:
        with open(ruta, encoding="utf-8-sig", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return -1


def revisar(raiz: Path) -> tuple[list[str], list[str], list[str]]:
    """Devuelve (problemas, avisos, detalle)."""
    doc = raiz / "documentacion_auditoria"
    if not doc.is_dir():
        return ([f"no existe {doc}"], [], [])

    problemas: list[str] = []
    detalle: list[str] = []
    en_la_nube: list[str] = []

    for rel, motivo in REQUERIDOS.items():
        ruta = doc / rel
        if not ruta.is_file():
            problemas.append(f"FALTA {rel}  ({motivo})")
            continue
        tam_disco = ruta.stat().st_size
        leidos = _hidratar_y_comprobar(ruta)
        if leidos < 0:
            problemas.append(f"NO SE PUDO LEER {rel}  ({motivo})")
            continue
        if tam_disco == 0 or leidos == 0:
            problemas.append(f"VACIO (0 bytes): {rel}  ({motivo})")
            continue
        if leidos != tam_disco:
            problemas.append(
                f"LECTURA INCOMPLETA: {rel} ({leidos} de {tam_disco} bytes)  ({motivo})")
            continue
        if rel.endswith(".csv"):
            lineas = _contar_lineas(ruta)
            if lineas <= 1:                     # solo cabecera, o nada
                problemas.append(
                    f"CSV sin datos ({lineas} linea/s): {rel}  ({motivo})")
                continue
            detalle.append(f"{rel}: {lineas - 1} filas de datos")
        else:
            detalle.append(f"{rel}: {leidos} bytes")
        etiqueta = _etiqueta_nube(_atributos_windows(ruta))
        if etiqueta:
            en_la_nube.append(f"{rel} [{etiqueta}]")

    # 51 fichas de analisis de codigo
    fichas = sorted((doc / "data" / "analisis_codigo").glob("*.json"))
    if len(fichas) != FICHAS_ESPERADAS:
        problemas.append(
            f"fichas de codigo: {len(fichas)} de {FICHAS_ESPERADAS} "
            "(R9 y R14 las cuentan)")
    else:
        detalle.append(f"data/analisis_codigo: {len(fichas)} fichas JSON")
    vacias, nube_fichas = [], 0
    for f in fichas:
        if _hidratar_y_comprobar(f) <= 0:
            vacias.append(f.name)
        if _etiqueta_nube(_atributos_windows(f)):
            nube_fichas += 1
    if vacias:
        problemas.append(f"fichas vacias o ilegibles: {', '.join(vacias[:5])}")
    if nube_fichas:
        en_la_nube.append(f"data/analisis_codigo/*.json [{nube_fichas} fichas]")

    # Corpus: LaTeX, validacion en Markdown y PDF (R10 y R17 exigen los PDF)
    grupos = {
        "latex": ("*.tex", "documentos LaTeX que leen R3, R13 y R14"),
        "data/validacion": ("*.md", "documentos de validacion que leen R13 y R17"),
        "pdf": ("*.pdf", "PDF compilados que exigen R10 y R17"),
    }
    for sub, (patron, motivo) in grupos.items():
        encontrados = [p for p in (doc / sub).rglob(patron) if p.is_file()]
        if not encontrados:
            problemas.append(f"FALTAN {patron} en {sub}/  ({motivo})")
        else:
            detalle.append(f"{sub}/: {len(encontrados)} {patron}")

    avisos = []
    if en_la_nube:
        avisos.append(
            f"{len(en_la_nube)} entrada(s) del contexto estaban en la nube "
            "(OneDrive). Este script ya las leyo, asi que quedan hidratadas para "
            "el build. Si el build volviera a fallar: marca 'Mantener siempre en "
            "este dispositivo' o construye desde una copia fuera de OneDrive.")
    return problemas, avisos, detalle + [f"  en la nube: {x}" for x in en_la_nube[:15]]


def main() -> int:
    raiz = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    print(f"CONTEXTO DE LA IMAGEN: {raiz}")
    problemas, avisos, detalle = revisar(raiz)

    print(f"  comprobados: {len(REQUERIDOS)} archivos de datos + {FICHAS_ESPERADAS} "
          "fichas + latex/ + data/validacion/ + pdf/")
    for linea in detalle:
        print(f"  ok  {linea}")

    for aviso in avisos:
        print(f"\n  [aviso] {aviso}")

    if problemas:
        print(f"\n  [x] {len(problemas)} problema(s):")
        for p in problemas:
            print(f"      - {p}")
        print("\n  Un contexto incompleto NO rompe el build, pero produce una imagen")
        print("  que da 13 PASA / 2 FALLA (R14 y R17) en vez de 15/0/2. Arreglo:")
        print("      1) hidratar los archivos (abrirlos, o 'Mantener siempre en este")
        print("         dispositivo' en OneDrive) y reconstruir; o")
        print("      2) construir desde una copia local fuera de OneDrive:")
        print("         robocopy . C:\\build\\consultoria /MIR /XD .git .venv node_modules")
        return 1

    print("\n  [OK] El contexto trae todo lo que las reglas leen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
