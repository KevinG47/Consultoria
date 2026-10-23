---
id: PUB-NOTOCAR
origen: sintesis
fase: "Operación"
tags: [zonas-fragiles, rutas, riesgos]
---

# 05 · Qué no tocar (y por qué)

Hay tres zonas del repositorio que **no se mueven ni se renombran**. No es superstición: cada
una rompe algo concreto si se toca.

## 1. `documentacion_auditoria/src/`

- Ahí viven los scripts y las **17 reglas**. Las reglas abren archivos con rutas relativas
  exactas (por ejemplo, `../data/objetivos.yaml`).
- Si se mueve la carpeta o se cambia el nivel de profundidad, `python -m memoria validar`
  falla en bloque y `compilar.py` deja de compilar.
- Tampoco conviene renombrar módulos: la CLI se invoca como `python -m memoria`, y eso depende
  del nombre del paquete y del archivo `__main__.py`.

## 2. `documentacion_auditoria/data/`

- `capas.yaml`, `objetivos.yaml`, `glosario.yaml`, `commits_timeline.csv`,
  `inventario_codigo.csv` son **la fuente de verdad** de la auditoría: los documentos citan de
  ahí y las reglas comprueban contra ahí.
- `data/memoria/` guarda los registros (`decisiones.yaml`, `fuentes_externas.yaml`) y los
  artefactos (`rag_indice.json`, `grafo_resumen.json`, `validacion_reglas.json`).
- Si se edita un YAML, hay que **volver a correr** `python -m memoria indexar` y
  `python -m memoria grafo`; si no, el sistema sigue viendo la versión anterior.
- Los artefactos se pueden regenerar; los YAML de metadatos, no: se editan con cuidado.

## 3. `documentacion_auditoria/latex/`

- Son las fuentes de los PDF. Cambiar nombres de archivo o de `\input{}` rompe la compilación.
- Los `.tex` **no** se editan a mano para "arreglar" un dato que las reglas marcan: se corrige
  la fuente (el YAML o el CSV) y se recompila, o el fallo vuelve en la siguiente corrida.

## 4. El repositorio auditado

`Observatorio_Ministerio_de_Ciencias_Grupo8` se consulta, nunca se modifica:

- Es la evidencia externa del trabajo. Si se altera, la auditoría deja de tener sentido.
- Varias reglas comparan contra sus commits y sus archivos reales (R5–R9): cualquier cambio
  local invalida la comparación.
- Si necesitas otra referencia, clónalo en otra ruta y pasa la ruta por parámetro.

## Reglas prácticas

1. **Antes de mover algo, corre `python -m memoria validar`.** Si ya estaba en 15/0/2, tienes
   una foto del estado bueno.
2. Mueve, y vuelve a correr la validación. Si baja el número de PASA, retrocede.
3. No commitees artefactos regenerables junto con cambios de código: dificulta ver qué cambió
   de verdad.
4. Si un archivo grande de datos da error al leerlo en Windows o en Docker, sospecha del
   cliente de sincronización en la nube antes que del código (ver
   [[06_docker_y_dashboards]]).

## Cuando sí se puede mover

- `pdf/`: son salidas; se regeneran compilando.
- `zip_overleaf/`, `slides_*/`: empaquetados de entrega.
- Todo lo que esté en `.gitignore` y no sea fuente de verdad.

Detalle de las carpetas en [[04_mapa_carpetas]]; las reglas que se rompen, en
[[03_reglas_validacion]].
