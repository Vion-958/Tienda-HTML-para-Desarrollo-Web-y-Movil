"""Vault local para desarrollo sin Docker. Imita la API de HashiCorp Vault que usa ChocoMania."""

import json
import os
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KV = "/v1/secret/data/"
POLITICA = "/v1/sys/policies/acl/"


class Almacen:
    """KV v2 con versiones, politicas de solo lectura y tokens."""

    def __init__(self, token_raiz: str):
        self.raiz = token_raiz
        self.datos: dict[str, list[dict]] = {}
        self.politicas: dict[str, set[str]] = {}
        self.tokens: dict[str, set[str]] = {}
        self.lock = threading.Lock()

    def puede_leer(self, token: str, ruta: str) -> bool:
        if secrets.compare_digest(token.encode(), self.raiz.encode()):
            return True
        politicas = self.tokens.get(token, set())
        return any(ruta in self.politicas.get(p, set()) for p in politicas)

    def es_raiz(self, token: str) -> bool:
        return secrets.compare_digest(token.encode(), self.raiz.encode())


def crear_servidor(token_raiz: str, puerto: int, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    almacen = Almacen(token_raiz)

    class Vault(BaseHTTPRequestHandler):
        def responder(self, status, cuerpo=None):
            datos = json.dumps(cuerpo or {}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(datos)))
            self.end_headers()
            self.wfile.write(datos)

        def token(self) -> str:
            return self.headers.get("X-Vault-Token", "")

        def cuerpo(self) -> dict:
            largo = int(self.headers.get("Content-Length", "0") or 0)
            return json.loads(self.rfile.read(largo) or b"{}") if largo else {}

        def do_GET(self):
            if self.path == "/v1/sys/health":
                return self.responder(200, {"initialized": True, "sealed": False})
            if not self.path.startswith(KV):
                return self.responder(404, {"errors": []})
            ruta = self.path[len(KV):]
            with almacen.lock:
                if not almacen.puede_leer(self.token(), ruta):
                    return self.responder(403, {"errors": ["permission denied"]})
                versiones = almacen.datos.get(ruta)
                if not versiones:
                    return self.responder(404, {"errors": []})
                return self.responder(200, {"data": {"data": versiones[-1],
                                                     "metadata": {"version": len(versiones)}}})

        def do_POST(self):
            if not almacen.es_raiz(self.token()):
                return self.responder(403, {"errors": ["permission denied"]})
            try:
                cuerpo = self.cuerpo()
            except ValueError:
                return self.responder(400, {"errors": ["json invalido"]})
            with almacen.lock:
                if self.path.startswith(KV):
                    ruta = self.path[len(KV):]
                    almacen.datos.setdefault(ruta, []).append(dict(cuerpo.get("data", {})))
                    return self.responder(200, {"data": {"version": len(almacen.datos[ruta])}})
                if self.path.startswith(POLITICA):
                    nombre = self.path[len(POLITICA):]
                    almacen.politicas[nombre] = set(re.findall(r'path\s+"secret/data/([^"]+)"', cuerpo.get("policy", "")))
                    return self.responder(204)
                if self.path == "/v1/auth/token/create":
                    nuevo = cuerpo.get("id") or "hvs." + secrets.token_urlsafe(24)
                    almacen.tokens[nuevo] = set(cuerpo.get("policies", []))
                    return self.responder(200, {"auth": {"client_token": nuevo, "policies": sorted(almacen.tokens[nuevo])}})
            self.responder(404, {"errors": []})

        do_PUT = do_POST

        def log_message(self, formato, *args):
            # Nunca se registra el contenido, solo la ruta y el codigo.
            print(f"vault-local {self.command} {self.path} {args[1] if len(args) > 1 else ''}", flush=True)

    return ThreadingHTTPServer((host, puerto), Vault)


if __name__ == "__main__":
    raiz = os.getenv("VAULT_TOKEN", "")
    if not raiz:
        raise SystemExit("Falta VAULT_TOKEN. Usa: python iniciar.py")
    puerto = int(os.getenv("VAULT_PORT", "8200"))
    print(f"vault-local en http://127.0.0.1:{puerto}", flush=True)
    crear_servidor(raiz, puerto).serve_forever()
