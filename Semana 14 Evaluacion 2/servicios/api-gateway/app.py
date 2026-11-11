"""API Gateway: unico punto de entrada publico."""

import os
import re
import sys
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402
from fastapi import FastAPI, HTTPException, Request, Response  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from comun.registro import configurar  # noqa: E402
from comun.seguridad import Usuario, cabeceras_servicio  # noqa: E402

# Pool de conexiones compartido.
HTTP = httpx.AsyncClient(limits=httpx.Limits(max_connections=200, max_keepalive_connections=50))


@asynccontextmanager
async def ciclo(_app):
    yield
    await HTTP.aclose()


app = FastAPI(title="ChocoMania API Gateway", docs_url=None, redoc_url=None, openapi_url=None, lifespan=ciclo)
log = configurar(app, "gateway", middleware=False)

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8080")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE = "session_token"
MAX_CUERPO = 12 * 1024 * 1024
# Solo para la prueba de carga.
FACTOR_LIMITE = max(1, int(os.getenv("GATEWAY_LIMITE_FACTOR", "1")))

SERVICIOS = {
    "auth": os.getenv("AUTH_URL", "http://127.0.0.1:8100"),
    "inventory": os.getenv("INVENTORY_URL", "http://127.0.0.1:9101"),
    "orders": os.getenv("ORDERS_URL", "http://127.0.0.1:9102"),
    "clients": os.getenv("CLIENTS_URL", "http://127.0.0.1:9103"),
    "payments": os.getenv("PAYMENTS_URL", "http://127.0.0.1:9104"),
    "graphql": os.getenv("GRAPHQL_URL", "http://127.0.0.1:9200"),
}

if not VAULT_TOKEN:
    raise RuntimeError("VAULT_TOKEN no configurado")




@dataclass(frozen=True)
class Ruta:
    id: str
    metodo: str
    patron: re.Pattern
    servicio: str
    destino: str          # ruta interna; {0}, {1} son los grupos del patron
    acceso: str           # anonimo | opcional | sesion | admin
    limite: int = 120     # solicitudes por minuto y por IP
    timeout: float = 5.0


def R(id_, metodo, patron, servicio, destino, acceso, **kw) -> Ruta:
    return Ruta(id_, metodo, re.compile(f"^{patron}$"), servicio, destino, acceso, **kw)


ID = r"([A-Za-z0-9_-]{1,40})"
NUM = r"([0-9]{1,9})"

# Rutas publicadas. Lo demas responde 404.
RUTAS = [
    R("S01", "GET", "products", "inventory", "/products", "anonimo"),
    R("S02", "GET", f"products/{ID}", "inventory", "/products/{0}", "anonimo"),
    R("S03", "GET", f"images/{ID}", "inventory", "/images/{0}", "anonimo", limite=600),
    R("S04", "POST", "products", "inventory", "/products", "admin", limite=30, timeout=15),
    R("S05", "PUT", f"products/{ID}", "inventory", "/products/{0}", "admin", limite=30, timeout=15),
    R("S06", "DELETE", f"products/{ID}", "inventory", "/products/{0}", "admin", limite=30),
    R("S07", "POST", "orders", "orders", "/orders", "sesion", limite=20, timeout=8),
    R("S08", "GET", "orders", "orders", "/orders", "sesion"),
    R("S09", "GET", f"orders/{NUM}", "orders", "/orders/{0}", "sesion"),
    R("S10", "POST", f"orders/{NUM}/cancel", "orders", "/orders/{0}/cancel", "sesion", limite=20, timeout=8),
    R("S11", "GET", "admin/orders", "orders", "/admin/orders", "admin"),
    R("S12", "PATCH", f"admin/orders/{NUM}/estado", "orders", "/admin/orders/{0}/estado", "admin", limite=60, timeout=8),
    R("S13", "GET", "clients/me", "clients", "/clients/me", "sesion"),
    R("S14", "PUT", "clients/me", "clients", "/clients/me", "sesion", limite=20),
    R("S15", "GET", "admin/clients", "clients", "/admin/clients", "admin"),
    R("S16", "POST", "payments", "payments", "/payments", "sesion", limite=20, timeout=8),
    R("S17", "POST", "payments/webhook", "payments", "/payments/webhook", "anonimo", limite=60, timeout=10),
    R("S18", "POST", f"admin/payments/{ID}/confirmar", "payments", "/admin/payments/{0}/confirmar", "admin", limite=30, timeout=8),
    R("S19", "POST", "graphql", "graphql", "/graphql", "sesion", limite=60, timeout=8),
    R("S20", "POST", "solicitudes", "clients", "/solicitudes", "opcional", limite=5),
    R("S21", "GET", "admin/solicitudes", "clients", "/admin/solicitudes", "admin"),
    R("S22", "PATCH", f"admin/solicitudes/{NUM}", "clients", "/admin/solicitudes/{0}", "admin", limite=60),
]

# Login: solo cuentan los intentos fallidos.
LIMITE_LOGIN_USUARIO, LIMITE_LOGIN_IP, LIMITE_REGISTRO = 10, 50, 5


# --- limite de solicitudes

class Limitador:
    """Ventana deslizante de 60 s por (IP, ruta). En memoria: una sola instancia."""

    def __init__(self):
        self.marcas: dict[tuple, deque] = defaultdict(deque)

    def _cola(self, ip: str, clave: str) -> deque:
        cola = self.marcas[(ip, clave)]
        ahora = time.monotonic()
        while cola and ahora - cola[0] > 60:
            cola.popleft()
        return cola

    def excedido(self, ip: str, clave: str, por_minuto: int) -> bool:
        return len(self._cola(ip, clave)) >= por_minuto

    def registrar(self, ip: str, clave: str):
        self._cola(ip, clave).append(time.monotonic())

    def permitir(self, ip: str, clave: str, por_minuto: int) -> bool:
        if self.excedido(ip, clave, por_minuto):
            return False
        self.registrar(ip, clave)
        return True


limitador = Limitador()


def _ip(request: Request) -> str:
    return request.client.host if request.client else "?"


def _limitar(request: Request, clave: str, por_minuto: int):
    if not limitador.permitir(_ip(request), clave, por_minuto * FACTOR_LIMITE):
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Espera un momento.")


# --- secretos (Vault)

class Secretos:
    """Credenciales desde Vault, con cache de 30 s y 5 min de gracia si Vault cae."""

    TTL, GRACIA = 30, 300

    def __init__(self):
        self.datos, self.leido = None, 0.0

    async def obtener(self) -> dict:
        ahora = time.monotonic()
        if self.datos and ahora - self.leido < self.TTL:
            return self.datos
        try:
            r = await HTTP.get(f"{VAULT_ADDR}/v1/secret/data/gateway", headers={"X-Vault-Token": VAULT_TOKEN}, timeout=3)
            r.raise_for_status()
            self.datos, self.leido = r.json()["data"]["data"], ahora
        except (httpx.HTTPError, KeyError, ValueError):
            if self.datos and ahora - self.leido < self.GRACIA:
                log.warning("vault no responde, se usa la cache")
                return self.datos
            raise HTTPException(status_code=503, detail="Servicio de secretos no disponible")
        return self.datos


secretos = Secretos()


async def _llamar(servicio: str, metodo: str, ruta: str, rid: str, usuario: Usuario | None = None,
                  timeout: float = 5.0, **kw) -> httpx.Response:
    sec = await secretos.obtener()
    cab = cabeceras_servicio("gateway", sec[servicio], rid, usuario)
    cab.update(kw.pop("extra", {}))
    try:
        return await HTTP.request(metodo, f"{SERVICIOS[servicio]}{ruta}", headers=cab, timeout=timeout, **kw)
    except httpx.TimeoutException:
        log.warning("rid=%s timeout %s %s", rid, servicio, ruta)
        raise HTTPException(status_code=504, detail=f"El servicio {servicio} tard\u00f3 demasiado")
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail=f"El servicio {servicio} no est\u00e1 disponible")


async def _identidad(request: Request) -> Usuario | None:
    token = request.cookies.get(COOKIE)
    if not token or len(token) > 200:
        return None
    r = await _llamar("auth", "POST", "/introspect", request.state.request_id, json={"token": token})
    if r.status_code != 200:
        log.error("rid=%s introspect respondio %s", request.state.request_id, r.status_code)
        raise HTTPException(status_code=503, detail="Servicio de autenticaci\u00f3n no disponible")
    d = r.json()
    return Usuario(d["user_id"], d["username"], d["roles"]) if d.get("active") else None


def _publico(u: Usuario, expira: int | None = None) -> dict:
    return {"user_id": u.user_id, "username": u.username, "roles": u.roles, "expires_in": expira}


# --- middleware

@app.middleware("http")
async def cabeceras_seguridad(request: Request, call_next):
    # El X-Request-ID lo genera el Gateway.
    request.state.request_id = uuid.uuid4().hex
    largo = request.headers.get("content-length")
    if largo and largo.isdigit() and int(largo) > MAX_CUERPO:
        return JSONResponse({"detail": "La solicitud es demasiado grande"}, status_code=413)
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "same-origin"
    respuesta.headers["X-Request-ID"] = request.state.request_id
    return respuesta


@app.exception_handler(HTTPException)
async def errores(request: Request, exc: HTTPException):
    rid = getattr(request.state, "request_id", "")
    return JSONResponse({"detail": exc.detail, "request_id": rid}, status_code=exc.status_code)


# --- sesion

class Login(BaseModel):
    username: str = Field(min_length=1, max_length=60)
    password: str = Field(min_length=1, max_length=128)


@app.get("/health")
def health():
    return {"status": "OK", "service": "gateway"}


def _poner_cookie(response: Response, token: str, segundos: int):
    response.set_cookie(COOKIE, token, httponly=True, samesite="lax", secure=COOKIE_SECURE,
                        max_age=segundos, path="/")


@app.post("/auth/login")
async def login(datos: Login, request: Request, response: Response):
    ip, clave_usuario = _ip(request), "login:" + datos.username.strip().lower()[:60]
    if (limitador.excedido(ip, clave_usuario, LIMITE_LOGIN_USUARIO * FACTOR_LIMITE)
            or limitador.excedido(ip, "login", LIMITE_LOGIN_IP * FACTOR_LIMITE)):
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espera un minuto.")
    r = await _llamar("auth", "POST", "/login", request.state.request_id, json=datos.model_dump())
    if r.status_code == 401:
        limitador.registrar(ip, clave_usuario)
        limitador.registrar(ip, "login")
        log.info("rid=%s login fallido", request.state.request_id)
        raise HTTPException(status_code=401, detail="Usuario o contrase\u00f1a incorrectos")
    if r.status_code != 200:
        raise HTTPException(status_code=503, detail="Servicio de autenticaci\u00f3n no disponible")
    s = r.json()
    _poner_cookie(response, s["access_token"], s["expires_in"])
    log.info("rid=%s login ok user=%s", request.state.request_id, s["user_id"])
    return _publico(Usuario(s["user_id"], s["username"], s["roles"]), s["expires_in"])


@app.post("/auth/register", status_code=201)
async def registrar(datos: Login, request: Request, response: Response):
    _limitar(request, "register", LIMITE_REGISTRO)
    rid = request.state.request_id
    r = await _llamar("auth", "POST", "/register", rid, json=datos.model_dump())
    if r.status_code in (400, 409):
        raise HTTPException(status_code=r.status_code, detail=r.json().get("detail"))
    if r.status_code != 201:
        raise HTTPException(status_code=503, detail="Servicio de autenticaci\u00f3n no disponible")
    # Registro exitoso: se inicia la sesion de inmediato.
    s = (await _llamar("auth", "POST", "/login", rid, json=datos.model_dump())).json()
    _poner_cookie(response, s["access_token"], s["expires_in"])
    return _publico(Usuario(s["user_id"], s["username"], s["roles"]), s["expires_in"])


@app.get("/auth/me")
async def me(request: Request):
    u = await _identidad(request)
    if not u:
        raise HTTPException(status_code=401, detail="Sesi\u00f3n requerida")
    return _publico(u)


@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE)
    revocado = False
    if token and len(token) <= 200:
        r = await _llamar("auth", "POST", "/logout", request.state.request_id, json={"token": token})
        revocado = r.status_code == 200 and r.json().get("revoked", False)
    response.delete_cookie(COOKIE, path="/", httponly=True, samesite="lax", secure=COOKIE_SECURE)
    return {"logged_out": True, "revoked": revocado}


# --- API

def _buscar_ruta(metodo: str, path: str) -> tuple[Ruta, tuple] | tuple[None, None]:
    for ruta in RUTAS:
        m = ruta.patron.match(path)
        if m and ruta.metodo == metodo:
            return ruta, m.groups()
    return None, None


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def api(path: str, request: Request):
    rid = request.state.request_id
    ruta, grupos = _buscar_ruta(request.method, path.rstrip("/"))
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no publicada")
    _limitar(request, ruta.id, ruta.limite)

    usuario = None
    if ruta.acceso == "opcional":
        # Publico: si hay sesion se adjunta la identidad.
        usuario = await _identidad(request)
    elif ruta.acceso != "anonimo":
        usuario = await _identidad(request)
        if not usuario:
            raise HTTPException(status_code=401, detail="Sesi\u00f3n requerida")
        if ruta.acceso == "admin" and not usuario.es_admin:
            log.info("rid=%s 403 user=%s ruta=%s", rid, usuario.user_id, ruta.id)
            raise HTTPException(status_code=403, detail="Se requiere el rol admin")

    # Solo pasan el content-type y la firma del proveedor.
    extra = {}
    if request.headers.get("content-type"):
        extra["content-type"] = request.headers["content-type"]
    if ruta.id == "S17" and request.headers.get("x-pasarela-firma"):
        extra["X-Pasarela-Firma"] = request.headers["x-pasarela-firma"][:200]

    inicio = time.perf_counter()
    r = await _llamar(ruta.servicio, request.method, ruta.destino.format(*grupos), rid, usuario,
                      timeout=ruta.timeout, params=request.query_params, content=await request.body(), extra=extra)
    log.info("rid=%s user=%s ruta=%s %s /api/%s -> %s %.0fms", rid, usuario.user_id if usuario else "-",
             ruta.id, request.method, path, r.status_code, (time.perf_counter() - inicio) * 1000)

    if r.status_code == 403 and ruta.acceso not in ("admin",):
        # 403 interno = credencial mal configurada.
        log.error("rid=%s %s rechazo la credencial del gateway", rid, ruta.servicio)
        raise HTTPException(status_code=503, detail="Servicio no disponible")
    cab = {k: v for k, v in r.headers.items() if k.lower() in ("content-type", "cache-control")}
    return Response(content=r.content, status_code=r.status_code, headers=cab)


# --- sitio

@app.get("/{path:path}")
async def sitio(path: str, request: Request):
    try:
        r = await HTTP.get(f"{FRONTEND_URL}/{path}", params=request.query_params, timeout=10.0)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Sitio web no disponible")
    cab = {k: v for k, v in r.headers.items() if k.lower() in ("content-type", "cache-control", "last-modified", "etag")}
    return Response(content=r.content, status_code=r.status_code, headers=cab)
