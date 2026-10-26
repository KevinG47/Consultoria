---
id: PUB-DEC
origen: sintesis
fase: "Decisiones"
tags: [decisiones, arquitectura, trazabilidad]
---

# 01 · Decisiones de diseño (D001–D010) y nota metodológica

Cada decisión vive en `documentacion_auditoria/data/memoria/decisiones.yaml` con su
justificación, alternativas descartadas y estado (`vigente`, `superada`,
`pendiente_implementacion`). Este archivo es la versión legible; la fuente de verdad es el
YAML, y la regla **R15** compara ese registro contra el código (ver
[[03_reglas_validacion]]).

## Tabla resumen

| ID | Decisión | Estado |
|---|---|---|
| D001 | Memoria semántica con RAG sobre el corpus documental | vigente |
| D002 | RAG con TF-IDF (sin embeddings) | superada por D007 |
| D003 | Grafo de memoria en memoria (networkx), no motor externo | vigente |
| D004 | Obsidian fuera del pipeline automatizado | vigente |
| D005 | Grafo alimentado con datos vivos del repositorio auditado | vigente |
| D006 | Validación como puerta antes de compilar | vigente |
| D007 | Migrar el RAG de TF-IDF a embeddings | pendiente de implementación |
| D008 | Corregir el indexador del RAG | vigente |
| D009 | Cerrar el ciclo de D008 y añadir la regla R17 | vigente |
| D010 | Rectificación sobre dos cifras del material propio | vigente |

## Por qué cada una

**D001 · RAG para la memoria semántica.** El corpus de auditoría crece documento a documento
y debe mantenerse coherente entre sí: antes de redactar o afirmar algo nuevo, el agente
recupera qué se dijo antes sobre ese tema. Sin esa recuperación, la consistencia se sostiene
solo en la memoria de las personas.

**D002 · TF-IDF en vez de embeddings (superada).** Con ~24 documentos homogéneos en
vocabulario técnico, TF-IDF resuelve la recuperación sin dependencias externas, sin costo y
sin salida de datos a la nube. Quedó superada por D007, pero se conserva como referencia
porque explica el punto de partida.

**D003 · Grafo en memoria con networkx.** La escala real del proyecto es de cientos de
nodos; un motor de grafos externo (Neo4j, Memgraph) exigiría infraestructura
desproporcionada. Migrar después es cambiar el motor sin rediseñar el modelo.

**D004 · Obsidian fuera del pipeline.** Obsidian es excelente para que una persona navegue,
pero no expone una API que el agente pueda consultar o validar. Su rol queda como
documentación humana, no como pieza automatizada. Esta bitácora *es* ese uso humano de
Markdown, no una dependencia del sistema.

**D005 · Datos vivos del repositorio auditado.** El grafo se construye clonando el repositorio
auditado y leyendo `git log` y `git ls-files`, de modo que la línea de tiempo y el inventario
de código se comparan contra el repositorio real y no contra una copia que puede quedar
desactualizada.

**D006 · Validación como puerta.** `compilar.py` ejecuta las reglas y aborta con código 2 si
hay alguna en FALLA. El requisito del trabajo era que el sistema estuviera *funcionando*, no
solo descrito; una puerta real lo demuestra. La compilación puede forzarse con `--forzar`,
pero eso queda registrado.

**D007 · Migración a embeddings (pendiente).** Se decidió migrar el RAG de TF-IDF a
embeddings por reproducibilidad y mantenimiento futuro. Está registrada como
`pendiente_implementacion`. Los intentos con modelos locales no superaron a TF-IDF en la
evaluación del banco de preguntas.

**D008 · Corregir el indexador.** El indexador limpiaba mal el LaTeX y perdía documentos con
el mismo nombre de sección. Tras el arreglo, el índice pasó de 145 fragmentos / 105 167
palabras a **151 fragmentos / 123 505 palabras**.

**D009 · Cerrar el ciclo de D008.** El cambio de cifras dejó números obsoletos en varios
documentos y nada lo detectaba. Se actualizaron los 6 sitios y se añadió la regla **R17**,
que vigila que las cifras citadas en los documentos coincidan con las de la última corrida.

**D010 · Rectificación sobre dos cifras.** Durante el trabajo se corrigieron dos afirmaciones
del material propio: un porcentaje que se había dado por no recomputable sí lo era, y una
comparación de registros que en realidad correspondía a universos distintos. Se registró la
rectificación en lugar de borrar el rastro.

## Nota metodológica: análisis longitudinal

La decisión metodológica del análisis longitudinal (unidad de análisis, deduplicación por
persona, tratamiento del evento de salida y comparación entre estimación muestral y censo) se
documenta en `03_informes/analisis_fase2/metodologia_muestreo.md` §7.4, junto con el diseño
del muestreo y los diagnósticos de supuestos.

## Cómo se consulta y se mantiene

- Leer el YAML: `documentacion_auditoria/data/memoria/decisiones.yaml`.
- Verificar el desfase con el código: `python -m memoria validar` (R15).
- Registrar una decisión nueva: añadir la entrada al YAML con `id`, `fecha`, `decision`,
  `justificacion`, `alternativas_descartadas`, `estado` y, si reemplaza a otra, `supersede`.

Ver [[03_reglas_validacion]] para R15 y R17, y [[02_arquitectura_memoria]] para el resto de
la arquitectura.
