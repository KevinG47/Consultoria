# -*- coding: utf-8 -*-
"""
memoria.flujo
=============

Punto de unión entre el sistema de memoria y el flujo de trabajo REAL del
proyecto (no scripts sueltos):

  * ANTES DE REDACTAR  -> rag.antes_de_redactar() dentro de los generadores
                          (generar_objetivo.py, generar_documento.py).
  * ANTES DE COMPILAR  -> reglas.antes_de_compilar() dentro de compilar.py,
                          que aborta la compilación si alguna regla FALLA.

Los enganches están envueltos en try/except para que una caída del sistema de
memoria nunca rompa la generación/compilación: se avisa y se continúa.
"""

from __future__ import annotations

from . import config, rag, reglas

UMBRAL_REDUNDANCIA = 0.35   # coseno a partir del cual se avisa de posible solapamiento


def revisar_antecedentes(tema: str, contexto: str = "", umbral: float = UMBRAL_REDUNDANCIA) -> dict | None:
    """Se llama antes de redactar un documento/sección."""
    try:
        consulta = " ".join(x for x in (tema, contexto) if x).strip()
        info = rag.antes_de_redactar(consulta, k=3)
        top = info["recuperados"][0] if info["recuperados"] else None
        if top and top["puntaje"] >= umbral:
            print(f"  [memoria] aviso de solapamiento: cos={top['puntaje']:.3f} con "
                  f"{top['documento']}::{top['seccion']} (revisar que no se contradiga)")
        return info
    except Exception as exc:                                    # noqa: BLE001
        print(f"  [memoria] no disponible para consulta previa: {exc}")
        return None


def puerta_compilacion(forzar: bool = False, silencioso: bool = False) -> bool:
    """
    Se llama antes de compilar el PDF final.

    Devuelve True si se puede continuar. Si alguna regla FALLA y no se ha pedido
    --forzar, devuelve False (el compilador aborta).
    """
    try:
        informe = reglas.antes_de_compilar(forzar=forzar)
        return not informe["abortar"]
    except Exception as exc:                                    # noqa: BLE001
        print(f"[memoria] validación previa no disponible ({exc}); se continúa sin puerta.")
        return True
