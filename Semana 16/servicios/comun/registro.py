"""Logs con X-Request-ID, sin cabeceras ni cuerpos."""

import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from comun.bitacora import RID, evento, logger
from comun.secretos import SinSecretos

_ID_VALIDO = re.compile(r"^[A-Za-z0-9-]{8,64}$")

__all__ = ["configurar", "evento", "RID"]


def configurar(app: FastAPI, servicio: str, middleware: bool = True) -> logging.Logger:
    log = logger(servicio)

    @app.exception_handler(SinSecretos)
    async def sin_secretos(request: Request, error: SinSecretos):
        evento("sin acceso a secretos: %s", error, nivel=logging.ERROR)
        return JSONResponse(status_code=503, content={"detail": "Servicio sin acceso a sus secretos"})

    if not middleware:
        return log

    @app.middleware("http")
    async def correlacion(request: Request, call_next):
        rid = request.headers.get("x-request-id", "")
        if not _ID_VALIDO.match(rid):
            rid = uuid.uuid4().hex
        request.state.request_id = rid
        RID.set(rid)
        inicio = time.perf_counter()
        respuesta = await call_next(request)
        ms = (time.perf_counter() - inicio) * 1000
        respuesta.headers["X-Request-ID"] = rid
        if request.url.path != "/health":
            caller = request.headers.get("x-service-name", "-")
            log.info("rid=%s caller=%s %s %s -> %s %.0fms", rid, caller, request.method,
                     request.url.path, respuesta.status_code, ms)
        return respuesta

    return log
