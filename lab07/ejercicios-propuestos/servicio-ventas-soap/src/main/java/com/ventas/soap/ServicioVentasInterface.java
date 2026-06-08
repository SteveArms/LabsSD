package com.ventas.soap;

import jakarta.jws.WebMethod;
import jakarta.jws.WebService;

@WebService
public interface ServicioVentasInterface {
    
    @WebMethod
    String listarProductos();
    
    @WebMethod
    double consultarPrecio(String producto);
    
    @WebMethod
    boolean comprarProducto(String producto, int cantidad);
    
    @WebMethod
    String verCarrito();
    
    @WebMethod
    double finalizarCompra();
}