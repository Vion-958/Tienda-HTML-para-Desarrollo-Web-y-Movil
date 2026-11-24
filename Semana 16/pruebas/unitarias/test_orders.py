"""orders: creacion con precios del servidor, propiedad, transiciones y fallos de inventory."""

import httpx
import pytest
from utiles import ANA, ERNESTO, cab, callers, cargar_servicio
from fastapi.testclient import TestClient

PRECIOS = {"choco-4": ("Caja de cupcakes surtidos", 6500), "choco-8": ("Barra chocolate amargo 85%", 4800)}


class InventoryFalso:
    def __init__(self):
        self.modo = "ok"
        self.liberados = []
        self.intentos = []

    def __call__(self, metodo, ruta, rid, **kw):
        req = httpx.Request(metodo, "http://inventory" + ruta)
        self.intentos.append(ruta)
        if self.modo == "caido":
            raise httpx.ConnectError("inventory caido", request=req)
        if ruta.endswith("/release"):
            self.liberados.append(int(ruta.split("/")[3]))
            return httpx.Response(200, json={}, request=req)
        if ruta.endswith("/confirm"):
            return httpx.Response(200, json={}, request=req)
        if self.modo == "sin_stock":
            return httpx.Response(409, json={"detail": {"mensaje": "Sin stock suficiente"}}, request=req)
        items = [{"producto_id": i["producto_id"], "nombre": PRECIOS[i["producto_id"]][0],
                  "precio_unitario": PRECIOS[i["producto_id"]][1], "cantidad": i["cantidad"]} for i in kw["json"]["items"]]
        return httpx.Response(200, json={"items": items}, request=req)


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    m = cargar_servicio("orders", monkeypatch, {
        "ORDERS_DB": str(tmp_path / "o.db"), "SERVICE_CALLERS": callers("gateway", "payments", "graphql"),
        "ORDERS_INVENTORY_TOKEN": "x" * 20})
    falso = InventoryFalso()
    monkeypatch.setattr(m, "_inventory", falso)
    return TestClient(m.app), falso


PEDIDO = {"items": [{"producto_id": "choco-4", "cantidad": 2}], "entrega": "retiro", "metodo_pago": "tarjeta"}


def test_total_lo_calcula_el_servidor(ctx):
    cli, _ = ctx
    # Un total o precio enviado por el navegador se ignora.
    r = cli.post("/orders", json=dict(PEDIDO, total=1, precio_unitario=1), headers=cab("gateway", ANA))
    assert r.status_code == 201
    o = r.json()["order"]
    assert (o["subtotal"], o["costo_envio"], o["total"], o["estado"]) == (13000, 0, 13000, "pendiente_pago")


def test_envio_delivery(ctx):
    cli, _ = ctx
    r = cli.post("/orders", json=dict(PEDIDO, entrega="delivery", direccion="Av Uno 123", comuna="Nunoa"),
                 headers=cab("gateway", ANA))
    assert r.json()["order"]["costo_envio"] == 3000
    sin_dir = cli.post("/orders", json=dict(PEDIDO, entrega="delivery"), headers=cab("gateway", ANA))
    assert sin_dir.status_code == 422


def test_inventory_caido_compensa_y_503(ctx):
    cli, falso = ctx
    falso.modo = "caido"
    r = cli.post("/orders", json=PEDIDO, headers=cab("gateway", ANA))
    # Se intenta liberar por si alcanzo a reservar antes de cortarse.
    assert r.status_code == 503 and any(i.endswith("/release") for i in falso.intentos)
    assert cli.get("/orders", headers=cab("gateway", ANA)).json()["total"] == 2  # el fallido no se ve


def test_sin_stock_409(ctx):
    cli, falso = ctx
    falso.modo = "sin_stock"
    assert cli.post("/orders", json=PEDIDO, headers=cab("gateway", ANA)).status_code == 409


def test_pedido_ajeno_404(ctx):
    cli, _ = ctx
    assert cli.get("/orders/1002", headers=cab("gateway", ANA)).status_code == 404
    assert cli.get("/orders/1002", headers=cab("gateway", ERNESTO, "user,admin")).status_code == 200


def test_cancelar_propio_conserva_historial_y_libera(ctx):
    cli, falso = ctx
    r = cli.post("/orders/1003/cancel", headers=cab("gateway", ANA))
    assert r.status_code == 200 and r.json()["order"]["estado"] == "cancelado"
    assert [e["estado_nuevo"] for e in r.json()["order"]["eventos"]] == ["pendiente_pago", "cancelado"]
    assert 1003 in falso.liberados
    assert cli.post("/orders/1003/cancel", headers=cab("gateway", ANA)).status_code == 409


def test_cliente_no_cancela_pagado(ctx):
    cli, _ = ctx
    assert cli.post("/orders/1001/cancel", headers=cab("gateway", ANA)).status_code == 409


def test_transiciones_admin(ctx):
    cli, _ = ctx
    adm = cab("gateway", ERNESTO, "user,admin")
    assert cli.patch("/admin/orders/1001/estado", json={"estado": "despachado"}, headers=adm).status_code == 409
    assert cli.patch("/admin/orders/1001/estado", json={"estado": "en_preparacion"}, headers=adm).status_code == 200
    assert cli.patch("/admin/orders/1001/estado", json={"estado": "despachado"}, headers=adm).status_code == 409  # es retiro
    assert cli.patch("/admin/orders/1001/estado", json={"estado": "listo_retiro"}, headers=adm).status_code == 200
    # Nadie fija 'pagado' por esta via.
    assert cli.patch("/admin/orders/1003/estado", json={"estado": "pagado"}, headers=adm).status_code == 409
    assert cli.patch("/admin/orders/1003/estado", json={"estado": "cancelado"},
                     headers=cab("gateway", ANA)).status_code == 403


def test_solo_payments_marca_pagado_e_idempotente(ctx):
    cli, _ = ctx
    assert cli.post("/internal/orders/1003/paid", json={"pago_id": "PAY-X"}, headers=cab("gateway", ERNESTO, "admin")).status_code == 403
    assert cli.post("/internal/orders/1003/paid", json={"pago_id": "PAY-X"}, headers=cab("payments")).json()["repetido"] is False
    assert cli.post("/internal/orders/1003/paid", json={"pago_id": "PAY-X"}, headers=cab("payments")).json()["repetido"] is True
    assert cli.post("/internal/orders/1003/paid", json={"pago_id": "PAY-OTRO"}, headers=cab("payments")).status_code == 409


def test_identidad_falsa_desde_llamador_no_confiable(ctx):
    cli, _ = ctx
    # payments no puede propagar usuarios.
    h = cab("payments")
    h.update({"X-User-Id": ERNESTO, "X-User-Roles": "admin"})
    assert cli.get("/orders", headers=h).status_code == 403
