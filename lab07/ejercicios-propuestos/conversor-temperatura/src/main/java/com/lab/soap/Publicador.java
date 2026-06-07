package com.lab.soap;

import jakarta.xml.ws.Endpoint;

public class Publicador {
    public static void main(String[] args) {
        Endpoint.publish("http://localhost:8080/conversor", new ConversorSOAP());
        System.out.println("Servicio SOAP de conversor publicado en http://localhost:8080/conversor");
        System.out.println("WSDL: http://localhost:8080/conversor?wsdl");
        System.out.println("Presiona Enter para detener...");
        try {
            System.in.read();
        } catch (Exception e) {
            e.printStackTrace();
        }
        System.exit(0);
    }
}