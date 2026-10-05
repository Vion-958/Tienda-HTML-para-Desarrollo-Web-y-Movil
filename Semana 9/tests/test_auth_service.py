"""Auth Service: login, introspección, revocación y expiración."""

import time

import auth_service
from conftest import AUTH_SECRET

GW = {"X-Introspection-Secret": AUTH_SECRET}


def login(client, username, password):
    return client.post("/login", json={"username": username, "password": password})


def test_login_valido_entrega_token(auth_client):
    r = login(auth_client, "ana", "1234")
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == auth_service.SESSION_TTL_SECONDS
    assert len(body["access_token"]) >= 32


def test_login_password_incorrecta_401(auth_client):
    r = login(auth_client, "ana", "incorrecta")
    assert r.status_code == 401
    assert auth_service.SESSIONS == {}


def test_login_usuario_inexistente_401(auth_client):
    assert login(auth_client, "mallory", "1234").status_code == 401


def test_passwords_no_estan_en_texto_plano():
    for user in auth_service.USERS.values():
        assert "password" not in user
        assert user["password_hash"] not in ("1234", "admin123")


def test_introspect_token_valido(auth_client):
    token = login(auth_client, "ana", "1234").json()["access_token"]
    r = auth_client.post("/introspect", json={"token": token}, headers=GW)
    assert r.status_code == 200
    body = r.json()
    assert body["active"] is True
    assert body["user_id"] == "USR-001"
    assert body["username"] == "ana"
    assert body["roles"] == ["user"]


def test_introspect_token_inexistente(auth_client):
    r = auth_client.post("/introspect", json={"token": "no-existe"}, headers=GW)
    assert r.status_code == 200
    assert r.json() == {"active": False}


def test_introspect_sin_secreto_del_gateway_403(auth_client):
    token = login(auth_client, "ana", "1234").json()["access_token"]
    r = auth_client.post("/introspect", json={"token": token})
    assert r.status_code == 403
    r = auth_client.post("/introspect", json={"token": token},
                         headers={"X-Introspection-Secret": "otro"})
    assert r.status_code == 403


def test_token_revocado_queda_inactivo(auth_client):
    token = login(auth_client, "ana", "1234").json()["access_token"]
    r = auth_client.post("/logout", json={"token": token}, headers=GW)
    assert r.status_code == 200
    assert r.json() == {"revoked": True}
    r = auth_client.post("/introspect", json={"token": token}, headers=GW)
    assert r.json() == {"active": False}


def test_logout_sin_secreto_403(auth_client):
    token = login(auth_client, "ana", "1234").json()["access_token"]
    assert auth_client.post("/logout", json={"token": token}).status_code == 403


def test_token_expirado_queda_inactivo(auth_client):
    token = login(auth_client, "ana", "1234").json()["access_token"]
    auth_service.SESSIONS[token]["expires_at"] = time.time() - 1
    r = auth_client.post("/introspect", json={"token": token}, headers=GW)
    assert r.json() == {"active": False}
    assert token not in auth_service.SESSIONS


def test_admin_tiene_rol_admin(auth_client):
    token = login(auth_client, "ernesto", "admin123").json()["access_token"]
    r = auth_client.post("/introspect", json={"token": token}, headers=GW)
    assert r.json()["roles"] == ["user", "admin"]
