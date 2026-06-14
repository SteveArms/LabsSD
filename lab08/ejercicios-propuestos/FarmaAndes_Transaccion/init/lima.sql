CREATE TABLE inventario (
    id SERIAL PRIMARY KEY,
    producto VARCHAR(100) UNIQUE,
    stock INTEGER CHECK (stock >= 0)
);

INSERT INTO inventario (producto, stock) VALUES ('Paracetamol', 50);