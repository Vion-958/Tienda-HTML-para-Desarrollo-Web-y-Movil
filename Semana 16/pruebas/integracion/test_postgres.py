"""PostgreSQL: un rol y un esquema por servicio, URL en Vault. Solo corre con CHOCOMANIA_POSTGRES."""

import os

import pytest
from conftest import sesion

import iniciar

ADMIN = os.getenv("CHOCOMANIA_POSTGRES")
pytestmark = pytest.mark.skipif(not ADMIN, reason="sin CHOCOMANIA_POSTGRES las pruebas usan SQLite")


def raiz(stack) -> iniciar.ClienteVault:
    return iniciar.ClienteVault(iniciar.url("vault"), stack["secretos"]["vault_raiz"])


def test_BD01_la_url_de_la_base_esta_solo_en_vault(stack):
    v = raiz(stack)
    for servicio in iniciar.CON_BD:
        assert v.leer(servicio)["database_url"].startswith(f"postgresql://chocomania_{servicio}:")
        assert not any("postgresql://" in valor for valor in stack["env"][servicio].values())


def test_BD02_cada_rol_solo_ve_su_esquema(stack):
    import psycopg
    with psycopg.connect(raiz(stack).leer("orders")["database_url"], autocommit=True) as c:
        assert c.execute("SELECT count(*) FROM pedidos").fetchone()[0] >= 1
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("SELECT * FROM auth.usuarios")


def test_BD03_el_pedido_queda_en_postgres(stack, ana):
    import psycopg
    r = ana.post("/api/orders", json={"items": [{"producto_id": "choco-3", "cantidad": 1}],
                                      "entrega": "retiro", "metodo_pago": "transferencia"})
    assert r.status_code == 201
    pid = r.json()["order"]["id"]
    with psycopg.connect(ADMIN, autocommit=True) as c:
        fila = c.execute("SELECT user_id, estado FROM orders.pedidos WHERE id = %s", (pid,)).fetchone()
        reserva = c.execute("SELECT count(*) FROM inventory.reservas WHERE pedido_id = %s", (pid,)).fetchone()[0]
    assert fila == ("USR-001", "pendiente_pago")
    assert reserva == 1
    ana.post(f"/api/orders/{pid}/cancel")


def test_BD04_clave_de_la_base_rotada_en_vault_sin_reinicio(stack):
    import psycopg
    v = raiz(stack)
    nuevas = iniciar.preparar_postgres(ADMIN)
    for servicio, url_bd in nuevas.items():
        datos = v.leer(servicio)
        datos["database_url"] = url_bd
        v.escribir(servicio, datos)
    stack["secretos"]["bd"] = nuevas
    # Se cierran las conexiones abiertas: las nuevas deben usar la clave nueva.
    with psycopg.connect(ADMIN, autocommit=True) as c:
        c.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename LIKE 'chocomania_%%'")
    c = sesion("ana", "1234")
    try:
        assert c.get("/api/orders").status_code == 200
        assert c.get("/api/clients/me").status_code == 200
    finally:
        c.close()
