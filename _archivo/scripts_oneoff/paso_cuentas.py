"""PASO 1 (continuacion): actualizar las citas de palabras/terminos que cambiaron
al reescribir los parrafos del anteproyecto (que SI es parte del corpus).

116 290 -> 116 312 palabras (3 sitios) y 45 805 -> 45 819 terminos (1 sitio).
Cambiar digitos no altera la cuenta de palabras, asi que la cifra nueva queda
estable; hace falta reindexar una vez mas para que R13 no vea el indice viejo.
"""
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "documentacion_auditoria"
CAMBIOS = [
    ("latex/anteproyecto/secciones/06b_memoria_agente.tex",
     r"($\approx$116\,290 palabras)", r"($\approx$116\,312 palabras)", "06b:16"),
    ("data/memoria/texto_seccion_6_2.md",
     "(≈116 290 palabras)", "(≈116 312 palabras)", "texto:24"),
    ("data/memoria/texto_seccion_6_2.md",
     r"($\approx$116\,290 palabras)", r"($\approx$116\,312 palabras)", "texto:100"),
    ("guia_defensa_sistema_memoria.md",
     "(**45 805 términos**)", "(**45 819 términos**)", "guia:37"),
]

for rel, viejo, nuevo, etq in CAMBIOS:
    p = DOC / rel
    s = p.read_text(encoding="utf-8")
    n = s.count(viejo)
    assert n == 1, f"{rel} [{etq}]: {n} coincidencias"
    p.write_text(s.replace(viejo, nuevo), encoding="utf-8")
    print(f"   {rel:52s} {etq:12s} {viejo!r} -> {nuevo!r}")

# comprobar que no queda ninguna cita vieja
for rel in {c[0] for c in CAMBIOS}:
    s = (DOC / rel).read_text(encoding="utf-8")
    for viejo in ("116 290", "116\\,290", "45 805", "45\\,805"):
        assert viejo not in s, f"queda '{viejo}' en {rel}"
print("no quedan citas viejas de palabras/terminos")
