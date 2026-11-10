"""Auth Service: login, registro, introspeccion y logout. Solo lo llama el Gateway."""

import hashlib
import os
import re
import secrets
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Depends, FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from comun.db import BaseDatos  # noqa: E402
from comun.registro import configurar  # noqa: E402
from comun.seguridad import VerificadorServicio, credenciales_desde_entorno  # noqa: E402

AQUI = Path(__file__).resolve().parent
app = FastAPI(title="ChocoMania Auth Service")
log = configurar(app, "auth")
db = BaseDatos(os.getenv("AUTH_DB", str(AQUI / "data" / "identity.db")), AQUI / "schema.sql", AQUI / "seed.sql")
solo_gateway = VerificadorServicio(credenciales_desde_entorno()).requiere("gateway")

TTL = int(os.getenv("SESSION_TTL_SECONDS", "1800"))
ITERACIONES = 200_000
USUARIO_VALIDO = re.compile(r"^[a-z0-9._-]{3,30}$")
_SAL_FALSA = secrets.token_hex(16)


def _hash(clave: str, sal: str, iteraciones: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), iteraciones).hex()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _identidad(fila, expira: float) -> dict:
    return {
        "active": True,
        "user_id": fila["user_id"],
        "username": fila["username"],
        "roles": fila["roles"].split(","),
        "expires_in": int(expira - time.time()),
    }


class Credenciales(BaseModel):
    username: str = Field(min_length=1, max_length=60)
    password: str = Field(min_length=1, max_length=128)


class Registro(BaseModel):
    username: str = Field(max_length=30)
    password: str = Field(max_length=72)


class Token(BaseModel):
    token: str = Field(min_length=10, max_length=200)


@app.get("/health")
def health():
    with db.conexion() as con:
        con.execute("SELECT 1")
    return {"status": "OK", "service": "auth"}


@app.post("/login", dependencies=[Depends(solo_gateway)])
def login(datos: Credenciales):
    with db.conexion() as con:
        fila = con.execute("SELECT * FROM usuarios WHERE username = ?", (datos.username.strip().lower(),)).fetchone()
    # Mismo costo si el usuario no existe.
    sal, it = (fila["sal"], fila["iteraciones"]) if fila else (_SAL_FALSA, ITERACIONES)
    calculado = _hash(datos.password, sal, it)
    if not fila or not secrets.compare_digest(calculado, fila["hash"]):
        raise HTTPException(status_code=401, detail="Credenciales inv\u00e1lidas")

    token = secrets.token_urlsafe(32)
    expira = time.time() + TTL
    with db.transaccion() as con:
        con.execute("DELETE FROM sesiones WHERE expira <= ?", (time.time(),))
        con.execute("INSERT INTO sesiones (token_hash, user_id, expira) VALUES (?, ?, ?)",
                    (_hash_token(token), fila["user_id"], expira))
    return {"access_token": token, "token_type": "bearer", "expires_in": TTL, **_identidad(fila, expira)}


@app.post("/register", status_code=201, dependencies=[Depends(solo_gateway)])
def registrar(datos: Registro):
    usuario = datos.username.strip().lower()
    errores = {}
    if not USUARIO_VALIDO.match(usuario):
        errores["username"] = "Usa de 3 a 30 caracteres: letras min\u00fasculas, n\u00fameros, punto, gui\u00f3n."
    if len(datos.password) < 8 or not re.search(r"[A-Za-z]", datos.password) or not re.search(r"\d", datos.password):
        errores["password"] = "La contrase\u00f1a debe tener al menos 8 caracteres, con letras y n\u00fameros."
    if errores:
        raise HTTPException(status_code=400, detail={"mensaje": "Revisa los campos marcados.", "errores": errores})

    sal = secrets.token_hex(16)
    uid = "USR-" + secrets.token_hex(3).upper()
    with db.transaccion() as con:
        if con.execute("SELECT 1 FROM usuarios WHERE username = ?", (usuario,)).fetchone():
            raise HTTPException(status_code=409, detail={"mensaje": "Ese usuario ya existe.",
                                                         "errores": {"username": "Ese usuario ya existe."}})
        con.execute("INSERT INTO usuarios (user_id, username, sal, hash, iteraciones, roles) VALUES (?, ?, ?, ?, ?, 'user')",
                    (uid, usuario, sal, _hash(datos.password, sal, ITERACIONES), ITERACIONES))
    log.info("usuario registrado user=%s", uid)
    return {"user_id": uid, "username": usuario, "roles": ["user"]}


@app.post("/introspect", dependencies=[Depends(solo_gateway)])
def introspect(datos: Token):
    with db.conexion() as con:
        fila = con.execute(
            "SELECT u.*, s.expira FROM sesiones s JOIN usuarios u ON u.user_id = s.user_id"
            " WHERE s.token_hash = ? AND s.expira > ?",
            (_hash_token(datos.token), time.time()),
        ).fetchone()
    return _identidad(fila, fila["expira"]) if fila else {"active": False}


@app.post("/logout", dependencies=[Depends(solo_gateway)])
def logout(datos: Token):
    with db.transaccion() as con:
        n = con.execute("DELETE FROM sesiones WHERE token_hash = ?", (_hash_token(datos.token),)).rowcount
    return {"revoked": n > 0}
