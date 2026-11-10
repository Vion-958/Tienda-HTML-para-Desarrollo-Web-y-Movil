"""Productor STOMP: publica pedidos en la cola de ActiveMQ."""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

import stomp

DESTINO = "/queue/chocomania.pedidos"
FORMATOS = ["texto", "fijo", "xml", "json"]
PATRON_PRODUCTO = re.compile(r"^choco-\d{1,2}$")


def construir_mensaje(formato: str, pedido: dict, texto: str) -> tuple[str, str]:
    """Serializa el pedido en el formato pedido. Devuelve (cuerpo, tipo MIME)."""
    if formato == "texto":
        return texto, "text/plain; charset=utf-8"

    if formato == "fijo":
        identificador = str(pedido["id"])
        cliente = str(pedido["cliente"])
        producto = str(pedido["producto"])
        monto = Decimal(pedido["monto"])
        monto_campo = f"{monto:010.2f}"
        if not (identificador.isascii() and identificador.isdigit() and len(identificador) <= 6):
            raise ValueError("En formato fijo, --id debe tener hasta 6 digitos ASCII")
        if len(cliente) > 20 or not cliente.isascii():
            raise ValueError("En formato fijo, --cliente admite hasta 20 caracteres ASCII (sin tildes)")
        if len(producto) > 8 or not producto.isascii():
            raise ValueError("En formato fijo, --producto admite hasta 8 caracteres ASCII")
        if monto < 0 or len(monto_campo) != 10:
            raise ValueError("En formato fijo, --monto debe estar entre 0 y 9999999.99")
        cuerpo = f"{identificador.zfill(6)}{cliente:<20}{producto:<8}{monto_campo}"
        return cuerpo, "text/plain; charset=utf-8"

    if formato == "json":
        return json.dumps(pedido, ensure_ascii=False), "application/json; charset=utf-8"

    if formato == "xml":
        raiz = ET.Element("pedido")
        for clave, valor in pedido.items():
            ET.SubElement(raiz, clave).text = str(valor)
        return ET.tostring(raiz, encoding="unicode"), "application/xml; charset=utf-8"

    raise ValueError(f"Formato desconocido: {formato}")


def main():
    parser = argparse.ArgumentParser(description="Productor STOMP de pedidos ChocoMania")
    parser.add_argument("--formato", choices=FORMATOS, required=True)
    parser.add_argument("--mensaje", default="Hola desde el productor de ChocoMania")
    parser.add_argument("--id", default="123")
    parser.add_argument("--cliente", default="Ana Perez")
    parser.add_argument("--producto", default="choco-3")
    parser.add_argument("--monto", default="12990")
    parser.add_argument("--repetir", type=int, default=1,
                        help="cuantos mensajes enviar; el id avanza en 1 por cada uno")
    parser.add_argument("--crudo", help="envia este cuerpo tal cual, sin validar (para probar errores)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=61613)
    parser.add_argument("--usuario", default="demo")
    parser.add_argument("--clave", default="demo123")
    args = parser.parse_args()

    try:
        monto = Decimal(args.monto)
        if not monto.is_finite():
            raise InvalidOperation
    except InvalidOperation:
        parser.error(f"Monto no valido: {args.monto}")

    if args.formato != "texto" and args.crudo is None and not PATRON_PRODUCTO.match(args.producto):
        parser.error(f"Producto no valido: {args.producto} (se espera choco-1 .. choco-15)")
    if args.repetir < 1:
        parser.error("--repetir debe ser 1 o mas")
    if args.formato != "texto" and args.crudo is None and not args.id.isdigit():
        parser.error("--id debe ser numerico")

    # Si un mensaje no cumple el contrato no se envia ninguno.
    mensajes = []
    if args.crudo is not None:
        mensajes = [(args.crudo, "text/plain; charset=utf-8")] * args.repetir
    for n in range(args.repetir if args.crudo is None else 0):
        identificador = str(int(args.id) + n) if args.id.isdigit() else args.id
        pedido = {
            "id": identificador,
            "cliente": args.cliente,
            "producto": args.producto,
            "monto": str(monto),
        }
        try:
            mensajes.append(construir_mensaje(args.formato, pedido, args.mensaje))
        except ValueError as exc:
            parser.error(str(exc))

    conexion = stomp.Connection12([(args.host, args.port)], vhost="/")
    try:
        conexion.connect(args.usuario, args.clave, wait=True)
        for cuerpo, mime in mensajes:
            conexion.send(
                destination=DESTINO,
                body=cuerpo,
                headers={
                    "content-type": mime,
                    "x-formato": args.formato,
                    "persistent": "true",  # el broker lo guarda aunque se reinicie
                },
            )
            print(f"Mensaje enviado a {DESTINO} (formato={args.formato}):\n{cuerpo}")
    except stomp.exception.ConnectFailedException:
        print(f"No se pudo conectar al broker en {args.host}:{args.port}. Esta ActiveMQ arriba?")
        raise SystemExit(1)
    finally:
        if conexion.is_connected():
            conexion.disconnect()


if __name__ == "__main__":
    main()
