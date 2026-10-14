"""
Descarga el dataset consolidado de Producción de Grupos de Investigación de
MinCiencias desde datos.gov.co (Socrata) y lo guarda en datos/raw/.

El recurso 33dq-ab5a contiene la producción revisada y evaluada de los grupos
para las 6 convocatorias 2013-2021 (~3.2M filas). Se descarga paginado.

Llave de cruce con investigadores (bqtm-4y2h):
    produccion.id_persona_pd  ↔  investigadores.id_persona_pr
    produccion.id_convocatoria ↔ investigadores.id_convocatoria

Uso:
    python -m src.ingesta.produccion                  # descarga completa paginada
    python -m src.ingesta.produccion --limit 5000     # muestra para pruebas
    python -m src.ingesta.produccion --token TU_TOKEN # con app token Socrata
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from sodapy import Socrata

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

DOMAIN = "www.datos.gov.co"
SOCRATA_ID = "33dq-ab5a"
PAGE_SIZE = 50_000
RAW_DIR = Path(__file__).resolve().parents[2] / "datos" / "raw"
CATALOGO = Path(__file__).resolve().parents[2] / "datos" / "catalogo.yaml"
SALIDA = RAW_DIR / "produccion_grupos.csv"


def descargar(limit: int | None = None, app_token: str | None = None) -> pd.DataFrame:
    """Descarga paginada del dataset de producción.

    Si `limit` se especifica, hace una sola llamada con ese tope (modo prueba).
    En modo completo pagina con $offset hasta agotar el dataset.
    """
    client = Socrata(DOMAIN, app_token, timeout=300)
    log.info("Conectando a datos.gov.co — dataset %s …", SOCRATA_ID)

    if limit:
        registros = client.get(SOCRATA_ID, limit=limit)
        client.close()
        df = pd.DataFrame.from_records(registros)
        log.info("Descargados (modo limit=%d): %d filas, %d columnas",
                 limit, len(df), len(df.columns))
        return df

    paginas = []
    offset = 0
    while True:
        log.info("Página offset=%d limit=%d …", offset, PAGE_SIZE)
        chunk = client.get(SOCRATA_ID, limit=PAGE_SIZE, offset=offset, order=":id")
        if not chunk:
            break
        paginas.append(pd.DataFrame.from_records(chunk))
        offset += len(chunk)
        if len(chunk) < PAGE_SIZE:
            break
    client.close()

    df = pd.concat(paginas, ignore_index=True)
    log.info("Descargados (paginado): %d filas, %d columnas", len(df), len(df.columns))
    return df


def guardar(df: pd.DataFrame) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    log.info("Guardado en %s (%.1f MB)", SALIDA, SALIDA.stat().st_size / 1_048_576)


def actualizar_catalogo(df: pd.DataFrame) -> None:
    with open(CATALOGO, encoding="utf-8") as f:
        catalogo = yaml.safe_load(f)
    for fuente in catalogo["fuentes"]:
        if fuente.get("socrata_id") == SOCRATA_ID:
            fuente["ultimo_pull"] = datetime.today().strftime("%Y-%m-%d")
            fuente["tamanio_registros"] = len(df)
            break
    with open(CATALOGO, "w", encoding="utf-8") as f:
        yaml.dump(catalogo, f, allow_unicode=True, sort_keys=False)


def main(limit: int | None = None, app_token: str | None = None) -> None:
    df = descargar(limit=limit, app_token=app_token)
    guardar(df)
    if not limit:
        actualizar_catalogo(df)
    log.info("Ingesta completada.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingesta Producción de Grupos desde datos.gov.co")
    parser.add_argument("--limit", type=int, default=None,
                        help="Límite total de registros (modo prueba; sin paginación)")
    parser.add_argument("--token", type=str, default=None,
                        help="App token Socrata (recomendado para evitar throttling en 3M filas)")
    args = parser.parse_args()
    main(limit=args.limit, app_token=args.token)
