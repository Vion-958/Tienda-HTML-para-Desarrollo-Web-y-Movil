"""Identidad entre servicios: una credencial por llamador y usuario solo desde gateway o graphql."""

import secrets
from dataclasses import dataclass, field

from fastapi import Header, HTTPException

from comun.bitacora import evento
from comun.secretos import Secretos

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


def _coincide(token: str, aceptados: str) -> bool:
    # Durante una rotacion se aceptan dos valores separados por coma.
    return any(len(v) >= 16 and secrets.compare_digest(token.encode(), v.encode())
               for v in aceptados.split(",") if v)


class VerificadorServicio:
    """Valida al llamador con las credenciales guardadas en Vault (llamador_<nombre>)."""

    def __init__(self, secretos: Secretos):
        self.secretos = secretos

    def _valido(self, nombre: str, token: str) -> bool:
        clave = f"llamador_{nombre}"
        if _coincide(token, self.secretos.todos().get(clave, "")):
            return True
        # Puede que la credencial haya rotado: se relee Vault una vez.
        return _coincide(token, self.secretos.todos(forzar=True).get(clave, ""))

    def identificar(self, nombre: str, token: str, uid: str, uname: str, roles: str) -> Llamador:
        if not nombre or not token or not self._valido(nombre, token):
            evento("Vault secret/%s v%s: credencial de %s rechazada -> 403", self.secretos.ruta,
                   self.secretos.version, nombre or "(sin nombre)")
            raise HTTPException(status_code=403, detail="Llamador no autorizado")
        evento("Vault secret/%s v%s: credencial de %s verificada -> permitido", self.secretos.ruta,
               self.secretos.version, nombre)
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
                evento("%s no tiene permiso para esta operacion -> 403", llamador.nombre)
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
