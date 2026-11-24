"""comun/secretos.py y la verificacion entre servicios con credenciales en Vault."""

import time

import pytest
from fastapi import HTTPException
from utiles import vault_de_prueba

from comun.secretos import Secretos, SinSecretos
from comun.seguridad import VerificadorServicio

A, B = "a" * 32, "b" * 32


@pytest.fixture
def vault():
    v = vault_de_prueba()
    v["cliente"].escribir("prueba", {"llamador_gateway": A, "token_orders": "t" * 32})
    return v


def secretos(v, **kw):
    return Secretos("prueba", addr=v["addr"], token=v["raiz"], **kw)


def test_lee_y_guarda_en_cache(vault):
    s = secretos(vault, ttl=60)
    assert s.get("token_orders") == "t" * 32
    vault["cliente"].escribir("prueba", {"llamador_gateway": B, "token_orders": "n" * 32})
    assert s.get("token_orders") == "t" * 32
    # El refresco forzado se limita a uno por segundo para no saturar Vault.
    assert s.get("token_orders", forzar=True) == "t" * 32
    time.sleep(1.1)
    assert s.get("token_orders", forzar=True) == "n" * 32


def test_refresca_al_vencer_el_ttl(vault):
    s = secretos(vault, ttl=0.2)
    v1 = s.todos() and s.version
    vault["cliente"].escribir("prueba", {"llamador_gateway": B})
    time.sleep(0.3)
    assert s.get("llamador_gateway") == B and s.version == v1 + 1


def test_vault_caido_usa_la_cache_durante_la_gracia(vault):
    s = secretos(vault, ttl=0, gracia=0.5)
    assert s.get("llamador_gateway") == A
    s.addr = "http://127.0.0.1:1"
    assert s.get("llamador_gateway") == A
    time.sleep(0.6)
    with pytest.raises(SinSecretos):
        s.get("llamador_gateway")
    assert not s.disponible()


def test_token_sin_permiso_no_obtiene_secretos(vault):
    s = Secretos("prueba", addr=vault["addr"], token="token-invalido")
    with pytest.raises(SinSecretos):
        s.todos()


def test_falta_clave(vault):
    with pytest.raises(SinSecretos):
        secretos(vault).get("no_existe")


def test_sin_token_no_arranca(monkeypatch):
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        Secretos("prueba")


def test_verificador_acepta_dos_credenciales_durante_la_rotacion(vault):
    s = secretos(vault, ttl=2)
    ver = VerificadorServicio(s)
    assert ver.identificar("gateway", A, "", "", "").nombre == "gateway"
    vault["cliente"].escribir("prueba", {"llamador_gateway": f"{B},{A}"})
    time.sleep(1.1)
    # Credencial desconocida: relee Vault una vez y la acepta sin esperar el TTL.
    assert ver.identificar("gateway", B, "", "", "").nombre == "gateway"
    assert ver.identificar("gateway", A, "", "", "").nombre == "gateway"
    vault["cliente"].escribir("prueba", {"llamador_gateway": B})
    # La anterior sigue valida hasta que vence la cache (TTL).
    assert ver.identificar("gateway", A, "", "", "").nombre == "gateway"
    time.sleep(2.1)
    with pytest.raises(HTTPException) as e:
        ver.identificar("gateway", A, "", "", "")
    assert e.value.status_code == 403


@pytest.mark.parametrize("nombre, token", [("gateway", ""), ("", A), ("orders", A), ("gateway", "corta")])
def test_verificador_rechaza(vault, nombre, token):
    with pytest.raises(HTTPException) as e:
        VerificadorServicio(secretos(vault)).identificar(nombre, token, "", "", "")
    assert e.value.status_code == 403
