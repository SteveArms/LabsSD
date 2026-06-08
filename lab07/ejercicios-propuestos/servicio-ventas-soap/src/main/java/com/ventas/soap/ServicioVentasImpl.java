package com.ventas.soap;

import java.util.HashMap;
import java.util.Map;

import jakarta.jws.WebService;

@WebService(endpointInterface = "com.ventas.soap.ServicioVentasInterface")
public class ServicioVentasImpl implements ServicioVentasInterface {
    
    // Catálogo de productos (nombre -> precio)
    private Map<String, Double> catalogo = new HashMap<>();
    
    // Carrito de compras (producto -> cantidad)
    private Map<String, Integer> carrito = new HashMap<>();
    
    public ServicioVentasImpl() {
        // Inicializar catálogo
        catalogo.put("Laptop", 1200.00);
        catalogo.put("Mouse", 25.50);
        catalogo.put("Teclado", 45.00);
        catalogo.put("Monitor", 300.00);
        catalogo.put("Audifonos", 35.00);
    }
    
    @Override
    public String listarProductos() {
        StringBuilder sb = new StringBuilder("CATÁLOGO DE PRODUCTOS:\n");
        for (Map.Entry<String, Double> entry : catalogo.entrySet()) {
            sb.append("- ").append(entry.getKey()).append(": $").append(entry.getValue()).append("\n");
        }
        return sb.toString();
    }
    
    @Override
    public double consultarPrecio(String producto) {
        if (catalogo.containsKey(producto)) {
            return catalogo.get(producto);
        }
        return -1; // Producto no existe
    }
    
    @Override
    public boolean comprarProducto(String producto, int cantidad) {
        if (!catalogo.containsKey(producto)) {
            return false;
        }
        if (cantidad <= 0) {
            return false;
        }
        carrito.put(producto, carrito.getOrDefault(producto, 0) + cantidad);
        return true;
    }
    
    @Override
    public String verCarrito() {
        if (carrito.isEmpty()) {
            return "El carrito está vacío.";
        }
        StringBuilder sb = new StringBuilder("CARRITO DE COMPRAS:\n");
        double total = 0;
        for (Map.Entry<String, Integer> entry : carrito.entrySet()) {
            String prod = entry.getKey();
            int cant = entry.getValue();
            double precio = catalogo.get(prod);
            double subtotal = precio * cant;
            sb.append("- ").append(prod).append(" x").append(cant)
              .append(" = $").append(String.format("%.2f", subtotal)).append("\n");
            total += subtotal;
        }
        sb.append("TOTAL: $").append(String.format("%.2f", total));
        return sb.toString();
    }
    
    @Override
    public double finalizarCompra() {
        double total = 0;
        for (Map.Entry<String, Integer> entry : carrito.entrySet()) {
            String prod = entry.getKey();
            int cant = entry.getValue();
            total += catalogo.get(prod) * cant;
        }
        carrito.clear(); // vaciar carrito después de comprar
        return total;
    }
}