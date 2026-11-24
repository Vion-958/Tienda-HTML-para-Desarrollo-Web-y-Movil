"""Levanta ChocoMania. Uso: python iniciar.py [--vault-docker] [--postgres URL] [--reiniciar-datos] [--sin-php]"""

import argparse
import json
import os
import secrets
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SERV = RAIZ / "servicios"
LOGS = RAIZ / "logs"
SESION = RAIZ / ".vault-sesion.json"
IMAGEN_VAULT = "hashicorp/vault:1.17"
CONTENEDOR_VAULT = "chocomania-vault"

PUERTOS = {
    "vault": 8200, "auth": 8100, "inventory": 9101, "orders": 9102, "clients": 9103,
    "payments": 9104, "graphql": 9200, "pasarela": 9300, "gateway": 8000, "sitio": 8080,
}
CARPETA = {
    "auth": "auth-service", "inventory": "inventory", "orders": "orders", "clients": "clients",
    "payments": "payments", "graphql": "graphql-gateway", "pasarela": "pasarela-sandbox", "gateway": "api-gateway",
}
# Quien puede llamar a quien. Cada flecha tiene su propia credencial.
LLAMADAS = {
    "auth": ["gateway"],
    "inventory": ["gateway", "orders", "graphql"],
    "orders": ["gateway", "payments", "graphql"],
    "clients": ["gateway", "graphql"],
    "payments": ["gateway", "graphql"],
    "graphql": ["gateway"],
}
# Servicios que leen sus secretos desde Vault (la pasarela simula un proveedor externo).
CON_VAULT = ["gateway", "auth", "inventory", "orders", "clients", "payments", "graphql"]

# Servicios con base de datos propia (un esquema y un rol de PostgreSQL por servicio).
CON_BD = ["auth", "inventory", "orders", "clients", "payments"]

ORDEN = ["vault", "auth", "inventory", "clients", "orders", "payments", "pasarela", "graphql", "gateway"]


def url(nombre: str) -> str:
    return f"http://127.0.0.1:{PUERTOS[nombre]}"


# --- secretos

def generar() -> dict:
    cred = {(a, b): secrets.token_urlsafe(32) for b, llamadores in LLAMADAS.items() for a in llamadores}
    return {
        "cred": cred,
        "vault_raiz": secrets.token_urlsafe(24),
        "pasarela_key": "sk_test_" + secrets.token_urlsafe(24),
        "pasarela_webhook": "whsec_" + secrets.token_urlsafe(32),
    }


def contenido_vault(s: dict) -> dict[str, dict]:
    """Un secreto por servicio: llamador_<x> son las credenciales que acepta, token_<y> las que usa."""
    datos = {n: {} for n in CON_VAULT}
    for (a, b), token in s["cred"].items():
        datos[b][f"llamador_{a}"] = token
        datos[a][f"token_{b}"] = token
    datos["payments"].update(pasarela_api_key=s["pasarela_key"], pasarela_webhook=s["pasarela_webhook"])
    for servicio, url_bd in s.get("bd", {}).items():
        datos[servicio]["database_url"] = url_bd
    return datos


def preparar_postgres(admin_url: str, reiniciar: bool = False) -> dict[str, str]:
    """Crea un rol y un esquema por servicio. Cada rol solo ve su esquema; la URL queda en Vault."""
    import psycopg
    from psycopg import sql
    from urllib.parse import urlsplit

    u = urlsplit(admin_url)
    base, host, puerto = u.path.lstrip("/") or "postgres", u.hostname, u.port or 5432
    urls = {}
    with psycopg.connect(admin_url, autocommit=True) as c:
        for n in CON_BD:
            rol, clave = sql.Identifier(f"chocomania_{n}"), secrets.token_urlsafe(24)
            if reiniciar:
                c.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(n)))
            existe = c.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (f"chocomania_{n}",)).fetchone()
            orden = "ALTER ROLE {} WITH LOGIN PASSWORD {}" if existe else "CREATE ROLE {} LOGIN PASSWORD {}"
            c.execute(sql.SQL(orden).format(rol, sql.Literal(clave)))
            c.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}").format(sql.Identifier(n), rol))
            c.execute(sql.SQL("ALTER ROLE {} SET search_path = {}").format(rol, sql.Identifier(n)))
            urls[n] = f"postgresql://chocomania_{n}:{clave}@{host}:{puerto}/{base}"
    return urls


class ClienteVault:
    """Cliente minimo de la API HTTP de Vault (sirve para HashiCorp y para vault-local)."""

    def __init__(self, addr: str, token: str):
        self.addr, self.token = addr.rstrip("/"), token

    def pedir(self, metodo: str, ruta: str, cuerpo: dict | None = None) -> dict:
        datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
        req = urllib.request.Request(f"{self.addr}/v1/{ruta}", data=datos, method=metodo,
                                     headers={"X-Vault-Token": self.token, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            texto = r.read()
        return json.loads(texto) if texto else {}

    def leer(self, ruta: str) -> dict:
        return self.pedir("GET", f"secret/data/{ruta}")["data"]["data"]

    def escribir(self, ruta: str, datos: dict) -> int:
        return self.pedir("POST", f"secret/data/{ruta}", {"data": datos})["data"]["version"]

    def politica_lectura(self, nombre: str, ruta: str):
        regla = f'path "secret/data/{ruta}" {{ capabilities = ["read"] }}'
        self.pedir("PUT", f"sys/policies/acl/{nombre}", {"policy": regla})

    def crear_token(self, politica: str, nombre: str, token_id: str | None = None) -> str:
        cuerpo = {"policies": [politica], "display_name": nombre, "ttl": "24h", "renewable": True}
        if token_id:
            cuerpo["id"] = token_id
        return self.pedir("POST", "auth/token/create", cuerpo)["auth"]["client_token"]


def preparar_vault(addr: str, s: dict, ids: dict[str, str] | None = None) -> dict[str, str]:
    """Guarda los secretos y crea un token de solo lectura por servicio."""
    v = ClienteVault(addr, s["vault_raiz"])
    tokens = {}
    for ruta, datos in contenido_vault(s).items():
        v.escribir(ruta, datos)
        v.politica_lectura(f"chocomania-{ruta}", ruta)
        try:
            tokens[ruta] = v.crear_token(f"chocomania-{ruta}", ruta, (ids or {}).get(ruta))
        except urllib.error.HTTPError:
            # docker compose up repetido: el token con ese id ya existe en Vault.
            if not ids:
                raise
            v.pedir("POST", "auth/token/revoke", {"token": ids[ruta]})
            tokens[ruta] = v.crear_token(f"chocomania-{ruta}", ruta, ids[ruta])
    return tokens


def entornos(s: dict, tokens: dict[str, str]) -> dict[str, dict]:
    """Variables de cada proceso: solo direcciones y el token de Vault, nunca credenciales."""
    base = {"PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"}
    urls = {f"{n.upper()}_URL": url(n) for n in ("auth", "inventory", "orders", "clients", "payments", "graphql")}
    env = {n: {**base, **urls, "VAULT_ADDR": url("vault"), "VAULT_TOKEN": tokens[n]} for n in CON_VAULT}
    env["vault"] = {**base, "VAULT_TOKEN": s["vault_raiz"], "VAULT_PORT": str(PUERTOS["vault"])}
    env["payments"].update(PASARELA_URL=url("pasarela"), PUBLIC_URL=url("gateway"))
    env["gateway"]["FRONTEND_URL"] = url("sitio")
    # Proveedor externo simulado: tiene sus propias claves, fuera de nuestro Vault.
    env["pasarela"] = {**base, "PASARELA_API_KEY": s["pasarela_key"], "PASARELA_WEBHOOK_SECRET": s["pasarela_webhook"],
                       "PASARELA_PUBLIC_URL": url("pasarela")}
    return env


# --- procesos

def comando(nombre: str) -> tuple[list[str], Path]:
    if nombre == "vault":
        return [sys.executable, "vault_local.py"], RAIZ / "vault-local"
    if nombre == "sitio":
        return ["php", "-S", f"127.0.0.1:{PUERTOS['sitio']}", "-t", str(RAIZ / "chocomania-frontend")], RAIZ
    return ([sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(PUERTOS[nombre]),
             "--no-access-log"], SERV / CARPETA[nombre])


def listo(nombre: str, espera: float = 20) -> bool:
    ruta = "/v1/sys/health" if nombre == "vault" else ("/" if nombre == "sitio" else "/health")
    fin = time.time() + espera
    while time.time() < fin:
        try:
            with urllib.request.urlopen(url(nombre) + ruta, timeout=1) as r:
                if r.status < 500:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


class VaultDocker:
    """HashiCorp Vault en modo dev dentro de Docker, como en la guia del curso."""

    def __init__(self, raiz: str, log_path: Path):
        if not shutil.which("docker"):
            raise RuntimeError("No se encontro 'docker'. Instala Docker Desktop o usa el Vault local (sin --vault-docker).")
        subprocess.run(["docker", "rm", "-f", CONTENEDOR_VAULT], capture_output=True)
        r = subprocess.run(["docker", "run", "-d", "--name", CONTENEDOR_VAULT, "-p", f"127.0.0.1:{PUERTOS['vault']}:8200",
                            "-e", f"VAULT_DEV_ROOT_TOKEN_ID={raiz}", "-e", "VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200",
                            IMAGEN_VAULT], capture_output=True, text=True)
        log_path.write_text(r.stdout + r.stderr, encoding="utf-8")
        if r.returncode != 0:
            raise RuntimeError(f"Docker no pudo iniciar Vault. Revisa {log_path}")

    def poll(self):
        r = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", CONTENEDOR_VAULT],
                           capture_output=True, text=True)
        return None if r.stdout.strip() == "true" else 1

    def terminate(self):
        subprocess.run(["docker", "rm", "-f", CONTENEDOR_VAULT], capture_output=True)

    def wait(self, timeout=None):
        return 0

    kill = terminate


def arrancar(env: dict, orden: list[str], carpeta_logs: Path = LOGS, mostrar=print, procesos=None,
             vault_docker: bool = False) -> dict:
    """Inicia los procesos en orden y espera que cada uno responda."""
    carpeta_logs.mkdir(parents=True, exist_ok=True)
    procesos = {} if procesos is None else procesos
    for nombre in orden:
        if nombre == "vault" and vault_docker:
            procesos[nombre] = VaultDocker(env["vault"]["VAULT_TOKEN"], carpeta_logs / "vault.log")
        else:
            cmd, cwd = comando(nombre)
            log = open(carpeta_logs / f"{nombre}.log", "w", encoding="utf-8")
            procesos[nombre] = subprocess.Popen(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                                env={**os.environ, **env.get(nombre, {})})
        ok = listo(nombre, 40 if nombre == "vault" and vault_docker else 20)
        mostrar(f"  {'OK ' if ok else 'ERR'} {nombre:<10} {url(nombre)}")
        if not ok:
            raise RuntimeError(f"{nombre} no arranco. Revisa {carpeta_logs / (nombre + '.log')}")
    return procesos


def levantar(orden: list[str], carpeta_logs: Path = LOGS, mostrar=print, extra: dict | None = None,
             vault_docker: bool = False, postgres: str | None = None,
             reiniciar_bd: bool = False) -> tuple[dict, dict]:
    """Vault primero, despues los secretos y por ultimo los servicios con su token."""
    s = generar()
    if postgres:
        s["bd"] = preparar_postgres(postgres, reiniciar_bd)
        mostrar(f"  OK  postgres   {len(s['bd'])} esquemas, un rol por servicio")
    previos = [n for n in orden if n in ("sitio", "vault")]
    resto = [n for n in orden if n not in previos]
    procesos = {}
    try:
        arrancar({"vault": entornos(s, dict.fromkeys(CON_VAULT, ""))["vault"]}, previos, carpeta_logs, mostrar,
                 procesos, vault_docker)
        tokens = preparar_vault(url("vault"), s)
        mostrar(f"  OK  secretos   {len(tokens)} servicios con su token de solo lectura")
        env = entornos(s, tokens)
        for nombre, valores in (extra or {}).items():
            for destino in (CON_VAULT if nombre == "*" else [nombre]):
                env.setdefault(destino, {}).update(valores)
        arrancar(env, resto, carpeta_logs, mostrar, procesos)
    except (RuntimeError, OSError, urllib.error.URLError):
        detener(procesos)
        raise
    return procesos, {"secretos": s, "tokens": tokens, "env": env}


def detener(procesos: dict):
    for pr in procesos.values():
        pr.terminate()
    for pr in procesos.values():
        try:
            pr.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pr.kill()


def _interrumpir(*_):
    raise KeyboardInterrupt


def main():
    # Cerrar la terminal (SIGTERM) detiene todo igual que Ctrl+C.
    signal.signal(signal.SIGTERM, _interrumpir)
    p = argparse.ArgumentParser(description="Inicia ChocoMania (Semana 16)")
    p.add_argument("--vault-docker", action="store_true", help="usa HashiCorp Vault real en Docker")
    p.add_argument("--postgres", metavar="URL", default=os.getenv("CHOCOMANIA_POSTGRES"),
                   help="URL de administrador de PostgreSQL; sin ella cada servicio usa SQLite")
    p.add_argument("--reiniciar-datos", action="store_true", help="borra las bases y recarga los datos de prueba")
    p.add_argument("--sin-php", action="store_true", help="no levanta el servidor PHP")
    args = p.parse_args()

    if args.reiniciar_datos:
        for carpeta in CARPETA.values():
            shutil.rmtree(SERV / carpeta / "data", ignore_errors=True)
        print("Bases borradas: se recrean con los datos de prueba.")

    orden = list(ORDEN)
    if not args.sin_php:
        if shutil.which("php"):
            orden.insert(0, "sitio")
        else:
            print("AVISO: no se encontro 'php'. Levanta el sitio aparte en el puerto 8080 (o XAMPP).")

    print(f"Base de datos: {'PostgreSQL' if args.postgres else 'SQLite (una por servicio)'}")
    print(f"Vault: {'HashiCorp en Docker (' + IMAGEN_VAULT + ')' if args.vault_docker else 'local (vault-local)'}")
    procesos = {}
    try:
        try:
            procesos, info = levantar(orden, vault_docker=args.vault_docker, postgres=args.postgres,
                                      reiniciar_bd=args.reiniciar_datos)
        except (RuntimeError, OSError, urllib.error.URLError, ImportError) as e:
            print(e)
            raise SystemExit(1)
        # Para rotar.py: direccion y token raiz de esta ejecucion (se borra al detener).
        SESION.write_text(json.dumps({"addr": url("vault"), "token": info["secretos"]["vault_raiz"],
                                      "ttl": float(os.getenv("VAULT_CACHE_TTL", "30"))}), encoding="utf-8")
        print("\nChocoMania listo en  http://127.0.0.1:8000   (Ctrl+C para detener)")
        print("Usuarios: ana / 1234 (cliente)   ernesto / admin123 (admin)")
        print("Rotar una credencial: python rotar.py orders inventory")
        print("Logs de cada servicio en la carpeta logs/\n")
        while True:
            time.sleep(1)
            caidos = [n for n, pr in procesos.items() if pr.poll() is not None]
            if caidos:
                print(f"Se detuvo: {', '.join(caidos)}. Revisa logs/.")
                break
    except KeyboardInterrupt:
        print("\nDeteniendo...")
    finally:
        detener(procesos)
        SESION.unlink(missing_ok=True)
        print("Todo detenido.")


if __name__ == "__main__":
    main()
