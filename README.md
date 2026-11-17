# Generador de Facturas

Sistema completo de generación de facturas, utilizando [FastAPI](https://fastapi.tiangolo.com/) para el backend que genera datos sintéticos con [Faker](https://faker.readthedocs.io/), y proporciona un frontend web con [Flask](https://flask.palletsprojects.com/) para generar PDFs de las facturas con [ReportLab](https://docs.reportlab.com/reportlab/userguide/ch1_intro/).

## Autor

- William Angulo - @WilliamAngulo04

## Descripción del Proyecto

Este proyecto consta de dos servicios principales:

- **Backend API**: FastAPI que genera datos sintéticos de facturas utilizando Faker
- **Frontend Web**: Aplicación web que consume el API y genera PDFs descargables de las facturas

## Arquitectura

```
┌────────────────┐          ┌───────────────┐
│  Frontend Web  │ ───────> │  Backend API  │
│  puerto 3000   │   HTTP   │  puerto 8000  │
│  Flask + RLab  │ <─────── │  FastAPI      │
└────────────────┘          └───────────────┘
```

## Estructura del Proyecto

```
factura-generator/
├── docker-compose.yml          # Orquestación de servicios
├── README.md                   # Este archivo
├── backend/                    # Servicio API
│   ├── Dockerfile
│   ├── requirements-dev.txt    # Dependencias para pruebas
│   ├── tests/                  # Pruebas con pytest
│   └── app/
│       ├── main.py            # API FastAPI
│       └── requirements.txt
└── frontend/                   # Servicio Frontend
    ├── Dockerfile
    ├── requirements-dev.txt    # Dependencias para pruebas
    ├── tests/                  # Pruebas con pytest
    └── app/
        ├── main.py            # Servidor web Flask
        ├── requirements.txt
        ├── static/            # Archivos estáticos
        │   ├── css/
        │   │    └── style.css
        │   └── js/
        │        └── app.js
        └── templates/         # Plantillas HTML
            └── index.html
```

## Inicio Rápido

### Prerrequisitos

- Docker
- Docker Compose

### Instalación y Ejecución

1. **Clonar el repositorio**

```bash
git clone https://github.com/UR-CC/lpa2-taller2.git
cd lpa2-taller2
```

2. **Construir y levantar los servicios**

```bash
docker-compose up --build
```

3. **Acceder a la aplicación**

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Documentación API: `http://localhost:8000/docs`

## Backend (API de Facturas)

El backend expone un *endpoint* que genera facturas sintéticas:

**Endpoint:** `GET /facturas/v1/{numero_factura}`

**Ejemplo de uso:**

```bash
curl http://localhost:8000/facturas/v1/FAC-2025-001
```

El número de factura debe tener entre 1 y 50 caracteres y contener solo letras, números, guiones (`-`) y guiones bajos (`_`). Si no cumple el formato, el API responde `422 Unprocessable Entity`.

Los datos son **deterministas**: el número de factura se usa como semilla, por lo que la misma factura siempre devuelve los mismos datos.

**Ejemplo de la Respuesta:**

```json
{
  "numero_factura": "FAC-2025-001",
  "fecha_emision": "2025-08-15",
  "empresa": {
    "nombre": "Tech Solutions S.L.",
    "direccion": "Calle Mayor 123, Madrid",
    "telefono": "+34 912 345 678",
    "email": "contacto@techsolutions.es"
  },
  "cliente": {
    "nombre": "Industrias López",
    "direccion": "Av. Libertad 456, Barcelona",
    "telefono": "+34 933 456 789"
  },
  "detalle": [...],
  "subtotal": 1250.00,
  "impuesto": 262.50,
  "total": 1512.50
}
```

## Frontend (Generador de PDF)

El frontend proporciona una interfaz web donde:

1. El usuario ingresa un número de factura
2. Se consulta el API backend
3. Se genera un PDF profesional con los datos
4. El usuario puede descargar o imprimir el PDF

### Tecnologías del Frontend

- **Flask**: Servidor web
- **Gunicorn**: Servidor WSGI usado en el contenedor
- **ReportLab**: Generación del PDF
- **Jinja2**: Motor de plantillas
- **HTML/CSS/JavaScript**: Interfaz de usuario

### Modificar el Frontend

- Editar `frontend/app/main.py` para crear la lógica de la consulta del API y generación del PDF
- Editar `frontend/app/templates/index.html` para modificar el diseño de la interfaz Web
- Editar `frontend/app/static/css/style.css` para modificar los estilos 
- Editar `frontend/app/static/js/app.js` para ajustar lógica de la interfaz, si se requiere

## Configuración Avanzada

### Variables de Entorno

Puedes modificar el `docker-compose.yml` para añadir variables de entorno:

```yaml
environment:
  - BACKEND_API_URL=http://backend:8000  # URL del API de facturas
  - DEBUG=false                          # Modo depuración de Flask (solo desarrollo local)
  - SECRET_KEY=cambiar-esto              # Clave para los mensajes flash
```

### Puertos Personalizados

Modificar en `docker-compose.yml`:

```yaml
ports:
  - "8080:3000"  # Frontend en puerto 8080
  - "9000:8000"  # Backend en puerto 9000
```

## Uso de la Aplicación

1. **Abrir el navegador** en `http://localhost:3000`
2. **Ingresar número de factura** (ej: FAC-2025-001, INV-2024-123, etc.)
3. **Hacer clic en "Generar Factura"**
4. **Ver la vista previa** de la factura
5. **Descargar PDF** haciendo clic en "Descargar PDF"

## Comandos Docker Útiles

```bash
# Levantar servicios
docker-compose up

# Levantar servicios en segundo plano
docker-compose up -d

# Reconstruir imágenes
docker-compose up --build

# Ver logs
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend
docker-compose logs -f frontend

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Reiniciar un servicio específico
docker-compose restart backend
```

## 🧪 Testing

### Probar el Backend

```bash
# Endpoint de salud
curl http://localhost:8000/

# Generar factura
curl http://localhost:8000/facturas/v1/TEST-001 | jq

# Usando httpie (más legible)
http http://localhost:8000/facturas/v1/TEST-001
```

### Pruebas automatizadas

Cada servicio tiene pruebas con `pytest` (el frontend simula el backend, no necesita tenerlo levantado):

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
pytest

# Frontend
cd frontend
pip install -r requirements-dev.txt
pytest
```

### Probar el Frontend manualmente

1. Navegar a `http://localhost:3000`
2. Probar diferentes números de factura
3. Verificar generación correcta de PDFs
4. Comprobar el endpoint de salud: `curl http://localhost:3000/health`

## API Documentation

La documentación interactiva de Swagger está disponible en:
- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)

