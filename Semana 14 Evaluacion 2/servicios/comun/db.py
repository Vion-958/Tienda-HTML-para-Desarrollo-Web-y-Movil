"""Acceso a SQLite: cada servicio tiene su propia base."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


class BaseDatos:
    def __init__(self, ruta: str, esquema: Path, datos_iniciales: Path | None = None):
        self.ruta = ruta
        nueva = ruta == ":memory:" or not Path(ruta).exists()
        if ruta != ":memory:":
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        # ":memory:" usa una conexion compartida (pruebas).
        self._memoria = (
            sqlite3.connect(ruta, check_same_thread=False, isolation_level=None) if ruta == ":memory:" else None
        )
        with self.conexion() as con:
            con.executescript(esquema.read_text(encoding="utf-8"))
            if nueva and datos_iniciales and datos_iniciales.exists():
                con.executescript(datos_iniciales.read_text(encoding="utf-8"))

    def _abrir(self) -> sqlite3.Connection:
        if self._memoria is not None:
            return self._memoria
        con = sqlite3.connect(self.ruta, timeout=10, isolation_level=None)
        con.execute("PRAGMA journal_mode=WAL")
        return con

    @contextmanager
    def conexion(self):
        con = self._abrir()
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
        finally:
            if self._memoria is None:
                con.close()

    @contextmanager
    def transaccion(self):
        """BEGIN IMMEDIATE: bloquea escrituras concurrentes (stock, pagos)."""
        with self.conexion() as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                yield con
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
