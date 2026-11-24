"""Carga los secretos en Vault para docker compose (contenedor vault-init)."""

import os
import sys
import time
import urllib.request

from iniciar import CON_VAULT, generar, preparar_postgres, preparar_vault


def esperar(addr: str, segundos: int = 60):
    fin = time.time() + segundos
    while time.time() < fin:
        try:
            with urllib.request.urlopen(f"{addr}/v1/sys/health", timeout=2):
                return
        except Exception:
            time.sleep(1)
    sys.exit(f"Vault no responde en {addr}")


def main():
    addr = os.environ["VAULT_ADDR"]
    esperar(addr)
    s = generar()
    s["vault_raiz"] = os.environ["VAULT_ROOT_TOKEN"]
    # La pasarela es externa: sus claves vienen del .env y payments las recibe por Vault.
    s["pasarela_key"] = os.environ["PASARELA_API_KEY"]
    s["pasarela_webhook"] = os.environ["PASARELA_WEBHOOK_SECRET"]
    if os.getenv("POSTGRES_ADMIN_URL"):
        s["bd"] = preparar_postgres(os.environ["POSTGRES_ADMIN_URL"])
        print(f"PostgreSQL listo: {len(s['bd'])} esquemas, cada uno con su rol; las URL quedan en Vault")
    ids = {n: os.environ[f"{n.upper()}_VAULT_TOKEN"] for n in CON_VAULT}
    preparar_vault(addr, s, ids)
    print(f"Vault listo: {len(ids)} servicios con su token de solo lectura")


if __name__ == "__main__":
    main()
