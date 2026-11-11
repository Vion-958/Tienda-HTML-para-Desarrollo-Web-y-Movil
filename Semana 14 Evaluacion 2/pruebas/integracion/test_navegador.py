"""Flujos del frontend en un navegador real (Playwright)."""

import shutil
import time

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

G = "http://127.0.0.1:8000"


@pytest.fixture(scope="module")
def navegador(stack):
    if not shutil.which("php"):
        pytest.skip("Se necesita php para servir el sitio")
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(navegador):
    ctx = navegador.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    errores = []
    pg.on("pageerror", lambda e: errores.append(str(e)))
    yield pg
    ctx.close()
    assert not errores, errores


def entrar(pg, usuario, clave):
    pg.goto(f"{G}/cuenta.php")
    pg.fill("#username", usuario)
    pg.fill("#password", clave)
    pg.click("#loginBtn")
    expect(pg.locator("#accountName")).to_have_text(usuario)


def test_N01_registro_compra_y_pago_aprobado(page):
    u = f"nav{int(time.time()) % 100000}"
    page.goto(f"{G}/cuenta.php")
    page.click("#showRegister")
    page.fill("#regUsuario", u)
    page.fill("#regClave", "clave1234")
    page.fill("#regNombre", "Camila Rojas")
    page.fill("#regCorreo", f"{u}@example.com")
    page.click("#registerBtn")
    expect(page.locator("#accountName")).to_have_text(u)
    expect(page.locator("#ordersMsg")).to_contain_text("no tienes pedidos")

    page.goto(f"{G}/catalogo.php")
    page.locator("#productGrid article").first.locator("button", has_text="Agregar").click()
    page.goto(f"{G}/carrito.php")
    expect(page.locator("#contactPanel")).to_be_visible()
    page.fill("#apellido", "Rojas")
    page.fill("#telefono", "+56922223333")
    page.fill("#direccion", "Los Leones 100")
    page.fill("#comuna", "Providencia")
    page.check("#aceptaTerminos")
    page.click("#confirmarBtn")

    page.wait_for_url("**/checkout/**")
    expect(page.locator("body")).to_contain_text("ENTORNO DE PRUEBA")
    page.click("#aprobar")
    page.wait_for_url("**/cuenta.php**")
    expect(page.locator("#orderActionMsg")).to_contain_text("Pago aprobado")
    expect(page.locator("#ordersTable tbody tr").first).to_contain_text("Pagado")


def test_N02_carrito_pide_sesion(page):
    page.goto(f"{G}/catalogo.php")
    page.locator("#productGrid article").first.locator("button", has_text="Agregar").click()
    page.goto(f"{G}/carrito.php")
    expect(page.locator("#loginPanel")).to_be_visible()
    expect(page.locator("#contactPanel")).to_be_hidden()
    # El checkout ya no pide datos de tarjeta.
    expect(page.locator("#numeroTarjeta")).to_have_count(0)


def test_N03_cliente_cancela_y_no_ve_administracion(page):
    entrar(page, "ana", "1234")
    expect(page.locator("#adminSection")).to_be_hidden()
    expect(page.locator("#adminOrdersSection")).to_be_hidden()
    fila = page.locator('#ordersTable tr[data-order-id="1003"]')
    fila.locator("button", has_text="Cancelar").click()
    expect(page.locator("#orderActionMsg")).to_contain_text("Pedido #1003 cancelado")
    expect(fila).to_contain_text("Cancelado")


def test_N04_admin_gestiona_pedidos_y_productos(page):
    entrar(page, "ernesto", "admin123")
    fila = page.locator('#adminOrdersTable tr[data-admin-order-id="1002"]')
    fila.locator("button", has_text="Confirmar transferencia").click()
    expect(page.locator("#adminOrdersMsg")).to_contain_text("Transferencia confirmada")
    fila.locator("button", has_text="Preparar").click()
    expect(fila).to_contain_text("En preparaci")

    page.locator('#productsTable tr[data-product-id="choco-3"] button', has_text="Editar").click()
    page.fill("#pfPrecio", "18900")
    page.click("#pfGuardar")
    expect(page.locator("#adminMsg")).to_contain_text("Producto actualizado")
    expect(page.locator('#productsTable tr[data-product-id="choco-3"]')).to_contain_text("$18.900")
