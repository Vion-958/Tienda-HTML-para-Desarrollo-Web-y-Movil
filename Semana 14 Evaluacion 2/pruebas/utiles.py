import importlib.util
import json
import sys
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SERV = RAIZ / "servicios"
sys.path.insert(0, str(SERV))
sys.path.insert(0, str(RAIZ))

# Credenciales de prueba (ficticias, solo para estas pruebas).
TOKENS = {n: f"token-de-prueba-{n}-0123456789" for n in ("gateway", "orders", "payments", "graphql")}


def callers(*nombres):
    return json.dumps({n: TOKENS[n] for n in nombres})


def cargar_servicio(carpeta: str, monkeypatch, env: dict):
    """Importa servicios/<carpeta>/app.py con un entorno propio (base temporal)."""
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    spec = importlib.util.spec_from_file_location(f"app_{carpeta}_{uuid.uuid4().hex}", SERV / carpeta / "app.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def cab(caller="gateway", user=None, roles="user"):
    h = {"X-Service-Name": caller, "X-Service-Token": TOKENS[caller]}
    if user:
        h.update({"X-User-Id": user, "X-User-Name": user.lower(), "X-User-Roles": roles})
    return h


ANA = "USR-001"
ERNESTO = "USR-003"
