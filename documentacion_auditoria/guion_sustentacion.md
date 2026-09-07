# Guion de sustentación — 10 minutos · Entrega 1 · Anteproyecto

**Regla de la rúbrica:** la sustentación pesa 60 %; S1 es individual (cada quien
debe defender el *conjunto*). Este guion reparte los bloques, pero **todos deben
poder responder cualquier pregunta** (banco al final).

## Reparto sugerido de la exposición (10 min)

| # | Diapositiva | Quién presenta | Tiempo |
|---|---|---|---|
| 1 | Título (presentación) | Cualquiera (30 s) | 0:00–0:30 |
| 2 | El problema: qué audita | **Kevin** | 0:30–1:30 |
| 3 | Evidencia propia (cifras) | **Kevin** | 1:30–2:45 |
| 4 | La pregunta estadística | **Valentina** | 2:45–3:30 |
| 5 | Estado del arte y vacío | **Paula** | 3:30–5:00 |
| 6 | Objetivos | **Valentina** | 5:00–6:00 |
| 7 | Datos y método | **Kevin** | 6:00–7:15 |
| 8 | Alcance y riesgos | **Paula** | 7:15–8:00 |
| 9 | Por qué cabe en el semestre | **Valentina** | 8:00–9:00 |
| 10 | Cierre | **Paula** | 9:00–10:00 |

## Frases clave por bloque (decirlas, no leerlas)

1. **Problema (Kevin):** "MinCiencias reconoce a los investigadores por
   convocatorias y ese padrón alimenta decisiones de política y de carrera.
   Nadie ha auditado si ese registro es confiable, comparable y equitativo."
2. **Evidencia (Kevin):** "No lo decimos por intuición: el padrón público
   declara 77 237 registros, pero al abrirlo encontramos 50 891 filas con
   26 662 personas únicas y solo 3 de 6 convocatorias (781/2017, 833/2018 y
   894/2021); 22 edades superan los 100 años; Bogotá y Antioquia concentran
   el 51 %; 24 % de mujeres en Ingeniería frente a 48 % en ciencias médicas."
3. **Pregunta (Valentina):** "Traducimos eso a una pregunta estadística
   respondible: ¿el padrón es fiable, comparable entre convocatorias y
   equitativo?"
4. **Estado del arte (Paula):** "La literatura de la science of science y las
   métricas responsables ya fijó cómo auditar indicadores; en Colombia hay
   crítica al modelo pero no evidencia cuantitativa reproducible. Ese es el
   vacío que atendemos. Contrastamos dos enfoques: Markov y supervivencia."
5. **Objetivos (Valentina):** "Un general y tres específicos: calidad,
   dinámica longitudinal y equidad. Cada uno tiene evidencia de cumplimiento."
6. **Datos (Kevin):** "Todo son datos abiertos ya abiertos por nosotros:
   bqtm-4y2h y 33dq-ab5a en datos.gov.co. Método reproducible en Python."
7. **Riesgos (Paula):** "El riesgo principal —la discrepancia de datos— ya es
   un hallazgo del objetivo, no un bloqueo; tenemos holgura de dos semanas."
8. **Cierre (Paula):** "Entregamos un marco de indicadores y un tablero para
   que MinCiencias sepa qué tan confiable y equitativo es su sistema."

## Banco de preguntas probables (rúbrica pág. 12–13) y respuestas-plantilla

- **¿Quién sufre este problema y desde cuándo?** (Kevin/Paula) — MinCiencias y
  el SNCTI desde 2013 (6 convocatorias); investigadores cuya categoría
  condiciona su carrera; política pública que usa el padrón.
- **¿Cómo se resuelve hoy sin ustedes?** — Con análisis descriptivos y críticas
  normativas; sin auditoría reproducible de calidad/equidad del registro.
- **¿Qué pasa si nadie hace nada?** — Decisiones de política sobre un
  instrumento no auditado; inequidades no cuantificadas.
- **¿Qué fuente los hizo cambiar de idea?** (Paula) — Las críticas al modelo de
  categorización colombiano + la evidencia propia de 50 891 vs 77 237: el
  problema no era solo de diseño, era de registro.
- **¿Qué hicieron distinto los dos enfoques que contrastan?** (Valentina) —
  Markov supone homogeneidad; supervivencia modela el tiempo al evento con
  covariables; los contrastamos porque el supuesto markoviano puede violarse.
- **¿Por qué no es una repetición de lo ya leído?** (Paula) — Porque no existe
  la combinación calidad + longitudinal + equidad reproducible sobre estos
  datos abiertos.
- **Si cumplen los tres específicos, ¿ya resolvieron el general?** (Valentina)
  — Sí: calidad + comparabilidad + equidad agotan el general; el tablero y el
  marco de indicadores son producto final.
- **¿Con qué evidencia declaran cumplido el objetivo 2?** — Matrices de
  transición con IC, curvas Kaplan–Meier y un modelo Cox reproducibles.
- **¿Cuál de sus objetivos es en realidad una actividad?** (revisar en voz
  alta) — Ninguno: los tres empiezan con verbos verificables (cuantificar,
  estimar, cuantificar) y declaran evidencia.
- **¿Alguien ya abrió el archivo? ¿Cuántas filas tiene?** (Kevin) — Sí: XLSX
  verificado con 50 891 filas × 30 columnas; 26 662 personas únicas
  (`ID_PERSONA_PR`); 3 convocatorias (781/2017, 833/2018 y 894/2021). Ojo: la
  convocatoria 833 es "de 2018", pero su campo ANO_CONVO dice 06/12/2019 (fecha
  de resolución); si el jurado pregunta por el "2019", explicar que es la fecha
  de resolución de la 833/2018, no una cuarta convocatoria.
- **¿Qué variable responde al primer objetivo específico?** — EDAD_ANOS_PR,
  ID_PERSONA_PR (unicidad), ID_CONVOCATORIA/ANO_CONVO.
- **¿Qué hacen si en octubre el dato no llega?** (Kevin) — OE1–OE3 no dependen
  de la producción (~1,2 GB); el cruce con producción ya se ejecutó para la
  línea base (el 36,9 % es resultado archivado), así que ningún objetivo
  específico queda bloqueado; si hace falta actualizar, redescarga por API
  Socrata con contratos.
- **¿Qué decidieron dejar por fuera y por qué?** (Paula) — producción
  individual ($h$), modelos predictivos individuales y causalidad: fuera del
  alcance semestral y/o del dato.
- **¿Qué es lo más probable que salga mal?** (Kevin) — La discrepancia del
  consolidado; ya está caracterizada y es parte del hallazgo.
- **¿Cuántas horas por semana reales?** — 1 h diaria después de clases, en la
  noche, 6 días a la semana por integrante = 6 h × 3 integrantes × 12 semanas
  = 216 h; carga estimada 180 h; 36 h de holgura (17 %).
- **Explíquemelo usted, que no redactó esa sección** — cada quien practica el
  bloque de los demás (rotar: Kevin explica objetivos; Paula explica datos;
  Valentina explica riesgos).
- **¿Qué alternativa consideraron y por qué la descartaron?** (Kevin) —
  Producción individual con $h$: descartada por volumen (~1,2 GB) y foco.
- **Si le digo que su tercer objetivo sobra, ¿qué responde?** (Valentina) — Sin
  equidad el general queda incompleto: la pregunta incluye la dimensión
  distributiva explícitamente.
- **Resuma el problema en dos frases** — "El registro oficial de investigadores
  reconocidos no ha sido auditado. Queremos saber si es confiable, comparable y
  equitativo, con evidencia reproducible."
- **¿Qué les devolvió la IA que descartaron?** (cualquiera) — Un agente afirmó
  un bug falso (el "SÍ" de diversidad.py) y un orden alfabético que era
  canónico; se corrigieron al verificar el código.
- **¿Qué riesgo ético tiene este proyecto?** (Paula) — Datos personales y
  categorías sensibles (etnia, discapacidad, víctimas): Ley 1581 de 2012; no
  publicamos microdatos identificables (la seudonimización no elimina el riesgo
  de reidentificación; Rocher et al., 2019).
- **¿Cuál fue exactamente su aporte humano frente a la IA?** (cualquiera) — El
  problema, el alcance y las exclusiones (D1/D5) los decidió el equipo; la
  pregunta estadística, los objetivos y el contraste Markov vs. supervivencia
  (D2/D3/D4) los eligió el equipo; los scripts se ejecutaron y auditaron con
  criterio humano; y la interpretación, qué se descarta, qué se publica y la
  revisión final completa fueron humanas. La IA fue asistente, no autora.
- **¿Quién escribió qué y quién revisó qué?** (cualquiera) — Kevin: ingesta y
  calidad de datos (OE1) + reproducibilidad; Valentina: longitudinal (OE2) +
  programación estadística; Paula: estado del arte + equidad (OE3) +
  coordinación de redacción. Todos revisaron el conjunto (sección 6.1) y
  cualquiera de los tres responde cualquier bloque (S1).
- **¿Por qué empezaron por el problema y no por los datos?** (Kevin) — Porque
  el problema es la puerta bloqueante (D1) y determina qué datos se necesitan,
  no al revés; además el problema ya tenía evidencia propia (50 891 vs.
  77 237), lo que orientó el diseño.
- **Con solo dos transiciones entre las 3 convocatorias (781→833→894),
  ¿qué estiman con Kaplan–Meier/Cox?** (Valentina) — Modelamos la permanencia
  entre ondas consecutivas como supervivencia discreta/por intervalos; es un
  análisis acotado y exploratorio, y el contraste con Markov es metodológico
  (supuestos distintos), no una promesa de inferencia fina. (El "2019" que a
  veces se cita es la fecha de resolución de la 833/2018, no una onda extra.)

## Checklist 5 minutos antes

- [ ] Portada con los tres nombres (PDF del anteproyecto).
- [ ] Llevar el PDF del anteproyecto, las diapositivas y esta guía.
- [ ] Memorizar los números críticos y que coincidan en documento, láminas y
      boca: 77 237 declarados vs. 50 891 filas y **26 662 personas únicas**
      verificadas; convocatorias 781/2017, 833/2018 y 894/2021 (el "2019" es la
      fecha de resolución de la 833/2018).
- [ ] Cada quien domina los bloques de los demás (rotación de 5 min).
- [ ] Respuestas orales de IA listas (cuánto/para qué/validación en 2 niveles/
      3 descartes) coherentes con la sección 6.2.
- [ ] Plan B si falla el proyector: las cifras clave van en esta guía.
- [ ] Cronómetro: 10 min sin recortar el cierre.
