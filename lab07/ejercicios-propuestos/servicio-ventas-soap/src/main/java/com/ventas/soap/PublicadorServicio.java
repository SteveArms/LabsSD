package com.ventas.soap;

import jakarta.xml.ws.Endpoint;

public class PublicadorServicio {
    public static void main(String[] args) {
        Endpoint.publish("http://localhost:8080/ventas", new ServicioVentasImpl());
        System.out.println("Servicio de ventas SOAP publicado en http://localhost:8080/ventas");
        System.out.println("WSDL: http://localhost:8080/ventas?wsdl");
        System.out.println("Presiona Enter para detener...");
        try {
            System.in.read();
        } catch (Exception e) {
            e.printStackTrace();
        }
        System.exit(0);
    }
}