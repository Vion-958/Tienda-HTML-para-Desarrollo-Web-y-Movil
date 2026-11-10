"""orders: pedidos y su ciclo de vida. Autoridad del estado del pedido."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402
from fastapi import Depends, FastAPI, HTTPException, Query, Request  # noqa: E402
from pydantic import BaseModel, Field, model_validator  # noqa: E402

from comun.db import BaseDatos  # noqa: E402
from comun.registro import configurar  # noqa: E402
from comun.seguridad import Llamador, Usuario, VerificadorServicio, cabeceras_servicio, credenciales_desde_entorno  # noqa: E402

AQUI = Path(__file__).resolve().parent
app = FastAPI(title="ChocoMania orders")
log = configurar(app, "orders")
db = BaseDatos(os.getenv("ORDERS_DB", str(AQUI / "data" / "orders.db")), AQUI / "schema.sql", AQUI / "seed.sql")
seg = VerificadorServicio(credenciales_desde_entorno())

INVENTORY_URL = os.getenv("INVENTORY_URL", "http://127.0.0.1:9101")
TOKEN_INVENTORY = os.getenv("ORDERS_INVENTORY_TOKEN", "")
TIMEOUT = float(os.getenv("UPSTREAM_TIMEOUT", "4"))
HTTP = httpx.Client(timeout=TIMEOUT, limits=httpx.Limits(max_connections=50, max_keepalive_connections=20))

ENVIO_DELIVERY = 3000
ENVIO_GRATIS_DESDE = 30000

# Estado actual -> estados permitidos.
TRANSICIONES_ADMIN = {
    "pendiente_pago": {"cancelado"},
    "pagado": {"en_preparacion", "cancelado"},
    "en_preparacion": {"listo_retiro", "despachado", "cancelado"},
    "listo_retiro": {"entregado"},
    "despachado": {"entregado"},
}
CANCELABLE_POR_CLIENTE = {"pendiente_pago"}
VISIBLES = "estado NOT IN ('creando', 'fallido')"


class ItemPedido(BaseModel):
    producto_id: str = Field(min_length=1, max_length=20)
    cantidad: int = Field(ge=1, le=50)


class NuevoPedido(BaseModel):
    items: list[ItemPedido] = Field(min_length=1, max_length=30)
    entrega: str = Field(pattern="^(retiro|delivery)$")
    metodo_pago: str = Field(pattern="^(tarjeta|transferencia)$")
    direccion: str = Field(default="", max_length=150)
    comuna: str = Field(default="", max_length=50)
    nota: str = Field(default="", max_length=200)

    @model_validator(mode="after")
    def direccion_si_delivery(self):
        self.direccion, self.comuna = self.direccion.strip(), self.comuna.strip()
        if self.entrega == "delivery" and (len(self.direccion) < 5 or len(self.comuna) < 2):
            raise ValueError("Para delivery se requiere direcci\u00f3n y comuna")
        if self.entrega == "retiro":
            self.direccion, self.comuna = "", ""
        return self


class CambioEstado(BaseModel):
    estado: str = Field(max_length=20)
    motivo: str = Field(default="", max_length=200)


class Pagado(BaseModel):
    pago_id: str = Field(min_length=3, max_length=40)


# --- utilidades

def _inventory(metodo: str, ruta: str, request_id: str, **kwargs) -> httpx.Response:
    cab = cabeceras_servicio("orders", TOKEN_INVENTORY, request_id)
    return HTTP.request(metodo, f"{INVENTORY_URL}{ruta}", headers=cab, **kwargs)


def _pedido(con, fila, con_eventos=False) -> dict:
    items = con.execute(
        "SELECT producto_id, nombre, precio_unitario, cantidad FROM pedido_items WHERE pedido_id = ? ORDER BY rowid",
        (fila["id"],),
    ).fetchall()
    p = {
        "id": fila["id"],
        "user_id": fila["user_id"],
        "estado": fila["estado"],
        "entrega": fila["entrega"],
        "direccion": fila["direccion"],
        "comuna": fila["comuna"],
        "nota": fila["nota"],
        "metodo_pago": fila["metodo_pago"],
        "subtotal": fila["subtotal"],
        "costo_envio": fila["costo_envio"],
        "total": fila["total"],
        "pago_id": fila["pago_id"],
        "creado": fila["creado"],
        "actualizado": fila["actualizado"],
        "items": [dict(i) for i in items],
    }
    if con_eventos:
        p["eventos"] = [dict(e) for e in con.execute(
            "SELECT estado_anterior, estado_nuevo, actor, motivo, creado FROM pedido_eventos"
            " WHERE pedido_id = ? ORDER BY id", (fila["id"],))]
    return p


def _evento(con, pedido_id: int, anterior: str | None, nuevo: str, actor: str, motivo: str = ""):
    con.execute(
        "INSERT INTO pedido_eventos (pedido_id, estado_anterior, estado_nuevo, actor, motivo) VALUES (?, ?, ?, ?, ?)",
        (pedido_id, anterior, nuevo, actor, motivo),
    )


def _cambiar(con, fila, nuevo: str, actor: str, motivo: str = ""):
    con.execute("UPDATE pedidos SET estado = ?, actualizado = datetime('now') WHERE id = ?", (nuevo, fila["id"]))
    _evento(con, fila["id"], fila["estado"], nuevo, actor, motivo)


def _propio_o_404(con, pedido_id: int, usuario: Usuario):
    """Un pedido ajeno responde igual que uno inexistente: no se revela que existe."""
    fila = con.execute(f"SELECT * FROM pedidos WHERE id = ? AND {VISIBLES}", (pedido_id,)).fetchone()
    if not fila or (fila["user_id"] != usuario.user_id and not usuario.es_admin):
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return fila


def _liberar_stock(pedido_id: int, request_id: str) -> bool:
    try:
        r = _inventory("POST", f"/internal/reservations/{pedido_id}/release", request_id)
        return r.status_code == 200
    except httpx.HTTPError:
        log.warning("rid=%s no se pudo liberar stock pedido=%s", request_id, pedido_id)
        return False


# --- endpoints

@app.get("/health")
def health():
    with db.conexion() as con:
        con.execute("SELECT 1")
    return {"status": "OK", "service": "orders"}


@app.post("/orders", status_code=201)
def crear(datos: NuevoPedido, request: Request,
          llamador: Llamador = Depends(seg.requiere("gateway", con_usuario=True))):
    rid = request.state.request_id
    usuario = llamador.usuario

    # Pedido invisible para tener un id idempotente.
    with db.transaccion() as con:
        pid = con.execute(
            "INSERT INTO pedidos (user_id, estado, entrega, direccion, comuna, nota, metodo_pago)"
            " VALUES (?, 'creando', ?, ?, ?, ?, ?)",
            (usuario.user_id, datos.entrega, datos.direccion, datos.comuna, datos.nota.strip(), datos.metodo_pago),
        ).lastrowid

    # inventory aparta stock y entrega el precio.
    cuerpo = {"pedido_id": pid, "items": [i.model_dump() for i in datos.items]}
    try:
        r = _inventory("POST", "/internal/reservations", rid, json=cuerpo)
    except httpx.HTTPError:
        # Compensacion: liberar por si alcanzo a reservar.
        _liberar_stock(pid, rid)
        with db.transaccion() as con:
            con.execute("UPDATE pedidos SET estado = 'fallido' WHERE id = ?", (pid,))
        log.warning("rid=%s inventory no responde, pedido=%s fallido", rid, pid)
        raise HTTPException(status_code=503, detail="No pudimos verificar el stock. Intenta de nuevo en unos minutos.")

    if r.status_code in (400, 409):
        with db.transaccion() as con:
            con.execute("DELETE FROM pedidos WHERE id = ?", (pid,))
        raise HTTPException(status_code=r.status_code, detail=r.json().get("detail"))
    if r.status_code != 200:
        _liberar_stock(pid, rid)
        with db.transaccion() as con:
            con.execute("UPDATE pedidos SET estado = 'fallido' WHERE id = ?", (pid,))
        raise HTTPException(status_code=503, detail="No pudimos verificar el stock. Intenta de nuevo en unos minutos.")

    # Totales con precios de inventory.
    reservados = r.json()["items"]
    subtotal = sum(i["precio_unitario"] * i["cantidad"] for i in reservados)
    envio = ENVIO_DELIVERY if datos.entrega == "delivery" and subtotal < ENVIO_GRATIS_DESDE else 0
    with db.transaccion() as con:
        con.executemany(
            "INSERT INTO pedido_items (pedido_id, producto_id, nombre, precio_unitario, cantidad) VALUES (?, ?, ?, ?, ?)",
            [(pid, i["producto_id"], i["nombre"], i["precio_unitario"], i["cantidad"]) for i in reservados],
        )
        con.execute(
            "UPDATE pedidos SET estado = 'pendiente_pago', subtotal = ?, costo_envio = ?, total = ? WHERE id = ?",
            (subtotal, envio, subtotal + envio, pid),
        )
        _evento(con, pid, None, "pendiente_pago", usuario.user_id)
        fila = con.execute("SELECT * FROM pedidos WHERE id = ?", (pid,)).fetchone()
        pedido = _pedido(con, fila)
    log.info("rid=%s pedido creado id=%s user=%s total=%s", rid, pid, usuario.user_id, pedido["total"])
    return {"order": pedido}


@app.get("/orders")
def mis_pedidos(
    pagina: int = Query(1, ge=1),
    tamano: int = Query(20, ge=1, le=50),
    llamador: Llamador = Depends(seg.requiere("gateway", "graphql", con_usuario=True)),
):
    uid = llamador.usuario.user_id
    with db.conexion() as con:
        total = con.execute(f"SELECT COUNT(*) FROM pedidos WHERE user_id = ? AND {VISIBLES}", (uid,)).fetchone()[0]
        filas = con.execute(
            f"SELECT * FROM pedidos WHERE user_id = ? AND {VISIBLES} ORDER BY id DESC LIMIT ? OFFSET ?",
            (uid, tamano, (pagina - 1) * tamano),
        ).fetchall()
        return {"orders": [_pedido(con, f) for f in filas], "total": total, "pagina": pagina}


@app.get("/orders/{pedido_id}")
def ver(pedido_id: int, llamador: Llamador = Depends(seg.requiere("gateway", "graphql", con_usuario=True))):
    with db.conexion() as con:
        return {"order": _pedido(con, _propio_o_404(con, pedido_id, llamador.usuario), con_eventos=True)}


@app.post("/orders/{pedido_id}/cancel")
def cancelar(pedido_id: int, request: Request,
             llamador: Llamador = Depends(seg.requiere("gateway", con_usuario=True))):
    """Anular no borra: el pedido queda 'cancelado' con su historial."""
    usuario = llamador.usuario
    with db.transaccion() as con:
        fila = _propio_o_404(con, pedido_id, usuario)
        propio = fila["user_id"] == usuario.user_id
        if fila["estado"] == "cancelado":
            raise HTTPException(status_code=409, detail="El pedido ya estaba cancelado")
        permitido = (propio and fila["estado"] in CANCELABLE_POR_CLIENTE) or (
            usuario.es_admin and "cancelado" in TRANSICIONES_ADMIN.get(fila["estado"], set()))
        if not permitido:
            if propio and not usuario.es_admin:
                raise HTTPException(status_code=409, detail="Este pedido ya fue pagado: no se puede cancelar desde la web. Escr\u00edbenos para gestionarlo.")
            raise HTTPException(status_code=409, detail=f"Un pedido {fila['estado']} no se puede cancelar")
        _cambiar(con, fila, "cancelado", usuario.user_id, "cancelado por el cliente" if propio else "cancelado por admin")
    # El stock vuelve al catalogo.
    liberado = _liberar_stock(pedido_id, request.state.request_id)
    with db.conexion() as con:
        fila = con.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        return {"order": _pedido(con, fila, con_eventos=True), "stock_liberado": liberado}


@app.get("/admin/orders")
def todos(
    estado: str | None = Query(None, max_length=20),
    pagina: int = Query(1, ge=1),
    tamano: int = Query(20, ge=1, le=50),
    _: Llamador = Depends(seg.requiere("gateway", "graphql", admin=True)),
):
    where, args = [VISIBLES], []
    if estado:
        where.append("estado = ?")
        args.append(estado)
    w = " AND ".join(where)
    with db.conexion() as con:
        total = con.execute(f"SELECT COUNT(*) FROM pedidos WHERE {w}", args).fetchone()[0]
        filas = con.execute(f"SELECT * FROM pedidos WHERE {w} ORDER BY id DESC LIMIT ? OFFSET ?",
                            args + [tamano, (pagina - 1) * tamano]).fetchall()
        return {"orders": [_pedido(con, f) for f in filas], "total": total, "pagina": pagina}


@app.patch("/admin/orders/{pedido_id}/estado")
def avanzar(pedido_id: int, datos: CambioEstado, request: Request,
            llamador: Llamador = Depends(seg.requiere("gateway", admin=True))):
    """PATCH: cambio parcial, solo el estado. 'pagado' no se puede fijar aqui."""
    with db.transaccion() as con:
        fila = _propio_o_404(con, pedido_id, llamador.usuario)
        siguientes = TRANSICIONES_ADMIN.get(fila["estado"], set())
        if datos.estado not in siguientes:
            raise HTTPException(status_code=409, detail=f"No se puede pasar de {fila['estado']} a {datos.estado}")
        if datos.estado == "listo_retiro" and fila["entrega"] != "retiro":
            raise HTTPException(status_code=409, detail="El pedido es con delivery: usa 'despachado'")
        if datos.estado == "despachado" and fila["entrega"] != "delivery":
            raise HTTPException(status_code=409, detail="El pedido es para retiro: usa 'listo_retiro'")
        _cambiar(con, fila, datos.estado, llamador.usuario.user_id, datos.motivo.strip())
    if datos.estado == "cancelado":
        _liberar_stock(pedido_id, request.state.request_id)
    with db.conexion() as con:
        fila = con.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        return {"order": _pedido(con, fila, con_eventos=True)}


# --- interno (payments)

@app.get("/internal/orders/{pedido_id}")
def para_pago(pedido_id: int, _: Llamador = Depends(seg.requiere("payments"))):
    with db.conexion() as con:
        fila = con.execute(f"SELECT * FROM pedidos WHERE id = ? AND {VISIBLES}", (pedido_id,)).fetchone()
    if not fila:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"id": fila["id"], "user_id": fila["user_id"], "estado": fila["estado"],
            "total": fila["total"], "metodo_pago": fila["metodo_pago"], "pago_id": fila["pago_id"]}


@app.post("/internal/orders/{pedido_id}/paid")
def marcar_pagado(pedido_id: int, datos: Pagado, request: Request,
                  _: Llamador = Depends(seg.requiere("payments"))):
    """Idempotente: repetir con el mismo pago no cambia nada."""
    with db.transaccion() as con:
        fila = con.execute(f"SELECT * FROM pedidos WHERE id = ? AND {VISIBLES}", (pedido_id,)).fetchone()
        if not fila:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        if fila["estado"] != "pendiente_pago":
            if fila["pago_id"] == datos.pago_id:
                return {"id": pedido_id, "estado": fila["estado"], "repetido": True}
            raise HTTPException(status_code=409, detail=f"El pedido est\u00e1 {fila['estado']}")
        con.execute("UPDATE pedidos SET pago_id = ? WHERE id = ?", (datos.pago_id, pedido_id))
        _cambiar(con, fila, "pagado", "payments", f"pago {datos.pago_id}")
    try:
        _inventory("POST", f"/internal/reservations/{pedido_id}/confirm", request.state.request_id)
    except httpx.HTTPError:
        log.warning("rid=%s no se confirmo la reserva pedido=%s", request.state.request_id, pedido_id)
    return {"id": pedido_id, "estado": "pagado", "repetido": False}
