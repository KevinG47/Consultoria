# Estudio de viabilidad — Mapas interactivos y flujos territoriales (F2-11)

**Estado:** aprobado y ejecutado. El mapa está construido: ver
`analisis_flujos.md` y `02_dashboards/mapa_migracion.html`. Este documento queda
como el registro de la decisión —qué se descartó, qué se rescató y por qué—, no
como una propuesta abierta.
**Alcance:** decidir qué se rescata de los dos Streamlit del repositorio auditado y
cómo se construye, offline, un mapa de Colombia con burbujas por departamento y
flujos de migración.
**Fecha:** 2026-10-17.

---

## 1. Resumen ejecutivo

1. El mapa del auditado **no usaba ni Folium ni Altair ni un GeoJSON**: era un
   `px.scatter_mapbox` con `mapbox_style="open-street-map"`, es decir **teselas de
   OpenStreetMap descargadas por internet en el momento de dibujar**. Sin red, el
   mapa queda en gris con las burbujas flotando en el vacío.
2. **No había ni un archivo de geometrías en todo el repositorio.** Las únicas
   coordenadas eran 33 pares `(lat, lon)` escritos a mano en el propio dashboard.
3. El grafo «raro» no es un problema de datos: es un **Pyvis incrustado que carga
   vis-network y Bootstrap desde dos CDN** y que además pide un archivo **relativo
   que no existe** (`lib/bindings/utils.js`). Sin internet no se dibuja; con internet
   se dibuja como una maraña porque el diseño de fuerzas no separa 120 nodos densos.
   Y las cifras que la app le pone al lado **no coinciden con el archivo**
   (dice 2021 · 141 nodos · 61 componentes; el archivo es 2019 · 120 · 55).
4. **Lo único que pedía credenciales es la capa de ingesta**, y de forma opcional:
   un *app token* de Socrata para no ser limitado al bajar 3,2 millones de filas
   (~1,2 GB). Ni el mapa ni el grafo ni la app en sí necesitan credencial ninguna.
   Por eso **la ingesta en línea se descarta** y se trabaja con la base versionada.
5. **La técnica propuesta funciona y está probada** (sondeo en
   `_archivo/scripts_oneoff/sondear_mapa_plotly.py`): Plotly dibuja polígonos +
   burbujas + líneas de flujo con un GeoJSON embebido, **sin una sola referencia
   externa**. El GeoJSON pesa **527 KB** ya limpio (613 KB antes de quitar los
   vértices repetidos que deja el redondeo) y sus **33 códigos DIVIPOLA coinciden
   33/33** con los del DANE que ya usa F2-2.
6. **El insumo de flujos existe, pero es pequeño y hay que elegir la definición.**
   Hay 808 personas (4,38 %) que cambian de departamento de residencia entre su
   primera y su última convocatoria, repartidas en 231 rutas; o 11.922 personas
   (41,6 %) que residen fuera de su departamento de nacimiento, en 577 rutas.

---

## 2. Qué hay realmente en el repositorio auditado

Los «dos Streamlit» son estos, y no son dos dashboards:

| Archivo | Tamaño | Qué es |
|---|---:|---|
| `streamlit_app.py` (raíz) | 983 líneas · 46 KB | **El dashboard real**: 7 pestañas tipo capítulo. Aquí están el mapa y el grafo. |
| `app/streamlit_app.py` | 17 líneas · 392 B | **Un cartel**: fija el título y muestra «Dashboard en construcción». Cero datos, cero análisis. Es lo que ejecuta el `Dockerfile`. |

Es decir: el `Dockerfile` despliega el cartel y Streamlit Cloud despliega el
dashboard real; son dos productos distintos según la vía de despliegue. Para este
estudio lo relevante es que **no hay un segundo dashboard que rescatar**: la
segunda pieza no aporta nada técnico (ya estaba fichada como «eliminar» en
`data/analisis_codigo/app_streamlit_app.py.json`).

El dashboard real tiene siete secciones: Calidad, Trayectoria, **Territorio**,
Diversidad, **Redes**, Productividad y Datos crudos. Lo que interesa aquí está en
la 3 y la 5.

---

## 3. Las cuatro preguntas

### 3.1 ¿Qué librería usaba el mapa interactivo? → Plotly, no Folium ni Altair

`streamlit_app.py:404-413`, dentro de `seccion_territorial`:

```python
fig = px.scatter_mapbox(
    conteo_geo, lat="lat", lon="lon",
    size="Investigadores", color="Investigadores",
    color_continuous_scale="YlOrRd", size_max=60,
    zoom=4.5, center={"lat": 4.5, "lon": -74.0},
    mapbox_style="open-street-map",     # ← aquí está el problema
)
```

Ni `folium` ni `altair` aparecen en el archivo (comprobado por búsqueda). Todo el
dashboard es Plotly: `px.imshow`, `px.bar`, `px.line` y este único `px.scatter_mapbox`.

### 3.2 ¿De dónde sacaba las geometrías? → No había geometrías

- **No existe ni un `.geojson`, `.topojson`, `.shp` o `.kml` en todo el
  repositorio** (comprobado por búsqueda recursiva). Tampoco en el nuestro.
- `mapbox_style="open-street-map"` no dibuja polígonos: pide **teselas raster** a
  los servidores de OpenStreetMap durante el renderizado. Es un mapa *de fondo*, no
  un mapa de datos.
- Lo único geográfico que había en disco era un diccionario de **33 coordenadas
  escritas a mano** (`COORDENADAS_DEPTO`, líneas 61-80), usadas como centro de cada
  burbuja. Con eso el mapa *parece* geográfico, pero la forma del país la pone
  internet.

Consecuencias verificables de ese diseño:

| Problema | Evidencia |
|---|---|
| Sin internet no se ve el país | Las teselas son peticiones HTTPS en tiempo de renderizado |
| Las burbujas caen sobre un punto arbitrario | 33 centroides a mano, sin polígono que las contenga; Bogotá en (4,71, −74,07) |
| Faltan categorías sin aviso | `conteo_geo` filtra por `isin(COORDENADAS_DEPTO)` (línea 399): «Exterior» y «No disponible» desaparecen sin decirlo |
| El denominador es otro | `POBLACION_DANE_2018` está escrito a mano **en miles** (líneas 83-94) y **no es el CNPV 2018**: Antioquia 6.407 frente a 5.975 del censo; Valle 4.476 frente a 3.790 |

Ese último punto importa para nosotros: **las tasas per cápita de la app y las de
F2-2 no son comparables** porque usan denominadores distintos. F2-2 usa el censo
oficial (44.164.417) y reporta además la versión con población ajustada (48.258.494),
que es con la que el auditado parece haber trabajado. Si algún día se cita la tasa
de la app, hay que decir cuál de los dos denominadores lleva.

### 3.3 ¿Por qué el grafo de nodos se veía «raro»? → Cuatro causas, ninguna de datos

El grafo no es un gráfico de Plotly: es un **HTML de Pyvis incrustado** con
`st.components.v1.html` (`streamlit_app.py:635-645`), generado por
`scripts/sprint3_grafo_interactivo.py` → `analisis.redes.generar_html_pyvis`.

```html
<script src="lib/bindings/utils.js"></script>                        <!-- no existe -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/...vis-network...">
<script src="https://cdnjs.cloudflare.com/.../vis-network.min.js"></script>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/...">
```

1. **Depende de internet** (cdnjs + jsdelivr). En un equipo sin red, el iframe de
   750 px queda en blanco.
2. **Pide un archivo relativo que no está**: `lib/bindings/utils.js` es una ruta
   interna del paquete Pyvis; al copiar el HTML a `hallazgos/` ese `lib/` no viaja,
   así que la petición da 404 y parte del arranque de vis-network falla. Es el bug
   clásico de «generar con Pyvis y mover el HTML».
3. **El diseño es una maraña por construcción**: `net.barnes_hut(gravity=-8000,
   central_gravity=0.3, spring_length=120)` sobre el subgrafo de grado ≥ 2. Ese
   subgrafo tiene densidad **baja** (0,0314) pero está dominado por **un componente
   gigante de 111 de los 120 nodos (92,5 %)** —los 8 restantes son 3 nodos sueltos y
   cinco de grado 2—, así que el diseño de fuerzas lo comprime en una bola. Las
   etiquetas se cortan a 40 caracteres y se solapan; el fondo es `#1a1a2e` y el color
   del nodo va de azul a **rojo** según la intermediación, así que «rojo» —que en
   nuestro lenguaje visual significa alarma— aquí significa «puente».
4. **Las cifras del texto no coinciden con el archivo.** La app escribe
   «Grafo interactivo de co-filiación **(2021)**» y «Filtrado a instituciones con
   grado ≥ 2 **(141 nodos)**», y el *takeaway* dice «**61** componentes
   desconectados». Verificado leyendo el propio HTML y reconstruyendo el grafo desde
   los dos insumos posibles:

   | | Nodos | Aristas | Componentes | Subgrafo grado ≥ 2 |
   |---|---:|---:|---:|---:|
   | `sprint3_grafo_completo.html` (lo que contiene de verdad) | **446** | 503 | 55 | — |
   | `sprint3_grafo_filtrado.html` (lo que la app muestra) | — | — | — | **120** |
   | Reconstruido desde el XLSX del repo | 446 | 503 | 55 | 120 |
   | Reconstruido desde `datos/tarea_join/*.csv` | 446 | 503 | 55 | 120 |
   | **Lo que dice la app** | — | — | **61** | **141** |
   | Lo que dice el docstring del script | **498** | — | — | **146** |

   Y el año está mal: la doble afiliación **solo existe en 2019** (569 registros),
   no en 2021, como ya demostró F2-4. Con tres cifras distintas para el mismo
   grafo (498 / 446 reales, 146 / 120 reales, 61 / 55 reales), el gráfico no puede
   leerse con confianza aunque se dibuje bien.

**Lo que sí es valioso de esa sección**, y merece rescatarse: la idea de mostrar el
grafo filtrado a instituciones con más de un enlace en lugar del grafo completo. Es
la decisión correcta (el grafo completo es 73 % hojas) y es exactamente lo que
nuestro panel ya hace mejor con Plotly.

### 3.4 ¿Qué pedía credenciales, y por qué se descarta?

Solo dos archivos, y solo para **descargar** datos:

| Archivo | Qué usa | Credencial |
|---|---|---|
| `src/ingesta/minciencias.py` | `sodapy.Socrata(DOMAIN, app_token)`, dataset `bqtm-4y2h` | `--token` **opcional** |
| `src/ingesta/produccion.py` | `sodapy.Socrata(DOMAIN, app_token)`, dataset `33dq-ab5a` | `--token` **opcional** |

`DOMAIN = "www.datos.gov.co"`. El token es el *app token* público de Socrata, que no
autentica a un usuario: **solo evita el limitador de peticiones** cuando se bajan
3,2 millones de filas (~1,2 GB). En el código **no hay ningún secreto escrito**: el
token entra por línea de comandos y no se guarda.

Conclusión para el alcance: **ni el mapa ni el grafo ni el dashboard necesitan
credenciales.** Lo que necesitaban era *red*, y solo en dos momentos: el fondo del
mapa (teselas OSM) y la descarga inicial del dataset de producción. Como trabajamos
con la base versionada de 77.237 registros y con geometrías locales, **la ingesta en
línea queda fuera del proyecto** definitivamente. El dataset de producción sigue
siendo el insumo que falta para F2-1 (Q7), y eso no cambia con este trabajo.

---

## 4. Qué se rescata y qué no

| Pieza del auditado | Veredicto | Motivo |
|---|---|---|
| `app/streamlit_app.py` (cartel) | **Descartar** | No tiene contenido técnico |
| Sección 3 · mapa `scatter_mapbox` | **Rescatar la idea, no el código** | El fondo depende de internet y no hay polígonos |
| Sección 3 · barras per cápita | **Ya superada** | F2-2 la hace con censo oficial, IC y descomposición del Theil |
| Sección 3 · HHI | **Ya superada** | Está roto (bug de `shape`) y F2-2 lo reproduce valor a valor |
| Sección 5 · grafo Pyvis | **Ya superado por F2-4 y por el panel** | El panel lo dibuja en Plotly, offline, con la conclusión correcta (el corretaje está concentrado, pero ninguna institución resiste la corrección múltiple) |
| Sección 5 · idea de filtrar el grafo | **Rescatar** | Ya está aplicada en el panel |
| Textos pregunta → evidencia → hallazgo → *caveat* | **Rescatar la estructura** | Es una buena forma de presentar; nuestro panel ya la usa |
| Ingesta Socrata con token | **Descartar** | Innecesaria: la base está versionada |
| `Dockerfile` que despliega el cartel | **Descartar** | Es un defecto, no un recurso |

**Lo que falta y sí es nuevo:** el auditado nunca hizo un mapa de **flujos**. Ni con
teselas ni sin ellas. Eso es lo que aporta F2-11.

---

## 5. Propuesta de arquitectura para F2-11

### 5.1 Dos capas en una sola figura de Plotly, sin red

```
go.Figure
├── go.Choropleth  geojson = <GeoJSON embebido>
│                  locations = 33 códigos DIVIPOLA
│                  featureidkey = "properties.codigo_dane"
│                  z = tasa por 100 000 (F2-2)      → color del departamento
├── go.Scattergeo  lon/lat = 33 centroides
│                  size ∝ √(investigadores)         → burbuja
│                  color = escala institucional
│                  hover = depto · investigadores · tasa · IC
└── go.Scattergeo  por cada una de las 10 rutas: 2 puntos (origen, destino)
                   mode = "lines+markers", marcador en el destino
                   width ∝ √(personas)              → flujo
```

- `fig.update_geos(fitbounds="locations", visible=False)`: encuadra Colombia y apaga
  el fondo del mundo. **No hay teselas, no hay red.** El país lo dibujan los
  polígonos del GeoJSON.
- Los tres elementos comparten el mismo subplot `geo`, así que burbujas y flechas
  caen exactamente sobre los polígonos.
- **Sondeado y funcionando.** El sondeo (20 líneas, en `_archivo/`) produjo un HTML
  autocontenido de **5,20 MiB** con las 3 trazas y **cero** referencias externas.

### 5.2 Los datos

| Capa | Fuente | Estado |
|---|---|---|
| Burbujas: investigadores y tasa per cápita | `01_datos/resultados_json/percapita_territorial.json` (stock, 28.950 personas; tasa nacional 65,55) | **Ya existe** |
| Polígonos | GeoJSON de departamentos **por descargar una vez** y versionar | **Falta** |
| Centroides | Calculados del GeoJSON (media de vértices) o los 33 del auditado como contraste | Por decidir |
| Flujos | Cálculo nuevo sobre la base de 77.237 registros | **Falta** |

### 5.3 El GeoJSON: comprado una vez, empaquetado para siempre

No hay geometrías en el repositorio y `geopandas`, `shapely`, `pyproj`, `folium` y
`branca` **no están instaladas** (comprobado). Por eso el plan no depende de ninguna
de ellas: la limpieza del GeoJSON es `json` puro.

Fuente probada (descarga correcta, 1.484 KB, **33 features**):

```
https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/
be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json
```

Propiedades que trae: `DPTO` (código DIVIPOLA de 2 dígitos), `NOMBRE_DPT`, `AREA`,
`PERIMETER`, `HECTARES`. Se conservan solo las dos primeras.

**Peso, medido:** 34.191 vértices. Quitando las propiedades sobrantes y redondeando:

| Redondeo | Precisión aproximada | Peso |
|---|---:|---:|
| 2 decimales | ~1,1 km | 480 KB |
| 3 decimales | ~110 m | 546 KB |
| **4 decimales (recomendado)** | ~11 m | **613 KB** |
| 6 decimales (original) | ~0,1 m | 700 KB |

A 11 m de resolución un mapa nacional de burbujas no pierde nada. Medido al
ejecutar: el archivo final quedó en **527 675 B** (515 KB) con 4 decimales —los
5 297 vértices repetidos que deja el redondeo también se quitaron—, la página suelta
en **5,39 MB** y el panel en **5,37 MiB**, por debajo del tope de 6 MB acordado.

**La clave del join son los códigos, no los nombres.** Verificado: los 33 códigos del
GeoJSON coinciden **33 de 33** con los del CSV del DANE que usa F2-2, sin sobrantes
ni faltantes. Y los nombres confirman por qué no se puede unir por nombre —
`SANTAFE DE BOGOTA D.C`, `ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA
CATALINA`—, exactamente la trampa de nombres que ya documentamos en H6 y en la ERRATA.

Se versionaría como los CSV del DANE: el `.geojson` limpio más un
`colombia_departamentos.procedencia.txt` con URL, fecha de descarga y SHA-256 del
archivo original.

### 5.4 Los flujos: los números reales, antes de dibujar

Aquí está la decisión de fondo, porque «se mudaron entre 2013 y 2021» admite dos
lecturas y **dan resultados de tamaño muy distinto**:

**Definición A — cambio de residencia dentro del período.** Para cada persona se
compara el departamento de su primera convocatoria con el de la última.

| | Valor |
|---|---:|
| Personas con 2 o más convocatorias | 19.215 |
| … con departamento válido en ambas | 18.430 |
| **Que cambian de departamento** | **808 (4,38 %)** |
| Rutas distintas | 231 |
| Rutas con una sola persona | 110 |
| Las 10 primeras rutas explican | 31,9 % de los movimientos |

| Origen → destino (top 10) | Personas |
|---|---:|
| Antioquia → Bogotá, D. C. | 38 |
| Bogotá, D. C. → Cundinamarca | 35 |
| Bogotá, D. C. → Boyacá | 32 |
| Bogotá, D. C. → Antioquia | 30 |
| Valle del Cauca → Bogotá, D. C. | 26 |
| Bogotá, D. C. → Valle del Cauca | 25 |
| Bolívar → Atlántico | 19 |
| Santander → Bogotá, D. C. | 19 |
| Cundinamarca → Bogotá, D. C. | 18 |
| Bogotá, D. C. → Atlántico | 16 |

Saldo neto: **Bogotá −57**, Cundinamarca +31, Boyacá +21, Atlántico +20.

**Definición B — residencia fuera del departamento de nacimiento** (migración
acumulada, no del período):

| | Valor |
|---|---:|
| Personas comparables (nacimiento y residencia válidos) | 28.673 |
| **Que residen fuera de su cuna** | **11.922 (41,6 %)** |
| Rutas distintas | 577 |
| Las 10 primeras rutas explican | 29,2 % |

| Origen → destino (top 10) | Personas |
|---|---:|
| Exterior → Bogotá, D. C. | 561 |
| Boyacá → Bogotá, D. C. | 519 |
| Santander → Bogotá, D. C. | 370 |
| Valle del Cauca → Bogotá, D. C. | 336 |
| Cundinamarca → Bogotá, D. C. | 313 |
| Antioquia → Bogotá, D. C. | 305 |
| Bogotá, D. C. → Antioquia | 288 |
| Bogotá, D. C. → Cundinamarca | 274 |
| Tolima → Bogotá, D. C. | 265 |
| Bogotá, D. C. → Valle del Cauca | 250 |

**Lo que hay que decir en voz alta antes de elegir:**

- **A es pequeña.** 808 personas en 231 rutas: la ruta mayor son **38 personas**. Un
  mapa de flujos con esos tamaños comunica «casi nadie se mueve», que es un hallazgo
  legítimo pero hay que presentarlo como tal, no como un mapa espectacular.
- **Bogotá ↔ Cundinamarca y Bogotá ↔ Boyacá no son ruido**, y esto lo comprobé
  porque era mi primera sospecha. Las 808 personas que cambian de departamento
  **también cambian de municipio en los 808 casos (0 conservan el mismo)**, y los
  destinos son municipios concretos y verosímiles de la sabana: Bogotá →
  Cundinamarca va a **Chía (14), Cajicá (9), Mosquera (4), Arbeláez (2), Zipaquirá
  (2)**, y Cundinamarca → Bogotá sale de Chía (9), Cajicá (3), Fusagasugá (2),
  Madrid (2). **No es un artefacto de etiqueta: son mudanzas de área metropolitana.**
  Pero ahí está el problema real: en un mapa *departamental* una mudanza Bogotá → Chía
  se ve igual que una mudanza Antioquia → Bogotá, y no son el mismo fenómeno. Hay que
  decirlo en el documento y, si se quiere, marcarlo en el mapa.
- **A no ve los movimientos intermedios:** quien se fue en 2015 y volvió en 2019
  cuenta como que no se movió. Y 10.871 personas aparecen una sola vez, así que no
  pueden moverse por definición.
- **B es más rica y más robusta** (11.922 casos, 41,6 %), pero no es «entre 2013 y
  2021»: es de toda la vida. Y su primera ruta es **Exterior → Bogotá**, que no se
  puede dibujar sobre el mapa de departamentos.

### 5.5 Codificación visual

| Variable | Canal | Escala propuesta |
|---|---|---|
| Total de investigadores | **tamaño de la burbuja** | `√` del conteo: 1 → 9.888 sin que el pequeño desaparezca |
| Tasa por 100 000 (F2-2) | **color del polígono** | rampa azul institucional; leyenda con la tasa nacional (65,55) marcada |
| Flujo | **grosor de la línea** + marca en el destino | `√` de las personas; origen gris claro → destino azul |
| Departamento sin dato | gris claro + `hover` que lo dice | nunca cero |

Nota honesta: **Plotly no dibuja puntas de flecha reales sobre un subplot `geo`.**
La dirección se comunica con la marca en el extremo de destino y con el `hover`
(«Antioquia → Bogotá: 38 personas»), no con una flecha. Prometer flechas sería
prometer algo que la herramienta no da sin salirse de Plotly.

### 5.6 Verificación (el patrón que ya usamos)

El script de F2-11 incluirá sus propias comprobaciones y fallará si no cuadran:

1. los 33 códigos del GeoJSON iguales a los 33 del DANE (conjuntos idénticos);
2. suma de burbujas = 28.950 (el stock de F2-2), sin departamentos perdidos;
3. cada centroide cae **dentro** de su polígono (o a menos de X km de su frontera);
4. las rutas del Top 10 suman lo que dice el JSON;
5. el número de personas que cambian de departamento no supera a las que tienen 2+
   convocatorias;
6. el HTML final no contiene ninguna referencia externa y pesa menos de 6 MB.

Y un `verificar_mapa.py` en la misma línea que `verificar_dashboard_fase2.py`.

### 5.7 Entregables propuestos

```
documentacion_auditoria/src/flujos_territoriales.py       # el análisis (script)
01_datos/resultados_json/flujos_territoriales.json
documentacion_auditoria/data/geo/colombia_departamentos.geojson
documentacion_auditoria/data/geo/colombia_departamentos.procedencia.txt
documentacion_auditoria/data/memoria/graficas_flujos/     # 2-3 figuras
documentacion_auditoria/data/memoria/mapa_flujos.html      # mapa autocontenido
03_informes/analisis_fase2/analisis_flujos.md                 # documento (1-2 págs)
documentacion_auditoria/src/verificar_mapa.py
```

---

## 6. Qué reutilizamos de lo que ya tenemos

| Recurso existente | Uso en F2-11 |
|---|---|
| **F2-2** `percapita_territorial.json` | Tasas, stock, IC y la tasa nacional. **No se recalcula nada** |
| Paleta institucional + template de Plotly | Tal cual, con un solo template registrado |
| El patrón `div()` / bundle embebido | Ya probado en los dos paneles y en el sondeo |
| La clave DIVIPOLA de 2 dígitos | Verificado 33/33 contra el DANE |
| La lección de los nombres (San Andrés, Bogotá) | Unir por código, nunca por etiqueta |
| **F2-4** y el panel | La red ya está resuelta y mejor que en el auditado: F2-11 **no toca la red** |
| `verificar_dashboard_fase2.py` | Plantilla para el verificador del mapa |
| El patrón de fuentes externas (`.procedencia.txt`) | Para el GeoJSON |

Lo que **no** reutilizamos: nada de Pyvis, nada de `sodapy`, nada de `mapbox_style`,
nada de `st.components.v1.html`.

---

## 7. Riesgos y límites

| Riesgo | Mitigación |
|---|---|
| El GeoJSON tiene licencia o procedencia dudosa | Versionarlo con `.procedencia.txt` y declarar la fuente; el de john-guerra es el más usado y su origen es DIVIPOLA/IGAC |
| Los 808 movimientos son demasiado pocos para un mapa | Presentarlo como hallazgo («el 4,4 % se mueve»), no como espectáculo; o usar la definición B |
| Los flujos de área metropolitana se confunden con migración interdepartamental | Marcarlos (D2) y decirlo en el documento; no son ruido de captura, son otro fenómeno |
| Centroides fuera del polígono (deptos con islas) | Validación 3; para San Andrés usar el centroide del polígono principal |
| El `Dockerfile` y el Streamlit Cloud ya no son el destino | El entregable es HTML estático autocontenido: no hay despliegue que mantener |
| El mapa desvía de lo aprobado en el anteproyecto | F2-11 es un análisis **nuevo** (flujos), no una réplica: se declara como tal |

---

## 8. Plan de trabajo (estimado)

| Paso | Qué | Salida |
|---|---|---|
| 1 | Descargar y limpiar el GeoJSON; validar 33/33 códigos; escribir `.procedencia.txt` | `data/geo/*` |
| 2 | Calcular flujos A y B; decidir cuál va al mapa; cuantificar el ruido Bogotá↔Cundinamarca | `flujos_territoriales.json` |
| 3 | Escribir el script del mapa (burbujas + polígonos + Top 10) y las figuras | `mapa_flujos.html` + figuras |
| 4 | Documento de 1-2 páginas con la conclusión y los límites | `analisis_flujos.md` |
| 5 | Verificador + panel (si se aprueba) + reglas 15/0/2 | `verificar_mapa.py` |

Los pasos 1 y 2 son la mitad del trabajo y son donde están las decisiones.

---

## 9. Decisiones: aprobadas y aplicadas

| # | Decisión | Opciones | Resolución |
|---|---|---|---|
| **D1** | ¿Qué definición de flujo va al mapa? | (a) cambio de residencia 2013→2021 · (b) nacimiento → residencia · (c) las dos, en dos pestañas | **Aprobada como (c): las dos conmutables, con (a) por defecto y (b) como vista secundaria.** Los dos resultados son legítimos y miden cosas distintas; esconder uno habría sido una decisión editorial. |
| **D2** | ¿Cómo se tratan las rutas de área metropolitana (Bogotá ↔ Chía, Cajicá, Mosquera…)? | (a) dibujarlas como cualquier otra · (b) excluirlas · (c) dibujarlas con otra forma o color y una nota | **Aprobada (c)**: trazo punteado, color más claro y rombo en el destino, con nota visible en la página y en el hover. |
| **D3** | ¿Cuántas rutas? | Top 10 (propuesto) · Top 20 (45,9 % de los movimientos) | **Aprobada Top 10**; el Top 20 queda como opción del gráfico (las 231 rutas completas están en el JSON). |
| **D4** | ¿El mapa es un HTML aparte o una pestaña nueva del panel? | (a) `mapa_flujos.html` autocontenido · (b) pestaña 8 de `dashboard_fase2.html` | **Aprobada: ambas**, generando además el HTML suelto. Son exactamente la misma figura; el verificador lo comprueba traza a traza. |
| **D5** | ¿Centroides del GeoJSON o los 33 del auditado? | (a) calculados del polígono · (b) los del auditado | **Aprobada (a)**; los 33 del auditado quedan solo como contraste en el documento. |
| **D6** | ¿Se versiona el GeoJSON limpio en el repositorio? | (a) sí, con `.procedencia.txt` · (b) se descarga en cada build | **Aprobada (a)**: sin él el análisis no es reproducible ni offline. |
| **D7** | ¿Toca F2-11 la red de instituciones? | (a) no · (b) sí, reemplazar el Pyvis | **Aprobada (a)**: el panel ya la dibuja mejor; F2-11 es de flujos. |
| **D8** | ¿Se toca el `percapita_territorial.json` o se lee tal cual? | (a) leerlo · (b) recalcular | **Aprobada (a)**: F2-2 ya está auditado; F2-11 no lo repite. |

Nota de la ejecución: el nombre del archivo suelto quedó **`mapa_migracion.html`**
(no `mapa_flujos.html`), porque cubre las dos definiciones de flujo y no solo una.
Los planos de trabajo y los verificadores están en `analisis_flujos.md`.

---

## 10. Anexo — evidencia de las comprobaciones hechas

| Comprobación | Resultado |
|---|---|
| ¿Hay `folium`/`altair` en el dashboard? | No. Todo es Plotly; el mapa es `px.scatter_mapbox` |
| ¿Hay geometrías en cualquier repositorio? | No: cero `.geojson`, `.topojson`, `.shp`, `.kml` |
| ¿Cuántos nodos tiene de verdad el grafo? | 446 completos / 120 filtrados (no 498 ni 146) |
| ¿Cuántos componentes? | 55 (la app dice 61) |
| ¿En qué año hay doble afiliación? | 2019 (la app dice 2021) |
| ¿Hay secretos en el código? | No: solo `DOMAIN = "www.datos.gov.co"`; el token es un argumento opcional |
| ¿El GeoJSON de departamentos se puede obtener? | Sí: 1.484 KB, 33 features, campos `DPTO`/`NOMBRE_DPT` |
| ¿Los códigos coinciden con el DANE? | 33 de 33, sin sobrantes ni faltantes |
| ¿Plotly dibuja el mapa sin red? | Sí: sondeo con 3 trazas y cero referencias externas |
| ¿Cuánto pesa? | GeoJSON 527 675 B (515 KB); página autocontenida 5,20 MiB en el sondeo y 5,39 MB con los datos reales |
| ¿Hay datos para los flujos? | Sí: 808 personas en 231 rutas (A) y 11.922 en 577 rutas (B) |
| ¿Las rutas Bogotá ↔ Cundinamarca son ruido de etiqueta? | **No**: las 808 personas cambian también de municipio (0 conservan el mismo) y los destinos son Chía, Cajicá, Mosquera, Zipaquirá. Son mudanzas de área metropolitana |
| ¿Cómo es el subgrafo que dibuja la app? | 120 nodos, 224 aristas, densidad 0,0314, **8 componentes con uno gigante de 111 nodos (92,5 %)** |
