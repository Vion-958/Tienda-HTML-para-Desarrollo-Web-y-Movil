"""Secretos en Vault: aislamiento por servicio, rotacion sin reinicio y Vault caido (matriz de la guia)."""

import threading
import time
import urllib.error

import httpx
import pytest
from conftest import G, GRACIA_VAULT, TTL_VAULT, sesion

import iniciar
import rotar

PEDIDO = {"items": [{"producto_id": "choco-2", "cantidad": 1}], "entrega": "retiro", "metodo_pago": "transferencia"}


def raiz(stack) -> iniciar.ClienteVault:
    return iniciar.ClienteVault(iniciar.url("vault"), stack["secretos"]["vault_raiz"])


def test_S01_cada_servicio_lee_solo_su_ruta(stack):
    for servicio in iniciar.CON_VAULT:
        propio = iniciar.ClienteVault(iniciar.url("vault"), stack["tokens"][servicio])
        assert propio.leer(servicio)
        for otro in iniciar.CON_VAULT:
            if otro != servicio:
                with pytest.raises(urllib.error.HTTPError) as e:
                    propio.leer(otro)
                assert e.value.code == 403


def test_S02_un_servicio_no_puede_escribir_en_vault(stack):
    orders = iniciar.ClienteVault(iniciar.url("vault"), stack["tokens"]["orders"])
    with pytest.raises(urllib.error.HTTPError) as e:
        orders.escribir("orders", {"token_inventory": "x" * 32})
    assert e.value.code == 403


def test_S03_las_credenciales_no_estan_en_el_entorno(stack):
    credenciales = list(stack["secretos"]["cred"].values())
    for servicio in iniciar.CON_VAULT:
        env = stack["env"][servicio]
        assert set(k for k in env if "TOKEN" in k or "KEY" in k or "SECRET" in k) == {"VAULT_TOKEN"}
        assert not any(c in env.values() for c in credenciales)


def test_S04_health_informa_el_acceso_a_vault(stack):
    for servicio in ("auth", "inventory", "orders", "clients", "payments", "graphql", "gateway"):
        assert httpx.get(iniciar.url(servicio) + "/health").json()["vault"] == "ok"


def test_S05_rotacion_sin_reinicio_ni_cortes(stack):
    v = raiz(stack)
    vieja = v.leer("orders")["token_inventory"]
    errores, compras, parar = [], [], threading.Event()

    def comprar():
        c = sesion("ana", "1234")
        try:
            while not parar.is_set():
                r = c.post("/api/orders", json=PEDIDO)
                if r.status_code != 201:
                    errores.append(r.status_code)
                else:
                    compras.append(r.json()["order"]["id"])
                    c.post(f"/api/orders/{r.json()['order']['id']}/cancel")
                time.sleep(0.4)
        except Exception as e:
            errores.append(repr(e))
        finally:
            c.close()

    hilo = threading.Thread(target=comprar)
    hilo.start()
    try:
        nuevas = rotar.rotar(v, [("orders", "inventory")], TTL_VAULT, mostrar=lambda *_: None)
    finally:
        parar.set()
        hilo.join()
    assert errores == []
    assert len(compras) >= 4
    nueva = nuevas[("orders", "inventory")]
    assert v.leer("inventory")["llamador_orders"] == nueva
    # La anterior deja de servir cuando vence la cache de inventory (como maximo un TTL).
    time.sleep(TTL_VAULT + 1)
    directo = iniciar.url("inventory") + "/internal/reservations"
    cab = {"X-Service-Name": "orders", "X-Service-Token": vieja}
    assert httpx.post(directo, headers=cab, json={"pedido_id": 999999, "items": []}).status_code == 403
    cab["X-Service-Token"] = nueva
    assert httpx.post(directo, headers=cab, json={"pedido_id": 999999, "items": []}).status_code != 403
    stack["secretos"]["cred"][("orders", "inventory")] = nueva


def test_S06_rotacion_de_la_credencial_del_gateway(stack):
    nuevas = rotar.rotar(raiz(stack), [("gateway", "auth")], TTL_VAULT, mostrar=lambda *_: None)
    stack["secretos"]["cred"].update(nuevas)
    c = sesion("ana", "1234")
    assert c.get("/auth/me").json()["username"] == "ana"
    c.close()


def test_S07_vault_caido_usa_cache_y_luego_responde_503(stack):
    procesos = stack["procesos"]
    c = sesion("ana", "1234")
    try:
        assert c.get("/api/orders").status_code == 200
        procesos["vault"].terminate()
        procesos["vault"].wait(timeout=5)
        try:
            # Dentro de la gracia: los servicios siguen con la cache.
            assert c.get("/api/orders").status_code == 200
            time.sleep(GRACIA_VAULT + 1)
            r = c.get("/api/orders")
            assert r.status_code == 503
            assert "secretos" in r.json()["detail"]
            assert httpx.get(iniciar.url("orders") + "/health").json()["vault"] == "sin acceso"
        finally:
            # Vault vuelve con los mismos secretos y tokens: los servicios se recuperan solos.
            iniciar.arrancar(stack["env"], ["vault"], stack["logs"], lambda *_: None, procesos)
            iniciar.preparar_vault(iniciar.url("vault"), stack["secretos"], stack["tokens"])
        time.sleep(TTL_VAULT + 1)
        assert c.get("/api/orders").status_code == 200
        assert httpx.get(iniciar.url("orders") + "/health").json()["vault"] == "ok"
    finally:
        c.close()


def test_S08_token_de_vault_invalido_responde_503_controlado(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from utiles import cargar_servicio
    m = cargar_servicio("clients", monkeypatch, {"CLIENTS_DB": str(tmp_path / "c.db")})
    m.secretos.token = "token-que-no-existe"
    m.secretos.datos = None
    with TestClient(m.app) as cli:
        r = cli.get("/clients/me", headers={"X-Service-Name": "gateway", "X-Service-Token": "x" * 32, "X-User-Id": "USR-001"})
    assert r.status_code == 503
    assert r.json()["detail"] == "Servicio sin acceso a sus secretos"


def test_S09_servicio_caido_responde_503_controlado(stack, ana):
    procesos = stack["procesos"]
    procesos["clients"].terminate()
    procesos["clients"].wait(timeout=5)
    try:
        r = ana.get("/api/clients/me")
        assert r.status_code == 503
        assert r.json()["detail"] == "El servicio clients no est\u00e1 disponible"
        # El resto de la tienda sigue funcionando.
        assert ana.get("/api/products?tamano=2").status_code == 200
    finally:
        iniciar.arrancar(stack["env"], ["clients"], stack["logs"], lambda *_: None, procesos)
    assert ana.get("/api/clients/me").status_code == 200
