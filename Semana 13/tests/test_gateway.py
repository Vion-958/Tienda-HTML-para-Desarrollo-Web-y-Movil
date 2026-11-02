"""Gateway: sesión requerida, política de roles y cookie.

Vault y el Auth Service se reemplazan por funciones falsas (monkeypatch),
así estas pruebas no necesitan ningún otro servicio corriendo.
"""

import pytest

import gateway

SECRETOS = {"backend_shared_secret": "x", "auth_introspection_secret": "y"}
SESIONES = {
    "token-ana": {"active": True, "user_id": "USR-001", "username": "ana", "roles": ["user"], "expires_in": 900},
    "token-ernesto": {"active": True, "user_id": "USR-003", "username": "ernesto",
                      "roles": ["user", "admin"], "expires_in": 900},
}


@pytest.fixture
def servicios_falsos(monkeypatch):
    async def fake_vault():
        return SECRETOS

    async def fake_introspect(token, vault_secrets):
        return SESIONES.get(token)

    monkeypatch.setattr(gateway, "get_vault_secrets", fake_vault)
    monkeypatch.setattr(gateway, "introspect", fake_introspect)


def test_politica_delete_productos_requiere_admin():
    assert gateway.required_role("DELETE", "products/choco-1") == "admin"
    assert gateway.required_role("GET", "products/choco-1") is None
    assert gateway.required_role("GET", "products") is None
    assert gateway.required_role("GET", "orders") is None


def test_api_sin_cookie_401(gateway_client):
    r = gateway_client.get("/api/products")
    assert r.status_code == 401


def test_me_sin_cookie_401(gateway_client):
    assert gateway_client.get("/auth/me").status_code == 401


def test_header_de_identidad_inventado_no_sirve(gateway_client):
    r = gateway_client.get("/api/products", headers={
        "X-Authenticated-User": "USR-003",
        "X-Authenticated-Roles": "user,admin",
    })
    assert r.status_code == 401


def test_token_invalido_401(gateway_client, servicios_falsos):
    gateway_client.cookies.set("session_token", "token-falso")
    assert gateway_client.get("/api/products").status_code == 401


def test_me_con_sesion_valida(gateway_client, servicios_falsos):
    gateway_client.cookies.set("session_token", "token-ana")
    r = gateway_client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["username"] == "ana"
    assert "token" not in r.text


def test_user_rechazado_en_delete_antes_de_llegar_al_backend(gateway_client, servicios_falsos, monkeypatch):
    llamado = {"backend": False}

    class NoDeberiaLlamarse:
        def __init__(self, *a, **k):
            llamado["backend"] = True
            raise AssertionError("El Gateway no debió llamar al Backend")

    monkeypatch.setattr(gateway.httpx, "AsyncClient", NoDeberiaLlamarse)
    gateway_client.cookies.set("session_token", "token-ana")
    r = gateway_client.delete("/api/products/choco-1")
    assert r.status_code == 403
    assert llamado["backend"] is False


def test_logout_borra_la_cookie(gateway_client):
    r = gateway_client.post("/auth/logout")
    assert r.status_code == 200
    set_cookie = r.headers["set-cookie"]
    assert "session_token=" in set_cookie
    assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower()
    assert "httponly" in set_cookie.lower()
