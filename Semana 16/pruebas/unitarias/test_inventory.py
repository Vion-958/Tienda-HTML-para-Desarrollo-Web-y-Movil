"""inventory: catalogo, administracion, reservas de stock."""

import struct
import zlib

import pytest
from utiles import ANA, ERNESTO, cab, callers, cargar_servicio
from fastapi.testclient import TestClient


def png() -> bytes:
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff")) + chunk(b"IEND", b""))


@pytest.fixture
def cli(tmp_path, monkeypatch):
    m = cargar_servicio("inventory", monkeypatch, {
        "INVENTORY_DB": str(tmp_path / "inv.db"), "SERVICE_CALLERS": callers("gateway", "orders", "graphql")})
    return TestClient(m.app)


ADMIN = cab("gateway", ERNESTO, "user,admin")
FORM = {"nombre": "Mousse de chocolate", "precio": "8900", "categoria": "Postres",
        "descripcion": "Mousse aireado de chocolate blanco.", "tags": "Frutal, frutal", "stock": "5",
        "alergenos": ["L\u00e1cteos", "lacteos"]}


def test_sin_credencial_de_servicio_403(cli):
    assert cli.get("/products").status_code == 403
    assert cli.get("/products", headers={"X-Service-Name": "gateway", "X-Service-Token": "falso"}).status_code == 403


def test_catalogo_paginado_y_filtrado(cli):
    r = cli.get("/products?tamano=5&tag=individual", headers=cab()).json()
    assert r["tamano"] == 5 and all("individual" in p["tags"] for p in r["products"])
    assert set(r["products"][0]) >= {"id", "nombre", "precio", "stock", "disponible", "imagen"}


def test_crear_editar_y_baja_logica(cli):
    r = cli.post("/products", data=FORM, files=[("imagenes", ("a.png", png(), "image/png"))], headers=ADMIN)
    assert r.status_code == 201
    p = r.json()["product"]
    assert p["tags"] == ["frutal"] and p["imagen"].startswith("/api/images/")
    assert p["alergenos"] == ["l\u00e1cteos"]
    assert cli.get(p["imagen"].removeprefix("/api"), headers=cab()).headers["content-type"] == "image/png"

    r = cli.put(f"/products/{p['id']}", data=dict(FORM, precio="9900"), headers=ADMIN)
    assert r.status_code == 200 and r.json()["product"]["precio"] == 9900
    assert r.json()["product"]["imagenes"] == p["imagenes"]  # sin imagenes nuevas se conservan

    assert cli.delete(f"/products/{p['id']}", headers=ADMIN).status_code == 200
    assert cli.get(f"/products/{p['id']}", headers=cab()).status_code == 404
    # La baja es logica: el historial lo sigue encontrando.
    lote = cli.get(f"/internal/products?ids={p['id']}", headers=cab("graphql", ANA)).json()["products"]
    assert lote[0]["activo"] is False


def test_usuario_sin_rol_admin_no_crea(cli):
    r = cli.post("/products", data=FORM, files=[("imagenes", ("a.png", png(), "image/png"))], headers=cab("gateway", ANA))
    assert r.status_code == 403


@pytest.mark.parametrize("cambio, campo", [({"precio": "50"}, "precio"), ({"nombre": "x"}, "nombre"),
                                           ({"stock": "-1"}, "stock"), ({"alergenos": ["mani"]}, "alergenos")])
def test_validaciones(cli, cambio, campo):
    r = cli.post("/products", data=dict(FORM, **cambio), files=[("imagenes", ("a.png", png(), "image/png"))], headers=ADMIN)
    assert r.status_code == 400 and campo in r.json()["detail"]["errores"]


def test_archivo_que_no_es_imagen(cli):
    r = cli.post("/products", data=FORM, files=[("imagenes", ("x.png", b"MZ no soy imagen", "image/png"))], headers=ADMIN)
    assert r.status_code == 400 and "imagenes" in r.json()["detail"]["errores"]


def test_reserva_descuenta_es_idempotente_y_se_libera(cli):
    stock = lambda: cli.get("/products/choco-4", headers=cab()).json()["product"]["stock"]  # noqa: E731
    antes = stock()
    cuerpo = {"pedido_id": 5000, "items": [{"producto_id": "choco-4", "cantidad": 3}]}
    r1 = cli.post("/internal/reservations", json=cuerpo, headers=cab("orders"))
    r2 = cli.post("/internal/reservations", json=cuerpo, headers=cab("orders"))
    assert r1.status_code == 200 and r2.json()["repetida"] is True
    assert r1.json()["items"][0]["precio_unitario"] == 6500  # precio oficial
    assert stock() == antes - 3
    cli.post("/internal/reservations/5000/release", headers=cab("orders"))
    cli.post("/internal/reservations/5000/release", headers=cab("orders"))
    assert stock() == antes


def test_sin_stock_409_y_no_descuenta(cli):
    r = cli.post("/internal/reservations", json={"pedido_id": 5001, "items": [{"producto_id": "choco-4", "cantidad": 50}]},
                 headers=cab("orders"))
    assert r.status_code == 409


def test_solo_orders_reserva(cli):
    r = cli.post("/internal/reservations", json={"pedido_id": 1, "items": [{"producto_id": "choco-4", "cantidad": 1}]},
                 headers=cab("gateway", ERNESTO, "admin"))
    assert r.status_code == 403
