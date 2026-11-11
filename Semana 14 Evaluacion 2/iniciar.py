"""Levanta ChocoMania sin Docker. Uso: python iniciar.py [--reiniciar-datos] [--sin-php]"""

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SERV = RAIZ / "servicios"
LOGS = RAIZ / "logs"

PUERTOS = {
    "vault": 8200, "auth": 8100, "inventory": 9101, "orders": 9102, "clients": 9103,
    "payments": 9104, "graphql": 9200, "pasarela": 9300, "gateway": 8000, "sitio": 8080,
}
CARPETA = {
    "auth": "auth-service", "inventory": "inventory", "orders": "orders", "clients": "clients",
    "payments": "payments", "graphql": "graphql-gateway", "pasarela": "pasarela-sandbox", "gateway": "api-gateway",
}
# Quien puede llamar a quien. Cada flecha tiene su propia credencial.
LLAMADAS = {
    "auth": ["gateway"],
    "inventory": ["gateway", "orders", "graphql"],
    "orders": ["gateway", "payments", "graphql"],
    "clients": ["gateway", "graphql"],
    "payments": ["gateway", "graphql"],
    "graphql": ["gateway"],
}


ORDEN = ["vault", "auth", "inventory", "clients", "orders", "payments", "pasarela", "graphql", "gateway"]


def url(nombre: str) -> str:
    return f"http://127.0.0.1:{PUERTOS[nombre]}"


def generar() -> dict:
    cred = {(a, b): secrets.token_urlsafe(32) for b, llamadores in LLAMADAS.items() for a in llamadores}
    return {
        "cred": cred,
        "vault_token": secrets.token_urlsafe(24),
        "pasarela_key": "sk_test_" + secrets.token_urlsafe(24),
        "pasarela_webhook": "whsec_" + secrets.token_urlsafe(32),
    }


def entornos(s: dict) -> dict[str, dict]:
    cred = s["cred"]

    def callers(servicio):
        return json.dumps({a: cred[(a, servicio)] for a in LLAMADAS[servicio]})

    base = {"PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"}
    urls = {f"{n.upper()}_URL": url(n) for n in ("auth", "inventory", "orders", "clients", "payments", "graphql")}
    return {
        "vault": {**base, "VAULT_TOKEN": s["vault_token"], "VAULT_PORT": str(PUERTOS["vault"]),
                  "VAULT_DATA": json.dumps({"gateway": {b: cred[("gateway", b)] for b in LLAMADAS if "gateway" in LLAMADAS[b]}})},
        "auth": {**base, "SERVICE_CALLERS": callers("auth")},
        "inventory": {**base, "SERVICE_CALLERS": callers("inventory")},
        "clients": {**base, "SERVICE_CALLERS": callers("clients")},
        "orders": {**base, **urls, "SERVICE_CALLERS": callers("orders"),
                   "ORDERS_INVENTORY_TOKEN": cred[("orders", "inventory")]},
        "payments": {**base, **urls, "SERVICE_CALLERS": callers("payments"),
                     "PAYMENTS_ORDERS_TOKEN": cred[("payments", "orders")],
                     "PASARELA_URL": url("pasarela"), "PASARELA_API_KEY": s["pasarela_key"],
                     "PASARELA_WEBHOOK_SECRET": s["pasarela_webhook"], "PUBLIC_URL": url("gateway")},
        "graphql": {**base, **urls, "SERVICE_CALLERS": callers("graphql"),
                    **{f"GRAPHQL_{b.upper()}_TOKEN": cred[("graphql", b)] for b in ("orders", "inventory", "payments", "clients")}},
        "pasarela": {**base, "PASARELA_API_KEY": s["pasarela_key"], "PASARELA_WEBHOOK_SECRET": s["pasarela_webhook"],
                     "PASARELA_PUBLIC_URL": url("pasarela")},
        "gateway": {**base, **urls, "VAULT_ADDR": url("vault"), "VAULT_TOKEN": s["vault_token"],
                    "FRONTEND_URL": url("sitio")},
    }


def comando(nombre: str) -> tuple[list[str], Path]:
    if nombre == "vault":
        return [sys.executable, "vault_local.py"], RAIZ / "vault-local"
    if nombre == "sitio":
        return ["php", "-S", f"127.0.0.1:{PUERTOS['sitio']}", "-t", str(RAIZ / "chocomania-frontend")], RAIZ
    return ([sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(PUERTOS[nombre]),
             "--no-access-log"], SERV / CARPETA[nombre])


def listo(nombre: str, espera: float = 20) -> bool:
    ruta = "/v1/sys/health" if nombre == "vault" else ("/" if nombre == "sitio" else "/health")
    fin = time.time() + espera
    while time.time() < fin:
        try:
            with urllib.request.urlopen(url(nombre) + ruta, timeout=1) as r:
                if r.status < 500:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def arrancar(env: dict, orden: list[str], carpeta_logs: Path = LOGS, mostrar=print) -> dict:
    """Inicia los procesos en orden y espera que cada uno responda."""
    carpeta_logs.mkdir(exist_ok=True)
    procesos = {}
    for nombre in orden:
        cmd, cwd = comando(nombre)
        log = open(carpeta_logs / f"{nombre}.log", "w", encoding="utf-8")
        procesos[nombre] = subprocess.Popen(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                            env={**os.environ, **env.get(nombre, {})})
        ok = listo(nombre)
        mostrar(f"  {'OK ' if ok else 'ERR'} {nombre:<10} {url(nombre)}")
        if not ok:
            detener(procesos)
            raise RuntimeError(f"{nombre} no arranco. Revisa {carpeta_logs / (nombre + '.log')}")
    return procesos


def detener(procesos: dict):
    for pr in procesos.values():
        pr.terminate()
    for pr in procesos.values():
        try:
            pr.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pr.kill()


def main():
    p = argparse.ArgumentParser(description="Inicia ChocoMania (Evaluacion 2) sin Docker")
    p.add_argument("--reiniciar-datos", action="store_true", help="borra las bases SQLite")
    p.add_argument("--sin-php", action="store_true", help="no levanta el servidor PHP")
    args = p.parse_args()

    if args.reiniciar_datos:
        for carpeta in CARPETA.values():
            shutil.rmtree(SERV / carpeta / "data", ignore_errors=True)
        print("Bases borradas: se recrean con los datos de prueba.")

    orden = list(ORDEN)
    if not args.sin_php:
        if shutil.which("php"):
            orden.insert(0, "sitio")
        else:
            print("AVISO: no se encontro 'php'. Levanta el sitio aparte en el puerto 8080 (o XAMPP).")

    env = entornos(generar())
    procesos = {}
    try:
        try:
            procesos = arrancar(env, orden)
        except RuntimeError as e:
            print(e)
            raise SystemExit(1)
        print("\nChocoMania listo en  http://127.0.0.1:8000   (Ctrl+C para detener)")
        print("Usuarios: ana / 1234 (cliente)   ernesto / admin123 (admin)")
        print("Logs de cada servicio en la carpeta logs/\n")
        while True:
            time.sleep(1)
            caidos = [n for n, pr in procesos.items() if pr.poll() is not None]
            if caidos:
                print(f"Se detuvo: {', '.join(caidos)}. Revisa logs/.")
                break
    except KeyboardInterrupt:
        print("\nDeteniendo...")
    finally:
        detener(procesos)
        print("Todo detenido.")


if __name__ == "__main__":
    main()
