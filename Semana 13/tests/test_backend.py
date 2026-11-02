"""Backend: bloqueo de acceso directo, identidad propagada y rol admin."""

from conftest import ANA, ERNESTO, identity_headers


def test_acceso_directo_sin_secreto_403(backend_client):
    r = backend_client.get("/products")
    assert r.status_code == 403


def test_secreto_incorrecto_403(backend_client):
    r = backend_client.get("/products", headers=identity_headers("USR-001", "ana", "user", secret="falso"))
    assert r.status_code == 403


def test_identidad_inventada_sin_secreto_403(backend_client):
    """Un header X-Authenticated-User solo no basta: falta el secreto interno."""
    r = backend_client.get("/products", headers={
        "X-Authenticated-User": "USR-003",
        "X-Authenticated-Roles": "user,admin",
    })
    assert r.status_code == 403


def test_secreto_sin_identidad_403(backend_client):
    r = backend_client.get("/products", headers={"X-Gateway-Secret": ANA["X-Gateway-Secret"]})
    assert r.status_code == 403


def test_productos_con_identidad_del_gateway(backend_client):
    r = backend_client.get("/products", headers=ANA)
    assert r.status_code == 200
    assert r.json()["authenticated_user"] == "ana"
    assert len(r.json()["products"]) == 15


def test_rol_user_rechazado_en_operacion_admin(backend_client):
    r = backend_client.delete("/products/choco-1", headers=ANA)
    assert r.status_code == 403
    assert backend_client.get("/products/choco-1", headers=ANA).status_code == 200


def test_rol_admin_autorizado(backend_client):
    r = backend_client.delete("/products/choco-1", headers=ERNESTO)
    assert r.status_code == 200
    assert r.json()["deleted"] == "choco-1"
    assert backend_client.get("/products/choco-1", headers=ERNESTO).status_code == 404


def test_eliminar_producto_inexistente_404(backend_client):
    assert backend_client.delete("/products/no-existe", headers=ERNESTO).status_code == 404


def test_usuario_ve_solo_sus_pedidos(backend_client):
    pedidos = backend_client.get("/orders", headers=ANA).json()["orders"]
    assert pedidos
    assert {p["user_id"] for p in pedidos} == {"USR-001"}


def test_admin_ve_todos_los_pedidos(backend_client):
    pedidos = backend_client.get("/orders", headers=ERNESTO).json()["orders"]
    assert {p["user_id"] for p in pedidos} == {"USR-001", "USR-003"}


def test_pedido_nuevo_queda_a_nombre_del_usuario(backend_client):
    r = backend_client.post("/orders", headers=ANA,
                            json={"items": [{"producto_id": "choco-5", "cantidad": 2}]})
    assert r.status_code == 201
    pedido = r.json()["order"]
    assert pedido["user_id"] == "USR-001"
    assert pedido["total"] == 8400
