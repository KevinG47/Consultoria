# Texto para la sección 6.2 del anteproyecto — Gestión de información del agente de IA

> **Uso:** este archivo contiene (1) el texto en prosa y (2) el bloque LaTeX listo
> para pegar en `latex/anteproyecto/secciones/` (versión propuesta:
> `06b_memoria_agente.tex`). Reemplaza o amplía el actual apartado «Uso declarado
> de herramientas de IA» de la sección 6.2.
> Todos los números citados provienen de la ejecución real sobre los datos del
> proyecto (ver `data/memoria/evidencia_validacion.md`).

---

## 1. Texto (prosa)

### 6.2 Uso de herramientas de IA y gestión de su información

Usamos IA generativa como **asistente**, no como autora. Para que ese uso fuera
**verificable** y no produjera contradicciones entre los trece documentos del
proyecto, implementamos una estrategia de gestión de información del agente con
tres piezas, todas ejecutables y ejecutadas sobre los datos reales:

**(i) Memoria semántica (RAG ligero).** Indexamos el corpus ya redactado —las
secciones LaTeX de los seis criterios, sus versiones LITE, el documento maestro
y los once informes de validación— en **137 fragmentos de 24 documentos**
(≈100 700 palabras). La recuperación usa **TF-IDF (1–2 gramas, `sublinear_tf`)
con similitud coseno** (scikit-learn). Se eligió TF-IDF y no *embeddings* por
cuatro razones concretas a esta escala: el corpus es pequeño (137 fragmentos), el
vocabulario es técnico y estable, no se depende de un proveedor externo ni de
red, y el resultado es determinista y explicable (podemos mostrar qué términos
pesan en cada recuperación). Antes de redactar cualquier sección, el generador
consulta esta memoria y registra los antecedentes en
`data/memoria/consultas_rag.jsonl`; si la similitud supera 0,35 avisa de posible
solapamiento. Así evitamos repetir o contradecir lo ya escrito entre documentos.

**(ii) Memoria estructural (grafo).** Modelamos explícitamente el proyecto como
un grafo dirigido de **255 nodos y 500 aristas**: `Criterio → Documento`
(completo/LITE), `Documento → TérminoGlosario`, `ArchivoCodigo → Capa`,
`Commit → Autor` y `Documento → Commit`. Se construye con **networkx** a partir de
los metadatos que ya eran fuente de verdad (`objetivos.yaml`, `glosario.yaml`,
`capas.yaml`, `commits_timeline.csv`, `inventario_codigo.csv`) **más datos vivos
del repositorio auditado**: `git log` y `git ls-files` sobre el clon real en el
commit `1528939`. No se usó un motor de grafos externo (Neo4j/Memgraph) porque
con decenas de nodos y consultas simples no aporta ventaja alguna y sí costo de
operación.

**(iii) Validación antes de compilar.** Doce reglas se ejecutan como **puerta
previa a la compilación del PDF final**, integradas en `compilar.py` (si alguna
falla, la compilación se aborta; puede omitirse con `--forzar`). Las seis
mínimas exigidas —cada criterio con completo y LITE; conclusiones registradas;
veredicto resumido en el LITE; términos del glosario realmente usados; línea de
tiempo coincidente con el `git log` real; y todo archivo de código referenciado
en el documento del criterio de código— más seis adicionales (commit auditado,
capas asignadas, cobertura de fichas, integridad referencial del grafo,
cobertura del índice y la regla LITE ≤ 40 %). Resultado real de la última
ejecución: **8 PASA, 3 FALLA, 1 ADVERTENCIA**, con la coincidencia exacta de
**133/133 commits** y **51/51 archivos** entre lo documentado y el repositorio
real.

Declaramos también lo que **no** pasa, porque es parte del resultado: el LITE del
criterio 3 no tiene `lite_veredicto` declarado en `objetivos.yaml`; el término
«ETL» está en el glosario pero no se usa en ningún documento; y `src/__init__.py`
no tiene capa asignada en `capas.yaml`. Los tres son hallazgos del propio sistema
de validación y quedan registrados con su evidencia en
`data/memoria/validacion_reglas.json`.

---

## 2. Bloque LaTeX listo para pegar

```latex
\subsection{Gestión de la información del agente de IA}

Usamos IA generativa como \textbf{asistente}, no como autora. Para que ese uso
fuera \textbf{verificable} y no produjera contradicciones entre los documentos
del proyecto, implementamos una estrategia de gestión de información del agente
con tres piezas, todas ejecutables y ejecutadas sobre los datos reales.

\textbf{(i) Memoria semántica (RAG ligero).} Indexamos el corpus ya redactado
---secciones de los seis criterios, sus versiones LITE, el documento maestro y
los once informes de validación--- en \textbf{137 fragmentos de 24 documentos}
($\approx$100\,700 palabras). La recuperación usa \textbf{TF-IDF (1--2 gramas,
\texttt{sublinear\_tf}) con similitud coseno} (scikit-learn). Se eligió TF-IDF y
no \emph{embeddings} por cuatro razones a esta escala: el corpus es pequeño
(137 fragmentos), el vocabulario es técnico y estable, no se depende de un
proveedor externo ni de red, y el resultado es determinista y explicable.
Antes de redactar, el generador consulta esta memoria y registra los
antecedentes (\texttt{data/memoria/consultas\_rag.jsonl}); si la similitud supera
0{,}35 avisa de posible solapamiento.

\textbf{(ii) Memoria estructural (grafo).} El proyecto se modela como un grafo
dirigido de \textbf{255 nodos y 500 aristas}:
\texttt{Criterio\,$\rightarrow$\,Documento} (completo/LITE),
\texttt{Documento\,$\rightarrow$\,T\'erminoGlosario},
\texttt{ArchivoCodigo\,$\rightarrow$\,Capa},
\texttt{Commit\,$\rightarrow$\,Autor}. Se construye con \textbf{networkx} a partir
de los metadatos que ya eran fuente de verdad (\texttt{objetivos.yaml},
\texttt{glosario.yaml}, \texttt{capas.yaml}, \texttt{commits\_timeline.csv},
\texttt{inventario\_codigo.csv}) \textbf{m\'as datos vivos del repositorio
auditado}: \texttt{git log} y \texttt{git ls-files} sobre el clon real en el
commit \texttt{1528939}. No se usó un motor de grafos externo
(Neo4j/Memgraph): con decenas de nodos y consultas simples no aporta ventaja y
sí costo de operación.

\textbf{(iii) Validación antes de compilar.} Doce reglas se ejecutan como
\textbf{puerta previa a la compilación del PDF final}, integradas en
\texttt{compilar.py} (si alguna falla, la compilación se aborta; puede omitirse
con \texttt{--forzar}). Las seis mínimas exigidas ---cada criterio con completo y
LITE; conclusiones registradas; veredicto resumido en el LITE; términos del
glosario realmente usados; línea de tiempo coincidente con el \texttt{git log}
real; y todo archivo de código referenciado en el documento del criterio de
código--- más seis adicionales (commit auditado, capas asignadas, cobertura de
fichas, integridad del grafo, cobertura del índice y LITE\,$\le$\,40\,\%).
Resultado real de la última ejecución: \textbf{8 PASA, 3 FALLA, 1 ADVERTENCIA},
con coincidencia exacta de \textbf{133/133 commits} y \textbf{51/51 archivos}
entre lo documentado y el repositorio real.

Declaramos también lo que \textbf{no} pasa, porque es parte del resultado: el
LITE del criterio~3 no tiene \texttt{lite\_veredicto} declarado; el término
``ETL'' está en el glosario pero no se usa en ningún documento; y
\texttt{src/\_\_init\_\_.py} no tiene capa asignada. Los tres quedan registrados
con su evidencia en \texttt{data/memoria/validacion\_reglas.json}.
```
