"""
ChocoManía - Vault local de reemplazo (solo para desarrollo sin Docker)

Imita la única ruta de HashiCorp Vault que usa el API Gateway:
    GET /v1/secret/data/gateway   (header X-Vault-Token)

Los secretos deben ser EXACTAMENTE los mismos que reciben los servicios:
    auth_introspection_secret == AUTH_INTROSPECTION_SECRET del Auth Service
    backend_shared_secret     == INTERNAL_GATEWAY_SECRET del Backend
Si no coinciden, el login responde 503 (el Auth Service rechaza la
introspección) o el catálogo falla (el Backend responde 403).

Ejecutar (no necesita instalar nada):
    python vault_local.py

Comprobar:
    curl -H "X-Vault-Token: dev-only-token" http://127.0.0.1:8200/v1/secret/data/gateway

Es solo un reemplazo de laboratorio: no cifra, no tiene políticas ni
auditoría. Con Docker disponible, usa el Vault real (docker compose up).
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

VAULT_TOKEN = os.getenv("VAULT_TOKEN", "dev-only-token")
SECRETOS = {
    "backend_shared_secret": os.getenv("BACKEND_SHARED_SECRET", "gateway-api-secret-456"),
    "auth_introspection_secret": os.getenv("AUTH_INTROSPECTION_SECRET", "gateway-auth-secret-789"),
}


class Vault(BaseHTTPRequestHandler):
    def responder(self, status: int, cuerpo: dict) -> None:
        datos = json.dumps(cuerpo).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        if self.path == "/v1/sys/health":
            return self.responder(200, {"initialized": True, "sealed": False})
        if self.path != "/v1/secret/data/gateway":
            return self.responder(404, {"errors": []})
        if self.headers.get("X-Vault-Token") != VAULT_TOKEN:
            return self.responder(403, {"errors": ["permission denied"]})
        # Misma forma que el motor KV v2 de Vault: data.data
        self.responder(200, {"data": {"data": SECRETOS, "metadata": {"version": 1}}})

    def log_message(self, formato, *args):
        print(f"[vault-local] {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")


if __name__ == "__main__":
    print("Vault local en http://127.0.0.1:8200 (token:", VAULT_TOKEN + ")")
    HTTPServer(("127.0.0.1", 8200), Vault).serve_forever()
