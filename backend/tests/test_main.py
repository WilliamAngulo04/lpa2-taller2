import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from main import app, TASA_IVA  # noqa: E402

client = TestClient(app)


def test_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_factura_estructura():
    response = client.get("/facturas/v1/FAC-2025-001")
    assert response.status_code == 200
    factura = response.json()
    assert factura["numero_factura"] == "FAC-2025-001"
    assert {"nombre", "direccion", "telefono", "email"} <= factura["empresa"].keys()
    assert {"nombre", "direccion", "telefono"} <= factura["cliente"].keys()
    assert 1 <= len(factura["detalle"]) <= 5


def test_factura_totales_cuadran():
    factura = client.get("/facturas/v1/INV-2024-123").json()
    for item in factura["detalle"]:
        assert item["total"] == pytest.approx(item["cantidad"] * item["precio_unitario"], abs=0.01)
    assert factura["subtotal"] == pytest.approx(sum(i["total"] for i in factura["detalle"]), abs=0.01)
    assert factura["impuesto"] == pytest.approx(factura["subtotal"] * TASA_IVA, abs=0.01)
    assert factura["total"] == pytest.approx(factura["subtotal"] + factura["impuesto"], abs=0.01)


def test_factura_determinista():
    primera = client.get("/facturas/v1/TEST-001").json()
    segunda = client.get("/facturas/v1/TEST-001").json()
    otra = client.get("/facturas/v1/TEST-002").json()
    assert primera == segunda
    assert primera != otra


@pytest.mark.parametrize("numero", ["FAC 001", "FAC%26001", "a" * 51, "FAC.001"])
def test_factura_numero_invalido(numero):
    response = client.get(f"/facturas/v1/{numero}")
    assert response.status_code == 422
