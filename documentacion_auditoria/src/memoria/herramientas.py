# -*- coding: utf-8 -*-
"""
memoria.herramientas — interfaz de línea de comandos del sistema de memoria.

Se puede ejecutar como módulo (`python -m memoria`) o como script directo
(`python src/memoria/herramientas.py`), y también se importa desde
compilar.py / generar_documento.py / generar_objetivo.py para integrar la
memoria al flujo de trabajo real (no como scripts sueltos).
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):                      # ejecución directa
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from memoria import config, grafo, rag, reglas, visual   # type: ignore
else:
    from . import config, grafo, rag, reglas, visual

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _cmd_indexar(args) -> int:
    mem = rag.MemoriaSemantica()
    meta = mem.indexar()
    print(f"[RAG] índice construido: {meta['n_fragmentos']} fragmentos de "
          f"{meta['n_documentos']} documentos ({meta['palabras_totales']} palabras, "
          f"{meta['n_terminos_vocabulario']} términos en el vocabulario).")
    print(f"[RAG] por colección: {meta['por_coleccion']}")
    print(f"[RAG] artefactos en {config.MEMORIA}")
    return 0


def _cmd_consultar(args) -> int:
    mem = rag.MemoriaSemantica().cargar()
    res = mem.consultar(args.texto, k=args.k)
    print(f"[RAG] consulta: {args.texto!r}  (índice: {len(mem.fragmentos)} fragmentos)")
    print(f"[RAG] términos que pesan: {mem.terminos_relevantes(args.texto, k=6)}")
    if not res:
        print("[RAG] sin antecedentes.")
        return 0
    for i, r in enumerate(res, 1):
        print(f"\n  {i}. cos={r['puntaje']:.4f}  {r['documento']}::{r['seccion']}  "
              f"[{r['coleccion']}, {r['n_palabras']} palabras]")
        print(f"     {r['ruta']}")
        print(f"     {r['extracto'][:240].strip()}...")
    return 0


def _cmd_antes_de_redactar(args) -> int:
    info = rag.antes_de_redactar(args.tema, k=args.k)
    print(f"[RAG] ANTES DE REDACTAR — tema: {info['tema']!r}")
    print(f"[RAG] {info['veredicto']}")
    for i, r in enumerate(info["recuperados"], 1):
        print(f"  {i}. cos={r['puntaje']:.4f} {r['documento']}::{r['seccion']}")
    print(f"[RAG] consulta registrada en {config.CONSULTAS_LOG.name}")
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


def _cmd_grafo(args) -> int:
    g, res = grafo.construir(refrescar_git=args.refrescar_git, guardar=True)
    print(f"[grafo] {res.total_nodos} nodos / {res.total_aristas} aristas  "
          f"(commit auditado real: {res.commit_auditado})")
    print("[grafo] nodos por tipo:")
    for t, n in sorted(res.nodos_por_tipo.items(), key=lambda x: -x[1]):
        print(f"   {t:22s} {n}")
    print("[grafo] aristas por relación:")
    for t, n in sorted(res.aristas_por_relacion.items(), key=lambda x: -x[1]):
        print(f"   {t:24s} {n}")
    print(f"[grafo] commits: reales={res.commits_reales} documentados={res.commits_documentados}")
    print(f"[grafo] archivos de código: reales={res.archivos_codigo_reales} "
          f"documentados={res.archivos_documentados} "
          f"solo_reales={len(res.archivos_solo_reales)} solo_documentados={len(res.archivos_solo_documentados)}")
    print(f"[grafo] términos del glosario usados: {res.terminos_usados}; "
          f"no usados: {res.terminos_no_usados}")
    print(f"[grafo] capas: {res.capas_usadas}")
    print(f"[grafo] archivos sin capa: {res.archivos_sin_capa}")
    if res.archivos_solo_reales:
        print(f"[grafo] ejemplos solo en el repo real: {res.archivos_solo_reales[:5]}")
    if res.archivos_solo_documentados:
        print(f"[grafo] ejemplos solo en el inventario: {res.archivos_solo_documentados[:5]}")
    print(f"[grafo] artefactos: {config.GRAFO_JSON.name}, {config.GRAFO_RESUMEN.name}")
    return 0


def _cmd_validar(args) -> int:
    informe = reglas.ejecutar(refrescar_git=args.refrescar_git, verbose=not args.json)
    if args.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    return 0 if informe["resumen"]["FALLA"] == 0 else 1


def _cmd_evidencia(args) -> int:
    informe = reglas.ejecutar(refrescar_git=args.refrescar_git, verbose=False)
    lineas = [
        "# Evidencia de ejecución — sistema de memoria del agente",
        "",
        f"**Fecha de ejecución:** {informe['fecha']}  ",
        f"**Commit auditado (HEAD real del clon):** `{informe['commit_auditado']}`  ",
        f"**Grafo:** {informe['grafo']['nodos']} nodos / {informe['grafo']['aristas']} aristas  ",
        f"**RAG:** {informe['rag'].get('n_fragmentos', 'N/D')} fragmentos de "
        f"{informe['rag'].get('n_documentos', 'N/D')} documentos "
        f"({informe['rag'].get('n_terminos_vocabulario', 'N/D')} términos)  ",
        f"**Reglas:** {informe['resumen']['PASA']} PASA · {informe['resumen']['FALLA']} FALLA · "
        f"{informe['resumen']['ADVERTENCIA']} ADVERTENCIA",
        "",
        "## Nodos del grafo",
        "",
        "| Tipo | Nodos |",
        "|---|---:|",
    ]
    for t, n in sorted(informe["grafo"]["nodos_por_tipo"].items(), key=lambda x: -x[1]):
        lineas.append(f"| {t} | {n} |")
    lineas += ["", "## Reglas de validación", "", "| Regla | Descripción | Estado | Detalle |", "|---|---|---|---|"]
    for r in informe["reglas"]:
        lineas.append(f"| {r['id']} | {r['descripcion']} | **{r['estado']}** | {r['detalle']} |")
    fallos = [r for r in informe["reglas"] if r["estado"] != reglas.PASA]
    lineas += ["", "## Detalle de reglas no aprobadas", ""]
    if not fallos:
        lineas.append("Ninguna: todas las reglas pasan sobre los datos reales.")
    for r in fallos:
        lineas.append(f"### {r['id']} — {r['estado']}: {r['descripcion']}")
        lineas.append("")
        lineas.append(r["detalle"])
        lineas.append("")
        lineas.append("```json")
        lineas.append(json.dumps(r["evidencia"], ensure_ascii=False, indent=2)[:1800])
        lineas.append("```")
        lineas.append("")
    config.EVIDENCIA_MD.write_text("\n".join(lineas), encoding="utf-8")
    print(f"[evidencia] escrito {config.EVIDENCIA_MD}")
    print(f"[evidencia] {informe['resumen']['PASA']} PASA · {informe['resumen']['FALLA']} FALLA · "
          f"{informe['resumen']['ADVERTENCIA']} ADVERTENCIA")
    return 0


def _informar_html(res: dict) -> int:
    """Imprime el resultado de la vista interactiva (o sugiere instalar PyVis)."""
    if "error" in res:
        print(f"[dibujar] {res['error']}")
        print(f"[dibujar] instálalo con:  {res['sugerencia']}")
        return 1
    print(f"[dibujar] HTML interactivo (PyVis): {res['salida']}  ({res['peso_kb']} KB)")
    print(f"[dibujar] vista: {res['nodos_dibujados']} nodos / {res['aristas_dibujadas']} relaciones "
          f"de {res['nodos_totales_grafo']} nodos / {res['aristas_totales_grafo']} del grafo completo")
    print(f"[dibujar] tipos: {', '.join(res['tipos'])} | colores/formas: {', '.join(res['claves_visuales'])}")
    print(f"[dibujar] flechas etiquetadas: {', '.join(res['relaciones_dibujadas'])}")
    print(f"[dibujar] autocontenido (funciona sin internet): {'sí' if res['autocontenido'] else 'NO'}")
    print(f"[dibujar] ábrelo con doble clic o:  Invoke-Item '{res['salida']}'")
    return 0


def _cmd_dibujar_html(args) -> int:
    tipos = [t.strip() for t in args.tipos.split(",") if t.strip()] or None
    res = visual.dibujar_html(tipos=tipos,
                              salida=Path(args.salida) if args.salida else None,
                              titulo=args.titulo or None,
                              refrescar_git=args.refrescar_git)
    return _informar_html(res)


def _cmd_dibujar(args) -> int:
    tipos = [t.strip() for t in args.tipos.split(",") if t.strip()] or None
    salida = Path(args.salida) if args.salida else None
    res = visual.dibujar(tipos=tipos, salida=salida,
                         titulo=args.titulo or None, html=args.html,
                         refrescar_git=args.refrescar_git)
    print(f"[dibujar] {res['salida']}")
    print(f"[dibujar] dibujados {res['nodos_dibujados']} nodos / {res['aristas_dibujadas']} aristas "
          f"de {res['nodos_totales_grafo']} nodos / {res['aristas_totales_grafo']} aristas totales")
    print(f"[dibujar] tipos: {', '.join(res['tipos'])}")
    if "salida_html" in res:
        print(f"[dibujar] HTML interactivo: {res['salida_html']}")
    if "aviso_html" in res:
        print(f"[dibujar] {res['aviso_html']}")
    if getattr(args, "interactivo", False):
        _informar_html(visual.dibujar_html(tipos=tipos, titulo=args.titulo or None,
                                           refrescar_git=args.refrescar_git))
    print("[dibujar] pista: para una diapositiva usa --tipos Criterio,Documento")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="memoria", description="Memoria del agente (RAG + grafo + reglas)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("indexar", help="construye el índice semántico (RAG)").set_defaults(func=_cmd_indexar)

    c = sub.add_parser("consultar", help="consulta el corpus ya escrito (RAG)")
    c.add_argument("texto")
    c.add_argument("-k", type=int, default=5)
    c.set_defaults(func=_cmd_consultar)

    a = sub.add_parser("antes-de-redactar", help="recupera antecedentes antes de escribir algo nuevo")
    a.add_argument("tema")
    a.add_argument("-k", type=int, default=5)
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=_cmd_antes_de_redactar)

    gr = sub.add_parser("grafo", help="construye y resume la memoria estructural")
    gr.add_argument("--refrescar-git", action="store_true")
    gr.set_defaults(func=_cmd_grafo)

    v = sub.add_parser("validar", help="ejecuta las reglas de validación sobre el grafo")
    v.add_argument("--refrescar-git", action="store_true")
    v.add_argument("--json", action="store_true")
    v.set_defaults(func=_cmd_validar)

    e = sub.add_parser("evidencia", help="genera el informe de evidencia en markdown")
    e.add_argument("--refrescar-git", action="store_true")
    e.set_defaults(func=_cmd_evidencia)

    d = sub.add_parser("dibujar", help="dibuja el grafo (PNG legible para diapositiva)")
    d.add_argument("--tipos", default="",
                   help="tipos de nodo separados por coma (por defecto: los estructurales)")
    d.add_argument("--salida", default="", help="ruta del PNG de salida")
    d.add_argument("--titulo", default="", help="título de la figura")
    d.add_argument("--html", action="store_true", help="además, HTML interactivo (plotly)")
    d.add_argument("--interactivo", action="store_true",
                   help="además del PNG, HTML interactivo con PyVis (etiquetas de relación, "
                        "colores/forma por tipo, tooltips; funciona sin internet)")
    d.add_argument("--refrescar-git", action="store_true")
    d.set_defaults(func=_cmd_dibujar)

    dh = sub.add_parser("dibujar-html",
                        help="genera el HTML interactivo del grafo con PyVis (sin PNG, sin internet)")
    dh.add_argument("--tipos", default="",
                    help="tipos de nodo separados por coma (por defecto: Criterio,Documento)")
    dh.add_argument("--salida", default="",
                    help="ruta del HTML (por defecto: data/memoria/grafo_interactivo.html)")
    dh.add_argument("--titulo", default="", help="título de la vista")
    dh.add_argument("--refrescar-git", action="store_true",
                    help="relee el clon auditado con git antes de dibujar")
    dh.set_defaults(func=_cmd_dibujar_html)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
