"""
Prueba end-to-end en el navegador (Playwright), con el sistema arriba.

    pip install pytest-playwright
    playwright install chromium
    pytest e2e/test_frontend.py --headed      (sin --headed corre oculto)

Variable opcional: SITE_URL (por defecto http://localhost:8000)
"""

import os
import re

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


def test_ana_inicia_sesion_y_no_puede_eliminar(page: Page):
    ingresar(page, "ana", "1234")

    expect(page.locator("#accountName")).to_have_text("ana")
    expect(page.locator("[data-account-link]")).to_have_text("Hola, ana")
    expect(page.locator("#ordersTable tbody tr").first).to_be_visible()
    expect(page.locator("#productsTable tbody tr").first).to_be_visible()

    # La cookie existe, pero JavaScript no puede leerla (HttpOnly).
    cookies = {c["name"]: c for c in page.context.cookies()}
    assert cookies["session_token"]["httpOnly"] is True
    assert "session_token" not in page.evaluate("document.cookie")
    assert page.evaluate("Object.keys(localStorage).join(',')").find("token") == -1

    # Operación de administrador: el servidor la rechaza.
    page.locator("[data-delete-id]").first.click()
    expect(page.locator("#adminMsg")).to_contain_text("403")

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

    filas = page.locator("#productsTable tbody tr")
    expect(filas.first).to_be_visible()
    total = filas.count()
    ultimo = filas.nth(total - 1)
    nombre = ultimo.locator("td").nth(1).inner_text()

    ultimo.locator("[data-delete-id]").click()
    expect(page.locator("#adminMsg")).to_contain_text(re.compile(r"eliminado.*200"))
    expect(filas).to_have_count(total - 1)
    expect(page.locator("#productsTable")).not_to_contain_text(nombre)


def test_sin_sesion_el_catalogo_usa_respaldo(page: Page):
    page.goto(f"{SITE_URL}/catalogo.php")
    expect(page.locator("#productGrid article").first).to_be_visible()
    assert page.evaluate("window.ChocoAPI.origenDatos") == "respaldo"
