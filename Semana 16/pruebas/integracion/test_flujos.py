"""Flujos de negocio completos a traves del Gateway (sistema real)."""

import httpx


def comprar(cliente, producto="choco-4", cantidad=1, metodo="tarjeta"):
    r = cliente.post("/api/orders", json={"items": [{"producto_id": producto, "cantidad": cantidad}],
                                          "entrega": "retiro", "metodo_pago": metodo})
    assert r.status_code == 201, r.text
    return r.json()["order"]


def stock(cliente, pid):
    return cliente.get(f"/api/products/{pid}").json()["product"]["stock"]


def test_F01_compra_con_pasarela_y_aviso_duplicado(ana, stack):
    pedido = comprar(ana, "choco-6", 2)
    pago = ana.post("/api/payments", json={"pedido_id": pedido["id"]}).json()
    cid = pago["redirect_url"].rsplit("/", 1)[1]
    # El cliente aprueba en la pagina del proveedor.
    r = httpx.post(f"http://127.0.0.1:9300/checkout/{cid}/resultado", data={"resultado": "aprobado"})
    assert r.status_code == 303 and "pago=aprobado" in r.headers["location"]
    assert ana.get(f"/api/orders/{pedido['id']}").json()["order"]["estado"] == "pagado"
    # El proveedor reenvia el mismo aviso: no se procesa dos veces.
    key = stack["secretos"]["pasarela_key"]
    ultimo_evento = None
    r = httpx.post(f"http://127.0.0.1:9300/v1/checkouts/{cid}/reenviar", headers={"Authorization": f"Bearer {key}"},
                   params={"evento_id": ultimo_evento} if ultimo_evento else None)
    assert r.json()["status"] == 200
    eventos = ana.get(f"/api/orders/{pedido['id']}").json()["order"]["eventos"]
    assert [e["estado_nuevo"] for e in eventos].count("pagado") == 1


def test_F02_pago_rechazado_permite_reintentar(ana):
    pedido = comprar(ana)
    cid = ana.post("/api/payments", json={"pedido_id": pedido["id"]}).json()["redirect_url"].rsplit("/", 1)[1]
    httpx.post(f"http://127.0.0.1:9300/checkout/{cid}/resultado", data={"resultado": "rechazado"})
    assert ana.get(f"/api/orders/{pedido['id']}").json()["order"]["estado"] == "pendiente_pago"
    nuevo = ana.post("/api/payments", json={"pedido_id": pedido["id"]}).json()
    assert nuevo["redirect_url"].rsplit("/", 1)[1] != cid


def test_F03_cancelar_devuelve_stock(ana):
    antes = stock(ana, "choco-9")
    pedido = comprar(ana, "choco-9", 3)
    assert stock(ana, "choco-9") == antes - 3
    r = ana.post(f"/api/orders/{pedido['id']}/cancel")
    assert r.json()["stock_liberado"] is True
    assert stock(ana, "choco-9") == antes


def test_F04_sin_stock(ana):
    r = ana.post("/api/orders", json={"items": [{"producto_id": "choco-12", "cantidad": 50}], "entrega": "retiro",
                                      "metodo_pago": "tarjeta"})
    assert r.status_code == 409


def test_F05_transferencia_confirmada_por_admin_y_despacho(ana, ernesto):
    pedido = comprar(ana, metodo="transferencia")
    pago = ana.post("/api/payments", json={"pedido_id": pedido["id"]}).json()
    assert pago["instrucciones"]["monto"] == pedido["total"]
    assert ernesto.post(f"/api/admin/payments/{pago['payment']['id']}/confirmar").status_code == 200
    for estado in ("en_preparacion", "listo_retiro", "entregado"):
        assert ernesto.patch(f"/api/admin/orders/{pedido['id']}/estado", json={"estado": estado}).status_code == 200
    q = ana.post("/api/graphql", json={"query": f"{{ pedido(id: {pedido['id']}) {{ estado pago {{ estado }} eventos {{ estadoNuevo }} }} }}"})
    d = q.json()["data"]["pedido"]
    assert d["estado"] == "entregado" and d["pago"]["estado"] == "aprobado"
    assert [e["estadoNuevo"] for e in d["eventos"]] == ["pendiente_pago", "pagado", "en_preparacion", "listo_retiro", "entregado"]


def test_F06_registro_y_perfil(anonimo):
    import uuid
    u = "test" + uuid.uuid4().hex[:8]
    r = anonimo.post("/auth/register", json={"username": u, "password": "clave1234"})
    assert r.status_code == 201
    assert anonimo.get("/api/clients/me").status_code == 404
    r = anonimo.put("/api/clients/me", json={"nombre": "Prueba Uno", "email": f"{u}@example.com"})
    assert r.status_code == 200
    assert anonimo.get("/api/orders").json()["total"] == 0


def test_F07_agregacion_graphql_desde_el_gateway(ana):
    r = ana.post("/api/graphql", json={"query": "{ misPedidos { pedidos { id pago { estado } cliente { nombre } items { producto { nombre imagen } } } } }"})
    d = r.json()
    assert "errors" not in d
    p1001 = next(p for p in d["data"]["misPedidos"]["pedidos"] if p["id"] == 1001)
    assert p1001["pago"]["estado"] == "aprobado" and p1001["cliente"]["nombre"] == "Ana Perez"
    assert p1001["items"][0]["producto"]["imagen"]


def test_F08_admin_crud_producto(ernesto, anonimo):
    from pathlib import Path
    img = (Path(__file__).resolve().parents[2] / "chocomania-frontend" / "img" / "servicio-tortas.jpg").read_bytes()
    datos = {"nombre": "Torta selva negra", "precio": "19500", "categoria": "De leche", "stock": "4",
             "descripcion": "Bizcocho de chocolate con cerezas y crema.", "tags": "frutal, para regalar"}
    r = ernesto.post("/api/products", data=datos, files=[("imagenes", ("t.jpg", img, "image/jpeg"))])
    assert r.status_code == 201
    p = r.json()["product"]
    assert anonimo.get(p["imagen"]).headers["content-type"] == "image/jpeg"
    assert ernesto.put(f"/api/products/{p['id']}", data=dict(datos, precio="20500")).json()["product"]["precio"] == 20500
    assert ernesto.delete(f"/api/products/{p['id']}").status_code == 200
    assert anonimo.get(f"/api/products/{p['id']}").status_code == 404


def test_F09_cotizacion_y_contacto_llegan_al_admin(anonimo, ernesto):
    r = anonimo.post("/api/solicitudes", json={"tipo": "contacto", "email": "visita@example.com",
                                                "asunto": "Sugerencia", "mensaje": "Abran los domingos"})
    assert r.status_code == 201
    lista = ernesto.get("/api/admin/solicitudes").json()["solicitudes"]
    assert any(s["id"] == r.json()["id"] for s in lista)
    assert anonimo.get("/api/admin/solicitudes").status_code == 401
