# Declaración de uso de IA y reparto del trabajo

**Proyecto:** Auditoría estadística reproducible del sistema de reconocimiento de
investigadores de MinCiencias (2013–2021) con datos abiertos — Observatorio MinCiencias
**Asignatura:** Consultoría Estadística · Universidad Santo Tomás · 2026-II
**Integrantes:** Kevin Leonardo Chaparro Reyes · Valentina Muñoz Palma · Paula Margarita Triana Ancinez
**Repositorio de trabajo:** https://github.com/KevinG47/Consultoria
**Repositorio auditado:** https://github.com/ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8 (commit `1528939`)

> **Qué es este documento.** Declaración exigida por la rúbrica (S3). Amplía y hace
> verificable lo ya declarado en la **sección 6.2 del anteproyecto**
> (`documentacion_auditoria/pdf/anteproyecto.pdf`). Cada afirmación sobre el uso de IA
> y sobre el reparto se apoya en evidencia del propio repositorio, y **lo que no puede
> verificarse se marca explícitamente como no verificado** (ver §4).

---

## 1. Qué se generó con asistencia de IA y qué no

### 1.1 Asistido por IA (con dirección, revisión y decisión humanas)

| Producto | Archivos / evidencia | Grado de asistencia |
|---|---|---|
| Documentación de auditoría del repositorio auditado | `latex/maestro_auditoria/` (126 págs.), `latex/objetivo_1..6/` y sus `_lite` | Redacción y análisis de código **generados por IA** a partir del clon real; revisión del equipo |
| Estado del arte multilingüe | `latex/estado_del_arte/`, `pdf/estado_del_arte.pdf` (20 págs., 39 referencias) | Búsqueda de literatura, síntesis y bibliografía **generadas por IA**; verificación de referencias con agentes independientes |
| Sistema de memoria del agente (código) | `documentacion_auditoria/src/memoria/` (`rag.py`, `grafo.py`, `reglas.py`, `visual.py`, `herramientas.py`, `flujo.py`, `config.py`) | **Código escrito por IA**; alcance y decisiones dirigidos por el equipo |
| Verificación numérica y puerta de compilación | `src/verificar_consistencia.py` (refactor), `src/compilar.py` (puerta `_puerta_memoria`) | **Escrito por IA**; la exigencia de "que sea una puerta real" fue del docente |
| Anteproyecto (documento calificable) | `latex/anteproyecto/` → `pdf/anteproyecto.pdf` | Borradores **generados por IA**; el problema, el alcance y las exclusiones fueron decididos por el equipo |
| Material de sustentación | `pdf/diapositivas_anteproyecto.pdf`, `pdf/guia_estudio.pdf`, `pdf/tarjetas_sustentacion.pdf` | **Generado por IA**; reparto por integrante definido con el equipo |
| Informes de validación | `data/validacion/*.md` (19 archivos) | **Generados por agentes de IA independientes** (ver §3) |
| Verificación de referencias y fuentes | `data/memoria/fuentes_externas.yaml`, correcciones bibliográficas de este documento | **IA con búsqueda web**; decisión de qué corregir, del equipo |
| Registros de trazabilidad | `data/memoria/decisiones.yaml` (D001–D007), `fuentes_externas.yaml` | **Estructura y contenido redactados por IA**; D007 es decisión del docente |
| Empaquetado y publicación | `ENTREGA_1/`, `README.md`, `.gitignore`, 19 ZIP Overleaf, commits | **Ejecutado por IA** en el entorno del equipo |

### 1.2 NO asistido por IA

- **El código y la documentación del repositorio auditado** (236 archivos, 51 archivos
  de código, 133 commits, 11 autores): es obra del **equipo auditado** (Grupo 8, 2026-I),
  no de este equipo ni de la IA. Nuestra contribución es la auditoría, no el sistema auditado.
- **La rúbrica y los requisitos del curso**, incluidos los de la actividad "Nada sin fuente"
  y la decisión de migrar el RAG a *embeddings* (decisión **D007**): son del docente.
- **La interpretación del problema de consultoría** y la elección del objeto de auditoría:
  decididas por el equipo.
- **Los nombres, roles y la disponibilidad horaria** de los integrantes: aportados por el equipo.
- **La aprobación final y la sustentación oral**: humanas e individuales; ningún material
  sustituye la defensa (criterio S1, individual, 28 % con techo de nota).

### 1.3 Casos concretos en que se descartó lo que devolvió la IA

1. Un agente de validación afirmó un *bug* en `diversidad.py` (comparación `"SÍ"`/`"SI"`);
   al leer y ejecutar el código se comprobó que la normalización previa lo resolvía: la
   afirmación se corrigió.
2. Un agente reportó un supuesto "orden alfabético" de archivos que en realidad era el
   orden canónico por capa: era un artefacto de su propio verificador.
3. Aparecieron tres defectos en mi propio código de validación al ejecutarlo sobre datos
   reales (limpiador LaTeX que borraba rutas de archivos, regex del commit auditado y
   alcance de la regla R13). Se corrigieron y quedaron documentados en el historial de commits.

---

## 2. Herramientas de IA utilizadas y para qué

| Herramienta | Versión / forma de uso | Para qué se usó |
|---|---|---|
| **DeepSeek Harness (DSH)**, modelo `deepseek-v4-flash` | `@deepseek-ai/dsh` **0.1.1-rc.2** (paquete local) | Agente principal: análisis del repositorio auditado, generación de los documentos LaTeX, escritura del sistema de memoria, verificación de referencias, empaquetado y publicación |
| **Agentes de validación independientes** (subagentes del mismo entorno) | ~16 ejecuciones en 4 rondas | Auditoría de código, validación fáctica, de reglas, de rúbrica, de cobertura/referencias del estado del arte y validación de cierre de los bloques D y S (informes en `data/validacion/`) |
| **Búsqueda web asistida** | Integrada en el agente | Verificar la existencia real de referencias (Revista CTS 2010, Cañibano & Bozeman, Wang & Barabási, Sabharwal) y completar el registro `fuentes_externas.yaml` |
| **Herramientas no generativas** (declaradas para completitud) | Python 3.11 (pandas, numpy, scipy, scikit-learn, networkx, matplotlib, plotly, PyMuPDF, PyYAML), LaTeX/TinyTeX, git, Overleaf | Ejecución de los análisis, compilación de PDF, control de versiones y empaquetado |

**Uso declarado de forma honesta:** el uso de IA fue **intensivo en producción**
(borradores, código, fichas y material de apoyo) y **nulo en la autoría de las
decisiones finales**. Todo el contenido fue revisado, corregido y aprobado por el
equipo antes de entregarse, y cada afirmación sobre el repositorio auditado se verificó
de forma empírica (ejecución real de scripts, conteos contra los archivos, `git log`).

---

## 3. Cómo verificar esta declaración (comandos reales)

```powershell
cd "C:\Users\InfoPersonal\OneDrive - Universidad Santo Tomás\Escritorio\consultoria"

git log --oneline                                   # 22 commits del repositorio de trabajo
git log --pretty=format:"%an|%ae|%s"                # autoría real de cada commit
cd documentacion_auditoria\src
python -m memoria validar                           # 16 reglas de validación (exit 1 si hay FALLA)
python -m memoria evidencia                         # informe de la última ejecución
python -m memoria consultar "declaración de uso de IA" -k 5   # qué se dijo antes sobre el tema
```

Los informes de los agentes de validación están en
`documentacion_auditoria/data/validacion/` (19 archivos, incluidos
`validacion_cierre_D.md` y `validacion_cierre_S.md`).

---

## 4. Reparto del trabajo — qué está verificado y qué no

### 4.1 Lo que la evidencia del repositorio muestra (verificado)

```text
$ git log --pretty=format:"%an" | sort | uniq -c
     13 Kevin Leonardo Chaparro Reyes
      9 KevinG47
```

**Los 22 commits del repositorio de trabajo están atribuidos a Kevin** (dos variantes del
mismo nombre de configuración de git; el correo es el mismo en todos:
`kevin47gremory@gmail.com`). El repositorio **no contiene evidencia de commits,
ramas o autorías de Valentina ni de Paula**.

> **Declaración honesta:** por lo anterior, **el repositorio no puede certificar por sí
> solo el reparto real del trabajo entre los tres integrantes** (el trabajo de revisión y
> verificación no deja commits). Escribir aquí un reparto "parejo" habría sido inventarlo.
> Lo que sigue es el reparto **declarado por el equipo**, que asume su veracidad con la
> firma de la §5.

### 4.2 Reparto del trabajo declarado por el equipo

Los roles provienen de la sección 6.1 del anteproyecto (redactada a solicitud del equipo
y marcada allí como *"Ajustable a la división real del trabajo"*); la naturaleza del
aporte fue precisada por el equipo para esta declaración:

| Integrante | Rol declarado | Naturaleza del aporte |
|---|---|---|
| **Kevin Leonardo Chaparro Reyes** | Ingesta y auditoría de calidad de datos (OE1); reproducibilidad del pipeline; operación del repositorio y de las herramientas | **Desarrollo**: código del sistema de memoria, documentos de auditoría, integración con la IA y ejecución de la carga de desarrollo |
| **Valentina Muñoz Palma** | Análisis longitudinal (OE2) y programación estadística | **Auditoría manual y verificación** (ver abajo) |
| **Paula Margarita Triana Ancinez** | Estado del arte, análisis de equidad (OE3) y coordinación de la redacción y la sustentación | **Auditoría manual y verificación** (ver abajo) |

**Aporte de Valentina Muñoz Palma y Paula Margarita Triana Ancinez.** Contribuyeron
mediante **auditoría manual**: verificación directa de las referencias bibliográficas del
estado del arte (abriendo cada enlace y confirmando que el contenido correspondiera a la
cita), y verificación cruzada de cifras del proyecto contra el *dashboard* de Streamlit
del repositorio auditado. Adicionalmente, **Valentina ejecutó el pipeline de ingesta
completo sobre el repositorio original** para confirmar cifras clave contra la fuente
primaria. Estas contribuciones fueron de **revisión y verificación, no de desarrollo de
código**, razón por la cual **no generaron commits** en el repositorio: el trabajo de
implementación (código del sistema de memoria, documentos de auditoría, integración con
la IA) fue ejecutado por **Kevin Leonardo Chaparro Reyes**, quien concentró la mayor parte
de la carga de desarrollo del proyecto.

> **Nota de trazabilidad:** esta es la declaración del equipo sobre su propio reparto. El
> repositorio, por sí solo, **no puede evidenciar** las contribuciones de revisión y
> verificación descritas (no dejan commits), de modo que quedan respaldadas por esta
> declaración y por la firma de los tres integrantes (§5). El `git log` sí evidencia, en
> cambio, que todo el desarrollo registrado fue ejecutado por Kevin (§4.1).

**Dedicación declarada:** 1 hora diaria después de clases (en la noche), 6 días a la
semana por integrante = 6 h/semana × 3 integrantes × 12 semanas = **216 h**, frente a
una carga estimada de 180 h (17 % de holgura). Esta cifra fue aportada verbalmente por
el equipo; **no existe registro de seguimiento de horas** en el repositorio.

### 4.3 Aclaración importante sobre la autoría del repositorio auditado

El repositorio **auditado** tiene 133 commits de **11 autores** (entre ellos
`camiloacr1322`, `Victor-Diaz-Usta`, `Maria Amaya`, `JulianMendez27`, `PaulaGuevara`,
`Ustadistica Bot`, `copilot-swe-agent[bot]`). **Ninguno de esos autores es una fuente
válida para el reparto de nuestro trabajo**: son el equipo auditado del semestre 2026-I.
En particular, las cuentas que contienen "Paula" en ese repositorio **no** deben
confundirse con la integrante Paula Margarita Triana Ancinez.

### 4.4 Qué falta para cerrar esta declaración

1. ✅ **Resuelto:** el reparto declarado y el aporte de cada integrante constan en §4.2
   (revisión/verificación de Valentina y Paula; desarrollo de Kevin).
2. Pendiente de precisar: **qué pieza concreta revisó cada una** (anteproyecto, estado
   del arte, cifras del dashboard), si se quiere detalle adicional al ya declarado.
3. Si se desea trazabilidad individual hacia adelante: que cada integrante haga commits
   propios (o se registre la autoría en los mensajes de commit) desde este punto.
4. **Firmas:** completar la tabla de la §5 con las tres firmas y la fecha de entrega.

---

## 5. Firma y fecha

Declaramos que la información anterior es fiel a lo ocurrido en el desarrollo del trabajo
y que el uso de herramientas de IA se realizó como apoyo, bajo nuestra dirección y
responsabilidad, con revisión y aprobación humanas.

| Integrante | Firma | Fecha |
|---|---|---|
| Kevin Leonardo Chaparro Reyes | | |
| Valentina Muñoz Palma | | |
| Paula Margarita Triana Ancinez | | |
