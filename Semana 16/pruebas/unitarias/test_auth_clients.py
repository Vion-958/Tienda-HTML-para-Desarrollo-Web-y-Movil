"""Auth Service y clients: hash con sal, sesiones revocables, registro y perfil propio."""

import pytest
from utiles import ANA, ERNESTO, cab, callers, cargar_servicio
from fastapi.testclient import TestClient


@pytest.fixture
def auth(tmp_path, monkeypatch):
    m = cargar_servicio("auth-service", monkeypatch, {"AUTH_DB": str(tmp_path / "a.db"), "SERVICE_CALLERS": callers("gateway")})
    return TestClient(m.app), m


@pytest.fixture
def clients(tmp_path, monkeypatch):
    m = cargar_servicio("clients", monkeypatch, {"CLIENTS_DB": str(tmp_path / "c.db"), "SERVICE_CALLERS": callers("gateway", "graphql")})
    return TestClient(m.app)


def test_login_introspect_logout(auth):
    cli, m = auth
    r = cli.post("/login", json={"username": "ana", "password": "1234"}, headers=cab())
    token = r.json()["access_token"]
    assert cli.post("/introspect", json={"token": token}, headers=cab()).json()["user_id"] == ANA
    assert cli.post("/logout", json={"token": token}, headers=cab()).json()["revoked"] is True
    assert cli.post("/introspect", json={"token": token}, headers=cab()).json() == {"active": False}
    # En la base no queda el token, solo su hash.
    with m.db.conexion() as con:
        assert con.execute("SELECT COUNT(*) FROM sesiones WHERE token_hash = ?", (token,)).fetchone()[0] == 0


def test_contrasena_incorrecta_y_solo_gateway(auth):
    cli, _ = auth
    assert cli.post("/login", json={"username": "ana", "password": "x"}, headers=cab()).status_code == 401
    assert cli.post("/login", json={"username": "ana", "password": "1234"}).status_code == 403


def test_registro_valida_y_guarda_hash_con_sal(auth):
    cli, m = auth
    assert cli.post("/register", json={"username": "Pe", "password": "corta"}, headers=cab()).status_code == 400
    r = cli.post("/register", json={"username": "camila", "password": "clave1234"}, headers=cab())
    assert r.status_code == 201 and r.json()["roles"] == ["user"]
    assert cli.post("/register", json={"username": "camila", "password": "clave1234"}, headers=cab()).status_code == 409
    with m.db.conexion() as con:
        fila = con.execute("SELECT * FROM usuarios WHERE username = 'camila'").fetchone()
    assert "clave1234" not in fila["hash"] and len(fila["sal"]) == 32 and fila["iteraciones"] >= 200000


def test_perfil_propio(clients):
    assert clients.get("/clients/me", headers=cab("gateway", ANA)).json()["client"]["email"] == "ana@example.com"
    r = clients.put("/clients/me", json={"nombre": "Ana P", "email": "ernesto@example.com"}, headers=cab("gateway", ANA))
    assert r.status_code == 409  # correo de otro cliente
    r = clients.put("/clients/me", json={"nombre": "Ana P", "email": "nuevo@example.com", "telefono": "abc"},
                    headers=cab("gateway", ANA))
    assert r.status_code == 422


def test_lote_graphql_solo_devuelve_el_propio(clients):
    r = clients.get(f"/internal/clients?ids={ANA},{ERNESTO}", headers=cab("graphql", ANA)).json()
    assert [c["user_id"] for c in r["clients"]] == [ANA]
    r = clients.get(f"/internal/clients?ids={ANA},{ERNESTO}", headers=cab("graphql", ERNESTO, "user,admin")).json()
    assert len(r["clients"]) == 2


def test_listado_de_clientes_solo_admin(clients):
    assert clients.get("/admin/clients", headers=cab("gateway", ANA)).status_code == 403
    assert clients.get("/admin/clients", headers=cab("gateway", ERNESTO, "user,admin")).status_code == 200


def test_solicitudes_publicas_y_gestion_admin(clients):
    cot = {"tipo": "cotizacion", "nombre": "Pia", "email": "pia@example.com", "asunto": "Tortas por encargo",
           "fecha_requerida": "2099-01-01", "cantidad": "40 unidades", "mensaje": "Torta de 3 pisos"}
    r = clients.post("/solicitudes", json=cot, headers=cab("gateway"))
    assert r.status_code == 201 and set(r.json()) == {"id", "tipo", "estado"}  # no devuelve datos personales
    assert clients.post("/solicitudes", json=dict(cot, fecha_requerida="2000-01-01"), headers=cab("gateway")).status_code == 422
    assert clients.post("/solicitudes", json=dict(cot, email="x"), headers=cab("gateway")).status_code == 422
    assert clients.get("/admin/solicitudes", headers=cab("gateway", ANA)).status_code == 403
    lista = clients.get("/admin/solicitudes", headers=cab("gateway", ERNESTO, "user,admin")).json()["solicitudes"]
    assert lista[0]["email"] == "pia@example.com"
    sid = lista[0]["id"]
    assert clients.patch(f"/admin/solicitudes/{sid}", json={"estado": "respondida"},
                         headers=cab("gateway", ERNESTO, "user,admin")).status_code == 200
