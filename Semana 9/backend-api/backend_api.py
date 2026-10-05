"""
ChocoManía - Backend API (:9000)

Ejecuta la lógica de negocio de la tienda: catálogo y pedidos.

No confía en cualquier cliente:
  1. Toda llamada de negocio debe traer X-Gateway-Secret (solo lo conoce el
     Gateway, que lo lee de Vault). Sin él -> 403.
  2. La identidad del usuario llega en headers que el Gateway arma DESPUÉS
     de validar la sesión con el Auth Service:
         X-Authenticated-User:     USR-001
         X-Authenticated-Username: ana
         X-Authenticated-Roles:    user
     El Backend solo cree en esos headers porque vienen junto al secreto
     interno; un cliente de Internet no puede llegar hasta aquí con ellos.
  3. DELETE /products/{id} vuelve a exigir el rol admin (defensa en
     profundidad: el Gateway ya lo revisó, pero el Backend no lo da por hecho).

Ejecutar:
    export INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"
    uvicorn backend_api:app --host 0.0.0.0 --port 9000
"""

import os
import secrets
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="ChocoManía Backend API",
    description="Lógica de negocio: catálogo y pedidos",
)

INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")

if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("INTERNAL_GATEWAY_SECRET no esta configurado")


class Identity(BaseModel):
    user_id: str
    username: str
    roles: list[str]


def gateway_identity(
    x_gateway_secret: str = Header(default=""),
    x_authenticated_user: str = Header(default=""),
    x_authenticated_username: str = Header(default=""),
    x_authenticated_roles: str = Header(default=""),
) -> Identity:
    """Acepta la llamada solo si viene del Gateway y trae una identidad."""
    if not secrets.compare_digest(
        x_gateway_secret.encode(), INTERNAL_GATEWAY_SECRET.encode()
    ):
        raise HTTPException(status_code=403, detail="Solicitud no autorizada desde Gateway")

    if not x_authenticated_user:
        raise HTTPException(status_code=403, detail="Falta la identidad propagada por el Gateway")

    return Identity(
        user_id=x_authenticated_user,
        username=x_authenticated_username,
        roles=[r.strip() for r in x_authenticated_roles.split(",") if r.strip()],
    )


def require_admin(identity: Identity = Depends(gateway_identity)) -> Identity:
    if "admin" not in identity.roles:
        raise HTTPException(status_code=403, detail="Se requiere el rol admin")
    return identity


# ---------------------------------------------------------------------------
# Datos de la tienda (en memoria): los 15 productos del catálogo ChocoManía.
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

# Cada pedido pertenece a un usuario (user_id del Auth Service).
ORDERS = [
    {"id": 1001, "user_id": "USR-001", "cliente": "ana", "status": "paid",
     "items": [{"producto_id": "choco-1", "cantidad": 1}], "total": 15800},
    {"id": 1002, "user_id": "USR-003", "cliente": "ernesto", "status": "pending",
     "items": [{"producto_id": "choco-5", "cantidad": 3}], "total": 12600},
    {"id": 1003, "user_id": "USR-001", "cliente": "ana", "status": "pending",
     "items": [{"producto_id": "choco-7", "cantidad": 2}], "total": 10400},
]


class OrderItem(BaseModel):
    producto_id: str
    cantidad: int = Field(gt=0)


class NewOrder(BaseModel):
    items: list[OrderItem] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "OK", "service": "ChocoManía Backend API"}


@app.get("/products")
def products(identity: Identity = Depends(gateway_identity)):
    return {"authenticated_user": identity.username, "products": PRODUCTS}


@app.get("/products/{product_id}")
def product(product_id: str, identity: Identity = Depends(gateway_identity)):
    found = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"authenticated_user": identity.username, "product": found}


@app.delete("/products/{product_id}")
def delete_product(product_id: str, identity: Identity = Depends(require_admin)):
    found = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    PRODUCTS.remove(found)
    return {"deleted": found["id"], "nombre": found["nombre"], "by": identity.username}


@app.get("/orders")
def orders(identity: Identity = Depends(gateway_identity)):
    """Un usuario ve solo sus pedidos; un admin ve todos."""
    if "admin" in identity.roles:
        visibles = ORDERS
    else:
        visibles = [o for o in ORDERS if o["user_id"] == identity.user_id]
    return {"authenticated_user": identity.username, "orders": visibles}


@app.post("/orders", status_code=201)
def create_order(order: NewOrder, identity: Identity = Depends(gateway_identity)):
    precios = {p["id"]: p["precio"] for p in PRODUCTS}
    faltantes = [i.producto_id for i in order.items if i.producto_id not in precios]
    if faltantes:
        raise HTTPException(status_code=400, detail=f"Productos inexistentes: {faltantes}")

    nuevo = {
        "id": max((o["id"] for o in ORDERS), default=1000) + 1,
        "user_id": identity.user_id,
        "cliente": identity.username,
        "status": "pending",
        "items": [i.model_dump() for i in order.items],
        "total": sum(precios[i.producto_id] * i.cantidad for i in order.items),
        "creado": datetime.now(timezone.utc).isoformat(),
    }
    ORDERS.append(nuevo)
    return {"authenticated_user": identity.username, "order": nuevo}
