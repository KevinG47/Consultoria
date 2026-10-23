# 00 · LEEME — Bitácora de IA de la consultoría (versión pública)

Esta carpeta es un **vault de Obsidian** con la parte publicable de la bitácora de IA del
proyecto *Auditoría estadística del Observatorio MinCiencias* (USTA, 2026-II).

No contiene transcripciones de chat: cada nota es una **síntesis** de las decisiones, la
arquitectura, las reglas de validación y el modo de uso del sistema. Está pensada para que
quien herede el repositorio entienda **cómo está construido** y **qué puede tocar sin romper
nada**.

## Cómo abrirlo en Obsidian

1. Descarga o clona la carpeta `06_bitacora_ia/` del repositorio.
2. Abre Obsidian → **Open folder as vault** → elige esta carpeta.
3. Abre `00_INDEX` y navega desde ahí.

Los archivos son Markdown puro con enlaces internos de Obsidian (doble corchete), así que
también se leen bien en GitHub, VS Code o cualquier visor de Markdown; Obsidian solo aporta el
grafo y la navegación.

## Por dónde empezar

| Si buscas… | Lee |
|---|---|
| Por qué el sistema es como es | [[01_decisiones_D001_D010_y_nota_metodologica]] |
| Cómo funciona la memoria y el RAG | [[02_arquitectura_memoria]] |
| Qué se valida automáticamente | [[03_reglas_validacion]] |
| Dónde está cada cosa | [[04_mapa_carpetas]] |
| Qué no se debe mover | [[05_que_no_tocar]] |
| Cómo correr Docker y los dashboards | [[06_docker_y_dashboards]] |

## Qué NO tocar

- `documentacion_auditoria/src/`, `documentacion_auditoria/data/` y
  `documentacion_auditoria/latex/`: los scripts y las 17 reglas usan rutas relativas exactas.
  Si se mueven, la validación y la compilación se rompen. Detalle en [[05_que_no_tocar]].
- El repositorio auditado (`Observatorio_Ministerio_de_Ciencias_Grupo8`): se consulta, no se
  modifica.

## Cómo se ve el grafo

Son 8 notas y **todas cuelgan de `00_INDEX`**, que actúa de nodo central. En la vista de
grafo de Obsidian se ve una estrella pequeña: el índice en el centro y las notas temáticas
alrededor, sin islas. Las notas se enlazan entre sí cuando una depende de otra (por ejemplo,
[[03_reglas_validacion]] apunta a [[02_arquitectura_memoria]] porque las reglas validan el
grafo y el índice del RAG).

## Estado del sistema (resumen)

- 17 reglas de validación → **15 PASA · 0 FALLA · 2 ADVERTENCIA**.
- La memoria se consulta con `python -m memoria {indexar, consultar, antes-de-redactar, grafo, dibujar, validar}`.
- La compilación de los PDF está **bloqueada** si alguna regla queda en FALLA.
- Hay contenedor Docker y cinco paneles HTML autocontenidos.

---

*Esta versión es un subconjunto curado. La bitácora completa (transcripciones) es material
interno y no se publica.*
