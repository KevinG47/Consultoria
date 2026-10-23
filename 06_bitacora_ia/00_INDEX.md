# 00 · Índice de la bitácora pública

Síntesis de la bitácora de IA del proyecto **Auditoría estadística del Observatorio
MinCiencias** (USTA, 2026-II). Ocho notas, cero wikilinks rotos.

| # | Nota | Qué responde |
|---|---|---|
| 01 | [[01_decisiones_D001_D010_y_nota_metodologica]] | Qué se decidió, cuándo y por qué (D001–D010), más la nota metodológica del análisis longitudinal |
| 02 | [[02_arquitectura_memoria]] | Cómo funciona la memoria del agente: RAG, grafo, CLI |
| 03 | [[03_reglas_validacion]] | Las 17 reglas: qué vigilan y el estado actual |
| 04 | [[04_mapa_carpetas]] | Mapa del repositorio, carpeta por carpeta |
| 05 | [[05_que_no_tocar]] | Zonas frágiles y por qué no se mueven |
| 06 | [[06_docker_y_dashboards]] | Reproducir con Docker y abrir los paneles |

## Orden de lectura sugerido

1. [[00_LEEME]] — cómo abrir el vault y por dónde empezar.
2. [[04_mapa_carpetas]] — ubicarse.
3. [[02_arquitectura_memoria]] — entender el sistema.
4. [[03_reglas_validacion]] — ver qué se comprueba solo.
5. [[01_decisiones_D001_D010_y_nota_metodologica]] — entender por qué se eligió cada pieza.
6. [[05_que_no_tocar]] y [[06_docker_y_dashboards]] — operar sin romper nada.

## Qué es y qué no es esta bitácora

- **Es** una fuente para el próximo equipo: decisiones, arquitectura, reglas y operación.
- **No es** el registro de conversaciones con las herramientas de IA que se usaron. Ese
  registro (transcripciones de los encargos y sus respuestas) es material interno y queda
  fuera de este repositorio.

## Estado actual del sistema

- **17 reglas** de validación → **15 PASA · 0 FALLA · 2 ADVERTENCIA**.
- **Compilación con puerta**: `compilar.py` aborta con código 2 si hay alguna FALLA.
- **Memoria**: `python -m memoria` (RAG con TF-IDF, grafo con networkx, reglas, CLI).
- **Docker**: imagen reproducible; los paneles HTML se sirven desde `02_dashboards/`.
