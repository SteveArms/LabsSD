-- ============================================================
-- Inicialización del nodo: Banco Arequipa
-- Base de datos: banco_arequipa
-- ============================================================

-- Crear tabla de cuentas con restricción de saldo no negativo
CREATE TABLE IF NOT EXISTS cuentas (
    id     SERIAL PRIMARY KEY,
    nombre VARCHAR(100)    NOT NULL,
    saldo  DECIMAL(10, 2)  NOT NULL CHECK (saldo >= 0)
);

-- Insertar datos iniciales
-- Saldo inicial: S/ 100,000.00
INSERT INTO cuentas (nombre, saldo)
VALUES ('Cuenta Arequipa', 100000.00);
