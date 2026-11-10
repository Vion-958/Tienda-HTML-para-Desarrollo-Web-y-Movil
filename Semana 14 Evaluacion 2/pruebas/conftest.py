import sys
from pathlib import Path

# Permite importar pruebas/utiles.py, los servicios e iniciar.py.
AQUI = Path(__file__).resolve().parent
for ruta in (AQUI, AQUI.parent / "servicios", AQUI.parent):
    sys.path.insert(0, str(ruta))
