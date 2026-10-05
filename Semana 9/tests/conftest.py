"""
Configuración de las pruebas unitarias.

Cada servicio se importa directamente y se prueba con el TestClient de
FastAPI, sin levantar servidores ni Vault. Los secretos de prueba se
definen aquí antes de importar los módulos (cada servicio exige el suyo
al arrancar).
"""

import copy
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

os.environ.setdefault("AUTH_INTROSPECTION_SECRET", "test-auth-secret")
os.environ.setdefault("INTERNAL_GATEWAY_SECRET", "test-backend-secret")
os.environ.setdefault("VAULT_TOKEN", "test-vault-token")

for carpeta in ("auth-service", "backend-api", "api-gateway"):
    sys.path.insert(0, str(ROOT / carpeta))

import auth_service  # noqa: E402
import backend_api  # noqa: E402
import gateway  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

AUTH_SECRET = os.environ["AUTH_INTROSPECTION_SECRET"]
BACKEND_SECRET = os.environ["INTERNAL_GATEWAY_SECRET"]


@pytest.fixture
def auth_client():
    auth_service.SESSIONS.clear()
    yield TestClient(auth_service.app)
    auth_service.SESSIONS.clear()


@pytest.fixture
def backend_client():
    productos = copy.deepcopy(backend_api.PRODUCTS)
    pedidos = copy.deepcopy(backend_api.ORDERS)
    yield TestClient(backend_api.app)
    backend_api.PRODUCTS[:] = productos
    backend_api.ORDERS[:] = pedidos


@pytest.fixture
def gateway_client():
    return TestClient(gateway.app)


def identity_headers(user_id, username, roles, secret=BACKEND_SECRET):
    """Headers que el Gateway agrega al llamar al Backend."""
    return {
        "X-Gateway-Secret": secret,
        "X-Authenticated-User": user_id,
        "X-Authenticated-Username": username,
        "X-Authenticated-Roles": roles,
    }


ANA = identity_headers("USR-001", "ana", "user")
ERNESTO = identity_headers("USR-003", "ernesto", "user,admin")
