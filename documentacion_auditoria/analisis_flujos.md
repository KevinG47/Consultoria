# Flujos de migración territorial: el mapa de la Fase 2 (F2-11)

**Estado:** entregado y verificado. **Fecha:** 2026-10-17.
**Insumos:** base versionada de 77 237 registros (30 086 personas), F2-2
(`percapita_territorial.json`) y un GeoJSON de departamentos versionado con su
`.procedencia.txt`.
**Entregables:** `data/memoria/mapa_migracion.html` (5,39 MB, autocontenido),
la pestaña 8 de `data/memoria/dashboard_fase2.html` (la misma figura) y tres
figuras estáticas en `data/memoria/graficas_flujos/`.

---

## 1. Qué se hizo

El repositorio auditado tenía un mapa que **pedía las teselas de OpenStreetMap a
internet en el momento de dibujar** (`px.scatter_mapbox`, `streamlit_app.py:404-413`):
sin red, el país desaparecía y quedaban 33 burbujas flotando en el vacío. No había
ni un archivo de geometrías en todo el repositorio.

F2-11 construye el mapa que ese repositorio no tenía, con dos cambios de fondo:

1. **Los polígonos están en el repositorio.** Un GeoJSON de los 33 departamentos,
   limpio y redondeado a 4 decimales (527 675 B), se dibuja con `go.Choropleth`
   sobre un subplot `geo` con `fitbounds="locations"` y `visible=False`. No hay
   teselas, ni CDN, ni una sola petición: el mapa se abre sin internet.
2. **Dibuja flujos, no solo puntos.** El auditado nunca hizo un mapa de migración.
   Aquí las rutas van como líneas de origen a destino con el destino marcado.

Y una decisión que el mapa tiene que hacer visible desde la primera línea: **«se
mudaron entre 2013 y 2021» admite dos lecturas que dan números de tamaño muy
distinto**. Las dos están calculadas, verificadas y conmutables con un botón.

---

## 2. Las dos definiciones

### Flujo A — mudanza de residencia dentro del periodo (vista por defecto)

Para cada persona se compara el departamento de su **primera** convocatoria con el
de su **última**.

| | Valor |
|---|---:|
| Personas con dos o más convocatorias | 19 215 |
| … con departamento válido en las dos | 18 430 |
| **Que cambian de departamento** | **808 (4,38 %)** |
| Rutas distintas | 231 |
| Rutas con una sola persona | 110 |
| Las 10 primeras rutas explican | 31,93 % (258 personas) |
| Las 20 primeras rutas explican | 45,92 % (371 personas) |

| Ruta (top 10) | Personas |
|---|---:|
| Antioquia → Bogotá, D. C. | 38 |
| Bogotá, D. C. → Cundinamarca *(área metropolitana)* | 35 |
| Bogotá, D. C. → Boyacá | 32 |
| Bogotá, D. C. → Antioquia | 30 |
| Valle del Cauca → Bogotá, D. C. | 26 |
| Bogotá, D. C. → Valle del Cauca | 25 |
| Bolívar → Atlántico | 19 |
| Santander → Bogotá, D. C. | 19 |
| Cundinamarca → Bogotá, D. C. *(área metropolitana)* | 18 |
| Bogotá, D. C. → Atlántico | 16 |

**Saldo neto** (entradas − salidas, suma cero por construcción): Bogotá **−57**,
Cundinamarca **+31**, Boyacá **+21**, Atlántico **+20**, Magdalena +12, Huila +9;
en el otro lado, Bolívar −11, Caldas −10, Santander −7, Quindío −6, Sucre −6.
Catorce departamentos ganan y catorce pierden.

### Flujo B — residencia fuera del departamento de nacimiento (vista secundaria)

Migración acumulada de toda la vida, **no del periodo**.

| | Valor |
|---|---:|
| Personas comparables (nacimiento y residencia válidos) | 28 673 |
| **Que residen fuera de su cuna** | **11 922 (41,58 %)** |
| Rutas distintas | 577 |
| Las 10 primeras rutas explican | 29,20 % |

La primera ruta es **Exterior → Bogotá, D. C. (561 personas)**: no se puede dibujar
sobre un mapa de departamentos. En total, 1 402 personas en 25 rutas nacieron fuera
de Colombia y el mapa solo las declara en el texto. La mayor ruta **dibujable** es
Boyacá → Bogotá, D. C. (519).

### Por qué no se elige una y se tira la otra

- **A es pequeña.** 808 personas y una ruta máxima de 38. Comunica «casi nadie se
  mueve», que es un hallazgo legítimo pero no un espectáculo.
- **A no ve los movimientos intermedios**: quien se fue en 2015 y volvió en 2019
  cuenta como que no se movió, y 10 871 personas aparecen una sola vez, así que no
  pueden moverse por definición.
- **B tiene volumen** y por eso es tentador presentarla como «la migración real»,
  pero no es del periodo y su primera ruta nace fuera del país.
- **Comparar los dos números como si uno corrigiera al otro sería el error que este
  mapa intenta evitar.** No miden lo mismo.

---

## 3. El hallazgo incómodo: el área metropolitana

Las rutas Bogotá ↔ Cundinamarca no son ruido de captura. Lo comprobé porque era mi
primera sospecha:

- de las 808 personas que cambian de departamento, **las 808 cambian también de
  municipio** (0 conservan el mismo);
- los destinos de Bogotá → Cundinamarca son municipios concretos de la sabana:
  **Chía (14), Cajicá (9), Mosquera (4)**, y los orígenes de Cundinamarca → Bogotá,
  Chía (9), Cajicá (3), Fusagasugá (2).

Son **mudanzas reales de área metropolitana**. Pero ahí está el problema de fondo:
**en un mapa departamental una mudanza de Bogotá a Chía se ve igual que una
migración de Antioquia a Bogotá, y no son el mismo fenómeno.** Por eso las rutas
Bogotá ↔ Cundinamarca se dibujan con **trazo punteado, color más claro y rombo en el
destino** (decisión D2), con una nota visible en la página, en la pestaña 8 y en el
hover de cada ruta.

El criterio es geográfico y verificable: esas dos rutas son las únicas con evidencia
municipal de una misma conurbación. **No** se marca, por ejemplo, Bolívar →
Atlántico, que en los datos es Cartagena → Barranquilla: son dos áreas
metropolitanas distintas. Sin una tabla de áreas metropolitanas versionada no se
puede marcar más, y no se inventa.

---

## 4. Lo que el mapa dice y lo que no

- **Dirección:** Bogotá pierde 57 investigadores en el balance de las mudanzas y
  Cundinamarca (+31), Boyacá (+21) y Atlántico (+20) ganan. Es la lectura que el
  mapa de líneas no da por sí sola, y por eso la pestaña 8 añade el saldo neto.
- **Límite del instrumento:** un mapa de departamentos no puede separar la mudanza
  a la sabana de la migración interdepartamental. Se marca; no se disimula.
- **Plotly no dibuja puntas de flecha** sobre un subplot `geo`. La dirección se
  comunica con el **marcador del destino** y con el texto del hover
  («Antioquia → Bogotá, D. C. · 38 personas · 4,70 % de los 808 movimientos»).
  Prometer flechas sería prometer algo que la herramienta no da.
- **Solo se dibujan las 10 rutas mayores de cada definición** (decisión D3). Las 231
  rutas de A serían una maraña y el mensaje es la dirección, no la cola larga.

---

## 5. Cómo está construido

| Pieza | Decisión | Por qué |
|---|---|---|
| Color del polígono | Tasa per cápita de F2-2 (rampa azul, tope 140, tasa nacional marcada en 65,55) | Es la variable intensiva del territorio; se lee igual que en la pestaña 2 |
| Tamaño de la burbuja | √(investigadores), de 1 (Vichada) a 9 888 (Bogotá) | El ojo percibe área: con el valor bruto Bogotá taparía al país |
| Grosor de la línea | √(personas) | Idem, y con 38 personas el trazo sería invisible |
| Marca del destino | Punto (interdepartamental) · rombo (área metropolitana) | Dirección y D2 en el mismo canal |
| Centroides | Calculados del polígono (shoelace) y validados dentro de la geometría; 1 por rejilla de respaldo (Cundinamarca, cuyo centroide cae en el hueco de Bogotá) | Los 33 del auditado estaban escritos a mano |
| Llave de unión | `codigo_dane` (DIVIPOLA) | Los nombres no sirven: «SANTAFE DE BOGOTA D.C», «ARCHIPIELAGO DE SAN ANDRES…» frente a «Bogotá, D. C.» y «San Andrés, Providencia y Santa Catalina» |
| Hover | Departamento: nombre, tasa, investigadores, habitantes, puesto, cuota del stock y saldo neto. Ruta: origen → destino, personas y porcentaje | Es el requisito del encargo: datos per cápita de F2-2 **y** información del flujo |

El GeoJSON se versiona con su `.procedencia.txt`: URL, fecha de descarga, SHA-256
del original (1 519 607 B, 33 features) y SHA-256 del archivo ya limpio
(527 675 B, 34 191 → 28 894 vértices). Se regenera con
`python documentacion_auditoria/src/preparar_geojson.py`, que vuelve a descargar,
valida los 33/33 códigos y falla si algo no cuadra.

---

## 6. Límites

1. **A no ve mudanzas intermedias** ni a quien apareció una sola vez (10 871
   personas).
2. **La residencia es la que declara el registro en cada convocatoria**; no hay
   fecha de la mudanza, solo el intervalo entre convocatorias.
3. **El área metropolitana solo se puede marcar para Bogotá ↔ Cundinamarca** (no hay
   tabla de áreas metropolitanas versionada).
4. **B no es del periodo.** Se presenta como vista secundaria y así se etiqueta.
5. **El mapa no es una estimación**: son conteos censales de la base, no una muestra.
   Las tasas per cápita heredan los límites de F2-2 (denominador censado 2018).

---

## 7. Las decisiones que se aplicaron

| # | Decisión | Estado |
|---|---|---|
| D1 | Flujo A por defecto y B como vista secundaria, **conmutables** | Aplicada: botón en el mapa |
| D2 | Rutas de área metropolitana con otra forma/color y nota | Aplicada: punteado + rombo + nota visible |
| D3 | Top 10 rutas por definición | Aplicada |
| D4 | HTML suelto **y** pestaña 8 del panel | Aplicado: la misma figura, verificada traza a traza |
| D5 | Centroides calculados del polígono | Aplicado y validado |
| D6 | GeoJSON versionado con `.procedencia.txt` | Aplicado |
| D7 | No se toca la red de instituciones | Aplicado |
| D8 | `percapita_territorial.json` se lee tal cual | Aplicado: F2-11 no recalcula F2-2 |

---

## 8. Verificación

| Comprobación | Resultado |
|---|---|
| `src/verificar_mapa.py` | **64 comprobaciones, todas en verde** |
| `src/verificar_dashboard_fase2.py` (panel completo) | **77 comprobaciones, todas en verde** |
| Referencias externas en el mapa y en el panel | 0 |
| Peso del mapa / del panel | 5,39 MB / 5,63 MB (tope acordado: 6 MB) |
| Polígonos embebidos y unidos por `codigo_dane` | 33/33, idénticos al archivo versionado |
| Burbujas | 33 y suman 28 950 = stock de F2-2 |
| Rutas dibujadas | 8 + 2 (A) y 10 (B); destinos verificados contra el JSON |
| Centroides dentro de su polígono | 33/33 |
| La figura de la página suelta y la de la pestaña 8 | **idénticas** (comparación del JSON de trazas) |
| Reglas del proyecto | 15 PASA · 0 FALLA · 2 ADVERTENCIA (R12, R15) |

**Comprobación visual pendiente del usuario:** este entorno no puede abrir un
navegador (el sandbox bloquea los *named pipes* que necesita Chrome/Edge headless),
así que la revisión visual del encuadre, de los botones y de los hovers es manual.
Todo lo que dejaría la página en blanco (JS que no compila, etiquetas mal cerradas,
referencias externas) sí está verificado automáticamente.

---

## 9. Archivos

```
documentacion_auditoria/src/preparar_geojson.py          # descarga y limpieza del GeoJSON (una vez)
documentacion_auditoria/src/flujos_territoriales.py       # cálculo de A y B
documentacion_auditoria/src/mapa_migracion.py             # la figura y la página
documentacion_auditoria/src/verificar_mapa.py             # 64 comprobaciones
documentacion_auditoria/data/geo/colombia_departamentos.geojson
documentacion_auditoria/data/geo/colombia_departamentos.procedencia.txt
documentacion_auditoria/data/memoria/flujos_territoriales.json
documentacion_auditoria/data/memoria/mapa_migracion.html  # 5,39 MB, sin red
documentacion_auditoria/data/memoria/graficas_flujos/*.png
documentacion_auditoria/data/memoria/dashboard_fase2.html # pestaña 8
```

Para regenerar todo, en este orden:

```bash
python documentacion_auditoria/src/preparar_geojson.py     # solo si falta el GeoJSON
python documentacion_auditoria/src/flujos_territoriales.py
python documentacion_auditoria/src/mapa_migracion.py
python documentacion_auditoria/src/generar_dashboard_fase2.py
python documentacion_auditoria/src/verificar_mapa.py
python documentacion_auditoria/src/verificar_dashboard_fase2.py
```
