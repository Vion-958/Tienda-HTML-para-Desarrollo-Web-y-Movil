"""
Prueba de integración del sistema completo (con todos los servicios arriba).

Secuencia: login -> cookie -> me -> products -> authorization -> logout

    pytest e2e/test_stack.py -q

Variables opcionales:
    GATEWAY_URL   por defecto http://localhost:8000
    BACKEND_URL   por defecto http://localhost:9000
    AUTH_URL      por defecto http://localhost:8100
"""

import os

import httpx
import pytest

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:9000")
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8100")


def nuevo_cliente():
    return httpx.Client(base_url=GATEWAY_URL, timeout=10.0)


def login(client, username, password):
    return client.post("/auth/login", json={"username": username, "password": password})


@pytest.fixture(scope="module", autouse=True)
def servicios_arriba():
    for url in (GATEWAY_URL, AUTH_URL, BACKEND_URL):
        try:
            r = httpx.get(f"{url}/health", timeout=3.0)
        except httpx.RequestError:
            pytest.exit(f"{url} no responde: levanta el sistema antes (docker compose up --build)")
        assert r.status_code == 200, url


def test_backend_directo_403():
    assert httpx.get(f"{BACKEND_URL}/products").status_code == 403


def test_introspect_directo_sin_secreto_403():
    r = httpx.post(f"{AUTH_URL}/introspect", json={"token": "x"})
    assert r.status_code == 403


def test_login_incorrecto_401():
    with nuevo_cliente() as client:
        r = login(client, "ana", "incorrecta")
        assert r.status_code == 401
        assert "session_token" not in client.cookies


def test_flujo_completo_ana():
    with nuevo_cliente() as client:
        # login -> cookie HttpOnly, el token no viaja en el cuerpo
        r = login(client, "ana", "1234")
        assert r.status_code == 200
        assert r.json()["roles"] == ["user"]
        assert "access_token" not in r.text
        set_cookie = r.headers["set-cookie"].lower()
        assert "session_token=" in set_cookie
        assert "httponly" in set_cookie
        assert "samesite=lax" in set_cookie
        token = client.cookies["session_token"]

        # me
        r = client.get("/auth/me")
        assert r.status_code == 200
        assert r.json()["username"] == "ana"

        # products y orders (solo los suyos)
        r = client.get("/api/products")
        assert r.status_code == 200
        assert r.json()["authenticated_user"] == "ana"
        productos = r.json()["products"]
        assert productos

        r = client.get("/api/orders")
        assert r.status_code == 200
        assert {o["user_id"] for o in r.json()["orders"]} <= {"USR-001"}

        # authorization: Ana no es admin
        r = client.delete(f"/api/products/{productos[-1]['id']}")
        assert r.status_code == 403

        # logout = revocación + cookie eliminada
        r = client.post("/auth/logout")
        assert r.status_code == 200
        assert r.json()["revoked"] is True
        assert client.get("/auth/me").status_code == 401

    # El token anterior ya no sirve aunque alguien lo haya copiado.
    with nuevo_cliente() as otro:
        otro.cookies.set("session_token", token)
        assert otro.get("/api/products").status_code == 401


def test_admin_elimina_producto():
    with nuevo_cliente() as client:
        assert login(client, "ernesto", "admin123").status_code == 200
        productos = client.get("/api/products").json()["products"]
        assert productos, "No quedan productos: reinicia el backend para restaurar el catálogo"
        objetivo = productos[-1]["id"]

        r = client.delete(f"/api/products/{objetivo}")
        assert r.status_code == 200
        assert r.json()["deleted"] == objetivo
        assert client.get(f"/api/products/{objetivo}").status_code == 404

        # el admin ve los pedidos de todos
        usuarios = {o["user_id"] for o in client.get("/api/orders").json()["orders"]}
        assert {"USR-001", "USR-003"} <= usuarios
        client.post("/auth/logout")


def test_headers_de_identidad_inventados_no_sirven():
    r = httpx.get(f"{GATEWAY_URL}/api/products", headers={
        "X-Authenticated-User": "USR-003",
        "X-Authenticated-Roles": "user,admin",
        "X-Gateway-Secret": "adivinando",
    })
    assert r.status_code == 401


def test_el_gateway_sirve_el_sitio():
    r = httpx.get(f"{GATEWAY_URL}/cuenta.php")
    assert r.status_code == 200
    assert "Mi cuenta" in r.text
