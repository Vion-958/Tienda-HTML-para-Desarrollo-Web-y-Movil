"""Levanta el sistema completo con bases temporales. Requiere los puertos libres.
Con CHOCOMANIA_POSTGRES=<url de administrador> las pruebas corren sobre PostgreSQL."""

import os
import shutil
import socket
import sys
from pathlib import Path

import httpx
import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import iniciar  # noqa: E402

G = "http://127.0.0.1:8000"
TTL_VAULT = 2
GRACIA_VAULT = 6


def _puerto_ocupado(p):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", p)) == 0


@pytest.fixture(scope="session")
def stack(tmp_path_factory):
    if any(_puerto_ocupado(p) for p in iniciar.PUERTOS.values()):
        pytest.skip("Hay puertos ocupados: deten iniciar.py antes de las pruebas de integracion")
    datos = tmp_path_factory.mktemp("datos")
    # Cache de Vault corta para probar la rotacion sin esperar 30 s.
    extra = {"*": {"VAULT_CACHE_TTL": str(TTL_VAULT), "VAULT_GRACIA": str(GRACIA_VAULT)}}
    for nombre, var in [("auth", "AUTH_DB"), ("inventory", "INVENTORY_DB"), ("orders", "ORDERS_DB"),
                        ("clients", "CLIENTS_DB"), ("payments", "PAYMENTS_DB")]:
        extra[nombre] = {var: str(datos / f"{nombre}.db")}
    orden = list(iniciar.ORDEN)
    if shutil.which("php"):
        orden.insert(0, "sitio")
    postgres = os.getenv("CHOCOMANIA_POSTGRES")
    procesos, info = iniciar.levantar(orden, carpeta_logs=datos / "logs", mostrar=lambda *_: None, extra=extra,
                                      postgres=postgres, reiniciar_bd=True)
    yield {**info, "procesos": procesos, "logs": datos / "logs"}
    iniciar.detener(procesos)


def sesion(usuario, clave) -> httpx.Client:
    c = httpx.Client(base_url=G, timeout=15)
    r = c.post("/auth/login", json={"username": usuario, "password": clave})
    assert r.status_code == 200, r.text
    return c


@pytest.fixture
def ana(stack):
    c = sesion("ana", "1234")
    yield c
    c.close()


@pytest.fixture
def ernesto(stack):
    c = sesion("ernesto", "admin123")
    yield c
    c.close()


@pytest.fixture
def anonimo(stack):
    with httpx.Client(base_url=G, timeout=15) as c:
        yield c
