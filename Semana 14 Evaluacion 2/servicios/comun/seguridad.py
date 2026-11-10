"""Identidad entre servicios: una credencial por llamador y usuario solo desde gateway o graphql."""

import json
import os
import secrets
from dataclasses import dataclass, field

from fastapi import Header, HTTPException

LLAMADORES_CON_USUARIO = {"gateway", "graphql"}


@dataclass
class Usuario:
    user_id: str
    username: str
    roles: list[str] = field(default_factory=list)

    @property
    def es_admin(self) -> bool:
        return "admin" in self.roles


@dataclass
class Llamador:
    nombre: str
    usuario: Usuario | None


def credenciales_desde_entorno() -> dict[str, str]:
    crudo = os.getenv("SERVICE_CALLERS", "")
    if not crudo:
        raise RuntimeError("SERVICE_CALLERS no esta configurado")
    datos = json.loads(crudo)
    if not all(isinstance(v, str) and len(v) >= 16 for v in datos.values()):
        raise RuntimeError("Cada credencial de SERVICE_CALLERS debe tener al menos 16 caracteres")
    return datos


class VerificadorServicio:
    def __init__(self, credenciales: dict[str, str]):
        self.credenciales = credenciales

    def identificar(self, nombre: str, token: str, uid: str, uname: str, roles: str) -> Llamador:
        esperado = self.credenciales.get(nombre)
        if not esperado or not secrets.compare_digest(token.encode(), esperado.encode()):
            raise HTTPException(status_code=403, detail="Llamador no autorizado")
        usuario = None
        if nombre in LLAMADORES_CON_USUARIO and uid:
            usuario = Usuario(uid, uname, [r for r in roles.split(",") if r])
        return Llamador(nombre, usuario)

    def requiere(self, *permitidos: str, con_usuario: bool = False, admin: bool = False):
        """Dependencia FastAPI: valida el llamador y, si se pide, el usuario."""

        def dependencia(
            x_service_name: str = Header(default=""),
            x_service_token: str = Header(default=""),
            x_user_id: str = Header(default=""),
            x_user_name: str = Header(default=""),
            x_user_roles: str = Header(default=""),
        ) -> Llamador:
            llamador = self.identificar(x_service_name, x_service_token, x_user_id, x_user_name, x_user_roles)
            if permitidos and llamador.nombre not in permitidos:
                raise HTTPException(status_code=403, detail="Llamador no autorizado para esta operacion")
            if (con_usuario or admin) and llamador.usuario is None:
                raise HTTPException(status_code=401, detail="Falta la identidad del usuario")
            if admin and not llamador.usuario.es_admin:
                raise HTTPException(status_code=403, detail="Se requiere el rol admin")
            return llamador

        return dependencia


def cabeceras_servicio(nombre: str, token: str, request_id: str = "", usuario: Usuario | None = None) -> dict:
    cab = {"X-Service-Name": nombre, "X-Service-Token": token}
    if request_id:
        cab["X-Request-ID"] = request_id
    if usuario:
        cab.update({
            "X-User-Id": usuario.user_id,
            "X-User-Name": usuario.username,
            "X-User-Roles": ",".join(usuario.roles),
        })
    return cab
