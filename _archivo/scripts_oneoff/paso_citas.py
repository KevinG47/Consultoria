"""PASOS 1-3: corregir las citas desactualizadas y la coherencia de lo que afirma
que R15 falla.

Solo se tocan citas y los parrafos que quedarian contradiciendose con el nuevo
estado. La cuenta de palabras/terminos NO cambia con los cambios de cifras (los
digitos ocupan las mismas posiciones), pero si con los parrafos reescritos: eso se
mide y se corrige despues de reindexar.
"""
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "documentacion_auditoria"
CAMBIOS: list[tuple[str, str, str]] = []


def editar(rel: str, viejo: str, nuevo: str, etiqueta: str) -> None:
    p = DOC / rel
    s = p.read_text(encoding="utf-8")
    n = s.count(viejo)
    assert n == 1, f"{rel} [{etiqueta}]: {n} coincidencias"
    p.write_text(s.replace(viejo, nuevo), encoding="utf-8")
    CAMBIOS.append((rel, etiqueta, f"{len(viejo)} -> {len(nuevo)} bytes"))


# =========================== 06b_memoria_agente.tex ========================
REL = "latex/anteproyecto/secciones/06b_memoria_agente.tex"

editar(REL, r"""la ejecución final: \textbf{15 PASA, 1 FALLA, 1 ADVERTENCIA}, con coincidencia
exacta de \textbf{133/133 commits} y \textbf{51/51 archivos} entre lo documentado
y el repositorio real. La única falla es, precisamente, el desfase declarado de
D007 (el código sigue en TF-IDF), que la regla reporta con archivo y marcador.""",
       r"""la ejecución final: \textbf{15 PASA, 0 FALLA, 2 ADVERTENCIA}, con coincidencia
exacta de \textbf{133/133 commits} y \textbf{51/51 archivos} entre lo documentado
y el repositorio real. Las dos advertencias son R12 (solapamiento entre documento
completo y LITE) y R15, que registra el respaldo declarado de TF-IDF.""",
       "recuento + quitar 'la unica falla'")

editar(REL, "(9 registradas)", "(10 registradas)", "decisiones registradas")
editar(REL, r"""\emph{propuesta}, \emph{pendiente\_implementacion}) y la relación de supersesión
explícita (p.\,ej.\ D007 supera a D002). La regla R15 verifica que ninguna
decisión superada siga implementada en el código ni presentada como vigente en
los documentos, y que exista una sola decisión actual por tema.""",
       r"""\emph{propuesta}, \emph{pendiente\_implementacion}) y la relación de supersesión
explícita (p.\,ej.\ D007 supera a D002). La regla R15 verifica que ninguna
decisión superada siga implementada en el código ni presentada como vigente en
los documentos, y que exista una sola decisión actual por tema. Si una decisión
superada se conserva a propósito, debe declarar el respaldo y su motivo: entonces
R15 lo registra como advertencia en lugar de falla.""",
       "mecanismo de respaldo")

# =============================== README.md =================================
editar("README.md", """  explícita, p. ej. D007 supera a D002). R15 falla si una decisión **superada**
  sigue en el código o se presenta como vigente; R16 falla si queda alguna URL
  en "PENDIENTE".""",
       """  explícita, p. ej. D007 supera a D002). R15 falla si una decisión **superada**
  sigue en el código sin declararlo, o si se presenta como vigente; si declara el
  respaldo y su motivo, lo registra como advertencia. R16 falla si queda alguna
  URL en "PENDIENTE".""",
       "descripcion de R15")

editar("README.md", """  Última ejecución real: **15 PASA · 1 FALLA · 1 ADVERTENCIA** (17 reglas).
  La FALLA es el desfase declarado D002→D007 (el código sigue en TF-IDF).""",
       """  Última ejecución real: **15 PASA · 0 FALLA · 2 ADVERTENCIA** (17 reglas).
  Las advertencias son R12 (solapamiento completo/LITE) y R15 (TF-IDF se conserva
  como respaldo declarado de D007, ya implementada).""",
       "recuento + quitar la FALLA")

# =================== guia_defensa_sistema_memoria.md =======================
REL = "guia_defensa_sistema_memoria.md"

editar(REL, "| **R15** | Las decisiones **superadas** no siguen en el código ni se presentan como vigentes: el código debe reflejar la decisión actual |",
       "| **R15** | Las decisiones **superadas** no siguen en el código ni se presentan como vigentes, salvo que declaren el respaldo y su motivo (entonces es ADVERTENCIA) |",
       "fila R15 de la tabla")

editar(REL, "el recuento de estados (**15 PASA · 1 FALLA · 1 ADVERTENCIA**)",
       "el recuento de estados (**15 PASA · 0 FALLA · 2 ADVERTENCIA**)", "recuento (tabla R17)")

editar(REL, r'''## 4. Por qué R15 falla hoy (y cómo explicarlo en vivo)

**Resultado real:** 17 reglas → **15 PASA · 1 FALLA · 1 ADVERTENCIA**.

**La falla, textual:**
```
D002 está SUPERADA (D007) pero su implementación sigue en el código:
'TfidfVectorizer' en documentacion_auditoria/src/memoria/rag.py
```

**Explicación en términos simples (memorízala):**
> "Al principio decidimos usar TF-IDF para el buscador interno (decisión D002). Después
> el docente pidió migrar a *embeddings* por transferibilidad (decisión D007). La bitácora
> registra el cambio, pero **el código todavía usa TF-IDF**: eso es exactamente lo que R15
> detecta. No es un error escondido: es una **deuda técnica declarada** que el sistema
> reporta con archivo y nombre de variable. Se cierra de dos maneras: implementando la
> migración, o declarando una **excepción temporal auditada** (motivo, quién la autoriza y
> hasta cuándo), que degrada la falla a advertencia y deja el motivo por escrito."''',
       r'''## 4. R15 y el respaldo declarado (cómo explicarlo en vivo)

**Resultado real:** 17 reglas → **15 PASA · 0 FALLA · 2 ADVERTENCIA**.

R15 ya **no falla**. Ahora registra como **advertencia** que TF-IDF siga en el código
aunque D002 esté superada, porque así está declarado en la bitácora:

```
D002 está SUPERADA (D007) pero su implementación sigue en el código:
'TfidfVectorizer' en documentacion_auditoria/src/memoria/rag.py
 — respaldo declarado: TF-IDF no se retira: se conserva como método por DEFECTO...
```

**Explicación en términos simples (memorízala):**
> "Al principio decidimos usar TF-IDF para el buscador interno (decisión D002). Después
> el docente pidió migrar a *embeddings* por transferibilidad (decisión D007). Esa
> migración ya está implementada, pero **conservamos TF-IDF a propósito** como método por
> defecto: es más rápido, no arrastra torch, es explicable y en el banco de 20 preguntas
> rinde igual o mejor que el modelo de embeddings. R15 está hecha para detectar que una
> decisión superada siga en el código, así que exigimos que ese respaldo se **declare** en
> la bitácora (motivo, qué se conserva y quién lo autoriza). Declarado, R15 lo registra
> como advertencia; sin declarar, la compilación se aborta. Es el mecanismo simétrico al
> que ya existía para el caso contrario —decisión vigente que no está implementada—."''',
       "seccion 4 reescrita")

editar(REL, "`[memoria] reglas: 15 PASA, 1 FALLA, 1 ADVERTENCIA` (exit code 1 por la falla de R15).",
       "`[memoria] reglas: 15 PASA, 0 FALLA, 2 ADVERTENCIA` (exit code 0).",
       "salida esperada de validar")

# ==================== data/memoria/texto_seccion_6_2.md ====================
REL = "data/memoria/texto_seccion_6_2.md"

editar(REL, """términos es incómodo de mantener; esa migración queda **pendiente de
implementación** y así lo declara la bitácora, de modo que el cambio no se
pierde: la regla R15 lo detecta y falla mientras el código siga en TF-IDF. Antes""",
       """términos es incómodo de mantener; esa migración ya está **implementada con un
modelo local** (sin API, porque la rúbrica prohíbe enviar datos de la contraparte a
la nube) y TF-IDF se conserva como método por defecto y respaldo declarado. La
regla R15 exige que ese respaldo esté declarado en la bitácora y, si lo está, lo
registra como advertencia. Antes""",
       "D007 implementada + mecanismo R15")

editar(REL, """(R17). Resultado de la ejecución final: **15 PASA, 1 FALLA, 1 ADVERTENCIA**, con
la coincidencia exacta de **133/133 commits** y **51/51 archivos** entre lo
documentado y el repositorio real. La única falla es, precisamente, el desfase
declarado de D007 (el código sigue en TF-IDF), que la regla reporta con archivo y
marcador.""",
       """(R17). Resultado de la ejecución final: **15 PASA, 0 FALLA, 2 ADVERTENCIA**, con
la coincidencia exacta de **133/133 commits** y **51/51 archivos** entre lo
documentado y el repositorio real. Las dos advertencias son R12 (solapamiento
entre el documento completo y su LITE) y R15, que registra el respaldo declarado
de TF-IDF con archivo y marcador.""",
       "recuento + quitar 'la unica falla'")

editar(REL, """supera a D002). La regla R15 verifica que ninguna decisión superada siga
implementada en el código ni presentada como vigente en los documentos, y que
exista una sola decisión actual por tema.""",
       """supera a D002). La regla R15 verifica que ninguna decisión superada siga
implementada en el código ni presentada como vigente en los documentos, y que
exista una sola decisión actual por tema. Una decisión superada puede conservarse
a propósito si declara el respaldo y su motivo: en ese caso R15 lo registra como
advertencia en lugar de falla.""",
       "mecanismo de respaldo")

editar(REL, r"""\textbf{15 PASA, 1 FALLA, 1 ADVERTENCIA}, con coincidencia exacta de
\textbf{133/133 commits} y \textbf{51/51 archivos} entre lo documentado y el
repositorio real.""",
       r"""\textbf{15 PASA, 0 FALLA, 2 ADVERTENCIA}, con coincidencia exacta de
\textbf{133/133 commits} y \textbf{51/51 archivos} entre lo documentado y el
repositorio real.""",
       "recuento en la version LaTeX")

# ======================= scripts/banco_preguntas.py ========================
editar("scripts/banco_preguntas.py",
       '''{"id": 16, "grupo": "C", "pregunta": "¿Cuál es el resultado de la regla R15?",
     "esperado": "FALLA", "claves": ["falla"]},''',
       '''{"id": 16, "grupo": "C", "pregunta": "¿Cuál es el resultado de la regla R15?",
     "esperado": "ADVERTENCIA", "claves": ["advertencia"]},''',
       "Q16: estado de R15")

print(f"aplicados {len(CAMBIOS)} cambios:")
for rel, etq, det in CAMBIOS:
    print(f"   {rel:52s} {etq:34s} {det}")
