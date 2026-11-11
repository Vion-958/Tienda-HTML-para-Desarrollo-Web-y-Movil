"""inventory: catalogo, stock e imagenes. Autoridad del precio y del stock."""

import json
import os
import re
import secrets
import unicodedata
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Response, UploadFile  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from comun.db import BaseDatos  # noqa: E402
from comun.registro import configurar  # noqa: E402
from comun.seguridad import Llamador, VerificadorServicio, credenciales_desde_entorno  # noqa: E402

AQUI = Path(__file__).resolve().parent
app = FastAPI(title="ChocoMania inventory")
log = configurar(app, "inventory")
db = BaseDatos(os.getenv("INVENTORY_DB", str(AQUI / "data" / "inventory.db")), AQUI / "schema.sql", AQUI / "seed.sql")
seg = VerificadorServicio(credenciales_desde_entorno())

MAX_IMAGENES = 5
MAX_BYTES_IMAGEN = 2 * 1024 * 1024
# Clave sin tildes -> nombre guardado.
ALERGENOS = {"gluten": "gluten", "lacteos": "l\u00e1cteos", "huevo": "huevo", "frutos secos": "frutos secos", "soya": "soya"}
TAMANO_MAX = 50


# --- lectura

def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c))


def _url_imagen(fila) -> str:
    return fila["url"] or f"/api/images/{fila['id']}"


def _armar(con, filas, incluir_inactivos=False) -> list[dict]:
    ids = [f["id"] for f in filas]
    if not ids:
        return []
    marcas = ",".join("?" * len(ids))
    tags, imgs = {}, {}
    for t in con.execute(f"SELECT producto_id, tag FROM producto_tags WHERE producto_id IN ({marcas}) ORDER BY tag", ids):
        tags.setdefault(t["producto_id"], []).append(t["tag"])
    for i in con.execute(f"SELECT id, producto_id, url FROM imagenes WHERE producto_id IN ({marcas}) ORDER BY posicion", ids):
        imgs.setdefault(i["producto_id"], []).append(_url_imagen(i))
    salida = []
    for f in filas:
        urls = imgs.get(f["id"], [])
        p = {
            "id": f["id"],
            "nombre": f["nombre"],
            "descripcion": f["descripcion"],
            "precio": f["precio"],
            "categoria": f["categoria"],
            "stock": f["stock"],
            "disponible": bool(f["activo"]) and f["stock"] > 0,
            "tags": tags.get(f["id"], []),
            "imagen": urls[0] if urls else None,
            "imagenes": urls,
            "ingredientes": f["ingredientes"],
            "alergenos": json.loads(f["alergenos"]),
        }
        if incluir_inactivos:
            p["activo"] = bool(f["activo"])
        salida.append(p)
    return salida


def _buscar(con, producto_id: str, solo_activos=True):
    sql = "SELECT * FROM productos WHERE id = ?" + (" AND activo = 1" if solo_activos else "")
    return con.execute(sql, (producto_id,)).fetchone()


@app.get("/health")
def health():
    with db.conexion() as con:
        con.execute("SELECT 1")
    return {"status": "OK", "service": "inventory"}


@app.get("/products")
def listar(
    categoria: str | None = Query(None, max_length=30),
    tag: list[str] = Query(default=[]),
    q: str | None = Query(None, max_length=60),
    disponible: bool | None = None,
    pagina: int = Query(1, ge=1),
    tamano: int = Query(TAMANO_MAX, ge=1, le=TAMANO_MAX),
    _: Llamador = Depends(seg.requiere("gateway", "graphql")),
):
    if len(tag) > 8:
        raise HTTPException(status_code=400, detail="M\u00e1ximo 8 tags por filtro")
    where, args = ["activo = 1"], []
    if categoria:
        where.append("categoria = ?")
        args.append(categoria)
    if q:
        where.append("(nombre LIKE ? OR descripcion LIKE ?)")
        args += [f"%{q}%", f"%{q}%"]
    if disponible is not None:
        where.append("stock > 0" if disponible else "stock = 0")
    for t in tag:
        where.append("id IN (SELECT producto_id FROM producto_tags WHERE tag = ?)")
        args.append(t.strip().lower())
    sql_where = " AND ".join(where)
    with db.conexion() as con:
        total = con.execute(f"SELECT COUNT(*) FROM productos WHERE {sql_where}", args).fetchone()[0]
        filas = con.execute(
            f"SELECT * FROM productos WHERE {sql_where} ORDER BY CAST(substr(id, 7) AS INTEGER), id LIMIT ? OFFSET ?",
            args + [tamano, (pagina - 1) * tamano],
        ).fetchall()
        return {"products": _armar(con, filas), "total": total, "pagina": pagina, "tamano": tamano}


@app.get("/products/{producto_id}")
def detalle(producto_id: str, _: Llamador = Depends(seg.requiere("gateway", "graphql"))):
    with db.conexion() as con:
        fila = _buscar(con, producto_id)
        if not fila:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return {"product": _armar(con, [fila])[0]}


@app.get("/images/{imagen_id}")
def imagen(imagen_id: str, _: Llamador = Depends(seg.requiere("gateway"))):
    with db.conexion() as con:
        fila = con.execute("SELECT mime, datos FROM imagenes WHERE id = ? AND datos IS NOT NULL", (imagen_id,)).fetchone()
    if not fila:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return Response(
        content=fila["datos"],
        media_type=fila["mime"],
        headers={"Cache-Control": "public, max-age=3600", "X-Content-Type-Options": "nosniff"},
    )


# --- administracion

def tipo_de_imagen(datos: bytes) -> str | None:
    """Por los primeros bytes, no por el nombre ni el content-type del navegador."""
    if datos.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(datos) > 12 and datos[:4] == b"RIFF" and datos[8:12] == b"WEBP":
        return "image/webp"
    return None


def normalizar_tags(texto: str) -> list[str]:
    tags = []
    for t in texto.split(","):
        t = re.sub(r"\s+", " ", t).strip().lower()
        if t and t not in tags:
            tags.append(t)
    return tags


def _entero(valor: str, minimo: int, maximo: int) -> int | None:
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return n if minimo <= n <= maximo else None


async def _validar(con, campos: dict, imagenes: list[UploadFile], producto_id: str | None):
    errores, datos = {}, {}
    nombre = campos["nombre"].strip()
    if not 3 <= len(nombre) <= 80:
        errores["nombre"] = "El nombre debe tener entre 3 y 80 caracteres."
    elif con.execute(
        "SELECT 1 FROM productos WHERE nombre = ? AND activo = 1 AND id != ?", (nombre, producto_id or "")
    ).fetchone():
        errores["nombre"] = "Ya existe un producto con ese nombre."
    datos["nombre"] = nombre

    datos["precio"] = _entero(campos["precio"], 100, 10_000_000)
    if datos["precio"] is None:
        errores["precio"] = "El precio debe ser un entero entre $100 y $10.000.000."

    datos["categoria"] = campos["categoria"].strip()
    if not 2 <= len(datos["categoria"]) <= 30:
        errores["categoria"] = "La categor\u00eda debe tener entre 2 y 30 caracteres."

    datos["descripcion"] = campos["descripcion"].strip()
    if not 10 <= len(datos["descripcion"]) <= 500:
        errores["descripcion"] = "La descripci\u00f3n debe tener entre 10 y 500 caracteres."

    datos["tags"] = normalizar_tags(campos["tags"])
    if len(datos["tags"]) > 8 or any(not 2 <= len(t) <= 25 for t in datos["tags"]):
        errores["tags"] = "Hasta 8 tags, separados por coma, de 2 a 25 caracteres."

    datos["stock"] = _entero(campos["stock"], 0, 9999)
    if datos["stock"] is None:
        errores["stock"] = "El stock debe ser un entero entre 0 y 9999."

    datos["ingredientes"] = campos["ingredientes"].strip()
    if len(datos["ingredientes"]) > 300:
        errores["ingredientes"] = "Los ingredientes admiten hasta 300 caracteres."

    claves = [a for a in dict.fromkeys(_sin_tildes(a.strip().lower()) for a in campos["alergenos"]) if a]
    if any(a not in ALERGENOS for a in claves):
        errores["alergenos"] = "Al\u00e9rgeno no reconocido."
    datos["alergenos"] = [ALERGENOS.get(a, a) for a in claves]

    archivos = [f for f in imagenes if f.filename]
    nuevas = []
    obligatorias = producto_id is None
    if len(archivos) > MAX_IMAGENES or (obligatorias and not archivos):
        errores["imagenes"] = f"Sube entre 1 y {MAX_IMAGENES} imagenes."
    else:
        for f in archivos:
            contenido = await f.read(MAX_BYTES_IMAGEN + 1)
            if len(contenido) > MAX_BYTES_IMAGEN:
                errores["imagenes"] = f"{f.filename}: supera los 2 MB."
                break
            mime = tipo_de_imagen(contenido)
            if mime is None:
                errores["imagenes"] = f"{f.filename}: solo se aceptan JPG, PNG o WEBP."
                break
            nuevas.append((contenido, mime))

    if errores:
        raise HTTPException(status_code=400, detail={"mensaje": "Revisa los campos marcados.", "errores": errores})
    return datos, nuevas


def _guardar_relaciones(con, producto_id: str, datos: dict, nuevas: list):
    con.execute("DELETE FROM producto_tags WHERE producto_id = ?", (producto_id,))
    con.executemany("INSERT INTO producto_tags (producto_id, tag) VALUES (?, ?)",
                    [(producto_id, t) for t in datos["tags"]])
    if nuevas:
        con.execute("DELETE FROM imagenes WHERE producto_id = ?", (producto_id,))
        con.executemany(
            "INSERT INTO imagenes (id, producto_id, posicion, mime, datos) VALUES (?, ?, ?, ?, ?)",
            [(secrets.token_hex(8), producto_id, i, mime, contenido) for i, (contenido, mime) in enumerate(nuevas)],
        )


def _siguiente_id(con) -> str:
    n = con.execute("SELECT COALESCE(MAX(CAST(substr(id, 7) AS INTEGER)), 0) FROM productos WHERE id LIKE 'choco-%'").fetchone()[0]
    return f"choco-{n + 1}"


def _formulario(
    nombre: str = Form(""),
    precio: str = Form(""),
    categoria: str = Form(""),
    descripcion: str = Form(""),
    tags: str = Form(""),
    stock: str = Form(""),
    ingredientes: str = Form(""),
    alergenos: list[str] = Form(default=[]),
) -> dict:
    return locals()


@app.post("/products", status_code=201)
async def crear(
    campos: dict = Depends(_formulario),
    imagenes: list[UploadFile] = File(default=[]),
    llamador: Llamador = Depends(seg.requiere("gateway", admin=True)),
):
    with db.conexion() as con:
        datos, nuevas = await _validar(con, campos, imagenes, None)
    with db.transaccion() as con:
        pid = _siguiente_id(con)
        con.execute(
            "INSERT INTO productos (id, nombre, descripcion, precio, categoria, stock, ingredientes, alergenos, creado_por)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (pid, datos["nombre"], datos["descripcion"], datos["precio"], datos["categoria"], datos["stock"],
             datos["ingredientes"], json.dumps(datos["alergenos"]), llamador.usuario.username),
        )
        _guardar_relaciones(con, pid, datos, nuevas)
    log.info("producto creado id=%s por=%s", pid, llamador.usuario.user_id)
    with db.conexion() as con:
        return {"product": _armar(con, [_buscar(con, pid)])[0]}


@app.put("/products/{producto_id}")
async def reemplazar(
    producto_id: str,
    campos: dict = Depends(_formulario),
    imagenes: list[UploadFile] = File(default=[]),
    llamador: Llamador = Depends(seg.requiere("gateway", admin=True)),
):
    """Reemplaza el producto; sin imagenes nuevas se conservan las actuales."""
    with db.conexion() as con:
        if not _buscar(con, producto_id):
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        datos, nuevas = await _validar(con, campos, imagenes, producto_id)
    with db.transaccion() as con:
        con.execute(
            "UPDATE productos SET nombre=?, descripcion=?, precio=?, categoria=?, stock=?, ingredientes=?,"
            " alergenos=?, actualizado=datetime('now') WHERE id=?",
            (datos["nombre"], datos["descripcion"], datos["precio"], datos["categoria"], datos["stock"],
             datos["ingredientes"], json.dumps(datos["alergenos"]), producto_id),
        )
        _guardar_relaciones(con, producto_id, datos, nuevas)
    log.info("producto modificado id=%s por=%s", producto_id, llamador.usuario.user_id)
    with db.conexion() as con:
        return {"product": _armar(con, [_buscar(con, producto_id)])[0]}


@app.delete("/products/{producto_id}")
def eliminar(producto_id: str, llamador: Llamador = Depends(seg.requiere("gateway", admin=True))):
    """Baja logica: los pedidos antiguos conservan el producto."""
    with db.transaccion() as con:
        fila = _buscar(con, producto_id)
        if not fila:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        con.execute("UPDATE productos SET activo = 0, actualizado = datetime('now') WHERE id = ?", (producto_id,))
    log.info("producto dado de baja id=%s por=%s", producto_id, llamador.usuario.user_id)
    return {"deleted": producto_id, "nombre": fila["nombre"]}


# --- interno

@app.get("/internal/products")
def lote(ids: str = Query(..., max_length=2000), _: Llamador = Depends(seg.requiere("graphql", "orders"))):
    """Varios productos en una sola llamada (evita N+1 en GraphQL)."""
    lista = [i for i in dict.fromkeys(ids.split(",")) if i][:100]
    if not lista:
        return {"products": []}
    with db.conexion() as con:
        filas = con.execute(f"SELECT * FROM productos WHERE id IN ({','.join('?' * len(lista))})", lista).fetchall()
        return {"products": _armar(con, filas, incluir_inactivos=True)}


class Item(BaseModel):
    producto_id: str = Field(min_length=1, max_length=20)
    cantidad: int = Field(ge=1, le=50)


class Reserva(BaseModel):
    pedido_id: int = Field(ge=1)
    items: list[Item] = Field(min_length=1, max_length=30)


def _reserva_actual(con, pedido_id: int) -> list[dict]:
    filas = con.execute(
        "SELECT r.producto_id, r.cantidad, r.estado, p.nombre, p.precio FROM reservas r"
        " JOIN productos p ON p.id = r.producto_id WHERE r.pedido_id = ? ORDER BY p.rowid",
        (pedido_id,),
    ).fetchall()
    return [
        {"producto_id": f["producto_id"], "nombre": f["nombre"], "precio_unitario": f["precio"],
         "cantidad": f["cantidad"], "estado": f["estado"]}
        for f in filas
    ]


@app.post("/internal/reservations")
def reservar(datos: Reserva, _: Llamador = Depends(seg.requiere("orders"))):
    """Aparta stock y devuelve el precio oficial. Idempotente por pedido_id."""
    cantidades: dict[str, int] = {}
    for it in datos.items:
        cantidades[it.producto_id] = cantidades.get(it.producto_id, 0) + it.cantidad

    with db.transaccion() as con:
        existente = _reserva_actual(con, datos.pedido_id)
        if existente:
            return {"pedido_id": datos.pedido_id, "items": existente, "repetida": True}

        faltantes, sin_stock = [], []
        for pid, cant in cantidades.items():
            fila = _buscar(con, pid)
            if not fila:
                faltantes.append(pid)
            elif fila["stock"] < cant:
                sin_stock.append({"producto_id": pid, "disponible": fila["stock"]})
        if faltantes:
            raise HTTPException(status_code=400, detail={"mensaje": "Productos inexistentes", "productos": faltantes})
        if sin_stock:
            raise HTTPException(status_code=409, detail={"mensaje": "Sin stock suficiente", "productos": sin_stock})

        for pid, cant in cantidades.items():
            con.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cant, pid))
            con.execute("INSERT INTO reservas (pedido_id, producto_id, cantidad) VALUES (?, ?, ?)",
                        (datos.pedido_id, pid, cant))
        return {"pedido_id": datos.pedido_id, "items": _reserva_actual(con, datos.pedido_id), "repetida": False}


@app.post("/internal/reservations/{pedido_id}/release")
def liberar(pedido_id: int, _: Llamador = Depends(seg.requiere("orders"))):
    """Devuelve el stock de un pedido cancelado o fallido (pagado o no). Idempotente."""
    with db.transaccion() as con:
        filas = con.execute("SELECT producto_id, cantidad FROM reservas WHERE pedido_id = ?"
                            " AND estado IN ('reservada', 'confirmada')", (pedido_id,)).fetchall()
        for f in filas:
            con.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (f["cantidad"], f["producto_id"]))
        con.execute("UPDATE reservas SET estado = 'liberada', actualizado = datetime('now')"
                    " WHERE pedido_id = ? AND estado IN ('reservada', 'confirmada')", (pedido_id,))
    return {"pedido_id": pedido_id, "liberados": len(filas)}


@app.post("/internal/reservations/{pedido_id}/confirm")
def confirmar(pedido_id: int, _: Llamador = Depends(seg.requiere("orders"))):
    """El pedido se pago: la reserva pasa a venta definitiva."""
    with db.transaccion() as con:
        n = con.execute("UPDATE reservas SET estado = 'confirmada', actualizado = datetime('now')"
                        " WHERE pedido_id = ? AND estado = 'reservada'", (pedido_id,)).rowcount
    return {"pedido_id": pedido_id, "confirmados": n}
