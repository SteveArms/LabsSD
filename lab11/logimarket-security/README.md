# LogiMarket Perú S.A.C. — Sistema de Seguridad para Microservicios

Laboratorio 11 — Seguridad Informática en Sistemas Distribuidos
Escuela Profesional de Ingeniería de Sistemas — UNSA

Implementación de un **API Gateway** de seguridad en Flask que resuelve los incidentes reportados por LogiMarket Perú S.A.C. (accesos no autorizados, interceptación de tráfico, exposición de datos, falta de auditoría y credenciales compartidas), cubriendo las Actividades 2, 3, 4 y 5 de la guía de laboratorio.

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `app.py` | API Gateway (autenticación, MFA, JWT, rate limiting, auditoría) |
| `portal.html` | Portal web cliente de ejemplo que consume la API |
| `diagrama_componentes_autenticacion.png` | Actividad 2 — arquitectura de autenticación |
| `diagrama_secuencia_autenticacion.png` | Actividad 2 — flujo de login + MFA |
| `diagrama_tecnico_proteccion_apis.png` | Actividad 4 — arquitectura de protección de APIs |
| `diagrama_flujo_sistema_auditoria.png` | Actividad 5 — esquema de monitoreo y auditoría |

## Características implementadas

- **Autenticación segura** (Actividad 2): login con `bcrypt`, MFA simulado con `pyotp` (TOTP), JWT con expiración y rol embebido.
- **Seguridad de comunicaciones** (Actividad 3): servidor Flask sobre HTTPS con certificado autofirmado generado con OpenSSL.
- **Protección de APIs** (Actividad 4): Gateway único que valida JWT y aplica Rate Limiting (5 req/min por IP) antes de reenviar a los microservicios simulados de inventario, pagos y logística.
- **Auditoría** (Actividad 5): registro de eventos en `audit.log` (formato JSON) con timestamp, usuario, IP y resultado de cada acción.

## Requisitos

- Python 3.10 o superior
- OpenSSL (para generar el certificado)
- (Opcional) Postman, curl o navegador web para probar los endpoints

## 1. Preparar el entorno

```bash
# Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd <carpeta_del_repositorio>

# Crear entorno virtual
python3 -m venv .venv

# Activar entorno virtual
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# Instalar dependencias
pip install flask pyjwt bcrypt pyotp flask-limiter flask-cors
```

## 2. Generar el certificado autofirmado (Actividad 3)

Este paso es obligatorio: el servidor no arranca sin `cert.pem` y `key.pem` en la misma carpeta que `app.py`.

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/C=PE/ST=Arequipa/L=Arequipa/O=LogiMarket Peru SAC/OU=TI/CN=localhost"
```

Verificar el certificado generado (opcional):

```bash
openssl x509 -in cert.pem -noout -subject -issuer -dates -fingerprint -sha256
```

> `cert.pem` y `key.pem` **no se suben al repositorio** (agrégalos a tu `.gitignore` local si los regeneras); cada persona que clone el proyecto debe generar los suyos con el comando anterior.

## 3. Ejecutar el servidor

```bash
python app.py
```

Deberías ver en consola:

```
======================================================================
 LogiMarket - API Gateway de Seguridad
======================================================================
Usuarios de prueba:
  admin  / Admin#2026   (rol: admin)
  jperez / Jperez#2026  (rol: user)
Los códigos MFA se imprimirán aquí en consola durante /login.
======================================================================
 * Running on https://127.0.0.1:5000
```

El servidor queda escuchando en `https://127.0.0.1:5000`. Déjalo corriendo y abre **otra terminal** para las pruebas.

## 4. Probar con el Portal Web (`portal.html`)

1. Con el servidor corriendo, abre `portal.html` directamente en el navegador (doble clic).
2. Acepta la advertencia de "certificado no confiable" (es esperado: es un certificado autofirmado, no emitido por una CA pública).
3. Inicia sesión con `admin` / `Admin#2026`.
4. Revisa la consola donde corre `app.py` para ver el código MFA impreso.
5. Ingresa el código y accede al panel para consultar inventario, pagos o logística.

## 5. Probar con curl

```bash
# 1) Login (paso 1) — el código MFA se imprime en la consola del servidor
curl -sk -X POST https://127.0.0.1:5000/login -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin#2026"}'

# 2) Verificar MFA (paso 2) con el código mostrado en consola
curl -sk -X POST https://127.0.0.1:5000/verify-mfa -H "Content-Type: application/json" \
  -d '{"mfa_token":"<MFA_TOKEN>","codigo":"<CODIGO_TOTP>"}'

# 3) Perfil protegido
curl -sk https://127.0.0.1:5000/profile -H "Authorization: Bearer <ACCESS_TOKEN>"

# 4) Endpoints del gateway (microservicios simulados)
curl -sk https://127.0.0.1:5000/api/inventario -H "Authorization: Bearer <ACCESS_TOKEN>"
curl -sk https://127.0.0.1:5000/api/pagos      -H "Authorization: Bearer <ACCESS_TOKEN>"
curl -sk https://127.0.0.1:5000/api/logistica  -H "Authorization: Bearer <ACCESS_TOKEN>"

# 5) Actualizar inventario (solo rol admin, queda registrado en audit.log)
curl -sk -X POST https://127.0.0.1:5000/api/inventario/actualizar \
  -H "Authorization: Bearer <ACCESS_TOKEN>" -H "Content-Type: application/json" \
  -d '{"sku":"SKU-003","stock":50}'

# 6) Probar Rate Limiting (6 peticiones seguidas -> la 6ta responde 429)
for i in 1 2 3 4 5 6; do curl -sk -o /dev/null -w "%{http_code}\n" \
  https://127.0.0.1:5000/api/logistica -H "Authorization: Bearer <ACCESS_TOKEN>"; done
```

## 6. Verificar el canal cifrado (Actividad 3)

```bash
# Detalle del handshake TLS con curl
curl -sk -v https://127.0.0.1:5000/api/pagos

# Verificación directa del certificado y cifrado con OpenSSL
echo | openssl s_client -connect 127.0.0.1:5000
```

Debe mostrar `SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384` y el aviso `self-signed certificate` (esperado, ya que no se usó una CA pública).

## 7. Revisar la auditoría (Actividad 5)

Cada acción (login, MFA, accesos, cambios de inventario, bloqueos por rate limit) queda registrada en `audit.log`, generado automáticamente en la misma carpeta al ejecutar el servidor:

```bash
cat audit.log
```

Ejemplo de entrada:

```json
{"timestamp": "2026-07-04T21:38:16.997226Z", "usuario": "admin", "ip": "127.0.0.1", "accion": "login", "resultado": "EXITO_CREDENCIALES_MFA_PENDIENTE"}
```

## Usuarios de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin#2026` | admin |
| `jperez` | `Jperez#2026` | user |

## Notas

- No se usa base de datos real: usuarios, inventario, pagos y logística son diccionarios en memoria, tal como pide la guía.
- Los datos se reinician cada vez que se reinicia el servidor.
- `cert.pem`, `key.pem` y `audit.log` se generan localmente y no deben subirse al repositorio.
