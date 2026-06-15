# Laboratorio 08 — Sistema Nacional de Bancos Cooperativos
**Sistemas Distribuidos — UNSA 2026A**

Implementación del protocolo **Two-Phase Commit (2PC)** sobre tres nodos PostgreSQL
para simular una transferencia bancaria distribuida de **S/ 25,000** desde Arequipa hacia Cusco.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    COORDINADOR 2PC                          │
│              (script Python en el host)                     │
└───────────┬──────────────────┬───────────────┬─────────────┘
            │                  │               │
     PREPARE/COMMIT      PREPARE/COMMIT     solo lectura
            │                  │               │
    ┌───────▼──────┐  ┌────────▼─────┐  ┌─────▼────────┐
    │   Arequipa   │  │    Cusco     │  │   Trujillo   │
    │  puerto 5433 │  │  puerto 5434 │  │  puerto 5435 │
    │ saldo inicial│  │ saldo inicial│  │ saldo inicial│
    │  S/100,000   │  │   S/50,000   │  │   S/75,000   │
    └──────────────┘  └──────────────┘  └──────────────┘
         ORIGEN            DESTINO         NO INVOLUCRADO
```

**Suma total constante: S/ 225,000**

---

## Requisitos previos

| Software | Versión mínima |
|---|---|
| Docker Desktop | 4.x |
| Docker Compose | 2.x |
| Python | 3.12 |

---

## Instalación y configuración

### 1. Clonar o descomprimir el proyecto

```bash
cd Laboratorio08
```

### 2. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 3. Levantar los tres nodos PostgreSQL

```bash
docker compose up -d
```

Esperar ~15 segundos a que los contenedores inicialicen. Verificar:

```bash
docker compose ps
```

Los tres servicios deben mostrar estado `healthy`.

### 4. Verificar conexiones manualmente (opcional)

```bash
# Arequipa
psql -h localhost -p 5433 -U admin -d banco_arequipa -c "SELECT * FROM cuentas;"

# Cusco
psql -h localhost -p 5434 -U admin -d banco_cusco -c "SELECT * FROM cuentas;"

# Trujillo
psql -h localhost -p 5435 -U admin -d banco_trujillo -c "SELECT * FROM cuentas;"
```

---

## Ejecución de los scripts

Todos los scripts deben ejecutarse desde el directorio `python/`:

```bash
cd python
```

### Transferencia exitosa (flujo normal 2PC)

```bash
python transfer_banco.py
```

**Salida esperada:**
```
FASE 1: PREPARE
  [arequipa] Saldo: S/ 100,000.00 → PREPARE OK
  [cusco]    PREPARE OK
FASE 2: COMMIT
  [arequipa] COMMIT PREPARED ✓
  [cusco]    COMMIT PREPARED ✓
✅ Transferencia completada exitosamente.
  Arequipa : S/  75,000.00
  Cusco    : S/  75,000.00
  Trujillo : S/  75,000.00
  TOTAL    : S/ 225,000.00
```

---

### Simulación de fallos

#### Fallo de red (Cusco no responde al PREPARE)

```bash
python simulate_failure.py --modo fallo_red
```

Simula que Cusco lanza un timeout durante el PREPARE.
Arequipa ya preparó → el coordinador ejecuta `ROLLBACK PREPARED` en Arequipa.
**Resultado: saldos sin cambios.**

#### Caída de nodo (Cusco inalcanzable)

```bash
python simulate_failure.py --modo caida_nodo
```

Simula conexión TCP fallida hacia Cusco antes del PREPARE.
El coordinador cancela antes de modificar cualquier dato.
**Resultado: saldos sin cambios.**

#### Recuperación de transacciones huérfanas

```bash
python simulate_failure.py --modo recuperacion
```

O con la herramienta de recuperación independiente:

```bash
python recovery.py --accion listar        # Ver transacciones pendientes
python recovery.py --accion rollback_todo # Limpiar todas
python recovery.py --accion verificar     # Verificar consistencia global
python recovery.py                        # Modo interactivo
```

---

## Estructura del proyecto

```
Laboratorio08/
├── docker-compose.yml        # Tres servicios PostgreSQL 16
├── .env                      # Variables de conexión y monto
├── requirements.txt          # psycopg2-binary, python-dotenv
├── python/
│   ├── config.py             # Parámetros de conexión y logging
│   ├── transfer_banco.py     # Coordinador 2PC — transferencia exitosa
│   ├── simulate_failure.py   # Simulación de fallos (3 modos)
│   └── recovery.py           # Limpieza de transacciones huérfanas
├── init/
│   ├── arequipa.sql          # Schema + datos iniciales Arequipa
│   ├── cusco.sql             # Schema + datos iniciales Cusco
│   └── trujillo.sql          # Schema + datos iniciales Trujillo
├── capturas/                 # (completar con capturas de pantalla)
└── README.md
```

---

## Diagrama de secuencia 2PC — Transferencia exitosa

```
Coordinador       Arequipa           Cusco
     │                │                │
     │──── PREPARE ──►│                │
     │                │── UPDATE ──────│ (débito)
     │                │   PREPARE TX   │
     │                │◄── VOTE OK ────│
     │──── PREPARE ───────────────────►│
     │                │                │── UPDATE (crédito)
     │                │                │   PREPARE TX
     │                │◄───────────── VOTE OK ──────│
     │                │                │
     │  (ambos OK)    │                │
     │──── COMMIT ───►│                │
     │                │── COMMIT PREPARED
     │──── COMMIT ────────────────────►│
     │                │                │── COMMIT PREPARED
     │                │                │
     │◄─── ACK ───────│                │
     │◄─── ACK ────────────────────────│
```

---

## Diagrama de secuencia 2PC — Con fallo de red en Cusco

```
Coordinador       Arequipa           Cusco
     │                │                │
     │──── PREPARE ──►│                │
     │                │   PREPARE TX ✓ │
     │◄── VOTE OK ────│                │
     │──── PREPARE ───────────────────►│
     │                │                │ ✗ TIMEOUT
     │◄───────── (sin respuesta) ──────│
     │                │                │
     │  (fallo!)      │                │
     │── ROLLBACK ───►│                │
     │                │─ ROLLBACK PREPARED
     │── ROLLBACK ────────────────────►│ (si llegó a preparar)
```

---

## Variables de entorno (.env)

| Variable | Valor | Descripción |
|---|---|---|
| `DB_USER` | `admin` | Usuario PostgreSQL |
| `DB_PASSWORD` | `admin123` | Contraseña |
| `DB_NAME_AREQUIPA` | `banco_arequipa` | BD del nodo Arequipa |
| `DB_NAME_CUSCO` | `banco_cusco` | BD del nodo Cusco |
| `DB_NAME_TRUJILLO` | `banco_trujillo` | BD del nodo Trujillo |
| `PORT_AREQUIPA` | `5433` | Puerto expuesto Arequipa |
| `PORT_CUSCO` | `5434` | Puerto expuesto Cusco |
| `PORT_TRUJILLO` | `5435` | Puerto expuesto Trujillo |
| `MONTO_TRANSFERENCIA` | `25000` | Monto en soles |

---

## Reiniciar los datos

Para volver al estado inicial (S/ 100k / 50k / 75k):

```bash
docker compose down -v
docker compose up -d
```

---

## Identificación de roles (Actividad 2)

| Rol | Entidad |
|---|---|
| **Coordinador** | Script Python `transfer_banco.py` |
| **Participante origen** | Nodo Arequipa (puerto 5433) |
| **Participante destino** | Nodo Cusco (puerto 5434) |
| **Nodo disponible** | Trujillo (puerto 5435, no involucrado) |
| **Recurso involucrado** | Tabla `cuentas` en Arequipa y Cusco |

---

## Análisis (Actividad 6)

### Impacto sobre consistencia
El protocolo 2PC garantiza que la suma `Arequipa + Cusco + Trujillo = S/ 225,000`
se mantiene en todo momento. Un fallo en cualquier fase resulta en rollback total.

### Impacto sobre disponibilidad
Durante las fases PREPARE y COMMIT, los recursos quedan bloqueados. Si el
coordinador falla entre ambas fases, los nodos permanecen en espera indefinida
(problema del bloqueo distribuido del 2PC clásico).

### Estrategias de mejora
- **3PC (Three-Phase Commit)**: agrega una fase intermedia para reducir bloqueos.
- **Saga pattern**: divide la transacción en pasos compensatorios independientes.
- **Paxos / Raft**: consenso tolerante a fallos del coordinador.

---

> **Informe técnico:** completar el archivo `informe.pdf` con capturas, análisis
> y conclusiones según la guía de laboratorio.
