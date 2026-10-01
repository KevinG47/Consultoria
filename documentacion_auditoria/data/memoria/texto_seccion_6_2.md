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

**(i) Memoria semántica (RAG).** Indexamos el corpus documental —las secciones
LaTeX de los seis criterios, sus versiones LITE, el documento maestro, los once
informes de validación y este anteproyecto— en **150 fragmentos de 25 documentos**
(≈116 290 palabras). En su primera versión la recuperación se resolvió con
**TF-IDF (1–2 gramas, `sublinear_tf`) y similitud coseno** (decisión **D002**),
suficiente a esa escala y sin dependencias externas. **El docente decidió después
migrar a *embeddings* vía API key** (decisión **D007**) para que el proyecto sea
transferible y reproducible por otros equipos, dado que un "diccionario" de
términos es incómodo de mantener; esa migración queda **pendiente de
implementación** y así lo declara la bitácora, de modo que el cambio no se
pierde: la regla R15 lo detecta y falla mientras el código siga en TF-IDF. Antes
de redactar cualquier sección, el generador consulta esta memoria y registra los
antecedentes en `data/memoria/consultas_rag.jsonl`; si la similitud supera 0,35
avisa de posible solapamiento. Así evitamos repetir o contradecir lo ya escrito.

**(ii) Memoria estructural (grafo).** Modelamos explícitamente el proyecto como
un grafo dirigido de **255 nodos y 498 aristas**: `Criterio → Documento`
(completo/LITE), `Documento → TérminoGlosario`, `ArchivoCodigo → Capa`,
`Commit → Autor` y `Documento → Commit`. Se construye con **networkx** a partir de
los metadatos que ya eran fuente de verdad (`objetivos.yaml`, `glosario.yaml`,
`capas.yaml`, `commits_timeline.csv`, `inventario_codigo.csv`) **más datos vivos
del repositorio auditado**: `git log` y `git ls-files` sobre el clon real en el
commit `1528939`. No se usó un motor de grafos externo (Neo4j/Memgraph) porque
con decenas de nodos y consultas simples no aporta ventaja alguna y sí costo de
operación.

**(iii) Validación antes de compilar.** Diecisiete reglas se ejecutan como **puerta
previa a la compilación del PDF final**, integradas en `compilar.py` (si alguna
falla, la compilación se aborta; puede omitirse con `--forzar`). Las seis
mínimas exigidas —cada criterio con completo y LITE; conclusiones registradas;
veredicto resumido en el LITE; términos del glosario realmente usados; línea de
tiempo coincidente con el `git log` real; y todo archivo de código referenciado
en el documento del criterio de código— más once adicionales: commit auditado,
capas asignadas por regla explícita, cobertura de fichas, integridad referencial
del grafo, cobertura y frescura del índice, la regla LITE ≤ 40 %,
**contradicciones numéricas entre documentos** (R14), **coherencia entre las
decisiones y el código** (R15), **integridad de los registros de trazabilidad**
(R16) y **coherencia entre las cifras del sistema y los documentos que las citan**
(R17). Resultado de la ejecución final: **15 PASA, 1 FALLA, 1 ADVERTENCIA**, con
la coincidencia exacta de **133/133 commits** y **51/51 archivos** entre lo
documentado y el repositorio real. La única falla es, precisamente, el desfase
declarado de D007 (el código sigue en TF-IDF), que la regla reporta con archivo y
marcador.

**(iv) Trazabilidad de fuentes externas y de decisiones.** Dos registros en
`data/memoria/` documentan el trabajo del agente. `fuentes_externas.yaml` registra
cada fuente consultada (documentación, comparativas, especificaciones) con su URL
verificada, fecha, para qué se usó y qué archivo del proyecto depende de ella; la
regla R16 falla si alguna URL queda como "PENDIENTE". `decisiones.yaml` es la
bitácora de decisiones de diseño (**9 registradas**) con justificación,
alternativas descartadas, estado (*vigente*, *superada*, *propuesta*,
*pendiente_implementacion*) y la relación de supersesión explícita (p. ej. D007
supera a D002). La regla R15 verifica que ninguna decisión superada siga
implementada en el código ni presentada como vigente en los documentos, y que
exista una sola decisión actual por tema.

Las reglas detectaron **tres defectos reales** del material, corregidos en la
fuente de verdad y registrados con su evidencia en
`data/memoria/validacion_reglas.json`: el LITE del criterio 3 no tenía veredicto
declarado (`objetivos.yaml`); el término «ETL» figuraba en el glosario sin usarse
en ningún documento; y `src/__init__.py` no tenía capa asignada (`capas.yaml`).
La única advertencia restante es una sección de relación entre criterios que el
LITE comparte con el documento completo de forma deliberada.

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
los once informes de validación--- en \textbf{150 fragmentos de 25 documentos}
($\approx$116\,290 palabras). La recuperación usa \textbf{TF-IDF (1--2 gramas,
\texttt{sublinear\_tf}) con similitud coseno} (scikit-learn). Se eligió TF-IDF y
no \emph{embeddings} por cuatro razones a esta escala: el corpus es pequeño
(150 fragmentos), el vocabulario es técnico y estable, no se depende de un
proveedor externo ni de red, y el resultado es determinista y explicable.
Antes de redactar, el generador consulta esta memoria y registra los
antecedentes (\texttt{data/memoria/consultas\_rag.jsonl}); si la similitud supera
0{,}35 avisa de posible solapamiento.

\textbf{(ii) Memoria estructural (grafo).} El proyecto se modela como un grafo
dirigido de \textbf{255 nodos y 498 aristas}:
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

\textbf{(iii) Validación antes de compilar.} Diecisiete reglas se ejecutan como
\textbf{puerta previa a la compilación del PDF final}, integradas en
\texttt{compilar.py} (si alguna falla, la compilación se aborta; puede omitirse
con \texttt{--forzar}). Las seis mínimas exigidas ---cada criterio con completo y
LITE; conclusiones registradas; veredicto resumido en el LITE; términos del
glosario realmente usados; línea de tiempo coincidente con el \texttt{git log}
real; y todo archivo de código referenciado en el documento del criterio de
código--- más siete adicionales (commit auditado, capas asignadas por regla
explícita, cobertura de fichas, integridad del grafo, cobertura y frescura del
índice, LITE\,$\le$\,40\,\%, contradicciones numéricas (R14), coherencia entre
las decisiones y el código (R15), integridad de los registros de trazabilidad
(R16) y coherencia entre las cifras del sistema y los documentos que las citan
(R17)). Resultado de la ejecución final:
\textbf{15 PASA, 1 FALLA, 1 ADVERTENCIA}, con coincidencia exacta de
\textbf{133/133 commits} y \textbf{51/51 archivos} entre lo documentado y el
repositorio real.

Las reglas detectaron tres defectos reales del material, corregidos en la fuente
de verdad y registrados con su evidencia en
\texttt{data/memoria/validacion\_reglas.json}: el LITE del criterio~3 no tenía
veredicto declarado; el término ``ETL'' figuraba en el glosario sin usarse en
ningún documento; y \texttt{src/\_\_init\_\_.py} no tenía capa asignada. La única
advertencia restante es una sección de relación entre criterios que el LITE
comparte con el documento completo de forma deliberada.
```
