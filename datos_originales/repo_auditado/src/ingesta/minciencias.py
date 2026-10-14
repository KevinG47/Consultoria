"""
Descarga el dataset consolidado de investigadores reconocidos de MinCiencias
desde datos.gov.co (Socrata) y lo guarda en datos/raw/.

El recurso bqtm-4y2h contiene todas las convocatorias 2013-2021 en un solo dataset.

Uso:
    python -m src.ingesta.minciencias                  # descarga completa
    python -m src.ingesta.minciencias --limit 1000     # muestra limitada (pruebas)
    python -m src.ingesta.minciencias --token TU_TOKEN # con app token Socrata
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
SOCRATA_ID = "bqtm-4y2h"
RAW_DIR = Path(__file__).resolve().parents[2] / "datos" / "raw"
CATALOGO = Path(__file__).resolve().parents[2] / "datos" / "catalogo.yaml"
SALIDA = RAW_DIR / "investigadores_consolidado.csv"


def descargar(limit: int | None = None, app_token: str | None = None) -> pd.DataFrame:
    client = Socrata(DOMAIN, app_token, timeout=120)
    kwargs = {"limit": limit} if limit else {"limit": 100_000}
    log.info("Conectando a datos.gov.co — dataset %s …", SOCRATA_ID)
    registros = client.get(SOCRATA_ID, **kwargs)
    client.close()
    df = pd.DataFrame.from_records(registros)
    log.info("Descargados: %d registros, %d columnas", len(df), len(df.columns))
    return df


def guardar(df: pd.DataFrame) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    log.info("Guardado en %s (%.1f MB)", SALIDA, SALIDA.stat().st_size / 1_048_576)


def actualizar_catalogo() -> None:
    with open(CATALOGO, encoding="utf-8") as f:
        catalogo = yaml.safe_load(f)
    catalogo["fuentes"][0]["ultimo_pull"] = datetime.today().strftime("%Y-%m-%d")
    with open(CATALOGO, "w", encoding="utf-8") as f:
        yaml.dump(catalogo, f, allow_unicode=True, sort_keys=False)


def main(limit: int | None = None, app_token: str | None = None) -> None:
    df = descargar(limit=limit, app_token=app_token)
    guardar(df)
    if not limit:
        actualizar_catalogo()
    log.info("Ingesta completada.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingesta MinCiencias desde datos.gov.co")
    parser.add_argument("--limit", type=int, default=None, help="Límite de registros (útil para pruebas)")
    parser.add_argument("--token", type=str, default=None, help="App token Socrata (evita throttling)")
    args = parser.parse_args()
    main(limit=args.limit, app_token=args.token)
