package com.ventas.soap;

import java.net.URL;
import java.util.Scanner;

import javax.xml.namespace.QName;

import jakarta.xml.ws.Service;

public class ClienteVentas {
    public static void main(String[] args) throws Exception {
        URL url = new URL("http://localhost:8080/ventas?wsdl");
        QName qname = new QName("http://soap.ventas.com/", "ServicioVentasImplService");
        Service service = Service.create(url, qname);
        ServicioVentasInterface ventas = service.getPort(ServicioVentasInterface.class);
        
        Scanner sc = new Scanner(System.in);
        int opcion;
        String producto;
        int cantidad;
        
        System.out.println("=== SISTEMA DE VENTAS EN LÍNEA (SOAP) ===");
        do {
            System.out.println("\n1. Listar productos");
            System.out.println("2. Consultar precio de un producto");
            System.out.println("3. Agregar producto al carrito");
            System.out.println("4. Ver carrito");
            System.out.println("5. Finalizar compra");
            System.out.println("0. Salir");
            System.out.print("Opción: ");
            opcion = sc.nextInt();
            sc.nextLine(); // limpiar buffer
            
            switch (opcion) {
                case 1:
                    System.out.println(ventas.listarProductos());
                    break;
                case 2:
                    System.out.print("Nombre del producto: ");
                    producto = sc.nextLine();
                    double precio = ventas.consultarPrecio(producto);
                    if (precio == -1) {
                        System.out.println("Producto no encontrado.");
                    } else {
                        System.out.printf("Precio de %s: $%.2f\n", producto, precio);
                    }
                    break;
                case 3:
                    System.out.print("Nombre del producto: ");
                    producto = sc.nextLine();
                    System.out.print("Cantidad: ");
                    cantidad = sc.nextInt();
                    if (ventas.comprarProducto(producto, cantidad)) {
                        System.out.println("Producto agregado al carrito.");
                    } else {
                        System.out.println("Error: producto no existe o cantidad inválida.");
                    }
                    break;
                case 4:
                    System.out.println(ventas.verCarrito());
                    break;
                case 5:
                    double total = ventas.finalizarCompra();
                    System.out.printf("Compra finalizada. Total a pagar: $%.2f\n", total);
                    break;
                case 0:
                    System.out.println("Saliendo del sistema de ventas.");
                    break;
                default:
                    System.out.println("Opción inválida.");
            }
        } while (opcion != 0);
        sc.close();
    }
}