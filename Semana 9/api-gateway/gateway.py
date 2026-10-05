"""
ChocoManía - API Gateway (:8000)

Frontera de seguridad del sistema. Coordina, pero no ejecuta negocio:

    Navegador --cookie session_token--> Gateway
        1. lee la cookie HttpOnly
        2. consulta Vault (secretos entre servicios)
        3. pregunta al Auth Service si el token sigue activo (introspección)
        4. revisa roles (autorización)
        5. reenvía al Backend con X-Gateway-Secret + identidad confiable

Rutas:
    POST /auth/login    pública: credenciales -> Auth Service -> cookie HttpOnly
    GET  /auth/me       sesión: identidad del usuario actual
    POST /auth/logout   revoca la sesión en el Auth Service y borra la cookie
    /api/{ruta}         sesión válida (+ rol según la política) -> Backend
    /{todo lo demás}    el sitio ChocoManía (proxy al servidor PHP)

Servir el sitio desde el mismo origen (:8000) permite que el navegador
envíe la cookie sin CORS, y que JavaScript nunca vea el token.

Errores:
    401  sin sesión, token inválido, expirado o revocado
    403  autenticado, pero sin el rol requerido
    502  el Backend (o el servidor del sitio) no respondió
    503  Auth Service o Vault no disponibles

Variables de entorno:
    VAULT_ADDR, VAULT_TOKEN   acceso a Vault (obligatoria VAULT_TOKEN)
    AUTH_URL                  Auth Service   (por defecto http://127.0.0.1:8100)
    BACKEND_URL               Backend API    (por defecto http://127.0.0.1:9000)
    FRONTEND_URL              sitio PHP      (por defecto http://127.0.0.1:8080)
    COOKIE_SECURE             "true" cuando el sitio se sirva por HTTPS
"""

import logging
import os
import re

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

app = FastAPI(
    title="ChocoManía API Gateway",
    description="Validación de sesión, autorización y enrutamiento",
)

log = logging.getLogger("gateway")
logging.basicConfig(level=logging.INFO, format="%(asctime)s gateway %(message)s")

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
AUTH_URL = os.getenv("AUTH_URL", "http://127.0.0.1:8100")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:9000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8080")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

COOKIE_NAME = "session_token"

if not VAULT_TOKEN:
    raise RuntimeError("VAULT_TOKEN no configurado")


# ---------------------------------------------------------------------------
# Política de autorización: qué rol exige cada operación.
# Lo que no aparece aquí solo requiere una sesión válida.
# ---------------------------------------------------------------------------

POLICIES = [
    # (método, ruta dentro de /api, rol requerido)
    ("DELETE", re.compile(r"^products/[^/]+$"), "admin"),
]


def required_role(method: str, path: str) -> str | None:
    for policy_method, pattern, role in POLICIES:
        if method == policy_method and pattern.match(path):
            return role
    return None


# ---------------------------------------------------------------------------
# Dependencias externas: Vault y Auth Service
# ---------------------------------------------------------------------------

async def get_vault_secrets() -> dict:
    """Lee secret/gateway: backend_shared_secret y auth_introspection_secret.

    Se lee en cada solicitud para que una rotación en Vault se aplique sin
    reiniciar el Gateway.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{VAULT_ADDR}/v1/secret/data/gateway",
                headers={"X-Vault-Token": VAULT_TOKEN},
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Servicio de secretos no disponible")

    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="Servicio de secretos no disponible")

    return response.json()["data"]["data"]


async def auth_call(path: str, payload: dict, vault_secrets: dict | None = None) -> httpx.Response:
    headers = {}
    if vault_secrets is not None:
        headers["X-Introspection-Secret"] = vault_secrets["auth_introspection_secret"]
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            return await client.post(f"{AUTH_URL}{path}", json=payload, headers=headers)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Servicio de autenticacion no disponible")


async def introspect(token: str, vault_secrets: dict) -> dict | None:
    response = await auth_call("/introspect", {"token": token}, vault_secrets)
    if response.status_code != 200:
        # 403 aquí significa que el secreto Gateway-Auth no coincide:
        # es una falla de configuración, no culpa del usuario.
        log.error("introspect respondio %s", response.status_code)
        raise HTTPException(status_code=503, detail="Servicio de autenticacion no disponible")
    data = response.json()
    return data if data.get("active") else None


async def current_identity(request: Request) -> tuple[dict, dict]:
    """Cookie -> Vault -> introspección. Devuelve (identidad, secretos)."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Sesion requerida")

    vault_secrets = await get_vault_secrets()
    identity = await introspect(token, vault_secrets)
    if identity is None:
        raise HTTPException(status_code=401, detail="Sesion invalida o expirada")

    return identity, vault_secrets


def public_identity(identity: dict) -> dict:
    return {
        "user_id": identity["user_id"],
        "username": identity["username"],
        "roles": identity["roles"],
        "expires_in": identity.get("expires_in"),
    }


# ---------------------------------------------------------------------------
# Rutas de sesión
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health():
    return {"status": "OK", "service": "ChocoManía API Gateway"}


@app.post("/auth/login")
async def login(data: LoginRequest, response: Response):
    auth_response = await auth_call("/login", data.model_dump())

    if auth_response.status_code == 401:
        log.info("login fallido usuario=%s", data.username)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    if auth_response.status_code != 200:
        raise HTTPException(status_code=503, detail="Servicio de autenticacion no disponible")

    session = auth_response.json()
    token = session["access_token"]

    vault_secrets = await get_vault_secrets()
    identity = await introspect(token, vault_secrets)
    if identity is None:
        raise HTTPException(status_code=503, detail="Servicio de autenticacion no disponible")

    # El token viaja solo en esta cookie: JavaScript no puede leerla.
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=session["expires_in"],
        path="/",
    )
    log.info("login ok usuario=%s roles=%s", identity["username"], ",".join(identity["roles"]))
    return public_identity(identity)


@app.get("/auth/me")
async def me(request: Request):
    identity, _ = await current_identity(request)
    return public_identity(identity)


@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE_NAME)
    revoked = False
    if token:
        vault_secrets = await get_vault_secrets()
        auth_response = await auth_call("/logout", {"token": token}, vault_secrets)
        revoked = auth_response.status_code == 200 and auth_response.json().get("revoked", False)

    # Logout = revocación en el servidor + eliminación de la cookie.
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="lax", secure=COOKIE_SECURE)
    log.info("logout revocado=%s", revoked)
    return {"logged_out": True, "revoked": revoked}


# ---------------------------------------------------------------------------
# API de negocio: sesión -> autorización -> Backend
# ---------------------------------------------------------------------------

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def api_proxy(path: str, request: Request):
    identity, vault_secrets = await current_identity(request)

    role = required_role(request.method, path)
    if role and role not in identity["roles"]:
        log.info("403 usuario=%s %s /api/%s requiere=%s",
                 identity["username"], request.method, path, role)
        raise HTTPException(status_code=403, detail=f"Se requiere el rol {role}")

    # Headers nuevos: nada de lo que mande el navegador (cookies, un
    # X-Authenticated-User inventado, etc.) llega al Backend.
    backend_headers = {
        "X-Gateway-Secret": vault_secrets["backend_shared_secret"],
        "X-Authenticated-User": identity["user_id"],
        "X-Authenticated-Username": identity["username"],
        "X-Authenticated-Roles": ",".join(identity["roles"]),
    }
    if request.headers.get("content-type"):
        backend_headers["content-type"] = request.headers["content-type"]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            upstream = await client.request(
                method=request.method,
                url=f"{BACKEND_URL}/{path}",
                params=request.query_params,
                content=await request.body(),
                headers=backend_headers,
            )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Backend no disponible")

    log.info("usuario=%s %s /api/%s -> %s",
             identity["username"], request.method, path, upstream.status_code)

    headers = {}
    if "content-type" in upstream.headers:
        headers["content-type"] = upstream.headers["content-type"]
    return Response(content=upstream.content, status_code=upstream.status_code, headers=headers)


# ---------------------------------------------------------------------------
# Sitio ChocoManía: todo lo demás se sirve desde el servidor PHP.
# Va al final para no tapar las rutas anteriores.
# ---------------------------------------------------------------------------

@app.get("/{path:path}")
async def frontend_proxy(path: str, request: Request):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            upstream = await client.get(f"{FRONTEND_URL}/{path}", params=request.query_params)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Sitio web no disponible")

    headers = {}
    for name in ("content-type", "cache-control", "last-modified", "etag"):
        if name in upstream.headers:
            headers[name] = upstream.headers[name]
    return Response(content=upstream.content, status_code=upstream.status_code, headers=headers)
