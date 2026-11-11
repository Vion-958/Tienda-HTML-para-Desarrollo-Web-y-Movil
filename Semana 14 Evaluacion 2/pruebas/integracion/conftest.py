"""Levanta el sistema completo con bases temporales. Requiere los puertos libres."""

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


def _puerto_ocupado(p):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", p)) == 0


@pytest.fixture(scope="session")
def stack(tmp_path_factory):
    if any(_puerto_ocupado(p) for p in iniciar.PUERTOS.values()):
        pytest.skip("Hay puertos ocupados: deten iniciar.py antes de las pruebas de integracion")
    datos = tmp_path_factory.mktemp("datos")
    secretos = iniciar.generar()
    env = iniciar.entornos(secretos)
    for nombre, var in [("auth", "AUTH_DB"), ("inventory", "INVENTORY_DB"), ("orders", "ORDERS_DB"),
                        ("clients", "CLIENTS_DB"), ("payments", "PAYMENTS_DB")]:
        env[nombre][var] = str(datos / f"{nombre}.db")
    orden = list(iniciar.ORDEN)
    if shutil.which("php"):
        orden.insert(0, "sitio")
    procesos = iniciar.arrancar(env, orden, carpeta_logs=datos / "logs", mostrar=lambda *_: None)
    yield {"secretos": secretos, "procesos": procesos, "logs": datos / "logs"}
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
