"""
Matriz de pruebas del laboratorio (Paso 10 y sección 17 de la guía).

Ejecuta las pruebas automáticas contra el Gateway y el backend y muestra
el código HTTP obtenido frente al esperado.

Uso (con el entorno virtual del Gateway activo):
    python pruebas.py
    python pruebas.py --token nuevo-token-789        (después de rotar en Vault)

Variables opcionales:
    GATEWAY_URL   (por defecto http://127.0.0.1:8000)
    BACKEND_URL   (por defecto http://192.168.1.20:9000)
"""

import argparse
import os

import httpx

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:8000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://192.168.1.20:9000")


def probar(nombre, esperado, metodo, url, headers=None, json=None):
    try:
        r = httpx.request(metodo, url, headers=headers, json=json, timeout=10.0)
        codigo = r.status_code
        detalle = r.text[:90].replace("\n", " ")
    except httpx.RequestError as e:
        codigo = None
        detalle = f"sin conexión ({type(e).__name__})"

    ok = codigo == esperado
    marca = "OK  " if ok else "FALLA"
    print(f"[{marca}] {nombre:<46} esperado {esperado}  obtenido {codigo}  {detalle}")
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", default="student-token-123",
                        help="token de cliente vigente en Vault")
    parser.add_argument("--token-anterior", default=None,
                        help="token ya rotado, que debería devolver 401")
    args = parser.parse_args()

    bearer = {"Authorization": f"Bearer {args.token}"}

    print(f"Gateway: {GATEWAY_URL}")
    print(f"Backend: {BACKEND_URL}\n")

    resultados = [
        probar("1. Gateway sin token", 401, "GET", f"{GATEWAY_URL}/api/products"),
        probar("2. Gateway con token falso", 401, "GET", f"{GATEWAY_URL}/api/products",
               headers={"Authorization": "Bearer token-incorrecto"}),
        probar("3. Gateway con token válido (/products)", 200, "GET",
               f"{GATEWAY_URL}/api/products", headers=bearer),
        probar("3b. Token válido, producto por id", 200, "GET",
               f"{GATEWAY_URL}/api/products/choco-1", headers=bearer),
        probar("3c. Token válido (/orders)", 200, "GET",
               f"{GATEWAY_URL}/api/orders", headers=bearer),
        probar("3d. Token válido, crear pedido (POST)", 201, "POST",
               f"{GATEWAY_URL}/api/orders", headers=bearer,
               json={"cliente": "Prueba", "items": [{"producto_id": "choco-5", "cantidad": 2}]}),
        probar("4. Acceso directo al backend sin secreto", 403, "GET",
               f"{BACKEND_URL}/products"),
        probar("8. Backend con secreto interno incorrecto", 403, "GET",
               f"{BACKEND_URL}/products", headers={"X-Gateway-Secret": "secreto-falso"}),
        probar("Extra: cliente intenta inyectar el secreto", 401, "GET",
               f"{GATEWAY_URL}/api/products",
               headers={"X-Gateway-Secret": "gateway-api-secret-456"}),
    ]

    if args.token_anterior:
        resultados.append(
            probar("7. Token anterior tras rotar en Vault", 401, "GET",
                   f"{GATEWAY_URL}/api/products",
                   headers={"Authorization": f"Bearer {args.token_anterior}"}))

    print(f"\n{sum(resultados)}/{len(resultados)} pruebas con el resultado esperado.")
    print("\nPruebas manuales:")
    print("  5. Apague Vault (docker stop vault-dev) y repita la 3 -> 500 controlado")
    print("  6. Apague el backend (Ctrl+C en HOST B) y repita la 3 -> 502")


if __name__ == "__main__":
    main()
