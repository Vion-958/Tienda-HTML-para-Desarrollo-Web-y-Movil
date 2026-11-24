import importlib.util
import json
import secrets
import socket
import sys
import threading
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SERV = RAIZ / "servicios"
sys.path.insert(0, str(SERV))
sys.path.insert(0, str(RAIZ))

# Credenciales de prueba (ficticias, solo para estas pruebas).
TOKENS = {n: f"token-de-prueba-{n}-0123456789" for n in ("gateway", "orders", "payments", "graphql")}


def callers(*nombres):
    return json.dumps({n: TOKENS[n] for n in nombres})


RUTA_VAULT = {"auth-service": "auth", "graphql-gateway": "graphql", "api-gateway": "gateway"}
# Variables de prueba que antes iban al entorno y ahora viven en Vault.
A_VAULT = {"ORDERS_INVENTORY_TOKEN": "token_inventory", "PAYMENTS_ORDERS_TOKEN": "token_orders",
           "PASARELA_API_KEY": "pasarela_api_key", "PASARELA_WEBHOOK_SECRET": "pasarela_webhook"}
_vault = {}


def vault_de_prueba():
    """Un vault-local en memoria para todas las pruebas unitarias."""
    if not _vault:
        sys.path.insert(0, str(RAIZ / "vault-local"))
        import vault_local
        with socket.socket() as so:
            so.bind(("127.0.0.1", 0))
            puerto = so.getsockname()[1]
        raiz = secrets.token_urlsafe(16)
        srv = vault_local.crear_servidor(raiz, puerto)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        import iniciar
        _vault.update(addr=f"http://127.0.0.1:{puerto}", raiz=raiz, cliente=iniciar.ClienteVault(f"http://127.0.0.1:{puerto}", raiz))
    return _vault


def cargar_servicio(carpeta: str, monkeypatch, env: dict, secretos: dict | None = None):
    """Importa servicios/<carpeta>/app.py con base temporal y sus secretos en un Vault de prueba."""
    datos = dict(secretos or {})
    for k, v in env.items():
        if k == "SERVICE_CALLERS":
            datos.update({f"llamador_{n}": t for n, t in json.loads(v).items()})
        elif k in A_VAULT and carpeta != "pasarela-sandbox":
            datos[A_VAULT[k]] = v
        elif k.startswith("GRAPHQL_") and k.endswith("_TOKEN"):
            datos[f"token_{k[8:-6].lower()}"] = v
        elif k != "VAULT_TOKEN":
            monkeypatch.setenv(k, v)
    if carpeta != "pasarela-sandbox":
        v = vault_de_prueba()
        v["cliente"].escribir(RUTA_VAULT.get(carpeta, carpeta), datos or {"vacio": "1"})
        monkeypatch.setenv("VAULT_ADDR", v["addr"])
        monkeypatch.setenv("VAULT_TOKEN", v["raiz"])
    spec = importlib.util.spec_from_file_location(f"app_{carpeta}_{uuid.uuid4().hex}", SERV / carpeta / "app.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def cab(caller="gateway", user=None, roles="user"):
    h = {"X-Service-Name": caller, "X-Service-Token": TOKENS[caller]}
    if user:
        h.update({"X-User-Id": user, "X-User-Name": user.lower(), "X-User-Roles": roles})
    return h


ANA = "USR-001"
ERNESTO = "USR-003"
