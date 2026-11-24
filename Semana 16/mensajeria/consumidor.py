"""Consumidor STOMP: procesa los pedidos de la cola y responde ACK o NACK."""

import argparse
import json
import re
import time
import xml.etree.ElementTree as ET
from decimal import Decimal

import stomp

DESTINO = "/queue/chocomania.pedidos"
LARGO_FIJO = 44  # contrato: ID[6] CLIENTE[20] PRODUCTO[8] MONTO[10]
CAMPOS = ("id", "cliente", "producto", "monto")
PATRON_PRODUCTO = re.compile(r"^choco-\d{1,2}$")


def interpretar(cuerpo: str, headers: dict):
    """Deserializa el mensaje. Devuelve (formato, contenido)."""
    formato = headers.get("x-formato", "").lower()
    tipo_mime = headers.get("content-type", "").lower()

    # Si el productor no dijo el formato, se deduce del tipo MIME.
    if not formato:
        if "application/json" in tipo_mime:
            formato = "json"
        elif "application/xml" in tipo_mime or "text/xml" in tipo_mime:
            formato = "xml"
        else:
            formato = "texto"

    if formato == "texto":
        return formato, cuerpo

    if formato == "fijo":
        if len(cuerpo) != LARGO_FIJO:
            raise ValueError(f"Registro de ancho fijo invalido: {len(cuerpo)} caracteres, se esperan {LARGO_FIJO}")
        identificador = cuerpo[0:6]
        cliente = cuerpo[6:26].rstrip()
        producto = cuerpo[26:34].rstrip()
        monto = cuerpo[34:44]
        if not (
            identificador.isascii() and identificador.isdigit()
            and monto[:7].isdigit() and monto[7] == "." and monto[8:].isdigit()
        ):
            raise ValueError("Campos numericos de ancho fijo invalidos")
        pedido = {"id": identificador, "cliente": cliente, "producto": producto, "monto": monto}

    elif formato == "json":
        pedido = json.loads(cuerpo)
        if not isinstance(pedido, dict):
            raise ValueError("El JSON debe ser un objeto pedido")

    elif formato == "xml":
        raiz = ET.fromstring(cuerpo)
        if raiz.tag != "pedido":
            raise ValueError("El nodo raiz de XML debe ser <pedido>")
        pedido = {elemento.tag: elemento.text for elemento in raiz}

    else:
        raise ValueError(f"Formato no soportado: {formato}")

    validar_pedido(pedido)
    return formato, pedido


def validar_pedido(pedido: dict) -> None:
    """Reglas de negocio minimas de ChocoMania, iguales para todos los formatos."""
    faltantes = [c for c in CAMPOS if not pedido.get(c)]
    if faltantes:
        raise ValueError(f"Al pedido le faltan campos: {', '.join(faltantes)}")
    if not PATRON_PRODUCTO.match(str(pedido["producto"])):
        raise ValueError(f"Producto desconocido: {pedido['producto']}")
    if Decimal(str(pedido["monto"])) < 0:
        raise ValueError("El monto no puede ser negativo")


def resumen(pedido: dict) -> str:
    monto = Decimal(str(pedido["monto"]))
    pesos = f"${monto:,.0f}".replace(",", ".")
    return f"Pedido #{pedido['id']} de {pedido['cliente']}: {pedido['producto']} por {pesos}"


class Escuchador(stomp.ConnectionListener):
    def __init__(self, conexion):
        self.conexion = conexion

    def on_error(self, frame):
        print(f"ERROR del broker: {frame.body}")

    def on_disconnected(self):
        print("Conexion STOMP cerrada")

    def on_message(self, frame):
        # En STOMP 1.2 el broker manda el id a confirmar en el header "ack".
        ack_id = frame.headers.get("ack") or frame.headers.get("message-id")
        try:
            formato, contenido = interpretar(frame.body, frame.headers)
            print(f"\n[RECIBIDO] formato={formato}")
            if isinstance(contenido, str):
                print(contenido)
            else:
                print(json.dumps(contenido, ensure_ascii=False, indent=2))
                print(f"-> {resumen(contenido)}")
            self.conexion.ack(id=ack_id)
        except Exception as exc:
            print(f"\n[MENSAJE NO VALIDO] {exc}")
            print(f"   cuerpo: {frame.body!r}")
            self.conexion.nack(id=ack_id)


def main():
    parser = argparse.ArgumentParser(description="Consumidor STOMP de pedidos ChocoMania")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=61613)
    parser.add_argument("--usuario", default="demo")
    parser.add_argument("--clave", default="demo123")
    args = parser.parse_args()

    conexion = stomp.Connection12([(args.host, args.port)], vhost="/")
    conexion.set_listener("pedidos", Escuchador(conexion))
    try:
        conexion.connect(args.usuario, args.clave, wait=True)
        conexion.subscribe(
            destination=DESTINO,
            id="lector-pedidos",
            ack="client-individual",
            # ActiveMQ entrega de a un mensaje hasta recibir su ACK/NACK
            headers={"activemq.prefetchSize": "1"},
        )
        print(f"Escuchando {DESTINO}. Presiona Ctrl+C para salir.")
        while conexion.is_connected():
            time.sleep(0.5)
    except stomp.exception.ConnectFailedException:
        print(f"No se pudo conectar al broker en {args.host}:{args.port}. Esta ActiveMQ arriba?")
    except KeyboardInterrupt:
        print("\nDeteniendo consumidor...")
    finally:
        if conexion.is_connected():
            conexion.disconnect()


if __name__ == "__main__":
    main()
