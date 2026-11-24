"""API Gateway: tabla de rutas, politicas y limitador."""

import pytest
from utiles import cargar_servicio


@pytest.fixture
def gw(monkeypatch):
    return cargar_servicio("api-gateway", monkeypatch, {"VAULT_TOKEN": "t" * 20})


@pytest.mark.parametrize("metodo, ruta, acceso, servicio", [
    ("GET", "products", "anonimo", "inventory"),
    ("POST", "products", "admin", "inventory"),
    ("PUT", "products/choco-1", "admin", "inventory"),
    ("DELETE", "products/choco-1", "admin", "inventory"),
    ("POST", "orders", "sesion", "orders"),
    ("POST", "orders/1003/cancel", "sesion", "orders"),
    ("PATCH", "admin/orders/1003/estado", "admin", "orders"),
    ("GET", "clients/me", "sesion", "clients"),
    ("POST", "payments/webhook", "anonimo", "payments"),
    ("POST", "admin/payments/PAY-1/confirmar", "admin", "payments"),
    ("POST", "graphql", "sesion", "graphql"),
    ("POST", "solicitudes", "opcional", "clients"),
    ("GET", "admin/solicitudes", "admin", "clients"),
])
def test_politica_de_cada_ruta(gw, metodo, ruta, acceso, servicio):
    r, _ = gw._buscar_ruta(metodo, ruta)
    assert (r.acceso, r.servicio) == (acceso, servicio)


@pytest.mark.parametrize("metodo, ruta", [
    ("GET", "internal/products"), ("POST", "internal/reservations"), ("POST", "internal/orders/1/paid"),
    ("GET", "admin/orders/../internal"), ("GET", "orders/abc"), ("DELETE", "orders/1003"), ("GET", "graphql"),
])
def test_rutas_internas_o_no_publicadas_no_existen(gw, metodo, ruta):
    assert gw._buscar_ruta(metodo, ruta) == (None, None)


def test_ids_de_ruta_unicos(gw):
    ids = [r.id for r in gw.RUTAS]
    assert len(ids) == len(set(ids))


def test_limitador(gw):
    lim = gw.Limitador()
    assert all(lim.permitir("1.1.1.1", "login", 3) for _ in range(3))
    assert not lim.permitir("1.1.1.1", "login", 3)
    assert lim.permitir("2.2.2.2", "login", 3)
