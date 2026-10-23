---
id: PUB-REG
origen: sintesis
fase: "Reglas de validación"
tags: [reglas, validacion, trazabilidad]
---

# 03 · Reglas de validación

Las 17 reglas están en `documentacion_auditoria/src/memoria/reglas.py` y se ejecutan con
`python -m memoria validar`. Cada regla devuelve `PASA`, `FALLA` o `ADVERTENCIA`, y
`compilar.py` **bloquea la compilación** si hay alguna FALLA (decisión D006).

## Estado actual

**17 reglas → 15 PASA · 0 FALLA · 2 ADVERTENCIA**

Las dos advertencias son R12 (una sección compartida entre documentos completo y LITE,
deliberada) y R15 (la migración a embeddings está registrada como pendiente, así que el
código y la decisión vigente no coinciden todavía). El mismo resultado se obtiene en local y
dentro del contenedor Docker.

## Qué vigila cada regla

| Regla | Comprueba |
|---|---|
| R1 | Cada criterio tiene documento completo **y** LITE |
| R2 | Todo documento completo tiene conclusiones registradas |
| R3 | Todo documento LITE tiene veredicto resumido |
| R4 | Todo término del glosario se usa de verdad en algún documento |
| R5 | La línea de tiempo documentada (`commits_timeline.csv`) coincide con el `git log` real |
| R6 | Todo archivo de código del repositorio auditado aparece referenciado en el documento del criterio de código |
| R7 | El commit auditado documentado coincide con el HEAD real del clon |
| R8 | Todo archivo del repositorio auditado está clasificado explícitamente en `capas.yaml` |
| R9 | Existe ficha de análisis de código para cada archivo del inventario |
| R10 | Integridad referencial del grafo: nodos, aristas, documentos y PDF |
| R11 | El índice del RAG cubre exactamente el corpus declarado |
| R12 | Los documentos LITE no exceden el 40 % y no copian secciones literales del completo |
| R13 | El índice del RAG está al día respecto a las fuentes |
| R14 | No hay contradicciones numéricas entre documentos (mismo dato, cifras distintas) |
| R15 | Las decisiones registradas coinciden con lo que hace el código (y no se cita como vigente una decisión superada) |
| R16 | Ninguna fuente externa queda con URL en `PENDIENTE` |
| R17 | Las cifras que los documentos citan del propio sistema coinciden con la última corrida |

## Para qué sirve esto

- **Trazabilidad:** cada afirmación del material tiene que poder rastrearse a un archivo, un
  YAML o una cita (ver R1–R5, R11, R17).
- **Consistencia interna:** el sistema detecta cuando un documento dice una cifra y otro dice
  otra (R14), cuando una sección se copió del documento completo (R12) o cuando el índice
  quedó desactualizado (R13).
- **Vigilancia de sí mismo:** R15 y R17 hacen que el sistema audite sus propios registros: si
  se registra una decisión nueva, R17 detecta que algún documento sigue citando el recuento
  anterior.

## Cómo se corre

```bash
python -m memoria validar            # las 17 reglas, con su estado y detalle
python documentacion_auditoria/src/verificar_consistencia.py   # comprobaciones numéricas (R14)
```

La compilación normal (`compilar.py`) ejecuta la validación antes de generar cada PDF y se
detiene si algo falla. Con `--forzar` se puede omitir la puerta, pero el paso queda registrado.

## Cuando una regla falla de verdad

1. Leer el mensaje literal de la regla: dice qué archivo y qué dato no cuadra.
2. Corregir **la fuente** (el YAML, el `.tex`, la decisión registrada), no el PDF generado.
3. Volver a correr `python -m memoria validar` y luego `python -m memoria indexar` si cambió
   el corpus.
4. Solo si el fallo es un falso positivo de la regla, corregir la regla — y anotarlo en
   `decisiones.yaml`.

Ver [[02_arquitectura_memoria]] para las piezas que validan y [[01_decisiones_D001_D010_y_nota_metodologica]] para
D006, D008, D009 y las reglas R15 y R17 que nacieron con ellas.
