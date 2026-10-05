"""
ChocoManía - Backend API (HOST B)

API REST de negocio de la tienda. Expone el catálogo de productos y los
pedidos. No acepta llamadas anónimas: cada recurso de negocio exige el
header X-Gateway-Secret, que solo conoce el API Gateway (lo obtiene de
Vault). El cliente final nunca ve este secreto.

Ejecutar:
    export INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"     (Linux/macOS)
    $env:INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"       (PowerShell)
    uvicorn backend_api:app --host 0.0.0.0 --port 9000
"""

import os
import secrets
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="ChocoManía Backend API",
    description="API de negocio ubicada en un host diferente al API Gateway",
)

INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")

if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("INTERNAL_GATEWAY_SECRET no esta configurado")


def verify_gateway(x_gateway_secret: str = Header(default="")):
    """Solo deja pasar solicitudes que traen la credencial interna del Gateway."""
    valid = secrets.compare_digest(
        x_gateway_secret.encode(),
        INTERNAL_GATEWAY_SECRET.encode(),
    )
    if not valid:
        raise HTTPException(
            status_code=403,
            detail="Solicitud no autorizada desde Gateway",
        )


# ---------------------------------------------------------------------------
# Datos de la tienda (en memoria). Son los mismos productos del catálogo de
# la Semana 7: los 5 de seed.js más los de prueba del frontend.
# ---------------------------------------------------------------------------

UNSPLASH = "https://images.unsplash.com/photo-{}?q=80&w=500&auto=format&fit=crop"

PRODUCTS = [
    {"id": "choco-1", "nombre": "Torta tres leches de chocolate", "precio": 15800,
     "descripcion": "Bizcocho húmedo bañado en tres leches con cobertura de chocolate.",
     "imagen": UNSPLASH.format("1464349095431-e9a21285b5f3"), "categoria": "De leche"},
    {"id": "choco-2", "nombre": "Torta frutos del bosque", "precio": 16600,
     "descripcion": "Bizcocho de vainilla, crema chantilly y frutos rojos frescos.",
     "imagen": UNSPLASH.format("1578985545062-69928b1d9587"), "categoria": "De leche"},
    {"id": "choco-3", "nombre": "Torta de cumpleaños", "precio": 17900,
     "descripcion": "Personalizable con mensaje y color a elección.",
     "imagen": UNSPLASH.format("1621303837174-89787a7d4729"), "categoria": "De leche"},
    {"id": "choco-4", "nombre": "Caja de cupcakes surtidos", "precio": 6500,
     "descripcion": "Chocolate, red velvet y limón. Caja de 3 unidades.",
     "imagen": UNSPLASH.format("1517427294546-5aa121f68e8a"), "categoria": "Postres"},
    {"id": "choco-5", "nombre": "Brownie de chocolate 70%", "precio": 4200,
     "descripcion": "Chocolate 70% cacao con nueces tostadas.",
     "imagen": UNSPLASH.format("1550617931-e17a7b70dce2"), "categoria": "Amargo"},
    {"id": "choco-6", "nombre": "Torta red velvet", "precio": 18500,
     "descripcion": "Bizcocho aterciopelado con relleno de queso crema y toque de cacao.",
     "imagen": UNSPLASH.format("1621303837174-89787a7d4729"), "categoria": "De leche"},
    {"id": "choco-7", "nombre": "Alfajores bañados en chocolate", "precio": 5200,
     "descripcion": "Alfajores artesanales rellenos de manjar, bañados en chocolate con leche.",
     "imagen": UNSPLASH.format("1517427294546-5aa121f68e8a"), "categoria": "De leche"},
    {"id": "choco-8", "nombre": "Barra chocolate amargo 85%", "precio": 4800,
     "descripcion": "Chocolate 85% cacao de origen único, intenso y sin relleno.",
     "imagen": UNSPLASH.format("1550617931-e17a7b70dce2"), "categoria": "Amargo"},
    {"id": "choco-9", "nombre": "Trufas de chocolate amargo", "precio": 6900,
     "descripcion": "Trufas artesanales con ganache 70% cacao y cobertura amarga.",
     "imagen": "img/servicio-cocteles.jpg", "categoria": "Amargo"},
    {"id": "choco-10", "nombre": "Torta vegana de chocolate", "precio": 19900,
     "descripcion": "Bizcocho 100% plant-based con ganache vegano, sin huevo ni lácteos.",
     "imagen": UNSPLASH.format("1464349095431-e9a21285b5f3"), "categoria": "Vegana"},
    {"id": "choco-11", "nombre": "Brownie vegano sin gluten", "precio": 4700,
     "descripcion": "Brownie húmedo con harina de almendras, sin gluten, huevo ni lácteos.",
     "imagen": UNSPLASH.format("1550617931-e17a7b70dce2"), "categoria": "Vegana"},
    {"id": "choco-12", "nombre": "Chocolate sin azúcar con stevia", "precio": 5500,
     "descripcion": "Barra de chocolate endulzada con stevia, ideal para un consumo más consciente.",
     "imagen": UNSPLASH.format("1550617931-e17a7b70dce2"), "categoria": "Sin azúcar"},
    {"id": "choco-13", "nombre": "Bombones sin azúcar surtidos", "precio": 7200,
     "descripcion": "Caja de bombones rellenos endulzados con maltitol, sin azúcar añadida.",
     "imagen": "img/servicio-cocteles.jpg", "categoria": "Sin azúcar"},
    {"id": "choco-14", "nombre": "Caja por mayor 50 chocolates", "precio": 45000,
     "descripcion": "Caja al por mayor con 50 chocolates surtidos, ideal para eventos y revendedores.",
     "imagen": "img/servicio-regalos.png", "categoria": "Por mayor"},
    {"id": "choco-15", "nombre": "Pack por mayor 100 mini brownies", "precio": 62000,
     "descripcion": "Pack al por mayor de 100 mini brownies individuales, precio especial por volumen.",
     "imagen": "img/servicio-regalos.png", "categoria": "Por mayor"},
]

ORDERS = [
    {"id": 1001, "cliente": "Camila Rojas", "status": "paid",
     "items": [{"producto_id": "choco-1", "cantidad": 1}], "total": 15800},
    {"id": 1002, "cliente": "Diego Muñoz", "status": "pending",
     "items": [{"producto_id": "choco-5", "cantidad": 3}], "total": 12600},
]


class OrderItem(BaseModel):
    producto_id: str
    cantidad: int = Field(gt=0)


class NewOrder(BaseModel):
    cliente: str
    items: list[OrderItem] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "OK", "service": "ChocoManía Backend API"}


@app.get("/products", dependencies=[Depends(verify_gateway)])
def products(x_authenticated_client: str | None = Header(default=None)):
    return {
        "authenticated_client": x_authenticated_client,
        "products": PRODUCTS,
    }


@app.get("/products/{product_id}", dependencies=[Depends(verify_gateway)])
def product(product_id: str, x_authenticated_client: str | None = Header(default=None)):
    found = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"authenticated_client": x_authenticated_client, "product": found}


@app.get("/orders", dependencies=[Depends(verify_gateway)])
def orders(x_authenticated_client: str | None = Header(default=None)):
    return {
        "authenticated_client": x_authenticated_client,
        "orders": ORDERS,
    }


@app.post("/orders", status_code=201, dependencies=[Depends(verify_gateway)])
def create_order(order: NewOrder, x_authenticated_client: str | None = Header(default=None)):
    precios = {p["id"]: p["precio"] for p in PRODUCTS}
    faltantes = [i.producto_id for i in order.items if i.producto_id not in precios]
    if faltantes:
        raise HTTPException(status_code=400, detail=f"Productos inexistentes: {faltantes}")

    nuevo = {
        "id": max(o["id"] for o in ORDERS) + 1,
        "cliente": order.cliente,
        "status": "pending",
        "items": [i.model_dump() for i in order.items],
        "total": sum(precios[i.producto_id] * i.cantidad for i in order.items),
        "creado": datetime.now(timezone.utc).isoformat(),
    }
    ORDERS.append(nuevo)
    return {"authenticated_client": x_authenticated_client, "order": nuevo}
