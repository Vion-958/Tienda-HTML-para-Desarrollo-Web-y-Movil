"""
ChocoManía - API Gateway seguro (HOST A)

Frontera de seguridad de la tienda. Todo cliente (el sitio web, una app
móvil o un script) entra por aquí:

    Cliente --Bearer token--> Gateway --consulta--> Vault
                                 |
                                 +--X-Gateway-Secret--> Backend API (HOST B)

1. Exige Authorization: Bearer <token>.
2. Lee de Vault el client_token esperado y el backend_shared_secret.
3. Si el token no coincide responde 401 y la solicitud nunca llega al backend.
4. Si coincide, reenvía la solicitud al backend agregando la credencial
   interna (X-Gateway-Secret) y la identidad del cliente.

Ningún secreto está escrito en este archivo: el Gateway solo conoce la
dirección de Vault y un token para consultarlo (variables de entorno).

Ejecutar:
    uvicorn gateway:app --host 0.0.0.0 --port 8000
"""

import os
import secrets

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

app = FastAPI(
    title="ChocoManía Secure API Gateway",
    description="API Gateway con Vault y Bearer Token",
)

# El sitio web de ChocoManía corre en otro origen (PHP en localhost/XAMPP),
# así que el navegador necesita CORS para poder llamar al Gateway.
# CORS_ORIGINS acepta una lista separada por comas; por defecto, cualquiera.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

security = HTTPBearer(auto_error=False)

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://192.168.1.20:9000")

if not VAULT_TOKEN:
    raise RuntimeError("VAULT_TOKEN no configurado")


async def get_gateway_secrets():
    """Lee secret/gateway desde Vault (motor KV v2) en cada solicitud.

    No se guarda en caché a propósito: así, al rotar el token en Vault, el
    cambio se aplica de inmediato sin reiniciar el Gateway.
    """
    url = f"{VAULT_ADDR}/v1/secret/data/gateway"
    headers = {"X-Vault-Token": VAULT_TOKEN}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError:
        # Vault apagado o inalcanzable: error controlado, sin detalles internos.
        raise HTTPException(status_code=500, detail="No fue posible acceder a Vault")

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="No fue posible acceder a Vault")

    return response.json()["data"]["data"]


async def authenticate_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Bearer token requerido")

    vault_secrets = await get_gateway_secrets()

    expected_token = vault_secrets["client_token"]
    received_token = credentials.credentials

    valid = secrets.compare_digest(received_token.encode(), expected_token.encode())

    if not valid:
        raise HTTPException(status_code=401, detail="Token invalido")

    return {
        "client_id": "chocomania-web",
        "backend_secret": vault_secrets["backend_shared_secret"],
    }


@app.get("/health")
def health():
    return {"status": "OK", "service": "ChocoManía API Gateway"}


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request, auth=Depends(authenticate_client)):
    target_url = f"{BACKEND_URL}/{path}"
    body = await request.body()

    # Se construyen headers nuevos: nada de lo que mande el cliente (por
    # ejemplo un X-Gateway-Secret inventado) llega al backend.
    gateway_headers = {
        "X-Gateway-Secret": auth["backend_secret"],
        "X-Authenticated-Client": auth["client_id"],
    }

    content_type = request.headers.get("content-type")
    if content_type:
        gateway_headers["content-type"] = content_type

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            upstream = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                content=body,
                headers=gateway_headers,
            )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Backend no disponible")

    response_headers = {}
    if "content-type" in upstream.headers:
        response_headers["content-type"] = upstream.headers["content-type"]

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
    )
