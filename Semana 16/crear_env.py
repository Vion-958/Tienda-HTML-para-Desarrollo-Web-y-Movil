"""Crea el .env de docker compose con valores aleatorios. Uso: python crear_env.py"""

import re
import secrets
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


def main():
    destino = RAIZ / ".env"
    if destino.exists() and "--forzar" not in sys.argv:
        sys.exit(".env ya existe. Usa --forzar para reemplazarlo (y luego: docker compose down -v).")
    plantilla = (RAIZ / ".env.example").read_text(encoding="utf-8")
    texto = re.sub(r"=reemplazar$", lambda _: "=" + secrets.token_urlsafe(24), plantilla, flags=re.M)
    destino.write_text(texto, encoding="utf-8")
    print(f"Listo: .env con {len(re.findall(r'^[A-Z_]+=', texto, re.M))} valores aleatorios")


if __name__ == "__main__":
    main()
