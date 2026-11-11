"""GraphQL Gateway privado: agrega orders, inventory, payments y clients."""

import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402
import strawberry  # noqa: E402
from fastapi import Depends, FastAPI, Request  # noqa: E402
from strawberry.dataloader import DataLoader  # noqa: E402
from graphql.validation import NoSchemaIntrospectionCustomRule  # noqa: E402
from strawberry.extensions import AddValidationRules, MaxAliasesLimiter, MaxTokensLimiter, QueryDepthLimiter  # noqa: E402
from strawberry.fastapi import BaseContext, GraphQLRouter  # noqa: E402
from strawberry.types import Info  # noqa: E402

from comun.registro import configurar  # noqa: E402
from comun.seguridad import Llamador, Usuario, VerificadorServicio, cabeceras_servicio, credenciales_desde_entorno  # noqa: E402

app = FastAPI(title="ChocoMania GraphQL Gateway")
log = configurar(app, "graphql")
seg = VerificadorServicio(credenciales_desde_entorno())

DESTINOS = {
    "orders": (os.getenv("ORDERS_URL", "http://127.0.0.1:9102"), os.getenv("GRAPHQL_ORDERS_TOKEN", "")),
    "inventory": (os.getenv("INVENTORY_URL", "http://127.0.0.1:9101"), os.getenv("GRAPHQL_INVENTORY_TOKEN", "")),
    "payments": (os.getenv("PAYMENTS_URL", "http://127.0.0.1:9104"), os.getenv("GRAPHQL_PAYMENTS_TOKEN", "")),
    "clients": (os.getenv("CLIENTS_URL", "http://127.0.0.1:9103"), os.getenv("GRAPHQL_CLIENTS_TOKEN", "")),
}
TIMEOUT = float(os.getenv("UPSTREAM_TIMEOUT", "3"))
HTTP = httpx.AsyncClient(timeout=TIMEOUT, limits=httpx.Limits(max_connections=100, max_keepalive_connections=40))
TAMANO_MAX = 20


class ErrorServicio(Exception):
    """Un subsistema no respondio: el campo queda en null y se informa en 'errors'."""


class Contexto(BaseContext):
    def __init__(self, usuario: Usuario, request_id: str):
        super().__init__()
        self.usuario = usuario
        self.request_id = request_id
        self.http = HTTP
        self.productos = DataLoader(load_fn=self._cargar_productos)
        self.pagos = DataLoader(load_fn=self._cargar_pagos)
        self.clientes = DataLoader(load_fn=self._cargar_clientes)

    async def get(self, servicio: str, ruta: str, **params):
        base, token = DESTINOS[servicio]
        cab = cabeceras_servicio("graphql", token, self.request_id, self.usuario)
        try:
            r = await self.http.get(f"{base}{ruta}", headers=cab, params=params)
        except httpx.HTTPError:
            raise ErrorServicio(f"{servicio} no disponible")
        if r.status_code == 404:
            return None
        if r.status_code == 403:
            raise PermissionError("No autorizado")
        if r.status_code != 200:
            raise ErrorServicio(f"{servicio} respondio {r.status_code}")
        return r.json()

    # Batching: una llamada por tipo y consulta.
    async def _cargar_productos(self, ids: list[str]):
        datos = await self.get("inventory", "/internal/products", ids=",".join(ids))
        por_id = {p["id"]: p for p in datos["products"]}
        return [por_id.get(i) for i in ids]

    async def _cargar_pagos(self, pedidos: list[int]):
        datos = await self.get("payments", "/internal/payments", pedidos=",".join(map(str, pedidos)))
        por_pedido = {p["pedido_id"]: p for p in datos["payments"]}
        return [por_pedido.get(p) for p in pedidos]

    async def _cargar_clientes(self, ids: list[str]):
        datos = await self.get("clients", "/internal/clients", ids=",".join(ids))
        por_id = {c["user_id"]: c for c in datos["clients"]}
        return [por_id.get(i) for i in ids]


# --- tipos

@strawberry.type
class Producto:
    id: str
    nombre: str
    imagen: Optional[str]
    disponible: bool
    activo: bool


@strawberry.type
class Pago:
    id: str
    estado: str
    metodo: str
    monto: int


@strawberry.type
class Cliente:
    nombre: str
    email: str
    telefono: str
    comuna: str


@strawberry.type
class Evento:
    estado_anterior: Optional[str]
    estado_nuevo: str
    creado: str


@strawberry.type
class Item:
    producto_id: str
    nombre: str
    cantidad: int
    precio_unitario: int

    @strawberry.field
    def subtotal(self) -> int:
        return self.cantidad * self.precio_unitario

    @strawberry.field(description="Datos actuales del catalogo (inventory)")
    async def producto(self, info: Info) -> Optional[Producto]:
        p = await info.context.productos.load(self.producto_id)
        if not p:
            return None
        return Producto(id=p["id"], nombre=p["nombre"], imagen=p["imagen"],
                        disponible=p["disponible"], activo=p.get("activo", True))


@strawberry.type
class Pedido:
    id: int
    estado: str
    entrega: str
    comuna: str
    direccion: str
    metodo_pago: str
    subtotal: int
    costo_envio: int
    total: int
    creado: str
    items: list[Item]
    user_id: strawberry.Private[str]
    eventos_crudos: strawberry.Private[Optional[list]]

    @strawberry.field(description="Ultimo pago (payments)")
    async def pago(self, info: Info) -> Optional[Pago]:
        p = await info.context.pagos.load(self.id)
        if not p:
            return None
        # Un pago pendiente de un pedido cancelado ya no se puede cobrar.
        estado = "anulado" if self.estado == "cancelado" and p["estado"] == "pendiente" else p["estado"]
        return Pago(id=p["id"], estado=estado, metodo=p["metodo"], monto=p["monto"])

    @strawberry.field(description="Perfil del cliente (clients). Solo el dueno o un admin.")
    async def cliente(self, info: Info) -> Optional[Cliente]:
        c = await info.context.clientes.load(self.user_id)
        return Cliente(nombre=c["nombre"], email=c["email"], telefono=c["telefono"], comuna=c["comuna"]) if c else None

    @strawberry.field(description="Historial de estados. Solo en la consulta 'pedido'.")
    def eventos(self) -> Optional[list[Evento]]:
        if self.eventos_crudos is None:
            return None
        return [Evento(estado_anterior=e["estado_anterior"], estado_nuevo=e["estado_nuevo"], creado=e["creado"])
                for e in self.eventos_crudos]


@strawberry.type
class PaginaPedidos:
    pedidos: list[Pedido]
    total: int
    pagina: int


def _pedido(d: dict) -> Pedido:
    return Pedido(
        id=d["id"], estado=d["estado"], entrega=d["entrega"], comuna=d["comuna"], direccion=d["direccion"],
        metodo_pago=d["metodo_pago"], subtotal=d["subtotal"], costo_envio=d["costo_envio"], total=d["total"],
        creado=d["creado"], user_id=d["user_id"], eventos_crudos=d.get("eventos"),
        items=[Item(producto_id=i["producto_id"], nombre=i["nombre"], cantidad=i["cantidad"],
                    precio_unitario=i["precio_unitario"]) for i in d["items"]],
    )


def _pagina(datos: dict) -> PaginaPedidos:
    return PaginaPedidos(pedidos=[_pedido(o) for o in datos["orders"]], total=datos["total"], pagina=datos["pagina"])


@strawberry.type
class Query:
    @strawberry.field(description="Pedidos del usuario autenticado, con productos y pago")
    async def mis_pedidos(self, info: Info, pagina: int = 1, tamano: int = 10) -> PaginaPedidos:
        tamano = max(1, min(tamano, TAMANO_MAX))
        return _pagina(await info.context.get("orders", "/orders", pagina=max(pagina, 1), tamano=tamano))

    @strawberry.field(description="Un pedido propio (o cualquiera si es admin), con historial")
    async def pedido(self, info: Info, id: int) -> Optional[Pedido]:
        datos = await info.context.get("orders", f"/orders/{id}")
        return _pedido(datos["order"]) if datos else None

    @strawberry.field(description="Todos los pedidos. Solo rol admin.")
    async def pedidos_admin(self, info: Info, estado: Optional[str] = None, pagina: int = 1,
                            tamano: int = 10) -> PaginaPedidos:
        if not info.context.usuario.es_admin:
            raise PermissionError("Se requiere el rol admin")
        params = {"pagina": max(pagina, 1), "tamano": max(1, min(tamano, TAMANO_MAX))}
        if estado:
            params["estado"] = estado
        return _pagina(await info.context.get("orders", "/admin/orders", **params))


schema = strawberry.Schema(
    query=Query,
    extensions=[
        lambda: QueryDepthLimiter(max_depth=6),
        lambda: MaxAliasesLimiter(max_alias_count=10),
        lambda: MaxTokensLimiter(max_token_count=1500),
        *([] if os.getenv("GRAPHQL_INTROSPECCION") == "1"
          else [lambda: AddValidationRules([NoSchemaIntrospectionCustomRule])]),
    ],
)


async def contexto(request: Request, llamador: Llamador = Depends(seg.requiere("gateway", con_usuario=True))):
    return Contexto(llamador.usuario, request.state.request_id)


router = GraphQLRouter(
    schema,
    context_getter=contexto,
    graphql_ide=None,
    allow_queries_via_get=False,
)
app.include_router(router, prefix="/graphql")


@app.get("/health")
def health():
    return {"status": "OK", "service": "graphql"}
