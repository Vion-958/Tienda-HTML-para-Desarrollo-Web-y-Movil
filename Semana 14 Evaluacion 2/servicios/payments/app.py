"""payments: inicio de pagos y verificacion del aviso del proveedor."""

import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from comun.db import BaseDatos  # noqa: E402
from comun.registro import configurar  # noqa: E402
from comun.seguridad import Llamador, VerificadorServicio, cabeceras_servicio, credenciales_desde_entorno  # noqa: E402

AQUI = Path(__file__).resolve().parent
app = FastAPI(title="ChocoMania payments")
log = configurar(app, "payments")
db = BaseDatos(os.getenv("PAYMENTS_DB", str(AQUI / "data" / "payments.db")), AQUI / "schema.sql", AQUI / "seed.sql")
seg = VerificadorServicio(credenciales_desde_entorno())


def _migrar():
    """Bases creadas antes del estado 'anulado'."""
    with db.conexion() as con:
        sql = con.execute("SELECT sql FROM sqlite_master WHERE name = 'pagos'").fetchone()[0]
        if "'anulado'" in sql:
            return
        con.executescript(
            "BEGIN; ALTER TABLE pagos RENAME TO pagos_v1; DROP INDEX IF EXISTS uq_pago_vivo;"
            + (AQUI / "schema.sql").read_text(encoding="utf-8").split("-- Cada aviso")[0]
            + "INSERT INTO pagos SELECT * FROM pagos_v1; DROP TABLE pagos_v1; COMMIT;")


_migrar()

ORDERS_URL = os.getenv("ORDERS_URL", "http://127.0.0.1:9102")
TOKEN_ORDERS = os.getenv("PAYMENTS_ORDERS_TOKEN", "")
PASARELA_URL = os.getenv("PASARELA_URL", "http://127.0.0.1:9300")
PASARELA_API_KEY = os.getenv("PASARELA_API_KEY", "")
PASARELA_WEBHOOK_SECRET = os.getenv("PASARELA_WEBHOOK_SECRET", "")
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://127.0.0.1:8000")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", f"{PUBLIC_URL}/api/payments/webhook")
TIMEOUT = float(os.getenv("UPSTREAM_TIMEOUT", "4"))
TOLERANCIA_FIRMA = 300  # segundos
HTTP = httpx.Client(timeout=TIMEOUT, limits=httpx.Limits(max_connections=50, max_keepalive_connections=20))

if not (PASARELA_API_KEY and PASARELA_WEBHOOK_SECRET):
    raise RuntimeError("Faltan las credenciales de la pasarela")

# Datos ficticios para transferencias (entorno de prueba).
CUENTA_TRANSFERENCIA = {
    "banco": "Banco de Prueba",
    "tipo": "Cuenta corriente",
    "numero": "00-000-00000-0",
    "rut": "76.000.000-0",
    "titular": "ChocoMania SpA (ficticio)",
}


class NuevoPago(BaseModel):
    pedido_id: int = Field(ge=1)


def _orders(metodo: str, ruta: str, rid: str, **kw) -> httpx.Response:
    return HTTP.request(metodo, f"{ORDERS_URL}{ruta}", headers=cabeceras_servicio("payments", TOKEN_ORDERS, rid), **kw)


def _pedido_cancelado(pedido_id: int, rid: str) -> bool:
    """Consulta orders; si no responde se asume que no esta cancelado."""
    try:
        r = _orders("GET", f"/internal/orders/{pedido_id}", rid)
    except httpx.HTTPError:
        return False
    return r.status_code == 200 and r.json()["estado"] == "cancelado"


def _anular(pago_id: str):
    with db.transaccion() as con:
        con.execute("UPDATE pagos SET estado = 'anulado', actualizado = datetime('now') WHERE id = ? AND estado != 'anulado'",
                    (pago_id,))


def _publico(fila) -> dict:
    return {
        "id": fila["id"],
        "pedido_id": fila["pedido_id"],
        "monto": fila["monto"],
        "metodo": fila["metodo"],
        "estado": fila["estado"],
        "creado": fila["creado"],
        "actualizado": fila["actualizado"],
    }


def _avisar_orders(pago_id: str, pedido_id: int, rid: str) -> bool:
    """Marca el pedido como pagado en orders. Idempotente en ambos lados."""
    try:
        r = _orders("POST", f"/internal/orders/{pedido_id}/paid", rid, json={"pago_id": pago_id})
    except httpx.HTTPError:
        log.warning("rid=%s orders no responde, pago=%s queda por sincronizar", rid, pago_id)
        return False
    if r.status_code != 200:
        log.warning("rid=%s orders respondio %s para pago=%s", rid, r.status_code, pago_id)
        return False
    with db.transaccion() as con:
        con.execute("UPDATE pagos SET sincronizado = 1 WHERE id = ?", (pago_id,))
    return True


@app.get("/health")
def health():
    with db.conexion() as con:
        con.execute("SELECT 1")
    return {"status": "OK", "service": "payments"}


@app.post("/payments", status_code=201)
def iniciar(datos: NuevoPago, request: Request,
            llamador: Llamador = Depends(seg.requiere("gateway", con_usuario=True))):
    rid = request.state.request_id
    usuario = llamador.usuario
    try:
        r = _orders("GET", f"/internal/orders/{datos.pedido_id}", rid)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos consultar el pedido. Intenta de nuevo.")
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if r.status_code != 200:
        raise HTTPException(status_code=503, detail="No pudimos consultar el pedido. Intenta de nuevo.")
    pedido = r.json()
    if pedido["user_id"] != usuario.user_id:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido["estado"] != "pendiente_pago":
        raise HTTPException(status_code=409, detail="Este pedido no est\u00e1 pendiente de pago")

    # Idempotencia: si ya hay un pago vivo para el pedido, se reutiliza.
    with db.conexion() as con:
        vivo = con.execute("SELECT * FROM pagos WHERE pedido_id = ? AND estado IN ('pendiente', 'aprobado')",
                           (datos.pedido_id,)).fetchone()
    if vivo:
        return _respuesta(vivo)

    pago_id = "PAY-" + secrets.token_hex(6).upper()
    with db.transaccion() as con:
        con.execute("INSERT INTO pagos (id, pedido_id, user_id, monto, metodo, estado) VALUES (?, ?, ?, ?, ?, 'pendiente')",
                    (pago_id, pedido["id"], usuario.user_id, pedido["total"], pedido["metodo_pago"]))

    if pedido["metodo_pago"] == "tarjeta":
        try:
            with httpx.Client(timeout=TIMEOUT) as c:
                rp = c.post(
                    f"{PASARELA_URL}/v1/checkouts",
                    headers={"Authorization": f"Bearer {PASARELA_API_KEY}"},
                    json={
                        "monto": pedido["total"],
                        "moneda": "CLP",
                        "referencia": pago_id,
                        "url_retorno": f"{PUBLIC_URL}/cuenta.php?pedido={pedido['id']}",
                        "url_aviso": WEBHOOK_URL,
                    },
                )
            rp.raise_for_status()
            checkout = rp.json()
        except httpx.HTTPError:
            with db.transaccion() as con:
                con.execute("DELETE FROM pagos WHERE id = ?", (pago_id,))
            log.warning("rid=%s pasarela no disponible pedido=%s", rid, pedido["id"])
            raise HTTPException(status_code=503, detail="La pasarela de pago no responde. Intenta de nuevo.")
        with db.transaccion() as con:
            con.execute("UPDATE pagos SET checkout_id = ?, checkout_url = ? WHERE id = ?",
                        (checkout["checkout_id"], checkout["url"], pago_id))

    log.info("rid=%s pago iniciado id=%s pedido=%s metodo=%s", rid, pago_id, pedido["id"], pedido["metodo_pago"])
    with db.conexion() as con:
        return _respuesta(con.execute("SELECT * FROM pagos WHERE id = ?", (pago_id,)).fetchone())


def _respuesta(fila) -> dict:
    salida = {"payment": _publico(fila)}
    if fila["metodo"] == "tarjeta" and fila["estado"] == "pendiente":
        salida["redirect_url"] = fila["checkout_url"]
    if fila["metodo"] == "transferencia" and fila["estado"] == "pendiente":
        salida["instrucciones"] = dict(CUENTA_TRANSFERENCIA, monto=fila["monto"], referencia=fila["id"])
    return salida


def verificar_firma(cuerpo: bytes, cabecera: str, ahora: float | None = None) -> bool:
    """Cabecera 't=<epoch>,v1=<hmac>'. HMAC-SHA256 sobre '<t>.<cuerpo>'."""
    try:
        partes = dict(p.split("=", 1) for p in cabecera.split(","))
        t = int(partes["t"])
        firma = partes["v1"]
    except (KeyError, ValueError):
        return False
    if abs((ahora or time.time()) - t) > TOLERANCIA_FIRMA:
        return False
    esperado = hmac.new(PASARELA_WEBHOOK_SECRET.encode(), f"{t}.".encode() + cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, firma)


@app.post("/payments/webhook")
async def aviso(request: Request, x_pasarela_firma: str = Header(default=""),
                _: Llamador = Depends(seg.requiere("gateway"))):
    """Aviso del proveedor: la confianza viene de la firma HMAC."""
    rid = request.state.request_id
    cuerpo = await request.body()
    if len(cuerpo) > 4096 or not verificar_firma(cuerpo, x_pasarela_firma):
        log.warning("rid=%s aviso con firma invalida", rid)
        raise HTTPException(status_code=401, detail="Firma inv\u00e1lida")
    try:
        evento = json.loads(cuerpo)
        evento_id, referencia = str(evento["evento_id"]), str(evento["referencia"])
        estado, monto, checkout_id = str(evento["estado"]), int(evento["monto"]), str(evento["checkout_id"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=400, detail="Aviso mal formado")
    if estado not in ("aprobado", "rechazado"):
        raise HTTPException(status_code=400, detail="Estado desconocido")

    with db.transaccion() as con:
        pago = con.execute("SELECT * FROM pagos WHERE id = ? AND checkout_id = ?", (referencia, checkout_id)).fetchone()
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        if con.execute("SELECT 1 FROM avisos_proveedor WHERE evento_id = ?", (evento_id,)).fetchone():
            duplicado = True
        else:
            duplicado = False
            if monto != pago["monto"]:
                log.warning("rid=%s monto no coincide pago=%s esperado=%s recibido=%s", rid, pago["id"], pago["monto"], monto)
                raise HTTPException(status_code=400, detail="El monto no coincide con el pago")
            con.execute("INSERT INTO avisos_proveedor (evento_id, pago_id, estado) VALUES (?, ?, ?)",
                        (evento_id, pago["id"], estado))
            if pago["estado"] == "pendiente":
                con.execute("UPDATE pagos SET estado = ?, actualizado = datetime('now') WHERE id = ?", (estado, pago["id"]))
        pago = con.execute("SELECT * FROM pagos WHERE id = ?", (referencia,)).fetchone()

    if pago["estado"] == "aprobado" and not pago["sincronizado"] and _pedido_cancelado(pago["pedido_id"], rid):
        # Cobro sobre un pedido ya cancelado: se anula y queda para reembolso.
        _anular(pago["id"])
        log.warning("rid=%s pago=%s aprobado sobre pedido cancelado=%s: anulado, requiere reembolso",
                    rid, pago["id"], pago["pedido_id"])
        return {"recibido": True, "duplicado": duplicado, "estado": "anulado"}

    sincronizado = bool(pago["sincronizado"])
    if pago["estado"] == "aprobado" and not sincronizado:
        sincronizado = _avisar_orders(pago["id"], pago["pedido_id"], rid)
        if not sincronizado:
            # 503: el proveedor reintenta sin duplicar.
            raise HTTPException(status_code=503, detail="Pedido no actualizado, reintentar")
    log.info("rid=%s aviso evento=%s pago=%s estado=%s duplicado=%s", rid, evento_id, pago["id"], pago["estado"], duplicado)
    return {"recibido": True, "duplicado": duplicado, "estado": pago["estado"]}


@app.post("/admin/payments/{pago_id}/confirmar")
def confirmar_transferencia(pago_id: str, request: Request,
                            llamador: Llamador = Depends(seg.requiere("gateway", admin=True))):
    with db.transaccion() as con:
        pago = con.execute("SELECT * FROM pagos WHERE id = ?", (pago_id,)).fetchone()
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        if pago["metodo"] != "transferencia":
            raise HTTPException(status_code=409, detail="Solo las transferencias se confirman a mano")
    if pago["estado"] == "pendiente" and _pedido_cancelado(pago["pedido_id"], request.state.request_id):
        _anular(pago_id)
        raise HTTPException(status_code=409, detail="El pedido fue cancelado: el pago se anul\u00f3 y no se puede confirmar")
    with db.transaccion() as con:
        pago = con.execute("SELECT * FROM pagos WHERE id = ?", (pago_id,)).fetchone()
        if pago["estado"] == "pendiente":
            con.execute("UPDATE pagos SET estado = 'aprobado', actualizado = datetime('now') WHERE id = ?", (pago_id,))
        elif pago["estado"] != "aprobado":
            raise HTTPException(status_code=409, detail=f"El pago est\u00e1 {pago['estado']}")
    if not _avisar_orders(pago_id, pago["pedido_id"], request.state.request_id):
        if _pedido_cancelado(pago["pedido_id"], request.state.request_id):
            _anular(pago_id)
            raise HTTPException(status_code=409, detail="El pedido fue cancelado: el pago se anul\u00f3 y no se puede confirmar")
        raise HTTPException(status_code=503, detail="Pago aprobado, pero el pedido no se pudo actualizar. Reintenta.")
    log.info("transferencia confirmada pago=%s por=%s", pago_id, llamador.usuario.user_id)
    with db.conexion() as con:
        return {"payment": _publico(con.execute("SELECT * FROM pagos WHERE id = ?", (pago_id,)).fetchone())}


@app.get("/internal/payments")
def por_pedidos(pedidos: str = Query(..., max_length=1000),
                llamador: Llamador = Depends(seg.requiere("graphql", con_usuario=True))):
    """Ultimo pago de cada pedido, para GraphQL. Un usuario solo ve los suyos."""
    ids = [int(p) for p in pedidos.split(",") if p.strip().isdigit()][:100]
    if not ids:
        return {"payments": []}
    sql = (f"SELECT * FROM pagos WHERE pedido_id IN ({','.join('?' * len(ids))})"
           + ("" if llamador.usuario.es_admin else " AND user_id = ?") + " ORDER BY creado")
    args = ids + ([] if llamador.usuario.es_admin else [llamador.usuario.user_id])
    with db.conexion() as con:
        ultimo = {f["pedido_id"]: f for f in con.execute(sql, args)}
    return {"payments": [_publico(f) for f in ultimo.values()]}
