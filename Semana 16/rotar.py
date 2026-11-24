"""Rota credenciales en Vault sin reiniciar. Uso: python rotar.py orders inventory | --todas"""

import argparse
import json
import secrets
import sys
import time

from iniciar import LLAMADAS, SESION, ClienteVault


def sesion() -> tuple[ClienteVault, float]:
    if not SESION.exists():
        raise SystemExit("No hay una sesion activa. Inicia el sistema con: python iniciar.py")
    d = json.loads(SESION.read_text(encoding="utf-8"))
    return ClienteVault(d["addr"], d["token"]), float(d.get("ttl", 30))


def rotar(v: ClienteVault, pares: list[tuple[str, str]], ttl: float, mostrar=print) -> dict:
    """Fase 1: el servicio acepta la nueva y la vieja. Fase 2, tras el TTL: solo la nueva."""
    validos = {(a, b) for b, ls in LLAMADAS.items() for a in ls}
    for par in pares:
        if par not in validos:
            raise SystemExit(f"{par[0]} no llama a {par[1]}. Pares validos: "
                             + ", ".join(f"{a} {b}" for a, b in sorted(validos)))
    nuevas = {}
    for llamador, servicio in pares:
        nueva = secrets.token_urlsafe(32)
        destino, origen = v.leer(servicio), v.leer(llamador)
        vieja = destino[f"llamador_{llamador}"].split(",")[0]
        destino[f"llamador_{llamador}"] = f"{nueva},{vieja}"
        mostrar(f"[1/3] secret/{servicio} v{v.escribir(servicio, destino)}: acepta la credencial nueva de {llamador} y la anterior")
        origen[f"token_{servicio}"] = nueva
        mostrar(f"[2/3] secret/{llamador} v{v.escribir(llamador, origen)}: {llamador} usa la credencial nueva")
        nuevas[(llamador, servicio)] = nueva

    espera = ttl + 2
    mostrar(f"      esperando {espera:.0f} s a que los servicios refresquen su cache...")
    time.sleep(espera)

    for (llamador, servicio), nueva in nuevas.items():
        destino = v.leer(servicio)
        destino[f"llamador_{llamador}"] = nueva
        mostrar(f"[3/3] secret/{servicio} v{v.escribir(servicio, destino)}: la credencial anterior de {llamador} "
                f"deja de servir en menos de {ttl:.0f} s")
    return nuevas


def main():
    p = argparse.ArgumentParser(description="Rota credenciales entre servicios en Vault")
    p.add_argument("llamador", nargs="?")
    p.add_argument("servicio", nargs="?")
    p.add_argument("--todas", action="store_true", help="rota todas las credenciales entre servicios")
    args = p.parse_args()
    v, ttl = sesion()
    if args.todas:
        pares = [(a, b) for b, ls in LLAMADAS.items() for a in ls]
    elif args.llamador and args.servicio:
        pares = [(args.llamador, args.servicio)]
    else:
        p.print_help()
        sys.exit(1)
    rotar(v, pares, ttl)
    print("Listo: ningun servicio se reinicio y el codigo no cambio.")


if __name__ == "__main__":
    main()
