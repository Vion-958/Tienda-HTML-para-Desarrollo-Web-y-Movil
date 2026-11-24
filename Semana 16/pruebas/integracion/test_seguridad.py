"""Casos de validacion del modulo 7 contra el sistema real."""

import hashlib
import hmac
import json
import time

import httpx
import pytest

SERVICIOS_INTERNOS = {"auth": 8100, "inventory": 9101, "orders": 9102, "clients": 9103, "payments": 9104, "graphql": 9200}


def test_V01_catalogo_anonimo(anonimo):
    """Anonimo -> GET catalogo -> 200 solo con campos publicos (Gateway + inventory)."""
    r = anonimo.get("/api/products")
    assert r.status_code == 200
    campos = set(r.json()["products"][0])
    assert campos.isdisjoint({"creado_por", "activo", "costo"})


def test_V02_operacion_protegida_sin_sesion(anonimo):
    """Sin cookie -> pedidos, perfil, pago, GraphQL -> 401 (Gateway)."""
    for metodo, ruta in [("GET", "/api/orders"), ("GET", "/api/clients/me"), ("POST", "/api/payments"),
                         ("POST", "/api/graphql")]:
        assert anonimo.request(metodo, ruta, json={}).status_code == 401


def test_V03_admin_desde_rol_sin_permiso(ana):
    """ana (user) -> crear/eliminar producto, pedidos de todos, confirmar pago -> 403 (Gateway)."""
    assert ana.delete("/api/products/choco-1").status_code == 403
    assert ana.post("/api/products", data={"nombre": "x"}).status_code == 403
    assert ana.get("/api/admin/orders").status_code == 403
    assert ana.post("/api/admin/payments/PAY-SEED-1002/confirmar").status_code == 403
    assert "Se requiere el rol admin" in ana.post("/api/graphql", json={"query": "{ pedidosAdmin { total } }"}).text


def test_V04_pedido_ajeno(ana):
    """ana -> pedido 1002 (de ernesto) -> 404 sin datos (orders verifica propiedad)."""
    r = ana.get("/api/orders/1002")
    assert r.status_code == 404 and "15600" not in r.text
    assert ana.post("/api/orders/1002/cancel").status_code == 404
    assert ana.post("/api/graphql", json={"query": "{ pedido(id: 1002) { total } }"}).json()["data"]["pedido"] is None
    assert ana.post("/api/payments", json={"pedido_id": 1002}).status_code == 404


@pytest.mark.parametrize("servicio, puerto", SERVICIOS_INTERNOS.items())
def test_V05_acceso_directo_a_servicios_internos(stack, servicio, puerto):
    """Llamada directa sin credencial de servicio -> 403 (cada servicio)."""
    ruta = {"auth": "/introspect", "graphql": "/graphql", "payments": "/payments", "orders": "/orders",
            "clients": "/clients/me", "inventory": "/products"}[servicio]
    metodo = "POST" if servicio in ("auth", "graphql", "payments") else "GET"
    falsas = {"X-Service-Name": "gateway", "X-Service-Token": "adivinado", "X-User-Id": "USR-003", "X-User-Roles": "admin"}
    r = httpx.request(metodo, f"http://127.0.0.1:{puerto}{ruta}", headers=falsas, json={})
    assert r.status_code == 403


def test_V06_cabeceras_de_identidad_del_navegador_se_descartan(ana):
    """ana envia X-User-Id/X-User-Roles de admin -> igual 403 (Gateway las reemplaza)."""
    h = {"X-User-Id": "USR-003", "X-User-Roles": "user,admin", "X-Service-Name": "gateway"}
    assert ana.get("/api/admin/orders", headers=h).status_code == 403
    assert ana.get("/api/orders/1002", headers=h).status_code == 404


def test_V07_pago_no_se_confirma_con_datos_del_frontend(ana, stack):
    """El navegador no puede: fijar el total, marcar pagado, ni falsificar el aviso del proveedor."""
    r = ana.post("/api/orders", json={"items": [{"producto_id": "choco-8", "cantidad": 1}], "entrega": "retiro",
                                       "metodo_pago": "tarjeta", "total": 1, "estado": "pagado"})
    pedido = r.json()["order"]
    assert pedido["total"] == 4800 and pedido["estado"] == "pendiente_pago"
    assert ana.patch(f"/api/admin/orders/{pedido['id']}/estado", json={"estado": "pagado"}).status_code == 403

    pago = ana.post("/api/payments", json={"pedido_id": pedido["id"]}).json()["payment"]
    cuerpo = json.dumps({"evento_id": "evt_falso", "checkout_id": "chk_x", "referencia": pago["id"],
                         "estado": "aprobado", "monto": pago["monto"]}).encode()
    firma_falsa = hmac.new(b"no-conozco-el-secreto", f"{int(time.time())}.".encode() + cuerpo, hashlib.sha256).hexdigest()
    r = ana.post("/api/payments/webhook", content=cuerpo,
                 headers={"X-Pasarela-Firma": f"t={int(time.time())},v1={firma_falsa}", "content-type": "application/json"})
    assert r.status_code == 401
    assert ana.get(f"/api/orders/{pedido['id']}").json()["order"]["estado"] == "pendiente_pago"


def test_V08_limite_de_intentos_de_login(stack):
    """11 fallos del mismo usuario en un minuto -> 429; los demas usuarios entran igual."""
    with httpx.Client(base_url="http://127.0.0.1:8000") as c:
        codigos = [c.post("/auth/login", json={"username": "intruso", "password": "mala"}).status_code for _ in range(11)]
        assert codigos[:10] == [401] * 10 and codigos[10] == 429
        assert c.post("/auth/login", json={"username": "ana", "password": "1234"}).status_code == 200


def test_V09_ruta_interna_no_publicada(ana):
    for metodo, ruta in [("GET", "/api/internal/products?ids=choco-1"), ("POST", "/api/internal/reservations"),
                         ("POST", "/api/internal/orders/1003/paid")]:
        assert ana.request(metodo, ruta, json={}).status_code == 404


def test_V10_cookie_httponly_y_sin_token_en_respuestas(stack):
    with httpx.Client(base_url="http://127.0.0.1:8000") as c:
        r = c.post("/auth/login", json={"username": "ana", "password": "1234"})
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert "access_token" not in r.text and c.cookies.get("session_token") not in r.text


def test_V11_logout_revoca_en_el_servidor(stack):
    c = httpx.Client(base_url="http://127.0.0.1:8000")
    c.post("/auth/login", json={"username": "ana", "password": "1234"})
    token = c.cookies.get("session_token")
    c.post("/auth/logout")
    robada = httpx.Client(base_url="http://127.0.0.1:8000", cookies={"session_token": token})
    assert robada.get("/auth/me").status_code == 401


def test_V12_logs_sin_secretos(stack, ana):
    ana.get("/api/orders")
    texto = "".join(p.read_text(encoding="utf-8") for p in stack["logs"].glob("*.log"))
    for valor in list(stack["secretos"]["cred"].values()) + [stack["secretos"]["pasarela_key"],
                                                           stack["secretos"]["pasarela_webhook"]]:
        assert valor not in texto
    assert ana.cookies.get("session_token") not in texto
    assert "rid=" in texto  # hay correlacion
