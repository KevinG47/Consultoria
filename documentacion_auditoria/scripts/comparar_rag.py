# -*- coding: utf-8 -*-
"""
comparar_rag.py
===============

Compara los dos métodos de recuperación del RAG (TF-IDF vs embeddings) sobre el
mismo banco de 20 preguntas, a partir de los dos JSON que produce
`banco_preguntas.py`.

Qué calcula
-----------
1. Tabla por pregunta: score del top-1 en cada método, si la respuesta esperada
   está en el top-1 y en el top-3, y el ranking del fragmento correcto.
2. Agregados: top-1 con respuesta, top-3 con respuesta, score promedio del top-1,
   ranking promedio y preguntas en que gana cada método.
3. Comprobación de no-regresión: si se le pasa el resultado histórico de TF-IDF,
   verifica que la corrida nueva de TF-IDF coincide (prueba de que el respaldo
   sigue comportándose igual).
4. Análisis de truncamiento: mide los tokens de cada fragmento y cuántos superan
   el máximo del modelo (explica por qué los embeddings pueden rendir peor).

Criterio de comparación por pregunta (documentado para que sea auditable)
------------------------------------------------------------------------
Se ordena lexicográficamente por: (1) acierto en top-1, (2) acierto en top-3,
(3) mejor (menor) ranking del fragmento correcto. Gana quien tenga la tupla
mayor; si son iguales, empate.

Uso
---
    python documentacion_auditoria/scripts/comparar_rag.py
    python documentacion_auditoria/scripts/comparar_rag.py --historico <ruta.json>
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOC = Path(__file__).resolve().parents[1]
MEM = DOC / "data" / "memoria"
SALIDA = MEM / "comparacion_rag.json"
N_FRAG = 150


def cargar(ruta: Path) -> dict:
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta}. Corre primero banco_preguntas.py para ese método.")
    return json.loads(ruta.read_text(encoding="utf-8"))


def clave(r: dict) -> tuple:
    """Tupla de mérito: top-1, luego top-3, luego menor ranking."""
    rank = r.get("rank_respuesta_en_corpus")
    return (int(bool(r.get("respuesta_en_top1"))),
            int(bool(r.get("respuesta_en_top3"))),
            -(rank if rank else 10 ** 6))


def nombre_top1(r: dict) -> str:
    t = r.get("top1")
    return f"{t['documento']}::{t['seccion']}" if t else "—"


def main() -> int:
    ap = argparse.ArgumentParser(description="Comparación TF-IDF vs embeddings del RAG")
    ap.add_argument("--tfidf", default=str(MEM / "resultados_banco_tfidf.json"))
    ap.add_argument("--embeddings", default=str(MEM / "resultados_banco_embeddings.json"))
    ap.add_argument("--historico", default=str(MEM / "resultados_banco_preguntas.json"),
                    help="resultado previo de TF-IDF, para comprobar que no hubo regresión")
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--sin-truncamiento", action="store_true",
                    help="omite el análisis de tokens (evita cargar el modelo)")
    args = ap.parse_args()

    a = cargar(Path(args.tfidf))
    b = cargar(Path(args.embeddings))
    pa, pb = {r["id"]: r for r in a["preguntas"]}, {r["id"]: r for r in b["preguntas"]}
    assert set(pa) == set(pb), "los dos archivos no cubren las mismas preguntas"

    # ---------------- 1 y 2: tabla y agregados ----------------
    filas = []
    for pid in sorted(pa):
        ra, rb = pa[pid], pb[pid]
        ka, kb = clave(ra), clave(rb)
        verdicto = "embeddings" if kb > ka else ("tfidf" if kb < ka else "empate")
        filas.append({
            "id": pid, "grupo": ra["grupo"], "pregunta": ra["pregunta"],
            "respuesta_esperada": ra["respuesta_esperada"],
            "score_top1_tfidf": ra["score_top1"], "score_top1_embeddings": rb["score_top1"],
            "top1_tfidf": (ra["top1"] or {}).get("documento", "") + "::" +
                          (ra["top1"] or {}).get("seccion", "") if ra["top1"] else None,
            "top1_embeddings": (rb["top1"] or {}).get("documento", "") + "::" +
                               (rb["top1"] or {}).get("seccion", "") if rb["top1"] else None,
            "en_top1_tfidf": bool(ra["respuesta_en_top1"]),
            "en_top1_embeddings": bool(rb["respuesta_en_top1"]),
            "en_top3_tfidf": bool(ra["respuesta_en_top3"]),
            "en_top3_embeddings": bool(rb["respuesta_en_top3"]),
            "en_corpus_tfidf": bool(ra["respuesta_en_corpus"]),
            "en_corpus_embeddings": bool(rb["respuesta_en_corpus"]),
            "rank_tfidf": ra.get("rank_respuesta_en_corpus"),
            "rank_embeddings": rb.get("rank_respuesta_en_corpus"),
            "gana": verdicto,
        })

    def suma(campo):
        return sum(1 for f in filas if f[campo])

    def promedio(campo):
        vals = [f[campo] for f in filas if f[campo] is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    def prom_rank(campo):
        vals = [f[campo] for f in filas if f[campo] is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    agg = {
        "n_preguntas": len(filas),
        "top1_tfidf": suma("en_top1_tfidf"), "top1_embeddings": suma("en_top1_embeddings"),
        "top3_tfidf": suma("en_top3_tfidf"), "top3_embeddings": suma("en_top3_embeddings"),
        "corpus_tfidf": suma("en_corpus_tfidf"), "corpus_embeddings": suma("en_corpus_embeddings"),
        "score_prom_top1_tfidf": promedio("score_top1_tfidf"),
        "score_prom_top1_embeddings": promedio("score_top1_embeddings"),
        "rank_prom_tfidf": prom_rank("rank_tfidf"),
        "rank_prom_embeddings": prom_rank("rank_embeddings"),
        "gana_embeddings": sum(1 for f in filas if f["gana"] == "embeddings"),
        "gana_tfidf": sum(1 for f in filas if f["gana"] == "tfidf"),
        "empates": sum(1 for f in filas if f["gana"] == "empate"),
    }
    # ganancias y pérdidas explícitas en top-1 / top-3
    agg["emb_solo_top1"] = sorted(f["id"] for f in filas
                                 if f["en_top1_embeddings"] and not f["en_top1_tfidf"])
    agg["tfidf_solo_top1"] = sorted(f["id"] for f in filas
                                    if f["en_top1_tfidf"] and not f["en_top1_embeddings"])
    agg["emb_solo_top3"] = sorted(f["id"] for f in filas
                                  if f["en_top3_embeddings"] and not f["en_top3_tfidf"])
    agg["tfidf_solo_top3"] = sorted(f["id"] for f in filas
                                    if f["en_top3_tfidf"] and not f["en_top3_embeddings"])

    por_grupo = {}
    for f in filas:
        g = por_grupo.setdefault(f["grupo"], {"n": 0, "top1_tfidf": 0, "top1_embeddings": 0,
                                             "top3_tfidf": 0, "top3_embeddings": 0})
        g["n"] += 1
        g["top1_tfidf"] += int(f["en_top1_tfidf"])
        g["top1_embeddings"] += int(f["en_top1_embeddings"])
        g["top3_tfidf"] += int(f["en_top3_tfidf"])
        g["top3_embeddings"] += int(f["en_top3_embeddings"])

    # ---------------- 3: no-regresión de TF-IDF ----------------
    regresion = None
    hist = Path(args.historico)
    if hist.exists():
        h = cargar(hist)
        ph = {r["id"]: r for r in h["preguntas"]}
        dif = []
        for pid in sorted(pa):
            if pid not in ph:
                dif.append(f"Q{pid}: ausente en el histórico")
                continue
            for campo in ("score_top1", "rank_respuesta_en_corpus",
                          "respuesta_en_top1", "respuesta_en_top3"):
                if pa[pid].get(campo) != ph[pid].get(campo):
                    dif.append(f"Q{pid}.{campo}: nuevo={pa[pid].get(campo)} "
                               f"histórico={ph[pid].get(campo)}")
        regresion = {
            "archivo_historico": hist.name,
            "fecha_historico": h["resumen"].get("fecha"),
            "preguntas_comparadas": len(pa),
            "diferencias": dif,
            "identico": not dif,
        }

    # ---------------- 4: truncamiento ----------------
    trunc = None
    if not args.sin_truncamiento:
        try:
            sys.path.insert(0, str(DOC / "src"))
            from memoria import config as cfg, rag as rag_mod   # noqa: E402
            modelo = rag_mod._cargar_modelo()
            mx = int(modelo.max_seq_length)
            frags = [l for l in (MEM / "rag_corpus.jsonl").read_text(
                encoding="utf-8").splitlines() if l.strip()]
            textos = [json.loads(l)["texto"] for l in frags]
            ids = [json.loads(l)["id"] for l in frags]
            cod = modelo.tokenizer(textos, truncation=False, padding=False)["input_ids"]
            largos = [len(x) for x in cod]
            exceden = [(i, ids[i], largos[i]) for i in range(len(largos)) if largos[i] > mx]
            largos_ord = sorted(largos)
            trunc = {
                "max_seq_length": mx,
                "n_fragmentos": len(largos),
                "n_exceden": len(exceden),
                "pct_exceden": round(100 * len(exceden) / len(largos), 1),
                "tokens_min": largos_ord[0],
                "tokens_mediana": largos_ord[len(largos_ord) // 2],
                "tokens_max": largos_ord[-1],
                "tokens_promedio": round(sum(largos) / len(largos), 1),
                "palabras_promedio": round(
                    sum(len(t.split()) for t in textos) / len(textos), 1),
                "ejemplos_excedidos": [{"id": i, "tokens": t} for _, i, t in
                                       sorted(exceden, key=lambda z: -z[2])[:5]],
                "cobertura_media_pct": round(
                    100 * sum(min(x, mx) for x in largos) / sum(largos), 1),
                # alias con el mismo nombre que usa el metadato del índice, para
                # que los dos artefactos se lean igual
                "cobertura_pct": round(
                    100 * sum(min(x, mx) for x in largos) / sum(largos), 1),
            }
        except Exception as exc:      # pragma: no cover
            trunc = {"error": str(exc)}

    salida = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "criterio_comparacion": ("orden lexicográfico por (top-1 acertado, top-3 acertado, "
                                 "menor ranking del fragmento correcto)"),
        "archivos": {"tfidf": Path(args.tfidf).name, "embeddings": Path(args.embeddings).name},
        "indices": {"tfidf": a["resumen"].get("indice"), "embeddings": b["resumen"].get("indice")},
        "agregados": agg,
        "por_grupo": por_grupo,
        "no_regresion_tfidf": regresion,
        "truncamiento": trunc,
        "preguntas": filas,
    }
    Path(args.salida).write_text(json.dumps(salida, ensure_ascii=False, indent=2),
                                 encoding="utf-8")

    # ---------------- informe en consola ----------------
    print("=" * 100)
    print("COMPARACIÓN TF-IDF vs EMBEDDINGS — banco de 20 preguntas")
    print("=" * 100)
    print(f"{'Q':>3} {'G':>2} {'score TF-IDF':>12} {'score emb':>10} "
          f"{'top1 tf':>7} {'top1 em':>7} {'top3 tf':>7} {'top3 em':>7} "
          f"{'rank tf':>7} {'rank em':>7}  gana")
    for f in filas:
        print(f"{f['id']:>3} {f['grupo']:>2} "
              f"{(f['score_top1_tfidf'] if f['score_top1_tfidf'] is not None else float('nan')):>12.4f} "
              f"{(f['score_top1_embeddings'] if f['score_top1_embeddings'] is not None else float('nan')):>10.4f} "
              f"{'sí' if f['en_top1_tfidf'] else 'no':>7} {'sí' if f['en_top1_embeddings'] else 'no':>7} "
              f"{'sí' if f['en_top3_tfidf'] else 'no':>7} {'sí' if f['en_top3_embeddings'] else 'no':>7} "
              f"{(f['rank_tfidf'] if f['rank_tfidf'] else '—'):>7} "
              f"{(f['rank_embeddings'] if f['rank_embeddings'] else '—'):>7}  {f['gana']}")
    print("-" * 100)
    print(f"Top-1 con respuesta : TF-IDF {agg['top1_tfidf']}/20  ·  embeddings {agg['top1_embeddings']}/20")
    print(f"Top-3 con respuesta : TF-IDF {agg['top3_tfidf']}/20  ·  embeddings {agg['top3_embeddings']}/20")
    print(f"Score prom. del top-1: TF-IDF {agg['score_prom_top1_tfidf']}  ·  "
          f"embeddings {agg['score_prom_top1_embeddings']}   (escalas NO comparables)")
    print(f"Ranking prom. del dato: TF-IDF {agg['rank_prom_tfidf']}  ·  "
          f"embeddings {agg['rank_prom_embeddings']}  (de {N_FRAG} fragmentos)")
    print(f"Gana: embeddings {agg['gana_embeddings']} · TF-IDF {agg['gana_tfidf']} · "
          f"empates {agg['empates']}")
    print(f"Embeddings encuentra y TF-IDF no (top-1): {agg['emb_solo_top1']}")
    print(f"TF-IDF encuentra y embeddings no (top-1): {agg['tfidf_solo_top1']}")
    print(f"Embeddings encuentra y TF-IDF no (top-3): {agg['emb_solo_top3']}")
    print(f"TF-IDF encuentra y embeddings no (top-3): {agg['tfidf_solo_top3']}")
    if regresion:
        print("-" * 100)
        print(f"No-regresión TF-IDF contra {regresion['archivo_historico']}: "
              f"{'IDÉNTICO' if regresion['identico'] else str(len(regresion['diferencias'])) + ' diferencias'}")
        for d in regresion["diferencias"][:10]:
            print("   ", d)
    if trunc:
        print("-" * 100)
        if "error" in trunc:
            print("Truncamiento: no se pudo medir:", trunc["error"])
        else:
            print(f"Truncamiento del modelo: max_seq_length={trunc['max_seq_length']} tokens · "
                  f"{trunc['n_exceden']}/{trunc['n_fragmentos']} fragmentos lo superan "
                  f"({trunc['pct_exceden']} %)")
            print(f"   tokens por fragmento: mín {trunc['tokens_min']} · mediana "
                  f"{trunc['tokens_mediana']} · máx {trunc['tokens_max']} · "
                  f"promedio {trunc['tokens_promedio']} (palabras promedio "
                  f"{trunc['palabras_promedio']})")
            print(f"   cobertura media del texto al vectorizar: "
                  f"{trunc['cobertura_media_pct']} % del contenido")
    print()
    print(f"Detalle en: {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
