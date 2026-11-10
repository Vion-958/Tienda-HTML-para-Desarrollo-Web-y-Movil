"""Pasarela de pago sandbox: simula un proveedor externo."""

import hashlib
import hmac
import html
import json
import os
import secrets
import time

import httpx
from fastapi import FastAPI, Form, Header, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Pasarela sandbox")
API_KEY = os.getenv("PASARELA_API_KEY", "")
WEBHOOK_SECRET = os.getenv("PASARELA_WEBHOOK_SECRET", "")
PUBLIC_URL = os.getenv("PASARELA_PUBLIC_URL", "http://127.0.0.1:9300")
REINTENTOS = 3

if not (API_KEY and WEBHOOK_SECRET):
    raise RuntimeError("Faltan PASARELA_API_KEY y PASARELA_WEBHOOK_SECRET")

CHECKOUTS: dict[str, dict] = {}


class NuevoCheckout(BaseModel):
    monto: int = Field(gt=0, le=100_000_000)
    moneda: str = Field(pattern="^CLP$")
    referencia: str = Field(min_length=3, max_length=40)
    url_retorno: str = Field(max_length=300)
    url_aviso: str = Field(max_length=300)


def _autorizar(authorization: str):
    if not secrets.compare_digest(authorization.encode(), f"Bearer {API_KEY}".encode()):
        raise HTTPException(status_code=401, detail="API key inv\u00e1lida")


def firmar(cuerpo: bytes, t: int | None = None) -> str:
    t = t or int(time.time())
    firma = hmac.new(WEBHOOK_SECRET.encode(), f"{t}.".encode() + cuerpo, hashlib.sha256).hexdigest()
    return f"t={t},v1={firma}"


def enviar_aviso(chk: dict, evento_id: str | None = None) -> int:
    cuerpo = json.dumps({
        "evento_id": evento_id or "evt_" + secrets.token_hex(8),
        "checkout_id": chk["id"],
        "referencia": chk["referencia"],
        "estado": chk["estado"],
        "monto": chk["monto"],
    }).encode()
    ultimo = 0
    for intento in range(REINTENTOS):
        try:
            r = httpx.post(chk["url_aviso"], content=cuerpo, timeout=5,
                           headers={"Content-Type": "application/json", "X-Pasarela-Firma": firmar(cuerpo)})
            ultimo = r.status_code
            if 200 <= r.status_code < 300:
                break
        except httpx.HTTPError:
            ultimo = 0
        time.sleep(0.5 * (intento + 1))
    chk["avisos"].append(ultimo)
    return ultimo


@app.get("/health")
def health():
    return {"status": "OK", "service": "pasarela-sandbox"}


@app.post("/v1/checkouts", status_code=201)
def crear(datos: NuevoCheckout, authorization: str = Header(default="")):
    _autorizar(authorization)
    cid = "chk_" + secrets.token_hex(8)
    CHECKOUTS[cid] = dict(datos.model_dump(), id=cid, estado="pendiente", avisos=[])
    return {"checkout_id": cid, "url": f"{PUBLIC_URL}/checkout/{cid}"}


@app.get("/checkout/{cid}", response_class=HTMLResponse)
def pagina(cid: str):
    chk = CHECKOUTS.get(cid)
    if not chk:
        raise HTTPException(status_code=404, detail="Checkout no encontrado")
    monto = f"${chk['monto']:,}".replace(",", ".")
    ref = html.escape(chk["referencia"])
    if chk["estado"] != "pendiente":
        cuerpo = f"<p>Este pago ya fue <strong>{chk['estado']}</strong>.</p>"
    else:
        cuerpo = f"""
        <form method="post" action="/checkout/{cid}/resultado">
          <button name="resultado" value="aprobado" class="ok" id="aprobar">Aprobar pago</button>
          <button name="resultado" value="rechazado" class="no" id="rechazar">Rechazar pago</button>
        </form>"""
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>SandboxPay</title>
<style>
body{{font-family:system-ui,sans-serif;background:#eef1f5;margin:0;padding:24px;color:#1d2433}}
.card{{max-width:420px;margin:40px auto;background:#fff;border-radius:12px;padding:28px;box-shadow:0 4px 20px #0001}}
.tag{{display:inline-block;background:#ffe9a8;color:#6b4e00;font-weight:700;font-size:12px;padding:3px 8px;border-radius:6px}}
h1{{font-size:22px;margin:12px 0}} .monto{{font-size:32px;font-weight:800;margin:8px 0 18px}}
button{{width:100%;padding:14px;border:0;border-radius:8px;font-size:16px;font-weight:700;margin-top:10px;cursor:pointer}}
.ok{{background:#1f7a4d;color:#fff}} .no{{background:#e5e7eb;color:#1d2433}} small{{color:#5b6475}}
</style></head><body><main class="card">
<span class="tag">ENTORNO DE PRUEBA</span><h1>SandboxPay</h1>
<p>Comercio: ChocoMania &middot; Referencia: {ref}</p><div class="monto">{monto} CLP</div>
{cuerpo}
<p><small>Simulador de proveedor externo. No se solicitan ni almacenan datos de tarjeta.</small></p>
</main></body></html>"""


@app.post("/checkout/{cid}/resultado")
def resultado(cid: str, resultado: str = Form(...)):
    chk = CHECKOUTS.get(cid)
    if not chk:
        raise HTTPException(status_code=404, detail="Checkout no encontrado")
    if resultado not in ("aprobado", "rechazado"):
        raise HTTPException(status_code=400, detail="Resultado inv\u00e1lido")
    if chk["estado"] == "pendiente":
        chk["estado"] = resultado
        enviar_aviso(chk)
    sep = "&" if "?" in chk["url_retorno"] else "?"
    return RedirectResponse(f"{chk['url_retorno']}{sep}pago={chk['estado']}", status_code=303)


@app.post("/v1/checkouts/{cid}/reenviar")
def reenviar(cid: str, evento_id: str | None = None, authorization: str = Header(default="")):
    """Reenvia el aviso (simula un proveedor que avisa dos veces)."""
    _autorizar(authorization)
    chk = CHECKOUTS.get(cid)
    if not chk or chk["estado"] == "pendiente":
        raise HTTPException(status_code=404, detail="Checkout sin resultado")
    return {"status": enviar_aviso(chk, evento_id)}
