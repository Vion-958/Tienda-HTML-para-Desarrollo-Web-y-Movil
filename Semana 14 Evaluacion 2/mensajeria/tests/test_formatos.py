"""Contrato de mensajes: lo que serializa el productor lo lee el consumidor."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from consumidor import LARGO_FIJO, interpretar, resumen  # noqa: E402
from productor import construir_mensaje  # noqa: E402

PEDIDO = {"id": "123", "cliente": "Ana Perez", "producto": "choco-3", "monto": "12990"}


def ida_y_vuelta(formato, pedido=PEDIDO, texto="hola"):
    cuerpo, mime = construir_mensaje(formato, pedido, texto)
    return cuerpo, interpretar(cuerpo, {"x-formato": formato, "content-type": mime})


def test_texto_viaja_igual():
    _, (formato, contenido) = ida_y_vuelta("texto", texto="Hola desde ChocoMania")
    assert formato == "texto"
    assert contenido == "Hola desde ChocoMania"


def test_fijo_respeta_el_contrato_de_44_caracteres():
    cuerpo, (_, pedido) = ida_y_vuelta("fijo")
    assert len(cuerpo) == LARGO_FIJO
    assert cuerpo == "000123Ana Perez           choco-3 0012990.00"
    assert pedido == {"id": "000123", "cliente": "Ana Perez", "producto": "choco-3", "monto": "0012990.00"}


@pytest.mark.parametrize("formato", ["json", "xml"])
def test_json_y_xml_conservan_los_campos(formato):
    _, (_, pedido) = ida_y_vuelta(formato)
    assert pedido == PEDIDO


def test_json_admite_tildes():
    pedido = dict(PEDIDO, cliente="Bego\u00f1a Mu\u00f1oz")
    _, (_, recibido) = ida_y_vuelta("json", pedido)
    assert recibido["cliente"] == "Bego\u00f1a Mu\u00f1oz"


def test_formato_se_deduce_del_mime_si_falta_el_header():
    cuerpo, mime = construir_mensaje("xml", PEDIDO, "")
    formato, _ = interpretar(cuerpo, {"content-type": mime})
    assert formato == "xml"


@pytest.mark.parametrize(
    "pedido, error",
    [
        (dict(PEDIDO, id="1234567"), "hasta 6 digitos"),
        (dict(PEDIDO, cliente="Bego\u00f1a Mu\u00f1oz"), "ASCII"),
        (dict(PEDIDO, cliente="X" * 21), "20 caracteres"),
        (dict(PEDIDO, monto="-1"), "entre 0"),
        (dict(PEDIDO, monto="10000000"), "entre 0"),
    ],
)
def test_productor_rechaza_lo_que_no_cabe_en_el_ancho_fijo(pedido, error):
    with pytest.raises(ValueError, match=error):
        construir_mensaje("fijo", pedido, "")


@pytest.mark.parametrize(
    "cuerpo, headers, error",
    [
        ("000123Ana", {"x-formato": "fijo"}, "ancho fijo invalido"),
        ("ABC123Ana Perez           choco-3 0012990.00", {"x-formato": "fijo"}, "numericos"),
        ("<orden><id>1</id></orden>", {"x-formato": "xml"}, "<pedido>"),
        ('{"id": "1", "cliente": "Ana"}', {"x-formato": "json"}, "faltan campos"),
        ('{"id":"1","cliente":"Ana","producto":"torta","monto":"1"}', {"x-formato": "json"}, "Producto desconocido"),
        ("hola", {"x-formato": "yaml"}, "no soportado"),
    ],
)
def test_consumidor_rechaza_mensajes_invalidos(cuerpo, headers, error):
    with pytest.raises(ValueError, match=error):
        interpretar(cuerpo, headers)


def test_resumen_en_pesos_chilenos():
    assert resumen(PEDIDO) == "Pedido #123 de Ana Perez: choco-3 por $12.990"
