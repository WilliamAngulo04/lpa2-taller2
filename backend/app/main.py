from fastapi import FastAPI
from faker import Faker
import hashlib
import random

app = FastAPI(title="API de Facturas Fake", version="1.0")


@app.get("/")
def health():
    return {"status": "ok", "servicio": "API de Facturas"}


@app.get("/facturas/v1/{numero_factura}")
def get_factura(numero_factura: str):
    # Semilla derivada del número de factura: la misma factura siempre genera los mismos datos
    semilla = int(hashlib.sha256(numero_factura.encode("utf-8")).hexdigest(), 16) % (2**32)
    fake = Faker("es_ES")
    fake.seed_instance(semilla)
    rng = random.Random(semilla)

    # Generar datos falsos para empresa y cliente
    empresa = {
        "nombre": fake.company(),
        "direccion": fake.address(),
        "telefono": fake.phone_number(),
        "email": fake.company_email()
    }

    cliente = {
        "nombre": fake.company(),
        "direccion": fake.address(),
        "telefono": fake.phone_number()
    }

    # Generar entre 1 y 5 ítems de detalle
    detalle = []
    for _ in range(rng.randint(1, 5)):
        cantidad = rng.randint(1, 10)
        precio_unitario = round(rng.uniform(50, 500), 2)
        total = round(cantidad * precio_unitario, 2)
        detalle.append({
            "descripcion": fake.catch_phrase(),
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "total": total
        })

    subtotal = round(sum(item["total"] for item in detalle), 2)
    impuesto = round(subtotal * 0.21, 2)  # IVA 21%
    total = round(subtotal + impuesto, 2)

    factura = {
        "numero_factura": numero_factura,
        "fecha_emision": str(fake.date_between(start_date="-1y", end_date="today")),
        "empresa": empresa,
        "cliente": cliente,
        "detalle": detalle,
        "subtotal": subtotal,
        "impuesto": impuesto,
        "total": total
    }

    return factura
