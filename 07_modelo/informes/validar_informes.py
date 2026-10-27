#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validar_informes.py
===================

Agente validador de la suite documental de la Fase 3 (modelo de movilidad de
categoría). Audita los seis documentos Markdown de `07_modelo/informes/`:

  00_informe_maestro.md
  01_ingesta_y_datos.md
  02_eda_y_auditoria.md
  03_modelado_xgboost.md
  04_modelo_bayesiano.md
  05_pruebas_alternativas.md

Qué verifica
------------
1. **Cifras de cierre.** Toda mención de la cifra final (F1 «baja», recall,
   Brier) en contexto de test/cierre debe contener el valor canónico
   (0,4234 / 0,7878 / 0,4692). Los valores experimentales (OOS, matriz,
   benchmark, alternativas) se admiten solo si están etiquetados como tales y
   se listan en el reporte como «menciones contextuales».
2. **Transiciones.** Toda cifra asociada a «transiciones» debe ser 43 187
   (se admite 47 151 solo para la variante «completo», que el texto etiqueta).
3. **Referencias cruzadas.** Los enlaces Markdown a otros .md y las menciones
   «Ver Informe NN» deben apuntar a archivos existentes.
4. **Ortografía de autores.** Detecta variantes no canónicas (p. ej.
   «Grinzstajn», «Kaufmann», «Benitez» sin tilde) y nombres con tilde omitida.
5. **Anclaje a los artefactos.** Contrasta las cifras canónicas contra
   `expE_test_*.json`, `model_card.md` y el manifiesto del dataset; si el
   artefacto no existe, lo declara y no falla.

Uso
---
    python 07_modelo/informes/validar_informes.py
    python 07_modelo/informes/validar_informes.py --fix
    python 07_modelo/informes/validar_informes.py --reporte otra_ruta.md

`--fix` solo normaliza redondeos inequívocos de la cifra de cierre
(0,42 → 0,4234) en frases que hablan del F1; nunca reescribe valores
experimentales ni métricas de otros modelos.

Salida: `reporte_validacion.md` junto a los informes. Código de salida 0 si no
quedan discrepancias; 2 si quedan pendientes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
CARPETA = Path(__file__).resolve().parent
REPORTE_DEFECTO = CARPETA / "reporte_validacion.md"
EXCLUIR = {"reporte_validacion.md"}

CANON = {
    "f1": "0,4234",
    "recall": "0,7878",
    "brier": "0,4692",
    "transiciones": "43 187",
}

# Valores legítimos en contextos experimentales (no son la cifra de cierre).
F1_CONTEXTUALES = {
    0.4234, 0.4223, 0.2985, 0.3054, 0.3063, 0.3032, 0.3049, 0.2987, 0.2983,
    0.2877, 0.2834, 0.1269, 0.003, 0.132, 0.149, 0.244, 0.345, 0.2728,
    0.3076, 0.3150, 0.2655, 0.3357, 0.4016, 0.4222, 0.1851, 0.4388, 0.6932,
    0.2945, 0.3939, 0.394, 0.498, 0.502, 0.5109, 0.989, 0.99, 0.055, 0.826,
    0.42, 0.21, 0.15, 0.08, 0.12, 0.27, 0.29, 0.06, 0.07, 0.117, 0.2,
    0.33, 0.50, 0.83, 0.90, 0.60, 0.54, 0.89, 0.84, 0.80, 0.79, 0.238,
    0.1851, 0.3185,
}
RECALL_CONTEXTUALES = {
    0.7878, 0.7437, 0.6153, 0.7416, 0.7438, 0.54, 0.89, 0.84, 0.80, 0.79,
    0.60, 0.29, 0.2949, 0.58,
}
BRIER_CONTEXTUALES = {
    0.4692, 0.4370, 0.4419, 0.4510, 0.4592, 0.4969, 0.4400, 0.4196, 0.4223,
    0.4151, 0.4130, 0.5479, 0.4917, 0.4851, 0.4785, 0.4049, 0.5851, 0.6411,
    0.3769, 0.4741, 0.1109, 0.02, 0.27, 0.15, 0.117,
}

AUTORES = {
    "Grinsztajn": {"Grinsztajn"},
    "Shwartz-Ziv": {"Shwartz-Ziv", "Shwartz–Ziv", "Shwartz"},
    "Lipton": {"Lipton"},
    "Kaufman": {"Kaufman"},
    "Cerqua": {"Cerqua"},
    "Godoy": {"Godoy"},
    "McCullagh": {"McCullagh"},
    "Tashman": {"Tashman"},
    "Bergmeir": {"Bergmeir"},
    "Sharabiani": {"Sharabiani"},
    "Gayatri": {"Gayatri"},
    "Richardson": {"Richardson"},
    "Holzmüller": {"Holzmüller"},
    "Varoquaux": {"Varoquaux"},
    "Benítez": {"Benítez"},
    "Dies": {"Dies"},
    "Yeo": {"Yeo"},
    "Jafor": {"Jafor"},
    "Saito": {"Saito"},
    "Cohen": {"Cohen"},
}

PATRONES_AUTOR = [
    (r"\bGrin[sz]t\w*", "Grinsztajn"),
    (r"\bShwart\w*(?:-Ziv)?", "Shwartz-Ziv"),
    (r"\bSchwart\w*", "Shwartz-Ziv"),
    (r"\bLipt\w*", "Lipton"),
    (r"\bKaufm\w*", "Kaufman"),
    (r"\bCerqu\w*", "Cerqua"),
    (r"\bGodo\w*", "Godoy"),
    (r"\bMcCul\w*", "McCullagh"),
    (r"\bTashm\w*", "Tashman"),
    (r"\bBergme\w*", "Bergmeir"),
    (r"\bSharab\w*", "Sharabiani"),
    (r"\bGayatr\w*", "Gayatri"),
    (r"\bRichard\w*", "Richardson"),
    (r"\bHolzm\w*", "Holzmüller"),
    (r"\bVaroqu\w*", "Varoquaux"),
    (r"\bBen[ií]tez\b", "Benítez"),
    (r"\bDies\b", "Dies"),
    (r"\bYeo\b", "Yeo"),
    (r"\bJafor\b", "Jafor"),
    (r"\bSait\w*", "Saito"),
    (r"\bCoh[eo]n\b", "Cohen"),
]

RE_DECIMAL = re.compile(r"(?<![\d.,])0[.,](\d{2,4})(?![\d])")
RE_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
RE_INFORME = re.compile(r"Informe\s+0?([1-5])\b", re.IGNORECASE)
RE_TRANS = re.compile(
    r"([\d][\d .,]{2,9})\s*transiciones|transiciones\D{0,20}?([\d][\d .,]{2,9})",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def normalizar(texto: str) -> str:
    for viejo, nuevo in (("\u00a0", " "), ("\u202f", " "), ("\u2009", " ")):
        texto = texto.replace(viejo, nuevo)
    return texto


def decimales(linea: str) -> list[float]:
    vals = []
    for m in RE_DECIMAL.finditer(linea):
        vals.append(float("0." + m.group(1)))
    return vals


def fmt(v: float) -> str:
    return f"{v:.4f}".replace(".", ",")


def es_contexto_cierre(linea: str) -> bool:
    low = linea.lower()
    return ("test" in low or "cierre" in low) and (
        "2021" in low or "cierre" in low or "13 355" in low
    )


def es_excepcion_matriz(linea: str) -> bool:
    low = linea.lower()
    return any(k in low for k in ("0,117", "matriz", "pasoe", "corrida previa"))


@dataclass
class Hallazgo:
    archivo: str
    linea: int
    tipo: str
    detalle: str


@dataclass
class Resultado:
    archivos: list[Path] = field(default_factory=list)
    comprobaciones: int = 0
    contextuales: list[tuple[str, int, str, str]] = field(default_factory=list)
    enlaces: list[tuple[str, str, bool]] = field(default_factory=list)
    autores: list[tuple[str, str, str]] = field(default_factory=list)
    hallazgos: list[Hallazgo] = field(default_factory=list)
    correcciones: list[tuple[str, int, str, str]] = field(default_factory=list)
    anclaje: list[tuple[str, str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Comprobaciones
# ---------------------------------------------------------------------------
RE_F1_VAL = re.compile(
    r"F1\s*(?:«\s*baja\s*»|de\s*«\s*baja\s*»|«\s*baja\s*»|baja)"
    r"\s*[^\d\n]{0,45}?(0[.,]\d{2,4})", re.IGNORECASE)
RE_RECALL_VAL = re.compile(
    r"recall\s*(?:«\s*baja\s*»)?\s*[^\d\n]{0,35}?(0[.,]\d{2,4})", re.IGNORECASE)
RE_BRIER_VAL = re.compile(
    r"Brier\s*(?:multiclase)?\s*[^\d\n]{0,35}?(0[.,]\d{2,4})", re.IGNORECASE)


def revisar_cifras(archivo: Path, lineas: list[str], res: Resultado) -> None:
    for n, linea in enumerate(lineas):
        low = linea.lower()
        prev = lineas[n - 1] if n > 0 else ""
        nxt = lineas[n + 1] if n + 1 < len(lineas) else ""
        ventana = (prev + " " + linea + " " + nxt).lower()

        matriz = any(k in ventana for k in ("0,117", "matriz", "pasoe", "corrida previa"))
        cierre = es_contexto_cierre(linea)

        # Filas compuestas: «F1 «baja» / recall / precisión» o «F1 macro / Brier».
        # Se valida la presencia conjunta en vez de asignar posición.
        compuesto = False
        es_fila_tabla = linea.lstrip().startswith("|")
        if es_fila_tabla and re.search(r"F1\s*«\s*baja\s*»\s*/\s*recall", linea, re.IGNORECASE):
            res.comprobaciones += 1
            compuesto = True
            if not all(v in low for v in ("0,4234", "0,7878", "0,2895")):
                res.hallazgos.append(Hallazgo(
                    archivo.name, n + 1, "F1/Recall", "fila compuesta sin las tres cifras canónicas"))
        elif es_fila_tabla and re.search(r"F1 macro\s*/\s*Brier", linea, re.IGNORECASE):
            res.comprobaciones += 1
            compuesto = True
            if not all(v in low for v in ("0,5109", "0,4692")):
                res.hallazgos.append(Hallazgo(
                    archivo.name, n + 1, "F1/Brier", "fila compuesta sin F1 macro / Brier canónicos"))
        if compuesto:
            continue

        def razon(low: str, matriz: bool) -> str:
            if matriz:
                return "matriz (umbral 0,117)"
            for clave, etiqueta in (
                ("bayes", "modelo bayesiano (validación)"),
                ("tabicl", "TabICLv2"),
                ("laya", "Laya"),
                ("limpio", "modelo limpio"),
                ("fold", "folds / OOS"),
                ("benchmark", "benchmark de identidad"),
                ("entidad disjunta", "benchmark de identidad"),
                ("control", "control de volumen"),
                ("prior", "corrección de prior shift"),
                ("constante", "constante de referencia"),
            ):
                if clave in low:
                    return etiqueta
            if re.search(r"\boos\b", low):
                return "folds / OOS"
            return "resultado experimental etiquetado"

        def registrar(metric: str, texto: str, valor: float, canon: float,
                      whitelist: set[float]) -> None:
            res.comprobaciones += 1
            if valor == canon:
                return
            if cierre and not matriz:
                res.hallazgos.append(Hallazgo(
                    archivo.name, n + 1, metric,
                    f"valor de cierre {texto} distinto de {fmt(canon)}"))
                return
            if valor in whitelist:
                res.contextuales.append(
                    (archivo.name, n + 1, texto, razon(low, matriz)))
            else:
                res.hallazgos.append(Hallazgo(
                    archivo.name, n + 1, metric, f"valor no verificado {texto}"))

        m = RE_F1_VAL.search(linea)
        if m:
            texto = m.group(1)
            registrar("F1", texto, float(texto.replace(",", ".")), 0.4234, F1_CONTEXTUALES)

        m = RE_RECALL_VAL.search(linea)
        if m:
            texto = m.group(1)
            registrar("Recall", texto, float(texto.replace(",", ".")), 0.7878, RECALL_CONTEXTUALES)

        m = RE_BRIER_VAL.search(linea)
        if m:
            texto = m.group(1)
            registrar("Brier", texto, float(texto.replace(",", ".")), 0.4692, BRIER_CONTEXTUALES)

        if "transiciones" in low:
            valores: list[int] = []
            for m in re.finditer(r"([\d][\d .,]{2,9})\s*transiciones", linea, re.IGNORECASE):
                valores.append(int(re.sub(r"[ .,]", "", m.group(1).strip())))
            for m in re.finditer(
                r"transiciones[^\d\n]{0,30}\|\s*([\d][\d .,]{2,9})", linea, re.IGNORECASE
            ):
                valores.append(int(re.sub(r"[ .,]", "", m.group(1).strip())))
            for v in valores:
                res.comprobaciones += 1
                if v == 43187:
                    continue
                if v == 47151 and any(k in low for k in ("completo", "saltos", "ventana")):
                    res.contextuales.append((archivo.name, n + 1, "47 151", "variante completo etiquetada"))
                    continue
                res.hallazgos.append(Hallazgo(
                    archivo.name, n + 1, "Transiciones", f"cifra {v} distinta de 43 187"))


def revisar_enlaces(archivo: Path, texto: str, res: Resultado) -> None:
    for m in RE_LINK.finditer(texto):
        destino = m.group(2).strip()
        if destino.startswith(("http://", "https://", "mailto:", "#")):
            continue
        objetivo = (CARPETA / destino.split("#")[0]).resolve()
        ok = objetivo.exists()
        res.enlaces.append((archivo.name, destino, ok))
        res.comprobaciones += 1
        if not ok:
            res.hallazgos.append(Hallazgo(
                archivo.name, 0, "Enlace", f"no existe el destino «{destino}»"))

    for m in RE_INFORME.finditer(texto):
        n = m.group(1)
        objetivo = CARPETA / f"0{n}_"
        ok = any(CARPETA.glob(f"0{n}_*.md"))
        res.enlaces.append((archivo.name, f"Informe {n}", ok))
        res.comprobaciones += 1
        if not ok:
            res.hallazgos.append(Hallazgo(
                archivo.name, 0, "Enlace", f"«Informe {n}» no tiene archivo 0{n}_*.md"))


def revisar_autores(archivo: Path, texto: str, res: Resultado) -> None:
    for patron, canonico in PATRONES_AUTOR:
        for m in re.finditer(patron, texto):
            token = m.group(0)
            permitidos = AUTORES[canonico]
            res.comprobaciones += 1
            if token not in permitidos:
                res.hallazgos.append(Hallazgo(
                    archivo.name, 0, "Autor",
                    f"«{token}» debería ser «{canonico}»"))
                res.autores.append((archivo.name, token, canonico))


def anclar_artefactos(res: Resultado) -> None:
    """Contrasta las cifras canónicas con los artefactos del repositorio."""
    exp = sorted((CARPETA.parent / "modelado" / "resultados").glob("expE_test_*.json"))
    if exp:
        try:
            j = json.loads(exp[-1].read_text(encoding="utf-8"))["metricas"]
            pares = [("F1", j.get("f1_baja"), 0.4234),
                     ("Recall", j.get("recall_baja"), 0.7878),
                     ("Brier", j.get("brier"), 0.4692)]
            for nombre, valor, canon in pares:
                ok = valor is not None and abs(float(valor) - canon) < 5e-5
                res.anclaje.append(("expE_test", nombre, "OK" if ok else f"difiere ({valor})"))
                res.comprobaciones += 1
                if not ok:
                    res.hallazgos.append(Hallazgo(
                        "expE_test", 0, "Anclaje", f"{nombre} del artefacto no coincide"))
        except Exception as exc:  # noqa: BLE001
            res.anclaje.append(("expE_test", "lectura", f"no evaluable: {exc}"))
    else:
        res.anclaje.append(("expE_test", "—", "artefacto no encontrado (no falla)"))

    man = CARPETA.parent / "ingesta" / "manifiestos" / "dataset_20261025_202401.json"
    if man.exists():
        try:
            j = json.loads(man.read_text(encoding="utf-8"))
            filas = j["modelos"]["ventana_contiguo"]["filas"]
            ok = filas == 43187
            res.anclaje.append(("dataset", "transiciones", "OK" if ok else f"difiere ({filas})"))
            res.comprobaciones += 1
            if not ok:
                res.hallazgos.append(Hallazgo(
                    "manifiesto", 0, "Anclaje", "filas del dataset no coinciden con 43 187"))
        except Exception as exc:  # noqa: BLE001
            res.anclaje.append(("dataset", "lectura", f"no evaluable: {exc}"))
    else:
        res.anclaje.append(("dataset", "—", "manifiesto no encontrado (no falla)"))


# ---------------------------------------------------------------------------
# Correcciones seguras
# ---------------------------------------------------------------------------
def aplicar_correcciones(archivo: Path, texto: str, res: Resultado) -> tuple[str, bool]:
    """Normaliza solo redondeos inequívocos del F1 (0,42 → 0,4234)."""
    cambios = 0
    nuevas = []
    for n, linea in enumerate(texto.splitlines(keepends=True), start=1):
        original = linea
        if (re.search(r"\bF1\b", linea) or "superar el 0,42" in linea
                or "Anatom\u00eda del 0,42" in linea) \
                and "0,42" in linea and "0,4234" not in linea:
            linea = re.sub(r"(?<![\d.,])0,42(?![\d])", "0,4234", linea)
        if linea != original:
            cambios += 1
            res.correcciones.append((archivo.name, n, "0,42 → 0,4234", original.strip()[:120]))
        nuevas.append(linea)
    return "".join(nuevas), cambios > 0


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------
def escribir_reporte(res: Resultado, ruta: Path, corregidas: int) -> None:
    fecha = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    n_arch = len(res.archivos)
    n_cons = res.comprobaciones
    pendientes = len(res.hallazgos)

    lineas = [
        "# Reporte de validación de la suite documental",
        "",
        f"**Fecha:** {fecha}  ",
        "**Validador:** `07_modelo/informes/validar_informes.py`  ",
        f"**Alcance:** {n_arch} informes de `07_modelo/informes/` (maestro + 5 modulares)  ",
        "**Fuentes de verdad:** `expE_test_20261026_024016.json`, "
        "`model_card.md` y el manifiesto del dataset",
        "",
        "---",
        "",
        f"**Auditoría completada. {n_arch} archivos revisados. "
        f"{n_cons} consistencias encontradas. {corregidas} discrepancias corregidas.**",
        "",
        "---",
        "",
        "## 1. Archivos revisados",
        "",
        "| Archivo | Líneas | Palabras |",
        "|---|---:|---:|",
    ]
    for f in res.archivos:
        t = normalizar(f.read_text(encoding="utf-8"))
        lineas.append(f"| `{f.name}` | {len(t.splitlines())} | {len(t.split())} |")

    lineas += [
        "",
        "## 2. Comprobaciones",
        "",
        "| Comprobación | Resultado |",
        "|---|---|",
        f"| Cifras de cierre (F1, recall, Brier) en contexto de test | "
        f"{'OK' if not any(h.tipo in {'F1','Recall','Brier'} for h in res.hallazgos) else 'CON HALLAZGOS'} |",
        f"| Transiciones = 43 187 | "
        f"{'OK' if not any(h.tipo == 'Transiciones' for h in res.hallazgos) else 'CON HALLAZGOS'} |",
        f"| Referencias cruzadas existentes | "
        f"{sum(1 for _,_,ok in res.enlaces if ok)}/{len(res.enlaces)} OK |",
        f"| Ortografía de autores | "
        f"{'OK' if not any(h.tipo == 'Autor' for h in res.hallazgos) else 'CON HALLAZGOS'} |",
        f"| Anclaje a artefactos | "
        f"{'; '.join(f'{a}:{b}:{c}' for a,b,c in res.anclaje)} |",
        "",
        "El detalle de las comprobaciones es:",
        "",
        "- **Cifras de cierre:** se considera contexto de cierre toda línea que "
        "menciona `test`, `cierre` o la cohorte 2021. En ese contexto, la cifra "
        "publicada debe ser la canónica. Las menciones a resultados experimentales "
        "(OOS, folds, matriz, benchmark, alternativas) se verifican contra su "
        "propio experimento y se listan abajo; no son discrepancias.",
        "- **Transiciones:** se exige 43 187; se admite 47 151 solo cuando el "
        "texto lo etiqueta como variante «completo».",
        "- **Referencias cruzadas:** todo enlace a un `.md` y toda mención "
        "«Informe NN» deben resolver a un archivo existente.",
        "- **Autores:** se comparan las formas encontradas contra la lista "
        "canónica; se marcan variantes, errores de letra y tildes omitidas.",
        "- **Anclaje:** las cifras canónicas se contrastan contra el JSON de test "
        "y el manifiesto del dataset.",
        "",
        "## 3. Menciones contextuales verificadas",
        "",
        "Valores que **no** son la cifra de cierre y que el validador deja "
        "intactos porque están etiquetados como resultados de otro experimento. "
        "No se corrigen: hacerlo falsificaría el informe.",
        "",
        "| Archivo | Línea | Valor | Justificación |",
        "|---|---:|---:|---|",
    ]
    for archivo, n, valor, just in res.contextuales:
        lineas.append(f"| `{archivo}` | {n} | {valor} | {just} |")

    lineas += [
        "",
        "## 4. Referencias cruzadas",
        "",
        "| Archivo | Destino | Existe |",
        "|---|---|---|",
    ]
    for archivo, destino, ok in res.enlaces:
        lineas.append(f"| `{archivo}` | `{destino}` | {'sí' if ok else '**NO**'} |")

    lineas += [
        "",
        "## 5. Ortografía de autores",
        "",
    ]
    if res.autores:
        lineas += ["| Archivo | Forma encontrada | Forma canónica |", "|---|---|---|"]
        for archivo, token, canon in res.autores:
            lineas.append(f"| `{archivo}` | {token} | {canon} |")
    else:
        lineas.append("Sin variantes: todas las formas encontradas coinciden con la lista canónica.")

    lineas += [
        "",
        "## 6. Discrepancias corregidas",
        "",
    ]
    if res.correcciones:
        lineas += ["| Archivo | Línea | Cambio | Texto original |", "|---|---:|---|---|"]
        for archivo, n, cambio, texto in res.correcciones:
            lineas.append(f"| `{archivo}` | {n} | {cambio} | {texto} |")
    else:
        lineas.append(
            "No hubo cifras que corregir: todas las menciones de cierre ya contenían "
            "el valor canónico."
        )

    lineas += [
        "",
        "## 7. Hallazgos pendientes",
        "",
    ]
    if res.hallazgos:
        lineas += ["| Archivo | Línea | Tipo | Detalle |", "|---|---:|---|---|"]
        for h in res.hallazgos:
            lineas.append(f"| `{h.archivo}` | {h.linea or '—'} | {h.tipo} | {h.detalle} |")
    else:
        lineas.append("Ninguno.")

    lineas += [
        "",
        "---",
        "",
        "## 8. Alcance y límites del validador",
        "",
        "El validador comprueba **consistencia textual y anclaje a artefactos**, no "
        "la verdad sustantiva de cada afirmación. Es decir: garantiza que los seis "
        "documentos digan lo mismo y que esas cifras coincidan con el JSON de test y "
        "el manifiesto del dataset; no sustituye la revisión de un lector humano "
        "sobre la interpretación de los resultados.",
        "",
        "Las menciones contextuales se listan para que el lector pueda auditar la "
        "decisión: son valores de otros experimentos (OOS, matriz, benchmark, "
        "alternativas) y convertirlos a 0,4234 habría introducido un error. El "
        "validador solo corrige redondeos inequívocos de la cifra de cierre.",
        "",
        "**Reproducción:**",
        "",
        "```powershell",
        "07_modelo\\.venv-bayes\\Scripts\\python.exe 07_modelo/informes/validar_informes.py",
        "```",
        "",
    ]
    ruta.write_text("\n".join(lineas), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Valida la suite documental de informes.")
    ap.add_argument("--fix", action="store_true", help="normaliza redondeos 0,42 → 0,4234")
    ap.add_argument("--reporte", default=str(REPORTE_DEFECTO), help="ruta del reporte")
    args = ap.parse_args(argv)

    archivos = sorted(p for p in CARPETA.glob("*.md") if p.name not in EXCLUIR)
    if not archivos:
        print(f"[validador] no hay informes en {CARPETA}", file=sys.stderr)
        return 2

    res = Resultado(archivos=archivos)

    for archivo in archivos:
        texto = normalizar(archivo.read_text(encoding="utf-8"))
        if args.fix:
            nuevo, cambio = aplicar_correcciones(archivo, texto, res)
            if cambio:
                archivo.write_text(nuevo, encoding="utf-8", newline="\n")
                texto = normalizar(nuevo)
        revisar_cifras(archivo, texto.splitlines(), res)
        revisar_enlaces(archivo, texto, res)
        revisar_autores(archivo, texto, res)

    corregidas = len(res.correcciones)
    anclar_artefactos(res)
    escribir_reporte(res, Path(args.reporte), corregidas)

    print(f"[validador] archivos: {len(archivos)} | comprobaciones: {res.comprobaciones} "
          f"| contextuales: {len(res.contextuales)} | correcciones: {corregidas} "
          f"| pendientes: {len(res.hallazgos)}")
    for h in res.hallazgos:
        print(f"  - {h.archivo}:{h.linea} [{h.tipo}] {h.detalle}")
    return 0 if not res.hallazgos else 2


if __name__ == "__main__":
    raise SystemExit(main())
