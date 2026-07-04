"""
=======================================================================
 LogiMarket Perú S.A.C. - Sistema de Seguridad para Microservicios
 Laboratorio 11 - Seguridad Informática en Sistemas Distribuidos
=======================================================================

Este archivo implementa, en un solo servidor Flask, un "API Gateway"
de seguridad que resuelve los 5 incidentes descritos en la guía:

  1. Accesos no autorizados a cuentas de clientes
        -> Autenticación con bcrypt + JWT + MFA (TOTP)  [Actividad 2]
  2. Interceptación de tráfico entre servicios
        -> Ejecución sobre HTTPS con certificado autofirmado [Actividad 3]
  3. Exposición accidental de datos personales
        -> Los "microservicios" solo devuelven datos si el JWT es válido
  4. Ausencia de mecanismos de auditoría
        -> Registro de eventos en audit.log en formato JSON [Actividad 5]
  5. Uso de credenciales compartidas por empleados
        -> Roles (admin/user) + JWT individual + Rate Limiting [Actividad 4]

Ejecución:
    python app.py

Clientes que consumen este Gateway (según el caso de LogiMarket):
    - Portal web para clientes  -> ver portal.html (cliente de ejemplo)
    - Aplicación móvil          -> consumiría el mismo contrato REST/JSON
      (no se implementa la app nativa; el Gateway ya queda listo para
      ser consumido por cualquier cliente HTTP con JWT en el header)

Requisitos (instalar antes de ejecutar):
    pip install flask pyjwt bcrypt pyotp flask-limiter flask-cors --break-system-packages
"""

import json
import time
import datetime
import functools

import bcrypt
import jwt
import pyotp
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# =======================================================================
# 0. CONFIGURACIÓN GENERAL
# =======================================================================

app = Flask(__name__)

# Habilita CORS para que el Portal Web (portal.html) y, en un caso real,
# la Aplicación móvil puedan consumir este Gateway desde otro origen
# (por ejemplo abriendo portal.html directamente en el navegador).
CORS(app)

# Clave secreta para firmar los JWT (en producción debe ir en variables
# de entorno / gestor de secretos, nunca hardcodeada).
JWT_SECRET = "cambia-esta-clave-en-produccion-2026"
JWT_ALGORITHM = "HS256"

# Duración de tokens
MFA_TOKEN_EXPIRE_SECONDS = 300      # 5 minutos para completar el MFA
ACCESS_TOKEN_EXPIRE_SECONDS = 1800  # 30 minutos de sesión

AUDIT_LOG_FILE = "audit.log"

# Rate limiting global: 5 peticiones por minuto por IP (Actividad 4)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],  # los límites se aplican por endpoint, no globales
    storage_uri="memory://",
)


# =======================================================================
# 1. "BASE DE DATOS" EN MEMORIA (no se usan BD reales, según lo pedido)
# =======================================================================

# Cada usuario tiene: contraseña hasheada con bcrypt, rol y secreto TOTP
# individual (esto además soluciona el problema de "credenciales
# compartidas": cada empleado tiene su propio secreto MFA).
def _hash(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


USERS = {
    "admin": {
        "password_hash": _hash("Admin#2026"),
        "role": "admin",
        "totp_secret": pyotp.random_base32(),
    },
    "jperez": {
        "password_hash": _hash("Jperez#2026"),
        "role": "user",
        "totp_secret": pyotp.random_base32(),
    },
}

# Tokens MFA pendientes: mfa_token -> {"username": ..., "exp": ...}
# (En un sistema real usaríamos Redis con expiración automática.)
PENDING_MFA = {}

# Inventario simulado (Actividad 4 - microservicio de inventario)
INVENTORY = {
    "SKU-001": {"nombre": "Laptop 14''", "stock": 25},
    "SKU-002": {"nombre": "Mouse inalámbrico", "stock": 120},
    "SKU-003": {"nombre": "Monitor 24''", "stock": 8},
}


# =======================================================================
# 2. AUDITORÍA (Actividad 5)
# =======================================================================

def audit_log(action: str, username: str = "anonimo", result: str = "OK", extra: dict = None):
    """
    Registra un evento de seguridad en audit.log en formato JSON (una
    línea por evento -> JSON Lines), incluyendo timestamp, usuario,
    IP y acción, tal como pide la guía.
    """
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "usuario": username,
        "ip": request.remote_addr,
        "accion": action,
        "resultado": result,
    }
    if extra:
        entry.update(extra)

    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# =======================================================================
# 3. UTILIDADES JWT Y DECORADORES DE SEGURIDAD
# =======================================================================

def generar_jwt(username: str, role: str, expire_seconds: int, extra_claims: dict = None) -> str:
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=expire_seconds),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def jwt_required(roles_permitidos=None):
    """
    Decorador que:
      - Exige header Authorization: Bearer <token>
      - Valida firma y expiración del JWT
      - Opcionalmente exige que el rol esté en roles_permitidos
      - Registra el acceso (éxito o fallo) en la auditoría
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                audit_log(f"acceso_denegado:{request.path}", result="FALLO_SIN_TOKEN")
                return jsonify({"error": "Token no proporcionado. Use: Authorization: Bearer <token>"}), 401

            token = auth_header.split(" ", 1)[1]
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            except jwt.ExpiredSignatureError:
                audit_log(f"acceso_denegado:{request.path}", result="FALLO_TOKEN_EXPIRADO")
                return jsonify({"error": "Token expirado"}), 401
            except jwt.InvalidTokenError:
                audit_log(f"acceso_denegado:{request.path}", result="FALLO_TOKEN_INVALIDO")
                return jsonify({"error": "Token inválido"}), 401

            if roles_permitidos and payload.get("role") not in roles_permitidos:
                audit_log(f"acceso_denegado:{request.path}", username=payload.get("sub"),
                          result="FALLO_ROL_INSUFICIENTE")
                return jsonify({"error": "No tiene permisos suficientes (Broken Access Control evitado)"}), 403

            # Se deja disponible el usuario autenticado para la vista
            g.user = payload
            audit_log(f"acceso_concedido:{request.path}", username=payload.get("sub"), result="OK")
            return f(*args, **kwargs)
        return wrapper
    return decorator


# =======================================================================
# 4. ACTIVIDAD 2 - AUTENTICACIÓN SEGURA (login + MFA)
# =======================================================================

@app.route("/login", methods=["POST"])
@limiter.limit("5 per minute")  # mitiga fuerza bruta / credenciales compartidas
def login():
    """
    Paso 1 del login.
    Recibe usuario y contraseña, valida con bcrypt y, si son correctos,
    genera un código TOTP (MFA) que se "envía" imprimiéndolo en la
    consola del servidor (simulación de SMS/App autenticadora) y
    devuelve un mfa_token temporal que el cliente deberá usar en
    /verify-mfa junto con el código.
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    user = USERS.get(username)
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"]):
        audit_log("login", username=username or "desconocido", result="FALLO_CREDENCIALES")
        return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

    # Genera y "envía" el código TOTP (Simulación de MFA)
    totp = pyotp.TOTP(user["totp_secret"])
    codigo_actual = totp.now()
    print(f"\n[MFA] Código de verificación para '{username}': {codigo_actual} "
          f"(válido ~30s)\n")

    mfa_token = generar_jwt(username, user["role"], MFA_TOKEN_EXPIRE_SECONDS,
                             extra_claims={"stage": "mfa_pending"})
    PENDING_MFA[mfa_token] = {
        "username": username,
        "exp": time.time() + MFA_TOKEN_EXPIRE_SECONDS,
    }

    audit_log("login", username=username, result="EXITO_CREDENCIALES_MFA_PENDIENTE")
    return jsonify({
        "message": "Credenciales válidas. Se requiere verificación MFA.",
        "mfa_token": mfa_token
    }), 200


@app.route("/verify-mfa", methods=["POST"])
@limiter.limit("10 per minute")
def verify_mfa():
    """
    Paso 2 del login.
    Recibe el mfa_token (obtenido en /login) y el código TOTP mostrado
    en consola. Si es válido, entrega el JWT final de sesión con el
    rol del usuario.
    """
    data = request.get_json(silent=True) or {}
    mfa_token = data.get("mfa_token")
    codigo = data.get("codigo")

    # 1) Validar que el mfa_token sea un JWT válido y esté pendiente
    pending = PENDING_MFA.get(mfa_token)
    if not pending or pending["exp"] < time.time():
        audit_log("verify-mfa", result="FALLO_TOKEN_MFA_INVALIDO_O_EXPIRADO")
        return jsonify({"error": "mfa_token inválido o expirado, inicie sesión nuevamente"}), 401

    try:
        payload = jwt.decode(mfa_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        audit_log("verify-mfa", result="FALLO_TOKEN_MFA_INVALIDO")
        return jsonify({"error": "mfa_token inválido"}), 401

    username = payload["sub"]
    user = USERS[username]

    # 2) Validar el código TOTP
    totp = pyotp.TOTP(user["totp_secret"])
    if not totp.verify(codigo, valid_window=1):
        audit_log("verify-mfa", username=username, result="FALLO_CODIGO_MFA_INCORRECTO")
        return jsonify({"error": "Código MFA incorrecto"}), 401

    # 3) Éxito: token de sesión definitivo + se invalida el mfa_token
    del PENDING_MFA[mfa_token]
    access_token = generar_jwt(username, user["role"], ACCESS_TOKEN_EXPIRE_SECONDS)

    audit_log("verify-mfa", username=username, result="EXITO_LOGIN_COMPLETO")
    return jsonify({
        "message": "Autenticación completa",
        "access_token": access_token,
        "role": user["role"],
        "expires_in": ACCESS_TOKEN_EXPIRE_SECONDS
    }), 200


@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    """Endpoint protegido de ejemplo: devuelve los datos del token."""
    return jsonify({
        "usuario": g.user["sub"],
        "rol": g.user["role"],
        "mensaje": "Acceso autorizado a datos de perfil"
    }), 200


# =======================================================================
# 5. ACTIVIDAD 4 - API GATEWAY (JWT + Rate Limiting + microservicios simulados)
# =======================================================================
#
# En un entorno real, estos endpoints reenviarían (proxy) la petición a
# microservicios independientes (p.ej. con requests.get() a otro puerto
# o contenedor). Aquí se simulan directamente con datos fijos en
# memoria, tal como pide la guía, pero conservando el mismo esquema de
# seguridad (Gateway como único punto de entrada, Rate Limiting, JWT).

@app.route("/api/inventario", methods=["GET"])
@limiter.limit("5 per minute")
@jwt_required(roles_permitidos=["admin", "user"])
def api_inventario():
    return jsonify({
        "servicio": "inventario",
        "atendido_por_gateway": True,
        "stock": INVENTORY
    }), 200


@app.route("/api/pagos", methods=["GET"])
@limiter.limit("5 per minute")
@jwt_required(roles_permitidos=["admin", "user"])
def api_pagos():
    return jsonify({
        "servicio": "pagos",
        "atendido_por_gateway": True,
        "transacciones_recientes": [
            {"id": "TXN-001", "monto": 150.50, "estado": "aprobado"},
            {"id": "TXN-002", "monto": 89.90, "estado": "pendiente"},
        ]
    }), 200


@app.route("/api/logistica", methods=["GET"])
@limiter.limit("5 per minute")
@jwt_required(roles_permitidos=["admin", "user"])
def api_logistica():
    return jsonify({
        "servicio": "logistica",
        "atendido_por_gateway": True,
        "envios_en_transito": [
            {"guia": "GUIA-100", "ciudad_destino": "Arequipa", "estado": "en camino"},
            {"guia": "GUIA-101", "ciudad_destino": "Lima", "estado": "entregado"},
        ]
    }), 200


@app.route("/api/inventario/actualizar", methods=["POST"])
@limiter.limit("5 per minute")
@jwt_required(roles_permitidos=["admin"])  # solo admin puede modificar (RBAC)
def api_inventario_actualizar():
    """
    Simula un cambio de inventario y lo registra en la auditoría
    (requisito explícito de la Actividad 5: 'Cambios en inventario').
    """
    data = request.get_json(silent=True) or {}
    sku = data.get("sku")
    nuevo_stock = data.get("stock")

    if sku not in INVENTORY or not isinstance(nuevo_stock, int):
        return jsonify({"error": "SKU inválido o stock no numérico"}), 400

    stock_anterior = INVENTORY[sku]["stock"]
    INVENTORY[sku]["stock"] = nuevo_stock

    audit_log("cambio_inventario", username=g.user["sub"], result="OK", extra={
        "sku": sku,
        "stock_anterior": stock_anterior,
        "stock_nuevo": nuevo_stock
    })

    return jsonify({
        "message": f"Stock de {sku} actualizado",
        "stock_anterior": stock_anterior,
        "stock_nuevo": nuevo_stock
    }), 200


# =======================================================================
# 6. MANEJO DE ERRORES (incluye 429 de Rate Limiting)
# =======================================================================

@app.errorhandler(429)
def rate_limit_exceeded(e):
    audit_log("rate_limit_excedido", result="BLOQUEADO", extra={"detalle": str(e.description)})
    return jsonify({
        "error": "Demasiadas solicitudes. Intente nuevamente en unos segundos.",
        "detalle": str(e.description)
    }), 429


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint no encontrado"}), 404


# =======================================================================
# 7. PUNTO DE ENTRADA - Actividad 3: servidor sobre HTTPS
# =======================================================================

if __name__ == "__main__":
    print("=" * 70)
    print(" LogiMarket - API Gateway de Seguridad ")
    print("=" * 70)
    print("Usuarios de prueba:")
    print("  admin  / Admin#2026   (rol: admin)")
    print("  jperez / Jperez#2026  (rol: user)")
    print("Los códigos MFA se imprimirán aquí en consola durante /login.")
    print("=" * 70)

    # Ejecuta con HTTPS usando el certificado autofirmado generado con
    # OpenSSL (ver instrucciones/README). Si aún no genera el
    # certificado, puede comentar ssl_context para probar en HTTP.
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        ssl_context=("cert.pem", "key.pem")
    )
