import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from main import app, construir_pdf, moneda  # noqa: E402

FACTURA = {
    "numero_factura": "FAC-2025-001",
    "fecha_emision": "2025-08-15",
    "empresa": {
        "nombre": "Tech Solutions S.L.",
        "direccion": "Calle Mayor 123\n28013 Madrid",
        "telefono": "+34 912 345 678",
        "email": "contacto@techsolutions.es",
    },
    "cliente": {
        "nombre": "Industrias López & Hijos <S.A.>",
        "direccion": "Av. Libertad 456, Barcelona",
        "telefono": "+34 933 456 789",
    },
    "detalle": [
        {"descripcion": "Consultoría", "cantidad": 2, "precio_unitario": 500.0, "total": 1000.0},
        {"descripcion": "Soporte", "cantidad": 1, "precio_unitario": 250.0, "total": 250.0},
    ],
    "subtotal": 1250.0,
    "impuesto": 262.5,
    "total": 1512.5,
}

FETCH = {"X-Requested-With": "fetch"}


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def respuesta_backend(status, json=None):
    return Mock(status_code=status, json=Mock(return_value=json))


def test_moneda():
    assert moneda(1512.5) == "1.512,50 €"


def test_construir_pdf_escapa_caracteres():
    pdf = construir_pdf(FACTURA).getvalue()
    assert pdf.startswith(b"%PDF")


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Generador de Facturas" in response.data


def test_health(client):
    assert client.get("/health").json["status"] == "ok"


@patch("main.requests.get")
def test_generar_pdf_vista_previa(mock_get, client):
    mock_get.return_value = respuesta_backend(200, FACTURA)
    response = client.post("/generar-pdf", data={"id_factura": "FAC-2025-001"}, headers=FETCH)
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert "attachment" not in response.headers.get("Content-Disposition", "")
    assert mock_get.call_args.args[0].endswith("/facturas/v1/FAC-2025-001")


@patch("main.requests.get")
def test_generar_pdf_descarga(mock_get, client):
    mock_get.return_value = respuesta_backend(200, FACTURA)
    response = client.post("/generar-pdf", data={"id_factura": "FAC-2025-001", "descargar": "1"})
    assert response.headers["Content-Disposition"].startswith("attachment")
    assert "factura_FAC-2025-001.pdf" in response.headers["Content-Disposition"]


def test_generar_pdf_sin_id(client):
    response = client.post("/generar-pdf", data={"id_factura": "  "}, headers=FETCH)
    assert response.status_code == 400


@patch("main.requests.get")
def test_generar_pdf_id_invalido(mock_get, client):
    mock_get.return_value = respuesta_backend(422)
    response = client.post("/generar-pdf", data={"id_factura": "FAC 001"}, headers=FETCH)
    assert response.status_code == 400
    assert "inválido" in response.json["error"]


@patch("main.requests.get")
def test_generar_pdf_no_encontrada(mock_get, client):
    mock_get.return_value = respuesta_backend(404)
    response = client.post("/generar-pdf", data={"id_factura": "FAC-404"}, headers=FETCH)
    assert response.status_code == 404


@patch("main.requests.get", side_effect=requests.exceptions.ConnectionError)
def test_generar_pdf_backend_caido(mock_get, client):
    response = client.post("/generar-pdf", data={"id_factura": "FAC-2025-001"}, headers=FETCH)
    assert response.status_code == 503


@patch("main.requests.get", side_effect=requests.exceptions.ConnectionError)
def test_generar_pdf_formulario_clasico_redirige(mock_get, client):
    response = client.post("/generar-pdf", data={"id_factura": "FAC-2025-001"})
    assert response.status_code == 302
