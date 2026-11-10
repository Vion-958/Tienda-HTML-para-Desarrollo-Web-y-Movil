"""Vault local de reemplazo para desarrollo sin Docker."""

import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.getenv("VAULT_TOKEN", "")
DATOS = json.loads(os.getenv("VAULT_DATA", "{}"))
PUERTO = int(os.getenv("VAULT_PORT", "8200"))

if not TOKEN or not DATOS:
    raise SystemExit("Faltan VAULT_TOKEN y VAULT_DATA. Usa: python iniciar.py")


class Vault(BaseHTTPRequestHandler):
    def responder(self, status, cuerpo):
        datos = json.dumps(cuerpo).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        if self.path == "/v1/sys/health":
            return self.responder(200, {"initialized": True, "sealed": False})
        prefijo = "/v1/secret/data/"
        if not self.path.startswith(prefijo) or self.path[len(prefijo):] not in DATOS:
            return self.responder(404, {"errors": []})
        if not secrets.compare_digest(self.headers.get("X-Vault-Token", "").encode(), TOKEN.encode()):
            return self.responder(403, {"errors": ["permission denied"]})
        self.responder(200, {"data": {"data": DATOS[self.path[len(prefijo):]], "metadata": {"version": 1}}})

    def log_message(self, formato, *args):
        # Nunca se registra el contenido, solo la ruta y el codigo.
        print(f"vault-local {self.command} {self.path} {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    print(f"vault-local en http://127.0.0.1:{PUERTO}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PUERTO), Vault).serve_forever()
