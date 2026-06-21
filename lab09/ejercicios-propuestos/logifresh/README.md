# LogiFresh S.A. — Sistema Distribuido de Pedidos (Lab 9)

Aplicación de microservicios en **Python (FastAPI)** que implementa el caso de
LogiFresh S.A. descrito en la guía de laboratorio: distribución de alimentos
refrigerados con arquitectura distribuida.

Cada microservicio tiene su propia base de datos **PostgreSQL** independiente
(orquestadas con Docker Compose), tal como exige una arquitectura distribuida real.

## Arquitectura

```
                        ┌────────────────┐
                        │    Cliente      │
                        │ (Postman/curl)  │
                        └────────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │    PEDIDOS      │  :8000
                         │  (orquestador)  │
                         └───────┬────────┘
              ┌──────────┬───────┼───────┬──────────┐
              ▼          ▼               ▼          ▼
        ┌──────────┐┌──────────┐  ┌──────────┐┌───────────────┐
        │INVENTARIO││FACTURACION│  │TRANSPORTE││NOTIFICACIONES │
        │  :8001   ││  :8002    │  │  :8003   ││    :8004      │
        └────┬─────┘└────┬─────┘  └────┬─────┘└───────┬───────┘
             │            │             │              │
        ┌────▼────┐  ┌────▼────┐  ┌────▼────┐   ┌────▼────┐
        │ Postgres │  │ Postgres │  │ Postgres │   │ Postgres │
        └─────────┘  └─────────┘  └─────────┘   └─────────┘
```

### Servicios

| Servicio | Puerto | Responsabilidad |
|---|---|---|
| **pedidos** | 8000 | Orquesta el flujo completo: verifica stock, reserva, confirma, emite factura, programa envío y notifica. |
| **inventario** | 8001 | Catálogo de productos, reserva/confirmación/liberación de stock, historial de movimientos. |
| **facturacion** | 8002 | Emisión de facturas (idempotente por `pedido_id`), aplicación de descuentos/promociones. |
| **transporte** | 8003 | Programación de envíos, asignación de transportista, costo según refrigeración. |
| **notificaciones** | 8004 | Envío simulado de notificaciones (email/SMS), con latencia y tasa de fallo configurables. |

El **Servicio de Pedidos** es el orquestador central: al crear un pedido,
llama en cadena a los otros 4 servicios (igual que en el caso real de LogiFresh),
lo que permite luego observar y reproducir los problemas descritos en el enunciado
(stock inconsistente, facturas duplicadas, notificaciones lentas, demoras &gt;8s, etc.)
durante las Actividades 2, 3 y 4 del laboratorio.

## Requisitos

- Docker Desktop + Docker Compose
- (Opcional, para el script de seed) Python 3.10+ con `pip install httpx`

## Cómo levantar el sistema

```bash
cd logifresh
docker compose up --build
```

Esto levanta 5 bases de datos Postgres + 5 microservicios. Espera a ver los 5
mensajes `Uvicorn running on http://0.0.0.0:8000` en los logs.

Cada servicio expone documentación interactiva Swagger en:

- Pedidos:        http://localhost:8000/docs
- Inventario:     http://localhost:8001/docs
- Facturación:    http://localhost:8002/docs
- Transporte:     http://localhost:8003/docs
- Notificaciones: http://localhost:8004/docs

## Poblar datos iniciales (productos)

Con el sistema ya corriendo, en otra terminal:

```bash
pip install httpx
python seed_data.py
```

Esto crea 8 productos en el catálogo de Inventario (incluye intencionalmente
un producto con **stock = 0** y otro con **stock muy bajo**, útiles para las
pruebas funcionales de la Actividad 2).

## Flujo de uso manual (para probar la app)

### 1. Ver productos disponibles
```bash
curl http://localhost:8001/productos
```

### 2. Crear un pedido (caso exitoso)
```bash
curl -X POST http://localhost:8000/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "cliente": "Supermercados Lider SAC",
    "direccion_entrega": "Av. Ejercito 123",
    "ciudad": "Arequipa",
    "items": [
      {"sku": "LCH-001", "cantidad": 10},
      {"sku": "ARR-006", "cantidad": 5}
    ],
    "codigo_promocion": "LOGIFRESH10"
  }'
```

La respuesta incluye el pedido confirmado con `factura_id` y `envio_id`
ya generados en sus respectivos servicios.

### 3. Crear un pedido con stock insuficiente (caso de error)
```bash
curl -X POST http://localhost:8000/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "cliente": "Bodega Don Pepe",
    "direccion_entrega": "Calle Lima 45",
    "ciudad": "Arequipa",
    "items": [{"sku": "HEL-008", "cantidad": 3}]
  }'
```
Debe responder `422` con estado `RECHAZADO_SIN_STOCK` (HEL-008 tiene stock 0).

### 4. Consultar un pedido
```bash
curl http://localhost:8000/pedidos/1
```

### 5. Cancelar un pedido (libera stock, anula factura, cancela envío)
```bash
curl -X POST http://localhost:8000/pedidos/1/cancelar
```

### 6. Ver la factura generada
```bash
curl http://localhost:8002/facturas/pedido/1
```

### 7. Ver el envío programado
```bash
curl http://localhost:8003/envios/pedido/1
```

### 8. Ver notificaciones enviadas para un pedido
```bash
curl "http://localhost:8004/notificaciones?pedido_id=1"
```

### 9. Ver historial de movimientos de inventario de un SKU
```bash
curl "http://localhost:8001/inventario/movimientos?sku=LCH-001"
```

## Códigos de promoción disponibles (Facturación)

| Código | Descuento |
|---|---|
| LOGIFRESH10 | 10% |
| LOGIFRESH20 | 20% |
| BIENVENIDA5 | 5% |

## Variables útiles para simular condiciones de carga/falla (Actividades 3 y 4)

En `docker-compose.yml`, dentro del servicio `notificaciones`, puedes ajustar:

```yaml
NOTIFICACIONES_DELAY_MS: "200"        # latencia base simulada
NOTIFICACIONES_DELAY_JITTER_MS: "150" # variabilidad aleatoria adicional
NOTIFICACIONES_TASA_FALLO: "0.0"      # 0.0 a 1.0 (probabilidad de fallo)
```

Subir estos valores permite reproducir en laboratorio el síntoma reportado
por LogiFresh ("retrasos en confirmaciones por correo", "lentitud al
registrar pedidos") para usarlo en las pruebas de integración y de carga
con JMeter/k6 (Actividades 3 y 4), sin tocar código.

## Apagar el sistema

```bash
docker compose down          # detiene los contenedores
docker compose down -v       # además borra los volúmenes (datos) de Postgres
```

## Estructura del proyecto

```
logifresh/
├── docker-compose.yml
├── seed_data.py
├── README.md
└── services/
    ├── pedidos/         (orquestador)
    ├── inventario/
    ├── facturacion/
    ├── transporte/
    └── notificaciones/
        each with:
        ├── Dockerfile
        ├── requirements.txt
        └── app/
            ├── main.py        (endpoints FastAPI)
            ├── models.py      (modelos SQLAlchemy)
            ├── schemas.py     (esquemas Pydantic)
            └── database.py    (conexión DB)
```

## Próximos pasos (no incluidos aún)

Esta entrega cubre **solo la aplicación funcional**. Las Actividades 1, 2, 3,
4 y 5 de la guía (matriz de riesgos, casos de prueba, pruebas de integración,
pruebas de carga con JMeter/k6, y estrategia de mejora) se desarrollarán en
una siguiente etapa una vez validado que el sistema funciona correctamente.
