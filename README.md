# Consultoría Estadística USTA · 2026-II — Entrega 1 · Anteproyecto

**Equipo:** Kevin Leonardo Chaparro Reyes · Valentina Muñoz Palma · Paula Margarita Triana Ancinez
**Asignatura:** Consultoría Estadística — Universidad Santo Tomás
**Modalidad:** Proyecto con datos abiertos

**Proyecto:** *Auditoría estadística reproducible del sistema de reconocimiento de
investigadores de MinCiencias (2013–2021) con datos abiertos y propuesta de mejora
para su observatorio.*

---

## ⚠️ PARA EL DOCENTE — qué se califica en esta entrega

Todo lo calificable está en **`documentacion_auditoria/pdf/`**. Los demás archivos
del repositorio son fuente LaTeX, datos de respaldo o material de fases previas.

| Qué es | Archivo (PDF) | Bloque de la rúbrica |
|---|---|---|
| **Documento (anteproyecto)** | `documentacion_auditoria/pdf/anteproyecto.pdf` | **Documento (D1–D5) · 40 %** — 8 págs. de cuerpo, APA 7, declaración de IA en §6 |
| **Diapositivas de la sustentación** | `documentacion_auditoria/pdf/diapositivas_anteproyecto.pdf` | **Sustentación (S1–S3) · 60 %** (apoyo visual, 10 láminas / 10 min) |
| Guía de estudio (apoyo) | `documentacion_auditoria/pdf/guia_estudio.pdf` | repaso: reparto, frases clave, banco de preguntas |
| Tarjetas frase por frase (apoyo) | `documentacion_auditoria/pdf/tarjetas_sustentacion.pdf` | una página por integrante para ensayar |

> La **declaración de uso de IA** (cuánto se usó, para qué, cómo se validó con
> agentes independientes) está en la **sección 6.2 del anteproyecto**, con los
> informes de validación en `documentacion_auditoria/data/validacion/`.

---

## Estructura del repositorio

```
consultoria/
├── README.md                        ← este archivo (guía de entrada)
├── Rúbrica — Entrega 1 · Anteproyecto.pdf   (rúbrica oficial del curso)
├── informe_consultoria_observatorio_minciencias.md
│                                     ← fase previa 2026-I (diagnóstico del repo
│                                       auditado); NO es la Entrega 1
└── documentacion_auditoria/          ← carpeta de trabajo de esta consultoría
    ├── README.md                     ← documentación interna y cómo reproducir
    ├── pdf/                          ← ★ TODOS LOS PDF ENTREGABLES (lo que se califica)
    ├── latex/                        ← fuentes LaTeX por proyecto (Overleaf-ready)
    ├── zip_overleaf/                 ← ZIPs listos para subir a Overleaf
    ├── data/                         ← datos de auditoría (fichas, validaciones…)
    │   └── validacion/               ← informes de los agentes validadores
    └── src/                          ← scripts generadores y verificadores
```

### Nota sobre `informe_consultoria_observatorio_minciencias.md`

Es la **primera versión del diagnóstico técnico** del repositorio auditado,
elaborada en la fase 2026-I. **No es parte de la Entrega 1**: el entregable que se
califica con la rúbrica es el anteproyecto (`pdf/anteproyecto.pdf`) y la
sustentación. Se conserva como antecedente del proyecto.

### Repositorio auditado (referencia, no se versiona aquí)

El proyecto audita el repositorio público
[`ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8`](https://github.com/ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8)
(commit auditado `1528939`). El clon local no se incluye en este repositorio para
evitar duplicar 441 MB; toda la evidencia está documentada en `data/`.

---

## Cómo se construyó (reproducibilidad)

1. Cada PDF se compila desde su fuente LaTeX en `latex/<proyecto>/` (`compilar.py`).
2. Los ZIPs de Overleaf se generan con `crear_zips.py` (19 proyectos).
3. Los informes de validación con agentes independientes están en `data/validacion/`.
4. Reglas de calidad verificadas automáticamente (LITE ≤40 %, glosario por
   documento, orden canónico por capa, cobertura computada, commit auditado).
