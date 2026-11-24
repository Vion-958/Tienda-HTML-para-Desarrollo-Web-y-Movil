"""payments: monto del servidor, firma del aviso, idempotencia y transferencias."""

import hashlib
import hmac
import json
import time

import httpx
import pytest
from utiles import ANA, ERNESTO, cab, callers, cargar_servicio
from fastapi.testclient import TestClient

SECRETO = "whsec_de_prueba_1234567890"


class Falsos:
    def __init__(self):
        self.pedidos = {1003: {"id": 1003, "user_id": ANA, "estado": "pendiente_pago", "total": 10400,
                               "metodo_pago": "tarjeta", "pago_id": None}}
        self.pagados = []
        self.orders_caido = False

    def orders(self, metodo, ruta, rid, **kw):
        req = httpx.Request(metodo, "http://orders" + ruta)
        if self.orders_caido:
            raise httpx.ConnectError("caido", request=req)
        pid = int(ruta.split("/")[3])
        if ruta.endswith("/paid"):
            self.pagados.append(pid)
            return httpx.Response(200, json={}, request=req)
        p = self.pedidos.get(pid)
        return httpx.Response(200, json=p, request=req) if p else httpx.Response(404, json={}, request=req)


class Pasarela:
    def post(self, url, headers, json):
        assert headers["Authorization"].startswith("Bearer ")
        assert json["monto"] == 10400
        return httpx.Response(201, json={"checkout_id": "chk_1", "url": "http://pasarela/checkout/chk_1"},
                              request=httpx.Request("POST", url))

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    m = cargar_servicio("payments", monkeypatch, {
        "PAYMENTS_DB": str(tmp_path / "p.db"), "SERVICE_CALLERS": callers("gateway", "graphql"),
        "PAYMENTS_ORDERS_TOKEN": "x" * 20, "PASARELA_API_KEY": "sk_test_" + "k" * 20,
        "PASARELA_WEBHOOK_SECRET": SECRETO})
    f = Falsos()
    monkeypatch.setattr(m, "_orders", f.orders)
    monkeypatch.setattr(m.httpx, "Client", lambda **kw: Pasarela())
    return TestClient(m.app), f, m


def aviso(estado="aprobado", monto=10400, evento="evt_1", t=None, secreto=SECRETO):
    cuerpo = json.dumps({"evento_id": evento, "checkout_id": "chk_1", "referencia": REF[0],
                         "estado": estado, "monto": monto}).encode()
    t = t or int(time.time())
    firma = hmac.new(secreto.encode(), f"{t}.".encode() + cuerpo, hashlib.sha256).hexdigest()
    return cuerpo, {**cab("gateway"), "X-Pasarela-Firma": f"t={t},v1={firma}", "content-type": "application/json"}


REF = [""]


def iniciar(cli):
    r = cli.post("/payments", json={"pedido_id": 1003}, headers=cab("gateway", ANA))
    REF[0] = r.json()["payment"]["id"]
    return r


def test_inicio_usa_monto_del_pedido_y_es_idempotente(ctx):
    cli, _, _ = ctx
    r = iniciar(cli)
    assert r.status_code == 201 and r.json()["payment"]["monto"] == 10400 and r.json()["redirect_url"]
    again = cli.post("/payments", json={"pedido_id": 1003}, headers=cab("gateway", ANA))
    assert again.json()["payment"]["id"] == REF[0]


def test_pedido_ajeno_404(ctx):
    cli, _, _ = ctx
    assert cli.post("/payments", json={"pedido_id": 1003}, headers=cab("gateway", ERNESTO, "user,admin")).status_code == 404


def test_aviso_valido_marca_pagado_una_sola_vez(ctx):
    cli, f, _ = ctx
    iniciar(cli)
    cuerpo, h = aviso()
    assert cli.post("/payments/webhook", content=cuerpo, headers=h).json()["duplicado"] is False
    assert cli.post("/payments/webhook", content=cuerpo, headers=h).json()["duplicado"] is True
    assert f.pagados == [1003]


@pytest.mark.parametrize("caso", ["firma", "vencido", "monto"])
def test_avisos_alterados_se_rechazan(ctx, caso):
    cli, f, _ = ctx
    iniciar(cli)
    if caso == "firma":
        cuerpo, h = aviso(secreto="otro-secreto-cualquiera")
    elif caso == "vencido":
        cuerpo, h = aviso(t=int(time.time()) - 3600)
    else:
        cuerpo, h = aviso(monto=1)
    r = cli.post("/payments/webhook", content=cuerpo, headers=h)
    assert r.status_code in (400, 401) and f.pagados == []


def test_si_orders_cae_el_proveedor_reintenta_sin_duplicar(ctx):
    cli, f, _ = ctx
    iniciar(cli)
    cuerpo, h = aviso()
    f.orders_caido = True
    assert cli.post("/payments/webhook", content=cuerpo, headers=h).status_code == 503
    f.orders_caido = False
    r = cli.post("/payments/webhook", content=cuerpo, headers=h)
    assert r.status_code == 200 and r.json()["duplicado"] is True and f.pagados == [1003]


def test_transferencia_la_confirma_solo_admin(ctx):
    cli, f, _ = ctx
    f.pedidos[1003]["metodo_pago"] = "transferencia"
    r = cli.post("/payments", json={"pedido_id": 1003}, headers=cab("gateway", ANA))
    pid = r.json()["payment"]["id"]
    assert r.json()["instrucciones"]["monto"] == 10400
    assert cli.post(f"/admin/payments/{pid}/confirmar", headers=cab("gateway", ANA)).status_code == 403
    assert cli.post(f"/admin/payments/{pid}/confirmar", headers=cab("gateway", ERNESTO, "user,admin")).status_code == 200
    assert f.pagados == [1003]


def test_transferencia_de_pedido_cancelado_se_anula(ctx):
    cli, f, _ = ctx
    f.pedidos[1003]["metodo_pago"] = "transferencia"
    pid = cli.post("/payments", json={"pedido_id": 1003}, headers=cab("gateway", ANA)).json()["payment"]["id"]
    f.pedidos[1003]["estado"] = "cancelado"
    r = cli.post(f"/admin/payments/{pid}/confirmar", headers=cab("gateway", ERNESTO, "user,admin"))
    assert r.status_code == 409 and f.pagados == []
    assert cli.post(f"/admin/payments/{pid}/confirmar", headers=cab("gateway", ERNESTO, "user,admin")).status_code == 409
    lote = cli.get("/internal/payments?pedidos=1003", headers=cab("graphql", ANA)).json()["payments"]
    assert lote[0]["estado"] == "anulado"


def test_aviso_aprobado_de_pedido_cancelado_se_anula(ctx):
    cli, f, _ = ctx
    iniciar(cli)
    f.pedidos[1003]["estado"] = "cancelado"
    cuerpo, h = aviso()
    r = cli.post("/payments/webhook", content=cuerpo, headers=h)
    assert r.status_code == 200 and r.json()["estado"] == "anulado" and f.pagados == []


def test_base_antigua_se_migra(tmp_path, monkeypatch):
    import sqlite3
    ruta = tmp_path / "vieja.db"
    con = sqlite3.connect(ruta)
    con.executescript(
        "CREATE TABLE pagos (id TEXT PRIMARY KEY, pedido_id INTEGER NOT NULL, user_id TEXT NOT NULL,"
        " monto INTEGER NOT NULL CHECK (monto > 0), metodo TEXT NOT NULL CHECK (metodo IN ('tarjeta', 'transferencia')),"
        " estado TEXT NOT NULL CHECK (estado IN ('pendiente', 'aprobado', 'rechazado')), checkout_id TEXT,"
        " checkout_url TEXT, sincronizado INTEGER NOT NULL DEFAULT 0, creado TEXT NOT NULL DEFAULT (datetime('now')),"
        " actualizado TEXT NOT NULL DEFAULT (datetime('now')));"
        "INSERT INTO pagos (id, pedido_id, user_id, monto, metodo, estado) VALUES ('PAY-1', 1, 'u', 100, 'tarjeta', 'pendiente');")
    con.close()
    m = cargar_servicio("payments", monkeypatch, {
        "PAYMENTS_DB": str(ruta), "SERVICE_CALLERS": callers("gateway", "graphql"),
        "PAYMENTS_ORDERS_TOKEN": "x" * 20, "PASARELA_API_KEY": "sk_test_" + "k" * 20, "PASARELA_WEBHOOK_SECRET": SECRETO})
    m._anular("PAY-1")
    with m.db.conexion() as c:
        assert c.execute("SELECT estado FROM pagos WHERE id = 'PAY-1'").fetchone()[0] == "anulado"
