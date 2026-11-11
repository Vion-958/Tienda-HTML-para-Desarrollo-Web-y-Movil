"""Prueba de carga reproducible. Uso: python pruebas/carga/carga.py [--usuarios N] [--segundos S]"""

import argparse
import asyncio
import json
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path

import httpx
import psutil

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import iniciar  # noqa: E402

G = "http://127.0.0.1:8000"
OBJETIVOS = {"catalogo": 500, "mis_pedidos_graphql": 800, "crear_y_cancelar_pedido": 1000}  # p95 en ms

CONSULTA = {"query": "{ misPedidos(tamano: 10) { total pedidos { id estado total pago { estado } "
                     "items { nombre cantidad producto { imagen } } } } }"}


async def escenario(nombre, usuarios, segundos, accion, cookies=None):
    latencias, errores, fin = [], 0, time.perf_counter() + segundos

    async def usuario(i):
        nonlocal errores
        async with httpx.AsyncClient(base_url=G, timeout=10, cookies=cookies) as c:
            while time.perf_counter() < fin:
                t0 = time.perf_counter()
                try:
                    ok = await accion(c, i)
                except httpx.HTTPError:
                    ok = False
                latencias.append((time.perf_counter() - t0) * 1000)
                errores += 0 if ok else 1

    inicio = time.perf_counter()
    await asyncio.gather(*(usuario(i) for i in range(usuarios)))
    dur = time.perf_counter() - inicio
    lat = sorted(latencias)
    pct = lambda p: lat[min(len(lat) - 1, int(len(lat) * p))]  # noqa: E731
    return {
        "escenario": nombre, "usuarios": usuarios, "segundos": round(dur, 1), "solicitudes": len(lat),
        "throughput_rps": round(len(lat) / dur, 1), "p50_ms": round(pct(0.50), 1), "p95_ms": round(pct(0.95), 1),
        "p99_ms": round(pct(0.99), 1), "media_ms": round(statistics.mean(lat), 1), "errores": errores,
        "tasa_error": round(errores / max(len(lat), 1) * 100, 2), "objetivo_p95_ms": OBJETIVOS[nombre],
    }


async def catalogo(c, i):
    return (await c.get("/api/products?tamano=20")).status_code == 200


async def mis_pedidos(c, i):
    r = await c.post("/api/graphql", json=CONSULTA)
    return r.status_code == 200 and "errors" not in r.json()


async def crear_y_cancelar(c, i):
    r = await c.post("/api/orders", json={"items": [{"producto_id": f"choco-{1 + i % 15}", "cantidad": 1}],
                                          "entrega": "retiro", "metodo_pago": "tarjeta"})
    if r.status_code != 201:
        return False
    return (await c.post(f"/api/orders/{r.json()['order']['id']}/cancel")).status_code == 200


def medir_recursos(procesos):
    datos = {}
    for nombre, pr in procesos.items():
        try:
            p = psutil.Process(pr.pid)
            datos[nombre] = {"cpu_s": round(sum(p.cpu_times()[:2]), 2), "rss_mb": round(p.memory_info().rss / 2**20, 1)}
        except psutil.Error:
            pass
    return datos


async def correr(usuarios, segundos):
    async with httpx.AsyncClient(base_url=G) as c:
        await c.post("/auth/login", json={"username": "ana", "password": "1234"})
        cookies = {"session_token": c.cookies.get("session_token")}
    resultados = []
    for nombre, accion, ck in [("catalogo", catalogo, None), ("mis_pedidos_graphql", mis_pedidos, cookies),
                               ("crear_y_cancelar_pedido", crear_y_cancelar, cookies)]:
        print(f"  {nombre}...", flush=True)
        resultados.append(await escenario(nombre, usuarios, segundos, accion, ck))
    return resultados


def informe(resultados, recursos_antes, recursos_despues, usuarios, segundos):
    fila = "| {escenario} | {usuarios} | {solicitudes} | {throughput_rps} | {p50_ms} | {p95_ms} | {p99_ms} | {tasa_error}% | {objetivo_p95_ms} | {ok} |"
    lineas = [
        "# Resultados de la prueba de carga", "",
        f"- Fecha: {time.strftime('%Y-%m-%d %H:%M')}",
        f"- Entorno: {platform.system()} {platform.release()}, Python {platform.python_version()}, "
        f"{psutil.cpu_count()} CPU, {round(psutil.virtual_memory().total / 2**30, 1)} GB RAM",
        f"- Carga: {usuarios} usuarios concurrentes, {segundos} s por escenario, todo en una maquina (localhost)",
        "- Datos: catalogo de prueba de 15 productos, SQLite por servicio",
        "- Tipo: medicion (no proyeccion)", "",
        "| Escenario | Usuarios | Solicitudes | Throughput (req/s) | p50 ms | p95 ms | p99 ms | Errores | Objetivo p95 ms | Cumple |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in resultados:
        lineas.append(fila.format(ok="si" if r["p95_ms"] <= r["objetivo_p95_ms"] and r["tasa_error"] < 1 else "no", **r))
    lineas += ["", "## CPU y memoria por proceso", "",
               "| Proceso | CPU usada en la prueba (s) | Memoria RSS al final (MB) |", "|---|---|---|"]
    for n, d in recursos_despues.items():
        cpu = round(d["cpu_s"] - recursos_antes.get(n, {}).get("cpu_s", 0), 2)
        lineas.append(f"| {n} | {cpu} | {d['rss_mb']} |")
    return "\n".join(lineas) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--usuarios", type=int, default=20)
    ap.add_argument("--segundos", type=int, default=20)
    args = ap.parse_args()

    datos = Path(tempfile.mkdtemp(prefix="carga_"))
    env = iniciar.entornos(iniciar.generar())
    env["gateway"]["GATEWAY_LIMITE_FACTOR"] = "1000"
    for n, var in [("auth", "AUTH_DB"), ("inventory", "INVENTORY_DB"), ("orders", "ORDERS_DB"),
                   ("clients", "CLIENTS_DB"), ("payments", "PAYMENTS_DB")]:
        env[n][var] = str(datos / f"{n}.db")
    print("Levantando el sistema...")
    procesos = iniciar.arrancar(env, list(iniciar.ORDEN), carpeta_logs=datos / "logs", mostrar=lambda *_: None)
    try:
        antes = medir_recursos(procesos)
        resultados = asyncio.run(correr(args.usuarios, args.segundos))
        despues = medir_recursos(procesos)
    finally:
        iniciar.detener(procesos)

    md = informe(resultados, antes, despues, args.usuarios, args.segundos)
    (RAIZ / "docs").mkdir(exist_ok=True)
    (RAIZ / "docs" / "resultados_carga.md").write_text(md, encoding="utf-8")
    (RAIZ / "docs" / "resultados_carga.json").write_text(json.dumps(resultados, indent=2), encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
