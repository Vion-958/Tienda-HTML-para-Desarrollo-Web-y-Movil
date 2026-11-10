"""clients: perfil, datos de contacto y solicitudes."""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import date  # noqa: E402

from fastapi import Depends, FastAPI, HTTPException, Query  # noqa: E402
from pydantic import BaseModel, Field, field_validator  # noqa: E402

from comun.db import BaseDatos  # noqa: E402
from comun.registro import configurar  # noqa: E402
from comun.seguridad import Llamador, VerificadorServicio, credenciales_desde_entorno  # noqa: E402

AQUI = Path(__file__).resolve().parent
app = FastAPI(title="ChocoMania clients")
log = configurar(app, "clients")
db = BaseDatos(os.getenv("CLIENTS_DB", str(AQUI / "data" / "clients.db")), AQUI / "schema.sql", AQUI / "seed.sql")
seg = VerificadorServicio(credenciales_desde_entorno())

EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[A-Za-z]{2,}$")
TELEFONO = re.compile(r"^\+?[0-9 ]{8,15}$")
CAMPOS = ("user_id", "nombre", "email", "telefono", "direccion", "comuna")


class Perfil(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    email: str = Field(max_length=254)
    telefono: str = Field(default="", max_length=20)
    direccion: str = Field(default="", max_length=150)
    comuna: str = Field(default="", max_length=50)

    @field_validator("nombre", "direccion", "comuna", "telefono", "email")
    @classmethod
    def recortar(cls, v: str) -> str:
        return v.strip()

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        if not EMAIL.match(v):
            raise ValueError("Correo no v\u00e1lido")
        return v.lower()

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        if v and not TELEFONO.match(v):
            raise ValueError("Tel\u00e9fono no v\u00e1lido")
        return v


def _perfil(fila) -> dict:
    return {c: fila[c] for c in CAMPOS}


@app.get("/health")
def health():
    with db.conexion() as con:
        con.execute("SELECT 1")
    return {"status": "OK", "service": "clients"}


@app.get("/clients/me")
def mi_perfil(llamador: Llamador = Depends(seg.requiere("gateway", con_usuario=True))):
    with db.conexion() as con:
        fila = con.execute("SELECT * FROM clientes WHERE user_id = ?", (llamador.usuario.user_id,)).fetchone()
    if not fila:
        raise HTTPException(status_code=404, detail="Perfil no registrado")
    return {"client": _perfil(fila)}


@app.put("/clients/me")
def guardar_perfil(datos: Perfil, llamador: Llamador = Depends(seg.requiere("gateway", con_usuario=True))):
    """PUT reemplaza el perfil completo del usuario autenticado (lo crea si no existe)."""
    uid = llamador.usuario.user_id
    with db.transaccion() as con:
        otro = con.execute("SELECT user_id FROM clientes WHERE email = ? AND user_id != ?", (datos.email, uid)).fetchone()
        if otro:
            raise HTTPException(status_code=409, detail="Ese correo ya est\u00e1 registrado")
        con.execute(
            "INSERT INTO clientes (user_id, nombre, email, telefono, direccion, comuna) VALUES (?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(user_id) DO UPDATE SET nombre=excluded.nombre, email=excluded.email,"
            " telefono=excluded.telefono, direccion=excluded.direccion, comuna=excluded.comuna,"
            " actualizado=datetime('now')",
            (uid, datos.nombre, datos.email, datos.telefono, datos.direccion, datos.comuna),
        )
        fila = con.execute("SELECT * FROM clientes WHERE user_id = ?", (uid,)).fetchone()
    log.info("perfil actualizado user=%s", uid)
    return {"client": _perfil(fila)}


@app.get("/admin/clients")
def listar(
    pagina: int = Query(1, ge=1),
    tamano: int = Query(20, ge=1, le=50),
    _: Llamador = Depends(seg.requiere("gateway", admin=True)),
):
    with db.conexion() as con:
        total = con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        filas = con.execute("SELECT * FROM clientes ORDER BY creado LIMIT ? OFFSET ?",
                            (tamano, (pagina - 1) * tamano)).fetchall()
    return {"clients": [_perfil(f) for f in filas], "total": total}


@app.get("/internal/clients")
def lote(ids: str = Query(..., max_length=2000), llamador: Llamador = Depends(seg.requiere("graphql", con_usuario=True))):
    """Perfiles por lote para GraphQL. Un usuario normal solo recibe el suyo."""
    lista = [i for i in dict.fromkeys(ids.split(",")) if i][:100]
    if not llamador.usuario.es_admin:
        lista = [i for i in lista if i == llamador.usuario.user_id]
    if not lista:
        return {"clients": []}
    with db.conexion() as con:
        filas = con.execute(f"SELECT * FROM clientes WHERE user_id IN ({','.join('?' * len(lista))})", lista).fetchall()
    return {"clients": [_perfil(f) for f in filas]}


# --- solicitudes

class Solicitud(BaseModel):
    tipo: str = Field(pattern="^(cotizacion|contacto)$")
    nombre: str = Field(default="", max_length=80)
    email: str = Field(max_length=254)
    telefono: str = Field(default="", max_length=20)
    asunto: str = Field(min_length=2, max_length=60)
    fecha_requerida: str = Field(default="", max_length=10)
    cantidad: str = Field(default="", max_length=40)
    mensaje: str = Field(default="", max_length=1000)

    @field_validator("nombre", "email", "telefono", "asunto", "fecha_requerida", "cantidad", "mensaje")
    @classmethod
    def recortar(cls, v: str) -> str:
        return v.strip()

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        if not EMAIL.match(v):
            raise ValueError("Correo no v\u00e1lido")
        return v.lower()

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        if v and not TELEFONO.match(v):
            raise ValueError("Tel\u00e9fono no v\u00e1lido")
        return v

    @field_validator("fecha_requerida")
    @classmethod
    def validar_fecha(cls, v: str) -> str:
        if v:
            try:
                if date.fromisoformat(v) < date.today():
                    raise ValueError("La fecha requerida ya pas\u00f3")
            except ValueError as e:
                raise ValueError(str(e) if "paso" in str(e) else "Fecha no valida")
        return v


@app.post("/solicitudes", status_code=201)
def nueva_solicitud(datos: Solicitud, llamador: Llamador = Depends(seg.requiere("gateway"))):
    """Formulario publico. Si hay sesion, se asocia al usuario."""
    if datos.tipo == "cotizacion" and len(datos.nombre) < 2:
        raise HTTPException(status_code=422, detail="El nombre es obligatorio")
    if datos.tipo == "contacto" and len(datos.mensaje) < 5:
        raise HTTPException(status_code=422, detail="Escribe tu mensaje")
    uid = llamador.usuario.user_id if llamador.usuario else None
    with db.transaccion() as con:
        sid = con.execute(
            "INSERT INTO solicitudes (tipo, nombre, email, telefono, asunto, fecha_requerida, cantidad, mensaje, user_id)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (datos.tipo, datos.nombre, datos.email, datos.telefono, datos.asunto, datos.fecha_requerida,
             datos.cantidad, datos.mensaje, uid),
        ).lastrowid
    log.info("solicitud recibida id=%s tipo=%s", sid, datos.tipo)
    # Al navegador solo vuelve el numero, no los datos personales.
    return {"id": sid, "tipo": datos.tipo, "estado": "nueva"}


@app.get("/admin/solicitudes")
def listar_solicitudes(estado: str | None = Query(None, pattern="^(nueva|respondida)$"),
                       _: Llamador = Depends(seg.requiere("gateway", admin=True))):
    sql, args = "SELECT * FROM solicitudes", []
    if estado:
        sql, args = sql + " WHERE estado = ?", [estado]
    with db.conexion() as con:
        filas = con.execute(sql + " ORDER BY id DESC LIMIT 50", args).fetchall()
    return {"solicitudes": [dict(f) for f in filas]}


class CambioSolicitud(BaseModel):
    estado: str = Field(pattern="^(nueva|respondida)$")


@app.patch("/admin/solicitudes/{sid}")
def marcar_solicitud(sid: int, datos: CambioSolicitud, _: Llamador = Depends(seg.requiere("gateway", admin=True))):
    with db.transaccion() as con:
        if not con.execute("UPDATE solicitudes SET estado = ? WHERE id = ?", (datos.estado, sid)).rowcount:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"id": sid, "estado": datos.estado}
