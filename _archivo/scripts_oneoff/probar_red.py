# -*- coding: utf-8 -*-
"""Sonda de red: determina si Python (OpenSSL) puede completar un TLS handshake
allá donde schannel falla con SEC_E_NO_CREDENTIALS."""
import io
import json
import socket
import ssl
import sys
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DESTINOS = [
    "https://www.dane.gov.co/",
    "https://pypi.org/simple/",
    "https://raw.githubusercontent.com/",
    "https://www.google.com/",
]


def probar(url: str) -> dict:
    salida = {"url": url, "cafile": ssl.get_default_verify_paths().cafile,
              "openssl": ssl.OPENSSL_VERSION}
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(url, timeout=20, context=ctx) as r:
            salida["status"] = r.status
            salida["bytes"] = len(r.read(4096))
    except urllib.error.HTTPError as e:
        salida["status"] = e.code
        salida["nota"] = "HTTPError (TLS OK)"
    except Exception as e:  # noqa: BLE001
        salida["error"] = f"{type(e).__name__}: {e}"
    return salida


def probar_sin_verificar(url: str) -> dict:
    """Descarta que el fallo sea de validación de certificado."""
    host = url.split("/")[2]
    try:
        ctx = ssl._create_unverified_context()
        with socket.create_connection((host, 443), timeout=20) as s:
            with ctx.wrap_socket(s, server_hostname=host) as ss:
                return {"host": host, "tls": ss.version(), "cipher": ss.cipher()[0]}
    except Exception as e:  # noqa: BLE001
        return {"host": host, "error": f"{type(e).__name__}: {e}"}


print("=== Python urllib (verificación normal) ===")
for u in DESTINOS:
    print(json.dumps(probar(u), ensure_ascii=False))

print("\n=== Handshake TLS sin verificar certificado ===")
for u in DESTINOS:
    print(json.dumps(probar_sin_verificar(u), ensure_ascii=False))

print("\n=== Rutas de CA por defecto ===")
print(ssl.get_default_verify_paths())

print("\n=== ¿existe certifi? ===")
try:
    import certifi
    print("certifi:", certifi.where())
except Exception as e:  # noqa: BLE001
    print("sin certifi:", e)
