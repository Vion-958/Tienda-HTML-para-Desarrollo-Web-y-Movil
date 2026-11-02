"""
ChocoManía - Auth Service (:8100)

Responsable de la AUTENTICACIÓN ("¿quién eres?") y de las sesiones:

    POST /login       usuario + contraseña -> token opaco temporal   (pública)
    POST /introspect  token -> identidad (o {"active": false})       (solo Gateway)
    POST /logout      revoca el token en el servidor                 (solo Gateway)

No ejecuta lógica de negocio ni decide qué puede hacer cada usuario:
solo informa quién es y qué roles tiene. La autorización la aplica el
Gateway (y el Backend la vuelve a verificar).

/introspect y /logout exigen el header X-Introspection-Secret, que solo
conoce el Gateway (lo lee de Vault). Así nadie desde afuera puede usar
este servicio para averiguar a quién pertenece un token.

Ejecutar:
    export AUTH_INTROSPECTION_SECRET="gateway-auth-secret-789"
    uvicorn auth_service:app --host 0.0.0.0 --port 8100
"""

import hashlib
import os
import secrets
import time

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="ChocoManía Auth Service",
    description="Autenticación, sesiones e introspección de tokens",
)

AUTH_INTROSPECTION_SECRET = os.getenv("AUTH_INTROSPECTION_SECRET")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "900"))

if not AUTH_INTROSPECTION_SECRET:
    raise RuntimeError("AUTH_INTROSPECTION_SECRET no esta configurado")

# ---------------------------------------------------------------------------
# Usuarios simulados. Las contraseñas NO están en texto plano: se guarda un
# hash PBKDF2-SHA256 con sal propia por usuario (200.000 iteraciones).
#   ana     / 1234      -> roles ["user"]
#   ernesto / admin123  -> roles ["user", "admin"]
# En producción se usaría una base de datos y un algoritmo como Argon2.
# ---------------------------------------------------------------------------

PBKDF2_ITERATIONS = 200_000

USERS = {
    "ana": {
        "user_id": "USR-001",
        "salt": "choco-ana-7f3a",
        "password_hash": "dea44eab80745d48c2624a36f59a3904eaffc0742a7749b4e166e33f4949cb43",
        "roles": ["user"],
    },
    "ernesto": {
        "user_id": "USR-003",
        "salt": "choco-ernesto-91c2",
        "password_hash": "743a661d210ceab4cca53b6ea7e2a71173ec4342e36f439fe4bc594d4b25aa96",
        "roles": ["user", "admin"],
    },
}

# Sesiones activas en memoria: token -> identidad + expiración.
SESSIONS: dict[str, dict] = {}


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS
    ).hex()


def verify_password(username: str, password: str) -> dict | None:
    user = USERS.get(username)
    # Si el usuario no existe igual se calcula un hash, para que la respuesta
    # tarde lo mismo y no delate qué nombres de usuario existen.
    salt = user["salt"] if user else "usuario-inexistente"
    calculado = hash_password(password, salt)
    if user and secrets.compare_digest(calculado, user["password_hash"]):
        return user
    return None


def verify_gateway(x_introspection_secret: str = Header(default="")):
    if not secrets.compare_digest(
        x_introspection_secret.encode(), AUTH_INTROSPECTION_SECRET.encode()
    ):
        raise HTTPException(status_code=403, detail="Solo el Gateway puede usar este endpoint")


def active_session(token: str) -> dict | None:
    session = SESSIONS.get(token)
    if session is None:
        return None
    if session["expires_at"] <= time.time():
        SESSIONS.pop(token, None)
        return None
    return session


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenRequest(BaseModel):
    token: str


@app.get("/health")
def health():
    return {"status": "OK", "service": "ChocoManía Auth Service"}


@app.post("/login")
def login(data: LoginRequest):
    user = verify_password(data.username, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    token = secrets.token_urlsafe(32)
    SESSIONS[token] = {
        "user_id": user["user_id"],
        "username": data.username,
        "roles": list(user["roles"]),
        "expires_at": time.time() + SESSION_TTL_SECONDS,
    }
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": SESSION_TTL_SECONDS,
    }


@app.post("/introspect", dependencies=[Depends(verify_gateway)])
def introspect(data: TokenRequest):
    session = active_session(data.token)
    if session is None:
        return {"active": False}
    return {
        "active": True,
        "user_id": session["user_id"],
        "username": session["username"],
        "roles": session["roles"],
        "expires_in": int(session["expires_at"] - time.time()),
    }


@app.post("/logout", dependencies=[Depends(verify_gateway)])
def logout(data: TokenRequest):
    revoked = SESSIONS.pop(data.token, None) is not None
    return {"revoked": revoked}
