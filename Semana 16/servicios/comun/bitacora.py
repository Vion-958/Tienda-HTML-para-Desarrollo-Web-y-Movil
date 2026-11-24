"""Log de cada servicio con el X-Request-ID de la solicitud en curso."""

import logging
from contextvars import ContextVar

RID: ContextVar[str] = ContextVar("rid", default="-")
_actual: logging.Logger | None = None


def logger(servicio: str) -> logging.Logger:
    global _actual
    log = logging.getLogger(servicio)
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(f"%(asctime)s {servicio} %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
        log.propagate = False
    _actual = log
    return log


def evento(msg: str, *args, nivel: int = logging.INFO):
    """Linea de log con el rid actual, para seguir una solicitud entre contenedores."""
    (_actual or logger("chocomania")).log(nivel, "rid=%s " + msg, RID.get(), *args)
