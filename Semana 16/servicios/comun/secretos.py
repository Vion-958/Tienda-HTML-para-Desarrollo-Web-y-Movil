"""Secretos de cada servicio leidos desde Vault (KV v2), con cache y gracia si Vault cae."""

import logging
import os
import threading
import time

import httpx

from comun.bitacora import evento


class SinSecretos(Exception):
    """El servicio no tiene acceso a sus secretos."""


class Secretos:
    def __init__(self, ruta: str, addr: str | None = None, token: str | None = None,
                 ttl: float | None = None, gracia: float | None = None):
        self.ruta = ruta
        self.addr = (addr or os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")).rstrip("/")
        self.token = token if token is not None else os.getenv("VAULT_TOKEN", "")
        self.ttl = float(ttl if ttl is not None else os.getenv("VAULT_CACHE_TTL", "30"))
        self.gracia = float(gracia if gracia is not None else os.getenv("VAULT_GRACIA", "300"))
        if not self.token:
            raise RuntimeError(f"Falta VAULT_TOKEN para leer secret/{ruta}")
        self.datos: dict | None = None
        self.version: int | None = None
        self.leido = 0.0
        self.intento = 0.0
        self._lock = threading.Lock()

    @property
    def url(self) -> str:
        return f"{self.addr}/v1/secret/data/{self.ruta}"

    def _vigente(self, ahora: float, forzar: bool) -> bool:
        if self.datos is None:
            return False
        if forzar:
            # Un refresco forzado como maximo por segundo.
            return ahora - self.intento < 1
        return ahora - self.leido < self.ttl

    def _guardar(self, r: httpx.Response, ahora: float):
        r.raise_for_status()
        cuerpo = r.json()["data"]
        nueva = cuerpo.get("metadata", {}).get("version")
        if self.version is not None and nueva != self.version:
            evento("Vault: secret/%s cambio de version %s a %s", self.ruta, self.version, nueva)
        elif self.version is None:
            evento("Vault: leido secret/%s v%s (cache de %.0f s)", self.ruta, nueva, self.ttl)
        self.datos, self.version, self.leido = dict(cuerpo["data"]), nueva, ahora

    def _fallo(self, ahora: float, error: Exception) -> dict:
        if self.datos is not None and ahora - self.leido < self.gracia:
            evento("Vault no responde (%s); se usa la cache de secret/%s", type(error).__name__, self.ruta,
                   nivel=logging.WARNING)
            return self.datos
        raise SinSecretos(f"Sin acceso a secret/{self.ruta}") from error

    def todos(self, forzar: bool = False) -> dict:
        with self._lock:
            ahora = time.monotonic()
            if self._vigente(ahora, forzar):
                return self.datos
            self.intento = ahora
            try:
                self._guardar(httpx.get(self.url, headers={"X-Vault-Token": self.token}, timeout=3), ahora)
            except (httpx.HTTPError, KeyError, ValueError) as e:
                return self._fallo(ahora, e)
            return self.datos

    async def atodos(self, cliente: httpx.AsyncClient, forzar: bool = False) -> dict:
        ahora = time.monotonic()
        if self._vigente(ahora, forzar):
            return self.datos
        self.intento = ahora
        try:
            self._guardar(await cliente.get(self.url, headers={"X-Vault-Token": self.token}, timeout=3), ahora)
        except (httpx.HTTPError, KeyError, ValueError) as e:
            return self._fallo(ahora, e)
        return self.datos

    def get(self, clave: str, forzar: bool = False) -> str:
        valor = self.todos(forzar).get(clave)
        if not valor:
            raise SinSecretos(f"Falta {clave} en secret/{self.ruta}")
        return valor

    def disponible(self) -> bool:
        try:
            self.todos()
            return True
        except SinSecretos:
            return False
