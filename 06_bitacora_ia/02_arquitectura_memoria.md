---
id: PUB-ARQ
origen: sintesis
fase: "Arquitectura"
tags: [memoria, rag, grafo, cli]
---

# 02 · Arquitectura del sistema de memoria

El sistema vive en `documentacion_auditoria/src/memoria/` y se usa como una CLI. No depende de
ningún modelo de lenguaje para funcionar: es código determinístico (TF-IDF, networkx, reglas).

## Piezas

| Módulo | Qué hace |
|---|---|
| `rag.py` | Memoria semántica: índice TF-IDF (1–2 gramas, `sublinear_tf`) y similitud coseno sobre el corpus documental |
| `grafo.py` | Memoria estructural: grafo dirigido con networkx (`Criterio → Documento → Término de glosario`, `Commit → Autor`, `ArchivoCodigo → Capa`) |
| `reglas.py` | Las 17 reglas de validación (ver [[03_reglas_validacion]]) |
| `herramientas.py` / `__main__.py` | CLI (`python -m memoria …`) |
| `flujo.py` | Integración con el flujo real: consultar antes de redactar y validar antes de compilar |

## Comandos

```bash
python -m memoria indexar            # reconstruye el índice del RAG
python -m memoria consultar "..."    # recupera los fragmentos más cercanos
python -m memoria antes-de-redactar  # consulta guiada previa a escribir
python -m memoria grafo              # reconstruye el grafo
python -m memoria dibujar            # genera la visualización del grafo
python -m memoria validar            # corre las 17 reglas y reporta el estado
```

`indexar` y `grafo` **no se ejecutan solos**: si se edita `data/`, hay que volver a correrlos
o el sistema seguirá viendo la versión anterior.

## Artefactos

En `documentacion_auditoria/data/memoria/`:

| Archivo | Contenido |
|---|---|
| `rag_indice.json` | Índice del corpus (fragmentos, vocabulario) |
| `grafo_resumen.json` | Nodos y aristas del grafo |
| `validacion_reglas.json` | Resultado de la última corrida de las 17 reglas |
| `decisiones.yaml` | Registro de decisiones D001–D010 (ver [[01_decisiones_D001_D010_y_nota_metodologica]]) |
| `fuentes_externas.yaml` | Fuentes externas consultadas, con URL y para qué se usaron |
| `git_log_real.csv`, `git_ls_files_real.txt` | Caché del repositorio auditado (commits y archivos reales) |

Esos dos últimos cachés existen para que las reglas que comparan contra el repositorio
auditado funcionen incluso en un clon limpio, sin depender de la red.

## Corpus indexado

Secciones LaTeX de los documentos de auditoría (completos y LITE), el documento maestro, el
anteproyecto y los informes de validación. Tras el arreglo del indexador (decisión D008) el
índice quedó en **151 fragmentos / 123 505 palabras**.

## Estados de una regla

`PASA` · `FALLA` · `ADVERTENCIA`. La validación devuelve un código de salida que
`compilar.py` interpreta: con alguna FALLA, la compilación se detiene (decisión D006). El
estado actual es **15 PASA · 0 FALLA · 2 ADVERTENCIA**.

## Diseño y límites

- **TF-IDF, no embeddings** (D002, superada por D007): con un corpus pequeño y homogéneo,
  TF-IDF da resultados defendibles sin dependencias ni salida de datos. **D007 implementada
  con embeddings locales (Granite)**; la migración por API key queda declarada como deuda y
  vigilada por R15.
- **networkx, no Neo4j** (D003): la escala es de cientos de nodos; un motor externo sería
  infraestructura desproporcionada.
- **El grafo se alimenta del repositorio auditado real** (D005), clonado dentro del repo de
  trabajo, para comparar lo documentado contra lo que de verdad existe.

Ver [[03_reglas_validacion]] y [[05_que_no_tocar]].
