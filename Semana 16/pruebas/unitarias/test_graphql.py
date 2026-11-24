"""GraphQL Gateway: agregacion, batching, autorizacion por campo, limites y errores parciales."""

import pytest
from utiles import ANA, ERNESTO, cab, callers, cargar_servicio
from fastapi.testclient import TestClient

PEDIDOS = {"orders": [
    {"id": 1003, "user_id": ANA, "estado": "pendiente_pago", "entrega": "retiro", "comuna": "", "direccion": "",
     "metodo_pago": "tarjeta", "subtotal": 10400, "costo_envio": 0, "total": 10400, "creado": "2026-11-09",
     "items": [{"producto_id": "choco-7", "nombre": "Alfajores", "cantidad": 2, "precio_unitario": 5200},
               {"producto_id": "choco-8", "nombre": "Barra", "cantidad": 1, "precio_unitario": 4800}]},
    {"id": 1001, "user_id": ANA, "estado": "pagado", "entrega": "retiro", "comuna": "", "direccion": "",
     "metodo_pago": "tarjeta", "subtotal": 15800, "costo_envio": 0, "total": 15800, "creado": "2026-11-08",
     "items": [{"producto_id": "choco-7", "nombre": "Alfajores", "cantidad": 1, "precio_unitario": 5200}]},
], "total": 2, "pagina": 1}


@pytest.fixture
def ctx(monkeypatch):
    m = cargar_servicio("graphql-gateway", monkeypatch, {"SERVICE_CALLERS": callers("gateway")})
    llamadas = []
    caidos = set()

    async def falso(self, servicio, ruta, **params):
        llamadas.append((servicio, ruta, params))
        if servicio in caidos:
            raise m.ErrorServicio(f"{servicio} no disponible")
        if ruta in ("/orders", "/admin/orders"):
            return PEDIDOS
        if ruta == "/internal/products":
            return {"products": [{"id": i, "nombre": i, "imagen": f"/img/{i}", "disponible": True, "activo": True}
                                 for i in params["ids"].split(",")]}
        if ruta == "/internal/payments":
            return {"payments": [{"id": "PAY-1", "pedido_id": 1001, "estado": "aprobado", "metodo": "tarjeta", "monto": 15800}]}
        return None

    monkeypatch.setattr(m.Contexto, "get", falso)
    return TestClient(m.app), llamadas, caidos


def q(cli, query, user=ANA, roles="user"):
    return cli.post("/graphql", json={"query": query}, headers=cab("gateway", user, roles)).json()


CONSULTA = "{ misPedidos { pedidos { id pago { estado } items { nombre producto { imagen } } } } }"


def test_agrega_tres_subsistemas_con_una_llamada_por_tipo(ctx):
    cli, llamadas, _ = ctx
    r = q(cli, CONSULTA)
    assert r["data"]["misPedidos"]["pedidos"][1]["pago"]["estado"] == "aprobado"
    assert r["data"]["misPedidos"]["pedidos"][0]["items"][0]["producto"]["imagen"] == "/img/choco-7"
    servicios = [c[0] for c in llamadas]
    # Batching: una llamada por servicio.
    assert servicios.count("inventory") == 1 and servicios.count("payments") == 1


def test_error_parcial_si_un_servicio_cae(ctx):
    cli, _, caidos = ctx
    caidos.add("payments")
    r = q(cli, CONSULTA)
    assert r["data"]["misPedidos"]["pedidos"][0]["items"][0]["producto"]["imagen"]
    assert r["data"]["misPedidos"]["pedidos"][0]["pago"] is None
    assert any("payments no disponible" in e["message"] for e in r["errors"])


def test_consulta_admin_requiere_rol(ctx):
    cli, _, _ = ctx
    assert q(cli, "{ pedidosAdmin { total } }")["errors"][0]["message"] == "Se requiere el rol admin"
    assert q(cli, "{ pedidosAdmin { total } }", ERNESTO, "user,admin")["data"]["pedidosAdmin"]["total"] == 2


def test_limites(ctx):
    cli, _, _ = ctx
    alias = "{ " + " ".join(f"a{i}: misPedidos {{ total }}" for i in range(12)) + " }"
    assert "errors" in q(cli, alias)
    assert "introspection" in q(cli, "{ __schema { types { name } } }")["errors"][0]["message"]
    assert "errors" in q(cli, "{ misPedidos { pedidos { id " + "estado " * 1600 + "} } }")


def test_tamano_maximo(ctx):
    cli, llamadas, _ = ctx
    q(cli, "{ misPedidos(tamano: 500) { total } }")
    assert llamadas[0][2]["tamano"] == 20


def test_solo_el_gateway_puede_llamar(ctx):
    cli, _, _ = ctx
    r = cli.post("/graphql", json={"query": "{ misPedidos { total } }"},
                 headers={"X-User-Id": ERNESTO, "X-User-Roles": "admin"})
    assert r.status_code == 403
