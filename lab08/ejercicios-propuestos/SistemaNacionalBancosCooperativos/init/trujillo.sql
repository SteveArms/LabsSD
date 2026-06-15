-- ============================================================
-- Inicialización del nodo: Banco Trujillo
-- Base de datos: banco_trujillo
-- ============================================================

-- Crear tabla de cuentas con restricción de saldo no negativo
CREATE TABLE IF NOT EXISTS cuentas (
    id     SERIAL PRIMARY KEY,
    nombre VARCHAR(100)    NOT NULL,
    saldo  DECIMAL(10, 2)  NOT NULL CHECK (saldo >= 0)
);

-- Insertar datos iniciales
-- Saldo inicial: S/ 75,000.00
INSERT INTO cuentas (nombre, saldo)
VALUES ('Cuenta Trujillo', 75000.00);
