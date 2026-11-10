"""Logs con X-Request-ID, sin cabeceras ni cuerpos."""

import logging
import re
import time
import uuid

from fastapi import FastAPI, Request

_ID_VALIDO = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def configurar(app: FastAPI, servicio: str, middleware: bool = True) -> logging.Logger:
    log = logging.getLogger(servicio)
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(f"%(asctime)s {servicio} %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
        log.propagate = False
    if not middleware:
        return log

    @app.middleware("http")
    async def correlacion(request: Request, call_next):
        rid = request.headers.get("x-request-id", "")
        if not _ID_VALIDO.match(rid):
            rid = uuid.uuid4().hex
        request.state.request_id = rid
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
