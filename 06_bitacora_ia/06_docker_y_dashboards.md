---
id: PUB-DOCKER
origen: sintesis
fase: "Operación"
tags: [docker, dashboards, reproducibilidad]
---

# 06 · Docker y dashboards

## Contenedor

El repositorio trae `Dockerfile` y `.dockerignore` para que el sistema se reproduzca igual en
Windows, macOS y Linux. Dentro del contenedor corren la validación y los paneles; no necesita
red.

```bash
# construir
docker build -t observatorio .

# correr la validación completa (las 17 reglas)
docker run --rm observatorio python -m memoria validar

# comprobaciones numéricas
docker run --rm observatorio python /app/documentacion_auditoria/src/verificar_consistencia.py

# servir los paneles en http://localhost:8000
docker run --rm -p 8000:8000 observatorio
```

El resultado esperado de la validación es el mismo que en local: **15 PASA · 0 FALLA · 2
ADVERTENCIA**.

## El CSV grande no va dentro de la imagen

`01_datos/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv` pesa unos
31 MB y es un **archivo en la nube** (marcador de posición del cliente de sincronización).
Docker no puede leer ese tipo de archivo virtual y el build falla con `invalid file request`.

Por eso:

- El CSV y `03_informes/` están excluidos en `.dockerignore` (el contenedor no los necesita
  para validar: trabaja con los JSON y el corpus).
- El CSV **sí queda versionado en Git**, así que la reproducibilidad no se sacrifica: si
  necesitas datos crudos dentro del contenedor, se monta por volumen:

```bash
docker run --rm -v "%cd%/01_datos:/app/01_datos" observatorio python -m memoria validar
```

Los datos también se pueden marcar como "Mantener siempre en este dispositivo" desde el
cliente de sincronización para que dejen de ser marcadores virtuales.

## Paneles HTML

Todos los paneles son **autocontenidos** (sin CDN, funcionan sin internet):

| Panel | Ruta | Contenido |
|---|---|---|
| Dashboard EDA | `02_dashboards/dashboard_eda.html` | Análisis exploratorio del padrón (4 pestañas) |
| Dashboard Fase 2 | `02_dashboards/dashboard_fase2.html` | 8 paneles de los análisis de Fase 2 |
| Trayectorias | `02_dashboards/herramienta_trayectorias.html` | Consulta la trayectoria de una persona por ID |
| Dashboard modelo | `02_dashboards/dashboard_modelo.html` | Modelo de ML (XGBoost con máscaras, F1 baja 0.4234) |
| Mapa de migración | dentro de Fase 2 / archivo propio | Evolución territorial por departamento |
| Presentación | `02_dashboards/presentacion.html` | Shell con barra lateral que navega a los cuatro anteriores |

### Importante: no abrir `presentacion.html` con doble clic

Chrome, Edge y Firefox **bloquean los iframes `file://`** por aislamiento de origen: el shell
se ve, pero los paneles salen en blanco. Hay que servirlo por HTTP:

```bash
cd 02_dashboards
python -m http.server 8000
# y abrir http://localhost:8000/presentacion.html
```

En Windows, `02_dashboards/servir_presentacion.bat` hace esas dos cosas: levanta el servidor y
abre el navegador en la URL correcta. Doble clic en el `.bat` = presentación funcionando.

## Notas de calidad

- Las paletas siguen la identidad institucional y el texto pequeño cumple contraste **WCAG AA**
  (el dorado institucional no alcanza AA sobre blanco; para texto se usa una variante más
  oscura).
- Si un panel se ve en blanco: revisar que se esté sirviendo por `localhost`, no por `file://`;
  y que el archivo exista en `02_dashboards/`.
- Los paneles no se modifican a mano: cada uno se genera con su script y se reemplaza entero.

Ver [[04_mapa_carpetas]] para la ubicación de cada pieza y [[05_que_no_tocar]] antes de mover
archivos.
