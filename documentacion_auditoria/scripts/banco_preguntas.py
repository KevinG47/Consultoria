# -*- coding: utf-8 -*-
"""
banco_preguntas.py
==================

Evaluación del RAG del proyecto con un banco de 20 preguntas de respuesta conocida.

Qué hace
--------
1. Carga el índice semántico ya construido (NO lo reconstruye: solo lee).
2. Consulta el RAG para cada una de las 20 preguntas (top-3 fragmentos).
3. Guarda, por pregunta: texto, grupo (A/B/C), respuesta esperada, top-1
   (documento/sección/ruta/score/extracto), top-3, si el fragmento contiene la
   respuesta esperada y, cuando no está en el top-3, en qué posición del
   ranking completo aparece (o si no está en el corpus). La comprobación se
   hace contra el texto COMPLETO del fragmento, no contra el extracto de 400
   caracteres que devuelve la API.
4. Escribe todo en `data/memoria/resultados_banco_preguntas.json`.
5. Imprime un resumen con el reparto de scores (>0,15 alto · 0,05–0,15 medio ·
   <0,05 bajo), la tasa de acierto por grupo y la cobertura del corpus.

API usada
---------
`memoria.rag.MemoriaSemantica().cargar().consultar(pregunta, k=3)`
-> lista de dicts con: puntaje, documento, coleccion, seccion, ruta, extracto,
   n_palabras.

Uso
---
    python documentacion_auditoria/scripts/banco_preguntas.py
"""

from __future__ import annotations

import io
import json
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# --- rutas -----------------------------------------------------------------
DOC = Path(__file__).resolve().parents[1]          # documentacion_auditoria/
SRC = DOC / "src"
SALIDA = DOC / "data" / "memoria" / "resultados_banco_preguntas.json"
sys.path.insert(0, str(SRC))

from memoria import rag  # noqa: E402


# --- banco de preguntas ----------------------------------------------------
# claves: fragmentos literales que, si aparecen en el fragmento recuperado,
# acreditan que el RAG devolvió el dato (se comparan normalizados: sin
# mayúsculas, sin acentos y sin espacios/puntos/guiones).
BANCO: list[dict] = [
    # ---------------- GRUPO A: deberían estar en el corpus ----------------
    {"id": 1, "grupo": "A", "pregunta": "¿Cuántos registros declara el dataset bqtm-4y2h?",
     "esperado": "77 237", "claves": ["77237"]},
    {"id": 2, "grupo": "A", "pregunta": "¿Cuántas convocatorias reconoce MinCiencias?",
     "esperado": "6 (2013-2021)", "claves": ["6 convocatorias", "seis convocatorias"]},
    {"id": 3, "grupo": "A", "pregunta": "¿Cuántos registros tiene el consolidado versionado?",
     "esperado": "50 891", "claves": ["50891"]},
    {"id": 4, "grupo": "A", "pregunta": "¿Cuántos investigadores únicos tiene el consolidado?",
     "esperado": "26 662", "claves": ["26662"]},
    {"id": 5, "grupo": "A", "pregunta": "¿Cuántas páginas tiene el estado del arte?",
     "esperado": "20", "claves": ["20 pags", "20 paginas", "20 pp"]},
    {"id": 6, "grupo": "A", "pregunta": "¿Cuántas referencias tiene el estado del arte?",
     "esperado": "39", "claves": ["39 referencias", "39 entradas"]},
    {"id": 7, "grupo": "A", "pregunta": "¿Cuántas filas tiene el dataset de producción?",
     "esperado": "3 166 629", "claves": ["3166629"]},
    {"id": 8, "grupo": "A", "pregunta": "¿Cuántos fragmentos indexa el RAG?",
     "esperado": "150", "claves": ["150 fragmentos"]},
    {"id": 9, "grupo": "A", "pregunta": "¿Cuántos nodos tiene el grafo?",
     "esperado": "255", "claves": ["255 nodos"]},
    {"id": 10, "grupo": "A", "pregunta": "¿Cuántas reglas de validación hay?",
     "esperado": "17", "claves": ["17 reglas", "diecisiete reglas"]},
    # Q13 se reclasificó de B a A: su dato ("16 scripts con 10 OK / 6 ERROR") SÍ
    # está enunciado en el corpus (validacion_factica.md::1), así que dejarla en
    # el grupo "NO debería estar en el corpus" habría corrompido las métricas.
    {"id": 13, "grupo": "A", "pregunta": "¿Cuál es el resultado real de los 16 scripts del pipeline?",
     "esperado": "10 OK / 6 ERROR", "claves": ["10 OK / 6 ERROR", "16 scripts 10/6"]},
    {"id": 18, "grupo": "A", "pregunta": "¿Cuántos autores participaron en el repositorio auditado?",
     "esperado": "11", "claves": ["11 autores", "once autores"]},

    # ------------- GRUPO B: NO deberían estar en el corpus ----------------
    {"id": 11, "grupo": "B", "pregunta": "¿Cuántos commits tiene el repo auditado?",
     "esperado": "133", "claves": ["133 commits"]},
    {"id": 12, "grupo": "B", "pregunta": "¿Cuántos archivos de código tiene el repo auditado?",
     "esperado": "51", "claves": ["51 archivos"]},
    {"id": 14, "grupo": "B", "pregunta": "¿Se usa folium en el código del repo auditado?",
     "esperado": "No", "claves": ["folium"]},
    {"id": 15, "grupo": "B", "pregunta": "¿Cuántos registros con edad mayor a 100 detectó el repo auditado?",
     "esperado": "19", "claves": ["natipicos_edad=19", "19 sobre 50891", "19 atipicos"]},

    # --------- GRUPO C: del propio sistema, verificables en corpus ---------
    {"id": 16, "grupo": "C", "pregunta": "¿Cuál es el resultado de la regla R15?",
     "esperado": "FALLA", "claves": ["falla"]},
    # Q17 y Q18 anteriores se eliminaron: nadie enunciaba esas cifras en el
    # corpus (el "0 citas" era un valor derivado por el equipo). Reemplazadas
    # por datos SÍ enunciados: los once informes de validación (06b, §6.2).
    {"id": 17, "grupo": "C", "pregunta": "¿Cuántos informes de validación cubre el corpus de la memoria?",
     "esperado": "11", "claves": ["once informes"]},
    {"id": 19, "grupo": "C", "pregunta": "¿Cuál es el commit auditado del repo?",
     "esperado": "1528939", "claves": ["1528939"]},
    {"id": 20, "grupo": "C", "pregunta": "¿Cuál es el DOI real de Cañibano & Bozeman (2009)?",
     "esperado": "10.3152/095820209x441754", "claves": ["103152/095820209x441754", "095820209x441754"]},
]


def normalizar(texto: str) -> str:
    """minúsculas, sin acentos y sin separadores (espacios, puntos, comas, guiones)."""
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    for ch in " .,;:_-–—\u00a0":
        t = t.replace(ch, "")
    return t


def contiene(extracto: str, claves: list[str]) -> bool:
    n = normalizar(extracto)
    return any(normalizar(c) in n for c in claves)


def banda(score: float) -> str:
    if score > 0.15:
        return "alto"
    if score >= 0.05:
        return "medio"
    return "bajo"


def main() -> int:
    print("=" * 78)
    print("EVALUACIÓN DEL RAG — banco de 20 preguntas")
    print("=" * 78)

    mem = rag.MemoriaSemantica().cargar()
    meta = mem.meta
    print(f"Índice cargado: {len(mem.fragmentos)} fragmentos | "
          f"{meta.get('n_documentos', '?')} documentos | técnica: {meta.get('tecnica', 'TF-IDF')}")
    print(f"Colecciones: {meta.get('por_coleccion', {})}")
    print()

    registros: list[dict] = []
    # Texto COMPLETO de cada fragmento. La API consultar() solo devuelve un
    # extracto de 400 caracteres: comprobar el dato contra ese extracto genera
    # falsos negativos (p. ej. la cifra de fragmentos puede quedar más allá del corte).
    completo: dict[tuple[str, str], str] = {
        (f.documento, f.seccion): normalizar(f.texto) for f in mem.fragmentos
    }
    n_fragmentos = len(mem.fragmentos)

    for item in BANCO:
        # ranking COMPLETO (todos los fragmentos con similitud > 0): permite
        # distinguir "no se recuperó" de "el dato no está en el corpus".
        ranking = mem.consultar(item["pregunta"], k=n_fragmentos)
        res = ranking[:3]
        top = res[0] if res else None

        def _tiene(reg: dict) -> bool:
            texto = completo.get((reg["documento"], reg["seccion"]),
                                 normalizar(reg["extracto"]))
            return any(normalizar(c) in texto for c in item["claves"])

        en_top1 = bool(top and _tiene(top))
        en_top3 = any(_tiene(r) for r in res)
        rank = next((i + 1 for i, r in enumerate(ranking) if _tiene(r)), None)

        registros.append({
            "id": item["id"],
            "grupo": item["grupo"],
            "pregunta": item["pregunta"],
            "respuesta_esperada": item["esperado"],
            "claves_comprobadas": item["claves"],
            "score_top1": top["puntaje"] if top else None,
            "banda": banda(top["puntaje"]) if top else "sin_resultado",
            "top1": {
                "documento": top["documento"], "seccion": top["seccion"],
                "ruta": top["ruta"], "coleccion": top["coleccion"],
                "puntaje": top["puntaje"], "n_palabras": top["n_palabras"],
                "extracto": top["extracto"][:300],
            } if top else None,
            "top3": [
                {"documento": r["documento"], "seccion": r["seccion"], "ruta": r["ruta"],
                 "coleccion": r["coleccion"], "puntaje": r["puntaje"]}
                for r in res
            ],
            "respuesta_en_top1": en_top1,
            "respuesta_en_top3": en_top3,
            "respuesta_en_corpus": rank is not None,
            "rank_respuesta_en_corpus": rank,
            "n_resultados": len(ranking),
        })

    # ---------------- resumen ----------------
    total = len(registros)
    por_banda = {"alto": 0, "medio": 0, "bajo": 0, "sin_resultado": 0}
    for r in registros:
        por_banda[r["banda"]] = por_banda.get(r["banda"], 0) + 1
    aciertos_top1 = sum(1 for r in registros if r["respuesta_en_top1"])
    aciertos_top3 = sum(1 for r in registros if r["respuesta_en_top3"])
    en_corpus = sum(1 for r in registros if r["respuesta_en_corpus"])
    ranks = [r["rank_respuesta_en_corpus"] for r in registros
             if r["rank_respuesta_en_corpus"] is not None]
    por_grupo: dict[str, dict] = {}
    for r in registros:
        g = por_grupo.setdefault(r["grupo"], {"n": 0, "en_top1": 0, "en_top3": 0,
                                              "en_corpus": 0, "scores": []})
        g["n"] += 1
        g["en_top1"] += int(r["respuesta_en_top1"])
        g["en_top3"] += int(r["respuesta_en_top3"])
        g["en_corpus"] += int(r["respuesta_en_corpus"])
        if r["score_top1"] is not None:
            g["scores"].append(r["score_top1"])
    for g in por_grupo.values():
        g["score_promedio"] = round(sum(g["scores"]) / len(g["scores"]), 4) if g["scores"] else None
        g.pop("scores")

    resumen = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "indice": {
            "n_fragmentos": len(mem.fragmentos),
            "n_documentos": meta.get("n_documentos"),
            "tecnica": meta.get("tecnica"),
            "fecha_construccion": meta.get("fecha_construccion"),
            "colecciones": meta.get("por_coleccion"),
        },
        "total_preguntas": total,
        "bandas_score": por_banda,
        "respuesta_en_top1": aciertos_top1,
        "respuesta_en_top3": aciertos_top3,
        "respuesta_en_corpus": en_corpus,
        "rank_promedio_cuando_existe": round(sum(ranks) / len(ranks), 2) if ranks else None,
        "por_grupo": por_grupo,
    }

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps({"resumen": resumen, "preguntas": registros},
                                 ensure_ascii=False, indent=2), encoding="utf-8")

    print("-" * 78)
    print("RESUMEN")
    print("-" * 78)
    print(f"Total de preguntas: {total}")
    print(f"Score ALTO  (>0,15)      : {por_banda['alto']}")
    print(f"Score MEDIO (0,05-0,15)  : {por_banda['medio']}")
    print(f"Score BAJO  (<0,05)      : {por_banda['bajo']}")
    if por_banda.get("sin_resultado"):
        print(f"Sin resultado            : {por_banda['sin_resultado']}")
    print(f"Respuesta esperada hallada en el TOP-1: {aciertos_top1}/{total}")
    print(f"Respuesta esperada hallada en el TOP-3: {aciertos_top3}/{total}")
    print(f"Respuesta presente en algún fragmento del corpus: {en_corpus}/{total}")
    if ranks:
        print(f"Posición promedio en el ranking cuando el dato existe: "
              f"{sum(ranks) / len(ranks):.1f} (de hasta {len(mem.fragmentos)} fragmentos)")
    print()
    print("Por grupo:")
    for g, datos in sorted(por_grupo.items()):
        print(f"  Grupo {g}: {datos['n']} preguntas | en top-1: {datos['en_top1']} | "
              f"en top-3: {datos['en_top3']} | en corpus: {datos['en_corpus']} | "
              f"score promedio: {datos['score_promedio']}")
    print()
    print(f"Detalle completo escrito en: {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
