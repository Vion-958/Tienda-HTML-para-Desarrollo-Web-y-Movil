"""Semana 13: el cliente cancela pedidos y el admin agrega productos con imágenes."""

import struct
import zlib

import backend_api
import gateway
import pytest
from conftest import ANA, ERNESTO


def png_minimo() -> bytes:
    """Un PNG real de 1x1 píxel, armado a mano."""
    def chunk(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
        + chunk(b"IEND", b"")
    )


CAMPOS = {
    "nombre": "Mousse de chocolate blanco",
    "precio": "8900",
    "categoria": "Postres",
    "descripcion": "Mousse aireado de chocolate blanco con frambuesas.",
    "tags": "Para Compartir, frutal, frutal",
    "stock": "12",
    "ingredientes": "Chocolate blanco, crema, frambuesas",
}


def crear(cliente, headers=ERNESTO, campos=None, imagenes=None):
    datos = dict(CAMPOS, **(campos or {}))
    archivos = imagenes if imagenes is not None else [("imagenes", ("mousse.png", png_minimo(), "image/png"))]
    datos["alergenos"] = ["lácteos"]
    return cliente.post("/products", headers=headers, data=datos, files=archivos)


@pytest.fixture(autouse=True)
def limpiar_imagenes():
    backend_api.IMAGES.clear()
    yield
    backend_api.IMAGES.clear()


# ---------------------------------------------------------------- productos

def test_admin_crea_producto_con_imagen(backend_client):
    r = crear(backend_client)
    assert r.status_code == 201
    p = r.json()["product"]
    assert p["id"].startswith("choco-")
    assert p["tags"] == ["para compartir", "frutal"]  # minúsculas y sin repetidos
    assert p["stock"] == 12
    assert p["alergenos"] == ["lácteos"]
    assert p["imagen"] == p["imagenes"][0]
    assert p["creado_por"] == "ernesto"

    # Aparece en el catálogo y su imagen se puede descargar.
    ids = [x["id"] for x in backend_client.get("/products", headers=ANA).json()["products"]]
    assert p["id"] in ids
    imagen = backend_client.get(p["imagen"].removeprefix("/api"), headers=ANA)
    assert imagen.status_code == 200
    assert imagen.headers["content-type"] == "image/png"


def test_admin_sube_varias_imagenes(backend_client):
    archivos = [("imagenes", (f"foto{i}.png", png_minimo(), "image/png")) for i in range(3)]
    r = crear(backend_client, imagenes=archivos)
    assert r.status_code == 201
    assert len(r.json()["product"]["imagenes"]) == 3


def test_usuario_no_puede_crear_producto(backend_client):
    assert crear(backend_client, headers=ANA).status_code == 403


@pytest.mark.parametrize(
    "campos, campo_con_error",
    [
        ({"nombre": "ab"}, "nombre"),
        ({"nombre": "Torta red velvet"}, "nombre"),  # ya existe
        ({"precio": "50"}, "precio"),
        ({"precio": "doce mil"}, "precio"),
        ({"categoria": ""}, "categoria"),
        ({"descripcion": "corta"}, "descripcion"),
        ({"stock": "-1"}, "stock"),
        ({"tags": ",".join(f"tag{i}" for i in range(9))}, "tags"),
    ],
)
def test_validaciones_del_formulario(backend_client, campos, campo_con_error):
    r = crear(backend_client, campos=campos)
    assert r.status_code == 400
    assert campo_con_error in r.json()["detail"]["errores"]


def test_sin_imagenes_400(backend_client):
    r = crear(backend_client, imagenes=[])
    assert r.status_code == 400
    assert "imagenes" in r.json()["detail"]["errores"]


def test_mas_de_cinco_imagenes_400(backend_client):
    archivos = [("imagenes", (f"f{i}.png", png_minimo(), "image/png")) for i in range(6)]
    assert crear(backend_client, imagenes=archivos).status_code == 400


def test_archivo_que_no_es_imagen_400(backend_client):
    """El nombre y el content-type dicen PNG, pero el contenido no lo es."""
    falso = [("imagenes", ("virus.png", b"MZ\x90\x00 no soy una imagen", "image/png"))]
    r = crear(backend_client, imagenes=falso)
    assert r.status_code == 400
    assert "JPG, PNG o WEBP" in r.json()["detail"]["errores"]["imagenes"]


def test_imagen_de_mas_de_2mb_400(backend_client):
    grande = png_minimo() + b"\x00" * (2 * 1024 * 1024)
    r = crear(backend_client, imagenes=[("imagenes", ("grande.png", grande, "image/png"))])
    assert r.status_code == 400
    assert "2 MB" in r.json()["detail"]["errores"]["imagenes"]


def test_eliminar_producto_borra_sus_imagenes(backend_client):
    p = crear(backend_client).json()["product"]
    assert len(backend_api.IMAGES) == 1
    backend_client.delete(f"/products/{p['id']}", headers=ERNESTO)
    assert backend_api.IMAGES == {}


def test_productos_iniciales_traen_tags_y_stock(backend_client):
    productos = backend_client.get("/products", headers=ANA).json()["products"]
    assert all(isinstance(p["tags"], list) and p["stock"] == 20 for p in productos)


# ---------------------------------------------------------------- pedidos

def test_cliente_cancela_su_pedido_pendiente(backend_client):
    stock_antes = next(p["stock"] for p in backend_api.PRODUCTS if p["id"] == "choco-7")
    r = backend_client.post("/orders/1003/cancel", headers=ANA)
    assert r.status_code == 200
    assert r.json()["order"]["status"] == "cancelled"
    # El stock reservado (2 alfajores) vuelve al catálogo.
    stock_despues = next(p["stock"] for p in backend_api.PRODUCTS if p["id"] == "choco-7")
    assert stock_despues == stock_antes + 2


def test_no_se_cancela_dos_veces(backend_client):
    backend_client.post("/orders/1003/cancel", headers=ANA)
    assert backend_client.post("/orders/1003/cancel", headers=ANA).status_code == 409


def test_pedido_pagado_no_se_cancela(backend_client):
    r = backend_client.post("/orders/1001/cancel", headers=ANA)
    assert r.status_code == 409
    assert "pagado" in r.json()["detail"]


def test_pedido_ajeno_responde_404(backend_client):
    """Ana no puede cancelar el pedido de Ernesto, ni saber que existe."""
    assert backend_client.post("/orders/1002/cancel", headers=ANA).status_code == 404


def test_pedido_inexistente_404(backend_client):
    assert backend_client.post("/orders/9999/cancel", headers=ANA).status_code == 404


def test_pedido_nuevo_descuenta_stock_y_falla_sin_stock(backend_client):
    r = backend_client.post("/orders", headers=ANA, json={"items": [{"producto_id": "choco-5", "cantidad": 20}]})
    assert r.status_code == 201
    r = backend_client.post("/orders", headers=ANA, json={"items": [{"producto_id": "choco-5", "cantidad": 1}]})
    assert r.status_code == 409


# ---------------------------------------------------------------- gateway

def test_politica_crear_producto_requiere_admin():
    assert gateway.required_role("POST", "products") == "admin"
    assert gateway.required_role("POST", "orders") is None
    assert gateway.required_role("POST", "orders/1003/cancel") is None
    assert gateway.required_role("GET", "images/abc") is None
