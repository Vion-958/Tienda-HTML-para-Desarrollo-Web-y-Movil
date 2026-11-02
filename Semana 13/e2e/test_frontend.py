"""
Prueba end-to-end en el navegador (Playwright), con el sistema arriba.

    pip install pytest-playwright
    playwright install chromium
    pytest e2e/test_frontend.py --headed      (sin --headed corre oculto)

Variable opcional: SITE_URL (por defecto http://localhost:8000)
"""

import os
import re
import struct
import time
import zlib

import pytest
from playwright.sync_api import Page, expect

SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")


def ingresar(page: Page, usuario: str, clave: str):
    page.goto(f"{SITE_URL}/cuenta.php")
    page.fill("#username", usuario)
    page.fill("#password", clave)
    page.click("#loginBtn")


@pytest.fixture(autouse=True)
def aceptar_confirmaciones(page: Page):
    page.on("dialog", lambda dialog: dialog.accept())


def test_login_incorrecto_muestra_401(page: Page):
    ingresar(page, "ana", "incorrecta")
    expect(page.locator("#loginMsg")).to_contain_text("401")
    expect(page.locator("#accountSection")).to_be_hidden()


def test_ana_inicia_sesion_y_no_ve_la_administracion(page: Page):
    ingresar(page, "ana", "1234")

    expect(page.locator("#accountName")).to_have_text("ana")
    expect(page.locator("[data-account-link]")).to_have_text("Hola, ana")
    expect(page.locator("#ordersTable tbody tr").first).to_be_visible()

    # Sin el rol admin no se muestra la administración de productos.
    expect(page.locator("#adminSection")).to_be_hidden()

    # La cookie existe, pero JavaScript no puede leerla (HttpOnly).
    cookies = {c["name"]: c for c in page.context.cookies()}
    assert cookies["session_token"]["httpOnly"] is True
    assert "session_token" not in page.evaluate("document.cookie")
    assert page.evaluate("Object.keys(localStorage).join(',')").find("token") == -1

    # Aunque la página no muestre el botón, el servidor sigue rechazando
    # la operación de administrador para Ana.
    estado = page.evaluate(
        "fetch('/api/products/choco-1', {method: 'DELETE'}).then(r => r.status)"
    )
    assert estado == 403

    # Con sesión, el catálogo viene en vivo desde el Gateway.
    page.goto(f"{SITE_URL}/catalogo.php")
    expect(page.locator("#productGrid article").first).to_be_visible()
    assert page.evaluate("window.ChocoAPI.origenDatos") == "gateway"

    # Logout: vuelve al login y la sesión no revive al recargar.
    page.goto(f"{SITE_URL}/cuenta.php")
    page.click("#logoutBtn")
    expect(page.locator("#loginSection")).to_be_visible()
    expect(page.locator("#loginMsg")).to_contain_text("revocada")
    page.reload()
    expect(page.locator("#loginSection")).to_be_visible()
    assert "session_token" not in {c["name"] for c in page.context.cookies()}


def test_ernesto_elimina_un_producto(page: Page):
    ingresar(page, "ernesto", "admin123")
    expect(page.locator("#accountRoles")).to_have_text("user, admin")
    expect(page.locator("#adminSection")).to_be_visible()

    filas = page.locator("#productsTable tbody tr")
    expect(filas.first).to_be_visible()
    total = filas.count()
    ultimo = filas.nth(total - 1)
    nombre = ultimo.locator("td").nth(2).inner_text()

    ultimo.locator("[data-delete-id]").click()
    expect(page.locator("#adminMsg")).to_contain_text(re.compile(r"Producto eliminado: .+"))
    expect(filas).to_have_count(total - 1)
    expect(page.locator("#productsTable")).not_to_contain_text(nombre)


def png_minimo() -> bytes:
    def chunk(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
        + chunk(b"IEND", b"")
    )


def test_ana_cancela_un_pedido_pendiente(page: Page):
    ingresar(page, "ana", "1234")
    expect(page.locator("#accountName")).to_have_text("ana")  # sesión lista
    # Se crea un pedido pendiente nuevo para no depender de los de ejemplo.
    estado = page.evaluate("""fetch('/api/orders', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({items: [{producto_id: 'choco-8', cantidad: 1}]})
    }).then(r => r.status)""")
    assert estado == 201
    page.reload()

    boton = page.locator("[data-cancel-id]").last
    pedido = boton.get_attribute("data-cancel-id")
    fila = page.locator(f'#ordersTable tr[data-order-id="{pedido}"]')
    boton.click()

    expect(page.locator("#orderActionMsg")).to_contain_text(f"Pedido #{pedido} cancelado")
    expect(fila).to_contain_text("Cancelado")
    expect(fila.locator("[data-cancel-id]")).to_have_count(0)

    # Un pedido pagado nunca muestra el botón.
    expect(page.locator('#ordersTable tr[data-order-id="1001"] [data-cancel-id]')).to_have_count(0)


def test_ernesto_agrega_un_producto_con_imagenes(page: Page):
    ingresar(page, "ernesto", "admin123")
    expect(page.locator("#adminSection")).to_be_visible()
    nombre = f"Mousse de prueba {int(time.time())}"

    page.click("#toggleProductForm")
    # Primero se intenta guardar vacío: la página marca los errores.
    page.click("#pfGuardar")
    expect(page.locator('[data-error-for="nombre"]')).to_be_visible()
    expect(page.locator('[data-error-for="imagenes"]')).to_be_visible()

    page.fill("#pfNombre", nombre)
    page.fill("#pfCategoria", "Postres")
    page.fill("#pfPrecio", "8900")
    page.fill("#pfStock", "3")
    page.fill("#pfDescripcion", "Mousse aireado de chocolate blanco con frambuesas.")
    page.fill("#pfTags", "pruebae2e, frutal")
    page.check('input[name="alergenos"][value="lácteos"]')
    page.set_input_files("#pfImagenes", [
        {"name": "portada.png", "mimeType": "image/png", "buffer": png_minimo()},
        {"name": "detalle.png", "mimeType": "image/png", "buffer": png_minimo()},
    ])
    expect(page.locator("#pfPreviews figure")).to_have_count(2)
    page.click("#pfGuardar")

    expect(page.locator("#adminMsg")).to_contain_text(f"Producto agregado: {nombre}")
    expect(page.locator("#productForm")).to_be_hidden()
    expect(page.locator("#productsTable")).to_contain_text(nombre)

    # En el catálogo aparece con su tag, y el filtro lo encuentra.
    page.goto(f"{SITE_URL}/catalogo.php")
    page.locator("#tagFilter button", has_text="pruebae2e").click()
    tarjeta = page.locator("#productGrid article", has_text=nombre)
    expect(tarjeta).to_be_visible()
    expect(page.locator("#productGrid article")).to_have_count(1)

    # Su página muestra las dos imágenes, el stock bajo y los alérgenos.
    tarjeta.locator("a", has_text="Detalles").click()
    expect(page.locator(".product-gallery__thumbs button")).to_have_count(2)
    expect(page.locator(".stock-note")).to_contain_text("Quedan 3")
    expect(page.locator("#productRoot")).to_contain_text("contiene lácteos")


def test_sin_sesion_el_catalogo_usa_respaldo(page: Page):
    page.goto(f"{SITE_URL}/catalogo.php")
    expect(page.locator("#productGrid article").first).to_be_visible()
    assert page.evaluate("window.ChocoAPI.origenDatos") == "respaldo"
